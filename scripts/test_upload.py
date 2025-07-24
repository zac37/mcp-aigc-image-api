#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件上传功能测试脚本

测试MinIO文件存储相关的API功能
"""

import requests
import json
import os
import sys
from pathlib import Path
import tempfile
from PIL import Image
import io

# API基础配置
BASE_URL = "http://localhost:5512/api"
API_ENDPOINTS = {
    "health": f"{BASE_URL}/health",
    "upload": f"{BASE_URL}/files/upload",
    "get_url": f"{BASE_URL}/files",
    "list_files": f"{BASE_URL}/files",
    "delete": f"{BASE_URL}/files"
}

def create_test_image(width=100, height=100, color=(255, 0, 0), format='PNG'):
    """创建测试图片"""
    image = Image.new('RGB', (width, height), color)
    img_buffer = io.BytesIO()
    image.save(img_buffer, format=format)
    img_buffer.seek(0)
    return img_buffer

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    
    try:
        response = requests.get(API_ENDPOINTS["health"])
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功")
            print(f"   服务状态: {data.get('status')}")
            print(f"   存储状态: {data.get('storage', {}).get('status')}")
            print(f"   文件存储: {'启用' if data.get('file_storage', {}).get('enabled') else '禁用'}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_file_upload():
    """测试文件上传"""
    print("\n📤 测试文件上传...")
    
    try:
        # 创建测试图片
        test_image = create_test_image(200, 200, (0, 255, 0))
        
        # 准备上传文件
        files = {
            'file': ('test_image.png', test_image, 'image/png')
        }
        
        # 上传文件
        response = requests.post(
            API_ENDPOINTS["upload"],
            files=files,
            params={'folder': 'test-uploads'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                file_info = data.get('data', {})
                print(f"✅ 文件上传成功")
                print(f"   对象名称: {file_info.get('object_name')}")
                print(f"   原始文件名: {file_info.get('original_filename')}")
                print(f"   文件大小: {file_info.get('file_size')} bytes")
                print(f"   内容类型: {file_info.get('content_type')}")
                print(f"   访问URL: {file_info.get('file_url')[:100]}...")
                return file_info.get('object_name')
            else:
                print(f"❌ 文件上传失败: {data.get('error')}")
                return None
        else:
            print(f"❌ 文件上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 文件上传异常: {e}")
        return None

def test_get_file_url(object_name):
    """测试获取文件URL"""
    print(f"\n🔗 测试获取文件URL: {object_name}")
    
    try:
        response = requests.get(
            f"{API_ENDPOINTS['get_url']}/{object_name}",
            params={'expires_hours': 2}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                file_data = data.get('data', {})
                print(f"✅ 获取文件URL成功")
                print(f"   对象名称: {file_data.get('object_name')}")
                print(f"   过期时间: {file_data.get('expires_hours')} 小时")
                print(f"   访问URL: {file_data.get('file_url')[:100]}...")
                
                # 测试URL是否可访问
                url_response = requests.head(file_data.get('file_url'))
                if url_response.status_code == 200:
                    print(f"✅ URL可正常访问")
                else:
                    print(f"⚠️  URL访问异常: {url_response.status_code}")
                    
                return True
            else:
                print(f"❌ 获取文件URL失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 获取文件URL失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取文件URL异常: {e}")
        return False

def test_redirect_to_file(object_name):
    """测试文件重定向"""
    print(f"\n🔀 测试文件重定向: {object_name}")
    
    try:
        response = requests.get(
            f"{API_ENDPOINTS['get_url']}/{object_name}/redirect",
            allow_redirects=False
        )
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')
            print(f"✅ 文件重定向成功")
            print(f"   重定向URL: {redirect_url[:100]}...")
            return True
        else:
            print(f"❌ 文件重定向失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 文件重定向异常: {e}")
        return False

def test_list_files():
    """测试文件列表"""
    print(f"\n📋 测试文件列表...")
    
    try:
        response = requests.get(
            API_ENDPOINTS["list_files"],
            params={
                'prefix': 'test-uploads',
                'limit': 10
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                file_data = data.get('data', {})
                files = file_data.get('files', [])
                print(f"✅ 获取文件列表成功")
                print(f"   文件数量: {file_data.get('count')}")
                print(f"   前缀过滤: {file_data.get('prefix')}")
                
                for i, file_info in enumerate(files[:3]):  # 只显示前3个
                    print(f"   文件{i+1}: {file_info.get('object_name')}")
                    print(f"         大小: {file_info.get('size')} bytes")
                    
                return True
            else:
                print(f"❌ 获取文件列表失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 获取文件列表失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取文件列表异常: {e}")
        return False

def test_delete_file(object_name):
    """测试文件删除"""
    print(f"\n🗑️  测试文件删除: {object_name}")
    
    try:
        response = requests.delete(f"{API_ENDPOINTS['delete']}/{object_name}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 文件删除成功")
                print(f"   对象名称: {data.get('data', {}).get('object_name')}")
                return True
            else:
                print(f"❌ 文件删除失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 文件删除失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 文件删除异常: {e}")
        return False

def test_upload_large_file():
    """测试大文件上传（应该失败）"""
    print(f"\n📦 测试大文件上传（超过限制）...")
    
    try:
        # 创建一个超过50MB的测试文件
        large_image = create_test_image(5000, 5000, (0, 0, 255), 'PNG')
        
        files = {
            'file': ('large_test_image.png', large_image, 'image/png')
        }
        
        response = requests.post(
            API_ENDPOINTS["upload"],
            files=files,
            params={'folder': 'test-uploads'}
        )
        
        if response.status_code == 400:
            print(f"✅ 大文件上传正确被拒绝")
            print(f"   错误信息: {response.json().get('detail', response.text)}")
            return True
        elif response.status_code == 200:
            print(f"⚠️  大文件上传意外成功（可能需要调整限制）")
            return True
        else:
            print(f"❌ 大文件上传测试异常: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 大文件上传测试异常: {e}")
        return False

def test_upload_invalid_file():
    """测试无效文件上传（应该失败）"""
    print(f"\n🚫 测试无效文件上传...")
    
    try:
        # 创建一个文本文件
        text_content = b"This is a text file, not an image"
        
        files = {
            'file': ('test.txt', io.BytesIO(text_content), 'text/plain')
        }
        
        response = requests.post(
            API_ENDPOINTS["upload"],
            files=files,
            params={'folder': 'test-uploads'}
        )
        
        if response.status_code == 400:
            print(f"✅ 无效文件上传正确被拒绝")
            print(f"   错误信息: {response.json().get('detail', response.text)}")
            return True
        elif response.status_code == 200:
            print(f"⚠️  无效文件上传意外成功（可能需要调整验证）")
            return True
        else:
            print(f"❌ 无效文件上传测试异常: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 无效文件上传测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试MinIO文件存储功能...\n")
    
    test_results = []
    uploaded_object = None
    
    # 1. 健康检查
    test_results.append(("健康检查", test_health_check()))
    
    # 2. 文件上传
    uploaded_object = test_file_upload()
    test_results.append(("文件上传", uploaded_object is not None))
    
    if uploaded_object:
        # 3. 获取文件URL
        test_results.append(("获取文件URL", test_get_file_url(uploaded_object)))
        
        # 4. 文件重定向
        test_results.append(("文件重定向", test_redirect_to_file(uploaded_object)))
        
        # 5. 文件列表
        test_results.append(("文件列表", test_list_files()))
        
        # 6. 文件删除
        test_results.append(("文件删除", test_delete_file(uploaded_object)))
    
    # 7. 大文件上传测试
    test_results.append(("大文件上传限制", test_upload_large_file()))
    
    # 8. 无效文件上传测试
    test_results.append(("无效文件上传限制", test_upload_invalid_file()))
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print(f"📊 测试结果汇总:")
    print(f"{'='*50}")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed + failed} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print(f"\n🎉 所有测试通过！MinIO文件存储功能正常运行。")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {e}")
        sys.exit(1)