---
title: 如何发布 pelican 到 github pages
date: '2021-12-26 17:32'
modified: '2021-12-26 17:32'
tags: pelican,
category: blog
slug: publish-pelican-to-ghp
authors: hillerliao
summary: Short version for index and feeds
---

去年决定将静态博客的生成工具从 hexo 改成基于 Python 的 pelican，初次搬运之后就没在动过，以至于已经忘了该如何更新。

为避免再次遗忘，现决定将发布过程写下来。  

## 第一次配置环境

```
# 进入项目根目录  
pipenv shell  
pip install pelican markdown

# change theme Enter prject home directory, run 
git clone https://github.com/getpelican/pelican-themes.git

```


```
# generate html pages
pelican content

# preview 
pelican -l -b 0.0.0.0 -p 8082 -r

# publish to github pages
pip install ghp-import=2.1.0
ghp-import output -b gh-pages
github push origin gh-pages
```