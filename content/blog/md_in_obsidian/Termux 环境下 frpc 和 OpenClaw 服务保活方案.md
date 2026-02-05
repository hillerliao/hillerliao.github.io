---
title: Termux 环境下 frpc 和 OpenClaw 服务保活方案
date: 2022-05-10T16:00:00+08:00
tags:
    - Termux
    - frpc
    - OpenClaw
    - 服务保活
    - 定时任务
    - 开机自启
    - 会话管理
    - tmux
    - cron
    - termux:boot
slug: termux-frpc-openclaw-service-survival   
---

## 背景与痛点

### 问题场景

在 Android 设备上运行 frpc（内网穿透客户端）和 OpenClaw 时，面临以下挑战：

1. **手机重启后服务不自动启动**  
   Android 系统不会自动运行 Termux 中的后台服务

2. **进程崩溃后不会重启**  
   frpc 或 OpenClaw 可能因网络波动、内存不足等原因崩溃，需要手动介入

3. **无法方便地查看日志**  
   后台运行的进程没有会话管理，调试困难

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
| **tmux** | 会话管理（保持进程运行、方便查看日志） |
| **cron** | 定时任务（每5分钟检测进程存活） |

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Android 系统                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Termux 环境                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │   │
│  │  │ termux:boot │→ │   tmux      │→ │ frpc        │ │   │
│  │  │ (开机执行)   │  │ (会话管理)   │  │ openclaw    │ │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │   │
│  │                                                  │     │   │
│  │  ┌─────────────┐  ┌────────────────────────────┐  │     │   │
│  │  │    cron     │→ │ monitor.sh (每5分钟执行)   │  │     │   │
│  │  │ (定时检测)   │  │ 检测进程是否存在 → 重启    │  │     │   │
│  │  └─────────────┘  └────────────────────────────┘  │     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 依赖安装

```bash
# 安装 tmux（会话管理）
pkg install tmux

# 安装 cron（定时任务）
pkg install crontab

# 启动 cron 服务
crond

# 安装 termux:boot（开机自启）
pkg install termux-boot
```

> **termux:boot 安装后需要在 Android 设置中授权自启动权限（忽略电池优化）**

---

## 脚本内容

### 1. OpenClaw 启动脚本 (`~/openclaw-run.sh`)

负责清理旧进程、重新启动 OpenClaw：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# OpenClaw 启动脚本

# 杀掉旧进程
pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null

# 等待资源释放
sleep 1

# 创建新 tmux 会话
tmux new -d -s openclaw

# 等待会话就绪
sleep 1

# 发送启动命令到 tmux 会话
tmux send-keys -t openclaw "export PATH=$NPM_BIN:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=$TOKEN; openclaw gateway --bind lan --port $PORT --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

### 2. 开机启动脚本 (`~/.termux/boot/services.sh`)

手机开机时自动启动 frpc 和 OpenClaw：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# termux:boot services - 开机自启动脚本

# 启动 frpc
tmux new-session -d -s frpc "frpc -c $PREFIX/etc/frp/frpc.ini"

# 清理旧 OpenClaw 进程后启动
pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null
sleep 1
tmux new -d -s openclaw
sleep 1
tmux send-keys -t openclaw "export PATH=$NPM_BIN:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=$TOKEN; openclaw gateway --bind lan --port $PORT --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

### 3. 进程监控脚本 (`~/monitor.sh`)

每5分钟检测一次，崩溃则重启：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# 进程监控脚本 - 每5分钟检测并重启崩溃的服务

# frpc 检测
if ! pgrep -f "frpc" > /dev/null; then
    echo "[$(date)] frpc 崩溃，重启中..."
    tmux new-session -d -s frpc "frpc -c $PREFIX/etc/frp/frpc.ini"
fi

# OpenClaw 检测
if ! pgrep -f "openclaw.*gateway" > /dev/null; then
    echo "[$(date)] OpenClaw 崩溃，重启中..."
    tmux kill-session -t openclaw 2>/dev/null
    bash ~/openclaw-run.sh
fi
```

---

## 操作步骤

### 第一步：安装依赖

```bash
pkg update && pkg install tmux crontab termux-api
crond
```

### 第二步：创建脚本文件

#### 创建目录
```bash
mkdir -p ~/.termux/boot
```

#### 创建 `~/openclaw-run.sh`
（将下方内容写入文件）

```bash
#!/data/data/com.termux/files/usr/bin/bash
pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null
sleep 1
tmux new -d -s openclaw
sleep 1
tmux send-keys -t openclaw "export PATH=$NPM_BIN:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=$TOKEN; openclaw gateway --bind lan --port $PORT --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

#### 创建 `~/.termux/boot/services.sh`
（将下方内容写入文件）

```bash
#!/data/data/com.termux/files/usr/bin/bash
tmux new-session -d -s frpc "frpc -c $PREFIX/etc/frp/frpc.ini"

pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null
sleep 1
tmux new -d -s openclaw
sleep 1
tmux send-keys -t openclaw "export PATH=$NPM_BIN:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=$TOKEN; openclaw gateway --bind lan --port $PORT --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

#### 创建 `~/monitor.sh`
（将下方内容写入文件）

```bash
#!/data/data/com.termux/files/usr/bin/bash
if ! pgrep -f "frpc" > /dev/null; then
    tmux new-session -d -s frpc "frpc -c $PREFIX/etc/frp/frpc.ini"
fi

if ! pgrep -f "openclaw.*gateway" > /dev/null; then
    tmux kill-session -t openclaw 2>/dev/null
    bash ~/openclaw-run.sh
fi
```

### 第三步：设置权限

```bash
chmod +x ~/.termux/boot/services.sh ~/openclaw-run.sh ~/monitor.sh
```

### 第四步：配置 cron

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每5分钟检测一次）
*/5 * * * * ~/monitor.sh
```

### 第五步：测试

```bash
# 手动启动服务
bash ~/.termux/boot/services.sh

# 查看 tmux 会话
tmux ls

# 查看 frpc 日志
tmux attach -t frpc

# 查看 OpenClaw 日志
tmux attach -t openclaw

# 手动测试检测脚本
bash ~/monitor.sh
```

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看 tmux 会话 | `tmux ls` |
| 查看 frpc 日志 | `tmux attach -t frpc`（Ctrl+B 然后 D 退出） |
| 查看 OpenClaw 日志 | `tmux attach -t openclaw` |
| 强制退出日志视图 | `Ctrl+B 然后 D` |
| 杀掉 tmux 会话 | `tmux kill-session -t frpc/openclaw` |
| 手动执行检测 | `bash ~/monitor.sh` |
| 查看 cron 日志 | `logcat -s crond` |

---

## 常见问题

### Q1: 检测频率会影响电池吗？

不会。`pgrep` 进程检查是非常轻量的系统调用，比手机待机功耗低几个数量级。每5分钟一次完全可接受。

### Q2: 为什么用 tmux 而不是 nohup？

- tmux 可以方便地查看实时日志
- tmux 保持会话不中断
- 可以随时手动连接查看状态

### Q3: termux:boot 没生效？

检查：
1. Android 设置中允许 Termux 自启动
2. 脚本权限正确（`chmod +x`）
3. 脚本有执行权限

### Q4: 如何调整检测频率？

编辑 crontab：

```bash
crontab -e
```

- 每1分钟：`* * * * * ~/monitor.sh`
- 每5分钟：`*/5 * * * * ~/monitor.sh`
- 每10分钟：`*/10 * * * * ~/monitor.sh`

---

## 效果

- **手机重启** → frpc + OpenClaw 自动启动
- **进程崩溃** → 5分钟内自动检测并重启
- **随时查看日志** → `tmux attach -t frpc/openclaw`

---

## 参考资源

- [Termux Wiki - Boot](https://wiki.termux.com/wiki/Termux:Boot)
- [Termux Wiki - Cron](https://wiki.termux.com/wiki/Cron)
- [Tmux 常用命令](https://tmuxcheatsheet.com/)
