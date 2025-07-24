# Kling API 代理服务

🚀 **基于 FastMCP 的 Kling AI API 服务，支持 Streamable HTTP 协议**

## 📋 项目概述

这是一个完整的 Kling AI API 代理服务，提供了文生图、文生视频、图生视频、虚拟换衣等功能，支持Streamable HTTP协议，包含智能服务管理脚本和完整的技术文档。

### ✨ 主要特性

- 🖼️ **文生图功能** - 根据文本描述生成高质量图像
- 🎬 **文生视频功能** - 根据文本描述生成视频内容  
- 📱 **图生视频功能** - 基于输入图像生成相关视频
- 👕 **虚拟换衣功能** - AI驱动的虚拟试衣体验
- 🔄 **任务管理** - 异步任务状态查询和结果获取
- 🛠️ **双协议支持** - FastAPI REST API + MCP Protocol
- 🚀 **智能服务管理** - 自动化启停和健康监控
- 📚 **详细技术文档** - 完整的API文档和使用指南

### 🏗️ 技术架构

```
Kling API 代理服务
├── FastAPI 服务 (端口 5511)     # REST API接口
├── MCP 服务 (端口 5510)        # MCP协议接口
├── FastMCP 2.5.1              # MCP协议框架
├── Python 3.11+               # 运行环境
└── Streamable HTTP            # 实时通信协议
```

## 🛠️ 安装和设置

### 1. 环境要求

- Python 3.11+
- Kling API 访问密钥 (格式: sk-xxxx)

### 2. 快速安装

```bash
# 克隆仓库
git clone <repository-url>
cd kling-api

# 创建虚拟环境
python3.11 -m venv .venv_py311
source .venv_py311/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 根据需要编辑 .env 文件
```

### 3. API 密钥配置

**重要说明**：本服务采用请求时传递API密钥的方式，无需在环境变量中配置。

API 鉴权格式：
```
Authorization: Bearer sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY
```

## 🚀 服务管理

### 快速启动

```bash
# 🔥 智能重启服务（推荐）
./restart.sh

# 📊 检查服务状态
./status.sh

# 🛑 停止服务
./stop.sh
```

### 服务信息

- **FastAPI 服务**: http://localhost:5511
- **API 文档**: http://localhost:5511/docs  
- **MCP 服务**: http://localhost:5510/mcp/v1
- **协议类型**: Streamable HTTP (POST + SSE)

## 📡 API 接口说明

### 🎨 文生图接口

```bash
POST /api/images/generations
```

**请求示例:**
```json
{
  "prompt": "一只可爱的小猫在花园里玩耍",
  "aspect_ratio": "1:1",
  "negative_prompt": "低质量，模糊",
  "cfg_scale": 7.5,
  "seed": 12345
}
```

### 🎬 文生视频接口

```bash
POST /api/videos/text-to-video
```

**请求示例:**
```json
{
  "prompt": "海边日落，海浪轻拍沙滩",
  "aspect_ratio": "16:9",
  "duration": 5,
  "cfg_scale": 7.5
}
```

### 📱 图生视频接口

```bash
POST /api/videos/image-to-video
```

**请求示例:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "prompt": "让图片中的人物挥手",
  "duration": 5,
  "cfg_scale": 7.5
}
```

### 👕 虚拟换衣接口

```bash
POST /api/try-on/virtual
```

**请求示例:**
```json
{
  "person_image": "https://example.com/person.jpg",
  "garment_image": "https://example.com/garment.jpg",
  "category": "tops"
}
```

### 📊 任务管理接口

```bash
# 获取任务状态
GET /api/tasks/{task_id}/status

# 获取任务结果
GET /api/tasks/{task_id}/result

# 获取任务完整信息
GET /api/tasks/{task_id}

# 等待任务完成
POST /api/tasks/{task_id}/wait
```

## 🔧 MCP 工具函数

本服务提供 8 个 MCP 工具函数：

1. **create_text_to_image_tool** - 创建文生图任务
2. **create_text_to_video_tool** - 创建文生视频任务  
3. **create_image_to_video_tool** - 创建图生视频任务
4. **create_virtual_try_on_tool** - 创建虚拟换衣任务
5. **get_task_status_tool** - 获取任务状态
6. **get_task_result_tool** - 获取任务结果
7. **get_single_task_tool** - 获取任务完整信息
8. **wait_for_task_completion_tool** - 等待任务完成

### MCP 客户端配置示例

```json
{
  "mcpServers": {
    "kling-api": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://localhost:5510/mcp/v1",
        "-H", "Content-Type: application/json"
      ]
    }
  }
}
```

## 🔧 开发

### 项目结构

```
kling-api/
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志系统
│   └── kling_client.py    # Kling API客户端
├── services/              # 业务逻辑层
│   └── kling_service.py   # Kling服务封装
├── routers/              # 路由层
│   ├── api.py           # FastAPI路由
│   └── mcp/             # MCP工具
│       ├── main.py      # MCP应用
│       └── kling_tools.py # MCP工具函数
├── scripts/              # 管理脚本
│   └── run_mcp_streamable.py # MCP启动脚本
├── logs/                 # 日志目录
├── main.py              # FastAPI主应用
├── restart.sh           # 服务重启脚本
├── stop.sh             # 服务停止脚本
└── status.sh           # 状态检查脚本
```

### 本地开发

```bash
# 激活虚拟环境
source .venv_py311/bin/activate

# 启动 FastAPI 服务（开发模式）
python main.py

# 启动 MCP 服务（另一个终端）
python scripts/run_mcp_streamable.py
```

## 🚨 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   ./restart.sh  # 自动处理端口冲突
   ```

2. **服务无响应**
   ```bash
   ./status.sh   # 检查服务状态
   ./restart.sh  # 强制重启
   ```

3. **API 认证失败**
   - 确保 Authorization header 格式正确：`Bearer sk-xxx`
   - 检查 API 密钥是否有效

4. **查看详细日志**
   ```bash
   tail -f fastapi_service.log  # FastAPI服务日志
   tail -f mcp_service.log      # MCP服务日志
   tail -f restart.log          # 重启日志
   ```

### 日志文件说明

- `fastapi_service.log` - FastAPI服务运行日志
- `mcp_service.log` - MCP服务运行日志  
- `restart.log` - 服务启停日志
- `logs/main.log` - 主应用日志
- `logs/api.log` - API调用日志
- `logs/access.log` - HTTP访问日志

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请查看：
1. [API 文档](http://localhost:5511/docs) (服务运行时可用)
2. 项目日志文件
3. GitHub Issues

---

⭐ 如果这个项目对您有帮助，请给个星星！

## 🔗 相关链接

- [Kling AI 官网](https://kling.kuaishou.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [FastMCP 项目](https://github.com/jlowin/fastmcp)