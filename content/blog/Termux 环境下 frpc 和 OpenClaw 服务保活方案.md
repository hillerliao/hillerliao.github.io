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
| **termux-wake-lock** | 防止系统休眠杀死进程 |
| **tmux** | 会话管理（保持进程运行、方便查看日志） |
| **cron** | 定时任务（每5分钟检测进程存活） |

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Android 系统                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Termux 环境                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │   │
│  │  │ termux:boot │→ │ frpc-start │→ │ frpc        │ │   │
│  │  │ (开机执行)   │→ │ (wake lock) │  │ openclaw    │ │   │
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

# 安装 termux:boot（开机自启）
pkg install termux-boot
```

> **termux:boot 安装后需要在 Android 设置中授权自启动权限**

---

## ⚠️ 关键经验教训

1. **termux:boot 只在开机时执行一次**，杀进程后不会自动重启
2. **boot 脚本不能用环境变量**，必须硬编码 token 和 port
3. **crond 必须加入 boot 脚本**，否则进程监控不生效
4. **monitor.sh 用绝对路径**，cron 环境下 $PREFIX 不生效
5. **frpc 用 exec 启动**，确保 wake lock 正确持有，防止休眠被杀死
6. **monitor.sh 添加日志**，便于追踪重启历史和调试

```bash
LOG_FILE=$HOME/monitor.log
log() {
    echo "[$(date)] $1" >> "$LOG_FILE"
}
```

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

手机开机时自动启动 crond、frpc 和 OpenClaw：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# termux:boot services - 开机会话启动

# 启动 crond（关键）
crond

# 启动 frpc（使用独立脚本，包含 wake lock）
bash ~/.termux/boot/frpc-start.sh &

# 清理旧 OpenClaw 进程后启动
pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null
sleep 1
tmux new -d -s openclaw
sleep 1
# 注意：这里必须用硬编码的参数，不能用环境变量
tmux send-keys -t openclaw "export PATH=/data/data/com.termux/files/home/.npm-global/bin:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=tokenac27a3d5; openclaw gateway --bind lan --port 18789 --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

### 3. frpc 启动脚本 (`~/.termux/boot/frpc-start.sh`)

负责启动 frpc 并持有 wake lock，防止系统休眠导致进程被杀死：

```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
/data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini
```

### 4. 进程监控脚本 (`~/monitor.sh`)

每5分钟检测一次，崩溃则重启：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# 进程监控脚本 - 每5分钟检测并重启崩溃的服务

LOG_FILE=$HOME/monitor.log
MAX_LOG_LINES=1000  # 日志最大行数

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

trim_log() {
    # 保留最后 MAX_LOG_LINES 行
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
    # 用 exec 确保 wake lock 正确持有
    tmux new-session -d -s frpc "exec /data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini"
    log "frpc 重启命令已发送"
else
    log "frpc 运行正常"
fi

# OpenClaw 检测
if ! pgrep -f "openclaw.*gateway" > /dev/null; then
    log "OpenClaw 进程不存在，准备重启..."
    tmux kill-session -t openclaw 2>/dev/null
    sleep 2  # 等待端口释放
    bash ~/openclaw-run.sh
    log "OpenClaw 重启命令已发送"
else
    log "OpenClaw 运行正常"
fi

# 清理日志
trim_log

log "========== Monitor finished =========="
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
（将下方内容写入文件，**注意：参数必须硬编码**）

```bash
#!/data/data/com.termux/files/usr/bin/bash
# OpenClaw 启动脚本 - 硬编码参数

# 杀掉旧进程
pkill -9 -f 'openclaw' 2>/dev/null
tmux kill-session -t openclaw 2>/dev/null

# 等待资源释放（增加等待时间）
sleep 2

# 创建新 tmux 会话
tmux new -d -s openclaw

# 等待会话就绪
sleep 1

# 发送启动命令（硬编码所有参数）
tmux send-keys -t openclaw "export PATH=/data/data/com.termux/files/home/.npm-global/bin:\$PATH TMPDIR=\$HOME/tmp; export OPENCLAW_GATEWAY_TOKEN=tokenac27a3d5; openclaw gateway --bind lan --port 18789 --token \$OPENCLAW_GATEWAY_TOKEN --allow-unconfigured" C-m
```

#### 创建 `~/.termux/boot/services.sh`
（将下方内容写入文件，**注意：参数必须硬编码**）

```bash
#!/data/data/com.termux/files/usr/bin/bash
# termux:boot services - 开机会话启动

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

log "Services started at $(date)" >> ~/boot.log 2>/dev/null || true
```

#### 创建 `~/.termux/boot/frpc-start.sh`
（将下方内容写入文件，包含 wake lock 防止休眠）

```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
/data/data/com.termux/files/usr/bin/frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini
```

#### 创建 `~/monitor.sh`
（将下方内容写入文件，**注意：用 tmux 管理 frpc**）

```bash
#!/data/data/com.termux/files/usr/bin/bash
# frpc 检测
if ! pgrep -f "frpc" > /dev/null; then
    tmux new-session -d -s frpc "frpc -c /data/data/com.termux/files/usr/etc/frp/frpc.ini"
fi

# OpenClaw 检测
if ! pgrep -f "openclaw.*gateway" > /dev/null; then
    tmux kill-session -t openclaw 2>/dev/null
    bash ~/openclaw-run.sh
fi
```

### 第三步：设置权限

```bash
chmod +x ~/.termux/boot/services.sh ~/.termux/boot/frpc-start.sh ~/openclaw-run.sh ~/monitor.sh
```

### 第四步：配置 cron

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每5分钟检测一次）
*/5 * * * * /data/data/com.termux/files/home/monitor.sh

# 保存退出后，启动 cron 服务（这一步也可以放到 boot 脚本里自动执行）
crond
```

### 第五步：测试

```bash
# 手动启动 boot 脚本测试
bash ~/.termux/boot/services.sh

# 查看 tmux 会话
tmux ls

# 查看进程是否运行
ps aux | grep -E "crond|frpc|openclaw" | grep -v grep

# 查看 crond 是否运行（验证 boot 脚本是否成功执行）
ps aux | grep crond | grep -v grep

# 手动测试检测脚本
bash ~/monitor.sh
```

### 第六步：验证开机自启动

```bash
# 重启手机，验证以下进程是否自动启动：
# 1. crond - 进程监控依赖它
# 2. frpc - 内网穿透
# 3. OpenClaw - 主服务

ps aux | grep -E "crond|frpc|openclaw" | grep -v grep
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
| 手动执行检测 | `bash /data/data/com.termux/files/home/monitor.sh` |
| 查看监控日志 | `tail -f ~/monitor.log` |
| 查看启动日志 | `tail -f ~/boot.log` |
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
3. **boot 脚本里用了硬编码的路径和参数？**
4. 重启手机测试，不只是重启 Termux app

### Q4: 手机重启后 frpc/OpenClaw 没启动？

可能原因：
1. **crond 没在 boot 脚本里启动** → monitor.sh 不会运行
2. **boot 脚本用了环境变量** → 开机时 $TOKEN、$PORT 为空
3. **boot 脚本语法错误** → 检查日志：`logcat -s termux:boot`

### Q5: 进程崩溃后没自动重启？

可能原因：
1. **crond 没运行** → `ps aux | grep crond`
2. **monitor.sh 路径错误** → crontab 里用绝对路径 `/data/data/com.termux/files/home/monitor.sh`
3. **monitor.sh 里用了 $PREFIX** → 改成绝对路径

### Q6: 如何调整检测频率？

编辑 crontab：

```bash
crontab -e
```

- 每1分钟：`* * * * * /data/data/com.termux/files/home/monitor.sh`
- 每5分钟：`*/5 * * * * /data/data/com.termux/files/home/monitor.sh`
- 每10分钟：`*/10 * * * * /data/data/com.termux/files/home/monitor.sh`

### Q7: boot 脚本执行了但进程没起来？

调试方法：

```bash
# 手动执行 boot 脚本看报错
bash -x ~/.termux/boot/services.sh

# 查看 termux:boot 日志
logcat -s termux:boot

# 检查环境变量是否存在
echo $TOKEN $PORT $PREFIX
```

### Q8: 如何查看日志？

```bash
# 查看监控日志（进程重启记录）
tail -f ~/monitor.log

# 查看启动日志
tail -f ~/boot.log

# 查看 tmux 会话日志
tmux attach -t openclaw
tmux attach -t frpc
```

---

## 效果

- **手机重启** → crond + frpc + OpenClaw **全部自动启动**
- **进程崩溃** → 5分钟内自动检测并重启
- **随时查看日志** → `tmux attach -t openclaw`

---

## 完整启动链路（手机开机后）

```
手机开机
    ↓
termux:boot 自动触发
    ↓
services.sh 执行：
  1. crond（关键！进程监控依赖它）
  2. frpc-start.sh（持有 wake lock）
  3. OpenClaw（主服务）
    ↓
frpc 持有 termux-wake-lock，防止系统休眠
    ↓
crond 每5分钟运行 monitor.sh
    ↓
检测到进程挂了 → 自动重启
```

---

## 参考资源

- [Termux Wiki - Boot](https://wiki.termux.com/wiki/Termux:Boot)
- [Termux Wiki - Cron](https://wiki.termux.com/wiki/Cron)
- [Tmux 常用命令](https://tmuxcheatsheet.com/)
