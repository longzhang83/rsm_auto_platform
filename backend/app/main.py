from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.utils.logger import setup_logging, get_logger, get_translation_logger, get_summary_logger

# 设置日志系统
setup_logging(
    level=settings.log_level,
    log_dir=settings.log_dir,
    enable_console=settings.log_enable_console,
    enable_file=settings.log_enable_file,
    enable_json=settings.log_enable_json,
    colored_console=settings.log_colored_console,
    max_file_size=settings.log_max_file_size,
    backup_count=settings.log_backup_count,
)

# 获取主日志器
logger = get_logger(__name__)

# 为特定模块设置日志级别
translation_logger = get_translation_logger()
translation_logger.setLevel(logging.INFO)

summary_logger = get_summary_logger()
summary_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    # 确保数据目录存在
    settings.data_dir.mkdir(exist_ok=True)
    settings.output_dir.mkdir(exist_ok=True)
    settings.log_dir.mkdir(exist_ok=True)

    logger.info(f"应用启动 - {settings.app_name} v{settings.app_version}")
    logger.info(f"环境: {settings.environment}")
    logger.info(f"数据目录: {settings.data_dir}")
    logger.info(f"输出目录: {settings.output_dir}")
    logger.info(f"日志目录: {settings.log_dir}")
    logger.info(f"翻译缓存路径: {settings.translation_mapping_path}")

    yield

    # 关闭时清理
    logger.info("应用正在关闭...")
    # 可以在这里添加清理逻辑


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="会计凭证生成与摘要翻译API",
    lifespan=lifespan,
)

# 配置CORS
if settings.environment == "development":
    # 开发环境：允许Vue开发服务器
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
else:
    # 生产环境：允许来自nginx的请求
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径 - API信息"""
    logger.info("访问根路径")
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api/v1",
        "health": "/health",
        "mode": "api-only"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    logger.debug("健康检查请求")
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "mode": "api-only",
        "service": "accounting-voucher-generation-api"
    }