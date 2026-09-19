from __future__ import annotations

import json
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.broadcast import broadcast_door
from static_workbench.config import RootConfig, WorkbenchConfig, load_config
from static_workbench.repos import discover_repositories


def make_config(tmp_path: Path, port=None):
    root = tmp_path / "repos"
    repo = root / "static-live"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),), broadcast_port=port,
    )


@contextmanager
def local_service(identity=None, status=None, redirect=False):
    identity = identity if identity is not None else {
        "service": "static-live.broadcast",
        "contract": "static-live.broadcast-house-door/v0.1",
        "consolePath": "/", "eventId": "demo",
    }
    status = status if status is not None else {
        "event": {"id": "demo", "title": "Local demo"},
        "status": {"state": "recording_only", "recording": True, "stream": False},
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if redirect:
                self.send_response(302)
                self.send_header("Location", "http://example.invalid/api/status")
                self.end_headers()
                return
            body = identity if self.path == "/api/house/identity" else status if self.path == "/api/status" else None
            if body is None:
                self.send_response(404)
                self.end_headers()
                return
            raw = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_checkout_is_not_confused_with_running_service(tmp_path: Path):
    config = make_config(tmp_path)
    discovered = discover_repositories(config.roots)
    door = broadcast_door(config, discovered)
    assert door["checkout_present"] is True
    assert door["connection"] == "unconfigured"
    assert door["open_url"] is None


def test_explicit_local_door_shows_self_reported_recording_only_state(tmp_path: Path):
    config = make_config(tmp_path)
    with local_service() as port:
        config = replace(config, broadcast_port=port)
        with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
            response = client.get("/api/broadcast/door")
            html = client.get("/").text
            js = client.get("/assets/app.js").text
    assert response.status_code == 200
    body = response.json()
    assert body["connection"] == "reachable"
    assert body["open_url"] == f"http://127.0.0.1:{port}/"
    assert body["event"] == {"id": "demo", "title": "Local demo"}
    assert body["broadcast_state"] == "recording_only"
    assert body["recording"] is True and body["stream"] is False
    assert "authority" in body and body["authority"] == "static-live"
    assert "/api/broadcast/door" in js
    assert "Open Static Broadcast" in js
    assert "127.0.0.1" in js
    assert "data-view=\"house\"" in html


def test_rejects_mismatched_identity_and_event_and_redirect(tmp_path: Path):
    config = make_config(tmp_path)
    repos = discover_repositories(config.roots)
    cases = [
        ({"service": "someone-else", "contract": "static-live.broadcast-house-door/v0.1", "consolePath": "/", "eventId": "demo"}, None, False),
        (None, {"event": {"id": "different", "title": "Fake"}, "status": {"state": "ready", "recording": False, "stream": False}}, False),
        (None, None, True),
    ]
    for identity, status, redirect in cases:
        with local_service(identity=identity, status=status, redirect=redirect) as port:
            result = broadcast_door(replace(config, broadcast_port=port), repos)
            assert result["open_url"] is None
            assert result["connection"] != "reachable"


def test_missing_checkout_never_probes_configured_service(tmp_path: Path):
    config = make_config(tmp_path)
    with local_service() as port:
        response = broadcast_door(replace(config, broadcast_port=port), [])
    assert response["connection"] == "checkout_missing"
    assert response["open_url"] is None


def test_config_rejects_wrong_and_workbench_ports(tmp_path: Path):
    cfg = tmp_path / "cfg.toml"
    for value in ['broadcast_port = "3008"', "broadcast_port = 13700", "broadcast_port = 65536", "broadcast_port = true"]:
        cfg.write_text('bind_host = "127.0.0.1"\nport = 13700\n' + value + '\n[[roots]]\nid = "static"\npath = "' + str(tmp_path) + '"\n')
        try:
            load_config(cfg)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid broadcast port accepted: {value}")
