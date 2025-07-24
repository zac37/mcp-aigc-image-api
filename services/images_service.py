#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API 业务逻辑服务

封装图像生成相关的业务逻辑，提供高级API接口
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime

from core.images_client import get_images_client, ImagesAPIError
from core.logger import get_api_logger, log_exception, log_performance
from core.config import settings

logger = get_api_logger()

class ImagesService:
    """Images API服务类"""
    
    def __init__(self):
        self.client = get_images_client()
        logger.debug("ImagesService initialized")
    
    # =============================================================================
    # GPT图像生成服务
    # =============================================================================
    
    async def create_gpt_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> Dict[str, Any]:
        """
        创建GPT图像生成任务
        
        Args:
            prompt: 图像描述提示词
            model: 模型名称 (dall-e-3, dall-e-2)
            n: 生成图像数量
            size: 图像尺寸
            quality: 图像质量 (standard, hd)
            style: 图像风格 (vivid, natural)
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating GPT image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if model not in ["dall-e-3", "dall-e-2"]:
                raise ValueError(f"Unsupported model: {model}")
            
            if size not in ["256x256", "512x512", "1024x1024", "1024x1792", "1792x1024"]:
                raise ValueError(f"Unsupported size: {size}")
            
            result = await self.client.gpt_generations(
                prompt=prompt.strip(),
                model=model,
                n=n,
                size=size,
                quality=quality,
                style=style
            )
            
            logger.info(f"GPT image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for GPT image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create GPT image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in GPT image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # Recraft图像生成服务
    # =============================================================================
    
    async def create_recraft_image(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "1024x1024",
        image_format: str = "png"
    ) -> Dict[str, Any]:
        """
        创建Recraft图像生成任务
        
        Args:
            prompt: 图像描述提示词
            style: 图像风格
            size: 图像尺寸
            image_format: 图像格式
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating Recraft image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.recraft_generate(
                prompt=prompt.strip(),
                style=style,
                size=size,
                image_format=image_format
            )
            
            logger.info(f"Recraft image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Recraft image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Recraft image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Recraft image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # 即梦3.0 (Seedream) 图像生成服务
    # =============================================================================
    
    async def create_seedream_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建即梦3.0图像生成任务
        
        Args:
            prompt: 图像描述提示词
            aspect_ratio: 宽高比
            negative_prompt: 负面提示词
            cfg_scale: CFG缩放值
            seed: 随机种子
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating Seedream image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if aspect_ratio not in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
                raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
            if cfg_scale < 1.0 or cfg_scale > 20.0:
                raise ValueError("CFG scale must be between 1.0 and 20.0")
            
            result = await self.client.seedream_generate(
                prompt=prompt.strip(),
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt.strip() if negative_prompt else None,
                cfg_scale=cfg_scale,
                seed=seed
            )
            
            logger.info(f"Seedream image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Seedream image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Seedream image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Seedream image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # 即梦垫图 (SeedEdit) 图像生成服务  
    # =============================================================================
    
    async def create_seededit_image(
        self,
        image_url: str,
        prompt: str,
        strength: float = 0.8,
        seed: Optional[int] = None,
        model: str = "seededit",
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        创建即梦垫图生成任务
        
        Args:
            image_url: 原始图像URL
            prompt: 编辑提示词
            strength: 编辑强度（0.0-1.0）
            seed: 随机种子
            model: 模型类型，支持 seededit 或 seededit-pro
            size: 输出图像尺寸
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating SeedEdit image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not image_url or not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if strength < 0.0 or strength > 1.0:
                raise ValueError("Strength must be between 0.0 and 1.0")
            
            if model not in ["seededit", "seededit-pro"]:
                raise ValueError("Model must be 'seededit' or 'seededit-pro'")
            
            result = await self.client.seededit_generate(
                image_url=image_url.strip(),
                prompt=prompt.strip(),
                strength=strength,
                seed=seed,
                model=model,
                size=size
            )
            
            logger.info(f"SeedEdit image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for SeedEdit image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create SeedEdit image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in SeedEdit image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # FLUX图像创建服务
    # =============================================================================
    
    async def create_flux_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        steps: int = 20,
        guidance: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建FLUX图像生成任务
        
        Args:
            prompt: 图像描述提示词
            aspect_ratio: 宽高比
            steps: 推理步数
            guidance: 引导强度
            seed: 随机种子
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating FLUX image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if aspect_ratio not in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
                raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
            if steps < 1 or steps > 50:
                raise ValueError("Steps must be between 1 and 50")
            
            if guidance < 1.0 or guidance > 20.0:
                raise ValueError("Guidance must be between 1.0 and 20.0")
            
            result = await self.client.flux_create(
                prompt=prompt.strip(),
                aspect_ratio=aspect_ratio,
                steps=steps,
                guidance=guidance,
                seed=seed
            )
            
            logger.info(f"FLUX image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for FLUX image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create FLUX image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in FLUX image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # 其他模型服务方法
    # =============================================================================
    
    async def create_recraftv3_image(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "1024x1024",
        image_format: str = "png"
    ) -> Dict[str, Any]:
        """创建Recraftv3图像生成任务"""
        try:
            logger.info(f"Creating Recraftv3 image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.recraftv3_create(
                prompt=prompt.strip(),
                style=style,
                size=size,
                image_format=image_format
            )
            
            logger.info(f"Recraftv3 image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Recraftv3 image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Recraftv3 image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Recraftv3 image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_cogview_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建Cogview图像生成任务"""
        try:
            logger.info(f"Creating Cogview image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.cogview_create(
                prompt=prompt.strip(),
                size=size,
                quality=quality,
                seed=seed
            )
            
            logger.info(f"Cogview image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Cogview image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Cogview image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Cogview image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_hunyuan_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建混元图像生成任务"""
        try:
            logger.info(f"Creating Hunyuan image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if aspect_ratio not in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
                raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
            result = await self.client.hunyuan_create(
                prompt=prompt.strip(),
                aspect_ratio=aspect_ratio,
                seed=seed
            )
            
            logger.info(f"Hunyuan image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Hunyuan image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Hunyuan image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Hunyuan image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_kling_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建Kling图像生成任务"""
        try:
            logger.info(f"Creating Kling image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if aspect_ratio not in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
                raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
            if cfg_scale < 1.0 or cfg_scale > 20.0:
                raise ValueError("CFG scale must be between 1.0 and 20.0")
            
            result = await self.client.kling_create(
                prompt=prompt.strip(),
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt.strip() if negative_prompt else None,
                cfg_scale=cfg_scale,
                seed=seed
            )
            
            logger.info(f"Kling image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Kling image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Kling image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Kling image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_stable_diffusion_image(
        self,
        prompt: str,
        size: str = "1:1",
        n: int = 1
    ) -> Dict[str, Any]:
        """创建StableDiffusion图像生成任务"""
        try:
            logger.info(f"Creating StableDiffusion image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if n < 1 or n > 10:
                raise ValueError("Number of images must be between 1 and 10")
            
            valid_sizes = ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"]
            if size not in valid_sizes:
                raise ValueError(f"Size must be one of: {', '.join(valid_sizes)}")
            
            result = await self.client.stable_diffusion_create(
                prompt=prompt.strip(),
                size=size,
                n=n
            )
            
            logger.info(f"StableDiffusion image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for StableDiffusion image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create StableDiffusion image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in StableDiffusion image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_generic_image(
        self,
        prompt: str,
        model: str = "auto",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """创建通用图像生成任务"""
        try:
            logger.info(f"Creating generic image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.images_create(
                prompt=prompt.strip(),
                model=model,
                size=size,
                quality=quality
            )
            
            logger.info(f"Generic image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for generic image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create generic image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in generic image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_image_variations(
        self,
        image_url: str,
        n: int = 1,
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """创建图像变体任务"""
        try:
            logger.info(f"Creating image variations task for: {image_url[:50]}...")
            
            if not image_url or not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            if n < 1 or n > 10:
                raise ValueError("Number of variations must be between 1 and 10")
            
            result = await self.client.images_variations(
                image_url=image_url.strip(),
                n=n,
                size=size
            )
            
            logger.info(f"Image variations task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for image variations: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create image variations task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in image variations")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_kolors_image(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        mode: str = "text2img",
        strength: float = 0.8,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建Kolors图像生成任务"""
        try:
            logger.info(f"Creating Kolors image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if mode not in ["text2img", "img2img"]:
                raise ValueError("Mode must be 'text2img' or 'img2img'")
            
            if mode == "img2img" and not image_url:
                raise ValueError("Image URL is required for img2img mode")
            
            if strength < 0.0 or strength > 1.0:
                raise ValueError("Strength must be between 0.0 and 1.0")
            
            result = await self.client.kolors_generate(
                prompt=prompt.strip(),
                image_url=image_url,
                mode=mode,
                strength=strength,
                seed=seed
            )
            
            logger.info(f"Kolors image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Kolors image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Kolors image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Kolors image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_flux_kontext_image(
        self,
        prompt: str,
        context_image: Optional[str] = None,
        strength: float = 0.8,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建flux-kontext图像生成任务"""
        try:
            logger.info(f"Creating flux-kontext image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if strength < 0.0 or strength > 1.0:
                raise ValueError("Strength must be between 0.0 and 1.0")
            
            result = await self.client.flux_kontext_generate(
                prompt=prompt.strip(),
                context_image=context_image,
                strength=strength,
                seed=seed
            )
            
            logger.info(f"flux-kontext image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for flux-kontext image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create flux-kontext image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in flux-kontext image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_hailuo_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建海螺图片生成任务"""
        try:
            logger.info(f"Creating Hailuo image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.hailuo_generate(
                prompt=prompt.strip(),
                size=size,
                quality=quality,
                seed=seed
            )
            
            logger.info(f"Hailuo image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Hailuo image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Hailuo image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Hailuo image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def create_doubao_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        guidance_scale: int = 3,
        watermark: bool = True
    ) -> Dict[str, Any]:
        """创建Doubao图片生成任务"""
        try:
            logger.info(f"Creating Doubao image generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            result = await self.client.doubao_generate(
                prompt=prompt.strip(),
                size=size,
                guidance_scale=guidance_scale,
                watermark=watermark
            )
            
            logger.info(f"Doubao image generation task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Doubao image generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Doubao image generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Doubao image generation")
            raise ImagesAPIError(f"Service error: {str(e)}")

# =============================================================================
# 全局服务实例
# =============================================================================

_images_service: Optional[ImagesService] = None

def get_images_service() -> ImagesService:
    """获取全局Images服务实例"""
    global _images_service
    if _images_service is None:
        _images_service = ImagesService()
    return _images_service