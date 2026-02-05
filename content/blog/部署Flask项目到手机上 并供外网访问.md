---
title: 部署Flask项目到手机上 并供外网访问
slug: deploy-flask-project-on-android
date: '2021-11-29 21:03:57 +0800'
tags:
  -  教程
categories:
  - 教程
---

_为什么写这篇文章？本需求的实现将之前折腾的几个服务综合起来，链条比较长，记录之，备忘。_
## 需求缘起

有一个抓取微信公众号文章生成 RSS 地址的 Flask 项目RSSHub-python，本地运行没什么问题，一旦部署到服务器上，秒秒钟被数据源网站搜狗给封杀了。

从两种环境的不同结果来看，本地运行没有问题可能是因为本地出口 IP 没有被封杀。顺着这个思路，如果把服务部署在本地，并保证持续不断地运行，即可避免被封杀的悲剧。

但本地化部署需要解决被外网访问的问题。电脑不适合一直开着，购买树莓派之类的硬件设备需要花钱，而且过往经历告诉我，树莓派大部分时候只是用来吃灰。综合考虑，我决定用闲置的安卓机OnePlus 2作为服务器运行服务，还能省省电。而要让外网能访问，可以借助内网穿透来实现。

简单说，需要准备一台OS版本至少在6.0以上的Android手机。本文以 Android 版本为 10的Redmi 10X 为例进行介绍。

## 部署方案
![image.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1637474979948-88ed5582-7cad-4b70-ad69-fd8e83e9eea3.png#height=440&id=uf821016d&originHeight=880&originWidth=1539&originalType=binary&ratio=1&rotation=0&showTitle=false&size=96230&status=done&style=shadow&title=&width=769.5)
我实际的部署方案如上图所示，用到了几个第三方服务，除了阿里云服务器，其他都是免费就能搞定。
关键点：

- 借助名字叫做 Aid Learning 的安卓 App 作为服务器环境，在服务器内部署 Flask 项目，并用 Supervisor 保证服务运行的稳定性；
- 然后借助花生壳内网版作内网穿透，让服务支持外网访问；
- 由于公司网络禁用了花生壳的服务，需要借助SS服务作为正向代理，通过 SS 客户端将访问花生壳的服务转换为访问阿里云服务器。如果本地网络不禁用花生壳内网穿透服务，这一步可以省略，一分钱都不用花。
## 配置「服务器」Aid Learning

要 Android 变成服务器，我们需要借助一个叫做「Aid Learning」的 App（最新版已更名为 AidLux ，查找网络资料时两个关键词都可以试试），可以从[官网](http://www.aidlearning.net/)下载。撰写本文时一开始想用[1.0a](https://www.aidlux.com/apk/AidLux_1.0a.apk)，结果遇到各种坑，换回0.86b2f4版本（可以通过酷安下载历史版本）。

安装成功后参考教程进行一些[设置](https://dontkillmyapp.com/xiaomi)，包括开启自动启动、常驻后台等，以确保App能持续在后台运行。

或者安装 [Termux](https://termux.com/) App 也可以达到同样目的。Termux 的优点是环境干净，占用存储空间小，自己想装什么就自行安装；缺点是需要自行配置各种环境依赖，配置过程往往会碰到各种各样的依赖问题，掉进坑里的感觉会把人逼疯。可以把App理解为一台 Linux 服务器，两个 APP 好比是Ubuntu 和Arch Linux之别。
![20211121_222306.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1637505262582-a9c92bec-008a-47d0-9e18-c06c0f3ae0b2.png#height=439&id=fi2tX&originHeight=994&originWidth=462&originalType=binary&ratio=1&rotation=0&showTitle=false&size=1836966&status=done&style=stroke&title=&width=204) 
上图：手机号登录，省得以后打开APP时老提示登录。当然这个步骤不是强制的，可以选择跳过。

首次运行APP 时，由于初始化任务的执行，会请求网络下载一些东西，速度比较慢，可能耗时数分钟。如果需要节省流量，记得在 WIFI 环境下操作。
![image.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1637505980097-2aa0a7c7-a21f-44d4-a55a-57dd84dd146b.png#height=440&id=ue7b0ca5b&originHeight=880&originWidth=396&originalType=binary&ratio=1&rotation=0&showTitle=false&size=150917&status=done&style=none&title=&width=198)
默认登录的是 root 用户，未设置密码，可以设置一个 root 用户的密码：打开 APP 内的终端，切换到全屏模式，输入命令 `passwd root`，按界面提示输入两次密码，设置成功。
![image.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1637506748306-153cc560-5584-4e71-a92f-4c6e276995e7.png#height=440&id=u401acc46&originHeight=880&originWidth=396&originalType=binary&ratio=1&rotation=0&showTitle=false&size=78958&status=done&style=none&title=&width=198)
为方便输入命令行命令，可以通过电脑远程访问服务器(Aidlux)：打开服务器上的终端，输入命令 `ifconfig` ，确认服务器的 ip 地址，如我的手机为 172.16.99.125。

保证手机与电脑在同一个WIFI 网络，通过电脑终端远程登录该服务器，注意端口为 **9022**。

```
ssh demo@192.168.1.9 -p 9022
# 密码为demo
```

更新软件包列表，并安装一些常用工具，如 git 等。

```bash
apt update
apt install git
```
## 部署项目
### 生成 ssh 密钥
获取项目代码拉取权限
```bash
# 生成密钥 ssh-keygen
ssh-keygen
cd /root/.ssh
# 复制 id_rsa.pub 文件中的字符。
# 将公钥添加到 github.进入 https://github.com/settings/keys，
# 创建新的 SSH key，填入刚才复制的公钥字符。 
```
### 拉取项目代码
```bash
# 回到服务器，拉取项目代码
cd /opt
git clone git@github.com:hillerliao/RSSHub-python.git
```
### 本地测试运行
```bash
# 进入项目文件夹
cd /opt/RSSHub-python

# 修改pip镜像源
mkdir ~/.config/pip
touch ~/.config/pip/pip.config

# 修改 pip.config 内容为
```pip.config内容
[global]
index-url = https://mirrors.aliyun.com/pypi/simple
```

# 安装 pipenv。也可以用 apt install pipenv 安装，但版本比较旧
pip install pipenv 

```
# 安装
whereis pipenv 
# 得到 /usr/local/bin/pipenv
# 创建软连接
ln -s /usr/local/bin/pipenv /usr/bin/pipenv
```

# 创建Python 虚拟环境。
# 我用Android 11的红米手机尝试会报错，用Android 6 的 OnePlus 2手机不报错
# 提示「OSError: Cannot find path to android app folder」
cd /opt/RSSHub-python
pipenv install

# 记下虚拟环境位置，后续 uwsgi 配置文件里会用到
# /root/User/demo/.local/share/virtualenvs/RSSHub-python-e4f4sLQi


# 验证本地运行是否正常
flask run 

# 如果确实依赖包，就手动安装，如 dotenv
pip install python-dotenv
```
## 配置 uwsgi 服务
### 安装 uwsgi
```bash
# 需要在root用户下运行
pip install uwsgi
```
### uwsgi 配置文件
```bash
# uwsgi --ini {current_file_path_and_name}
[uwsgi]
http = 127.0.0.1:5000
processes = 4
threads = 2
; plugins = python3
master = true
# 启动主进程，来管理其他进程，其它的uwsgi进程都是这个master进程的子进程，如果kill这个master进程，相当于重启所有的uwsgi进程。

chdir = /opt/RSSHub-python
# 在app加载前切换到当前目录， 指定运行目录 

wsgi-file = wsgi.py
#virtualenv = /root/.local/share/virtualenvs/RSSHub-python-e4f4sLQi
virtualenv = /usr/bin/python
# pythonpath = /opt/RSSHub-python
#上面的pythonpath需要换成刚才你自己创建的应用的目录
# module = rsshub
callable = app
memory-report = true
#py-autoreload = 1 ##监控python模块mtime来触发重载 (只在开发时使用)

#daemonize = /var/log/uwsgi/rsshub-python.log
# 使进程在后台运行，并将日志打到指定的日志文件或者udp服务器

touch-reload = /opt/RSSHub-python
# 表示要监听的文件路径，当要监听的文件路径下的文件发生变化的时候自动重新加载服务。

lazy-apps=true
# 在每个worker而不是master中加载应用

vacuum = true
# 当服务退出的时候自动删除unix socket文件和pid文件。
```
## 配置Nginx
### 安装Nginx 
```
apt install nginx

#查看Nginx状态
service nginx status
```
### Nginx配置文件

创建配置文件  `touch /etc/nginx/conf.d/rsshub.conf`，通过 nano 命令编辑该文件。具体配置如下：

```bash
server {
      listen 9080;
      server_name [域名];
      location / {
              include uwsgi_params;
              #uwsgi_pass 127.0.0.1:5000;
	      			proxy_pass http://127.0.0.1:5000;
              uwsgi_read_timeout 120;
      }
}
```

保存好配置文件，并进行测试  `service nginx -t`

重新加载Nginx服务 `service nginx reload`
## 开启Supervisor服务
### 安装supervisor
```
# 安装supervisor
apt install supervisor
```
### Supervisor 配置文件
```bash
# 文件位置：/etc/supervisor/conf.d/rsshub.conf

[program:rsshub_python]
command=/home/lxf/.local/bin/uwsgi --ini /opt/RSSHub-python/uwsgi.ini
user=lxf
autorestart=true
autostart=true
startretries=3
redirect_stderr=true
startsecs=5
#↓注意需要创建这个日志文件
stdout_logfile=/var/log/uwsgi/supervisor.log 
stopasgroup=true
killasgroup=true
priority=999
```
### 启动Supersivor
```
# 启动supervisor
service supervisor start
```
## 配置内网穿透
### 配置映射关系
在花生壳内网穿透服务后台[配置中心](https://console.hsk.oray.com/parts)开启 HTTP 映射服务；
接着在内网穿透菜单填写配置信息，其中：

- 内网主机：为上文服务器内通过`ifconfig` 命令获取到的ip；
- 内网端口：为9080（aid learning默认的http端口）。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1638106924932-113da602-2430-419a-b4a5-3f84029e10de.png#height=275&id=uf78ea94b&originHeight=867&originWidth=1578&originalType=binary&ratio=1&rotation=0&showTitle=false&size=105038&status=done&style=shadow&title=&width=500)
### 安装花生壳内网版 App
apk文件可以通过[豌豆荚](https://www.wandoujia.com/apps/7956016)下载，官网比较凌乱，没找到下载入口；
安装后登录花生壳账号，诊断一下，预期是正常连接；
访问花生壳内网穿透服务后台的外网域名，即可访问到Nginx默认页面：
![image.png](https://cdn.nlark.com/yuque/0/2021/png/147312/1638149455953-acb7d41a-9f11-446a-9c6c-2fcffa63f3e8.png#clientId=u7beefe37-88dc-4&from=paste&height=144&id=u7770bb69&originHeight=287&originWidth=591&originalType=binary&ratio=1&rotation=0&showTitle=false&size=31776&status=done&style=shadow&taskId=ub24d638c-e9d2-430a-ab0c-ca3c8e6231c&title=&width=295.5)
## 代理访问(非必须)
有的公司网络监控会将花生壳、todesk等内网穿透性质的服务在域名层面进行封禁，所以可能需要正向代理来突破限制。

这里我们借助小火箭，在阿里云服务器上部署ss-server端。为简化部署，通过docker方式进行。考虑到安全问题，本文不详述部署过程。
## 日常运维
### 重启服务
手机没电了，重新充电，怎么重启服务？
依次启动几个APP，包括：

- 开启代理软件 SS
- 开启内网穿透App“ 花生壳内网版”
- 重启‘服务器’
- 启动nginx `service nginx start`
- 启动supervisor服务。此时会自动启动 uwsgi 服务。

总体还算比较稳定，出现过一次花生壳内网版APP崩溃的情况。

首发在[语雀](https://www.yuque.com/hillerliao/zhihai.me/mtx53r)