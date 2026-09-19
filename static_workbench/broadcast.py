"""Read-only loopback discovery for the project-owned Static Broadcast console.

Only the operator config selects the port. Browser input cannot choose a host, URL,
port or request method. A self-reported identity is not an authentication proof.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .config import WorkbenchConfig
from .repos import RepoStatus

_IDENTITY = "static-live.broadcast"
_CONTRACT = "static-live.broadcast-house-door/v0.1"
_STATES = frozenset({"ready", "recording", "recording_only", "live", "faulted", "boot", "preflight", "blocked", "ending", "preserved"})
_LIMIT = 16384


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused for loopback broadcast probe")


def _get_json(base: str, path: str) -> dict[str, Any]:
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(base + path, headers={"Accept": "application/json"}, method="GET")
    with opener.open(request, timeout=0.75) as response:
        if response.status != 200:
            raise ValueError("unexpected broadcast response")
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("broadcast response was not JSON")
        raw = response.read(_LIMIT + 1)
        if len(raw) > _LIMIT:
            raise ValueError("broadcast response exceeded size limit")
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("broadcast response was not an object")
    return body


def broadcast_door(config: WorkbenchConfig, repos: list[RepoStatus]) -> dict[str, Any]:
    present = any(r.name.casefold() == "static-live" for r in repos)
    base: dict[str, Any] = {
        "checkout_present": present,
        "configured": config.broadcast_port is not None,
        "connection": "unconfigured",
        "open_url": None,
        "event": None,
        "broadcast_state": None,
        "recording": None,
        "stream": None,
        "source": "static-live.broadcast / self-reported local service; not authenticated",
        "authority": "static-live",
    }
    if not present or config.broadcast_port is None:
        base["connection"] = "checkout_missing" if not present else "unconfigured"
        return base
    # Config is validated during load; dataclass can also be constructed directly in tests.
    port = config.broadcast_port
    if type(port) is not int or not 1 <= port <= 65535 or port == config.port:
        base["connection"] = "invalid_configuration"
        return base
    url = f"http://127.0.0.1:{port}"
    try:
        identity = _get_json(url, "/api/house/identity")
        if (
            identity.get("service") != _IDENTITY
            or identity.get("contract") != _CONTRACT
            or identity.get("consolePath") != "/"
            or not isinstance(identity.get("eventId"), str)
            or not identity["eventId"].strip()
        ):
            base["connection"] = "unrecognized_service"
            return base
        live = _get_json(url, "/api/status")
        status = live.get("status")
        event = live.get("event")
        if (
            not isinstance(status, dict)
            or not isinstance(event, dict)
            or event.get("id") != identity["eventId"]
            or not isinstance(event.get("title"), str)
            or not 0 < len(event["title"]) <= 200
            or status.get("state") not in _STATES
            or type(status.get("recording")) is not bool
            or type(status.get("stream")) is not bool
        ):
            base["connection"] = "unrecognized_service"
            return base
    except (HTTPError, URLError, ValueError, OSError, TimeoutError, json.JSONDecodeError):
        base["connection"] = "offline_or_incompatible"
        return base
    return {
        **base,
        "connection": "reachable",
        "open_url": url + "/",
        "event": {"id": identity["eventId"], "title": event["title"]},
        "broadcast_state": status["state"],
        "recording": status["recording"],
        "stream": status["stream"],
    }
