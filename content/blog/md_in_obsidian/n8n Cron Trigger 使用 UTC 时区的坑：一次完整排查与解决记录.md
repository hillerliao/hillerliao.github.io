---
title: n8n Cron Trigger 使用 UTC 时区的坑：一次完整排查与解决记录
slug: n8n-cron-trigger-utc-timezone-issue
date: 2026-01-18
description: 详细记录了 n8n Cron Trigger 升级后使用 UTC 时区导致日期错位问题的完整排查过程，包括容器时区确认、Code node 测试、以及最终的三种解决方案。
tags:
    - n8n
    - Cron
    - 时区
    - 自动化
    - Docker
    - UTC
---

## 问题背景

我使用 n8n 做自动化，通过 Cron Trigger，每天**早上 7 点**自动执行一个工作流：
- 抓取 **当天天气预报**
- 获取 **农历日**
- 组合成消息，推送到微信 / 企业微信

N8N 容器启动时已经明确设置：
- `TZ=Asia/Shanghai`
- `GENERIC_TIMEZONE=Asia/Shanghai`

运行多年都没问题。但最近**升级了n8n**之后，出现问题：获取到的是头一天的日期和农历。

## 原因排查

我第一反应是容器的时区没有指定为东八区，
### Code node 中生成的日期慢了一天

工作流中有一个 Code node，用来生成当天日期，后续用这个日期去查农历：

```js
let currentDateTime = new Date();
let year = currentDateTime.getFullYear();
let month = (currentDateTime.getMonth() + 1).toString().padStart(2, '0');
let day = currentDateTime.getDate().toString().padStart(2, '0');

return { currentDate: `${year}${month}${day}` };
```

在 **1 月 18 日早上 7 点（中国时间）** 执行时，得到的却是：

```
20260117
```

直接导致日期、农历错位。

## 二、排查过程

### ✅ 第一步：确认容器时区是否正确

```bash
docker exec -it n8n date
```

输出：

```
Sun Jan 18 22:48:54 CST 2026
```

结论：

✔ Docker 容器时区 **完全正确**

---

### ❌ 第二步：怀疑 TZ / localtime 是否未生效

尝试过：

- 设置 `TZ=Asia/Shanghai`
    
- 设置 `GENERIC_TIMEZONE=Asia/Shanghai`
    
- 挂载 `/etc/localtime`
    

结果：

> **Cron Trigger 仍然使用 UTC**

说明这不是 Docker / Linux 层面的问题。

---

### ❌ 第三步：怀疑是 n8n Code node 的 bug

测试代码：

```js
return { now: new Date().toISOString() };
```

输出：

```
2026-01-18T14:45:18.537Z
```

看起来像是 UTC，但这一步反而帮我确认了关键事实。

---

## 四、真相：这是 n8n 的“设计行为”，不是 Bug

### ⚠️ 核心结论

> **n8n 的 Cron Trigger 永远使用 UTC 进行调度**

这是官方设计选择，原因包括：

- 保证工作流在不同时区、不同服务器上行为一致
    
- 避免夏令时（DST）导致的歧义
    
- 方便在数据库中统一存储时间
    

### 同时要明确三点：

|项目|是否受 TZ / GENERIC_TIMEZONE 影响|
|---|---|
|Docker 容器时间|✅ 是|
|Code node `Date()`|❌ 默认 UTC|
|**Cron Trigger**|❌ 永远 UTC|

也就是说：

> **Cron ≠ 系统时间 ≠ Code node 本地时间**

这是大多数人第一次踩坑的根源。

---

## 五、正确的解决方案

### ✅ 方案一：Cron 时间手动减 8 小时（最推荐）

如果你希望：

> **每天 22:00（中国时间）执行**

Cron 应该写成：

```
14:00 UTC
```

即：

```
0 14 * * *
```

#### 常用对照表：

|中国时间|Cron（UTC）|
|---|---|
|08:00|00:00|
|09:30|01:30|
|12:00|04:00|
|22:00|14:00|

这是 **生产环境最稳妥的做法**。

---

### ✅ 方案二：Code node 中显式指定时区（处理日期）

在 Code node 中，**永远不要**直接用：

```js
getFullYear()
getMonth()
getDate()
```

正确写法：

```js
const tz = 'Asia/Shanghai';
const now = new Date();

const parts = new Intl.DateTimeFormat('en-CA', {
  timeZone: tz,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
}).formatToParts(now);

const map = Object.fromEntries(parts.map(p => [p.type, p.value]));

return {
  currentDate: `${map.year}${map.month}${map.day}`
};
```

### 输出：

```
20260118
```

---

### ✅ 方案三：Cron 高频触发 + 本地时间判断（进阶）

如果你不想心算 UTC：

- Cron：每 5 分钟 / 每 10 分钟
    
- Code node 判断 **中国时间是否满足条件**
    

示例：

```js
const hour = Number(
  new Date().toLocaleString('en-US', {
    timeZone: 'Asia/Shanghai',
    hour: '2-digit',
    hour12: false,
  })
);

if (hour === 22) {
  return [{ run: true }];
}

return [];
```

适合复杂条件调度，但不适合简单定时。

---

## 六、强烈不建议的做法

❌ 依赖容器时区影响 Cron  
❌ 使用 `toISOString()` 生成业务日期  
❌ 在 Code node 中假设 `Date()` 是本地时间  
❌ 试图“修复” n8n 的 Cron 行为

这些都会让问题在将来再次出现。

---

## 七、最佳实践总结（TL;DR）

- **Cron Trigger：永远按 UTC 思考**
    
- **时间展示 / 业务日期：必须显式指定 Asia/Shanghai**
    
- **不要相信默认行为**
    
- 把“时区”当成显式参数，而不是隐含前提
    

如果你的自动化流程：

- 涉及日期边界
    
- 涉及每日任务
    
- 涉及财务 / 日志 / 报表
    

那么这个问题 **迟早会踩**。

早点理解，少掉几个坑。

---

## 八、延伸

后续可以继续深入的点包括：

- n8n 内部是如何存储 Cron 的
    
- `$now` / Expression 的时区规则
    
- 多时区任务如何设计更安全
    

如果你也踩过这个坑，希望这篇记录能帮你节省几个小时的排查时间。