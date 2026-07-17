#!/bin/bash
# ========================================
# 一键部署脚本 - 首次在服务器上运行
# ========================================

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Demo02 一键部署脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置（请根据实际情况修改）
REGISTRY="ghcr.io"
USERNAME="ambition-ljx"             # 改成你的 GitHub 用户名
PROJECT_DIR="/opt/demo02"

# 登录 GitHub Container Registry
echo -e "${YELLOW}[1/5] 登录镜像仓库...${NC}"
echo "$GITHUB_TOKEN" | docker login $REGISTRY -u "$USERNAME" --password-stdin

# 创建目录
echo -e "${YELLOW}[2/5] 创建项目目录...${NC}"
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 拉取 docker-compose 文件
echo -e "${YELLOW}[3/5] 复制部署配置...${NC}"
# 如果项目已经 git clone 到服务器，直接 cp
# 如果没有，可以从 GitHub 下载：
# curl -O https://raw.githubusercontent.com/$USERNAME/demo02/main/deploy/docker-compose.prod.yml

# 拉取最新镜像（触发 Watchtower 开始监控）
echo -e "${YELLOW}[4/5] 拉取最新镜像...${NC}"
docker compose -f docker-compose.prod.yml pull

# 启动所有服务
echo -e "${YELLOW}[5/5] 启动服务...${NC}"
docker compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}=========================================="
echo "  部署完成！"
echo "==========================================${NC}"
echo "访问地址: http://你的服务器IP"
echo "查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "停止服务: docker compose -f docker-compose.prod.yml down"
echo ""
echo "Watchtower 已配置，每 5 分钟自动检查更新"
echo "当 GitHub 有新镜像时，会自动拉取并重启容器"
