Title: 用 龙虾🦞 监控 OpenRouter 免费模型上新
Date: 2026-04-24
Category: AI
Tags: AI, OpenRouter, 自动化, 教程
Slug: openrouter-free-model-monitor-lobster
Author: 龙虾

## 1. 痛点：不想天天刷页面薅羊毛

时不时会看到新闻说，又有哪个新模型在 OpenRouter 上提供限时免费体验。前几天打开 OpenRouter，发现某款国产大模型可以免费用。作为一个经常薅免费模型羊毛的人，我的第一反应是——这上新多久了？我怎么才知道？

OpenRouter 是一个 LLM API 聚合平台，汇集了各家大模型，其中不少提供免费额度。问题是，免费模型的上下架没有固定规律：

- **你不知道什么时候会多出一个新模型** —— 可能是限时免费，错过了就没了
- **你不知道哪个模型悄悄下线了** —— 正在用的模型突然不能用了
- **你不知道哪个模型更值得用** —— 免费模型有几十个，质量和速度参差不齐，新上的可能更好

我想第一时间知道，但手动刷网站太累了。OpenRouter 并未提供 RSS 订阅或邮件提醒之类的通知方式。

AI时代了，不能再用手工的笨办法。与其天天刷页面，不如让我的 AI 助手帮我盯着——一旦有新免费模型上线，自动通知我。

## 2. 方案：让 AI 替你盯着

核心逻辑很简单：

1. **定期调用 OpenRouter API**，获取当前所有免费模型列表
2. **与本地记录对比**，找出新增和下架的模型
3. **有变化就通知我**，没变化就静默

本文以轻量级 AI 助手框架 **nanobot**为例。它有一个 **heartbeat 机制**——你可以在 `HEARTBEAT.md` 中定义周期性任务，nanobot 会按配置的间隔（比如每小时一次）自动执行，全程无需人工干预。

其他同类 AI 助手（如 OpenClaw、Hermes Agent）的实现逻辑类似。

## 3. 动手拆解（共四步）

下面这些步骤主要是 nanobot 自己想的。

我把需求用自然语言告诉 nanobot，它自动生成 Python 脚本。

### 3.1 第一步：写个脚本，调 API 拿列表

OpenRouter 提供了公开的模型列表 API：

```
GET https://openrouter.ai/api/v1/models
```

返回的 JSON 中，每个模型有 `id` 和 `pricing` 字段。免费模型的特征是 `pricing.prompt` 和 `pricing.completion` 都为 `"0"`。

nanobot 生成的脚本核心逻辑：

```python
def filter_free_models(models):
    return [
        m for m in models
        if m.get("pricing", {}).get("prompt") == "0"
        and m.get("pricing", {}).get("completion") == "0"
    ]
```

这一步需要 OpenRouter 的 API Key，nanobot 会提示你提供。

如果让我自己想，还真想不到这么优雅的解决方案。我最初的思路是直接抓页面，检查有没有新模型出现——远不如调 API 干净准确。

### 3.2 第二步：存个快照，当对比基准

第一次运行时，nanobot 自动把当前免费模型列表保存为 JSON 文件（如 `config/openrouter_free_models.json`）。下次检查时，它对比这个文件里的内容，看是否有变化。

### 3.3 第三步：配个心跳，让任务自动重复运行

在 nanobot 的 `HEARTBEAT.md` 中添加一行任务：

```markdown
## OpenRouter 免费模型监控
- 检查 OpenRouter 免费模型列表是否有新增（对比 config/openrouter_free_models.json），如有变化通过飞书通知用户
```

配置完成后，nanobot 每次 heartbeat 自动执行：调 API → 对比 → 通知 → 更新快照。

> ⚠️ OpenRouter 的 API 结构和免费策略可能随时调整。如果监控脚本失效，请检查 API 返回的数据格式是否变化。

### 3.4 第四步：坐等通知，新模型到手

配置完成。等通知就行。

## 4. 效果：我收到了什么？

当 OpenRouter 上新免费模型时，我会在飞书收到类似这样的消息：

> 🤖 bot 🆓 OpenRouter 新增免费模型
>
> 🕐 2026-04-23 18:00
> 新增 1 个免费模型，当前共 29 个
>
> **Tencent: Hy3 preview (free)**
> ID: `tencent/hy3-preview:free`
> 模态: text->text｜上下文: 262,144
> 简介: Hy3 Preview is a high-efficiency Mixture-of-Experts model from Tencent designed for agentic workflows and production use...
> [查看详情](https://openrouter.ai/tencent/hy3-preview:free)

不需要主动去查，模型上新第一时间知道。

## 5. 总结：全程没写一行代码

整个方案搭建过程：

1. 把需求用自然语言告诉 nanobot，它生成脚本并配好环境
2. 运行一次，保存当前免费模型列表作为基准
3. 在 `HEARTBEAT.md` 写一句话描述任务

剩下的全自动。

这就是 AI 助手的魅力——你不需要打开编程软件写监控脚本、配置 cron、自己对接通知渠道。把需求说清楚，剩下的它来。

## 6. 附录：手把手配置指南

如果你还不清楚如何让 AI 助手使用 OpenRouter 的免费模型，下面是简单的配置方法。

### 方法一：使用 openrouter/free 路由（推荐）

OpenRouter 提供了免费路由 `openrouter/free`，自动选择当前可用的免费模型之一，无需手动指定模型 ID。

**配置步骤：**

1. 注册 OpenRouter 账号：访问 [openrouter.ai](https://openrouter.ai)
2. 创建 API Key：Settings → Keys → Create Key
3. 在 AI 助手的配置文件中添加：

```json
{
  "api_key": "sk-or-v1-xxxxxxxx",
  "base_url": "https://openrouter.ai/api/v1",
  "model": "openrouter/free"
}
```

**注意事项：**
- 调用时必须在请求头中携带 `HTTP-Referer` 和 `X-Title` 字段，否则返回 402 错误
- 免费路由会智能过滤，只选择支持你所需功能的模型
- 上下文长度支持 200,000 token

### 方法二：直接指定免费模型

在 [OpenRouter 模型列表页](https://openrouter.ai/models) 筛选免费模型，直接指定模型 ID：

```json
{
  "api_key": "sk-or-v1-xxxxxxxx",
  "base_url": "https://openrouter.ai/api/v1",
  "model": "tencent/hy3-preview:free"
}
```

模型 ID 带 `:free` 后缀的是免费模型。目前 OpenRouter 上有数十款免费模型，包括 Google Gemini、Meta Llama、阿里巴巴 Qwen、腾讯混元等。
