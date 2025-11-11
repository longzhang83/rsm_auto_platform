"""
认证服务
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.services.verification_service import VerificationService


class AuthService:
    """认证服务类"""

    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> UserResponse:
        """
        注册新用户

        Args:
            db: 数据库会话
            user_data: 用户数据

        Returns:
            创建的用户信息

        Raises:
            HTTPException: 用户名或邮箱已存在，或验证码错误
        """
        # 验证邮箱验证码
        success, message = VerificationService.verify_code(
            db, user_data.email, user_data.verification_code
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        # 检查用户名是否存在
        existing_user = (
            db.query(User).filter(User.username == user_data.username).first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
            )

        # 检查邮箱是否存在
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册"
            )

        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return UserResponse.model_validate(db_user)

    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> Token:
        """
        用户登录

        Args:
            db: 数据库会话
            login_data: 登录数据

        Returns:
            Token和用户信息

        Raises:
            HTTPException: 用户名或密码错误
        """
        # 查找用户
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建访问令牌
        access_token = create_access_token(data={"sub": user.username})

        return Token(access_token=access_token, user=UserResponse.model_validate(user))

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """
        通过用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户对象

        Raises:
            HTTPException: 用户不存在
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )
        return user

    @staticmethod
    def request_password_reset(
        db: Session, request_data: PasswordResetRequest
    ) -> PasswordResetResponse:
        """
        请求重置密码

        Args:
            db: 数据库会话
            request_data: 重置请求数据

        Returns:
            重置响应（包含token，仅用于开发环境）

        Raises:
            HTTPException: 邮箱不存在
        """
        # 查找用户，在生成验证码前先检验邮箱是否已注册
        user = db.query(User).filter(User.email == request_data.email).first()
        if not user:
            # 明确告知用户该邮箱未注册
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该邮箱未注册，请先注册账号",
            )

        # 生成重置token（验证码）
        reset_token = create_password_reset_token(user.email)

        # 在生产环境中，应该通过邮件发送reset_token
        # 这里为了开发方便，直接返回token
        return PasswordResetResponse(
            message="密码重置链接已生成",
            reset_token=reset_token,  # 仅用于开发，生产环境应该通过邮件发送
        )

    @staticmethod
    def reset_password(db: Session, reset_data: PasswordResetConfirm) -> dict:
        """
        重置密码

        Args:
            db: 数据库会话
            reset_data: 重置密码数据

        Returns:
            成功消息

        Raises:
            HTTPException: token无效或用户不存在
        """
        # 验证token
        email = verify_password_reset_token(reset_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置密码链接无效或已过期",
            )

        # 查找用户
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 更新密码
        user.hashed_password = get_password_hash(reset_data.new_password)
        db.commit()

        return {"message": "密码重置成功，请使用新密码登录"}

    @staticmethod
    def change_password(
        db: Session, user: User, change_data: ChangePasswordRequest
    ) -> ChangePasswordResponse:
        """
        修改密码

        Args:
            db: 数据库会话
            user: 当前用户
            change_data: 修改密码数据

        Returns:
            修改结果

        Raises:
            HTTPException: 当前密码错误
        """
        # 如果用户已有密码，需要验证当前密码
        if user.hashed_password:
            if not change_data.old_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="请输入当前密码"
                )

            # 验证当前密码
            if not verify_password(change_data.old_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误"
                )

        # 更新密码
        user.hashed_password = get_password_hash(change_data.new_password)
        db.commit()

        return ChangePasswordResponse(success=True, message="密码修改成功")
