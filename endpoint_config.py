# 根据深度分析生成的API端点配置
# 每个模型使用正确的端点和参数

# Recraft图像生成
# 端点: /recraft/v1
# 模型: recraft
# 请求格式: {}

# 虚拟换衣
# 端点: /v1/images/virtual-try-on:
# 模型: kolors-virtual-try-on
# 请求格式: {}

# Seedream图像生成
# 端点: /v1/images/generations:
# 模型: seedream-3.0
# 请求格式: {}

# 海螺图片
# 端点: /v1/images/generations:
# 模型: dall-e-3
# 请求格式: {}


# 端点映射配置
ENDPOINT_MAPPING = {
  "recraft_generate": {
    "endpoint": "/recraft/v1",
    "model": "recraft",
    "request_format": {}
  },
  "virtual_try_on_generate": {
    "endpoint": "/v1/images/virtual-try-on:",
    "model": "kolors-virtual-try-on",
    "request_format": {}
  },
  "seedream_generate": {
    "endpoint": "/v1/images/generations:",
    "model": "seedream-3.0",
    "request_format": {}
  },
  "hailuo_generate": {
    "endpoint": "/v1/images/generations:",
    "model": "dall-e-3",
    "request_format": {}
  }
}