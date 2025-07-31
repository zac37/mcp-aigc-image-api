#!/bin/bash

# Images API 服务重启脚本
# 启动 FastAPI、MCP、Celery Worker、Celery Beat 和任务监控服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Restarting all Images API services..."
echo "✨ 启动完整的AI图片/视频生成平台"
echo "   - FastAPI API服务 (5512)"
echo "   - MCP Streamable HTTP服务 (5513)"
echo "   - Celery Worker 异步任务处理"
echo "   - Celery Beat 定时任务调度"

# 停止现有服务
./stop.sh

sleep 2

# 检查Redis服务状态
echo "🔍 Checking Redis service..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis service is running"
    else
        echo "⚠️  Redis service not responding - please start Redis manually"
        echo "    brew services start redis  # macOS"
        echo "    sudo systemctl start redis # Linux"
    fi
else
    echo "⚠️  redis-cli not found - please ensure Redis is installed and running"
fi

echo ""
echo "🚀 Starting FastAPI service (port 5512)..."
# 启动 FastAPI 服务
nohup python3 main.py > fastapi_service.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > fastapi_service.pid
echo "✅ FastAPI service started with PID: $FASTAPI_PID"

echo "🚀 Starting MCP Streamable HTTP service (port 5513)..."
# 启动 MCP 服务（streamable HTTP模式）
nohup python3 scripts/run_mcp_streamable.py > mcp_service.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > mcp_service.pid
echo "✅ MCP service started with PID: $MCP_PID"

echo "🚀 Starting Celery Worker for async tasks..."
# 启动 Celery Worker - 处理视频和图片存储任务
nohup celery -A celery_config.app worker --loglevel=info --logfile=celery_worker.log > /dev/null 2>&1 &
CELERY_WORKER_PID=$!
echo $CELERY_WORKER_PID > celery_worker.pid
echo "✅ Celery Worker started with PID: $CELERY_WORKER_PID"

echo "🚀 Starting Celery Beat for scheduled monitoring..."
# 启动 Celery Beat - 定时任务调度器，负责监控视频任务
nohup celery -A celery_config.app beat --loglevel=info --logfile=celery_beat.log > /dev/null 2>&1 &
CELERY_BEAT_PID=$!
echo $CELERY_BEAT_PID > celery_beat.pid
echo "✅ Celery Beat started with PID: $CELERY_BEAT_PID"

sleep 5

# 检查服务状态
echo "🔍 Checking all service status..."
./status.sh

echo ""
echo "📝 Service Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 API Services:"
echo "  📊 FastAPI API Server: http://localhost:5512"
echo "  📖 API Documentation: http://localhost:5512/docs"
echo "  🔌 MCP Streamable Service: http://localhost:5513/mcp/v1"
echo "  💚 Health Check: http://localhost:5513/mcp/v1/health"
echo "  🛠️  Available Tools: http://localhost:5513/mcp/v1/tools"
echo ""
echo "⚙️  Background Services:"
echo "  🔄 Celery Worker: Processing async tasks"
echo "  ⏰ Celery Beat: Monitoring scheduled tasks every 60s"
echo "  📦 Redis: Task queue and caching backend"
echo ""
echo "📊 Task Monitoring:"
echo "  🎬 Video Generation: Auto-monitoring via Celery Beat"
echo "  🖼️  Image Storage: Async processing via Celery Worker"
echo "  📝 Task Queue: Simple queue with Redis backend"
echo ""
echo "📂 Log Files:"
echo "  fastapi_service.log   - FastAPI服务日志"
echo "  mcp_service.log       - MCP服务日志" 
echo "  celery_worker.log     - Celery Worker日志"
echo "  celery_beat.log       - Celery Beat调度日志"
echo "  logs/                 - 详细组件日志目录"
echo ""
echo "🎯 Platform Features:"
echo "  ✅ 15+ AI Image Models (GPT, FLUX, Recraft, etc.)"
echo "  ✅ Dual Protocol Support (REST API + MCP)"
echo "  ✅ Streamable HTTP MCP Implementation"
echo "  ✅ Async Task Processing (Celery)"
echo "  ✅ Auto Video Monitoring (60s intervals)"
echo "  ✅ MinIO File Storage Integration"
echo "  ✅ JARVIS Asset Library Notification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 完整AI图片/视频生成平台启动完成！"
echo "   所有服务已启动并运行在统一管理脚本中"