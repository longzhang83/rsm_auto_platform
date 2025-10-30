# Python 后端镜像
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目依赖文件
COPY pyproject.toml .
COPY backend/requirements.txt .
COPY uv.lock* .

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# 激活虚拟环境
RUN echo ". /opt/venv/bin/activate" >> /root/.bashrc

# 复制后端源码
COPY backend/app ./backend/app
COPY src ./src

# 创建数据目录
RUN mkdir -p data/output

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV ENVIRONMENT=production
ENV SERVE_FRONTEND=true

# 暴露端口
EXPOSE 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# 启动命令
CMD ["/opt/venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8888"]