#!/bin/bash

# 远程服务器部署脚本
# 版本: v1.0
# 更新时间: 2025-07-23

set -e  # 遇到错误时退出

# 服务器配置
REMOTE_HOST="8.219.206.213"
REMOTE_USER="ecs-user"
REMOTE_PASSWORD="5bmIINW6OUdwgpX#@u"
REMOTE_PATH="/home/ecs-user/kling-api"

# 本地项目路径
LOCAL_PATH="$(pwd)"
PROJECT_NAME="kling-api"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# 检查依赖
check_dependencies() {
    log "检查本地依赖..."
    
    if ! command -v sshpass &> /dev/null; then
        error "sshpass 未安装。请安装: brew install sshpass (macOS) 或 apt-get install sshpass (Linux)"
        exit 1
    fi
    
    if ! command -v rsync &> /dev/null; then
        error "rsync 未安装。请安装 rsync"
        exit 1
    fi
    
    log "依赖检查通过"
}

# 测试远程连接
test_connection() {
    log "测试远程服务器连接..."
    
    if sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "echo '连接成功'" &> /dev/null; then
        log "远程服务器连接成功"
    else
        error "无法连接到远程服务器"
        exit 1
    fi
}

# 同步代码到远程服务器
sync_code() {
    log "同步代码到远程服务器..."
    
    # 先确保远程服务器有rsync
    log "检查远程服务器rsync..."
    sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "
        if ! command -v rsync &> /dev/null; then
            echo '安装rsync...'
            sudo yum install -y rsync || sudo apt-get install -y rsync
        fi
    "
    
    # 排除不需要的文件
    EXCLUDE_PATTERNS=(
        "--exclude=__pycache__"
        "--exclude=*.pyc"
        "--exclude=*.pyo"
        "--exclude=.git"
        "--exclude=.gitignore"
        "--exclude=.DS_Store"
        "--exclude=node_modules"
        "--exclude=*.log"
        "--exclude=docker-logs"
        "--exclude=.env"
        "--exclude=venv"
        "--exclude=env"
    )
    
    # 使用 rsync 同步文件
    sshpass -p "${REMOTE_PASSWORD}" rsync -avz --delete \
        "${EXCLUDE_PATTERNS[@]}" \
        "${LOCAL_PATH}/" \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
    
    if [ $? -eq 0 ]; then
        log "代码同步完成"
    else
        error "代码同步失败"
        exit 1
    fi
}

# 在远程服务器上执行部署
deploy_remote() {
    log "在远程服务器上执行部署..."
    
    # 创建远程部署脚本
    REMOTE_SCRIPT="
    set -e
    
    echo '开始远程部署...'
    cd ${REMOTE_PATH}
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        echo '安装Docker...'
        sudo yum update -y
        sudo yum install -y docker
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker \$(whoami)
    fi
    
    # 检查docker-compose是否安装
    if ! command -v docker-compose &> /dev/null; then
        echo '安装Docker Compose...'
        sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64\" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi
    
    # 创建必要的目录
    mkdir -p docker-logs
    mkdir -p logs
    
    # 停止现有容器（如果存在）
    sudo docker-compose down 2>/dev/null || true
    
    # 清理旧的镜像
    sudo docker system prune -f 2>/dev/null || true
    
    # 构建并启动服务
    echo '构建Docker镜像...'
    sudo docker-compose build --no-cache
    
    echo '启动服务...'
    sudo docker-compose up -d
    
    # 等待服务启动
    echo '等待服务启动...'
    sleep 15
    
    # 检查服务状态
    echo '检查服务状态:'
    sudo docker-compose ps
    
    # 检查服务健康状态
    echo '检查API健康状态:'
    curl -f http://localhost:5511/api/health || echo 'API健康检查失败'
    
    echo '远程部署完成!'
    echo '服务访问地址:'
    echo '  FastAPI: http://${REMOTE_HOST}:5511'
    echo '  MCP服务: http://${REMOTE_HOST}:5510'
    echo '  健康检查: http://${REMOTE_HOST}:5511/api/health'
    echo '  API文档: http://${REMOTE_HOST}:5511/docs'
    "
    
    # 执行远程脚本
    sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "${REMOTE_SCRIPT}"
}

# 验证部署
verify_deployment() {
    log "验证远程部署..."
    
    # 检查API健康状态
    if curl -f "http://${REMOTE_HOST}:5511/api/health" &> /dev/null; then
        log "✅ FastAPI服务运行正常"
    else
        warning "⚠️ FastAPI服务可能未正常启动"
    fi
    
    # 检查MCP服务状态（简单连接测试）
    if nc -z "${REMOTE_HOST}" 5510 &> /dev/null 2>&1; then
        log "✅ MCP服务端口可访问"
    else
        warning "⚠️ MCP服务端口不可访问"
    fi
}

# 显示部署后信息
show_info() {
    echo
    log "🎉 部署完成!"
    echo
    echo -e "${BLUE}服务访问信息:${NC}"
    echo "  🌐 FastAPI服务: http://${REMOTE_HOST}:5511"
    echo "  🔧 MCP服务: http://${REMOTE_HOST}:5510"
    echo "  ❤️ 健康检查: http://${REMOTE_HOST}:5511/api/health"
    echo "  📚 API文档: http://${REMOTE_HOST}:5511/docs"
    echo
    echo -e "${BLUE}管理命令:${NC}"
    echo "  查看日志: ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && sudo docker-compose logs -f'"
    echo "  重启服务: ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && sudo docker-compose restart'"
    echo "  停止服务: ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && sudo docker-compose down'"
    echo
    echo -e "${YELLOW}安全提醒:${NC}"
    echo "  🔒 请及时修改服务器密码"
    echo "  🔒 建议配置SSH密钥认证"
    echo "  🔒 考虑配置防火墙规则"
}

# 主函数
main() {
    echo -e "${GREEN}"
    echo "============================================"
    echo "  Kling API 远程服务器部署脚本"
    echo "  目标服务器: ${REMOTE_HOST}"
    echo "============================================"
    echo -e "${NC}"
    
    warning "⚠️ 安全提醒: 当前使用明文密码连接，建议部署后立即配置SSH密钥认证"
    
    read -p "是否继续部署? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 1
    fi
    
    check_dependencies
    test_connection
    sync_code
    deploy_remote
    verify_deployment
    show_info
}

# 运行主函数
main "$@" 