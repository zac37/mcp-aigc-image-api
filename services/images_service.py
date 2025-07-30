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
from core.veo3_client import veo3_client, Veo3APIError

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
        model: str = "gpt-image-1",
        n: int = 1,
        response_format: str = "url",
        size: str = "auto",
        background: str = "auto",
        quality: str = "auto",
        moderation: str = "auto"
    ) -> Dict[str, Any]:
        """
        创建GPT图像生成任务
        
        Args:
            prompt: 图像描述提示词
            model: 模型名称 (gpt-image-1)
            n: 生成图像数量
            response_format: 返回格式 (url, b64_json, oss_url)
            size: 图像尺寸 (1024x1024, 1536x1024, 1024x1536, auto)
            background: 背景类型 (transparent, opaque, auto)
            quality: 图像质量 (high, medium, low, auto)
            moderation: 内容审核级别 (low, auto)
        
        Returns:
            生成任务结果
        """
        try:
            logger.info(f"Creating GPT image generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if model not in ["gpt-image-1"]:
                raise ValueError(f"Unsupported model: {model}")
            
            if size not in ["1024x1024", "1536x1024", "1024x1536", "auto"]:
                raise ValueError(f"Unsupported size: {size}")
            
            if response_format not in ["url", "b64_json", "oss_url"]:
                raise ValueError(f"Unsupported response_format: {response_format}")
            
            if background not in ["transparent", "opaque", "auto"]:
                raise ValueError(f"Unsupported background: {background}")
            
            if quality not in ["high", "medium", "low", "auto"]:
                raise ValueError(f"Unsupported quality: {quality}")
            
            if moderation not in ["low", "auto"]:
                raise ValueError(f"Unsupported moderation: {moderation}")
            
            result = await self.client.gpt_generations(
                prompt=prompt.strip(),
                model=model,
                n=n,
                response_format=response_format,
                size=size,
                background=background,
                quality=quality,
                moderation=moderation
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
    
    async def create_gpt_image_edit(
        self,
        image,  # UploadFile
        prompt: str,
        model: str = "gpt-image-1",
        mask = None,  # Optional[UploadFile]
        n: str = "1",  # 改为字符串类型
        size: str = "1024x1024",
        response_format: str = "url",
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建GPT图像编辑任务
        
        在给定原始图像和提示的情况下创建编辑或扩展图像。
        
        Args:
            image: 要编辑的图像文件（UploadFile）
            prompt: 所需图像的文本描述，最大长度为1000个字符
            model: 用于图像生成的模型（gpt-image-1）
            mask: 附加图像，指示应编辑的位置（可选）
            n: 要生成的图像数，必须介于1和10之间（字符串格式）
            size: 生成图像的大小，必须是256x256、512x512或1024x1024之一
            response_format: 生成的图像返回格式，必须是url或b64_json
            user: 用户标识符（可选）
        
        Returns:
            编辑任务结果
        """
        try:
            logger.info(f"Creating GPT image edit task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if len(prompt.strip()) > 1000:
                raise ValueError("Prompt cannot exceed 1000 characters")
            
            if not image:
                raise ValueError("Image file is required")
                
            # 验证n参数
            try:
                n_int = int(n)
                if n_int < 1 or n_int > 10:
                    raise ValueError("Number of images must be between 1 and 10")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError("n must be a valid integer string between 1 and 10")
                raise
                
            # 验证文件类型
            if hasattr(image, 'content_type') and image.content_type and not image.content_type.startswith("image/"):
                raise ValueError("Image must be a valid image file")
                
            # 验证文件大小（4MB）
            # 处理bytes对象（从API路由层传来）或UploadFile对象
            if hasattr(image, 'size') and image.size and image.size > 4 * 1024 * 1024:
                raise ValueError("Image file must be smaller than 4MB")
            elif isinstance(image, bytes) and len(image) > 4 * 1024 * 1024:
                raise ValueError("Image file must be smaller than 4MB")
                
            # 验证model参数
            if model not in ["gpt-image-1"]:
                raise ValueError(f"Unsupported model: {model}")
            
            result = await self.client.gpt_edits(
                image=image,
                prompt=prompt.strip(),
                model=model,
                mask=mask,
                n=n_int,
                size=size,
                response_format=response_format,
                user=user
            )
            
            logger.info(f"GPT image edit task created successfully")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for GPT image edit: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create GPT image edit task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in GPT image edit")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # Recraft图像生成服务
    # =============================================================================
    
    async def create_recraft_image(
        self,
        prompt: str,
        style: str = "realistic_image",
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
        style: str = "realistic_image",
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
    
    async def create_veo3_video(
        self,
        prompt: str,
        model: str = "veo3",
        images: Optional[List[str]] = None,
        enhance_prompt: bool = True
    ) -> Dict[str, Any]:
        """创建Veo3视频生成任务"""
        try:
            logger.info(f"Creating Veo3 video generation task: {prompt[:50]}...")
            
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            # 验证模型名称
            valid_models = ["veo3", "veo3-frames", "veo3-pro", "veo3-pro-frames"]
            if model not in valid_models:
                raise ValueError(f"Unsupported model: {model}. Valid models: {valid_models}")
            
            # 验证图生视频模式参数
            if model.endswith("-frames"):
                if not images or len(images) == 0:
                    raise ValueError(f"Model {model} requires images parameter for image-to-video generation")
                logger.info(f"Using {len(images)} input images for image-to-video generation")
            
            result = await self.client.veo3_generate(
                prompt=prompt.strip(),
                model=model,
                images=images,
                enhance_prompt=enhance_prompt
            )
            
            logger.info(f"Veo3 video generation task created successfully with ID: {result.get('id', 'unknown')}")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Veo3 video generation: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to create Veo3 video generation task")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Veo3 video generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def get_veo3_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """获取Veo3视频生成任务状态"""
        try:
            logger.info(f"Getting Veo3 task status: {task_id}")
            
            if not task_id or not task_id.strip():
                raise ValueError("Task ID cannot be empty")
            
            result = await self.client.veo3_get_task(task_id=task_id.strip())
            
            logger.info(f"Veo3 task status retrieved: {result.get('status', 'unknown')}")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for Veo3 task query: {e}")
            raise
        except ImagesAPIError as e:
            log_exception(logger, e, "Failed to get Veo3 task status")
            raise
        except Exception as e:
            log_exception(logger, e, "Unexpected error in Veo3 task query")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    # =============================================================================
    # Google官方Veo3视频生成服务
    # =============================================================================
    
    async def create_veo3_official_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        wait_for_completion: bool = False,
        max_wait: int = 600,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用Google官方API创建Veo3视频生成任务
        
        Args:
            prompt: 视频生成提示词
            duration: 视频时长(秒)，默认5秒
            aspect_ratio: 宽高比，默认16:9
            wait_for_completion: 是否等待完成，默认False
            max_wait: 最大等待时间(秒)，默认600秒
            **kwargs: 其他可选参数（如seed, guidanceScale等）
        
        Returns:
            视频生成任务结果
        """
        try:
            logger.info(f"Creating official Veo3 video generation task: {prompt[:50]}...")
            
            # 参数验证
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if duration < 1 or duration > 30:
                raise ValueError("Duration must be between 1 and 30 seconds")
            
            valid_ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
            if aspect_ratio not in valid_ratios:
                raise ValueError(f"Aspect ratio must be one of: {', '.join(valid_ratios)}")
            
            if max_wait < 60 or max_wait > 1800:
                raise ValueError("Max wait time must be between 60 and 1800 seconds")
            
            # 使用官方Veo3客户端生成视频
            result = await veo3_client.generate_video_async(
                prompt=prompt.strip(),
                duration=duration,
                aspect_ratio=aspect_ratio,
                wait_for_completion=wait_for_completion,
                max_wait=max_wait,
                **kwargs
            )
            
            logger.info(f"Official Veo3 video generation task created successfully - Operation ID: {result.get('operation_id')}")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for official Veo3 video generation: {e}")
            raise
        except Veo3APIError as e:
            log_exception(logger, e, "Failed to create official Veo3 video generation task")
            raise ImagesAPIError(f"Veo3 API error: {str(e)}")
        except Exception as e:
            log_exception(logger, e, "Unexpected error in official Veo3 video generation")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def check_veo3_official_status(
        self,
        operation_id: str
    ) -> Dict[str, Any]:
        """
        检查Google官方Veo3任务状态
        
        Args:
            operation_id: 任务操作ID
        
        Returns:
            任务状态信息
        """
        try:
            logger.info(f"Checking official Veo3 task status: {operation_id}")
            
            if not operation_id or not operation_id.strip():
                raise ValueError("Operation ID cannot be empty")
            
            # 检查任务状态
            status, data = await veo3_client.check_status_async(operation_id.strip())
            
            result = {
                'operation_id': operation_id,
                'status': status,
                'data': data
            }
            
            # 如果任务完成，尝试提取视频URL
            if status == 'completed' and data:
                # 处理新的响应格式
                if 'videos' in data:
                    videos = data['videos']
                    if videos and len(videos) > 0:
                        video_info = videos[0]
                        gcs_uri = video_info.get('gcsUri')
                        if gcs_uri:
                            result['gcs_uri'] = gcs_uri
                            
                            # 构建公开访问URL（假设存储桶是公开的）
                            # 解析 gs://bucket/path 格式
                            if gcs_uri.startswith('gs://'):
                                uri_parts = gcs_uri[5:].split('/', 1)  # 移除 'gs://'
                                if len(uri_parts) == 2:
                                    bucket_name = uri_parts[0]
                                    blob_path = uri_parts[1]
                                    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_path}"
                                    result['public_url'] = public_url
                                    result['video_url'] = public_url  # 向后兼容
                # 兼容旧的响应格式
                elif 'predictions' in data:
                    predictions = data['predictions']
                    if predictions and len(predictions) > 0:
                        prediction = predictions[0]
                        if 'videoUri' in prediction:
                            result['video_url'] = prediction['videoUri']
            
            logger.info(f"Official Veo3 task status checked: {status}")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for official Veo3 status check: {e}")
            raise
        except Veo3APIError as e:
            log_exception(logger, e, "Failed to check official Veo3 task status")
            raise ImagesAPIError(f"Veo3 API error: {str(e)}")
        except Exception as e:
            log_exception(logger, e, "Unexpected error in official Veo3 status check")
            raise ImagesAPIError(f"Service error: {str(e)}")
    
    async def wait_veo3_official_completion(
        self,
        operation_id: str,
        max_wait: int = 600,
        check_interval: int = 15
    ) -> Dict[str, Any]:
        """
        等待Google官方Veo3任务完成
        
        Args:
            operation_id: 任务操作ID
            max_wait: 最大等待时间(秒)
            check_interval: 检查间隔(秒)
        
        Returns:
            任务完成结果
        """
        try:
            logger.info(f"Waiting for official Veo3 task completion: {operation_id}")
            
            if not operation_id or not operation_id.strip():
                raise ValueError("Operation ID cannot be empty")
            
            if max_wait < 60 or max_wait > 1800:
                raise ValueError("Max wait time must be between 60 and 1800 seconds")
            
            if check_interval < 5 or check_interval > 60:
                raise ValueError("Check interval must be between 5 and 60 seconds")
            
            # 等待任务完成
            success, data = await veo3_client.wait_for_completion_async(
                operation_id.strip(),
                max_wait=max_wait,
                check_interval=check_interval
            )
            
            result = {
                'operation_id': operation_id,
                'success': success,
                'data': data
            }
            
            # 如果成功完成，尝试提取视频URL
            if success and data:
                if 'predictions' in data:
                    predictions = data['predictions']
                    if predictions and len(predictions) > 0:
                        prediction = predictions[0]
                        if 'videoUri' in prediction:
                            result['video_url'] = prediction['videoUri']
                result['status'] = 'completed'
            else:
                result['status'] = 'failed' if data else 'timeout'
            
            logger.info(f"Official Veo3 task completion result: {result['status']}")
            return result
            
        except ValueError as e:
            logger.warning(f"Invalid parameters for official Veo3 completion wait: {e}")
            raise
        except Veo3APIError as e:
            log_exception(logger, e, "Failed to wait for official Veo3 task completion")
            raise ImagesAPIError(f"Veo3 API error: {str(e)}")
        except Exception as e:
            log_exception(logger, e, "Unexpected error in official Veo3 completion wait")
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