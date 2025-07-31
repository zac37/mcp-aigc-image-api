#!/bin/bash

# 远程生产环境部署脚本
# 目标服务器: 8.219.206.213
# 用户: ecs-user
# 使用生产环境Docker配置和外部服务

set -e

SERVER="8.219.206.213"
USER="ecs-user"
REMOTE_DIR="/home/ecs-user/images-api"
PASSWORD="5bmIINW6OUdwgpX#@u"

echo "🚀 开始远程生产环境部署到 $SERVER"
echo "================================"

# 0. 预部署检查
echo "🔍 执行预部署检查..."
if [ -f "check_docker_compatibility.sh" ]; then
    ./check_docker_compatibility.sh
    if [ $? -ne 0 ]; then
        echo "❌ 预部署检查失败，停止部署"
        exit 1
    fi
else
    echo "⚠️  跳过Docker兼容性检查（脚本不存在）"
fi

# 1. 测试SSH连接
echo "📡 测试SSH连接..."
if ! sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $USER@$SERVER "echo 'SSH连接成功'"; then
    echo "❌ SSH连接失败，请检查:"
    echo "   1. 服务器是否在线"
    echo "   2. SSH密码是否正确"
    echo "   3. 用户权限是否正确"
    exit 1
fi

# 2. 同步代码（使用.dockerignore优化）
echo "📤 同步项目代码..."
rsync -avz --progress \
    --delete \
    --exclude='.git/' \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='test_*' \
    --exclude='check_*' \
    --exclude='create_*' \
    --exclude='debug_*' \
    --exclude='*.mp4' \
    --exclude='*.jpg' \
    --exclude='*.png' \
    -e "sshpass -p $PASSWORD ssh -o StrictHostKeyChecking=no" \
    . $USER@$SERVER:$REMOTE_DIR/

if [ $? -eq 0 ]; then
    echo "✅ 代码同步完成"
else
    echo "❌ 代码同步失败"
    exit 1
fi

# 3. 远程部署
echo "🏗️  执行远程生产环境Docker部署..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $USER@$SERVER << 'ENDSSH'
cd /home/ecs-user/images-api

echo "🔧 停止现有服务..."
sudo docker-compose down 2>/dev/null || true
sudo docker-compose -f docker-compose.production.yml down 2>/dev/null || true

echo "🧹 清理资源..."
sudo docker container prune -f
sudo docker image prune -f

echo "🔍 检查外部服务状态..."
echo "   检查Redis服务..."
if sudo docker ps | grep jarvis_redis > /dev/null; then
    echo "   ✅ Redis服务运行正常"
else
    echo "   ❌ Redis服务未运行"
    exit 1
fi

echo "   检查MinIO服务..."
if sudo docker ps | grep jarvis_minio > /dev/null; then
    echo "   ✅ MinIO服务运行正常"
else
    echo "   ❌ MinIO服务未运行"
    exit 1
fi

echo "   检查Docker网络..."
if sudo docker network ls | grep jarvis-v2_default > /dev/null; then
    echo "   ✅ jarvis-v2_default网络存在"
else
    echo "   ❌ jarvis-v2_default网络不存在"
    exit 1
fi

echo "🏗️  构建生产环境Docker镜像..."
sudo docker-compose -f docker-compose.production.yml build --no-cache

echo "🚀 启动生产环境服务..."
sudo docker-compose -f docker-compose.production.yml up -d

echo "⏳ 等待服务启动（60秒）..."
sleep 60

echo "📊 检查服务状态..."
sudo docker-compose -f docker-compose.production.yml ps

echo "📋 检查最新服务日志..."
sudo docker-compose -f docker-compose.production.yml logs --tail=20

echo "🧪 测试服务健康（多次重试）..."
for i in {1..10}; do
    if curl -sf http://localhost:5512/api/health > /dev/null; then
        echo "✅ FastAPI服务健康检查通过 ($i/10)"
        break
    else
        echo "⏳ 等待FastAPI服务响应... ($i/10)"
        if [ $i -eq 10 ]; then
            echo "❌ FastAPI服务健康检查失败"
            sudo docker-compose -f docker-compose.production.yml logs --tail=50
        fi
        sleep 5
    fi
done

echo "🧪 测试MCP服务..."
for i in {1..5}; do
    if curl -sf http://localhost:5513/mcp/v1/health > /dev/null; then
        echo "✅ MCP服务健康检查通过 ($i/5)"
        break
    else
        echo "⏳ 等待MCP服务响应... ($i/5)"
        if [ $i -eq 5 ]; then
            echo "⚠️  MCP服务可能需要更长启动时间"
        fi
        sleep 10
    fi
done

echo ""
echo "📊 最终服务状态检查..."
sudo docker stats --no-stream | head -5
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 远程生产环境部署完成！"
    echo "================================"
    echo "🌐 API文档: http://$SERVER:5512/docs"
    echo "💗 健康检查: http://$SERVER:5512/api/health"  
    echo "🔧 MCP服务: http://$SERVER:5513/mcp/v1/health"
    echo ""
    echo "📊 部署信息:"
    echo "   - 配置文件: docker-compose.production.yml"
    echo "   - Python版本: 3.11.12"
    echo "   - 外部Redis: jarvis_redis (连接正常)"
    echo "   - 外部MinIO: jarvis_minio (连接正常)"
    echo "   - Docker网络: jarvis-v2_default"
    echo "   - 资源限制: 4G内存，4核CPU"
    echo "   - 健壮启动: docker-entrypoint.sh"
    echo "   - 非root用户: appuser"
    echo "   - 时区设置: Asia/Shanghai"
    echo ""
    echo "🛠️  故障排查:"
    echo "   - 查看日志: ssh $USER@$SERVER 'cd $REMOTE_DIR && sudo docker-compose -f docker-compose.production.yml logs'"
    echo "   - 重启服务: ssh $USER@$SERVER 'cd $REMOTE_DIR && sudo docker-compose -f docker-compose.production.yml restart'"
    echo "   - 进入容器: ssh $USER@$SERVER 'sudo docker exec -it images-api-service bash'"
    echo ""
else
    echo "❌ 远程生产环境部署失败"
    echo "🔍 请检查服务日志获取详细错误信息"
    exit 1
fi