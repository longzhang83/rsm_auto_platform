"""
认证服务
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # 检查用户名是否存在
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否存在
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
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

        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
