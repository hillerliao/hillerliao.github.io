Title: OpenClaw多Agent配置实战（多BOT版）
Date: 2026-03-25 16:45
Category: 技术教程
Tags: OpenClaw, AI, 多Agent, 飞书, 配置教程
Slug: openclaw-multi-agent-tutorial
Summary: 通过多Agent架构，根据任务复杂度自动路由到不同模型，实现成本优化和专业化分工。

> **懒人方案**：如果不想手动折腾配置文件，可以直接进入 `~/.openclaw` 文件夹，启用 OpenCode，把这篇文章扔给它，让 OpenCode 参照着搞定。你只需要安装OpenCode就行（让OpenClaw帮你安装）。两个工具互相帮忙！

---

## 为什么要多Agent？

最近有一些任务，OpenClaw 处理起来不是很得力，容易出错，不太爽。

- "帮我查一下这个函数怎么用" → 便宜的普通模型能够快速响应，还算不错。
- "帮忙破解这个接口的数据解密方法" → 一般的模型可能就搞不定了，得上更厉害的模型。而更厉害的模型，也就意味着需要更多的钱去购买。

有什么办法能够让我在不同的时候使用不同的模型，既把事办了，也把钱省了呢？

经过一番研究发现，**OpenClaw的多Agent架构完美解决了这个问题**：每个Agent可以绑定不同的模型，通过路由规则自动分配任务。

---

## 最终效果

配置完成后，我的系统是这样的：

| Agent | 模型 | 用途 | 成本 |
|-------|------|------|------|
| main | MiniMax M2.7 | 日常对话、简单编码 | 低 |
| code-reviewer | GPT 5.4 Pro | 代码审查、安全分析 | 高 |

用户通过不同的飞书机器人发起请求，OpenClaw自动路由到对应的Agent。

---

## 原理图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户消息                                │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                          │
│                  (根据Bindings路由)                           │
└─────────────────────────────────────────────────────────────┘
                     │                    │
                     ▼                    ▼
     ┌───────────────────────┐  ┌───────────────────────┐
     │   飞书机器人1(default)  │  │ 飞书机器人2(code-reviewer)│
     └───────────────────────┘  └───────────────────────┘
                     │                    │
                     ▼                    ▼
     ┌───────────────────────┐  ┌───────────────────────┐
     │     main Agent        │  │  code-reviewer Agent  │
     │   模型: MiniMax       │  │   模型: GPT 5.4 Pro   │
     │   成本: 低            │  │   成本: 高            │
     └───────────────────────┘  └───────────────────────┘
```

---

## 环境准备

### 1. 确认OpenClaw版本

```bash
openclaw --version
```

确保版本 >= 2026.3.x

### 2. 获取OpenCode Zen API密钥

访问 [https://opencode.ai/auth](https://opencode.ai/auth)，注册并获取API密钥。

> GPT 5.4系列模型通过OpenCode Zen提供。

### 3. 确认飞书扩展

本文使用OpenClaw内置的飞书扩展 **`feishu`**（路径：`openclaw/extensions/feishu`），安装方便。

```bash
# 查看已启用的插件
openclaw plugins list
```

期望输出中应包含：
```
feishu: enabled
```

### 4. 准备飞书应用

需要两个飞书应用：
- **应用1**：已有的飞书机器人（用于main Agent）
- **应用2**：新建的代码审查机器人（用于code-reviewer Agent）

在 [飞书开放平台](https://open.feishu.cn/) 创建新应用，获取 `App ID` 和 `App Secret`。

> 飞书应用需要开启以下权限：`im:message`、`im:message:send_as_bot` 等。最好是把能开的权限都开上。

---

## 实战步骤

### Step 1：查看当前配置

先了解一下现有的配置结构：

```bash
# 查看当前Agent列表
openclaw agents list
```

输出：
```
Agents:
- main (default)
  Model: minimax/MiniMax-M2.7
  Routing: default
```

查看配置文件：

```bash
# 配置文件位置
cat ~/.openclaw/openclaw.json
```

当前只有 `main` 一个Agent，使用MiniMax模型。

---

### Step 2：添加OpenCode Zen模型提供商

> 这一步可以通过``openclaw configure``命令完成，模型配置步骤有OpenCode选项，更不容易出错。

编辑 `~/.openclaw/openclaw.json`，在 `models.providers` 中添加GPT 5.4系列模型：

```json
{
  "models": {
    "providers": {
      "minimax": {
        "baseUrl": "https://api.minimaxi.com/anthropic",
        "api": "anthropic-messages",
        "models": [
          {
            "id": "MiniMax-M2.7",
            "name": "MiniMax M2.7"
          }
        ]
      },
      "opencode-zen": {
        "baseUrl": "https://opencode.ai/zen/v1",
        "api": "openai-completions",
        "authHeader": true,
        "models": [
          {
            "id": "gpt-5.4",
            "name": "GPT 5.4",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 200000,
            "maxTokens": 8192
          },
          {
            "id": "gpt-5.4-pro",
            "name": "GPT 5.4 Pro",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  }
}
```

在 `agents.defaults.models` 中添加模型别名：

```json
{
  "agents": {
    "defaults": {
      "models": {
        "minimax/MiniMax-M2.7": {
          "alias": "MiniMax"
        },
        "opencode-zen/gpt-5.4-pro": {
          "alias": "GPT 5.4 Pro (Code Review)"
        }
      }
    }
  }
}
```

---

### Step 3：添加OpenCode Zen API密钥

编辑 `~/.openclaw/agents/main/agent/auth-profiles.json`：

```json
{
  "version": 1,
  "profiles": {
    "minimax:cn": {
      "type": "api_key",
      "provider": "minimax",
      "key": "your-minimax-api-key"
    },
    "opencode-zen:default": {
      "type": "api_key",
      "provider": "opencode-zen",
      "key": "your-opencode-zen-api-key"
    }
  }
}
```

---

### Step 4：创建code-reviewer Agent

使用CLI命令一键创建：

```bash
openclaw agents add code-reviewer \
  --workspace ~/.openclaw/workspace-code-reviewer \
  --model opencode-zen/gpt-5.4-pro \
  --non-interactive
```

这条命令会自动创建：
- 独立的工作空间目录：`~/.openclaw/workspace-code-reviewer`
- 独立的Agent配置目录：`~/.openclaw/agents/code-reviewer/agent`
- 独立的会话存储：`~/.openclaw/agents/code-reviewer/sessions/`

---

### Step 5：定义Agent人格

每个Agent都可以有独立的人格配置。

**AGENTS.md** (`~/.openclaw/workspace-code-reviewer/AGENTS.md`)：

```markdown
# Code Review Agent

你是一个专门的代码审查助手，使用GPT 5.4 Pro进行深度代码分析。

## 职责
- 代码质量审查
- 潜在Bug识别
- 性能优化建议
- 安全性检查
- 最佳实践建议

## 审查标准
1. 代码可读性
2. 错误处理
3. 性能考虑
4. 安全性
5. 测试覆盖

## 输出格式
- 总体评分（A-F）
- 问题列表（文件:行号）
- 严重程度（高/中/低）
- 建议修复方案
```

**SOUL.md** (`~/.openclaw/workspace-code-reviewer/SOUL.md`)：

```markdown
# Code Review Agent Soul

你是一个经验丰富、耐心细致的代码审查专家。

## 性格
- 严谨但友好
- 注重细节
- 建设性而非批评性

## 语气
- 专业但亲切
- 清晰简洁
- 避免技术术语滥用
```

---

### Step 6：配置飞书机器人

在 `openclaw.json` 的 `channels` 部分配置飞书多账户：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "accounts": {
        "default": {
          "appId": "cli_已有应用ID",
          "appSecret": "已有应用Secret"
        },
        "code-review": {
          "appId": "cli_新应用ID",
          "appSecret": "新应用Secret"
        }
      },
      "connectionMode": "websocket",
      "domain": "feishu",
      "groupPolicy": "open"
    }
  }
}
```

> **说明**：`accounts` 是多账户配置的关键字段，每个账户对应一个飞书应用。`default` 账户用于main Agent，`code-review` 账户用于code-reviewer Agent。

---

### Step 7：配置路由绑定

在 `openclaw.json` 中添加Bindings：

```json
{
  "bindings": [
    {
      "agentId": "code-reviewer",
      "match": {
        "channel": "feishu",
        "accountId": "code-review"
      }
    }
  ]
}
```

**路由规则解读**：
- 当消息来自 `feishu` 渠道
- 且账户为 `code-review`（即新创建的飞书机器人）
- 则路由到 `code-reviewer` Agent

---

### Step 8：重启网关使配置生效

```bash
openclaw gateway restart
```

---

### Step 9：验证配置

```bash
openclaw agents list --bindings
```

期望输出：
```
Agents:
- main (default)
  Model: minimax/MiniMax-M2.7
  Routing: default

- code-reviewer
  Model: opencode-zen/gpt-5.4-pro
  Routing rules:
    - feishu accountId=code-review
```

检查频道状态：

```bash
openclaw channels status
```

期望看到两个飞书账户都在运行：
```
- Feishu default: enabled, configured, running
- Feishu code-review: enabled, configured, running
```

---

## 测试效果

### 测试1：日常编码（走main Agent，MiniMax模型）

通过第一个飞书机器人发送：
```
帮我写一个Python函数，计算斐波那契数列
```

MiniMax快速响应，成本低。

### 测试2：代码审查（走code-reviewer Agent，GPT 5.4 Pro）

（简单例子示意，非大模型真实输出）

通过第二个飞书机器人发送：
```python
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE id = " + user_input
    result = db.execute(query)
    return result
```

GPT 5.4 Pro 深度分析，输出：
```
🚨 严重问题：SQL注入漏洞

文件位置: 代码片段:2
问题: 用户输入直接拼接SQL查询
严重程度: 高
建议修复: 使用参数化查询

修复代码:
```python
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE id = %s"
    result = db.execute(query, (user_input,))
    return result
```


---

## 总结

多Agent架构的核心价值：

1. **成本优化**：简单任务用便宜模型，复杂任务用强模型
2. **专业化**：每个Agent可以定制专属的人格和规则

**好钢用在刀刃上**，让每个模型做最擅长的事。
