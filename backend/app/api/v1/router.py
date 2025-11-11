from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    vouchers,
    progress,
    translate_v2,
    logs,
    bank_statements,
    dashboard,
    auth,
)

api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(vouchers.router, prefix="/vouchers", tags=["vouchers"])
api_router.include_router(translate_v2.router, prefix="/translate", tags=["translate"])
api_router.include_router(progress.router, tags=["progress"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(
    bank_statements.router, prefix="/bank-statements", tags=["bank-statements"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
