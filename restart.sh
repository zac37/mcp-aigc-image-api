#!/bin/bash

# Images API 服务重启脚本
# 重启 FastAPI 和 MCP 服务（使用简化MCP实现，兼容Python 3.9+）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Restarting Images API services..."
echo "✨ 使用简化MCP实现，兼容Python $(python3 --version | cut -d' ' -f2)"

# 停止现有服务
./stop.sh

sleep 2

echo "🚀 Starting FastAPI service (port 5512)..."
# 启动 FastAPI 服务
nohup python3 main.py > fastapi_service.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > fastapi_service.pid
echo "✅ FastAPI service started with PID: $FASTAPI_PID"

echo "🚀 Starting MCP service (port 5513)..."
# 启动 MCP 服务（使用简化实现）
nohup python3 scripts/run_mcp_streamable.py > mcp_service.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > mcp_service.pid
echo "✅ MCP service started with PID: $MCP_PID"

sleep 3

# 检查服务状态
echo "🔍 Checking service status..."
./status.sh

echo ""
echo "📝 Service Information:"
echo "  FastAPI: http://localhost:5512"
echo "  API Docs: http://localhost:5512/docs"
echo "  MCP Service: http://localhost:5513/mcp/v1"
echo "  MCP Health: http://localhost:5513/mcp/v1/health"
echo "  MCP Tools: http://localhost:5513/mcp/v1/tools"
echo "  MCP Info: http://localhost:5513/mcp/v1/info"
echo "  Log files: fastapi_service.log, mcp_service.log"
echo ""
echo "🎯 MCP Features:"
echo "  ✅ Python 3.9+ Compatible"
echo "  ✅ 9 Image Generation Tools"
echo "  ✅ Resources & Prompts Support"
echo "  ✅ Streamable HTTP Protocol"
echo "  ✅ Session Management"
echo ""
echo "🎉 Services restart completed!"