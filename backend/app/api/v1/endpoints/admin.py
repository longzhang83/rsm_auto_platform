"""
管理员API端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import User
from app.api.dependencies import get_current_admin
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

router = APIRouter()


class UserLoginStats(BaseModel):
    """用户登录方式统计"""

    login_type: str = Field(..., description="登录方式")
    count: int = Field(..., description="用户数量")
    percentage: float = Field(..., description="占比百分比")


class RecentUser(BaseModel):
    """最近注册用户"""

    id: int
    username: str
    email: str
    login_type: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """用户统计信息"""

    total_users: int = Field(..., description="总用户数")
    admin_users: int = Field(..., description="管理员用户数")
    password_users: int = Field(..., description="密码登录用户数")
    wework_users: int = Field(..., description="企业微信登录用户数")
    login_type_distribution: List[UserLoginStats] = Field(
        ..., description="登录方式分布"
    )
    recent_users: List[RecentUser] = Field(..., description="最近注册用户")


class UserListItem(BaseModel):
    """用户列表项"""

    id: int
    username: str
    email: str
    login_type: str
    is_admin: bool
    wework_userid: str | None
    wework_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""

    total: int = Field(..., description="总数")
    users: List[UserListItem] = Field(..., description="用户列表")


@router.get("/stats", response_model=UserStats, summary="获取用户统计信息")
async def get_user_stats(
    _: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """
    获取用户统计信息（需要管理员权限）

    返回：
    - 总用户数
    - 管理员用户数
    - 按登录方式分组的用户统计
    - 最近注册的10个用户
    """
    # 总用户数
    total_users = db.query(User).count()

    # 管理员用户数
    admin_users = db.query(User).filter(User.is_admin == True).count()  # noqa: E712

    # 密码登录用户数
    password_users = (
        db.query(User).filter(User.login_type == "password").count()
    )

    # 企业微信登录用户数
    wework_users = db.query(User).filter(User.login_type == "wework").count()

    # 登录方式分布
    login_type_stats = (
        db.query(User.login_type, func.count(User.id))
        .group_by(User.login_type)
        .all()
    )

    login_type_distribution = []
    for login_type, count in login_type_stats:
        percentage = (count / total_users * 100) if total_users > 0 else 0
        login_type_distribution.append(
            UserLoginStats(
                login_type=login_type, count=count, percentage=round(percentage, 2)
            )
        )

    # 最近注册的10个用户
    recent_users = (
        db.query(User).order_by(User.created_at.desc()).limit(10).all()
    )

    return UserStats(
        total_users=total_users,
        admin_users=admin_users,
        password_users=password_users,
        wework_users=wework_users,
        login_type_distribution=login_type_distribution,
        recent_users=[RecentUser.model_validate(user) for user in recent_users],
    )


@router.get("/users", response_model=UserListResponse, summary="获取用户列表")
async def get_user_list(
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（需要管理员权限）

    - **page**: 页码（从1开始）
    - **page_size**: 每页数量

    返回分页的用户列表
    """
    # 计算总数
    total = db.query(User).count()

    # 分页查询
    offset = (page - 1) * page_size
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return UserListResponse(
        total=total, users=[UserListItem.model_validate(user) for user in users]
    )
