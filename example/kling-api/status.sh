#!/bin/bash

# Kling API 服务状态检查脚本

FASTAPI_PORT=5511
MCP_PORT=5510

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Kling API Service Status ===${NC}"

# 检查FastAPI服务
if lsof -ti:$FASTAPI_PORT > /dev/null 2>&1; then
    pid=$(lsof -ti:$FASTAPI_PORT)
    echo -e "${GREEN}✓ FastAPI Service${NC}: Running (PID: $pid, Port: $FASTAPI_PORT)"
    echo -e "  URL: http://localhost:$FASTAPI_PORT"
    echo -e "  Docs: http://localhost:$FASTAPI_PORT/docs"
else
    echo -e "${RED}✗ FastAPI Service${NC}: Not running"
fi

# 检查MCP服务
if lsof -ti:$MCP_PORT > /dev/null 2>&1; then
    pid=$(lsof -ti:$MCP_PORT)
    echo -e "${GREEN}✓ MCP Service${NC}: Running (PID: $pid, Port: $MCP_PORT)"
    echo -e "  URL: http://localhost:$MCP_PORT/mcp/v1"
else
    echo -e "${RED}✗ MCP Service${NC}: Not running"
fi

# 检查日志文件
echo -e "\n${BLUE}=== Log Files ===${NC}"
for log_file in fastapi_service.log mcp_service.log restart.log; do
    if [ -f "$log_file" ]; then
        size=$(du -h "$log_file" | cut -f1)
        echo -e "${GREEN}✓${NC} $log_file ($size)"
    else
        echo -e "${YELLOW}-${NC} $log_file (not found)"
    fi
done

echo -e "\n${BLUE}=== Quick Commands ===${NC}"
echo -e "Start services: ${GREEN}./restart.sh${NC}"
echo -e "Stop services:  ${GREEN}./stop.sh${NC}"
echo -e "View logs:      ${GREEN}tail -f fastapi_service.log${NC} or ${GREEN}tail -f mcp_service.log${NC}"