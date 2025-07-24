#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Docker容器启动 ==="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动Kling API服务..."

# 创建必要的目录
mkdir -p /app/logs

# 启动MCP服务 (后台运行)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动MCP服务..."
cd /app
python3 scripts/run_mcp_streamable.py > /app/logs/mcp_service.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > /app/mcp.pid
echo "[$(date '+%Y-%m-%d %H:%M:%S')] MCP服务已启动，PID: $MCP_PID"

# 等待MCP服务启动
sleep 5

# 检查MCP服务是否正常运行
if kill -0 $MCP_PID 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ MCP服务运行正常"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ MCP服务启动失败"
    exit 1
fi

# 启动FastAPI服务 (前台运行)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动FastAPI服务..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 5511 --log-level info &
FASTAPI_PID=$!
echo $FASTAPI_PID > /app/fastapi.pid
echo "[$(date '+%Y-%m-%d %H:%M:%S')] FastAPI服务已启动，PID: $FASTAPI_PID"

# 等待FastAPI服务启动
sleep 10

# 检查FastAPI服务是否正常运行
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ FastAPI服务运行正常"
    
    # 尝试健康检查
    for i in {1..5}; do
        if curl -s http://localhost:5511/api/health > /dev/null; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 健康检查通过"
            break
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待服务就绪... ($i/5)"
            sleep 2
        fi
    done
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ FastAPI服务启动失败"
    kill $MCP_PID 2>/dev/null || true
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 服务启动完成 ==="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] FastAPI服务: http://0.0.0.0:5511"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] API文档: http://0.0.0.0:5511/docs"  
echo "[$(date '+%Y-%m-%d %H:%M:%S')] MCP服务: http://0.0.0.0:5510/mcp/v1"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 配置的API-KEY: $(python3 -c "from core.config import settings; print(settings.kling.api_key[:15] + '...')" 2>/dev/null || echo "已配置")"

# 信号处理函数
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 接收到停止信号，正在关闭服务..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $MCP_PID 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 服务已停止"
    exit 0
}

# 注册信号处理
trap cleanup SIGTERM SIGINT

# 保持容器运行，等待子进程
wait $FASTAPI_PID 