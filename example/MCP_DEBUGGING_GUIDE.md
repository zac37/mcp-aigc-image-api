# MCP服务调试与修复经验指南

**版本**: v1.0  
**更新时间**: 2025-07-23  
**适用场景**: FastMCP + Docker部署环境

## 问题概述

在将Kling API部署到Docker容器时，MCP（Model Context Protocol）服务出现无法启动和工具列表加载失败的问题。经过对比成功案例meta-curl-api的实现，最终成功解决了所有问题。

## 问题分析与解决方案

### 问题1：MCP服务启动方式错误

**错误现象**：
```bash
TypeError: FastMCP.run_stdio_async() got an unexpected keyword argument 'host'
```

**原因分析**：
- 使用`uvicorn`启动FastMCP应用是错误的方式
- FastMCP有自己的运行机制，不应该通过uvicorn包装启动
- `run_stdio_async`方法不接受`host`参数，这是内部实现细节

**解决方案**：
创建独立的MCP启动脚本`scripts/run_mcp_streamable.py`：

```python
from routers.mcp.main import app as mcp
# 直接调用FastMCP的run方法
mcp.run(transport="streamable-http", host="0.0.0.0", port=5510)
```

### 问题2：FastMCP应用配置不完善

**错误现象**：
- 连接不稳定
- 工具列表无法获取
- 内部服务器错误

**原因分析**：
- 缺少FastMCP的高级配置参数
- 错误处理和连接管理配置缺失
- 缺少必要的资源和提示定义

**解决方案**：
参考meta-curl-api的成功配置模式：

```python
# 创建MCP应用 - 优化配置以提高连接稳定性
mcp = FastMCP(
    "Kling API",
    # 启用短期缓存以提高连接稳定性
    cache_expiration_seconds=30.0,
    # 简化错误处理
    mask_error_details=False,
    # 处理重复工具时的行为
    on_duplicate_tools="ignore",
    on_duplicate_resources="ignore", 
    on_duplicate_prompts="ignore",
    # 添加连接管理配置
    max_message_size=1024*1024,  # 1MB消息大小限制
    keep_alive_interval=10.0,    # 10秒心跳间隔
    connection_timeout=60.0       # 60秒连接超时
)
```

### 问题3：缺少MCP资源和提示定义

**错误现象**：
- MCP协议功能不完整
- 客户端连接后功能受限

**原因分析**：
- 只注册了工具，缺少资源(resources)和提示(prompts)
- MCP协议需要完整的功能定义

**解决方案**：
添加资源和提示定义：

```python
@mcp.resource("kling://config")
def get_mcp_config():
    """MCP配置信息"""
    return {
        "name": "Kling API",
        "version": "1.0.0",
        # ...配置详情
    }

@mcp.prompt("kling_usage_guide")
def kling_usage_guide():
    """Kling API使用指南"""
    return """
    # 详细的使用指南内容
    """
```

### 问题4：Docker容器中的进程管理

**错误现象**：
- 端口被占用（Address already in use）
- 多个进程同时运行冲突

**原因分析**：
- Docker entrypoint脚本中的旧进程没有正确清理
- 新旧启动方式并存导致端口冲突

**解决方案**：
1. 修改docker-entrypoint.sh使用新的启动脚本：
```bash
# 启动MCP服务 (后台运行)
python3 scripts/run_mcp_streamable.py > /app/logs/mcp_service.log 2>&1 &
```

2. 容器重启前清理旧进程：
```bash
docker exec -it container-name kill $(ps aux | grep 'routers.mcp.main' | grep -v grep | awk '{print $2}')
```

### 问题5：FastMCP版本兼容性

**错误现象**：
```python
AttributeError: 'FastMCP' object has no attribute 'tools'
```

**原因分析**：
- FastMCP 2.5.1版本中，工具列表的访问方式可能有变化
- 不同版本的API接口存在差异

**解决方案**：
- 避免在启动脚本中直接访问`mcp.tools`属性
- 专注于核心功能实现，让FastMCP内部处理工具管理
- 参考官方文档和成功案例的实现方式

## 最佳实践总结

### 1. 架构设计原则
- **分离关注点**: MCP服务和FastAPI服务应该独立启动
- **参考成功案例**: 遇到问题时对比已运行成功的类似服务
- **渐进式修复**: 先解决核心问题，再优化细节功能

### 2. 调试方法
- **查看进程状态**: 使用`ps aux`检查容器内进程
- **检查端口占用**: 识别端口冲突问题
- **对比日志输出**: 成功案例vs问题案例的启动日志对比
- **分步验证**: 先本地测试，再容器内测试

### 3. 代码组织
```
kling-api/
├── scripts/
│   └── run_mcp_streamable.py    # 独立MCP启动脚本
├── routers/mcp/
│   ├── main.py                  # MCP应用定义
│   └── kling_tools.py           # 工具函数
└── docker-entrypoint.sh         # 容器启动脚本
```

### 4. 配置要点
- **传输协议**: 使用`streamable-http`而非`stdio`
- **网络绑定**: 容器内使用`0.0.0.0`绑定所有接口
- **错误处理**: 设置`mask_error_details=False`便于调试
- **连接管理**: 配置合适的超时和心跳参数

## 验证清单

修复MCP服务后，按以下清单验证：

- [ ] 容器启动无错误日志
- [ ] MCP服务监听在正确端口(5510)
- [ ] 可以接收MCP初始化请求
- [ ] 工具列表能够正常返回
- [ ] 客户端可以成功调用工具函数
- [ ] 长时间运行稳定性测试通过

## 常见错误及快速解决

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Address already in use` | 端口被占用 | 杀死旧进程或更换端口 |
| `got an unexpected keyword argument 'host'` | 启动方式错误 | 使用独立脚本启动 |
| `Missing session ID` | MCP协议错误 | 先发送initialize请求 |
| `'FastMCP' object has no attribute 'tools'` | 版本兼容性 | 避免直接访问内部属性 |

## 总结

MCP服务的成功部署关键在于：
1. **正确的启动方式**: 使用独立脚本而非uvicorn
2. **完整的配置**: 参考成功案例添加所有必要配置
3. **进程管理**: 避免端口冲突和进程重复
4. **协议遵循**: 严格按照MCP协议规范实现

通过对比成功案例meta-curl-api的实现，我们学到了MCP服务部署的正确模式，这为后续类似项目提供了宝贵经验。

---
*本文档基于实际问题解决过程总结，如有更新请及时修订版本号和时间。* 