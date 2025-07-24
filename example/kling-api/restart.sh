#!/bin/bash

# Kling API 服务重启脚本
# 自动处理进程检测、停止、启动等操作

set -e

SERVICE_NAME="Kling API"
FASTAPI_PORT=5511
MCP_PORT=5510
LOG_FILE="restart.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# 检查端口占用
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port > /dev/null 2>&1; then
        local pid=$(lsof -ti:$port)
        log "$service_name port $port is occupied by PID: $pid"
        return 0
    else
        log "$service_name port $port is available"
        return 1
    fi
}

# 停止端口上的进程
stop_port() {
    local port=$1
    local service_name=$2
    
    if check_port $port "$service_name"; then
        local pids=$(lsof -ti:$port)
        log "Stopping $service_name processes on port $port: $pids"
        
        # 尝试优雅停止
        kill $pids 2>/dev/null || true
        sleep 3
        
        # 检查是否还在运行
        if check_port $port "$service_name"; then
            warn "Process still running, force killing..."
            kill -9 $pids 2>/dev/null || true
            sleep 2
        fi
        
        if ! check_port $port "$service_name"; then
            success "$service_name stopped successfully"
        else
            error "Failed to stop $service_name"
            return 1
        fi
    fi
}

# 检查Python环境
check_python_env() {
    if [ -d ".venv_py311" ]; then
        log "Found Python virtual environment: .venv_py311"
        source .venv_py311/bin/activate
        success "Activated virtual environment"
    else
        warn "Virtual environment .venv_py311 not found, using system Python"
    fi
    
    # 检查Python版本
    python_version=$(python3 --version 2>&1)
    log "Python version: $python_version"
    
    # 检查关键依赖
    if ! python3 -c "import fastapi, uvicorn, fastmcp" 2>/dev/null; then
        error "Required dependencies not found. Please run: pip install -r requirements.txt"
        exit 1
    fi
    
    success "Python environment check passed"
}

# 启动FastAPI服务
start_fastapi() {
    log "Starting FastAPI service..."
    
    nohup python3 main.py > fastapi_service.log 2>&1 &
    local pid=$!
    
    echo $pid > fastapi.pid
    log "FastAPI service started with PID: $pid"
    
    # 等待服务启动
    sleep 5
    
    if check_port $FASTAPI_PORT "FastAPI"; then
        success "FastAPI service is running on port $FASTAPI_PORT"
        return 0
    else
        error "FastAPI service failed to start"
        return 1
    fi
}

# 启动MCP服务
start_mcp() {
    log "Starting MCP service..."
    
    nohup python3 scripts/run_mcp_streamable.py > mcp_service.log 2>&1 &
    local pid=$!
    
    echo $pid > mcp.pid
    log "MCP service started with PID: $pid"
    
    # 等待服务启动
    sleep 5
    
    if check_port $MCP_PORT "MCP"; then
        success "MCP service is running on port $MCP_PORT"
        return 0
    else
        error "MCP service failed to start"
        return 1
    fi
}

# 检查服务健康状态
check_health() {
    log "Checking service health..."
    
    # 检查FastAPI健康
    if curl -f -s "http://localhost:$FASTAPI_PORT/health" > /dev/null; then
        success "FastAPI service is healthy"
    else
        warn "FastAPI health check failed"
    fi
    
    # 检查MCP健康 (简单的端口检查)
    if check_port $MCP_PORT "MCP"; then
        success "MCP service is responsive"
    else
        warn "MCP service is not responsive"
    fi
}

# 主函数
main() {
    log "=== $SERVICE_NAME Service Restart Started ==="
    
    # 停止现有服务
    log "Stopping existing services..."
    stop_port $FASTAPI_PORT "FastAPI" || true
    stop_port $MCP_PORT "MCP" || true
    
    # 清理旧的PID文件
    rm -f fastapi.pid mcp.pid 2>/dev/null || true
    
    # 检查Python环境
    check_python_env
    
    # 启动服务
    log "Starting services..."
    
    if start_fastapi && start_mcp; then
        success "All services started successfully"
        
        # 健康检查
        sleep 2
        check_health
        
        log "=== Service Information ==="
        log "FastAPI Service: http://localhost:$FASTAPI_PORT"
        log "API Documentation: http://localhost:$FASTAPI_PORT/docs"
        log "MCP Service: http://localhost:$MCP_PORT/mcp/v1"
        log "Log files: fastapi_service.log, mcp_service.log"
        log "=== $SERVICE_NAME Service Restart Completed ==="
        
        success "🎉 $SERVICE_NAME services are ready!"
        
    else
        error "Failed to start services"
        exit 1
    fi
}

# 运行主函数
main "$@"