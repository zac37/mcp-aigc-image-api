#!/bin/bash

# 本地跨平台构建并部署到远程服务器
# 解决本地arm64和远程x86_64架构差异问题

set -e

# 配置参数
SERVER="8.219.206.213"
USER="ecs-user"
PASSWORD="5bmIINW6OUdwgpX#@u"
REMOTE_DIR="/home/ecs-user/images-api"
IMAGE_NAME="images-api"
IMAGE_TAG="production"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 本地跨平台构建并远程部署${NC}"
echo "========================================"
echo "📍 本地架构: $(uname -m)"
echo "📍 目标架构: x86_64 (amd64)"
echo "📍 镜像名称: $FULL_IMAGE_NAME"
echo "📍 远程服务器: $SERVER"
echo ""

# 1. 预检查
echo -e "${BLUE}📍 1. 执行预检查...${NC}"

# 检查Docker buildx
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker buildx 未安装或未启用${NC}"
    echo "请运行: docker buildx install"
    exit 1
fi

# 检查是否支持多平台构建
if ! docker buildx ls | grep -q "docker-container"; then
    echo -e "${YELLOW}⚠️  创建多平台构建器...${NC}"
    docker buildx create --name multiarch --driver docker-container --use
    docker buildx inspect --bootstrap
fi

echo -e "${GREEN}✅ Docker buildx 就绪${NC}"

# 执行预部署检查
if [ -f "check_docker_compatibility.sh" ]; then
    echo "执行兼容性检查..."
    ./check_docker_compatibility.sh
else
    echo -e "${YELLOW}⚠️  跳过兼容性检查${NC}"
fi

# 2. 本地跨平台构建
echo -e "${BLUE}📍 2. 本地跨平台构建镜像...${NC}"

echo "构建目标平台: linux/amd64 (远程服务器架构)"
echo "开始构建，这可能需要较长时间..."

# 使用buildx进行跨平台构建
docker buildx build \
    --platform linux/amd64 \
    --tag $FULL_IMAGE_NAME \
    --load \
    --file Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 跨平台镜像构建完成${NC}"
else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

# 检查镜像信息
echo "📊 镜像信息:"
docker images $FULL_IMAGE_NAME
docker inspect $FULL_IMAGE_NAME | grep -E '"Architecture"|"Os"' || true

# 3. 镜像压缩和优化
echo -e "${BLUE}📍 3. 镜像导出和压缩...${NC}"

IMAGE_FILE="${IMAGE_NAME}_${IMAGE_TAG}_$(date +%Y%m%d_%H%M%S).tar"
echo "导出镜像到: $IMAGE_FILE"

docker save $FULL_IMAGE_NAME | gzip > $IMAGE_FILE

if [ $? -eq 0 ]; then
    IMAGE_SIZE=$(du -h $IMAGE_FILE | cut -f1)
    echo -e "${GREEN}✅ 镜像导出完成，大小: $IMAGE_SIZE${NC}"
else
    echo -e "${RED}❌ 镜像导出失败${NC}"
    exit 1
fi

# 4. 传输镜像到远程服务器
echo -e "${BLUE}📍 4. 传输镜像到远程服务器...${NC}"

echo "正在传输镜像文件..."
scp -o StrictHostKeyChecking=no -o Compression=yes \
    $IMAGE_FILE \
    ecs-user@$SERVER:/tmp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 镜像传输完成${NC}"
else
    echo -e "${RED}❌ 镜像传输失败${NC}"
    exit 1
fi

# 5. 同步必要的配置文件
echo -e "${BLUE}📍 5. 同步配置文件...${NC}"

rsync -avz --progress \
    --include='docker-compose.production.yml' \
    --include='docker-entrypoint.sh' \
    --include='.env*' \
    --exclude='*' \
    -e "sshpass -p $PASSWORD ssh -o StrictHostKeyChecking=no" \
    . $USER@$SERVER:$REMOTE_DIR/

echo -e "${GREEN}✅ 配置文件同步完成${NC}"

# 6. 远程加载和部署
echo -e "${BLUE}📍 6. 远程加载镜像并部署...${NC}"

sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $USER@$SERVER << ENDSSH
set -e

cd $REMOTE_DIR
IMAGE_FILE="/tmp/${IMAGE_FILE}"

echo "🔧 停止现有服务..."
sudo docker-compose -f docker-compose.production.yml down 2>/dev/null || true

echo "🗑️  清理旧镜像..."
sudo docker rmi $FULL_IMAGE_NAME 2>/dev/null || true
sudo docker image prune -f

echo "📦 加载新镜像..."
gunzip -c \$IMAGE_FILE | sudo docker load

if [ \$? -eq 0 ]; then
    echo "✅ 镜像加载成功"
    
    # 验证镜像
    echo "📊 验证加载的镜像:"
    sudo docker images $FULL_IMAGE_NAME
    sudo docker inspect $FULL_IMAGE_NAME | grep -E '"Architecture"|"Os"' || true
else
    echo "❌ 镜像加载失败"
    exit 1
fi

echo "🚀 启动服务..."
sudo docker-compose -f docker-compose.production.yml up -d

echo "⏳ 等待服务启动..."
sleep 60

echo "📊 检查服务状态..."
sudo docker-compose -f docker-compose.production.yml ps

echo "🧪 健康检查..."
for i in {1..10}; do
    if curl -sf http://localhost:5512/api/health > /dev/null; then
        echo "✅ 服务健康检查通过 (\$i/10)"
        break
    else
        echo "⏳ 等待服务响应... (\$i/10)"
        sleep 5
    fi
done

echo "🧹 清理临时文件..."
rm -f \$IMAGE_FILE

echo "📊 最终状态检查..."
sudo docker stats --no-stream | head -3
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 跨平台构建和远程部署完成！${NC}"
    echo "========================================"
    echo "📊 部署摘要:"
    echo "   - 构建架构: linux/amd64"
    echo "   - 镜像大小: $IMAGE_SIZE"
    echo "   - 传输方式: 本地构建 → 文件传输 → 远程加载"
    echo "   - 部署配置: docker-compose.production.yml"
    echo ""
    echo "🌐 服务地址:"
    echo "   - API文档: http://$SERVER:5512/docs"
    echo "   - 健康检查: http://$SERVER:5512/api/health"
    echo "   - MCP服务: http://$SERVER:5513/mcp/v1/health"
    echo ""
    echo "🔧 管理命令:"
    echo "   - 查看日志: ssh $USER@$SERVER 'cd $REMOTE_DIR && sudo docker-compose -f docker-compose.production.yml logs'"
    echo "   - 重启服务: ssh $USER@$SERVER 'cd $REMOTE_DIR && sudo docker-compose -f docker-compose.production.yml restart'"
    echo ""
else
    echo -e "${RED}❌ 远程部署失败${NC}"
    exit 1
fi

# 7. 清理本地临时文件
echo -e "${BLUE}📍 7. 清理本地临时文件...${NC}"
rm -f $IMAGE_FILE
echo -e "${GREEN}✅ 本地清理完成${NC}"

echo ""
echo -e "${GREEN}🎊 全部完成！镜像已成功部署到远程服务器${NC}"