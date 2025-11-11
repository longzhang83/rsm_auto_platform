<template>
  <div id="userLayout" class="w-full h-full relative">
    <!-- 背景图片 -->
    <div class="fixed inset-0 w-full h-full" style="background-color: rgb(255, 255, 255);">
      <img src="/images/login_background.jpg" draggable="false" class="absolute inset-0 w-full h-full" style="width: 100%; height: 100vh;" alt="Background" />
    </div>

    <!-- 半透明遮罩 -->
    <div class="fixed inset-0 bg-black bg-opacity-30"></div>

    <!-- 注册表单容器 -->
    <div class="register-container">
      <div class="register-box">
      <div class="register-header">
        <img src="/images/logo.png" alt="Logo" class="logo" />
        <h1 class="title">用户注册</h1>
        <p class="subtitle">容诚税务师事务所 - 智能化自动化工具平台</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名（3-50个字符）"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="email">
          <div class="email-input-group">
            <el-input
              v-model="registerForm.email"
              placeholder="邮箱 (@rsmchina.com.cn;@rsmcn.cloud)"
              size="large"
              prefix-icon="Message"
              clearable
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
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码（至少6个字符）"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="register-button"
            :loading="loading"
            @click="handleRegister"
          >
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>

        <div class="login-link">
          已有账号？
          <router-link to="/login" class="link">立即登录</router-link>
        </div>
      </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const router = useRouter()
const authStore = useAuthStore()
const registerFormRef = ref(null)
const loading = ref(false)
const codeLoading = ref(false)
const codeCountdown = ref(0)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  verification_code: ''
})

// 验证确认密码
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 允许的邮箱域名列表
const allowedEmailDomains = ['rsmchina.com.cn', 'rsmcn.cloud']

// 自定义邮箱域名验证器
const validateEmailDomain = (rule, value, callback) => {
  if (!value) {
    callback()
    return
  }

  const emailPattern = /^[^\s@]+@([^\s@]+)$/
  const match = value.match(emailPattern)

  if (!match) {
    callback(new Error('请输入正确的邮箱地址'))
    return
  }

  const domain = match[1].toLowerCase()
  if (!allowedEmailDomains.includes(domain)) {
    const domainsText = allowedEmailDomains.join(' 或 ')
    callback(new Error(`邮箱域名必须为 ${domainsText}`))
    return
  }

  callback()
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] },
    {
      validator: validateEmailDomain,
      trigger: ['blur', 'change']
    }
  ],
  verification_code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 发送验证码
const sendVerificationCode = async () => {
  // 验证邮箱格式
  if (!registerForm.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }

  // 验证邮箱域名
  const emailPattern = /^[^\s@]+@([^\s@]+)$/
  const match = registerForm.email.match(emailPattern)

  if (!match) {
    ElMessage.error('请输入正确的邮箱地址')
    return
  }

  const domain = match[1].toLowerCase()
  if (!allowedEmailDomains.includes(domain)) {
    const domainsText = allowedEmailDomains.join(' 或 ')
    ElMessage.error(`邮箱域名必须为 ${domainsText}`)
    return
  }

  codeLoading.value = true
  try {
    const result = await request({
      url: '/auth/send-verification-code',
      method: 'post',
      data: {
        email: registerForm.email
      }
    })

    // request 函数直接返回响应数据
    if (result.success) {
      ElMessage.success(result.message)
      // 启动倒计时
      codeCountdown.value = 60
      const timer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送验证码失败，请稍后重试')
  } finally {
    codeLoading.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const success = await authStore.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
        verification_code: registerForm.verification_code
      })

      if (success) {
        // 注册成功，跳转到登录页
        setTimeout(() => {
          router.push('/login')
        }, 1500)
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.register-box {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  padding: 50px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  width: 120px;
  height: auto;
  margin-bottom: 20px;
  object-fit: contain;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 14px;
  color: #7f8c8d;
}

.register-form {
  margin-top: 30px;
}

.email-input-group {
  display: flex;
  gap: 10px;
  width: 100%;
}

.email-input-group :deep(.el-input) {
  flex: 1;
}

.send-code-btn {
  white-space: nowrap;
}

.register-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: #7f8c8d;
  font-size: 14px;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  color: #764ba2;
  text-decoration: underline;
}

@media (max-width: 576px) {
  .register-box {
    padding: 40px 30px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
