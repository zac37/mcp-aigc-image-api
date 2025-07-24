#!/usr/bin/env python3
"""
ChatFire API Documentation Scraper with Selenium
使用Selenium处理JavaScript动态内容的API文档抓取器
"""

import time
import re
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class SeleniumDocsScraper:
    def __init__(self, base_url: str = "https://api.chatfire.cn/docs", output_dir: str = "../api_docs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls: Set[str] = set()
        self.driver = None
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
    def setup_driver(self):
        """设置Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            return True
        except Exception as e:
            print(f"无法启动Chrome WebDriver: {e}")
            print("请确保已安装Chrome浏览器和ChromeDriver")
            return False
    
    def get_page_content(self, url: str) -> str:
        """获取页面完整内容，等待JavaScript加载"""
        try:
            print(f"正在加载: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 额外等待确保动态内容加载
            time.sleep(3)
            
            # 尝试等待特定的内容元素
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".content, .main-content, article, main"))
                )
            except TimeoutException:
                pass
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"加载页面失败 {url}: {e}")
            return ""
    
    def extract_content(self, html: str, url: str) -> Dict[str, str]:
        """提取页面内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 尝试多种内容选择器
        content_selectors = [
            '.content',
            '.main-content', 
            '.api-content',
            '.documentation',
            'main',
            'article',
            '#content',
            '#main-content',
            '.markdown-body',
            '.doc-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element and content_element.get_text(strip=True):
                break
        
        if not content_element:
            # 如果找不到特定内容区域，使用body但排除导航
            content_element = soup.find('body')
            if content_element:
                # 移除导航、侧边栏等
                for nav in content_element.find_all(['nav', 'header', 'footer']):
                    nav.decompose()
                for sidebar in content_element.find_all(class_=re.compile(r'sidebar|navigation|menu')):
                    sidebar.decompose()
        
        # 提取标题
        title = ""
        title_selectors = ['h1', 'h2', '.title', 'title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            # 从URL提取标题
            title = url.split('/')[-1] or "未知页面"
        
        # 转换为markdown
        markdown_content = self.html_to_markdown(content_element) if content_element else ""
        
        return {
            'title': title,
            'content': markdown_content,
            'url': url
        }
    
    def html_to_markdown(self, element) -> str:
        """将HTML元素转换为Markdown"""
        if not element:
            return ""
        
        markdown_lines = []
        
        # 处理各种HTML元素
        for elem in element.find_all(True):
            tag = elem.name.lower()
            text = elem.get_text(strip=True)
            
            if not text:
                continue
                
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag[1])
                markdown_lines.append(f"{'#' * level} {text}")
                
            elif tag == 'p':
                markdown_lines.append(text)
                
            elif tag in ['ul', 'ol']:
                # 处理列表项
                for li in elem.find_all('li', recursive=False):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_lines.append(f"- {li_text}")
                        
            elif tag == 'pre':
                code_text = elem.get_text()
                markdown_lines.append(f"```\n{code_text}\n```")
                
            elif tag == 'code' and elem.parent.name != 'pre':
                markdown_lines.append(f"`{text}`")
                
            elif tag == 'table':
                table_md = self.convert_table(elem)
                if table_md:
                    markdown_lines.append(table_md)
        
        # 如果没有提取到结构化内容，直接使用文本
        if not markdown_lines:
            text_content = element.get_text(strip=True)
            if text_content:
                markdown_lines.append(text_content)
        
        return '\n\n'.join(markdown_lines)
    
    def convert_table(self, table_elem) -> str:
        """转换表格为Markdown格式"""
        rows = []
        
        # 处理表头
        thead = table_elem.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                if headers:
                    rows.append('| ' + ' | '.join(headers) + ' |')
                    rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # 处理表格内容
        tbody = table_elem.find('tbody') or table_elem
        for tr in tbody.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')
        
        return '\n'.join(rows) if rows else ""
    
    def categorize_content(self, title: str, url: str, content: str) -> str:
        """根据内容对API进行分类"""
        title_lower = title.lower()
        url_lower = url.lower()
        content_lower = content.lower()
        
        # 扩展的分类规则
        categories = {
            '图像生成': ['image', 'picture', 'photo', 'flux', 'stable', 'midjourney', '图像', '图片', '生成', 'generate'],
            '视频生成': ['video', 'movie', 'clip', '视频', '影片', 'cogvideo', 'runway', 'pika'],
            '语音处理': ['audio', 'voice', 'speech', 'tts', '语音', '音频', '合成', '克隆'],
            '文件处理': ['file', 'upload', 'download', '文件', '上传', '下载', 'pdf', 'document'],
            '任务管理': ['task', 'job', 'queue', '任务', '队列', '状态', 'status'],
            '内容审核': ['moderation', 'review', 'check', '审核', '检查', '过滤'],
            '文本处理': ['text', 'translate', 'ocr', '文本', '翻译', '识别'],
            '嵌入向量': ['embedding', 'vector', '嵌入', '向量', '相似'],
            '系统接口': ['api', 'system', 'config', '系统', '配置', '接口'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower or keyword in url_lower or keyword in content_lower 
                   for keyword in keywords):
                return category
        
        return '其他'
    
    def save_content(self, category: str, title: str, content: str, url: str):
        """保存内容到文件"""
        # 创建分类目录
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # 清理文件名
        safe_filename = re.sub(r'[^\w\s-]', '', title).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        if not safe_filename:
            safe_filename = f"page-{len(self.visited_urls)}"
        
        file_path = category_dir / f"{safe_filename}.md"
        
        # 构建完整的markdown内容
        full_content = f"# {title}\n\n"
        full_content += f"**URL**: {url}\n\n"
        full_content += content
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            print(f"保存: {file_path}")
            return True
        except Exception as e:
            print(f"保存失败 {file_path}: {e}")
            return False
    
    def discover_links(self) -> List[str]:
        """发现所有文档链接"""
        print("正在发现文档链接...")
        
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            return []
        
        soup = BeautifulSoup(main_content, 'html.parser')
        links = set()
        
        # 查找所有链接
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if href and not href.startswith('#'):
                full_url = urljoin(self.base_url, href)
                # 只保留同域名的文档链接
                if full_url.startswith(self.base_url.split('/docs')[0]):
                    links.add(full_url)
        
        print(f"发现 {len(links)} 个链接")
        return list(links)
    
    def scrape_sample_pages(self, max_pages: int = 10):
        """抓取样本页面进行测试"""
        if not self.setup_driver():
            return
        
        try:
            links = self.discover_links()
            
            # 限制抓取数量进行测试
            test_links = links[:max_pages]
            
            print(f"开始抓取 {len(test_links)} 个样本页面...")
            
            for i, url in enumerate(test_links, 1):
                if url in self.visited_urls:
                    continue
                    
                print(f"[{i}/{len(test_links)}] 处理: {url}")
                
                html_content = self.get_page_content(url)
                if html_content:
                    content_data = self.extract_content(html_content, url)
                    
                    if content_data['content'].strip():
                        category = self.categorize_content(
                            content_data['title'], 
                            url, 
                            content_data['content']
                        )
                        
                        self.save_content(
                            category,
                            content_data['title'],
                            content_data['content'],
                            url
                        )
                        
                        self.visited_urls.add(url)
                    else:
                        print(f"  内容为空，跳过")
                else:
                    print(f"  无法获取内容")
                
                # 添加延迟
                time.sleep(2)
            
            print(f"\n样本抓取完成! 共处理 {len(self.visited_urls)} 个页面")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()


def main():
    scraper = SeleniumDocsScraper()
    
    print("ChatFire API文档抓取器 (Selenium版本)")
    print("=" * 50)
    
    # 先抓取少量页面测试
    scraper.scrape_sample_pages(max_pages=5)


if __name__ == "__main__":
    main()