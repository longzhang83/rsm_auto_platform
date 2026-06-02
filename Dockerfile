# Python 后端镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行依赖
RUN pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    "pandas>=2.1,<3.0" \
    "openpyxl>=3.1,<4.0" \
    "zhipuai>=2.1.5.20250825" \
    "tqdm>=4.66,<5.0" \
    "xlrd>=1.2,<2.0" \
    "fastapi>=0.111,<0.112" \
    "uvicorn[standard]>=0.30,<0.31" \
    "python-multipart>=0.0.9,<0.0.10" \
    "jinja2>=3.1,<4.0" \
    "sqlalchemy>=2.0,<3.0" \
    "passlib>=1.7,<2.0" \
    "python-jose[cryptography]>=3.3,<4.0" \
    "email-validator>=2.1,<3.0" \
    "httpx>=0.27,<1.0" \
    "pydantic-settings>=2.2,<3.0" \
    "sniffio>=1.3,<2.0"

RUN pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    "loguru>=0.7,<1.0"

# 复制后端源码
COPY backend/app ./app
COPY src ./src

# 创建数据目录
RUN mkdir -p data/output logs

# 设置环境变量
ENV PYTHONPATH="/app:/app/src"
ENV ENVIRONMENT=production
ENV SERVE_FRONTEND=false

# 暴露端口
EXPOSE 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health', timeout=5).read()" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
