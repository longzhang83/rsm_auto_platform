from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import vouchers, translate

api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(vouchers.router, prefix="/vouchers", tags=["vouchers"])
api_router.include_router(translate.router, prefix="/translate", tags=["translate"])