# RSM 服务器部署指南

本文档记录 `rsm_auto_platform` 在 `rsm` 服务器上的生产部署流程。

## 部署目标

- SSH 主机：`rsm`
- 远端目录：`/home/louis/code/rsm_auto_platform`
- Compose 文件：`docker-compose.rsm.yml`
- 访问地址：`http://10.31.0.4:18080/`
- 后端直连端口：`127.0.0.1:18888`

## 一键部署

在本地项目根目录执行：

```bash
bash scripts/deploy-rsm.sh
```

脚本会自动完成：

1. 同步当前项目文件到 `ssh rsm:/home/louis/code/rsm_auto_platform`
2. 保留远端 `.env`、`data/`、`logs/`、`backups/`
3. 备份远端 SQLite 数据库和当前 `static/`
4. 在远端执行前端构建并刷新 `static/`
5. 执行 `sudo docker compose -f docker-compose.rsm.yml up -d --build --force-recreate`
6. 检查 `/health` 和 `/backend-health`

## 可配置环境变量

```bash
SSH_HOST=rsm \
REMOTE_DIR=/home/louis/code/rsm_auto_platform \
APP_URL=http://127.0.0.1:18080 \
PUBLIC_URL=http://10.31.0.4:18080 \
bash scripts/deploy-rsm.sh
```

默认值已经适配当前 `rsm` 服务器，一般不需要传环境变量。

## 远端配置要求

远端必须提前准备好：

- Docker 和 Docker Compose
- Node.js / npm
- `/home/louis/code/rsm_auto_platform/.env`
- `/home/louis/code/rsm_auto_platform/data/` 下的业务配置文件

部署脚本不会覆盖 `.env` 和 `data/`，避免误删生产密钥、用户库和 mapping 配置。

## 常用运维命令

```bash
ssh rsm
cd /home/louis/code/rsm_auto_platform

sudo docker compose -f docker-compose.rsm.yml ps
sudo docker compose -f docker-compose.rsm.yml logs -f backend
sudo docker compose -f docker-compose.rsm.yml logs -f nginx
sudo docker compose -f docker-compose.rsm.yml restart backend
```

健康检查：

```bash
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/backend-health
```

## 备份与回滚

每次部署前，脚本会创建：

```text
/home/louis/code/rsm_auto_platform/backups/deploy-YYYYMMDD-HHMMSS/
```

其中可能包含：

- `rsm_auto_platform.db`：部署前 SQLite 数据库备份
- `static.tar.gz`：部署前前端静态文件备份
- `data-sha256.txt`：部署前 data 配置文件哈希

恢复前端静态文件示例：

```bash
cd /home/louis/code/rsm_auto_platform
rm -rf static
tar -xzf backups/deploy-YYYYMMDD-HHMMSS/static.tar.gz
sudo docker compose -f docker-compose.rsm.yml up -d --force-recreate nginx
```

恢复数据库前应先停止后端，并确认目标备份时间点：

```bash
cd /home/louis/code/rsm_auto_platform
sudo docker compose -f docker-compose.rsm.yml stop backend
cp backups/deploy-YYYYMMDD-HHMMSS/rsm_auto_platform.db data/rsm_auto_platform.db
sudo docker compose -f docker-compose.rsm.yml start backend
```
