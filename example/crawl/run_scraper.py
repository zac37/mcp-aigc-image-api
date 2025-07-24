#!/usr/bin/env python3
"""
运行ChatFire文档抓取器的脚本
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

try:
    from scrape_chatfire_simple import ChatFireDocsScraper
    
    def main():
        print("ChatFire API文档抓取器")
        print("=" * 50)
        
        scraper = ChatFireDocsScraper()
        scraper.scrape_all()
        
        print("\n完成!")
        
        # 显示结果统计
        api_docs_dir = Path("../api_docs")
        if api_docs_dir.exists():
            categories = [d for d in api_docs_dir.iterdir() if d.is_dir()]
            print(f"\n生成的文档分类 ({len(categories)} 个):")
            
            total_files = 0
            for category_dir in categories:
                md_files = list(category_dir.glob("*.md"))
                total_files += len(md_files)
                print(f"  {category_dir.name}: {len(md_files)} 个文件")
            
            print(f"\n总共生成 {total_files} 个markdown文件")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保 scrape_chatfire_simple.py 文件存在")
except Exception as e:
    print(f"运行错误: {e}")
    import traceback
    traceback.print_exc()