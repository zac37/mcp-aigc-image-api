#!/bin/bash

# Images API 服务状态检查脚本
# 检查 FastAPI 和 MCP 服务状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Checking Images API services status..."
echo ""

# 检查 FastAPI 服务
echo "📡 FastAPI Service (Port 5512):"
if [ -f "fastapi_service.pid" ]; then
    FASTAPI_PID=$(cat fastapi_service.pid)
    if ps -p $FASTAPI_PID > /dev/null; then
        echo "  Status: ✅ Running (PID: $FASTAPI_PID)"
        
        # 检查端口是否监听
        if lsof -i :5512 > /dev/null 2>&1; then
            echo "  Port 5512: ✅ Listening"
            
            # 检查健康状态
            if curl -s http://localhost:5512/api/health > /dev/null 2>&1; then
                echo "  Health: ✅ Healthy"
            else
                echo "  Health: ❌ Not responding"
            fi
        else
            echo "  Port 5512: ❌ Not listening"
        fi
    else
        echo "  Status: ❌ Not running (stale PID file)"
        rm -f fastapi_service.pid
    fi
else
    echo "  Status: ❌ Not running (no PID file)"
fi

echo ""

# 检查 MCP 服务
echo "🔗 MCP Service (Port 5513):"
if [ -f "mcp_service.pid" ]; then
    MCP_PID=$(cat mcp_service.pid)
    if ps -p $MCP_PID > /dev/null; then
        echo "  Status: ✅ Running (PID: $MCP_PID)"
        
        # 检查端口是否监听
        if lsof -i :5513 > /dev/null 2>&1; then
            echo "  Port 5513: ✅ Listening"
        else
            echo "  Port 5513: ❌ Not listening"
        fi
    else
        echo "  Status: ❌ Not running (stale PID file)"
        rm -f mcp_service.pid
    fi
else
    echo "  Status: ❌ Not running (no PID file)"
fi

echo ""

# 检查日志文件
echo "📋 Log Files:"
if [ -f "fastapi_service.log" ]; then
    LOG_SIZE=$(du -h fastapi_service.log | cut -f1)
    echo "  FastAPI Log: ✅ fastapi_service.log ($LOG_SIZE)"
else
    echo "  FastAPI Log: ❌ No log file"
fi

if [ -f "mcp_service.log" ]; then
    LOG_SIZE=$(du -h mcp_service.log | cut -f1)
    echo "  MCP Log: ✅ mcp_service.log ($LOG_SIZE)"
else
    echo "  MCP Log: ❌ No log file"
fi

echo ""

# 显示服务URL
echo "🌐 Service URLs:"
echo "  FastAPI: http://localhost:5512"
echo "  API Docs: http://localhost:5512/docs"
echo "  MCP Service: http://localhost:5513/mcp/v1"

echo ""

# 检查最近的错误
echo "⚠️  Recent Errors (if any):"
if [ -f "fastapi_service.log" ]; then
    ERROR_COUNT=$(grep -i error fastapi_service.log | tail -5 | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  FastAPI Errors:"
        grep -i error fastapi_service.log | tail -3 | sed 's/^/    /'
    fi
fi

if [ -f "mcp_service.log" ]; then
    ERROR_COUNT=$(grep -i error mcp_service.log | tail -5 | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  MCP Errors:"
        grep -i error mcp_service.log | tail -3 | sed 's/^/    /'
    fi
fi