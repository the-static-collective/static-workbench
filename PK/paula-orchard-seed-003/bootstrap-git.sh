#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"
[ -d .git ] || git init
git add .
if ! git diff --cached --quiet; then git commit -m "Paula Story Workbench v0.1"; fi
git branch -M main
printf "Paste the new GitHub repository URL, or press Enter to keep this local: "
read REMOTE
if [ -n "$REMOTE" ]; then
  if git remote get-url origin >/dev/null 2>&1; then git remote set-url origin "$REMOTE"; else git remote add origin "$REMOTE"; fi
  git push -u origin main
fi
