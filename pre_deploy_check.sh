#!/bin/bash

# 部署前检查脚本
# 确保所有依赖和配置都准备就绪

echo "🔍 开始部署前检查..."

# 检查必需的工具
echo "📦 检查必需工具..."
REQUIRED_TOOLS=("docker" "docker-compose" "curl" "jq" "sshpass" "rsync")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ 缺少必需工具: ${MISSING_TOOLS[*]}"
    echo "请安装缺少的工具后重试"
    exit 1
fi
echo "✅ 所有必需工具已安装"

# 检查本地服务状态
echo "🔧 检查本地服务状态..."
if curl -s http://localhost:5512/ > /dev/null; then
    echo "✅ 本地服务运行正常"
else
    echo "⚠️  本地服务未运行（这是正常的）"
fi

# 检查Google OAuth文件
echo "🔑 检查Google OAuth凭据..."
GOOGLE_OAUTH_FILE="/Users/zac/workspace/google_oauth/qhhl-veo-26fd3f12ace3.json"
if [ -f "$GOOGLE_OAUTH_FILE" ]; then
    echo "✅ Google OAuth凭据文件存在"
else
    echo "❌ Google OAuth凭据文件不存在: $GOOGLE_OAUTH_FILE"
    echo "请确保Google Cloud凭据文件已正确放置"
    exit 1
fi

# 检查远程服务器连接
echo "🌐 检查远程服务器连接..."
REMOTE_HOST="8.219.206.213"
REMOTE_USER="ecs-user"
REMOTE_PASSWORD="5bmIINW6OUdwgpX#@u"

if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST "echo 'SSH连接成功'" 2>/dev/null; then
    echo "✅ 远程服务器SSH连接正常"
else
    echo "❌ 无法连接到远程服务器"
    exit 1
fi

# 检查远程Docker服务
echo "🐳 检查远程Docker服务..."
if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "docker --version" 2>/dev/null > /dev/null; then
    echo "✅ 远程Docker服务正常"
else
    echo "❌ 远程Docker服务异常"
    exit 1
fi

# 检查远程Redis服务
echo "📦 检查远程Redis服务..."
if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "docker exec jarvis_redis redis-cli ping" 2>/dev/null | grep -q "PONG"; then
    echo "✅ 远程Redis服务正常"
else
    echo "❌ 远程Redis服务异常"
    exit 1
fi

# 检查远程MinIO服务
echo "🗄️  检查远程MinIO服务..."
if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "curl -s http://localhost:9000/minio/health/live" 2>/dev/null; then
    echo "✅ 远程MinIO服务正常"
else
    echo "❌ 远程MinIO服务异常"
    exit 1
fi

# 检查配置文件
echo "📄 检查配置文件..."
CONFIG_FILES=("docker-compose.remote.yml" "Dockerfile" "requirements.txt")
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

# 最终总结
echo ""
echo "🎉 部署前检查完成！"
echo "📋 检查结果总结:"
echo "   ✅ 必需工具已安装"
echo "   ✅ Google OAuth凭据已准备"
echo "   ✅ 远程服务器连接正常"
echo "   ✅ 远程Docker服务正常"
echo "   ✅ 远程Redis服务正常"
echo "   ✅ 远程MinIO服务正常"
echo "   ✅ 配置文件完整"
echo ""
echo "🚀 现在可以执行部署了:"
echo "   ./deploy_to_remote.sh" 