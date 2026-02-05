---
title: 用你的旧手机运行 OpenClaw，省下买服务器的钱
urlname: install-openclaw-on-old-phone-with-termux
date: 2026-02-03
description: 记录了如何使用 Termux 在旧手机上运行 OpenClaw 的完整过程，包括技术选型、问题解决、脚本架构设计等开发经验。
tags:
  - OpenClaw
  - Termux
  - Android
  - Shell 脚本
  - AI 助手
---

![[Pasted image 20260203103854.png]]
## 需求背景

最近，一个叫做 OpenClaw 的软件开始火了起来。我试着在虚拟机 Ubuntu 系统上跑了一下，虽然部署过程十分艰辛，但跑起来之后，发现确实很好用，能当个全天候的 AI 助手。

但问题来了：要 24 小时在线，就得有台机器一直开着。有时候出门去，电脑休眠了，助手就连不上了。

我看了一眼书桌上尘封已久的旧手机，突然冒出一个想法：既然网上教程都说最低 2G 2 核的机器就能运行 OpenClaw，那现在的安卓机配置那么高，**是不是可以让 OpenClaw 跑在旧手机上？**

一开始想找现成的方案，但失败了。最麻烦的就是包依赖的问题，看到那些报错，网上信息也不多，很头疼。不过带着报错信息，在多个大模型之间来回穿梭，终于比较圆满地解决了。

不多说，直接上过程。

---

## 前置条件

开始之前，请确认你准备好以下条件：

- 一部能正常使用的**安卓旧手机**（配置要求不高，普通旧手机就行）
- 手机能正常访问**互联网**（下载和安装需要）
- ⚠️ 网络环境可能需要**魔法上网**，如果下载失败请注意这一点
- 最重要的是要有**信心和耐心**，跟着一步步来，没问题！

## 下载和安装 Termux

首先，我们需要下载 Termux 应用。

**什么是 Termux？**简单说，它是一个能在安卓手机上运行命令行工具的软件，相当于给手机装了个简易的 Linux 系统。

### 如何下载

由于国内应用市场无法直接下载，你需要通过以下方式之一获取：

**推荐方式：**
- [F-Droid](https://f-droid.org/en/packages/com.termux/) - 官方下载渠道，最安全

**其他方式（如上面的打不开）：**
- [GitHub 官方发布页](https://github.com/termux/termux-app/releases) - 需要魔法上网
- [Google Play](https://play.google.com/store/apps/details?id=com.termux)
- 第三方应用商店（如 ApkPure 等）- 注意选择正规来源

> 💡 **小贴士**：下载时请认准官方来源，避免下载不安全的第三方应用。

### 安装

下载好后，直接安装。安装完成后：

1. **打开 Termux 应用**
2. 你会看到一个黑色屏幕，这就是命令行终端界面
3. 长按屏幕可以粘贴内容，点击屏幕可以输入

## 🦞 运行安装脚本

接下来，复制下面的命令，粘贴到终端界面：

```bash
curl -sL https://s.zhihai.me/openclaw > openclaw-install.sh
chmod +x openclaw-install.sh
./openclaw-install.sh
```

或者整行复制 `curl -sL https://s.zhihai.me/openclaw > openclaw-install.sh && chmod +x openclaw-install.sh && ./openclaw-install.sh`

注意记住你输入或随机生成的 token 。

## 初始化

### 方法一

如果顺利安装完成，接着：

1) 运行 `oclog` 命令，查看运行状态。
2) 新开一个终端窗口（屏幕左滑，点击 New Session），运行 `openclaw setup` 命令 。
3) 运行 `openclaw onboard` 启动服务。这个就和常见的初始化教程说得一样了。不多说，最后一步提示 gateway 启动失败，可以不管，Termux 不支持这个，但前面 `oclog` 能看到服务已经启动了。

### 方法二

如果上面这个看不懂，直接杀掉应用，重启 Termux 应用，再次进入终端界面。

运行 `ocr` 命令（OpenClaw Restart），接着运行 `oenclaw setup`。

![[7a766f2f9e5ce50840dad1267374e815.png]]
运行 ocr 命令后，过一段时间看到的效果（来自 2016年的 OnePlus 2 手机）
## 可能的问题与局限

OpenClaw还在快速更新，不保证脚本针对新版本还能成功运行，届时可能需要相应调整。

相比标准的 OpenClaw 运行环境，使用 Termux 运行 OpenClaw 有一些局限：

1. **性能限制**：安卓设备的硬件资源可能不如 PC，影响 OpenClaw 的运行效率。
2. **稳定性**：Termux 环境可能不如正式的 Linux 发行版稳定，偶尔会出现兼容性问题。
3. **功能缺失**：某些高级功能可能需要额外配置或不被支持。

![[74590364992b496b8dbbfaf93d907f96.png]]

但就尝鲜和玩耍来说，这些限制是可以接受的。更何况，让旧手机变废为宝，不失为一件让人开心的事情。

## 更多可能的玩法

1. **定时任务**：可以设置定时任务，让手机在特定时间自动执行某些任务。
2. **远程控制**：通过网络远程控制手机（安装 `Termux-API` ），实现远程操作。
3. **智能家居集成**：将手机作为智能家居中心的一部分，实现语音控制等。

## 总结

驱动 AI 写这个脚本花了我两个晚上的时间，第一次失败了，本来想放弃。后来不死心，第二天晚上又重来一遍。大部分时间都在解决 Android 兼容性问题。

**核心思路总结为这几句话：**
1. 用 Termux 提供 Linux 环境
2. 修复 OpenClaw 的平台兼容性问题
3. 用 tmux 守护进程，确保服务持续运行
4. 用 termux-wake-lock 防止手机休眠

安装成功之后，记住几个命令就行：
- `ocr` - 重启 OpenClaw 服务
- `oclog` - 查看 OpenClaw 服务状态
- `ockill` - 停止 OpenClaw 服务

如果你有旧手机，不妨让它 Great Again 。👏

安装过程中如果遇到问题，或有改进建议，欢迎反馈。

也可以扫码进群交流：

![[a416b9ca688bec9e83693414c4075eb3.png]]