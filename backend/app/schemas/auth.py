"""
认证相关的Pydantic模型
"""

from pydantic import BaseModel, EmailStr, Field, computed_field, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")  # 改为2以支持中文名
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """用户注册模型"""

    password: str = Field(..., min_length=6, max_length=100, description="密码")
    verification_code: str = Field(..., description="邮箱验证码")


class UserLogin(BaseModel):
    """用户登录模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型 - 不继承UserBase以允许更灵活的验证"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")  # 使用str而非EmailStr，允许内部域名
    created_at: datetime
    wework_userid: Optional[str] = None
    wework_name: Optional[str] = None
    wework_avatar: Optional[str] = None
    wework_department: Optional[str] = None
    login_type: str = "password"
    is_admin: bool = False
    hashed_password: Optional[str] = Field(None, exclude=True)  # 从数据库读取，但不输出到JSON

    @computed_field
    @property
    def has_password(self) -> bool:
        """计算属性：用户是否设置了密码"""
        return self.hashed_password is not None and self.hashed_password != ""


class Token(BaseModel):
    """Token响应模型"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token数据模型"""

    username: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """请求重置密码模型"""

    email: EmailStr = Field(..., description="注册邮箱地址")


class PasswordResetConfirm(BaseModel):
    """确认重置密码模型"""

    token: str = Field(..., description="重置密码token")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class PasswordResetResponse(BaseModel):
    """重置密码响应模型"""

    message: str
    reset_token: Optional[str] = None  # 仅用于开发环境，生产环境应通过邮件发送


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""

    old_password: Optional[str] = Field(None, description="当前密码（如果有）")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class ChangePasswordResponse(BaseModel):
    """修改密码响应模型"""

    success: bool = Field(..., description="是否修改成功")
    message: str = Field(..., description="提示消息")


class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求模型"""

    email: EmailStr = Field(..., description="邮箱地址")


class SendVerificationCodeResponse(BaseModel):
    """发送验证码响应模型"""

    success: bool = Field(..., description="是否发送成功")
    message: str = Field(..., description="提示消息")


# 企业微信相关模型


class WeWorkConfigResponse(BaseModel):
    """企业微信配置响应模型"""

    corp_id: str = Field(..., description="企业ID")
    agent_id: str = Field(..., description="应用ID")
    redirect_uri: str = Field(..., description="回调URL")
    state: str = Field(..., description="随机state字符串")
    enabled: bool = Field(..., description="是否启用企业微信登录")


class WeWorkCallbackRequest(BaseModel):
    """企业微信回调请求模型"""

    code: str = Field(..., description="授权码")
    state: str = Field(..., description="State字符串")


class WeWorkBindRequest(BaseModel):
    """绑定企业微信账号请求模型"""

    code: str = Field(..., description="授权码")


class WeWorkBindResponse(BaseModel):
    """绑定企业微信账号响应模型"""

    success: bool = Field(..., description="是否绑定成功")
    message: str = Field(..., description="提示消息")
    user: Optional[UserResponse] = Field(None, description="用户信息")


class WeWorkUnbindResponse(BaseModel):
    """解绑企业微信账号响应模型"""

    success: bool = Field(..., description="是否解绑成功")
    message: str = Field(..., description="提示消息")
