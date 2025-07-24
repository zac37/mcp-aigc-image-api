#!/bin/bash

# Kling API 服务停止脚本

FASTAPI_PORT=5511
MCP_PORT=5510

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# 停止端口上的进程
stop_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port > /dev/null 2>&1; then
        local pids=$(lsof -ti:$port)
        log "Stopping $service_name on port $port (PIDs: $pids)"
        
        # 尝试优雅停止
        kill $pids 2>/dev/null || true
        sleep 3
        
        # 检查是否还在运行
        if lsof -ti:$port > /dev/null 2>&1; then
            log "Force stopping $service_name..."
            kill -9 $pids 2>/dev/null || true
            sleep 2
        fi
        
        if ! lsof -ti:$port > /dev/null 2>&1; then
            success "$service_name stopped"
        else
            error "Failed to stop $service_name"
        fi
    else
        log "$service_name is not running on port $port"
    fi
}

log "=== Stopping Kling API Services ==="

# 停止服务
stop_port $FASTAPI_PORT "FastAPI Service"
stop_port $MCP_PORT "MCP Service"

# 清理PID文件
rm -f fastapi.pid mcp.pid 2>/dev/null || true

success "All services stopped"