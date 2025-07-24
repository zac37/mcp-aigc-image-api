#!/usr/bin/env python3
"""
修改apifox_urls.json中的所有API文档URL，添加.md后缀
"""

import json
from pathlib import Path

def modify_urls_with_md_suffix():
    """为apifox_urls.json中的所有URL添加.md后缀"""
    
    input_file = Path("apifox_urls.json")
    output_file = Path("apifox_urls_with_md.json")
    
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
            
            # 检查URL是否需要修改（排除一些不适合添加.md的URL）
            if original_url and should_modify_url(original_url):
                # 在URL末尾添加.md
                item['url'] = original_url + '.md'
                
                # 同时修改href字段
                if 'href' in item and item['href']:
                    item['href'] = item['href'] + '.md'
                
                modified_count += 1
                print(f"修改: {original_url} -> {item['url']}")
        
        # 保存修改后的JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(urls_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理完成:")
        print(f"- 总共处理: {len(urls_data)} 条记录")
        print(f"- 修改数量: {modified_count} 条")
        print(f"- 保存至: {output_file}")
        
        # 同时更新原文件
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(urls_data, f, ensure_ascii=False, indent=2)
        
        print(f"- 原文件已更新: {input_file}")
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

def should_modify_url(url: str) -> bool:
    """判断URL是否应该添加.md后缀"""
    
    # 不修改的URL模式
    skip_patterns = [
        'https://apifox.com',  # Apifox主站
        'https://api.chatfire.cn/pricing',  # 价格页面
        'https://api.chatfire.cn/topup',    # 充值页面
        'https://status.chatfire.cn',       # 状态页面
        '.txt',  # 已经有文件扩展名的
        '.json',
        '.xml',
        '.html'
    ]
    
    # 检查是否包含不应修改的模式
    for pattern in skip_patterns:
        if pattern in url:
            return False
    
    # 检查是否是API文档相关的URL
    api_patterns = [
        '/apidoc/',
        '/docs/',
        'apifox.com/apidoc',
        'chatfire.cn/docs'
    ]
    
    # 只修改API文档相关的URL
    for pattern in api_patterns:
        if pattern in url:
            return True
    
    return False

def main():
    print("开始修改API文档URL，添加.md后缀...")
    modify_urls_with_md_suffix()

if __name__ == "__main__":
    main()