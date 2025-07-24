#!/usr/bin/env python3
"""
修改apifox_urls.json中的所有API文档URL，添加.md后缀
这次修改所有相关的URL，不要遗漏
"""

import json
from pathlib import Path

def modify_all_api_urls():
    """为apifox_urls.json中的所有API相关URL添加.md后缀"""
    
    input_file = Path("apifox_urls.json")
    
    if not input_file.exists():
        print(f"错误: 文件 {input_file} 不存在")
        return
    
    try:
        # 读取原始JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            urls_data = json.load(f)
        
        print(f"读取到 {len(urls_data)} 条URL记录")
        
        # 修改每个URL记录
        modified_count = 0
        for item in urls_data:
            original_url = item.get('url', '')
            
            # 检查URL是否需要修改
            if original_url and should_modify_url(original_url):
                # 在URL末尾添加.md
                if not original_url.endswith('.md'):
                    item['url'] = original_url + '.md'
                    
                    # 同时修改href字段
                    if 'href' in item and item['href'] and not item['href'].endswith('.md'):
                        item['href'] = item['href'] + '.md'
                    
                    modified_count += 1
                    print(f"修改: {original_url} -> {item['url']}")
        
        # 保存修改后的JSON文件
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(urls_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理完成:")
        print(f"- 总共处理: {len(urls_data)} 条记录")
        print(f"- 修改数量: {modified_count} 条")
        print(f"- 文件已更新: {input_file}")
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

def should_modify_url(url: str) -> bool:
    """判断URL是否应该添加.md后缀 - 更宽松的条件"""
    
    # 明确不修改的URL模式
    skip_patterns = [
        'https://api.chatfire.cn/pricing',  # 价格页面
        'https://api.chatfire.cn/topup',    # 充值页面
        'https://status.chatfire.cn',       # 状态页面
        'https://apifox.com',              # 纯Apifox主站链接（不包含文档路径）
        'https://api.chatfire.cn$'         # 纯官网主页（以$结尾表示精确匹配）
    ]
    
    # 检查精确匹配的URL
    exact_skip_urls = [
        'https://api.chatfire.cn',
        'https://apifox.com'
    ]
    
    if url in exact_skip_urls:
        return False
    
    # 检查是否包含不应修改的模式
    for pattern in skip_patterns:
        if pattern.replace('$', '') == url:  # 精确匹配
            return False
        if pattern not in ['https://api.chatfire.cn$'] and pattern in url:
            return False
    
    # 包含以下模式的URL都应该修改
    api_patterns = [
        '/apidoc/',        # Apifox文档
        '/docs/',          # ChatFire文档
        'apifox.com/apidoc',  # Apifox API文档
        'chatfire.cn/docs',   # ChatFire API文档
        '.txt',           # 文本文件
        'm0',             # 以m0结尾的文档ID
        'e0',             # 以e0结尾的文档ID 
        'f0'              # 以f0结尾的文档ID
    ]
    
    # 检查是否匹配API文档模式
    for pattern in api_patterns:
        if pattern in url:
            return True
    
    return False

def main():
    print("开始修改所有API文档URL，添加.md后缀...")
    modify_all_api_urls()

if __name__ == "__main__":
    main()