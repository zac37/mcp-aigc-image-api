#!/bin/bash

# Images API 服务停止脚本
# 停止 FastAPI 和 MCP 服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping Images API services..."

# 停止 FastAPI 服务
if [ -f "fastapi_service.pid" ]; then
    FASTAPI_PID=$(cat fastapi_service.pid)
    if ps -p $FASTAPI_PID > /dev/null; then
        echo "🛑 Stopping FastAPI service (PID: $FASTAPI_PID)..."
        kill $FASTAPI_PID
        sleep 2
        # 强制杀死如果还在运行
        if ps -p $FASTAPI_PID > /dev/null; then
            echo "🔨 Force killing FastAPI service..."
            kill -9 $FASTAPI_PID
        fi
        echo "✅ FastAPI service stopped"
    else
        echo "ℹ️  FastAPI service not running"
    fi
    rm -f fastapi_service.pid
else
    echo "ℹ️  No FastAPI service PID file found"
fi

# 停止 MCP 服务
if [ -f "mcp_service.pid" ]; then
    MCP_PID=$(cat mcp_service.pid)
    if ps -p $MCP_PID > /dev/null; then
        echo "🛑 Stopping MCP service (PID: $MCP_PID)..."
        kill $MCP_PID
        sleep 2
        # 强制杀死如果还在运行
        if ps -p $MCP_PID > /dev/null; then
            echo "🔨 Force killing MCP service..."
            kill -9 $MCP_PID
        fi
        echo "✅ MCP service stopped"
    else
        echo "ℹ️  MCP service not running"
    fi
    rm -f mcp_service.pid
else
    echo "ℹ️  No MCP service PID file found"
fi

# 清理其他可能的进程
echo "🧹 Cleaning up any remaining processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "run_mcp_streamable.py" 2>/dev/null || true

echo "✅ All services stopped!"