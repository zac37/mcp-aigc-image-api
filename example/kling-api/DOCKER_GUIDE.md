# Kling API Docker 部署指南

## 📋 概述

本指南将帮助您使用Docker部署Kling API服务，包含FastAPI和MCP两个服务。

## 🚀 快速开始

### 1. 使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up --build

# 后台运行
docker-compose up -d --build

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f kling-api
```

### 2. 使用 Docker 命令

```bash
# 构建镜像
docker build -t kling-api:latest .

# 运行容器
docker run -d \
  --name kling-api-container \
  -p 5511:5511 \
  -p 5510:5510 \
  -v $(pwd)/docker-logs:/app/logs \
  kling-api:latest

# 查看日志
docker logs -f kling-api-container

# 停止容器
docker stop kling-api-container

# 删除容器
docker rm kling-api-container
```

## 🔧 配置说明

### 环境变量配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `HOST` | `0.0.0.0` | 服务器监听地址 |
| `PORT` | `5511` | FastAPI服务端口 |
| `MCP_PORT` | `5510` | MCP服务端口 |
| `DEBUG` | `false` | 调试模式 |
| `LOG_LEVEL` | `info` | 日志级别 |
| `KLING_API_BASE_URL` | `https://api.chatfire.cn` | Kling API基础URL |
| `KLING_REQUEST_TIMEOUT` | `30` | API请求超时时间 |
| `MAX_POOL_CONNECTIONS` | `100` | 最大连接池大小 |

### API-KEY 配置

API-KEY已经配置在代码中：`sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY`

如需修改，请编辑 `core/config.py` 文件中的 `api_key` 字段。

## 📁 目录结构

```
kling-api/
├── Dockerfile                 # Docker镜像构建文件
├── docker-compose.yml        # Docker Compose配置
├── docker-entrypoint.sh      # 容器启动脚本
├── .dockerignore             # Docker构建忽略文件
├── docker-logs/              # 日志挂载目录（自动创建）
└── ...                       # 其他项目文件
```

## 🌐 服务端点

启动成功后，可以通过以下地址访问服务：

- **FastAPI服务**: http://localhost:5511
- **API文档**: http://localhost:5511/docs
- **健康检查**: http://localhost:5511/api/health
- **MCP服务**: http://localhost:5510/mcp/v1

## 📝 API 使用示例

### 文生图

```bash
curl -X POST http://localhost:5511/api/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只可爱的小猫咪",
    "aspect_ratio": "1:1",
    "cfg_scale": 0.8
  }'
```

### 查询任务状态

```bash
curl http://localhost:5511/api/tasks/{task_id}/status
```

### 获取任务结果

```bash
curl http://localhost:5511/api/tasks/{task_id}/result
```

## 🔍 故障排查

### 检查容器状态

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker-compose logs kling-api

# 进入容器调试
docker exec -it kling-api-service /bin/bash
```

### 检查服务健康状态

```bash
# 健康检查
curl http://localhost:5511/api/health

# 检查端口是否可用
netstat -tlnp | grep :5511
```

### 重建和重启

```bash
# 重建镜像
docker-compose build --no-cache

# 强制重启
docker-compose down && docker-compose up -d --build
```

## 📊 监控和日志

### 查看实时日志

```bash
# Docker Compose
docker-compose logs -f kling-api

# Docker 命令
docker logs -f kling-api-container
```

### 日志文件位置

- 容器内日志: `/app/logs/`
- 宿主机日志: `./docker-logs/`

### 主要日志文件

- `fastapi_service.log` - FastAPI服务日志
- `mcp_service.log` - MCP服务日志

## 🔒 安全考虑

1. **API密钥管理**: API-KEY已配置在代码中，生产环境建议使用环境变量
2. **网络安全**: 默认暴露5511和5510端口，生产环境建议使用反向代理
3. **资源限制**: docker-compose.yml中已配置资源限制

## 🛠️ 高级配置

### 自定义环境变量

创建 `.env` 文件：

```env
# 服务配置
HOST=0.0.0.0
PORT=5511
DEBUG=false

# 性能调优
MAX_POOL_CONNECTIONS=200
MAX_CONCURRENT_REQUESTS=150
WORKERS=8
```

### 生产环境部署

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🎯 性能优化

- **资源限制**: 默认限制CPU 2核心，内存2GB
- **并发配置**: 支持100个并发连接
- **缓存策略**: 启用HTTP连接池缓存
- **日志优化**: 结构化日志输出

## 📞 技术支持

如遇到问题，请检查：
1. Docker和Docker Compose版本
2. 端口是否被占用
3. 网络连接是否正常
4. 日志文件中的错误信息

---

**版本**: 1.0.0  
**更新时间**: 2025-07-23 