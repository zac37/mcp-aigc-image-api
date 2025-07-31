#!/bin/bash

# Images API 服务状态检查脚本
# 检查 FastAPI、MCP、Celery Worker、Celery Beat 服务状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Checking all Images API services status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

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

# 检查 Celery Worker 服务
echo "⚙️  Celery Worker Service:"
if [ -f "celery_worker.pid" ]; then
    CELERY_WORKER_PID=$(cat celery_worker.pid)
    if ps -p $CELERY_WORKER_PID > /dev/null; then
        echo "  Status: ✅ Running (PID: $CELERY_WORKER_PID)"
        
        # 检查进程是否真正活跃
        if ps aux | grep "celery.*worker" | grep -v grep > /dev/null; then
            echo "  Process: ✅ Active worker process found"
        else
            echo "  Process: ❌ No active worker process"
        fi
    else
        echo "  Status: ❌ Not running (stale PID file)"
        rm -f celery_worker.pid
    fi
else
    echo "  Status: ❌ Not running (no PID file)"
fi

echo ""

# 检查 Celery Beat 服务
echo "⏰ Celery Beat Service:"
if [ -f "celery_beat.pid" ]; then
    CELERY_BEAT_PID=$(cat celery_beat.pid)
    if ps -p $CELERY_BEAT_PID > /dev/null; then
        echo "  Status: ✅ Running (PID: $CELERY_BEAT_PID)"
        
        # 检查进程是否真正活跃
        if ps aux | grep "celery.*beat" | grep -v grep > /dev/null; then
            echo "  Process: ✅ Active beat process found"
        else
            echo "  Process: ❌ No active beat process"
        fi
        
        # 检查调度文件
        if [ -f "celerybeat-schedule.db" ]; then
            echo "  Schedule: ✅ Schedule database exists"
        else
            echo "  Schedule: ⚠️  No schedule database"
        fi
    else
        echo "  Status: ❌ Not running (stale PID file)"
        rm -f celery_beat.pid
    fi
else
    echo "  Status: ❌ Not running (no PID file)"
fi

echo ""

# 检查 Redis 连接
echo "📦 Redis Service:"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "  Status: ✅ Running and responding"
        
        # 检查 Redis 中的任务队列
        PENDING_COUNT=$(redis-cli zcard "veo3_tasks:pending" 2>/dev/null || echo "0")
        MONITORING_COUNT=$(redis-cli zcard "veo3_tasks:monitoring" 2>/dev/null || echo "0")
        echo "  Task Queues: 📋 Pending: $PENDING_COUNT, Monitoring: $MONITORING_COUNT"
    else
        echo "  Status: ❌ Not responding"
    fi
else
    echo "  Status: ⚠️  redis-cli not found"
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

if [ -f "celery_worker.log" ]; then
    LOG_SIZE=$(du -h celery_worker.log | cut -f1)
    echo "  Celery Worker Log: ✅ celery_worker.log ($LOG_SIZE)"
else
    echo "  Celery Worker Log: ❌ No log file"
fi

if [ -f "celery_beat.log" ]; then
    LOG_SIZE=$(du -h celery_beat.log | cut -f1)
    echo "  Celery Beat Log: ✅ celery_beat.log ($LOG_SIZE)"
else
    echo "  Celery Beat Log: ❌ No log file"
fi

echo ""

# 显示服务URL
echo "🌐 Service URLs:"
echo "  📊 FastAPI API: http://localhost:5512"
echo "  📖 API Documentation: http://localhost:5512/docs"
echo "  🔌 MCP Service: http://localhost:5513/mcp/v1"
echo "  💚 Health Check: http://localhost:5513/mcp/v1/health"
echo "  🛠️  Available Tools: http://localhost:5513/mcp/v1/tools"

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

if [ -f "celery_worker.log" ]; then
    ERROR_COUNT=$(grep -i error celery_worker.log | tail -5 | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  Celery Worker Errors:"
        grep -i error celery_worker.log | tail -3 | sed 's/^/    /'
    fi
fi

if [ -f "celery_beat.log" ]; then
    ERROR_COUNT=$(grep -i error celery_beat.log | tail -5 | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  Celery Beat Errors:"
        grep -i error celery_beat.log | tail -3 | sed 's/^/    /'
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"