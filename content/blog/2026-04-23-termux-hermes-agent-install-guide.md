---
title: 不仅龙虾，旧手机也能跑 Hermes Agent（安装实录）
date: 2026-04-23
modified: 2026-04-23
tags:
    - hermes agent
    - termux
    - android
    - self-hosted
    - ai agent
category: blog
slug: termux-hermes-agent-install-guide
authors: hillerliao
description: 记录一次在安卓手机上，通过 Termux 部署 Hermes Agent 的实际过程。
---

## 需求背景

近期 AI Agent 相关项目关注度较高，例如在"龙虾（OpenClaw）"之后，一些类似工具，尤其是 Hermes Agent 开始被更多人尝试。就像 OpenClaw，除了在电脑或服务器上运行，这类工具基本都可以在移动设备上部署，只是可能有一些细微差异需要注意。

手机具备以下特点：

- 长时间在线
- 自带网络环境
- 可作为低成本运行节点

这里记录一次在**安卓手机上，通过 Termux 部署 Hermes Agent** 的实际过程。

## 前置条件

开始之前，需满足：

- 一部安卓手机（建议 RAM ≥ 4GB）
- 可能需要魔法上网
- 安装 Termux App（建议 F-Droid 版本）

## 什么是 Termux

Termux 是一个在安卓系统上提供 Linux 命令行环境的应用，可以执行常见的包管理、编译和脚本操作。安装后可以通过 `pkg` 管理软件包。

## 方法一：一键安装

在 Termux 中下载脚本并执行安装：

```bash
curl -O https://raw.githubusercontent.com/hillerliao/termux-hermes-agent/main/install-termux.sh
bash install-termux.sh
```

该脚本会执行以下操作：

- 检测运行环境
- 安装系统依赖
- 安装 Python 环境
- 克隆 Hermes Agent 仓库
- 安装 Python 依赖

> 执行过程中会出现编译输出（Rust / C 扩展）。⚠️ 视手机配置和网络情况，执行过程可能非常耗时，下文方法二也是如此。

## 方法二：手动安装

如需手动执行，或一键脚本运行异常，可按以下步骤操作。

### 1️⃣ 安装系统依赖

```bash
pkg update
pkg install -y git build-essential clang cmake rust python
```

用于安装编译和运行所需的基础环境，包括：

- git（用于克隆项目代码）
- Python 运行环境
- C / C++ 编译工具链（clang）
- Rust 编译环境（部分依赖需要）

### 2️⃣ 设置 ANDROID_API_LEVEL

```bash
export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)
```

该变量用于告知编译工具当前安卓系统的 API 等级，部分依赖在编译时会用到。可写入：

```bash
echo 'export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)' >> ~/.bashrc
```

用于在每次启动 Termux 时自动生效。

### 3️⃣ 克隆仓库

```bash
git clone https://github.com/nousresearch/hermes-agent.git ~/hermes-agent
```

将 Hermes Agent 源代码下载到本地目录，用于后续安装。

### 4️⃣ 安装 Python 依赖

```bash
cd ~/hermes-agent
pip install -e .
```

安装项目所需的 Python 依赖，并以"开发模式"安装当前项目，使 `hermes` 命令可用。

> 说明：仓库自带的 `install.sh` 面向标准 Linux 环境，Termux 中不使用。

### 5️⃣ 初始化配置

```bash
hermes setup
```

运行交互式配置向导，用于设置：

- 模型 API Key
- 基本运行参数

配置文件默认生成在：`~/.hermes/config.yaml`

> ⚠️ 输入大模型的 API Key 时可能看上去没反应，但实际上已经输入成功，继续回车下一步就行。

### 6️⃣ 验证安装

```bash
hermes --version
```

用于确认 Hermes Agent 已正确安装，并可正常调用。

## 常用命令

```bash
hermes --version
hermes setup
hermes
```

## 后台运行说明

- 设备需保持供电
- 关闭系统电池优化
- 避免 Termux 被系统回收

## 功能使用

安装完成并配置后，可实现：

- 通过消息平台与 Agent 通信
- 执行定时任务
- 接入扩展能力
- 执行基础自动化任务

## 已知限制

- 性能受限于手机硬件
- 部分依赖在 ARM 架构不可用
- 安装过程包含编译步骤，耗时较长

## 总结

该过程本质为：

- 使用 Termux 提供 Linux 环境
- 在本地安装 Hermes Agent
- 通过配置实现运行

适用于在移动设备上进行基础 Agent 部署测试。
