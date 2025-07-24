# 根据API文档分析生成的端点更新
# 更新 core/images_client.py 中的对应方法

# GPT图像生成
async def gpt_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """GPT图像生成"""
    return await self._make_request("POST", "/v1/images/generations", data)

# Recraft图像生成
async def recraft_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Recraft图像生成"""
    return await self._make_request("POST", "/v1/images/generations", data)

# Seedream图像生成
async def seedream_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Seedream图像生成"""
    return await self._make_request("POST", "/v1/images/generations", data)

# StableDiffusion图像生成
async def stable_diffusion_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """StableDiffusion图像生成"""
    return await self._make_request("POST", "/v1/images/generations", data)

# 虚拟换衣
async def virtual_try_on_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """虚拟换衣"""
    return await self._make_request("POST", "/v1/images/virtual", data)

# 海螺图片
async def hailuo_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """海螺图片"""
    return await self._make_request("POST", "/v1/images/generations", data)

# Doubao图片生成
async def doubao_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Doubao图片生成"""
    return await self._make_request("POST", "/v1/images/generations", data)
