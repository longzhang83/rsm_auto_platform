"""
认证相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    SendVerificationCodeRequest, SendVerificationCodeResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from app.services.auth_service import AuthService
from app.services.verification_service import VerificationService
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/send-verification-code", response_model=SendVerificationCodeResponse, summary="发送邮箱验证码")
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送邮箱验证码

    - **email**: 邮箱地址（必须是rsmchina.com.cn域名）

    返回：
    - **success**: 是否发送成功
    - **message**: 提示消息
    """
    success, message = VerificationService.send_code(db, request.email)
    return SendVerificationCodeResponse(success=success, message=message)


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址（rsmchina.com.cn域名）
    - **password**: 密码（6-100字符）
    - **verification_code**: 邮箱验证码（需要先发送验证码）
    """
    return AuthService.register_user(db, user_data)


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    Returns:
        Token和用户信息
    """
    return AuthService.login_user(db, login_data)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息

    需要认证
    """
    return UserResponse.model_validate(current_user)


@router.post("/send-reset-password-code", response_model=SendVerificationCodeResponse, summary="发送密码重置验证码")
async def send_reset_password_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送密码重置验证码

    - **email**: 注册的邮箱地址

    返回：
    - **success**: 是否发送成功
    - **message**: 提示消息
    """
    success, message = VerificationService.send_code(db, request.email, code_type="reset_password")
    return SendVerificationCodeResponse(success=success, message=message)


@router.post("/reset-password", response_model=ResetPasswordResponse, summary="重置密码")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    重置密码

    - **email**: 邮箱地址
    - **verification_code**: 邮箱验证码
    - **new_password**: 新密码（6-100字符）

    返回：
    - **success**: 是否重置成功
    - **message**: 提示消息
    """
    # 验证验证码
    success, message = VerificationService.verify_code(
        db, request.email, request.verification_code, code_type="reset_password"
    )
    if not success:
        return ResetPasswordResponse(success=False, message=message)

    # 查找用户
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return ResetPasswordResponse(success=False, message="用户不存在")

    # 更新密码
    from app.utils.auth import get_password_hash
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    return ResetPasswordResponse(success=True, message="密码重置成功，请使用新密码登录")
