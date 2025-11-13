"""
认证相关API端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    WeWorkConfigResponse,
    WeWorkCallbackRequest,
    WeWorkBindRequest,
    WeWorkBindResponse,
    WeWorkUnbindResponse,
)
from app.services.auth_service import AuthService
from app.services.verification_service import VerificationService
from app.services.wework_service import WeWorkService
from app.api.dependencies import get_current_user
from app.core.config import settings

router = APIRouter()


@router.get(
    "/email-domains",
    response_model=dict,
    summary="获取允许的邮箱域名列表"
)
async def get_allowed_email_domains():
    """
    获取注册时允许的邮箱域名列表

    返回：
    - **domains**: 域名列表（如 ["rsmchina.com.cn", "rsmcn.cloud"]）
    """
    # 从配置中读取域名，支持逗号分隔的多个域名
    domains_str = settings.allowed_email_domains
    domains = [d.strip() for d in domains_str.split(',') if d.strip()]
    return {"domains": domains}


@router.post(
    "/send-verification-code",
    response_model=SendVerificationCodeResponse,
    summary="发送邮箱验证码",
)
async def send_verification_code(
    request: SendVerificationCodeRequest, db: Session = Depends(get_db)
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
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址（rsmchina.com.cn域名）
    - **password**: 密码（6-100字符）
    - **verification_code**: 邮箱验证码（需要先发送验证码）
    """
    return AuthService.register_user(db, user_data)


@router.post("/login", response_model=Token, summary="用户登录")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    Returns:
        Token和用户信息
    """
    return AuthService.login_user(db, login_data)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息

    需要认证
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/forgot-password", response_model=PasswordResetResponse, summary="请求重置密码"
)
async def forgot_password(
    request_data: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    请求重置密码

    - **email**: 注册邮箱地址

    Returns:
        重置密码响应（开发环境包含token）
    """
    return AuthService.request_password_reset(db, request_data)


@router.post("/reset-password", summary="重置密码")
async def reset_password(
    reset_data: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """
    重置密码

    - **token**: 重置密码token
    - **new_password**: 新密码（6-100字符）

    Returns:
        成功消息
    """
    return AuthService.reset_password(db, reset_data)


@router.post(
    "/change-password", response_model=ChangePasswordResponse, summary="修改密码"
)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    修改密码（需要认证）

    - **old_password**: 当前密码（如果账号有密码）
    - **new_password**: 新密码（6-100字符）

    场景：
    1. 已有密码的账号修改密码：需要验证旧密码
    2. 纯企业微信账号设置密码：不需要旧密码

    Returns:
        修改结果
    """
    return AuthService.change_password(db, current_user, change_data)


# 企业微信相关端点


@router.get(
    "/wework/config", response_model=WeWorkConfigResponse, summary="获取企业微信登录配置"
)
async def get_wework_config():
    """
    获取企业微信登录配置

    返回企业微信二维码所需的配置信息：
    - **corp_id**: 企业ID
    - **agent_id**: 应用ID
    - **redirect_uri**: 回调URL
    - **state**: 随机state字符串（用于防止CSRF攻击）
    - **enabled**: 是否启用企业微信登录

    前端使用此配置生成企业微信登录二维码
    """
    if not WeWorkService.is_enabled():
        return WeWorkConfigResponse(
            corp_id="",
            agent_id="",
            redirect_uri="",
            state="",
            enabled=False,
        )

    return WeWorkConfigResponse(
        corp_id=settings.wework_corp_id or "",
        agent_id=settings.wework_agent_id or "",
        redirect_uri=settings.wework_callback_url or "",
        state=WeWorkService.generate_state(),
        enabled=True,
    )


@router.post("/wework/callback", response_model=Token, summary="企业微信授权回调")
async def wework_callback(
    callback_data: WeWorkCallbackRequest, db: Session = Depends(get_db)
):
    """
    企业微信授权回调

    - **code**: 企业微信授权码
    - **state**: State字符串（需与请求时一致）

    流程：
    1. 使用code换取企业微信用户信息
    2. 检查用户是否已绑定账号
    3. 如果已绑定，直接登录
    4. 如果未绑定但邮箱匹配，自动绑定
    5. 否则创建新账号

    Returns:
        JWT Token和用户信息
    """
    # TODO: 实际应该验证state（从Redis或session中读取）
    # 简单实现暂时跳过state验证

    # 获取企业微信用户信息
    wework_info = await WeWorkService.get_user_info_by_code(callback_data.code)

    # 登录或创建用户
    return WeWorkService.login_or_create_user(db, wework_info)


@router.post(
    "/wework/bind", response_model=WeWorkBindResponse, summary="绑定企业微信账号"
)
async def bind_wework(
    bind_data: WeWorkBindRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    绑定企业微信账号到当前用户

    需要认证

    - **code**: 企业微信授权码

    用于已登录用户绑定企业微信账号，绑定后可以使用企业微信扫码登录
    """
    # 获取企业微信用户信息
    wework_info = await WeWorkService.get_user_info_by_code(bind_data.code)

    # 绑定企业微信账号
    updated_user = WeWorkService.bind_wework_to_user(db, current_user, wework_info)

    return WeWorkBindResponse(
        success=True,
        message="企业微信账号绑定成功",
        user=UserResponse.model_validate(updated_user),
    )


@router.post(
    "/wework/unbind", response_model=WeWorkUnbindResponse, summary="解绑企业微信账号"
)
async def unbind_wework(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    解绑企业微信账号

    需要认证

    注意：
    - 如果账号仅通过企业微信登录（没有设置密码），不允许解绑
    - 解绑后将无法使用企业微信扫码登录
    """
    # 解绑企业微信账号
    WeWorkService.unbind_wework_from_user(db, current_user)

    return WeWorkUnbindResponse(success=True, message="企业微信账号解绑成功")
