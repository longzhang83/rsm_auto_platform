# 邮箱验证码注册功能

## 功能概述

实现了基于邮箱验证码的用户注册流程。用户注册时需要：
1. 使用 `rsmchina.com.cn` 域名的邮箱
2. 点击"获取验证码"按钮
3. 输入收到的验证码
4. 完成注册

## 后端实现

### 1. 配置 (`backend/app/core/config.py`)

添加了邮件和验证码相关的配置：

```python
# 邮件配置
smtp_server: str = "smtp.qq.com"          # SMTP服务器
smtp_port: int = 587                      # SMTP端口
smtp_username: Optional[str] = None       # 发件人邮箱
smtp_password: Optional[str] = None       # 邮箱授权码
email_from_name: str = "容诚税务师事务所" # 发件人名称

# 邮箱注册配置
allowed_email_domains: str = "rsmchina.com.cn"  # 允许的邮箱域名
verification_code_expiry: int = 300            # 验证码有效期（秒），默认5分钟
verification_code_length: int = 6              # 验证码长度
```

**配置方法**：在项目根目录的 `.env` 文件中设置：

```bash
# =============================================================================
# 邮箱服务器配置（用于发送验证码）
# =============================================================================

# SMTP服务器地址
SMTP_SERVER=smtp.qq.com

# SMTP服务器端口（587: STARTTLS加密，推荐）
SMTP_PORT=587

# SMTP用户名（发件人邮箱地址）
SMTP_USERNAME=your-email@qq.com

# SMTP密码或授权码（QQ邮箱需要使用授权码）
SMTP_PASSWORD=your-authorization-code

# 发件人显示名称
EMAIL_FROM_NAME=容诚税务师事务所

# =============================================================================
# 邮箱验证码配置
# =============================================================================

# 允许注册的邮箱域名（多个域名用逗号分隔）
ALLOWED_EMAIL_DOMAINS=rsmchina.com.cn

# 验证码有效期（秒），默认5分钟
VERIFICATION_CODE_EXPIRY=300

# 验证码长度（数字位数）
VERIFICATION_CODE_LENGTH=6
```

**如何获取QQ邮箱授权码**：
1. 登录 [QQ邮箱](https://mail.qq.com) → 设置 → 账户
2. 找到 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
3. 开启 "IMAP/SMTP服务"
4. 点击 "生成授权码"，按提示完成验证
5. 将生成的授权码填入 `SMTP_PASSWORD` 配置项

**其他邮箱服务器配置**：
- **163邮箱**: `SMTP_SERVER=smtp.163.com`, `SMTP_PORT=465`（SSL）或 `587`（STARTTLS）
- **Gmail**: `SMTP_SERVER=smtp.gmail.com`, `SMTP_PORT=587`
- **企业邮箱**: 根据企业邮箱服务商提供的SMTP配置

### 2. 数据库模型 (`backend/app/db/models.py`)

添加了 `VerificationCode` 模型：

```python
class VerificationCode(Base):
    """邮箱验证码模型"""
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    is_verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)           # 验证尝试次数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
```

### 3. 邮件服务 (`backend/app/services/email_service.py`)

实现了通过SMTP发送验证码邮件的功能：

```python
class EmailService:
    @staticmethod
    def send_verification_code(email: str, code: str) -> bool:
        """发送验证码邮件"""
```

**特性**：
- 支持HTML格式邮件
- 美观的邮件模板
- 5分钟有效期提示
- 自动日志记录
- 如果SMTP未配置，验证码会输出到后端日志（开发模式）

### 4. 验证码服务 (`backend/app/services/verification_service.py`)

管理验证码的生成、发送和验证：

```python
class VerificationService:
    @staticmethod
    def generate_code(length: int = None) -> str:
        """生成随机数字验证码"""

    @staticmethod
    def validate_email_domain(email: str) -> bool:
        """验证邮箱域名是否在允许列表"""

    @staticmethod
    def send_code(db: Session, email: str) -> tuple[bool, str]:
        """发送验证码"""

    @staticmethod
    def verify_code(db: Session, email: str, code: str) -> tuple[bool, str]:
        """验证验证码"""

    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """清理过期验证码"""
```

**验证码发送规则**：
- ✅ 邮箱域名必须是允许列表中的域名
- ✅ 最多5分钟内发送一次（防止频繁发送）
- ✅ 验证码有效期5分钟
- ✅ 最多允许5次验证尝试

### 5. API端点 (`backend/app/api/v1/endpoints/auth.py`)

新增了验证码相关的API：

#### 发送验证码
```
POST /api/v1/auth/send-verification-code
Content-Type: application/json

{
  "email": "user@rsmchina.com.cn"
}

Response:
{
  "success": true,
  "message": "验证码已发送至邮箱，请查收"
}
```

#### 用户注册 (修改)
```
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john",
  "email": "john@rsmchina.com.cn",
  "password": "password123",
  "verification_code": "123456"
}

Response:
{
  "id": 1,
  "username": "john",
  "email": "john@rsmchina.com.cn",
  "created_at": "2024-11-10T..."
}
```

### 6. Schema 更新 (`backend/app/schemas/auth.py`)

新增了验证码相关的Pydantic模型：

```python
class SendVerificationCodeRequest(BaseModel):
    email: EmailStr

class SendVerificationCodeResponse(BaseModel):
    success: bool
    message: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str
```

## 前端实现

### 1. 注册页面 (`frontend/src/views/auth/Register.vue`)

#### 新增字段
- 邮箱输入框右侧添加"获取验证码"按钮
- 新增验证码输入框

#### 功能特性
- **倒计时**: 点击"获取验证码"后，按钮显示60秒倒计时
- **邮箱格式校验**: 强制使用 `@rsmchina.com.cn` 域名
- **验证码校验**: 验证码必须为6位数字
- **加载状态**: 发送验证码时显示加载状态，防止重复点击

#### 代码示例
```vue
<template>
  <el-form-item prop="email">
    <div class="email-input-group">
      <el-input
        v-model="registerForm.email"
        placeholder="邮箱地址（@rsmchina.com.cn）"
        size="large"
        prefix-icon="Message"
      />
      <el-button
        type="primary"
        :disabled="!registerForm.email || codeLoading || codeCountdown > 0"
        :loading="codeLoading"
        @click="sendVerificationCode"
        class="send-code-btn"
      >
        {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
      </el-button>
    </div>
  </el-form-item>

  <el-form-item prop="verification_code">
    <el-input
      v-model="registerForm.verification_code"
      placeholder="邮箱验证码"
      size="large"
      prefix-icon="Key"
    />
  </el-form-item>
</template>
```

### 2. 验证规则

```javascript
registerRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] },
    {
      pattern: /@rsmchina\.com\.cn$/,
      message: '邮箱必须为 rsmchina.com.cn 域名',
      trigger: ['blur', 'change']
    }
  ],
  verification_code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' }
  ]
}
```

## 使用流程

### 用户端
1. 打开注册页面
2. 输入用户名、邮箱（必须是 @rsmchina.com.cn）
3. 点击"获取验证码"
4. 等待邮件（通常秒级到达）
5. 输入收到的6位验证码
6. 输入密码并确认
7. 点击"注册"

### 配置端 (管理员)
1. 配置 SMTP 服务器信息（.env 文件）
2. （可选）修改允许的邮箱域名
3. （可选）修改验证码有效期

## 开发模式使用

如果未配置SMTP，验证码会输出到后端日志：

```
2024-11-10 19:00:00,000 - app.services.email_service - INFO - [开发模式] 验证码: 123456
```

可以从日志中查看验证码来完成注册测试。

## API 测试

### 使用 Postman 或 curl 测试

#### 1. 发送验证码
```bash
curl -X POST http://localhost:8888/api/v1/auth/send-verification-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@rsmchina.com.cn"}'
```

#### 2. 注册
```bash
curl -X POST http://localhost:8888/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser",
    "email":"test@rsmchina.com.cn",
    "password":"password123",
    "verification_code":"123456"
  }'
```

## 错误处理

### 常见错误消息

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| "邮箱域名必须为: rsmchina.com.cn" | 邮箱域名不符合 | 使用正确的邮箱域名 |
| "请勿频繁发送验证码，请1分钟后再试" | 发送过于频繁 | 等待1分钟后重试 |
| "验证码已过期，请重新发送" | 验证码超过5分钟 | 重新发送验证码 |
| "验证码错误，还有X次尝试机会" | 验证码输入错误 | 检查验证码并重试 |
| "尝试次数过多，请重新发送验证码" | 尝试超过5次 | 重新发送验证码 |

## 安全特性

✅ **域名白名单**: 仅允许特定域名邮箱注册
✅ **速率限制**: 防止验证码滥用（1分钟1次）
✅ **尝试限制**: 最多5次验证尝试
✅ **过期机制**: 验证码5分钟自动过期
✅ **数据库存储**: 所有验证记录可追踪
✅ **邮件验证**: 真实邮箱验证，防止虚假注册

## 扩展建议

1. **短信验证**: 可扩展为支持短信验证码
2. **多域名支持**: 轻松支持多个邮箱域名
3. **邮件模板**: 可自定义邮件内容和样式
4. **统计分析**: 记录验证码发送和使用统计
5. **国际化**: 支持多语言邮件内容

## 文件清单

### 后端
- `backend/app/core/config.py` - 添加SMTP配置
- `backend/app/db/models.py` - 添加VerificationCode模型
- `backend/app/services/email_service.py` - 新增邮件服务
- `backend/app/services/verification_service.py` - 新增验证码服务
- `backend/app/services/auth_service.py` - 修改注册逻辑
- `backend/app/api/v1/endpoints/auth.py` - 添加验证码API
- `backend/app/schemas/auth.py` - 添加验证码Schema

### 前端
- `frontend/src/views/auth/Register.vue` - 修改注册页面

## 相关文档

- [配置指南](./CONFIG.md)
- [API文档](./API.md)
- [开发指南](./DEVELOPMENT.md)
