"""
企业微信OAuth认证服务
"""

import httpx
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models import User
from app.schemas.auth import UserResponse, Token
from app.utils.auth import create_access_token
from app.core.config import settings
import secrets
import logging

logger = logging.getLogger(__name__)


class WeWorkService:
    """企业微信认证服务类"""

    # 企业微信API配置
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    USER_INFO_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
    USER_DETAIL_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/get"

    # 缓存access_token（实际应用中应使用Redis等缓存服务）
    _access_token_cache: Optional[Dict[str, str]] = None

    @classmethod
    def is_enabled(cls) -> bool:
        """检查企业微信登录是否启用"""
        return (
            settings.wework_enabled
            and settings.wework_corp_id
            and settings.wework_agent_id
            and settings.wework_secret
        )

    @classmethod
    async def get_access_token(cls, force_refresh: bool = False) -> str:
        """
        获取企业微信access_token

        Args:
            force_refresh: 是否强制刷新token

        Returns:
            access_token字符串

        Raises:
            HTTPException: 获取token失败
        """
        if not cls.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="企业微信登录未启用或配置不完整",
            )

        # 检查缓存（简单实现，生产环境应使用Redis并检查过期时间）
        if not force_refresh and cls._access_token_cache:
            return cls._access_token_cache.get("access_token", "")

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "corpid": settings.wework_corp_id,
                    "corpsecret": settings.wework_secret,
                }
                response = await client.get(cls.TOKEN_URL, params=params, timeout=10.0)
                data = response.json()

                if data.get("errcode") == 0:
                    access_token = data["access_token"]
                    # 缓存token（实际应该根据expires_in设置过期时间）
                    cls._access_token_cache = {
                        "access_token": access_token,
                        "expires_in": data.get("expires_in", 7200),
                    }
                    logger.info("成功获取企业微信access_token")
                    return access_token
                else:
                    error_msg = data.get("errmsg", "未知错误")
                    logger.error(f"获取企业微信access_token失败: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"获取企业微信access_token失败: {error_msg}",
                    )
        except httpx.TimeoutException:
            logger.error("获取企业微信access_token超时")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="企业微信服务响应超时",
            )
        except Exception as e:
            logger.error(f"获取企业微信access_token异常: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"企业微信服务异常: {str(e)}",
            )

    @classmethod
    async def get_user_info_by_code(cls, code: str) -> Dict[str, any]:
        """
        根据OAuth code获取用户信息

        Args:
            code: 企业微信授权码

        Returns:
            用户信息字典

        Raises:
            HTTPException: 获取用户信息失败
        """
        access_token = await cls.get_access_token()

        try:
            async with httpx.AsyncClient() as client:
                # 1. 根据code获取userid
                params = {"access_token": access_token, "code": code}
                response = await client.get(
                    cls.USER_INFO_URL, params=params, timeout=10.0
                )
                data = response.json()

                if data.get("errcode") != 0:
                    error_msg = data.get("errmsg", "未知错误")
                    logger.error(f"获取企业微信用户信息失败: {error_msg}")

                    # 如果是token过期，尝试刷新token后重试一次
                    if data.get("errcode") in [40014, 42001]:
                        logger.info("access_token过期，尝试刷新")
                        access_token = await cls.get_access_token(force_refresh=True)
                        params["access_token"] = access_token
                        response = await client.get(
                            cls.USER_INFO_URL, params=params, timeout=10.0
                        )
                        data = response.json()

                        if data.get("errcode") != 0:
                            error_msg = data.get("errmsg", "未知错误")
                            raise HTTPException(
                                status_code=status.HTTP_502_BAD_GATEWAY,
                                detail=f"获取用户信息失败: {error_msg}",
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"获取用户信息失败: {error_msg}",
                        )

                userid = data.get("UserId") or data.get("userid")
                if not userid:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="未获取到用户ID",
                    )

                # 2. 获取用户详细信息
                detail_params = {"access_token": access_token, "userid": userid}
                detail_response = await client.get(
                    cls.USER_DETAIL_URL, params=detail_params, timeout=10.0
                )
                detail_data = detail_response.json()

                if detail_data.get("errcode") != 0:
                    # 如果获取详细信息失败，至少返回基本信息
                    logger.warning(
                        f"获取用户详细信息失败: {detail_data.get('errmsg')}, 使用基本信息"
                    )
                    return {
                        "userid": userid,
                        "name": userid,  # 使用userid作为默认名称
                        "email": None,
                        "avatar": None,
                        "department": None,
                    }

                logger.info(f"成功获取企业微信用户信息: {userid}")
                return {
                    "userid": userid,
                    "name": detail_data.get("name") or userid,
                    "email": detail_data.get("email") or detail_data.get("biz_mail"),
                    "avatar": detail_data.get("avatar"),
                    "department": ",".join(
                        map(str, detail_data.get("department", []))
                    ),  # 部门ID列表转字符串
                }

        except httpx.TimeoutException:
            logger.error("获取企业微信用户信息超时")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="企业微信服务响应超时",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取企业微信用户信息异常: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"企业微信服务异常: {str(e)}",
            )

    @classmethod
    def login_or_create_user(cls, db: Session, wework_info: Dict[str, any]) -> Token:
        """
        企业微信登录或创建用户

        场景：
        1. 如果wework_userid已绑定，直接登录
        2. 尝试用户名匹配（企业微信name与注册username匹配）
        3. 尝试邮箱用户名部分匹配（例如：zhanglong@wework.local 和 zhanglong@rsmchina.com.cn）
        4. 否则创建新用户

        Args:
            db: 数据库会话
            wework_info: 企业微信用户信息

        Returns:
            Token和用户信息

        Raises:
            HTTPException: 登录或创建失败
        """
        userid = wework_info.get("userid")
        name = wework_info.get("name")
        email = wework_info.get("email")
        avatar = wework_info.get("avatar")
        department = wework_info.get("department")

        # 1. 检查是否已通过wework_userid绑定
        user = db.query(User).filter(User.wework_userid == userid).first()
        if user:
            logger.info(f"企业微信用户已绑定: {userid} -> {user.username}")
            # 更新企业微信信息（可能有变化）
            user.wework_name = name
            user.wework_avatar = avatar
            user.wework_department = department
            # 保留原有登录方式，支持双登录
            db.commit()
            db.refresh(user)

            # 创建JWT token
            access_token = create_access_token(data={"sub": user.username})
            return Token(
                access_token=access_token, user=UserResponse.model_validate(user)
            )

        # 2. 尝试通过用户名匹配（如果企业微信名称与已有用户名完全匹配）
        # 优先使用姓名匹配，因为这是最可靠的方式
        if name:
            existing_user = db.query(User).filter(User.username == name).first()
            if existing_user and not existing_user.wework_userid:
                logger.info(f"自动绑定企业微信账号到已有用户（用户名匹配）: {name}")
                existing_user.wework_userid = userid
                existing_user.wework_name = name
                existing_user.wework_avatar = avatar
                existing_user.wework_department = department
                # 保留原有登录方式，支持双登录
                db.commit()
                db.refresh(existing_user)

                access_token = create_access_token(data={"sub": existing_user.username})
                return Token(
                    access_token=access_token,
                    user=UserResponse.model_validate(existing_user),
                )

        # 3. 尝试通过邮箱用户名部分匹配
        # 例如：zhanglong@wework.local 和 zhanglong@rsmchina.com.cn 可以匹配
        if email and "@" in email:
            email_username = email.split("@")[0]  # 提取@前面的部分
            # 查询所有用户，检查邮箱用户名部分是否匹配
            all_users = db.query(User).filter(User.wework_userid.is_(None)).all()
            for existing_user in all_users:
                if existing_user.email and "@" in existing_user.email:
                    existing_email_username = existing_user.email.split("@")[0]
                    if email_username == existing_email_username:
                        logger.info(
                            f"自动绑定企业微信账号到已有用户（邮箱用户名匹配）: {email_username} ({email} -> {existing_user.email})"
                        )
                        existing_user.wework_userid = userid
                        existing_user.wework_name = name
                        existing_user.wework_avatar = avatar
                        existing_user.wework_department = department
                        # 保留原有登录方式，支持双登录
                        db.commit()
                        db.refresh(existing_user)

                        access_token = create_access_token(data={"sub": existing_user.username})
                        return Token(
                            access_token=access_token,
                            user=UserResponse.model_validate(existing_user),
                        )

        # 4. 创建新用户
        # 生成唯一用户名（基于企业微信名称或userid）
        base_username = name or userid
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1

        # 生成默认邮箱（如果企业微信没有提供）
        if not email:
            email = f"{userid}@wework.local"
            # 确保邮箱唯一
            counter = 1
            while db.query(User).filter(User.email == email).first():
                email = f"{userid}{counter}@wework.local"
                counter += 1

        logger.info(f"创建新的企业微信用户: {username}")
        new_user = User(
            username=username,
            email=email,
            hashed_password=None,  # 企业微信登录不需要密码
            wework_userid=userid,
            wework_name=name,
            wework_avatar=avatar,
            wework_department=department,
            login_type="wework",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 创建JWT token
        access_token = create_access_token(data={"sub": new_user.username})
        return Token(access_token=access_token, user=UserResponse.model_validate(new_user))

    @classmethod
    def bind_wework_to_user(
        cls, db: Session, user: User, wework_info: Dict[str, any]
    ) -> User:
        """
        绑定企业微信账号到现有用户

        Args:
            db: 数据库会话
            user: 当前登录用户
            wework_info: 企业微信用户信息

        Returns:
            更新后的用户对象

        Raises:
            HTTPException: 绑定失败（如wework_userid已被其他用户绑定）
        """
        userid = wework_info.get("userid")

        # 检查wework_userid是否已被其他用户绑定
        existing_user = db.query(User).filter(User.wework_userid == userid).first()
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该企业微信账号已被其他用户绑定",
            )

        # 绑定企业微信信息
        user.wework_userid = userid
        user.wework_name = wework_info.get("name")
        user.wework_avatar = wework_info.get("avatar")
        user.wework_department = wework_info.get("department")
        db.commit()
        db.refresh(user)

        logger.info(f"成功绑定企业微信账号: {user.username} -> {userid}")
        return user

    @classmethod
    def unbind_wework_from_user(cls, db: Session, user: User) -> User:
        """
        解绑企业微信账号

        Args:
            db: 数据库会话
            user: 当前登录用户

        Returns:
            更新后的用户对象

        Raises:
            HTTPException: 解绑失败
        """
        if not user.wework_userid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="当前账号未绑定企业微信"
            )

        # 检查是否有密码（如果是纯企业微信账号，不允许解绑）
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该账号仅通过企业微信登录，不能解绑。请先设置密码",
            )

        # 解绑企业微信信息
        user.wework_userid = None
        user.wework_name = None
        user.wework_avatar = None
        user.wework_department = None
        user.login_type = "password"
        db.commit()
        db.refresh(user)

        logger.info(f"成功解绑企业微信账号: {user.username}")
        return user

    @staticmethod
    def generate_state() -> str:
        """
        生成随机state字符串用于OAuth验证

        Returns:
            32字符的随机字符串
        """
        return secrets.token_urlsafe(32)
