# Docker部署经验总结

## 部署概述

本次成功将Images API服务部署到远程服务器的Docker环境中，包含FastAPI服务(端口5512)、MCP服务(端口5513)和Celery Worker。

## 部署环境

- **远程服务器**: 8.219.206.213
- **用户**: ecs-user
- **架构**: x86_64 (远程) vs arm64 (本地)
- **Docker版本**: 28.3.2
- **外部依赖**: jarvis_redis, jarvis_minio (通过jarvis-v2_default网络)

## 部署脚本选择

### 1. `deploy-remote-production.sh` - 传统部署方式 ✅
- 直接在远程服务器上构建镜像
- 适合网络良好、远程服务器性能足够的情况
- **推荐使用**，部署过程更稳定

### 2. `build-and-deploy.sh` - 跨平台构建部署
- 本地构建arm64→amd64跨平台镜像
- 传输镜像文件到远程服务器
- 适合本地和远程架构不同且远程构建困难的情况

## 遇到的问题及解决方案

### 1. 全局变量未定义错误
**问题**: `_veo3_client`变量在cleanup函数中被引用但未定义
```bash
NameError: name '_veo3_client' is not defined
```

**解决方案**: 在`core/images_client.py`中添加全局变量定义
```python
# 全局客户端实例
_images_client: Optional[ImagesAPIClient] = None
_veo3_client: Optional[Any] = None  # 添加这行
_vertex_veo_client: Optional[VertexAIVeoClient] = None
```

### 2. Docker启动脚本PID处理错误
**问题**: `start_service()`函数错误地返回PID值，导致后续检查失败
```bash
return $pid  # 错误：bash函数返回值应该是0-255的状态码
```

**解决方案**: 修改`docker-entrypoint.sh`，将PID写入临时文件
```bash
# 修改前
return $pid

# 修改后
echo $pid > "/tmp/${service_name}.pid"
return 0

# 获取PID的方式也相应修改
FASTAPI_PID=$(cat /tmp/fastapi.pid)
```

### 3. 日志文件权限问题
**问题**: 容器中appuser无法创建/写入日志文件
```bash
PermissionError: [Errno 13] Permission denied: '/app/logs/access.log'
```

**解决方案组合**:
1. **Dockerfile权限修复**:
```dockerfile
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs  # 添加日志目录写权限
```

2. **临时禁用访问日志中间件**:
```python
# 注释掉访问日志中间件避免权限问题
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
```

3. **部署时清理旧日志**:
```bash
sudo rm -rf logs/*  # 清理权限混乱的旧日志文件
```

## 成功部署验证

### 服务状态检查
```bash
# 检查容器状态
sudo docker-compose -f docker-compose.production.yml ps

# 检查健康状态
curl http://8.219.206.213:5512/api/health

# 检查根路径
curl http://8.219.206.213:5512/

# 检查MCP服务
curl http://8.219.206.213:5513/mcp/v1
```

### 最终服务地址
- 🌐 **API文档**: http://8.219.206.213:5512/docs
- 💗 **健康检查**: http://8.219.206.213:5512/api/health  
- 🔧 **MCP服务**: http://8.219.206.213:5513/mcp/v1
- 📋 **服务信息**: http://8.219.206.213:5512/

## 部署最佳实践

### 1. 预部署检查
```bash
# 执行Docker兼容性检查
./check_docker_compatibility.sh

# 测试SSH连接
ssh ecs-user@8.219.206.213 "echo 'SSH连接测试'"

# 检查外部服务状态
sudo docker ps | grep jarvis_redis
sudo docker ps | grep jarvis_minio
```

### 2. 部署流程
```bash
# 使用推荐的部署脚本
chmod +x deploy-remote-production.sh
./deploy-remote-production.sh
```

### 3. 故障排查命令
```bash
# 查看服务日志
ssh ecs-user@8.219.206.213 'cd /home/ecs-user/images-api && sudo docker-compose -f docker-compose.production.yml logs --tail=50'

# 重启服务
ssh ecs-user@8.219.206.213 'cd /home/ecs-user/images-api && sudo docker-compose -f docker-compose.production.yml restart'

# 进入容器调试
ssh ecs-user@8.219.206.213 'sudo docker exec -it images-api-service bash'

# 检查容器内权限
sudo docker exec images-api-service ls -la /app/logs/
```

## 关键配置文件

### docker-compose.production.yml
- 使用外部Redis和MinIO服务
- 连接jarvis-v2_default网络
- 资源限制：2G内存，1.8核CPU
- 健康检查配置

### Dockerfile
- 基于Python 3.11-slim
- 创建appuser非root用户
- 正确设置日志目录权限
- 多阶段构建优化

### docker-entrypoint.sh
- 健壮的服务启动脚本
- 外部服务依赖检查
- 进程监控和自动重启
- 正确的PID管理

## 经验教训

1. **权限问题预防**: 在Dockerfile中正确设置目录权限，避免运行时权限冲突
2. **日志策略**: 生产环境建议使用Docker日志驱动而非文件日志，避免权限问题
3. **依赖检查**: 部署前充分检查外部服务依赖，确保网络连通性
4. **脚本调试**: bash脚本中函数返回值要正确处理，避免PID等大数值返回
5. **分阶段部署**: 先解决基础问题（权限、网络），再处理业务逻辑
6. **快速修复**: 遇到权限等阻塞性问题时，可以临时禁用相关功能先让服务运行

## 后续优化建议

1. **日志系统**: 重新启用访问日志，使用Docker volume挂载解决权限问题
2. **监控告警**: 集成Prometheus监控和告警系统
3. **自动化CI/CD**: 基于成功的部署脚本建立自动化流水线
4. **备份策略**: 定期备份配置文件和重要数据
5. **安全加固**: 使用secrets管理敏感信息，限制容器权限

## 支持的AI模型

部署成功后支持以下15+种AI图像/视频生成模型：
- GPT (DALL-E 2/3)
- Recraft / Recraftv3  
- 即梦3.0 / 即梦垫图
- FLUX / Flux-kontext
- Cogview / 混元 / Kling
- Stable Diffusion / Kolors
- 虚拟换衣 / 海螺图片 / Doubao
- Veo3视频生成

总结：本次部署虽然遇到了一些技术问题，但通过系统性的问题定位和解决，最终成功部署了一个完整的多模型AI图像生成服务。部署过程中的经验和解决方案为后续类似项目提供了宝贵参考。