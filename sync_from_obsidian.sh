#!/usr/bin/env bash
set -e

# Obsidian 写作目录
OBSIDIAN_BLOG_DIR="/mnt/d/Documents/jianguoyun/obsidian/zhihai.me"

# Pelican 文章目录
PELICAN_BLOG_DIR="./content/blog/md_in_obsidian"

echo "==> Sync from Obsidian to Pelican..."
mkdir -p "$PELICAN_BLOG_DIR"

rsync -av --delete \
  --exclude ".obsidian/" \
  --exclude ".trash/" \
  "$OBSIDIAN_BLOG_DIR/" \
  "$PELICAN_BLOG_DIR/"

echo "==> Done."
