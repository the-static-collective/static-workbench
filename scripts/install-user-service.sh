#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/static-workbench"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
unit_path="$unit_dir/static-workbench.service"

if [[ -x "$repo_root/.venv/bin/static-workbench" ]]; then
  executable="$repo_root/.venv/bin/static-workbench"
elif command -v static-workbench >/dev/null 2>&1; then
  executable="$(command -v static-workbench)"
else
  echo "static-workbench executable not found." >&2
  echo "Create .venv and run: .venv/bin/pip install -e ." >&2
  exit 2
fi

mkdir -p "$config_dir" "$unit_dir"
if [[ ! -f "$config_dir/config.toml" ]]; then
  cp "$repo_root/config.example.toml" "$config_dir/config.toml"
  echo "Created $config_dir/config.toml"
fi

EXECUTABLE="$executable" REPO_ROOT="$repo_root" TEMPLATE="$repo_root/systemd/static-workbench.service" UNIT_PATH="$unit_path" python3 - <<'PY'
import json
import os
from pathlib import Path

template = Path(os.environ["TEMPLATE"]).read_text(encoding="utf-8")
template = template.replace("__EXEC_START__", json.dumps(os.environ["EXECUTABLE"]))
template = template.replace("__WORKING_DIRECTORY__", json.dumps(os.environ["REPO_ROOT"]))
Path(os.environ["UNIT_PATH"]).write_text(template, encoding="utf-8")
PY

systemctl --user daemon-reload
systemctl --user enable --now static-workbench.service

echo "Static Workbench service installed and started."
echo "Open: http://127.0.0.1:13700"
echo "Status: systemctl --user status static-workbench.service"
