---
title: 免装单词App，在 iPhone 锁屏随机显示单词
date: '2024-10-17 23:23'
modified: '2024-10-17 23:23'
tags: 小工具,
category: blog
slug: randomly-show-a-word-on-ios-lockscreen
authors: hillerliao
summary: 免装单词App，在iPhone锁屏随机显示单词！这样，你每天解锁手机的时候，都能顺便瞟一眼单词，日积月累，词汇量自然水涨船高！
---


亲爱的朋友们，你是否曾经为背单词而烦恼？是否觉得用手机时有很多零碎时间没有利用上？

今天，我要给大家带来一个神奇的方法——免装单词App，在iPhone锁屏随机显示单词！这样，你每天解锁手机的时候，都能顺便瞟一眼单词，日积月累，词汇量自然水涨船高！

有些背单词软件可能有提供这种功能，但通常有一些问题：单词列表不受自己控制，显示的内容无法自定义，搞不好还收费。

今天我就来给大家介绍一种免费实现自定义锁屏单词小组件的办法。

## 需要的工具  

- iPhone；
- Scriptable

Scriptable是一款iOS应用程序，允许用户使用JavaScript自动化构建和自定义桌面或锁屏小部件。

得益于优秀的 Scriptable（苹果应用商店的开发者工具类排名前十），我们只需要写一点简单的基于JavaScript的脚本，就能干很多事情。

## 脚本代码

借助ChatGPT，把需求描述一番，很快就有了如下脚本：

```
// 指定RSS源的URL
const url = "https://politepol.com/fd/f1NYOd8OAcsA.xml";

// 使用fetch来获取RSS数据
let req = new Request(url);
let rssData = await req.loadString();

// 输出RSS数据到日志
console.log(rssData);

// 使用正则表达式解析RSS中的内容，ChatGPT给的参考代码中变量名为title，这里实际选择读取摘要。
let titles = [];
let regex = /<description>(.*?)<\/description>/g;
let match;
while ((match = regex.exec(rssData)) !== null) {
    titles.push(match[1]);
}

// 创建一个Widget展示RSS摘要
let widget = new ListWidget();
widget.backgroundColor = new Color("#1a1a1a");

// 如果解析到的摘要为空，显示占位符
if (titles.length === 0) {
    let placeholder = widget.addText("No RSS data available");
    placeholder.textColor = Color.white();
    placeholder.font = Font.systemFont(12);
} else {
    // 添加RSS摘要到Widget
    for (let i = 0; i < Math.min(titles.length, 3); i++) {
        let title = titles[i];
        let text = widget.addText(title);
        text.textColor = Color.white();
        text.font = Font.systemFont(12);
        widget.addSpacer(4);
    }
}

// 设置Widget定期刷新，设为30分钟。
widget.refreshAfterDate = new Date(Date.now() + 1000 * 60 * 30);

// 预览Widget
if (config.runsInWidget) {
    Script.setWidget(widget);
} else {
    widget.presentMedium();
}

Script.complete();

```

具体代码是什么意思，我们就不用管太多了，只需要注意替换数据源地址就行。上述示例的 RSS 地址 `https://politepol.com/fd/f1NYOd8OAcsA.xml` 系通过名为 [politepol](https://politepol.com/) 的网页生成RSS服务将 `https://pyrss.vercel.app/word/jlpt2`页面的日语N2单词转换而成。如果想要英文单词，请联系我。

你可以在Scriptable上先运行脚本以验证数据是否获取成功，然后再进行下一步的设置。

## 设置为锁屏组件

接下来，开始编辑锁屏界面。添加 Scriptable 小组件，并选取刚才添加到 Scriptable 的脚本，即告完成。

![](https://fastly.jsdelivr.net/gh/henrylovemiller/img@main/1727536737513%E9%94%81%E5%B1%8F%E5%8D%95%E8%AF%8D.png)

## 更多可能

也可以把小组件钉在手机桌面上。相比锁屏界面，桌面组件效果对样式要求更高，可以通过修改脚本中的样式代码让桌面小组件变得更加漂亮。

此外，不仅仅是单词，天气、热搜、格言、倒数日之类的小组件，都可以借助Scriptable实现，核心就是换个数据和显示样式，本质都一样。只要你有想法，借助ChatGPT大概率能实现，一次不行，再试一次。

如果觉得这篇文章有意思，对你有启发，欢迎点个赞。
