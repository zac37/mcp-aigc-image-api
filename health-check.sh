#!/bin/bash
# 简化的健康检查脚本 - 遵循KISS原则

set -e

ENV=${1:-development}
ENV_FILE=".env.${ENV}"

# 加载环境变量
if [[ -f "$ENV_FILE" ]]; then
    export $(cat $ENV_FILE | grep -v '#' | xargs)
else
    # 使用默认值
    APP_PORT=${APP_PORT:-5512}
    MCP_PORT=${MCP_PORT:-5513}
fi

echo "🏥 Images API 健康检查 - 环境: ${ENV}"
echo ""

# 检查FastAPI服务
echo "🔍 检查FastAPI服务 (端口 ${APP_PORT})..."
if curl -f -s "http://localhost:${APP_PORT}/api/health" >/dev/null; then
    echo "✅ FastAPI服务正常"
    
    # 显示详细健康信息
    echo "📊 服务详情:"
    curl -s "http://localhost:${APP_PORT}/api/health" | python3 -m json.tool 2>/dev/null || echo "  无法解析健康检查响应"
else
    echo "❌ FastAPI服务异常"
fi

echo ""

# 检查MCP服务
echo "🔍 检查MCP服务 (端口 ${MCP_PORT})..."
if nc -z localhost "$MCP_PORT" 2>/dev/null; then
    echo "✅ MCP服务正常监听端口"
else
    echo "❌ MCP服务端口无响应"
fi

echo ""

# 检查容器状态
echo "🐳 检查容器状态..."
if command -v docker-compose >/dev/null; then
    COMPOSE_FILE="docker-compose.yml"
    if [[ -f "$COMPOSE_FILE" ]] && [[ -f "$ENV_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    else
        echo "  配置文件不存在，跳过容器状态检查"
    fi
else
    echo "  docker-compose未安装，跳过容器状态检查"
fi

echo ""
echo "✨ 健康检查完成"