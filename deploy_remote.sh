#!/bin/bash

# Images API 远程服务器部署脚本
# 基于 REMOTE_DEPLOYMENT_SUMMARY.md 的成功经验
# 
# 目标服务器: 8.219.206.213
# 用户: ecs-user
# 部署方式: Docker容器化部署

set -e

# =============================================================================
# 配置信息
# =============================================================================

REMOTE_HOST="8.219.206.213"
REMOTE_USER="ecs-user"
REMOTE_PASSWORD="5bmIINW6OUdwgpX#@u"
REMOTE_DIR="/home/ecs-user/images-api"
CONTAINER_NAME="images-api-service"
NETWORK_NAME="images-api_images-network"

# 端口配置
FASTAPI_PORT="5512"
MCP_PORT="5513"

echo "🚀 Starting Images API Remote Deployment..."
echo "📡 Target Server: $REMOTE_HOST"
echo "👤 User: $REMOTE_USER"
echo "📂 Remote Directory: $REMOTE_DIR"
echo "🐳 Container: $CONTAINER_NAME"

# =============================================================================
# 检查本地环境
# =============================================================================

echo "🔍 Checking local environment..."

# 检查必需的工具
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass is required but not installed."
    echo "💡 Install with: brew install sshpass (macOS) or apt-get install sshpass (Linux)"
    exit 1
fi

# 检查项目文件
required_files=("main.py" "requirements.txt" "core/config.py" "routers/api.py")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ Local environment check passed"

# =============================================================================
# 创建远程部署所需文件
# =============================================================================

echo "📝 Creating deployment configuration..."

# 创建 Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 5512 5513

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5512/docs || exit 1

# 启动脚本
CMD ["bash", "-c", "python3 main.py > /app/logs/fastapi_service.log 2>&1 & python3 scripts/run_mcp_streamable.py > /app/logs/mcp_service.log 2>&1 & wait"]
EOF

# 创建 docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  images-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: $CONTAINER_NAME
    ports:
      - "$FASTAPI_PORT:5512"
      - "$MCP_PORT:5513"
    volumes:
      - ./logs:/app/logs
    networks:
      - images-network
    restart: unless-stopped
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5512/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  images-network:
    name: $NETWORK_NAME
    driver: bridge
EOF

# 创建启动脚本
cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Images API Services..."
echo "⏰ $(date)"

# 启动 FastAPI 服务
echo "🌟 Starting FastAPI service..."
python3 main.py > /app/logs/fastapi_service.log 2>&1 &
FASTAPI_PID=$!
echo "✅ FastAPI started with PID: $FASTAPI_PID"

# 等待FastAPI启动
sleep 5

# 启动 MCP 服务
echo "🔧 Starting MCP service..."
python3 scripts/run_mcp_streamable.py > /app/logs/mcp_service.log 2>&1 &
MCP_PID=$!
echo "✅ MCP started with PID: $MCP_PID"

# 保持容器运行
echo "🎯 Services started successfully!"
echo "📊 FastAPI PID: $FASTAPI_PID"
echo "📊 MCP PID: $MCP_PID"

# 等待所有后台进程
wait
EOF

chmod +x docker-entrypoint.sh

echo "✅ Deployment files created"

# =============================================================================
# 部署到远程服务器
# =============================================================================

echo "📤 Deploying to remote server..."

# 创建远程目录
echo "📁 Creating remote directory..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "
    mkdir -p $REMOTE_DIR
    mkdir -p $REMOTE_DIR/logs
"

# 上传项目文件
echo "📤 Uploading project files..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no -r \
    main.py \
    requirements.txt \
    core/ \
    routers/ \
    services/ \
    scripts/ \
    Dockerfile \
    docker-compose.yml \
    docker-entrypoint.sh \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# 停止旧容器（如果存在）
echo "🛑 Stopping existing containers..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR
    sudo docker-compose down --remove-orphans || true
    sudo docker rm -f $CONTAINER_NAME || true
"

# 构建和启动新容器
echo "🏗️ Building and starting containers..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR
    sudo docker-compose build --no-cache
    sudo docker-compose up -d
"

echo "⏳ Waiting for services to start..."
sleep 10

# =============================================================================
# 验证部署
# =============================================================================

echo "🔍 Verifying deployment..."

# 检查容器状态
echo "📊 Checking container status..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR
    sudo docker-compose ps
"

# 检查服务健康状态
echo "🏥 Testing service health..."

# 测试 FastAPI 服务
if curl -f -s --max-time 10 "http://$REMOTE_HOST:$FASTAPI_PORT/docs" > /dev/null; then
    echo "✅ FastAPI service is healthy"
else
    echo "⚠️ FastAPI service might not be ready yet"
fi

# 测试 MCP 服务
if curl -f -s --max-time 10 "http://$REMOTE_HOST:$MCP_PORT/mcp/v1/health" > /dev/null; then
    echo "✅ MCP service is healthy"
else
    echo "⚠️ MCP service might not be ready yet"
fi

# =============================================================================
# 部署总结
# =============================================================================

echo ""
echo "🎉 Deployment Summary"
echo "==================="
echo "📡 Remote Server: $REMOTE_HOST"
echo "🐳 Container: $CONTAINER_NAME"
echo "🌐 FastAPI Service: http://$REMOTE_HOST:$FASTAPI_PORT"
echo "🔧 MCP Service: http://$REMOTE_HOST:$MCP_PORT"
echo "📖 API Documentation: http://$REMOTE_HOST:$FASTAPI_PORT/docs"
echo "🏥 Health Check: http://$REMOTE_HOST:$FASTAPI_PORT/docs"
echo ""
echo "📝 Management Commands:"
echo "# SSH to server"
echo "ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "# View container status"
echo "sudo docker-compose ps"
echo ""
echo "# View logs"
echo "sudo docker-compose logs -f"
echo ""
echo "# Restart services"
echo "sudo docker-compose restart"
echo ""

# 清理本地临时文件
rm -f Dockerfile docker-compose.yml docker-entrypoint.sh

echo "✅ Remote deployment completed!"
echo "🌟 Services should be available in ~1 minute" 