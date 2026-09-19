#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/static-workbench"
config_path="$config_dir/config.toml"
static_root="${STATIC_ROOT:-$HOME/static}"

cd "$repo_root"
mkdir -p "$static_root" "$config_dir"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -e .

if [[ ! -f "$config_path" ]]; then
  cp config.example.toml "$config_path"
  echo "Created $config_path"
else
  echo "Keeping existing $config_path"
fi

echo
echo "Static Workbench v0.2 is installed locally."
echo "Repository habitat: $static_root"
echo "Run: STATIC_WORKBENCH_CONFIG=$config_path $repo_root/.venv/bin/static-workbench"
echo "Open: http://127.0.0.1:13700"

if [[ "${1:-}" == "--service" ]]; then
  "$repo_root/scripts/install-user-service.sh"
fi
