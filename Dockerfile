# 使用Python 3.11作为基础镜像（支持fastmcp>=0.2.0）
FROM python:3.11-slim

# 设置时区和语言环境
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# 复制requirements文件
COPY requirements.txt .

# 升级pip并安装Python依赖
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录并设置权限
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 5512 5513

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5512/api/health || exit 1

# 创建启动脚本
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# 使用启动脚本
ENTRYPOINT ["/app/docker-entrypoint.sh"]