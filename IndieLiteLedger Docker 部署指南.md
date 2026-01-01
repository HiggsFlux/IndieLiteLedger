# IndieLiteLedger Docker 部署指南

本指南旨在帮助您快速在服务器上通过 Docker 部署 IndieLiteLedger 系统。

## 1. 环境准备

在开始之前，请确保服务器已安装：

- **Docker** (推荐版本 20.10+)
- **Docker Compose** (推荐版本 2.0+)

---

## 2. 部署步骤

### 第一步：准备持久化目录与权限

为了确保图片上传和数据库文件能够正常读写，需要提前在宿主机创建目录并设置权限。

```bash
# 创建数据存放目录
sudo mkdir -p /data/IndieLiteLedger/storage

# 设置权限（确保容器内进程有权读写）
sudo chmod -R 777 /data/IndieLiteLedger/storage
```

### 第二步：准备 `.env` 环境变量文件

Docker 容器运行需要特定的环境变量。您需要手动在项目根目录下创建一个 `.env` 文件。

如果使用的是 MySQL 数据库，则需要配置以下内容：

```text
# MySQL Configuration
MYSQL_SERVER=您的服务器IP地址（如果是 1Panel 可以填写 host.docker.internal）
MYSQL_USER=用户名
MYSQL_PASSWORD=密码
MYSQL_DB=数据库名称
MYSQL_PORT=端口
```

### 第三步：加载镜像

如果您是通过 `.tar` 文件传输镜像，请执行：

```bash
docker load -i IndieLiteLedger.tar
```

### 第四步：配置 `docker-compose.indie.yml`
确保根目录下的 `docker-compose.indie.yml` 配置正确。参考配置如下：

```yaml
version: '3.8'

services:
  indieliteledger:
    image: indieliteledger:latest
    container_name: indieliteledger
    ports:
      - "27359:8000"  # 外部访问端口:容器内部端口
    volumes:
      - /data/IndieLiteLedger/storage:/app/storage  # 数据持久化挂载
      - ./.env:/app/.env                            # 配置文件挂载
    environment:
      TZ: Asia/Shanghai
    extra_hosts:
      - "host.docker.internal:host-gateway" # 允许容器访问宿主机
    restart: always
```

### 第五步：启动服务
在根目录下运行：

```bash
docker-compose -f docker-compose.indie.yml up -d
```

---

## 3. 常见问题与坑点 (Troubleshooting)

### ⚠️ 代理软件冲突 (最重要)

**现象**：无法上传图片、接口返回 503 错误或请求超时。
**原因**：本地或服务器开启了代理软件（如 V2Ray, Clash）。代理软件可能会拦截/缓冲大文件上传请求，或者其规则配置导致容器与外部通信异常。
**解决**：

- 在部署和测试时，请**关闭**系统级代理。
- 如果必须使用代理，请将部署服务器的 IP 地址加入代理软件的 **绕过名单 (Whitelist/Direct)**。

### 📁 目录权限问题

**现象**：图片上传失败，后台日志显示 `Permission denied`。
**解决**：
确保宿主机上的挂载目录（如 `/data/IndieLiteLedger/storage`）具有读写权限：

```bash
sudo chmod -R 777 /data/IndieLiteLedger/storage
```

### 🌐 端口访问

**现象**：服务启动成功但无法通过浏览器访问。
**解决**：

- 检查服务器防火墙（如 `ufw` 或 `iptables`）是否放行了 `27359` 端口。
- 如果是云服务器（阿里云、腾讯云等），请在安全组中添加入站规则。

---

## 4. 日志查看

如果遇到其他问题，可以通过查看容器日志排查：

```bash
docker logs -f indieliteledger
```
