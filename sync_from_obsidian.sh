#!/usr/bin/env bash
set -e

# Obsidian 写作目录
OBSIDIAN_BLOG_DIR="/mnt/d/Documents/jianguoyun/obsidian/zhihai.me"

# Pelican 文章目录
PELICAN_BLOG_DIR="./content/blog"

command -v rsync >/dev/null 2>&1 || { echo "❌ rsync not found, try again in linux machine"; exit 1; }

echo "==> Sync markdown from Obsidian to Pelican..."
mkdir -p "$PELICAN_BLOG_DIR"

rsync -av --delete \
  --exclude ".obsidian/" \
  --exclude ".trash/" \
  --exclude ".DS_Store" \
  --exclude "Thumbs.db" \
  --include "*/" \
  --include "*.md" \
  --exclude "*" \
  "$OBSIDIAN_BLOG_DIR/" \
  "$PELICAN_BLOG_DIR/"

echo "==> Done."
