#!/usr/bin/env python3
"""
强制修改所有API文档URL，添加.md后缀
简化逻辑，只要包含文档路径就修改
"""

import json
from pathlib import Path

def force_modify_all_urls():
    """强制为所有符合条件的URL添加.md后缀"""
    
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
            
            # 简单规则：如果URL还没有.md结尾，且是文档相关的URL，就加上.md
            if original_url and not original_url.endswith('.md'):
                # 检查是否是需要修改的URL
                should_modify = False
                
                # 包含这些路径的URL都要修改
                doc_indicators = [
                    '/apidoc/',          # Apifox文档
                    '/docs/',            # 文档页面
                    'docs-site',         # 文档站点
                    'apifox.com/apidoc', # Apifox API文档
                    'chatfire.cn/docs',  # ChatFire文档
                ]
                
                # 排除这些URL
                exclude_patterns = [
                    'https://api.chatfire.cn/pricing',
                    'https://api.chatfire.cn/topup', 
                    'https://status.chatfire.cn',
                    'https://apifox.com$',  # 纯主站链接
                    'https://api.chatfire.cn$'  # 纯主站链接
                ]
                
                # 检查是否应该排除
                is_excluded = False
                for exclude in exclude_patterns:
                    if exclude.replace('$', '') == original_url:
                        is_excluded = True
                        break
                
                # 如果不被排除，且包含文档指示符，就修改
                if not is_excluded:
                    for indicator in doc_indicators:
                        if indicator in original_url:
                            should_modify = True
                            break
                
                if should_modify:
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

def main():
    print("强制修改所有API文档URL，添加.md后缀...")
    force_modify_all_urls()

if __name__ == "__main__":
    main()