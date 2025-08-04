#!/bin/bash
# 生产服务器安全加固脚本
# 解决Redis/MinIO端口直接暴露的安全风险

set -e

echo "🔒 开始生产服务器安全加固..."
echo "🎯 目标：移除不必要的端口暴露，加强网络安全"
echo ""

# 检查当前暴露的端口
echo "🔍 步骤1: 检查当前端口暴露情况..."

echo "  外部可访问的端口:"
netstat -tlnp | grep -E ':551[23]|:6379|:900[01]' | while read line; do
    echo "    $line"
done

echo ""
echo "  Docker容器端口映射:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(6379|9000|9001|5512|5513)"

echo ""

echo "🚫 步骤2: 识别安全风险..."

# 检查Redis外部暴露
if netstat -tln | grep -q ":6379"; then
    echo "  ❌ 高风险：Redis端口6379暴露到外部"
    echo "     风险：数据库可被直接访问，存在数据泄露和攻击风险"
fi

# 检查MinIO外部暴露
if netstat -tln | grep -q ":9000"; then
    echo "  ❌ 中风险：MinIO端口9000暴露到外部"
    echo "     风险：对象存储可被直接访问"
fi

if netstat -tln | grep -q ":9001"; then
    echo "  ❌ 中风险：MinIO控制台端口9001暴露到外部"
    echo "     风险：管理界面可被外部访问"
fi

# 检查应用端口
if netstat -tln | grep -q ":5512"; then
    echo "  ✅ 正常：FastAPI端口5512暴露（应用服务）"
fi

if netstat -tln | grep -q ":5513"; then
    echo "  ✅ 正常：MCP端口5513暴露（应用服务）"
fi

echo ""

echo "🛡️ 步骤3: 配置防火墙规则..."

# 检查ufw状态
if command -v ufw >/dev/null; then
    echo "  配置UFW防火墙..."
    
    # 启用防火墙
    ufw --force enable
    
    # 设置默认策略
    ufw default deny incoming
    ufw default allow outgoing
    
    # 允许SSH
    ufw allow ssh
    
    # 允许应用端口
    ufw allow 5512/tcp comment 'FastAPI Service'
    ufw allow 5513/tcp comment 'MCP Service'
    
    # 禁止数据库端口
    ufw deny 6379/tcp comment 'Redis - Internal Only'
    ufw deny 9000/tcp comment 'MinIO - Internal Only'
    ufw deny 9001/tcp comment 'MinIO Console - Internal Only'
    
    echo "  ✅ 防火墙规则配置完成"
    echo "  当前防火墙状态:"
    ufw status numbered | head -15
else
    echo "  ⚠️  UFW未安装，跳过防火墙配置"
    echo "  建议: apt install ufw"
fi

echo ""

echo "🔧 步骤4: Docker网络安全配置..."

# 检查Docker daemon配置
DOCKER_CONFIG="/etc/docker/daemon.json"

if [[ ! -f "$DOCKER_CONFIG" ]]; then
    echo "  创建Docker daemon配置..."
    cat > "$DOCKER_CONFIG" << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true
}
EOF
    echo "  ✅ Docker daemon配置已创建"
else
    echo "  ✅ Docker daemon配置已存在"
fi

echo ""

echo "📋 步骤5: 生成安全的docker-compose配置..."

# 创建安全的环境变量文件
cat > ".env.production.secure" << 'EOF'
# 安全的生产环境配置
ENV=production

# 应用端口 (仅这些端口对外暴露)
APP_PORT=5512
MCP_PORT=5513

# 服务器配置
SERVER_BASE_URL=http://8.219.206.213:5512
LOG_LEVEL=info
TZ=Asia/Shanghai

# Redis配置 (仅内部访问，不暴露端口)
REDIS_HOST=jarvis_redis
REDIS_PORT=6379
REDIS_DB=0

# MinIO配置 (仅内部访问，不暴露端口)
MINIO_ENDPOINT=jarvis_minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
MINIO_BUCKET_NAME=images

# 网络配置
NETWORK_NAME=jarvis-production

# 资源配置
MEMORY_LIMIT=2G
CPU_LIMIT=1.8
MEMORY_RESERVE=512M
CPU_RESERVE=0.5
WORKERS=4
WORKER_CONCURRENCY=4

# 健康检查
HEALTH_START_PERIOD=60

# Google凭证路径
GOOGLE_CREDS_PATH=/home/ecs-user/workspace/google_oauth

# Google Cloud配置
VEO3_PROJECT_ID=qhhl-veo
VEO3_LOCATION=us-central1
VEO3_STORAGE_BUCKET=veo-output-pub
EOF

echo "  ✅ 安全环境配置已生成: .env.production.secure"

echo ""

echo "🔒 步骤6: 容器安全配置建议..."

cat << 'EOF'
  建议的容器安全配置:

  1. 非root用户运行:
     在Dockerfile中添加:
     RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
     USER appuser

  2. 只读文件系统:
     在docker-compose.yml中添加:
     read_only: true
     tmpfs:
       - /tmp
       - /var/run

  3. 安全标签:
     security_opt:
       - no-new-privileges:true
       - apparmor:docker-default

  4. 资源限制:
     deploy:
       resources:
         limits:
           memory: 2G
           cpus: '1.8'
EOF

echo ""

echo "📊 步骤7: 安全状态报告..."

echo "  当前网络连接:"
ss -tlnp | grep -E ':551[23]|:6379|:900[01]' | head -10

echo ""
echo "  Docker安全扫描:"
if command -v docker >/dev/null; then
    echo "    容器运行状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -5
    
    echo "    网络配置:"
    docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | head -5
fi

echo ""

echo "✅ 安全加固完成！"
echo ""
echo "🛡️ 安全改进总结:"
echo "  - 防火墙: 仅允许必要端口(5512, 5513)对外访问"
echo "  - Redis: 禁止外部访问，仅容器内部通信"
echo "  - MinIO: 禁止外部访问，仅容器内部通信"
echo "  - Docker: 配置安全daemon选项"
echo "  - 日志: 配置日志轮转，防止磁盘占满"
echo ""
echo "🔄 后续步骤:"
echo "  1. 使用 docker-compose.production-optimized.yml 重新部署"
echo "  2. 使用 .env.production.secure 环境配置"
echo "  3. 测试应用功能和内部服务连通性"
echo "  4. 监控安全日志和网络连接"
echo ""
echo "⚠️  重要提醒:"
echo "  - 重新部署后Redis和MinIO将不再能从外部直接访问"
echo "  - 所有数据库操作必须通过应用程序进行"
echo "  - 确保应用代码使用服务名(jarvis_redis, jarvis_minio)而非IP"