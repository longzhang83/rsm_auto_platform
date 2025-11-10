<template>
  <div class="forgot-password-container">
    <div class="forgot-password-box">
      <div class="forgot-password-header">
        <img src="/images/logo.png" alt="Logo" class="logo" />
        <h1 class="title">忘记密码</h1>
        <p class="subtitle">容诚税务师事务所 - 智能化自动化工具平台</p>
      </div>

      <el-form
        ref="forgotPasswordFormRef"
        :model="forgotPasswordForm"
        :rules="forgotPasswordRules"
        class="forgot-password-form"
      >
        <el-form-item prop="email">
          <div class="email-input-group">
            <el-input
              v-model="forgotPasswordForm.email"
              placeholder="注册时使用的邮箱地址"
              size="large"
              prefix-icon="Message"
              clearable
            />
            <el-button
              type="primary"
              :disabled="!forgotPasswordForm.email || codeLoading || codeCountdown > 0"
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
            v-model="forgotPasswordForm.verification_code"
            placeholder="邮箱验证码"
            size="large"
            prefix-icon="Key"
            clearable
          />
        </el-form-item>

        <el-form-item prop="new_password">
          <el-input
            v-model="forgotPasswordForm.new_password"
            type="password"
            placeholder="新密码（至少6个字符）"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="confirm_password">
          <el-input
            v-model="forgotPasswordForm.confirm_password"
            type="password"
            placeholder="确认新密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleResetPassword"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="reset-button"
            :loading="loading"
            @click="handleResetPassword"
          >
            {{ loading ? '重置中...' : '重置密码' }}
          </el-button>
        </el-form-item>

        <div class="login-link">
          想起密码了？
          <router-link to="/login" class="link">返回登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const router = useRouter()
const forgotPasswordFormRef = ref(null)
const loading = ref(false)
const codeLoading = ref(false)
const codeCountdown = ref(0)

const forgotPasswordForm = reactive({
  email: '',
  verification_code: '',
  new_password: '',
  confirm_password: ''
})

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

// 验证确认密码
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== forgotPasswordForm.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const forgotPasswordRules = {
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
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 发送验证码
const sendVerificationCode = async () => {
  // 验证邮箱格式
  if (!forgotPasswordForm.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }

  // 验证邮箱域名
  const emailPattern = /^[^\s@]+@([^\s@]+)$/
  const match = forgotPasswordForm.email.match(emailPattern)

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
    const response = await request({
      url: '/auth/send-reset-password-code',
      method: 'post',
      data: {
        email: forgotPasswordForm.email
      }
    })

    // 响应数据在 response.data 中
    const result = response.data
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

const handleResetPassword = async () => {
  if (!forgotPasswordFormRef.value) return

  await forgotPasswordFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const response = await request({
        url: '/auth/reset-password',
        method: 'post',
        data: {
          email: forgotPasswordForm.email,
          verification_code: forgotPasswordForm.verification_code,
          new_password: forgotPasswordForm.new_password
        }
      })

      const result = response.data
      if (result.success) {
        ElMessage.success(result.message)
        // 密码重置成功，2秒后跳转到登录页
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      } else {
        ElMessage.error(result.message)
      }
    } catch (error) {
      console.error('密码重置失败:', error)
      ElMessage.error(error.response?.data?.detail || '密码重置失败，请稍后重试')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('/images/login_background.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 20px;
  position: relative;
}

.forgot-password-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 0;
}

.forgot-password-box {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  padding: 50px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.forgot-password-header {
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

.forgot-password-form {
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

.reset-button {
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
  .forgot-password-box {
    padding: 40px 30px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
