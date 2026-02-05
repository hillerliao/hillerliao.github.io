#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

./sync_from_obsidian.sh

git add .
git commit -m "publish: $(date '+%Y-%m-%d %H:%M')" || echo "No changes"
git push origin main
