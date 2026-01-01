## 第一步：文件夹准备

为了确保图片上传和数据库文件能够正常读写，需要提前在宿主机创建目录并设置权限。

```bash
# 创建数据存放目录
sudo mkdir -p /data/IndieLiteLedger/storage
# 设置权限（确保容器内进程有权读写）
sudo chmod -R 777 /data/IndieLiteLedger/storage
```

### 第二步：准备 `.env` 环境变量文件

Docker 容器运行需要特定的环境变量。您需要手动在项目根目录下创建一个 `.env` 文件。
**这个路径快捷查看**：点击【容器】- 【编排】- 【创建编排】
说明：目前还没有indieliteledger这个文件夹，可以先去创建文件夹并创建一个.env文件

1. 创建文件夹可以进入【文件】菜单后进入目录/opt/1panel/docker/compose后点击创建，选择文件夹，创建indieliteledger（注意是全小写）文件夹，为了避免各种不必要问题，可以以给完整授权，也可以根据自己情况调整。
2. 然后进入文件夹创建.env文件。
3. 创建完成后点击文件，进行编辑，填写mysql信息：

```
如果使用的是 MySQL 数据库，则需要配置以下内容：

```text
# MySQL Configuration
MYSQL_SERVER=您的服务器IP地址（如果是 1Panel本地服务 可以填写 host.docker.internal）
MYSQL_USER=用户名
MYSQL_PASSWORD=密码
MYSQL_DB=数据库名称
MYSQL_PORT=端口
```

我的mysql也部署在同一个服务器，所以我填写的是：
![image.png](https://typora999.oss-cn-beijing.aliyuncs.com/20260101135250019.png)
记得点击保存。

## 第三步：导入镜像并创建并运行容器

1. 上传IndieLiteLedger.tar文件到服务器。
2. 点击【容器】- 【镜像】 - 【导入镜像】，选择刚才上传的文件导入。
3. 导入成功后点击【编排】 - 【创建编排】
   ![image.png](https://typora999.oss-cn-beijing.aliyuncs.com/20260101140158556.png)
   ```
   version: '3.8'

   services:
     indieliteledger:
       image: indieliteledger:latest
       container_name: indieliteledger
       ports:
         - "27359:8000"    # 27359是您对外访问的端口，需要开启防火墙才能进行访问
       volumes:
         - /data/IndieLiteLedger/storage:/app/storage
         - ./.env:/app/.env
       environment:
         TZ: Asia/Shanghai
       extra_hosts:
         - "host.docker.internal:host-gateway"
       restart: always

   ```
4. 创建成功
   ![image.png](https://typora999.oss-cn-beijing.aliyuncs.com/20260101140422826.png)

点击返回列表，点击刚才创建的容器，查看运行是否正常并点击日志，如果运行成功，日志最后的信息为：

```
...其他日志
INFO:app.main:Mounting /assets to /app/app/static/assets
INFO: Started server process [8]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

```

## 第四步：进入系统

浏览器输入：您的服务器IP:27359 即可进入系统
初始化管理员账号： admin ，初始化管理员密码：123456
![image.png](https://typora999.oss-cn-beijing.aliyuncs.com/20260101140648255.png)
进入后建议首先创建一个新的超级管理员，然后删掉默认的超级管理员（防止别人暴力破解）。
