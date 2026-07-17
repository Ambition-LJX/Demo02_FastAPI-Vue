#!/bin/bash
# ========================================
# 手动更新脚本 - 当 Watchtower 不可用时使用
# ========================================

set -e

echo "开始更新服务..."

# 登录
docker login ghcr.io -u YOUR_USERNAME --password-stdin <<< "$GITHUB_TOKEN"

# 拉取最新镜像
docker pull ghcr.io/YOUR_USERNAME/demo02-backend:latest
docker pull ghcr.io/YOUR_USERNAME/demo02-frontend:latest

# 重启容器（会自动使用新镜像）
docker compose -f /opt/demo02/docker-compose.prod.yml restart

echo "更新完成！"
