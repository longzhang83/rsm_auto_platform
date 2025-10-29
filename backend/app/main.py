from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import JSONResponse
import asyncio
import json

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    # 确保数据目录存在
    settings.data_dir.mkdir(exist_ok=True)
    settings.output_dir.mkdir(exist_ok=True)

    # 集成部署模式下的前端静态文件检查
    if settings.serve_frontend:
        frontend_dist = settings.frontend_build_path
        if frontend_dist.exists():
                print(f"Integrated deployment mode: serving frontend static files from {frontend_dist}")
        else:
            print(f"警告：前端构建目录不存在: {frontend_dist}")
            print("请先构建前端: cd frontend && npm run build")

    yield

    # 关闭时清理（如果需要）


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
    # 生产环境：允许同源和指定域名
    cors_origins = ["*"] if settings.serve_frontend else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

# 集成部署：挂载前端静态文件
if settings.serve_frontend:
    frontend_dist = settings.frontend_build_path
    if frontend_dist.exists():
        # 挂载静态文件
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

        @app.get("/api/v1/status")
        async def deployment_status():
            """部署状态"""
            return {
                "mode": "integrated",
                "environment": settings.environment,
                "frontend_served": True,
                "frontend_path": str(frontend_dist),
                "api_prefix": "/api/v1"
            }


@app.get("/")
async def root():
    """根路径"""
    if settings.serve_frontend:
        # 集成部署模式：返回前端首页
        frontend_dist = settings.frontend_build_path
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            return {
                "message": f"欢迎使用 {settings.app_name}",
                "version": settings.app_version,
                "mode": "integrated",
                "error": "前端构建文件不存在",
                "hint": "请先运行: cd frontend && npm run build"
            }
    else:
        # API 模式：返回 API 信息
        return {
            "message": f"欢迎使用 {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "api": "/api/v1",
        }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "mode": "integrated" if settings.serve_frontend else "api-only"
    }


# 集成部署：SPA 路由支持
if settings.serve_frontend:
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """处理 SPA 路由，返回前端页面"""
        frontend_dist = settings.frontend_build_path
        index_file = frontend_dist / "index.html"

        # 如果是静态文件请求，直接返回
        requested_file = frontend_dist / full_path
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)

        # 否则返回 index.html 让前端路由处理
        if index_file.exists():
            return FileResponse(index_file)

        return {
            "error": "前端构建文件不存在",
            "hint": "请先运行: cd frontend && npm run build"
        }