# 企业微信扫码登录设计文档

## 1. 技术方案

### 1.1 企业微信OAuth2.0登录流程

```
用户 → 前端页面 → 显示企业微信二维码
  ↓
用户扫码 → 企业微信授权
  ↓
企业微信回调 → 后端接收code
  ↓
后端用code换取access_token
  ↓
后端用access_token获取用户信息
  ↓
创建/绑定用户账号 → 返回JWT token
  ↓
前端存储token → 登录成功
```

### 1.2 需要的企业微信配置

- **CorpID**: 企业ID
- **AgentID**: 应用ID（自建应用）
- **Secret**: 应用密钥
- **回调域名**: 授权后的回调URL

## 2. 数据库设计

### 2.1 扩展User表

添加企业微信相关字段：

```sql
ALTER TABLE users ADD COLUMN wework_userid VARCHAR(100) UNIQUE;
ALTER TABLE users ADD COLUMN wework_name VARCHAR(100);
ALTER TABLE users ADD COLUMN wework_avatar VARCHAR(500);
ALTER TABLE users ADD COLUMN wework_department VARCHAR(200);
ALTER TABLE users ADD COLUMN login_type VARCHAR(20) DEFAULT 'password';
```

**字段说明**：
- `wework_userid`: 企业微信用户ID（唯一标识）
- `wework_name`: 企业微信用户名
- `wework_avatar`: 企业微信头像URL
- `wework_department`: 所属部门
- `login_type`: 登录方式（password/wework）

### 2.2 新增WeWorkConfig表（可选）

存储企业微信应用配置：

```sql
CREATE TABLE wework_configs (
    id INTEGER PRIMARY KEY,
    corp_id VARCHAR(100) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    secret VARCHAR(200) NOT NULL,
    callback_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 3. 后端API设计

### 3.1 配置管理

**环境变量** (`.env`):
```bash
# 企业微信配置
WEWORK_CORP_ID=your_corp_id
WEWORK_AGENT_ID=your_agent_id
WEWORK_SECRET=your_secret
WEWORK_CALLBACK_URL=http://localhost:3000/auth/wework/callback
```

### 3.2 API接口

#### 3.2.1 获取企业微信二维码配置
```
GET /api/v1/auth/wework/config
Response:
{
  "corp_id": "wwxxxx",
  "agent_id": "1000002",
  "redirect_uri": "http://localhost:3000/auth/wework/callback",
  "state": "random_state_string"
}
```

#### 3.2.2 企业微信授权回调
```
POST /api/v1/auth/wework/callback
Request:
{
  "code": "authorization_code",
  "state": "random_state_string"
}

Response:
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@company.com",
    "wework_name": "张三",
    "login_type": "wework"
  }
}
```

#### 3.2.3 企业微信账号绑定
```
POST /api/v1/auth/wework/bind
Headers: Authorization: Bearer <jwt_token>
Request:
{
  "code": "authorization_code"
}

Response:
{
  "success": true,
  "message": "企业微信账号绑定成功",
  "user": {
    "id": 1,
    "wework_userid": "zhangsan",
    "wework_name": "张三"
  }
}
```

#### 3.2.4 解绑企业微信账号
```
POST /api/v1/auth/wework/unbind
Headers: Authorization: Bearer <jwt_token>

Response:
{
  "success": true,
  "message": "企业微信账号解绑成功"
}
```

## 4. 前端实现

### 4.1 企业微信二维码组件

**位置**: `frontend/src/components/WeWorkLogin.vue`

```vue
<template>
  <div class="wework-login">
    <div id="wework-qr-container"></div>
    <p>使用企业微信扫码登录</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(async () => {
  // 获取企业微信配置
  const config = await fetch('/api/v1/auth/wework/config').then(r => r.json())

  // 生成二维码
  const WwLogin = window.WwLogin
  if (WwLogin) {
    new WwLogin({
      id: 'wework-qr-container',
      appid: config.corp_id,
      agentid: config.agent_id,
      redirect_uri: encodeURIComponent(config.redirect_uri),
      state: config.state,
      href: '' // 自定义样式CSS
    })
  }
})
</script>
```

### 4.2 登录页面集成

**修改**: `frontend/src/views/login/index.vue`

添加企业微信登录选项：

```vue
<template>
  <div class="login-container">
    <!-- 原有的用户名密码登录 -->
    <div class="password-login">
      <!-- ... -->
    </div>

    <!-- 分隔线 -->
    <div class="divider">或</div>

    <!-- 企业微信扫码登录 -->
    <WeWorkLogin />
  </div>
</template>
```

### 4.3 回调处理页面

**位置**: `frontend/src/views/auth/wework-callback.vue`

```vue
<template>
  <div class="callback-loading">
    <div class="spinner"></div>
    <p>正在登录...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { setToken } from '@/api/request'

const router = useRouter()

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  const state = urlParams.get('state')

  if (code) {
    try {
      const response = await fetch('/api/v1/auth/wework/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, state })
      })

      const data = await response.json()

      if (response.ok) {
        setToken(data.access_token)
        router.push('/dashboard')
      } else {
        router.push('/login?error=wework_failed')
      }
    } catch (error) {
      console.error('企业微信登录失败:', error)
      router.push('/login?error=wework_error')
    }
  }
})
</script>
```

## 5. 企业微信API封装

### 5.1 获取access_token

```python
async def get_wework_access_token(corp_id: str, secret: str) -> str:
    """获取企业微信access_token"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {
        "corpid": corp_id,
        "corpsecret": secret
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("errcode") == 0:
            return data["access_token"]
        else:
            raise Exception(f"获取access_token失败: {data.get('errmsg')}")
```

### 5.2 获取用户信息

```python
async def get_wework_user_info(access_token: str, code: str) -> dict:
    """根据code获取用户信息"""
    # 1. 获取userid
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
    params = {
        "access_token": access_token,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

        if data.get("errcode") != 0:
            raise Exception(f"获取用户信息失败: {data.get('errmsg')}")

        userid = data.get("UserId")

        # 2. 获取详细信息
        detail_url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        detail_params = {
            "access_token": access_token,
            "userid": userid
        }

        detail_response = await client.get(detail_url, params=detail_params)
        detail_data = detail_response.json()

        return {
            "userid": userid,
            "name": detail_data.get("name"),
            "avatar": detail_data.get("avatar"),
            "email": detail_data.get("email"),
            "department": detail_data.get("department")
        }
```

## 6. 安全考虑

### 6.1 State参数验证

- 生成随机state字符串
- 缓存state到Redis（5分钟过期）
- 回调时验证state是否匹配

### 6.2 Token缓存

- access_token缓存到Redis（2小时过期）
- 避免频繁调用企业微信API

### 6.3 账号绑定策略

**场景1**: 企业微信用户首次登录
- 检查是否有相同email的账号
- 如果有，提示绑定
- 如果没有，自动创建新账号

**场景2**: 已登录用户绑定企业微信
- 验证JWT token
- 绑定wework_userid到当前用户

**场景3**: 企业微信用户已绑定
- 直接登录，返回JWT token

## 7. 配置步骤

### 7.1 企业微信后台配置

1. 登录企业微信管理后台
2. 创建自建应用
3. 配置可信域名和回调URL
4. 获取 CorpID、AgentID、Secret

### 7.2 应用配置

1. 在 `.env` 文件中添加企业微信配置
2. 重启后端服务
3. 访问登录页面测试

## 8. 测试计划

### 8.1 功能测试

- [ ] 显示企业微信二维码
- [ ] 扫码后正确跳转
- [ ] 首次登录自动创建账号
- [ ] 已绑定账号直接登录
- [ ] 账号绑定功能
- [ ] 账号解绑功能

### 8.2 异常测试

- [ ] 无效code处理
- [ ] state验证失败
- [ ] 企业微信API调用失败
- [ ] Token过期处理

## 9. 优化建议

### 9.1 性能优化

- 使用Redis缓存access_token
- 异步处理企业微信API调用
- 二维码懒加载

### 9.2 用户体验

- 添加加载动画
- 错误提示友好化
- 支持手机端扫码
- 记住登录状态

## 10. 参考文档

- [企业微信网页授权登录](https://developer.work.weixin.qq.com/document/path/91335)
- [企业微信API文档](https://developer.work.weixin.qq.com/document/path/90664)
