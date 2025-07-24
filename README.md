# Images API Service

基于 FastAPI 和 MCP 协议的多模型图像生成 AI 服务，支持多种主流图像生成模型的统一接口。

## 🌟 功能特性

### 支持的图像生成模型
- **GPT (DALL-E)**: OpenAI的DALL-E 2和DALL-E 3模型
- **Recraft**: 专业的图像创作工具  
- **即梦3.0 (Seedream)**: 先进的图像生成技术
- **即梦垫图 (SeedEdit)**: 基于现有图像的智能编辑
- **FLUX**: 高质量的开源图像生成模型
- **Recraftv3**: 最新版本的Recraft图像生成
- **Cogview**: 清华大学的图像生成模型
- **混元**: 腾讯的图像生成技术
- **Kling**: 快手的图像生成服务
- **Stable Diffusion**: 经典的开源图像生成模型
- **Kolors**: 多彩图像生成技术
- **虚拟换衣**: AI驱动的虚拟试衣功能
- **flux-kontext**: 上下文感知的图像生成
- **海螺图片**: 海螺AI的图像生成
- **Doubao**: 字节跳动的图像生成

### 双协议支持
- **FastAPI**: RESTful API接口，兼容OpenAI格式
- **MCP**: Model Context Protocol，支持streamable-http传输

## 🚀 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动所有服务
./restart.sh

# 或分别启动
python main.py                          # FastAPI服务 (端口5512)
python scripts/run_mcp_streamable.py    # MCP服务 (端口5513)
```

### 检查服务状态

```bash
./status.sh
```

### 停止服务

```bash
./stop.sh
```

## 📚 API 使用示例

### FastAPI 接口

#### GPT图像生成
```bash
curl -X POST "http://localhost:5512/api/gpt/generations" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over a mountain landscape",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "style": "vivid"
  }'
```

#### Recraft图像生成
```bash
curl -X POST "http://localhost:5512/api/recraft/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city with flying cars",
    "style": "realistic",
    "size": "1024x1024",
    "image_format": "png"
  }'
```

#### 即梦3.0图像生成
```bash
curl -X POST "http://localhost:5512/api/seedream/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只可爱的熊猫在竹林中玩耍",
    "aspect_ratio": "1:1",
    "cfg_scale": 7.5,
    "seed": 12345
  }'
```

#### 即梦垫图编辑
```bash
curl -X POST "http://localhost:5512/api/seededit/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "prompt": "将图片背景改为蓝天白云",
    "strength": 0.8
  }'
```

#### FLUX图像创建
```bash
curl -X POST "http://localhost:5512/api/flux/create" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A magical forest with glowing mushrooms",
    "aspect_ratio": "16:9",
    "steps": 20,
    "guidance": 7.5
  }'
```

### MCP 协议

MCP服务运行在端口5513，支持以下工具函数：
- `create_gpt_image`
- `create_recraft_image` 
- `create_seedream_image`
- `create_seededit_image`
- `create_flux_image`

## 🔧 配置说明

### 环境变量

创建 `.env` 文件配置环境变量：

```env
# 服务器配置
HOST=0.0.0.0
PORT=5512
DEBUG=False
LOG_LEVEL=info

# MCP配置
MCP_HOST=0.0.0.0
MCP_PORT=5513
MCP_TRANSPORT=streamable-http

# Images API配置
IMAGES_API_BASE_URL=https://api.chatfire.cn
IMAGES_REQUEST_TIMEOUT=30
IMAGES_MAX_RETRIES=3

# 性能配置
MAX_POOL_CONNECTIONS=100
MAX_POOL_CONNECTIONS_PER_HOST=30
RATE_LIMIT_REQUESTS=1000
```

### API密钥

API密钥配置在 `core/config.py` 中，默认使用example项目的密钥。生产环境请修改为自己的密钥。

## 📖 项目结构

```
mcp_aigc_image_api/
├── core/                     # 核心模块
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志管理
│   └── images_client.py     # API客户端
├── routers/                 # 路由模块
│   ├── api.py              # FastAPI路由
│   └── mcp/                # MCP路由
│       ├── main.py         # MCP服务主程序
│       └── images_tools.py # MCP工具函数
├── services/               # 业务逻辑
│   └── images_service.py   # 图像服务
├── scripts/                # 脚本工具
│   ├── run_mcp_streamable.py # MCP服务启动脚本
│   └── test_api.py         # API测试脚本
├── main.py                 # FastAPI主程序
├── requirements.txt        # 依赖包
├── restart.sh             # 服务重启脚本
├── stop.sh               # 服务停止脚本
└── status.sh             # 状态检查脚本
```

## 🧪 测试

运行API测试：

```bash
python scripts/test_api.py
```

检查服务健康状态：

```bash
curl http://localhost:5512/api/health
```

## 📋 日志

服务日志文件：
- `fastapi_service.log` - FastAPI服务日志
- `mcp_service.log` - MCP服务日志
- `logs/` - 详细分类日志

## 🔗 相关链接

- **FastAPI文档**: http://localhost:5512/docs
- **MCP服务**: http://localhost:5513/mcp/v1
- **健康检查**: http://localhost:5512/api/health

## 📄 许可证

本项目基于example项目架构开发，遵循相同的许可协议。

## 🤝 贡献

欢迎提交Issue和Pull Request来完善项目功能。