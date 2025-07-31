#!/bin/bash

# Docker容器启动脚本
# 用于健壮地启动FastAPI + MCP + Celery服务

set -e

echo "🚀 启动AI图片/视频生成平台"
echo "   ✅ FastAPI API服务 (端口5512)"
echo "   ✅ MCP Streamable HTTP服务 (端口5513)"
echo "   ✅ Celery Worker (异步任务处理)"
echo "   📊 服务监控和健康检查"
echo ""

# 检查必要的环境变量
required_vars=(
    "REDIS_HOST"
    "MINIO_ENDPOINT"
    "SERVER_BASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 错误: 环境变量 $var 未设置"
        exit 1
    fi
done

echo "✅ 环境变量检查通过"

# 等待外部服务可用
echo "🔍 等待外部服务..."

# 等待Redis
echo "   检查Redis连接..."
timeout=30
while ! timeout 5 bash -c "echo > /dev/tcp/${REDIS_HOST}/${REDIS_PORT:-6379}" 2>/dev/null; do
    echo "   等待Redis ($REDIS_HOST:${REDIS_PORT:-6379})..."
    sleep 2
    timeout=$((timeout-2))
    if [ $timeout -le 0 ]; then
        echo "❌ Redis连接超时"
        exit 1
    fi
done
echo "   ✅ Redis连接正常"

# 等待MinIO
minio_host=$(echo $MINIO_ENDPOINT | cut -d: -f1)
minio_port=$(echo $MINIO_ENDPOINT | cut -d: -f2)
echo "   检查MinIO连接..."
timeout=30
while ! timeout 5 bash -c "echo > /dev/tcp/${minio_host}/${minio_port}" 2>/dev/null; do
    echo "   等待MinIO ($MINIO_ENDPOINT)..."
    sleep 2
    timeout=$((timeout-2))
    if [ $timeout -le 0 ]; then
        echo "❌ MinIO连接超时"
        exit 1
    fi
done
echo "   ✅ MinIO连接正常"

echo ""

# 启动服务的函数
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="/app/logs/${service_name}.log"
    
    echo "🔧 启动 $service_name..."
    
    # 确保日志目录存在并可写
    mkdir -p /app/logs 2>/dev/null || true
    # 修复日志目录权限
    chown -R appuser:appuser /app/logs 2>/dev/null || true
    chmod -R 755 /app/logs 2>/dev/null || true
    
    # 启动服务并获取PID，如果日志文件无法写入则输出到stdout
    if touch "$log_file" 2>/dev/null; then
        bash -c "$command" > "$log_file" 2>&1 &
    else
        echo "⚠️  无法写入日志文件，使用标准输出"
        bash -c "$command" &
    fi
    local pid=$!
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否还在运行
    if kill -0 $pid 2>/dev/null; then
        echo "✅ $service_name 启动成功 (PID: $pid)"
        echo $pid > "/tmp/${service_name}.pid"
        return 0
    else
        echo "❌ $service_name 启动失败"
        if [ -f "$log_file" ] && [ -r "$log_file" ]; then
            echo "最后10行日志:"
            tail -10 "$log_file" 2>/dev/null || echo "无法读取日志文件"
        else
            echo "日志文件不可访问，请检查权限设置"
        fi
        return 1
    fi
}

# 信号处理函数
cleanup() {
    echo ""
    echo "🛑 接收到停止信号，正在关闭服务..."
    
    # 杀死所有子进程
    jobs -p | xargs -r kill
    
    echo "✅ 所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 启动FastAPI服务
if ! start_service "fastapi" "python main.py"; then
    echo "❌ FastAPI启动失败，退出"
    exit 1
fi
FASTAPI_PID=$(cat /tmp/fastapi.pid)

sleep 5

# 启动MCP服务
if ! start_service "mcp" "python scripts/run_mcp_streamable.py"; then
    echo "❌ MCP服务启动失败，退出"
    exit 1
fi
MCP_PID=$(cat /tmp/mcp.pid)

sleep 5

# 启动Celery Worker
if ! start_service "celery-worker" "celery -A celery_config worker --loglevel=info --pool=threads --concurrency=4"; then
    echo "⚠️  Celery Worker启动失败，但继续运行其他服务"
    WORKER_PID=""
else
    WORKER_PID=$(cat /tmp/celery-worker.pid)
fi

sleep 5

# 启动Celery Beat (定时任务调度器)
if ! start_service "celery-beat" "celery -A celery_config beat --loglevel=info"; then
    echo "⚠️  Celery Beat启动失败，但继续运行其他服务"
    BEAT_PID=""
else
    BEAT_PID=$(cat /tmp/celery-beat.pid)
fi

echo ""
echo "🎉 所有服务启动完成！"
echo "📊 服务信息:"
echo "   - FastAPI: http://0.0.0.0:5512 (PID: $FASTAPI_PID)"
echo "   - MCP: http://0.0.0.0:5513 (PID: $MCP_PID)"
if [ -n "$WORKER_PID" ]; then
    echo "   - Celery Worker: 运行中 (PID: $WORKER_PID)"
else
    echo "   - Celery Worker: 未启动"
fi
if [ -n "$BEAT_PID" ]; then
    echo "   - Celery Beat: 运行中 (PID: $BEAT_PID)"
else
    echo "   - Celery Beat: 未启动"
fi
echo ""

# 监控服务状态
while true; do
    # 检查FastAPI
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "❌ FastAPI进程异常退出，重启服务"
        cleanup
        exit 1
    fi
    
    # 检查MCP
    if ! kill -0 $MCP_PID 2>/dev/null; then
        echo "❌ MCP进程异常退出，重启服务"
        cleanup
        exit 1
    fi
    
    # 检查Celery Worker（可选）
    if [ -n "$WORKER_PID" ] && ! kill -0 $WORKER_PID 2>/dev/null; then
        echo "⚠️  Celery Worker进程异常退出，尝试重启"
        if start_service "celery-worker" "celery -A celery_config worker --loglevel=info --pool=threads --concurrency=4"; then
            WORKER_PID=$(cat /tmp/celery-worker.pid)
            echo "✅ Celery Worker重启成功"
        else
            echo "❌ Celery Worker重启失败，继续运行其他服务"
            WORKER_PID=""
        fi
    fi
    
    # 检查Celery Beat（可选）
    if [ -n "$BEAT_PID" ] && ! kill -0 $BEAT_PID 2>/dev/null; then
        echo "⚠️  Celery Beat进程异常退出，尝试重启"
        if start_service "celery-beat" "celery -A celery_config beat --loglevel=info"; then
            BEAT_PID=$(cat /tmp/celery-beat.pid)
            echo "✅ Celery Beat重启成功"
        else
            echo "❌ Celery Beat重启失败，继续运行其他服务"
            BEAT_PID=""
        fi
    fi
    
    sleep 30
done