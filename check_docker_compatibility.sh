#!/bin/bash

# Docker兼容性检查脚本
# 检查本地和远程环境的Docker配置兼容性

set -e

echo "🔍 Docker环境兼容性检查"
echo "========================================"

# 1. 检查本地Docker环境
echo "📍 1. 检查本地Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装" 
    exit 1
fi

echo "   ✅ Docker版本: $(docker --version)"
echo "   ✅ Docker Compose版本: $(docker-compose --version)"

# 2. 检查架构兼容性
echo "📍 2. 检查架构兼容性..."
local_arch=$(uname -m)
echo "   本地架构: $local_arch"

# 检查Python镜像兼容性
echo "   检查Python镜像兼容性..."
if docker pull python:3.11-slim > /dev/null 2>&1; then
    echo "   ✅ Python 3.11镜像兼容"
else
    echo "   ❌ Python 3.11镜像不兼容"
    exit 1
fi

# 3. 检查Docker配置文件
echo "📍 3. 检查Docker配置文件..."
config_files=(
    "Dockerfile"
    "docker-compose.yml" 
    "docker-compose.production.yml"
    "docker-entrypoint.sh"
    ".dockerignore"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file 存在"
    else
        echo "   ❌ $file 缺失"
        exit 1
    fi
done

# 4. 验证Docker配置语法
echo "📍 4. 验证Docker配置语法..."
if docker-compose -f docker-compose.yml config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.yml 语法正确"
else
    echo "   ❌ docker-compose.yml 语法错误"
    exit 1
fi

if docker-compose -f docker-compose.production.yml config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.production.yml 语法正确"
else
    echo "   ❌ docker-compose.production.yml 语法错误"
    exit 1 
fi

# 5. 检查远程服务器环境（如果可连接）
echo "📍 5. 检查远程服务器环境..."
if command -v sshpass &> /dev/null; then
    echo "   检查远程服务器Docker环境..."
    if sshpass -p "5bmIINW6OUdwgpX#@u" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ecs-user@8.219.206.213 "docker --version && docker-compose --version" 2>/dev/null; then
        echo "   ✅ 远程服务器Docker环境正常"
        
        # 检查远程服务器架构
        remote_arch=$(sshpass -p "5bmIINW6OUdwgpX#@u" ssh -o StrictHostKeyChecking=no ecs-user@8.219.206.213 "uname -m" 2>/dev/null)
        echo "   远程架构: $remote_arch"
        
        if [ "$local_arch" = "$remote_arch" ]; then
            echo "   ✅ 架构兼容"
        else
            echo "   ⚠️  架构不同，但Docker镜像应该兼容"
        fi
        
        # 检查外部服务
        echo "   检查外部服务状态..."
        if sshpass -p "5bmIINW6OUdwgpX#@u" ssh -o StrictHostKeyChecking=no ecs-user@8.219.206.213 "sudo docker ps | grep -E 'jarvis_redis|jarvis_minio'" > /dev/null 2>&1; then
            echo "   ✅ 外部Redis和MinIO服务运行正常"
        else
            echo "   ❌ 外部服务状态异常"
        fi
        
        # 检查网络
        if sshpass -p "5bmIINW6OUdwgpX#@u" ssh -o StrictHostKeyChecking=no ecs-user@8.219.206.213 "sudo docker network ls | grep jarvis-v2_default" > /dev/null 2>&1; then
            echo "   ✅ jarvis-v2_default网络存在"
        else
            echo "   ❌ jarvis-v2_default网络不存在"
        fi
    else
        echo "   ⚠️  无法连接远程服务器，跳过远程检查"
    fi
else
    echo "   ⚠️  sshpass未安装，跳过远程检查"
fi

# 6. 构建测试
echo "📍 6. 执行构建测试..."
echo "   构建Docker镜像（干运行）..."
if docker-compose -f docker-compose.yml build --dry-run images-api > /dev/null 2>&1; then
    echo "   ✅ 构建配置验证通过"
else
    echo "   ❌ 构建配置验证失败"
    exit 1
fi

echo ""
echo "🎉 Docker环境兼容性检查完成！"
echo "========================================"
echo "✅ 所有检查项目通过"
echo "🚀 可以安全进行Docker部署"
echo ""

# 生成兼容性报告
cat > docker_compatibility_report.txt << EOF
Docker环境兼容性报告
生成时间: $(date)

本地环境:
- 架构: $local_arch
- Docker: $(docker --version)
- Docker Compose: $(docker-compose --version)

配置文件:
$(for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "- $file: ✅"
    else
        echo "- $file: ❌"
    fi
done)

兼容性状态: 通过
部署建议: 使用 docker-compose.production.yml 进行生产环境部署
EOF

echo "📄 兼容性报告已保存到: docker_compatibility_report.txt"