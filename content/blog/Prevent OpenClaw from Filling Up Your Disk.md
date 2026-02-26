---
title: 我替你踩坑了：部署 OpenClaw 后，记得先做这一步，防止服务器被跑死
date: '2026-02-26 12:02:14'
category: Tech
tags: openclaw, linux, server, log, disk
slug: prevent-openclaw-from-filling-up-your-disk
---

# 我替你踩坑了：部署 OpenClaw 后，记得先做这一步

如果你已经把 OpenClaw 跑起来了，这篇文章建议你花 5 分钟看完，**可以直接帮你避开服务器跑死的坑**。

---

## 不想看过程？直接照做这 3 步

```bash
# 1. 清理已有日志
sudo rm -f /tmp/openclaw/*.log
```

```bash
# 2. 设置日志上限（单文件 >1GB 自动删）
sudo tee /usr/local/bin/openclaw-log-guard.sh >/dev/null <<'EOF'
#!/bin/bash
find /tmp/openclaw -name "*.log" -size +1G -delete
EOF
sudo chmod +x /usr/local/bin/openclaw-log-guard.sh
```

```bash
# 3. 每小时执行一次
(crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/openclaw-log-guard.sh") | crontab -
```

做到这里就够了。
下面是我为什么会踩到这个坑。

---

## 事情背景：早上 7 点，服务器告警

早上七点多，收到阿里云短信：

> 磁盘使用率超过 95%

---

## 一、确认磁盘真的满了

```bash
df -h
```

只看一行：

* `/`（根分区）
* `Use% > 95%`

---

## 二、到底是谁在占磁盘？

### 1️⃣ 先看哪个目录最大

```bash
sudo du -sh /* 2>/dev/null | sort -rh | head -10
```

结果发现：

* `/tmp` 占用了 **十几 GB**

---

### 2️⃣ 继续往 `/tmp` 里找

```bash
sudo du -sh /tmp/* 2>/dev/null | sort -rh | head -10
```

当时最扎眼的一行是：

```text
10G   /tmp/openclaw
```

---

### 3️⃣ 看里面是什么

```bash
ls -lh /tmp/openclaw
```

看到的是几个日志文件：

* 一个接近 **9GB**
* 另一个 **1GB+**

到这里已经可以确定：

> **是 OpenClaw 日志把磁盘写满了**

---

## 三、这些日志主要在记什么？

查看日志里主要的错误信息：

```
grep -Ei "disconnect|reconnect|unauthorized|token|1008|ws" /tmp/openclaw/openclaw-2026-02-24.log | head
```

内容主要是三类：

1. **Gateway / WebSocket 日志**
   Web UI 连接、断开、重连都会写。

2. **浏览器或工具调用失败日志**
   比如浏览器控制没连上、工具参数不完整，**失败会反复重试**，每次都写一条。

3. **插件或消息通道异常日志**
   插件加载了，但目标不匹配，也会持续尝试并记录失败。

重点不在“有没有错误”，而在于：

> **这些日志默认没有大小上限**

一旦进入异常循环，文件会一直涨。

---

## 四、我当时怎么处理的（先止血）

### 1️⃣ 直接删日志

```bash
sudo rm -f /tmp/openclaw/*.log
```

### 2️⃣ 再看磁盘

```bash
df -h
```

这时根分区使用率降到了 **69% 左右**。

---

## 五、真正关键的一步：防止再发生

只清一次没意义，必须加“上限”。

### 限制 OpenClaw 日志大小

#### 1️⃣ 新建清理脚本

```bash
sudo tee /usr/local/bin/openclaw-log-guard.sh >/dev/null <<'EOF'
#!/bin/bash
find /tmp/openclaw -name "*.log" -size +1G -delete
EOF
```

```bash
sudo chmod +x /usr/local/bin/openclaw-log-guard.sh
```

作用只有一句话：

> **任何 OpenClaw 日志文件超过 1GB，就删除**

---

#### 2️⃣ 设置定时任务（每小时一次）

```bash
crontab -e
```

加一行：

```cron
0 * * * * /usr/local/bin/openclaw-log-guard.sh
```

* 不频繁
* 不影响排障
* 足够安全

---

## 六、现在的状态

* 磁盘不再突然 95%+
* 日志不会无限增长
* OpenClaw 正常运行
* 不需要人工盯着

---

## 最后一句话

> 部署 OpenClaw 后，
> **第一件要做的事是：给日志设上限。**

这个坑我已经踩过了，
你不需要再踩一次。

如果你在部署或使用OpenClaw过程中有碰到问题，都可以进群交流，大多数坑都已经有人踩过了。

![](../images/a416b9ca688bec9e83693414c4075eb3.png)