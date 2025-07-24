# ChatFire API 文档抓取器

这个目录包含用于抓取 https://api.chatfire.cn/docs API文档的工具。

## 文件说明

- `scrape_chatfire_docs.py` - 完整版抓取器（需要额外依赖）
- `scrape_chatfire_simple.py` - 简化版抓取器（仅使用标准库）
- `run_scraper.py` - 运行脚本
- `requirements.txt` - 依赖包列表

## 使用方法

### 方法一：直接运行简化版（推荐）

```bash
cd crawl
python3 scrape_chatfire_simple.py
```

### 方法二：通过运行脚本

```bash
cd crawl
python3 run_scraper.py
```

### 方法三：使用完整版（需要安装依赖）

```bash
cd crawl
pip install -r requirements.txt
python3 scrape_chatfire_docs.py
```

## 输出说明

抓取的文档将保存在 `../api_docs` 目录中，按以下分类组织：

- **用户管理** - 用户账户、认证相关API
- **消息管理** - 消息发送、接收相关API  
- **文件管理** - 文件上传、下载相关API
- **群组管理** - 群组、团队、频道管理API
- **配置管理** - 系统配置、设置相关API
- **统计分析** - 数据统计、分析报告API
- **系统管理** - 系统管理、控制相关API
- **AI功能** - AI助手、智能功能API
- **接口文档** - API接口参考文档
- **其他** - 未分类的其他API

每个分类目录下包含相应的markdown文件。

## 特性

- 自动分类API文档
- HTML到Markdown格式转换
- 支持表格、代码块等格式
- 避免重复抓取
- 请求频率控制
- 错误处理和重试

## 注意事项

- 抓取过程可能需要几分钟时间
- 网络连接问题可能导致部分页面抓取失败
- 生成的markdown文件可能需要手动调整格式