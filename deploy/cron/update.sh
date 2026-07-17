#!/bin/bash
# ========================================
# 手动更新脚本 - 当 Watchtower 不可用时使用
# ========================================

set -e

USERNAME="ambition-ljx"
PROJECT_DIR="/opt/demo01/Demo02_FastAPI-Vue"

echo "开始更新服务..."

# 登录
docker login ghcr.io -u "$USERNAME" --password-stdin <<< "$GITHUB_TOKEN"

# 拉取最新镜像
docker pull ghcr.io/$USERNAME/demo02-backend:latest
docker pull ghcr.io/$USERNAME/demo02-frontend:latest

# 重启容器（会自动使用新镜像）
docker compose -f $PROJECT_DIR/deploy/docker-compose.prod.yml restart

echo "更新完成！"
