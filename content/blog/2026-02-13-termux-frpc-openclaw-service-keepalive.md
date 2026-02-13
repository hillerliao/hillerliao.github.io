---
title: Termux 环境下 frpc 和 OpenClaw 服务保活方案
date: 2026-02-13
modified: 2026-02-13
tags:
    - termux
    - openclaw
    - frpc
    - android
    - self-hosted
category: blog
slug: termux-frpc-openclaw-auto-restart
authors: hillerliao
description: 利用 Termux 生态中的 termux:boot、termux-wake-lock、tmux 和 cron 组合，实现手机重启后服务自动启动、进程崩溃后自动检测并重启。
---

## 背景与痛点

### 问题场景

在 Android 设备上运行 frpc（内网穿透客户端）和 OpenClaw 时，面临以下挑战：

1. **手机重启后服务不自动启动** - Android 系统不会自动运行 Termux 中的后台服务
2. **进程崩溃后不会重启** - frpc 或 OpenClaw 可能因网络波动、内存不足等原因崩溃，需要手动介入
3. **无法方便地查看日志** - 后台运行的进程没有会话管理，调试困难

### 需求

- ✅ 手机开机后 frpc + OpenClaw 自动启动
- ✅ 进程崩溃后自动检测并重启
- ✅ 方便查看运行日志
- ✅ 低资源占用（不频繁检测）

---

## 方案概述

利用 Termux 生态中的三个工具组合：

| 工具 | 作用 |
|------|------|
| **termux:boot** | 开机时自动执行脚本 |
| **termux-wake-lock** | 防止系统休眠杀死进程 |
| **tmux** | 会话管理（保持进程运行、方便查看日志） |
| **cron** | 定时任务（每5分钟检测进程存活） |

---

## 依赖安装

```bash
# 安装 tmux（会话管理）
pkg install tmux

# 安装 cron（定时任务）
pkg install crontab

# 安装 termux:boot（开机自启）
pkg install termux-boot
```

> **termux:boot 安装后需要在 Android 设置中授权自启动权限**

---

## 脚本内容

### 1. OpenClaw 启动脚本 (`~/openclaw-run.sh`)

负责清理旧进程、重新启动 OpenClaw：

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -e

SESSION="openclaw"
PORT="18789"
NPM_BIN="$HOME/.npm-global/bin"
TOKEN_FILE="$HOME/.openclaw_token"

# 基础检查
if ! command -v tmux >/dev/null 2>&1; then
    echo "[ERR] tmux not found. Install: pkg install tmux"
    exit 1
fi

if [ ! -d "$NPM_BIN" ]; then
    echo "[ERR] $NPM_BIN not found"
    exit 1
fi

if [ ! -f "$TOKEN_FILE" ]; then
    echo "[ERR] token file not found: $TOKEN_FILE"
    exit 1
fi

TOKEN="$(cat "$TOKEN_FILE" | tr -d '\r ')"

mkdir -p "$HOME/tmp"

# 杀掉旧 session
tmux kill-session -t "$SESSION" 2>/dev/null || true
sleep 1

# 新建 session 并启动
tmux new -d -s "$SESSION"
sleep 1

tmux send-keys -t "$SESSION" \
    "export PATH=$NPM_BIN:\$PATH; export TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN='$TOKEN'; openclaw gateway --bind lan --port $PORT --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" \
    C-m

echo "[OK] OpenClaw started in tmux session: $SESSION"
```

### 2. 开机启动脚本 (`~/.termux/boot/services.sh`)

手机开机时自动启动 crond、frpc 和 OpenClaw：

```bash
#!/data/data/com.termux/files/usr/bin/bash

# 1. 清理旧会话
tmux kill-session -t frpc 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null
sleep 1

# 2. 启动 crond（关键）
crond

# 3. 启动 frpc（持有 wake lock）
tmux new-session -d -s frpc "exec /data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini"

# 4. 启动 OpenClaw
tmux new -d -s openclaw
sleep 1
tmux send-keys -t openclaw "export PATH=/data/data/com.termux/files/home/.npm-global/bin:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=tokenac27a3d5; openclaw gateway --bind lan --port 18789 --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

### 3. frpc 启动脚本 (`~/.termux/boot/frpc-start.sh`)

负责启动 frpc 并持有 wake lock：

```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
exec /data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini
```

> **关键点**：使用 `exec` 前缀确保 wake lock 正确持有

### 4. 进程监控脚本 (`~/monitor.sh`)

```bash
#!/data/data/com.termux/files/usr/bin/bash

LOG_FILE=$HOME/monitor.log
MAX_LOG_LINES=1000

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

trim_log() {
    local lines=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
    if [ "$lines" -gt "$MAX_LOG_LINES" ]; then
        tail -n "$MAX_LOG_LINES" "$LOG_FILE" > "$LOG_FILE.tmp"
        mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

log "========== Monitor started =========="

# frpc 检测
if ! pgrep -f "frpc" > /dev/null; then
    log "frpc 进程不存在，准备重启..."
    tmux kill-session -t frpc 2>/dev/null
    sleep 1
    tmux new-session -d -s frpc "exec /data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini"
    log "frpc 重启命令已发送"
else
    log "frpc 运行正常"
fi

# OpenClaw 检测
if ! pgrep -f "openclaw.*gateway" > /dev/null; then
    log "OpenClaw 进程不存在，准备重启..."
    bash ~/openclaw-run.sh > /dev/null 2>&1
    sleep 3
    if pgrep -f "openclaw.*gateway" > /dev/null; then
        log "OpenClaw 进程确认已启动"
    else
        log "OpenClaw 启动验证失败"
    fi
else
    log "OpenClaw 运行正常"
fi

trim_log
log "========== Monitor finished =========="
```

---

## 操作步骤

### 第一步：安装依赖

```bash
pkg update && pkg install tmux crontab termux-api crond
```

### 第二步：创建脚本文件

```bash
mkdir -p ~/.termux/boot
chmod +x ~/.termux/boot/services.sh ~/.termux/boot/frpc-start.sh ~/openclaw-run.sh ~/monitor.sh
```

### 第三步：配置 cron

```bash
crontab -e
# 添加以下内容（每5分钟检测一次）
*/5 * * * * /data/data/com.termux/files/home/monitor.sh
```

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看 tmux 会话 | `tmux ls` |
| 查看 frpc 日志 | `tmux attach -t frpc` |
| 查看 OpenClaw 日志 | `tmux attach -t openclaw` |
| 杀掉 tmux 会话 | `tmux kill-session -t frpc/openclaw` |
| 手动执行检测 | `bash ~/monitor.sh` |
| 查看监控日志 | `tail -f ~/monitor.log` |

---

## 效果

- **手机重启** → crond + frpc + OpenClaw **全部自动启动**
- **进程崩溃** → 5分钟内自动检测并重启
- **随时查看日志** → `tmux attach -t openclaw`

---

## ⚠️ 关键经验教训

1. **termux:boot 只在开机时执行一次**，杀进程后不会自动重启
2. **boot 脚本不能用环境变量**，必须硬编码 token 和 port
3. **crond 必须加入 boot 脚本**，否则进程监控不生效
4. **monitor.sh 用绝对路径**，cron 环境下 $PREFIX 不生效
5. **frpc 用 exec 启动**，确保 wake lock 正确持有

---

## 参考资源

- [Termux Wiki - Boot](https://wiki.termux.com/wiki/Termux:Boot)
- [Termux Wiki - Cron](https://wiki.termux.com/wiki/Cron)
- [Tmux 常用命令](https://tmuxcheatsheet.com/)
