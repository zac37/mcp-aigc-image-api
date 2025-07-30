# Docker部署指南

本项目提供了两种Docker部署方式：本地部署和远程部署。

## 🏠 本地部署

### 使用自动更新脚本

```bash
# 更新Docker容器为最新代码
./update-docker.sh
```

### 手动部署步骤

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止现有服务
docker-compose down

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 检查服务状态
docker-compose ps
```

## 🌐 远程部署

### 前提条件

1. **SSH访问权限**: 确保可以SSH连接到远程服务器
2. **Docker环境**: 远程服务器已安装Docker和docker-compose
3. **网络访问**: 服务器可访问GitHub拉取代码

### 使用远程部署脚本

```bash
# 部署到远程服务器 (8.219.206.213)
./deploy-remote.sh
```

### 手动远程部署

```bash
# 1. SSH连接到远程服务器
ssh ecs-user@8.219.206.213

# 2. 进入项目目录（如果不存在则先克隆）
cd ~/mcp-aigc-image-api
# 或者克隆: git clone https://github.com/zac37/mcp-aigc-image-api.git ~/mcp-aigc-image-api

# 3. 拉取最新代码
git pull origin main

# 4. 停止现有服务
docker-compose down

# 5. 重新构建并启动
docker-compose build --no-cache
docker-compose up -d
```

## 📊 服务验证

### 本地服务地址
- FastAPI服务: http://localhost:5512
- API文档: http://localhost:5512/docs
- MCP服务: http://localhost:5513/mcp/v1
- MinIO控制台: http://localhost:9001

### 远程服务地址
- FastAPI服务: http://8.219.206.213:5512
- API文档: http://8.219.206.213:5512/docs
- MCP服务: http://8.219.206.213:5513/mcp/v1
- MinIO控制台: http://8.219.206.213:9001

### 健康检查命令

```bash
# 检查FastAPI服务
curl http://localhost:5512/api/health
curl http://8.219.206.213:5512/api/health

# 检查MCP服务
curl http://localhost:5513/mcp/v1/health
curl http://8.219.206.213:5513/mcp/v1/health

# 查看容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f images-api
```

## 🔧 故障排除

### 常见问题

1. **端口占用**: 确保5512、5513、9000、9001端口未被占用
2. **权限问题**: 确保Docker daemon运行且有权限
3. **网络问题**: 检查防火墙设置和端口开放状态
4. **资源不足**: 确保服务器有足够的内存和磁盘空间

### 查看详细日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs images-api
docker-compose logs minio

# 实时查看日志
docker-compose logs -f images-api
```

### 重置服务

```bash
# 完全重置（删除所有数据）
docker-compose down -v
docker system prune -a
docker-compose up -d
```

## 🚀 新功能部署

当添加新功能（如GPT图像编辑）后：

1. **本地测试**: 确保本地功能正常
2. **提交代码**: `git add . && git commit -m "feature description"`
3. **推送代码**: `git push origin main`
4. **远程部署**: `./deploy-remote.sh`
5. **功能验证**: 测试新功能是否正常工作

## 📝 部署检查清单

- [ ] 代码已提交并推送到GitHub
- [ ] Docker环境正常
- [ ] 端口未被占用
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] API文档可访问
- [ ] 新功能测试通过