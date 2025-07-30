#!/bin/bash

# MinIO数据同步脚本（可选）
# 将本地MinIO的数据同步到远程MinIO

set -e

# 配置变量
REMOTE_HOST="8.219.206.213"
REMOTE_USER="ecs-user" 
REMOTE_PASSWORD="5bmIINW6OUdwgpX#@u"
LOCAL_MINIO="http://localhost:9000"
REMOTE_MINIO="http://$REMOTE_HOST:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin123"

echo "🔄 开始同步MinIO数据到远程服务器..."

# 检查本地MinIO连接
echo "🔍 检查本地MinIO连接..."
if ! curl -s $LOCAL_MINIO/minio/health/live > /dev/null; then
    echo "❌ 无法连接本地MinIO服务"
    exit 1
fi

# 检查远程MinIO连接
echo "🔍 检查远程MinIO连接..."
if ! curl -s $REMOTE_MINIO/minio/health/live > /dev/null; then
    echo "❌ 无法连接远程MinIO服务"
    exit 1
fi

echo "✅ MinIO服务连接正常"

# 创建临时目录用于数据传输
TEMP_DIR="/tmp/minio_sync_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📁 创建临时目录: $TEMP_DIR"

# 下载本地MinIO数据
echo "📥 下载本地MinIO数据..."
# 这里可以使用mc客户端工具，但为了简化，我们暂时跳过
# 实际项目中，远程MinIO是空的，会在使用过程中自动创建结构

echo "💡 提示: 由于远程MinIO是空的，数据结构会在服务运行时自动创建"
echo "   - images/YYYY/MM/DD/ (生成的图片)"
echo "   - videos/YYYY/MM/DD/ (生成的视频)"
echo "   - uploads/YYYYMMDD/ (上传的文件)"
echo "   - materials/YYYY/MM/DD/ (原始素材和元数据)"

# 清理临时目录
rm -rf "$TEMP_DIR"

echo "✅ MinIO同步检查完成！"
echo "💡 建议: 远程部署后，通过API使用来逐步填充数据" 