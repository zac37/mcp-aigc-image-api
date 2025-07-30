# MCP AIGC Image API 接口列表

## 图像生成 API

### 1. GPT (DALL-E)
- **POST** `/api/gpt/generations` - DALL-E 2/3 图像生成
- **POST** `/api/gpt/edits` - GPT 图像编辑
- **MCP Tool**: `create_gpt_image` - GPT图像生成工具
- **MCP Tool**: `create_gpt_image_edit` - GPT图像编辑工具

### 2. Recraft
- **POST** `/api/recraft/generate` - Recraft 图像生成
- **MCP Tool**: `create_recraft_image` - Recraft图像生成工具

### 3. 即梦 (Seedream)
- **POST** `/api/seedream/generate` - 即梦3.0图像生成
- **MCP Tool**: `create_seedream_image` - 即梦图像生成工具

### 4. 即梦垫图 (SeedEdit)
- **POST** `/api/seededit/generate` - 即梦垫图编辑
- **MCP Tool**: `create_seededit_image` - 即梦垫图工具

### 5. FLUX
- **POST** `/api/flux/create` - FLUX图像生成
- **MCP Tool**: `create_flux_image` - FLUX图像生成工具

### 6. Recraftv3
- **POST** `/api/recraftv3/create` - Recraftv3图像生成

### 7. Cogview
- **POST** `/api/cogview/create` - Cogview图像生成

### 8. 混元 (Hunyuan)
- **POST** `/api/hunyuan/create` - 腾讯混元图像生成

### 9. Kling
- **POST** `/api/kling/create` - 快手Kling图像生成

### 10. Stable Diffusion
- **POST** `/api/stable-diffusion/create` - Stable Diffusion图像生成
- **MCP Tool**: `create_stable_diffusion_image` - SD图像生成工具

### 11. Kolors
- **POST** `/api/kolors/generate` - Kolors图像生成

### 12. flux-kontext
- **POST** `/api/flux-kontext/generate` - FLUX上下文感知图像生成

### 13. 海螺图片 (Hailuo)
- **POST** `/api/hailuo/generate` - 海螺AI图像生成
- **MCP Tool**: `create_hailuo_image` - 海螺图像生成工具

### 14. Doubao
- **POST** `/api/doubao/generate` - 字节跳动豆包图像生成
- **MCP Tool**: `create_doubao_image` - 豆包图像生成工具

### 15. 通用接口
- **POST** `/api/images/create` - 通用图像生成接口
- **POST** `/api/images/variations` - 图像变体生成

## 视频生成 API

### Veo3 官方API
- **POST** `/api/veo3/official/generate` - 官方Veo3视频生成（异步模式）
- **GET** `/api/veo3/official/status/{operation_id}` - 查询任务状态

## 文件管理 API

- **POST** `/api/files/upload` - 上传文件
- **GET** `/api/images/{object_name}` - 获取图像文件
- **GET** `/api/files/{object_name}/redirect` - 重定向到文件URL
- **GET** `/api/files/{object_name}` - 获取文件信息
- **DELETE** `/api/files/{object_name}` - 删除文件
- **GET** `/api/files` - 列出所有文件

## 系统 API

- **GET** `/api/health` - 健康检查

## 服务端点

### FastAPI 服务
- **主服务**: http://localhost:5512
- **API文档**: http://localhost:5512/docs
- **路由前缀**: `/api`

### MCP 服务
- **端点**: http://localhost:5513
- **协议**: Streamable HTTP (POST /mcp/v1)
- **工具列表**:
  - `create_gpt_image` - GPT图像生成
  - `create_gpt_image_edit` - GPT图像编辑
  - `create_recraft_image` - Recraft图像生成
  - `create_seedream_image` - 即梦图像生成
  - `create_seededit_image` - 即梦垫图
  - `create_flux_image` - FLUX图像生成
  - `create_stable_diffusion_image` - SD图像生成
  - `create_hailuo_image` - 海螺图像生成
  - `create_doubao_image` - 豆包图像生成

## 支持的模型总结

### 图像生成模型（15个）
1. GPT/DALL-E (OpenAI)
2. Recraft & Recraftv3
3. 即梦3.0 & 即梦垫图
4. FLUX & flux-kontext
5. Cogview
6. 混元 (Tencent)
7. Kling (Kuaishou)
8. Stable Diffusion
9. Kolors
10. 海螺图片 (Hailuo AI)
11. Doubao (ByteDance)

### 视频生成模型（1个）
1. Veo3 (Google Vertex AI) - 官方API接入

## 异步任务处理

- **Celery Worker**: 处理长时间运行的视频生成任务
- **Redis队列**: 
  - `image_queue` - 图像任务队列
  - `video_queue` - 视频任务队列
  - `video_monitor_queue` - 视频监控队列
- **SimpleTaskQueue**: 用于管理视频生成任务状态