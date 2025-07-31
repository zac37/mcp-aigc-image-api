#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Images API 客户端模块

统一封装对各种图像生成API的调用
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import time
import os
from io import BytesIO

from .config import settings
from .logger import get_images_client_logger, log_exception, log_performance

logger = get_images_client_logger()

class ImagesAPIError(Exception):
    """Images API异常类"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"ImagesAPIError(message='{self.message}', status_code={self.status_code}, error_code='{self.error_code}')"

class ImagesAPIClient:
    """Images API客户端"""
    
    def __init__(self):
        self.api_key = settings.images.api_key
        self.base_url = settings.images.api_base_url
        self.timeout = settings.images.request_timeout
        self.max_retries = settings.images.max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        
        # 性能计数器
        self._request_count = 0
        self._total_time = 0.0
        
        logger.info(f"ImagesAPIClient initialized with base_url: {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=settings.performance.max_pool_connections,
                limit_per_host=settings.performance.max_pool_connections_per_host,
                ttl_dns_cache=settings.performance.dns_cache_ttl,
                use_dns_cache=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "Images-API-Client/1.0.0",
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            logger.debug("Created new aiohttp session")
        return self._session
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        发起API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            headers: 额外的请求头
            retry_count: 当前重试次数
        
        Returns:
            API响应数据
        
        Raises:
            ImagesAPIError: API请求失败
        """
        start_time = time.time()
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # 合并请求头
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        try:
            session = await self._get_session()
            
            request_kwargs = {
                "headers": request_headers
            }
            
            if method.upper() == "GET":
                if params:
                    request_kwargs["params"] = params
                elif data:
                    request_kwargs["params"] = data
            else:
                if data:
                    request_kwargs["json"] = data
            
            logger.debug(f"Making {method} request to {url}")
            
            async with session.request(method, url, **request_kwargs) as response:
                response_text = await response.text()
                
                # 计算性能指标
                duration = time.time() - start_time
                self._request_count += 1
                self._total_time += duration
                
                log_performance(
                    logger, 
                    f"{method} {endpoint}", 
                    duration,
                    status_code=response.status,
                    request_count=self._request_count
                )
                
                # 处理响应
                if response.status == 200:
                    if not response_text.strip():
                        # 空响应，可能是异步任务，返回成功状态
                        return {"status": "success", "data": None, "message": "Request accepted"}
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError as e:
                        # 如果JSON解析失败，但状态码是200，可能是文本响应
                        logger.warning(f"Non-JSON response from API: {response_text[:200]}")
                        return {"status": "success", "data": response_text, "message": "Non-JSON response"}
                
                # 处理错误响应
                error_data = {}
                try:
                    error_data = json.loads(response_text)
                except json.JSONDecodeError:
                    error_data = {"message": response_text}
                
                error_message = error_data.get("error", {}).get("message") or error_data.get("message", f"HTTP {response.status}")
                error_code = error_data.get("error", {}).get("code") or str(response.status)
                
                # 判断是否需要重试
                if retry_count < self.max_retries and response.status in [429, 500, 502, 503, 504]:
                    retry_delay = 2 ** retry_count  # 指数退避
                    logger.warning(f"Request failed with status {response.status}, retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(retry_delay)
                    return await self._make_request(method, endpoint, data, headers, params, retry_count + 1)
                
                raise ImagesAPIError(
                    error_message,
                    status_code=response.status,
                    error_code=error_code
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            if retry_count < self.max_retries:
                retry_delay = 2 ** retry_count
                logger.warning(f"Network error, retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(retry_delay)
                return await self._make_request(method, endpoint, data, headers, retry_count + 1)
            
            raise ImagesAPIError(f"Network error: {str(e)}")
        
        except Exception as e:
            log_exception(logger, e, f"Unexpected error in {method} {endpoint}")
            error_message = str(e) if str(e).strip() else f"Network timeout or connection error in {method} {endpoint}"
            raise ImagesAPIError(f"Unexpected error: {error_message}")
    
    # =============================================================================
    # GPT图像生成API
    # =============================================================================
    
    async def gpt_generations(
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
        """GPT图像生成"""
        data = {
            "prompt": prompt,
            "model": model,
            "n": n,
            "response_format": response_format,
            "size": size,
            "background": background,
            "quality": quality,
            "moderation": moderation
        }
        return await self._make_request("POST", "/v1/images/generations", data)
    
    async def gpt_edits(
        self,
        image,  # UploadFile
        prompt: str,
        model: str = "gpt-image-1",
        mask = None,  # Optional[UploadFile]
        n: Union[int, str] = 1,  # 支持int或str类型
        size: str = "1024x1024",
        response_format: str = "url",
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        GPT图像编辑
        
        在给定原始图像和提示的情况下创建编辑或扩展图像。
        
        Args:
            image: 要编辑的图像文件（UploadFile）
            prompt: 所需图像的文本描述，最大长度为1000个字符
            model: 用于图像生成的模型（gpt-image-1）
            mask: 附加图像，指示应编辑的位置（可选）
            n: 要生成的图像数，必须介于1和10之间（支持int或str）
            size: 生成图像的大小，必须是256x256、512x512或1024x1024之一
            response_format: 生成的图像返回格式，必须是url或b64_json
            user: 用户标识符，可选
        
        Returns:
            API响应数据
        """
        # 准备表单数据
        data = {
            "prompt": prompt,
            "model": model,
            "n": str(n),  # 确保转换为字符串
            "size": size,
            "response_format": response_format
        }
        
        if user:
            data["user"] = user
        
        # 准备文件数据
        files = {}
        
        # 添加主图像文件 - 处理bytes或UploadFile对象
        if isinstance(image, bytes):
            image_content = image
        else:
            image_content = await image.read()
        files["image"] = image_content
        
        # 添加mask文件（如果提供） - 处理bytes或UploadFile对象
        if mask:
            if isinstance(mask, bytes):
                mask_content = mask
            else:
                mask_content = await mask.read()
            files["mask"] = mask_content
            
        return await self._make_multipart_request("POST", "/v1/images/edits", files, data)
    
    async def _make_multipart_request(
        self,
        method: str,
        endpoint: str,
        files: Optional[Dict[str, Union[str, bytes, None]]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        发起multipart/form-data请求
        """
        start_time = time.time()
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        try:
            session = await self._get_session()
            
            # 构建multipart form data
            form_data = aiohttp.FormData()
            
            # 添加文件
            if files:
                for field_name, file_data in files.items():
                    if file_data is None:
                        continue
                        
                    if isinstance(file_data, str):
                        # 如果是URL，先下载文件
                        if file_data.startswith(('http://', 'https://')):
                            async with session.get(file_data) as resp:
                                if resp.status == 200:
                                    file_content = await resp.read()
                                    filename = file_data.split('/')[-1].split('?')[0]
                                    if not filename.endswith(('.png', '.jpg', '.jpeg')):
                                        filename += '.png'
                                    form_data.add_field(
                                        field_name,
                                        file_content,
                                        filename=filename,
                                        content_type='image/png'
                                    )
                                else:
                                    raise ImagesAPIError(f"Failed to download image from URL: {file_data}")
                        else:
                            # 如果是文件路径
                            if os.path.exists(file_data):
                                with open(file_data, 'rb') as f:
                                    file_content = f.read()
                                filename = os.path.basename(file_data)
                                content_type = 'image/png' if filename.endswith('.png') else 'image/jpeg'
                                form_data.add_field(
                                    field_name,
                                    file_content,
                                    filename=filename,
                                    content_type=content_type
                                )
                            else:
                                raise ImagesAPIError(f"File not found: {file_data}")
                    elif isinstance(file_data, bytes):
                        # 直接使用字节数据
                        form_data.add_field(
                            field_name,
                            file_data,
                            filename=f"{field_name}.png",
                            content_type='image/png'
                        )
            
            # 添加表单数据
            if data:
                for key, value in data.items():
                    if value is not None:
                        form_data.add_field(key, str(value))
            
            logger.debug(f"Making multipart {method} request to {url}")
            
            async with session.request(method, url, data=form_data, headers=request_headers) as response:
                response_text = await response.text()
                
                # 计算性能指标
                duration = time.time() - start_time
                self._request_count += 1
                self._total_time += duration
                
                log_performance(
                    logger, 
                    f"{method} {endpoint} (multipart)", 
                    duration,
                    status_code=response.status,
                    request_count=self._request_count
                )
                
                # 处理响应
                if response.status == 200:
                    if not response_text.strip():
                        return {"status": "success", "data": None, "message": "Request accepted"}
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Non-JSON response from API: {response_text[:200]}")
                        return {"status": "success", "data": response_text, "message": "Non-JSON response"}
                
                # 处理错误响应
                error_data = {}
                try:
                    error_data = json.loads(response_text)
                except json.JSONDecodeError:
                    error_data = {"message": response_text}
                
                error_message = error_data.get("error", {}).get("message") or error_data.get("message", f"HTTP {response.status}")
                error_code = error_data.get("error", {}).get("code") or str(response.status)
                
                # 判断是否需要重试
                if retry_count < self.max_retries and response.status in [429, 500, 502, 503, 504]:
                    retry_delay = 2 ** retry_count
                    logger.warning(f"Multipart request failed with status {response.status}, retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(retry_delay)
                    return await self._make_multipart_request(method, endpoint, files, data, headers, retry_count + 1)
                
                raise ImagesAPIError(
                    error_message,
                    status_code=response.status,
                    error_code=error_code
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error in multipart request: {str(e)}")
            if retry_count < self.max_retries:
                retry_delay = 2 ** retry_count
                logger.warning(f"Network error, retrying multipart request in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(retry_delay)
                return await self._make_multipart_request(method, endpoint, files, data, headers, retry_count + 1)
            
            raise ImagesAPIError(f"Network error: {str(e)}")
        
        except Exception as e:
            log_exception(logger, e, f"Unexpected error in multipart {method} {endpoint}")
            error_message = str(e) if str(e).strip() else f"Network timeout or connection error in {method} {endpoint}"
            raise ImagesAPIError(f"Unexpected error: {error_message}")
    
    # =============================================================================
    # Recraft图像生成API
    # =============================================================================
    
    async def recraft_generate(
        self,
        prompt: str,
        style: str = "realistic_image",  # 使用文档中正确的风格值
        size: str = "1024x1024",
        image_format: str = "png"
    ) -> Dict[str, Any]:
        """Recraft图像生成"""
        # 根据API文档构建请求数据
        data = {
            "model": "recraftv3",  # 必需参数，使用文档中的模型名称
            "prompt": prompt,      # 必需参数
            "n": 1,               # 整数，默认1
            "style": style,       # 风格参数
            "response_format": "url",  # 必需参数，返回格式
            "size": size          # 图像尺寸
        }
        
        # 使用正确的API端点
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # 即梦3.0 (Seedream) API
    # =============================================================================
    
    async def seedream_generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """即梦3.0图像生成"""
        data = {
            "prompt": prompt,
            "model": "seedream-3.0",
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # 即梦垫图 (SeedEdit) API
    # =============================================================================
    
    async def seededit_generate(
        self,
        image_url: str,
        prompt: str,
        strength: float = 0.8,  # 保持参数兼容性，但不传递给API
        seed: Optional[int] = None,  # 保持参数兼容性，但不传递给API
        model: str = "seededit",
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """即梦垫图生成 - 基于即梦3.0 (Seedream) API实现图生图功能"""
        # 根据即梦3.0 API文档，prompt需要包含图片URL和编辑指令
        # 格式：图片URL + 空格 + 编辑指令
        combined_prompt = f"{image_url} {prompt}"
        
        # 根据即梦3.0 API文档构建请求数据，传递所有必需参数
        data = {
            "model": "seedream-3.0",      # 必需参数：使用即梦3.0模型
            "prompt": combined_prompt,    # 必需参数：图片URL + 编辑指令
            "n": 1,                       # 必需参数：生成图像数量
            "response_format": "url",     # 必需参数：返回格式
            "size": size                  # 必需参数：图像尺寸
        }
        
        # 注意: strength和seed参数不在即梦3.0 API文档中，已移除
        # model参数在工具层保留用于兼容性，但API层统一使用seedream-3.0
        
        # 使用正确的API端点
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # FLUX图像创建API
    # =============================================================================
    
    async def flux_create(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        steps: int = 20,
        guidance: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """FLUX图像创建"""
        # 将aspect_ratio转换为size格式
        size_mapping = {
            "1:1": "1024x1024",
            "16:9": "1024x576", 
            "9:16": "576x1024",
            "4:3": "1024x768",
            "3:4": "768x1024"
        }
        
        size = size_mapping.get(aspect_ratio, "1024x1024")
        
        # 根据API文档构建请求数据
        data = {
            "model": "flux-pro",  # 使用文档中的正确模型名称
            "prompt": prompt,
            "n": 1,  # 必需参数
            "response_format": "url",  # 必需参数  
            "size": size  # 必需参数
        }
        
        # seed作为可选参数，如果API支持的话可以添加
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # Recraftv3图像创建API
    # =============================================================================
    
    async def recraftv3_create(
        self,
        prompt: str,
        style: str = "realistic_image",
        size: str = "1024x1024",
        image_format: str = "png"
    ) -> Dict[str, Any]:
        """Recraftv3图像创建"""
        data = {
            "prompt": prompt,
            "model": "recraft-v3",
            "style": style,
            "size": size,
            "format": image_format
        }
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # Cogview图像创建API
    # =============================================================================
    
    async def cogview_create(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cogview图像创建"""
        data = {
            "prompt": prompt,
            "model": "cogview-3",
            "size": size,
            "quality": quality
        }
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # 混元图像创建API
    # =============================================================================
    
    async def hunyuan_create(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """混元图像创建"""
        data = {
            "prompt": prompt,
            "model": "hunyuan-dit",
            "aspect_ratio": aspect_ratio,
            "cfg_scale": 7.5
        }
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # Kling图像创建API
    # =============================================================================
    
    async def kling_create(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Kling图像创建"""
        data = {
            "prompt": prompt,
            "model": "kling",
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # StableDiffusion图像创建API
    # =============================================================================
    
    async def stable_diffusion_create(
        self,
        prompt: str,
        size: str = "1:1",
        n: int = 1
    ) -> Dict[str, Any]:
        """StableDiffusion图像创建"""
        data = {
            "model": "stable-diffusion-3-5-large",
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # 通用图像创建API
    # =============================================================================
    
    async def images_create(
        self,
        prompt: str,
        model: str = "auto",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """通用图像创建"""
        data = {
            "prompt": prompt,
            "model": model,
            "size": size,
            "quality": quality
        }
        return await self._make_request("POST", "/images/create", data)
    
    
    # =============================================================================
    # flux-kontext图像生成API
    # =============================================================================
    
    async def flux_kontext_generate(
        self,
        prompt: str,
        context_image: Optional[str] = None,
        strength: float = 0.8,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """flux-kontext图像生成"""
        data = {
            "prompt": prompt,
            "model": "flux-kontext",
            "strength": strength
        }
        if context_image:
            data["context_image"] = context_image
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # 海螺图片生成API
    # =============================================================================
    
    async def hailuo_generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """海螺图片生成"""
        data = {
            "prompt": prompt,
            "model": "dall-e-3",
            "n": 1,
            "size": size,
            "quality": quality
        }
        if seed is not None:
            data["seed"] = seed
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # Doubao图片生成API
    # =============================================================================
    
    async def doubao_generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        guidance_scale: int = 3,
        watermark: bool = True
    ) -> Dict[str, Any]:
        """Doubao图片生成"""
        data = {
            "model": "doubao-seedream-3-0-t2i-250415",
            "prompt": prompt,
            "response_format": "url",
            "size": size,
            "guidance_scale": guidance_scale,
            "watermark": watermark
        }
        
        return await self._make_request("POST", "/v1/images/generations", data)
    
    # =============================================================================
    # Veo3视频生成API
    # =============================================================================
    
    async def veo3_generate(
        self,
        prompt: str,
        model: str = "veo3",
        images: Optional[List[str]] = None,
        enhance_prompt: bool = True
    ) -> Dict[str, Any]:
        """Veo3视频生成
        
        Args:
            prompt: 视频描述提示词
            model: 模型名称 (veo3, veo3-frames, veo3-pro, veo3-pro-frames)
            images: 图像URL列表（图生视频需要，文生视频会忽略）
            enhance_prompt: 是否增强提示词
            
        Returns:
            包含任务ID和状态的响应
        """
        data = {
            "model": model,
            "prompt": prompt,
            "enhance_prompt": enhance_prompt
        }
        
        # 图生视频模式需要提供图像
        if images and (model.endswith("-frames")):
            data["images"] = images
        
        return await self._make_request("POST", "/veo/v1/videos/generations", data)
    
    async def veo3_get_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """获取Veo3视频生成任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含任务状态、视频URL等信息的响应
        """
        params = {"id": task_id}
        return await self._make_request("GET", "/veo/v1/videos/generations", params=params)
    
    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("ImagesAPIClient session closed")



class VertexAIVeoClient:
    """Google Vertex AI Veo视频生成客户端"""
    
    def __init__(self):
        self.api_key = settings.images.gemini_api_key
        self.project_id = settings.images.vertex_project_id
        self.location = settings.images.vertex_location
        self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1"
        self.timeout = settings.images.request_timeout
        self.max_retries = settings.images.max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"VertexAIVeoClient initialized for project: {self.project_id}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=settings.performance.max_pool_connections,
                limit_per_host=settings.performance.max_pool_connections_per_host,
                ttl_dns_cache=settings.performance.dns_cache_ttl,
                keepalive_timeout=settings.server.keepalive_timeout
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=settings.performance.connection_timeout,
                sock_read=settings.performance.read_timeout
            )
            
            # 尝试使用API密钥作为Bearer token（某些情况下可能有效）
            # 正确的方式应该是使用 gcloud auth print-access-token
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
        return self._session

    async def create_video(
        self,
        prompt: str,
        model_id: str = "veo-3.0-generate-preview",
        duration: Optional[int] = 5,
        aspect_ratio: Optional[str] = "16:9",
        resolution: Optional[str] = "720p",
        sample_count: int = 1,
        storage_uri: Optional[str] = None,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建Vertex AI Veo视频
        
        Args:
            prompt: 视频描述文本
            model_id: 模型ID，默认veo-3.0-generate-preview
            duration: 视频时长(秒)，5-8秒
            aspect_ratio: 宽高比
            resolution: 分辨率，720p或1080p
            sample_count: 生成视频数量，1-4
            storage_uri: 存储URI，如果不提供则返回字节数据
            seed: 随机种子
            negative_prompt: 负面提示词
            
        Returns:
            包含操作信息的字典
        """
        start_time = time.time()
        
        if not self.project_id:
            raise ImagesAPIError("Vertex AI project ID not configured")
        
        # 构建请求数据 (使用Vertex AI predictLongRunning格式)
        request_data = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {}
        }
        
        # 添加可选参数
        if aspect_ratio:
            request_data["parameters"]["aspectRatio"] = aspect_ratio
        if negative_prompt:
            request_data["parameters"]["negativePrompt"] = negative_prompt
        if sample_count:
            request_data["parameters"]["sampleCount"] = sample_count
        if seed is not None:
            request_data["parameters"]["seed"] = seed
        if storage_uri:
            request_data["parameters"]["storageUri"] = storage_uri
        if duration:
            # 转换为秒数
            if isinstance(duration, str) and duration.endswith('s'):
                duration_seconds = int(duration[:-1])
            else:
                duration_seconds = int(duration)
            request_data["parameters"]["durationSeconds"] = duration_seconds
        
        # 添加增强提示词选项
        request_data["parameters"]["enhancePrompt"] = kwargs.get("enhance_prompt", True)

        session = await self._get_session()
        url = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_id}:predictLongRunning"
        
        try:
            logger.info(f"Creating Vertex AI Veo video with prompt: {prompt[:100]}...")
            
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    elapsed_time = time.time() - start_time
                    
                    logger.info(f"Vertex AI Veo video creation initiated in {elapsed_time:.2f}s")
                    
                    # 解析操作信息
                    operation_name = result.get("name", "")
                    operation_id = operation_name.split("/")[-1] if operation_name else ""
                    
                    return {
                        "success": True,
                        "operation_name": operation_name,
                        "operation_id": operation_id,
                        "status": "running",
                        "prompt": prompt,
                        "model_id": model_id,
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        "generation_time": elapsed_time,
                        "raw_response": result
                    }
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Vertex AI Veo API request failed: {response.status} - {error_text}")
                    raise ImagesAPIError(
                        f"Vertex AI Veo API request failed: {error_text}",
                        status_code=response.status
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Vertex AI Veo API client error: {str(e)}")
            raise ImagesAPIError(f"Vertex AI Veo API client error: {str(e)}")
        except Exception as e:
            logger.error(f"Vertex AI Veo API unexpected error: {str(e)}")
            raise ImagesAPIError(f"Vertex AI Veo API unexpected error: {str(e)}")

    async def get_operation_status(self, operation_name: str) -> Dict[str, Any]:
        """
        查询Vertex AI操作状态
        
        Args:
            operation_name: 操作名称
            
        Returns:
            操作状态信息
        """
        session = await self._get_session()
        url = f"{self.base_url}/{operation_name}"
        
        try:
            logger.info(f"Checking Vertex AI operation status: {operation_name}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Vertex AI operation status retrieved: {result.get('done', False)}")
                    
                    # 解析操作状态
                    status_info = {
                        "operation_name": operation_name,
                        "done": result.get("done", False),
                        "status": "completed" if result.get("done") else "running"
                    }
                    
                    # 如果操作完成，提取结果
                    if result.get("done"):
                        if "response" in result:
                            status_info["response"] = result["response"]
                        if "error" in result:
                            status_info.update({
                                "status": "failed",
                                "error": result["error"]
                            })
                    
                    # 添加元数据
                    if "metadata" in result:
                        status_info["metadata"] = result["metadata"]
                    
                    return status_info
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Vertex AI operation status request failed: {response.status} - {error_text}")
                    raise ImagesAPIError(
                        f"Vertex AI operation status request failed: {error_text}",
                        status_code=response.status
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Vertex AI operation status client error: {str(e)}")
            raise ImagesAPIError(f"Vertex AI operation status client error: {str(e)}")
        except Exception as e:
            logger.error(f"Vertex AI operation status unexpected error: {str(e)}")
            raise ImagesAPIError(f"Vertex AI operation status unexpected error: {str(e)}")

    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("VertexAIVeoClient session closed")

# 全局客户端实例
_images_client: Optional[ImagesAPIClient] = None
_veo3_client: Optional[Any] = None
_vertex_veo_client: Optional[VertexAIVeoClient] = None

def get_images_client() -> ImagesAPIClient:
    """获取全局Images API客户端实例"""
    global _images_client
    if _images_client is None:
        _images_client = ImagesAPIClient()
    return _images_client

def get_vertex_veo_client() -> VertexAIVeoClient:
    """获取全局Vertex AI Veo客户端实例"""
    global _vertex_veo_client
    if _vertex_veo_client is None:
        _vertex_veo_client = VertexAIVeoClient()
    return _vertex_veo_client

async def cleanup_images_client():
    """清理全局客户端实例"""
    global _images_client, _veo3_client, _vertex_veo_client
    if _images_client:
        await _images_client.close()
        _images_client = None
    if _veo3_client:
        await _veo3_client.close()
        _veo3_client = None
    if _vertex_veo_client:
        await _vertex_veo_client.close()
        _vertex_veo_client = None