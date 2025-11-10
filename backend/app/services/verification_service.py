"""
验证码服务
"""
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import VerificationCode
from app.core.config import settings
from app.services.email_service import EmailService

import logging

logger = logging.getLogger(__name__)


class VerificationService:
    """验证码服务"""

    @staticmethod
    def generate_code(length: int = None) -> str:
        """
        生成随机数字验证码

        Args:
            length: 验证码长度

        Returns:
            随机验证码
        """
        if length is None:
            length = settings.verification_code_length

        # 生成纯数字验证码
        return ''.join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def validate_email_domain(email: str) -> bool:
        """
        验证邮箱域名是否在允许列表中

        Args:
            email: 邮箱地址

        Returns:
            是否允许
        """
        allowed_domains = [
            d.strip().lower()
            for d in settings.allowed_email_domains.split(',')
        ]

        if '@' not in email:
            return False

        domain = email.split('@')[1].lower()
        return domain in allowed_domains

    @staticmethod
    def send_code(db: Session, email: str, code_type: str = "register") -> tuple[bool, str]:
        """
        发送验证码到邮箱

        Args:
            db: 数据库会话
            email: 邮箱地址
            code_type: 验证码类型 (register/reset_password)

        Returns:
            (是否成功, 消息)
        """
        # 验证邮箱域名
        if not VerificationService.validate_email_domain(email):
            allowed_domains = settings.allowed_email_domains
            return False, f"邮箱域名必须为: {allowed_domains}"

        # 如果是密码重置，需要检查邮箱是否已注册
        if code_type == "reset_password":
            from app.db.models import User
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False, "该邮箱未注册"

        # 检查是否在1分钟内已发送过验证码
        recent_code = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.created_at > datetime.utcnow() - timedelta(minutes=1)
        ).order_by(VerificationCode.created_at.desc()).first()

        if recent_code and not recent_code.is_verified:
            return False, "请勿频繁发送验证码，请1分钟后再试"

        # 生成验证码
        code = VerificationService.generate_code()

        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(seconds=settings.verification_code_expiry)

        # 保存到数据库
        verification_code = VerificationCode(
            email=email,
            code=code,
            code_type=code_type,
            expires_at=expires_at
        )
        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)

        # 发送邮件
        if code_type == "reset_password":
            success = EmailService.send_reset_password_code(email, code)
        else:
            success = EmailService.send_verification_code(email, code)

        if success:
            logger.info(f"{code_type}验证码已发送至: {email}")
            return True, "验证码已发送至邮箱，请查收"
        else:
            logger.error(f"{code_type}验证码发送失败: {email}")
            # 删除已保存的验证码
            db.delete(verification_code)
            db.commit()
            return False, "验证码发送失败，请稍后重试"

    @staticmethod
    def verify_code(db: Session, email: str, code: str, code_type: str = "register") -> tuple[bool, str]:
        """
        验证邮箱验证码

        Args:
            db: 数据库会话
            email: 邮箱地址
            code: 用户输入的验证码
            code_type: 验证码类型 (register/reset_password)

        Returns:
            (是否成功, 消息)
        """
        # 查询最新的未验证码
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.is_verified == False
        ).order_by(VerificationCode.created_at.desc()).first()

        if not verification_code:
            return False, "请先发送验证码"

        # 检查是否过期
        if datetime.utcnow() > verification_code.expires_at:
            return False, "验证码已过期，请重新发送"

        # 检查尝试次数
        if verification_code.attempts >= 5:
            return False, "尝试次数过多，请重新发送验证码"

        # 验证码校验
        if verification_code.code != code:
            verification_code.attempts += 1
            db.commit()
            remaining = 5 - verification_code.attempts
            return False, f"验证码错误，还有{remaining}次尝试机会"

        # 标记为已验证
        verification_code.is_verified = True
        db.commit()

        logger.info(f"邮箱验证成功: {email}")
        return True, "验证成功"

    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """
        清理过期的验证码

        Args:
            db: 数据库会话

        Returns:
            删除的记录数
        """
        result = db.query(VerificationCode).filter(
            VerificationCode.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        logger.info(f"清理了{result}条过期的验证码")
        return result
