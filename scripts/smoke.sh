#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
tmp="$(mktemp -d)"
pid=""
cleanup() {
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  rm -rf "$tmp"
}
trap cleanup EXIT

mkdir -p "$tmp/root" "$tmp/state"
printf 'smoke witness
' > "$tmp/root/hello.txt"
port="$(python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"
cat > "$tmp/config.toml" <<EOF_CONFIG
bind_host = "127.0.0.1"
port = $port
state_dir = "$tmp/state"
max_repo_depth = 2
preview_bytes = 4096

[[roots]]
id = "smoke"
path = "$tmp/root"
EOF_CONFIG

cd "$repo_root"
STATIC_WORKBENCH_CONFIG="$tmp/config.toml" python3 -m static_workbench.app >"$tmp/server.log" 2>&1 &
pid=$!

PORT="$port" python3 - <<'PY'
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

base = f"http://127.0.0.1:{os.environ['PORT']}"

def get(path):
    with urllib.request.urlopen(base + path, timeout=2) as response:
        return response.status, response.read(), response.headers.get_content_type()

def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.status, json.loads(response.read())

for _ in range(80):
    try:
        status, body, _ = get("/api/bootstrap")
        if status == 200:
            break
    except (OSError, urllib.error.URLError):
        time.sleep(0.05)
else:
    raise SystemExit("supervisor did not become ready")

status, body, _ = get("/api/bootstrap")
bootstrap = json.loads(body)
assert status == 200 and bootstrap["roots"][0]["id"] == "smoke"

status, body, _ = get("/api/machine")
assert status == 200 and "cpu_percent" in json.loads(body)

status, body, _ = get("/api/repos")
assert status == 200 and "repos" in json.loads(body)

query = urllib.parse.urlencode({"root_id": "smoke", "path": "hello.txt"})
status, body, _ = get("/api/objects/inspect?" + query)
obj = json.loads(body)
assert status == 200 and obj["preview"] == "smoke witness
"

status, first = post_json("/api/aperture/analyze", {"raw_text": "The bank moved."})
assert status == 200
assert first["analysis"]["status"] == "unresolved"
assert [reading["id"] for reading in first["analysis"]["readings"]] == [
    "bank.financial", "bank.river", "bank.maneuver"
]

status, second = post_json(
    "/api/aperture/analyze",
    {
        "raw_text": "The bank moved.",
        "context_text": "After the flood, the bank moved six feet east.",
        "parent_id": first["id"],
    },
)
assert status == 200
assert second["parent_id"] == first["id"]
assert second["analysis"]["status"] == "narrowed"
assert [reading["id"] for reading in second["analysis"]["readings"]] == ["bank.river"]

status, body, _ = get("/api/aperture/history")
history = json.loads(body)["sense_fields"]
assert status == 200
assert [row["id"] for row in history[:2]] == [second["id"], first["id"]]
assert history[1]["analysis"]["status"] == "unresolved"

status, body, _ = get("/api/events")
events = json.loads(body)["events"]
assert status == 200
assert any(e["kind"] == "object.inspected" for e in events)
assert any(e["kind"] == "aperture.analyzed" for e in events)

status, body, content_type = get("/")
assert status == 200 and b"STATIC / WORKBENCH" in body and content_type == "text/html"
print("smoke: supervisor + API + UI + durable witness + APERTURE lineage OK")
PY
