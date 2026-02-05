---
title: 如何通过IB模拟账号体验程序化交易
slug: gc9osg
date: '2017-08-24 19:57:57 +0800'
tags:
  - 证券
categories:
  - 证券
---

## 所需工具

- IB 账号信息
  - 通过老虎证券获取 IB 账号和密码
  - 登录 IB 后台，申请 [IB 模拟交易账号](https://www.interactivebrokers.com/en/software/allocationfunds/topics/papertrader.htm)
- 抓包
  - 安卓本地抓包工具 [HttpCapture](https://github.com/JZ-Darkal/AndroidHttpCapture)
  - 包文件解析工具 [Fiddler](http://www.telerik.com/download/fiddler)
- IB API for Python
  - [IB 官方 API 文档](https://interactivebrokers.github.io/tws-api/classIBApi_1_1Contract.html#gsc.tab=0)
  - [IbPy 第三方 Python API](https://github.com/blampe/IbPy)
    - [入门教程](https://valiant-falstaff.github.io/IbPy-Getting-Started/)
    - [下单 DEMO](https://www.quantstart.com/articles/Using-Python-IBPy-and-the-Interactive-Brokers-API-to-Automate-Trades)
- 其他信息
  - [TWS 下载地址](https://www.interactivebrokers.com/en/index.php?f=16040)
  - [科学上网](https://github.com/getlantern/forum/issues/833)
