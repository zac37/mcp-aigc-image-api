#!/bin/bash

# Images API 服务停止脚本
# 停止 FastAPI、MCP、Celery Worker、Celery Beat 服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping all Images API services..."
echo "   Stopping FastAPI, MCP, Celery Worker, and Celery Beat"

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

# 停止 Celery Worker 服务
if [ -f "celery_worker.pid" ]; then
    CELERY_WORKER_PID=$(cat celery_worker.pid)
    if ps -p $CELERY_WORKER_PID > /dev/null; then
        echo "🛑 Stopping Celery Worker (PID: $CELERY_WORKER_PID)..."
        kill $CELERY_WORKER_PID
        sleep 2
        # 强制杀死如果还在运行
        if ps -p $CELERY_WORKER_PID > /dev/null; then
            echo "🔨 Force killing Celery Worker..."
            kill -9 $CELERY_WORKER_PID
        fi
        echo "✅ Celery Worker stopped"
    else
        echo "ℹ️  Celery Worker not running"
    fi
    rm -f celery_worker.pid
else
    echo "ℹ️  No Celery Worker PID file found"
fi

# 停止 Celery Beat 服务
if [ -f "celery_beat.pid" ]; then
    CELERY_BEAT_PID=$(cat celery_beat.pid)
    if ps -p $CELERY_BEAT_PID > /dev/null; then
        echo "🛑 Stopping Celery Beat (PID: $CELERY_BEAT_PID)..."
        kill $CELERY_BEAT_PID
        sleep 2
        # 强制杀死如果还在运行
        if ps -p $CELERY_BEAT_PID > /dev/null; then
            echo "🔨 Force killing Celery Beat..."
            kill -9 $CELERY_BEAT_PID
        fi
        echo "✅ Celery Beat stopped"
    else
        echo "ℹ️  Celery Beat not running"
    fi
    rm -f celery_beat.pid
else
    echo "ℹ️  No Celery Beat PID file found"
fi

# 清理其他可能的进程
echo "🧹 Cleaning up any remaining processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "run_mcp_streamable.py" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

# 清理 Celery Beat 调度文件
if [ -f "celerybeat-schedule.db" ]; then
    echo "🧹 Cleaning up Celery Beat schedule file..."
    rm -f celerybeat-schedule.db
fi

echo "✅ All services stopped completely!"