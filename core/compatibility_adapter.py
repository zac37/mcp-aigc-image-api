"""
简化的兼容性适配器 - 遵循KISS原则

将15+个重复方法合并为3个核心方法，大幅简化维护成本
"""

from typing import Dict, Any, Optional, Union, List
from .api_gateway import get_api_gateway
from .base_client import APIError

class ImagesAPIClient:
    """
    简化的兼容性客户端适配器
    
    核心设计原则：
    1. 统一的生成接口替代15+个重复方法
    2. 基于参数自动识别操作类型
    3. 保持完全向后兼容性
    """
    
    def __init__(self):
        self.gateway = get_api_gateway()
    
    # ========================================
    # 核心统一接口 (替代15+个重复方法)
    # ========================================
    
    async def generate_image(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        统一图像生成接口 - 替代所有*_generate, *_create方法
        
        支持所有模型: gpt-image-1, recraft, seedream, flux, etc.
        自动路由到正确的API提供方
        """
        return await self.gateway.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def edit_image(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        统一图像编辑接口 - 替代所有编辑相关方法
        
        支持: gpt_edits, seededit_generate等
        自动处理图片上传和编辑参数
        """
        # 处理图像文件参数
        if 'image' in kwargs:
            image = kwargs.pop('image')
            kwargs['image_content'] = await image.read() if hasattr(image, 'read') else image
        
        if 'mask' in kwargs:
            mask = kwargs.pop('mask') 
            kwargs['mask_content'] = await mask.read() if mask and hasattr(mask, 'read') else mask
            
        return await self.gateway.edit_image(model=model, prompt=prompt, **kwargs)
    
    async def generate_video(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        统一视频生成接口 - 替代所有视频生成方法
        
        支持: veo3, veo3-official等
        """
        return await self.gateway.generate_video(model=model, prompt=prompt, **kwargs)
    
    # ========================================
    # 兼容性方法 (保持向后兼容，内部调用统一接口)
    # ========================================
    
    # GPT系列
    async def gpt_generations(self, **kwargs) -> Dict[str, Any]:
        """GPT图像生成 - 兼容旧接口"""
        model = kwargs.pop('model', 'gpt-image-1')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def gpt_edits(self, image, prompt: str, **kwargs) -> Dict[str, Any]:
        """GPT图像编辑 - 兼容旧接口"""
        model = kwargs.pop('model', 'gpt-image-1')
        kwargs['image'] = image
        return await self.edit_image(model=model, prompt=prompt, **kwargs)
    
    # ChatFire系列 - 统一处理
    async def recraft_generate(self, **kwargs) -> Dict[str, Any]:
        """Recraft图像生成"""
        model = kwargs.pop('model', 'recraft')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def seedream_generate(self, **kwargs) -> Dict[str, Any]:
        """Seedream图像生成"""
        model = kwargs.pop('model', 'seedream')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def seededit_generate(self, **kwargs) -> Dict[str, Any]:
        """SeedEdit图像编辑"""
        model = kwargs.pop('model', 'seededit')
        prompt = kwargs.pop('prompt', '')
        return await self.edit_image(model=model, prompt=prompt, **kwargs)
    
    async def flux_create(self, **kwargs) -> Dict[str, Any]:
        """FLUX图像创建"""
        model = kwargs.pop('model', 'flux')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def recraftv3_create(self, **kwargs) -> Dict[str, Any]:
        """Recraftv3图像创建"""
        model = kwargs.pop('model', 'recraftv3')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def cogview_create(self, **kwargs) -> Dict[str, Any]:
        """Cogview图像创建"""
        model = kwargs.pop('model', 'cogview')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def hunyuan_create(self, **kwargs) -> Dict[str, Any]:
        """混元图像创建"""
        model = kwargs.pop('model', 'hunyuan')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def kling_create(self, **kwargs) -> Dict[str, Any]:
        """Kling图像创建"""
        model = kwargs.pop('model', 'kling')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def stable_diffusion_create(self, **kwargs) -> Dict[str, Any]:
        """StableDiffusion图像创建"""
        model = kwargs.pop('model', 'stable-diffusion')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def images_create(self, **kwargs) -> Dict[str, Any]:
        """通用图像创建"""
        model = kwargs.pop('model', 'auto')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def flux_kontext_generate(self, **kwargs) -> Dict[str, Any]:
        """FluxKontext图像生成"""
        model = kwargs.pop('model', 'flux-kontext')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def hailuo_generate(self, **kwargs) -> Dict[str, Any]:
        """海螺图像生成"""
        model = kwargs.pop('model', 'hailuo')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    async def doubao_generate(self, **kwargs) -> Dict[str, Any]:
        """豆包图像生成"""
        model = kwargs.pop('model', 'doubao')
        prompt = kwargs.pop('prompt', '')
        return await self.generate_image(model=model, prompt=prompt, **kwargs)
    
    # 视频生成系列
    async def veo3_generate(self, **kwargs) -> Dict[str, Any]:
        """Veo3视频生成"""
        model = kwargs.pop('model', 'veo3')
        prompt = kwargs.pop('prompt', '')
        
        # 如果是官方Veo3，路由到Vertex AI
        if model == 'veo3-official':
            return await self.generate_video(model=model, prompt=prompt, **kwargs)
        else:
            # 否则路由到ChatFire
            return await self.generate_video(model=model, prompt=prompt, **kwargs)
    
    async def veo3_get_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """获取Veo3任务状态"""
        # 根据task_id格式判断是哪个API提供方
        if 'operations/' in task_id:
            # Vertex AI格式
            return await self.gateway.check_video_status('veo3-official', task_id)
        else:
            # ChatFire格式
            return await self.gateway.check_video_status('veo3', task_id)
    
    # ========================================
    # 清理方法
    # ========================================
    
    async def close(self):
        """关闭客户端"""
        await self.gateway.close()


# 兼容性函数
_client_instance = None

def get_images_client():
    """获取兼容性客户端实例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = ImagesAPIClient()
    return _client_instance

async def cleanup_images_client():
    """清理兼容性客户端"""
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None

# 兼容性异常类
class ImagesAPIError(APIError):
    """兼容性异常类"""
    pass