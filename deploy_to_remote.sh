#!/bin/bash

# 远程Docker部署脚本
# 部署Images API服务到远程服务器

set -e

# 配置变量
REMOTE_HOST="8.219.206.213"
REMOTE_USER="ecs-user"
REMOTE_PASSWORD="5bmIINW6OUdwgpX#@u"
PROJECT_NAME="mcp_aigc_image_api"
REMOTE_PATH="/home/ecs-user/workspace/$PROJECT_NAME"
GOOGLE_OAUTH_PATH="/Users/zac/workspace/google_oauth"

echo "🚀 开始部署Images API服务到远程服务器..."

# 1. 检查本地Google OAuth文件
echo "📁 检查Google OAuth凭据文件..."
if [ ! -f "$GOOGLE_OAUTH_PATH/qhhl-veo-26fd3f12ace3.json" ]; then
    echo "❌ Google OAuth凭据文件不存在: $GOOGLE_OAUTH_PATH/qhhl-veo-26fd3f12ace3.json"
    exit 1
fi
echo "✅ Google OAuth凭据文件找到"

# 2. 创建远程目录结构
echo "📂 创建远程目录结构..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'EOF'
    mkdir -p /home/ecs-user/workspace/mcp_aigc_image_api
    mkdir -p /home/ecs-user/workspace/google_oauth
    echo "远程目录创建完成"
EOF

# 3. 上传项目文件（排除不需要的文件）
echo "📤 上传项目代码..."
rsync -avz --progress \
    --exclude='*.log' \
    --exclude='logs/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.mp4' \
    --exclude='*.jpg' \
    --exclude='*.png' \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='venv/' \
    --exclude='*.pid' \
    -e "sshpass -p '$REMOTE_PASSWORD' ssh -o StrictHostKeyChecking=no" \
    ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# 4. 上传Google OAuth凭据
echo "🔑 上传Google OAuth凭据..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    "$GOOGLE_OAUTH_PATH/qhhl-veo-26fd3f12ace3.json" \
    $REMOTE_USER@$REMOTE_HOST:/home/ecs-user/workspace/google_oauth/

# 5. 远程部署命令
echo "🐳 在远程服务器执行Docker部署..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'EOF'
    cd /home/ecs-user/workspace/mcp_aigc_image_api
    
    echo "停止现有容器..."
    docker stop images-api-service 2>/dev/null || true
    docker rm images-api-service 2>/dev/null || true
    
    echo "构建新镜像..."
    docker build -t images-api:latest .
    
    echo "启动新服务..."
    docker-compose -f docker-compose.remote.yml up -d
    
    echo "等待服务启动..."
    sleep 10
    
    echo "检查服务状态..."
    docker ps | grep images-api-service || echo "服务可能还在启动中..."
    
    echo "检查服务健康状态..."
    timeout 30 bash -c 'until curl -f http://localhost:5512/; do sleep 2; done' || echo "服务启动可能需要更多时间"
EOF

# 6. 验证部署
echo "🔍 验证部署结果..."
sleep 5
if curl -s http://$REMOTE_HOST:5512/ > /dev/null; then
    echo "✅ 部署成功！服务正在运行"
    echo "🌐 API端点: http://$REMOTE_HOST:5512/"
    echo "🔧 MCP端点: http://$REMOTE_HOST:5513/mcp/v1"
    
    # 测试主要功能
    echo "🧪 测试主要功能..."
    echo "支持的模型:"
    curl -s http://$REMOTE_HOST:5512/ | jq -r '.supported_models[]' | head -5
else
    echo "❌ 部署可能失败，请检查日志"
    echo "查看日志命令: ssh $REMOTE_USER@$REMOTE_HOST 'docker logs images-api-service'"
fi

echo "🎉 部署脚本执行完成！" 