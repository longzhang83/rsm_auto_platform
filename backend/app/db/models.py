"""
数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # 企业微信登录时可为空

    # 企业微信相关字段
    wework_userid = Column(String(100), unique=True, index=True, nullable=True)
    wework_name = Column(String(100), nullable=True)
    wework_avatar = Column(String(500), nullable=True)
    wework_department = Column(String(200), nullable=True)
    login_type = Column(String(20), default="password", nullable=False)  # password/wework

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, login_type={self.login_type})>"


class VerificationCode(Base):
    """邮箱验证码模型"""

    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    code_type = Column(
        String(20), default="register", nullable=False
    )  # register 或 reset_password
    is_verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)  # 验证尝试次数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<VerificationCode(email={self.email}, type={self.code_type}, verified={self.is_verified})>"


class ProcessRecord(Base):
    """处理记录模型 - 存储Dashboard处理记录"""

    __tablename__ = "process_records"

    id = Column(String(36), primary_key=True)  # UUID
    tool = Column(
        String(50), nullable=False, index=True
    )  # 工具名称：费用清单转凭证/摘要翻译/银行流水转凭证
    file_name = Column(String(255), nullable=False)  # 文件名
    status = Column(String(20), nullable=False, index=True)  # 状态：成功/失败/处理中
    duration = Column(Float, nullable=False)  # 处理时长（秒）
    record_count = Column(Integer, default=0)  # 处理记录条数
    user_id = Column(Integer, index=True, nullable=True)  # 关联用户ID（可选）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProcessRecord(id={self.id}, tool={self.tool}, status={self.status})>"
