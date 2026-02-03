---
title: Vercel 环境无法正常请求带中文字符URL的问题排查
urlname: fix-chinese-characters-included-url-bug-in-vercel
date: '2022-8-11 21:12:57 +0800'
tags:
  - 运维
categories:
  - 运维
---

## 问题描述
利用 [RSSHub-python](https://github.com/hillerliao/RSSHub-python) 项目抓取[爱思想](https://www.aisixiang.com/)网站搜索结果列表生成 RSS 时，在 [Vercel](https://vercel.com/) 环境下，关键词为英文时一切正常，关键词为中文时无法获取到结果。
## 问题分析
根据第一版程序，请求`https://pyrsshub.vercel.app/aisixiang/search/author/%E9%83%91%E6%B0%B8%E5%B9%B4`得到的HTML 源码`<title><![CDATA[%E9%83%91%E6%B0%B8%E5%B9%B4 - author搜索 - 爱思想]]></title>`可以看出，RSS 地址中的中文字符在 HTML 源码没有正常显示，还是 urlencode之后的状态。
第一版本[程序](https://github.com/hillerliao/RSSHub-python/commit/cfcb04afa116941292a1bddab03cfbad4fde59da)通过以下代码直接将URL 中的中文字符转换为为GBK编码的字符。
```python
from urllib.parse import quote
keywords_gbk = quote(keywords, encoding='gbk')
```
然后将上述转换后的字符拼成目标网站的 URL 供爬虫发送请求之用。
程序在本地、docker 上运行，都没有问题，但在 vercel.app 环境中不灵。
具体原因没搞懂，也不方便调试。结论就是： vercel.app 的环境不支持 urlencode 过的字符串直接urlencode为 gbk 字符串，需要先解码再编码。
## 查找方案
先解码再编码的解决方案：
`rss 地址中的中文字符 → urldecode 为 utf-8字符 → urlencode 为 gbk 字符`
增加中间这一步，兼容 vercel.app 环境。
**编码**：一般来说，URL只能使用英文字母、阿拉伯数字和某些标点符号，不能使用其他文字和符号。如果URL中有汉字，就必须编码（`urlencode`）后使用。这一步由浏览器完成。
**解码**：当urlencode之后的字符串传递到后端之后，Flask 响应函数需要进行解码（`urldecode`），可以用 Python 库`urllib.parse` 的`unquote`函数进行解码。
**编码**：接着，将解码后的字符，按照目标网站指定的字符集进行编码（`urlencode`），可以用`quote`方法实现。
具体到爱思想搜索结果列表页，为什么确定用的是gbk 字符来编码？`https://www.aisixiang.com/data/search.php?keyWords=%D1%D6%D1%A7%CD%A8&searchfield=author` 属于其他页面搜索框的 Get 方法触发的请求，URL包含汉字，这时的URL编码方法由网页的编码决定，也就是由HTML源码中字符集的设定决定。 查看 HTML 源码 `<meta http-equiv="Content-Type" content="text/html; charset=gbk" />`得知，所发请求必须是GBK 编码的 URL。
[最终程序](https://github.com/hillerliao/RSSHub-python/commit/53e055637a85191cf88987740eeedb7bdb8204af)修改为：
```python
from urllib.parse import quote, unquote
keywords = unquote(keywords,encoding='utf-8') # 或者用 gbk 字符集解码
keywords_gbk = quote(keywords, encoding='gbk')
```
以字符`郑永年`为例：
```python
from urllib.parse import quote, unquote

str_urlencoded = '%E9%83%91%E6%B0%B8%E5%B9%B4' 
str_utf8_decoded = unquote(str_urlencoded, encoding='utf-8')
str_gbk = quote(str_utf8,encoding='gbk')
str_gbk2 = quote(str_urlencoded, encoding='gbk')

print('按 utf8 解码结果：', str_utf8_decoded)
print('按 gbk 编码结果：',str_gbk)
print('urlencoded字符直接按gbk编码结果：', str_gbk2)
```
运行结果：
```python
按 utf8 解码结果： 郑永年
按 gbk 编码结果： %D6%A3%D3%C0%C4%EA  （此为需要的结果）
urlencoded 字符直接按gbk编码结果： %25E9%2583%2591%25E6%25B0%25B8%25E5%25B9%25B4 （在 vercel 环境出错的结果）
```
## 后续工作
需要再次研究Vercel环境下怎么调试的问题，提高问题排查效率。
## 参考资料

- [关于URL编码 - 阮一峰的网络日志](https://www.ruanyifeng.com/blog/2010/02/url_encoding.html)
- [Python菜鸟晋级11----urlencode与unquote_翻滚吧挨踢男的博客-CSDN博客](https://blog.csdn.net/a359680405/article/details/44857359)
