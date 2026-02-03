---
title: 尝试让 Pelican 博客的部分发布步骤自动化
date: '2023-06-22 20:33'
modified: '2023-06-22 20:33'
tags: pelican,
category: blog
slug: automated-pelican-publishment
authors: hillerliao
summary: 尝试让 pelican 发布博客自动化，为此折腾了一天，几点收货。 
---

个人独立博客上最新一篇文章出现烂图，严重影响站点形象，而且持续了好长一段时间没有修复。图床用的是腾讯的某个服务，后来不让我的站点引用了。我早就忘了具体通过哪个图床工具上传的。

## 操作繁琐 修改动力不足

为什么迟迟不修复？ 

我的个人博客用 Pelican 生成，静态文件托管在 Github Pages，操作过程大致为：

- 本地添加 Markdown 文件；
- 手动运行命令生成 HTML 静态文件；
- 运行命令将静态文件推送到 Github 仓库的 gh-page 分支。

这一顿操作太麻烦，导致我对更新博客有所抵触。

今天端午节，决定花点时间让上述步骤半自动化。没想到折腾了一天才搞定。

为了让这一天变得更有价值一点，稍作记录，顺便执行 push 触发一下自动更新的过程。

## 走了一些弯路

耗时太多主要是由于走了一些弯路，碰到好几个障碍：

- 将 Github 仓库拉到本地，项目内的主题文件夹内容为空。经分析，问题出在引用其他仓库作为子模块。为让子模块文件夹内容出现，花了很大力气才搞定。直到现在，对Git子模块的理解还是云里雾里。

- 运行 Github Workflow 报错，说是主题文件没找到。尝试修改别人的 Github Workflow Action ，加入安装主题的命令，然后尝试在 workflow里使用。但发现需要发布到 Marketplace 才行。 思路不对，我的做法是硬编码了，fork 之后的修改不合理。明明知道不合理的做法还是花了大力气尝试。进行一项尝试前尽量多花点时间评估方案的合理性。

- 对 Pelican 配置文件不够熟悉，折腾了大半天才知道配置项 theme 的值可以是整个路径，之前以为必须是路径的最后一节，导致使用时以为也必须通过pelican-themes 命令安装主题才能添加主题文件。 技术选型需要尽可能先对官方文档读一遍，并找一些别人的操作案例多看，然后再自己动手。

- 找 [Workflow 模板](https://github.com/rehanhaider/pelican-to-github-pages/tree/main)时一开始找的是 Stars 数更少的一个，里面用到的一个关键 Action [源代码](https://github.com/rehanhaider/pelican-to-github-pages/blob/main/entrypoint.sh)读起来不太好理解，后来找了另外一个模板，所引用的 [Action](https://github.com/marketplace/actions/github-pages-pelican-build-action) 实现思路和我自己理解的更接近，借助 Codium 进行[源代码](https://github.com/nelsonjchen/gh-pages-pelican-action/blob/master/entrypoint.sh)解读，基本理解了过程。它将生成的 output 作为仓库推送到 gh-page 分支。 当然前者对我还是有价值的， 因为它指定了 submodule相关的操作。

## 意外的收获

折腾过程中也算是有几点意外收获：

- Git 仓库内子模块又是一个仓库的时候，该怎么做才能在 Clone 时子模块的内容也能同时克隆下来。`--recursive` 参数能解决这个问题。

- Github Workflow 的配置文件里`run`可以直接运行指定的脚本文件。其实别人的 Action 最核心的就是一个shell脚本文件。以后如果想在 workflow 里运行自有脚本，可以尝试该功能。

- 实际感受了 [Codium](https://www.codium.ai/) 这个工具在辅助阅读代码时的便利。

- 基于 pelican 生成的静态博客如何更新到 github Pages？还有一个方法是借助 git hook。在执行 push 前触发运行指定脚本。[参考案例](https://nekrasovp.github.io/pelican-github-script-automation.html)

## 参考资料

- 通过 [How to use Pelican on GitHub Pages Gittip](https://gist.github.com/JosefJezek/6053301)  发现 `theme` 配置项可以填入整个路径。
- [Move blog to github and automate deploying with git hooks - Data driven](https://nekrasovp.github.io/pelican-github-script-automation.html)
