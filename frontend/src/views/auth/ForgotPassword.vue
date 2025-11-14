<template>
  <div id="userLayout" class="w-full h-full relative">
    <!-- 背景图片 -->
    <div class="fixed inset-0 w-full h-full" style="background-color: rgb(255, 255, 255);">
      <img src="/images/login_background.jpg" draggable="false" class="absolute inset-0 w-full h-full" style="width: 100%; height: 100vh;" alt="Background" />
    </div>

    <!-- 半透明遮罩 -->
    <div class="fixed inset-0 bg-black bg-opacity-30"></div>

    <!-- 忘记密码表单容器 -->
    <div class="login-container">
      <div class="login-box">
      <div class="login-header">
        <img src="/images/logo.png" alt="Logo" class="logo" />
        <h1 class="title">忘记密码</h1>
        <p class="subtitle">输入您的注册邮箱，我们将发送重置密码链接</p>
      </div>

      <!-- 成功提示 -->
      <el-alert
        v-if="resetSent"
        type="success"
        :closable="false"
        class="success-alert"
      >
        <template #title>
          <div class="alert-content">
            <p class="alert-title">重置链接已生成</p>
            <p class="alert-message">{{ successMessage }}</p>

            <!-- 开发环境显示token -->
            <div v-if="resetToken" class="token-box">
              <p class="token-label">开发环境 - 重置Token:</p>
              <p class="token-value">{{ resetToken }}</p>
              <el-button
                size="small"
                type="success"
                text
                @click="copyToken"
              >
                复制Token
              </el-button>
            </div>

            <el-button
              type="success"
              text
              class="reset-link"
              @click="goToResetPassword"
            >
              前往重置密码页面 →
            </el-button>
          </div>
        </template>
      </el-alert>

      <!-- 表单 -->
      <el-form
        v-else
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        class="login-form"
        @keyup.enter="handleSubmit"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            placeholder="请输入注册邮箱"
            size="large"
            prefix-icon="Message"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ loading ? '发送中...' : '发送重置链接' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 返回登录 -->
      <div class="register-link">
        <router-link to="/login" class="link">← 返回登录</router-link>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { forgotPassword } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const forgotFormRef = ref(null)
const loading = ref(false)
const resetSent = ref(false)
const successMessage = ref('')
const resetToken = ref('')

const forgotForm = reactive({
  email: ''
})

const forgotRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!forgotFormRef.value) return

  try {
    // 验证表单
    await forgotFormRef.value.validate()

    loading.value = true
    try {
      const response = await forgotPassword({ email: forgotForm.email })
      resetSent.value = true
      successMessage.value = response.message || '重置链接已发送到您的邮箱'
      resetToken.value = response.reset_token || ''
    } catch (error) {
      console.error('发送重置链接失败:', error)
      ElMessage.error(error.response?.data?.detail || '发送失败，请稍后重试')
    } finally {
      loading.value = false
    }
  } catch (error) {
    // 表单验证失败，不做任何操作（Element Plus 会自动显示错误信息）
    console.log('表单验证失败:', error)
  }
}

const copyToken = () => {
  navigator.clipboard.writeText(resetToken.value)
  ElMessage.success('Token已复制到剪贴板')
}

const goToResetPassword = () => {
  if (resetToken.value) {
    router.push(`/reset-password?token=${resetToken.value}`)
  } else {
    router.push('/reset-password')
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.login-box {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  padding: 50px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.login-header {
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
  line-height: 1.6;
}

.login-form {
  margin-top: 30px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  color: #7f8c8d;
  font-size: 14px;
}

.link {
  color: var(--brand-primary);
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  color: var(--brand-primary-dark);
  text-decoration: underline;
}

.success-alert {
  margin-bottom: 20px;
}

.alert-content {
  width: 100%;
}

.alert-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 8px;
}

.alert-message {
  font-size: 14px;
  color: var(--brand-success);
  margin-bottom: 12px;
}

.token-box {
  margin-top: 16px;
  padding: 12px;
  background: var(--primary-50);
  border: 1px solid var(--brand-success);
  border-radius: 8px;
}

.token-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.token-value {
  font-size: 12px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
  color: #2c3e50;
  margin-bottom: 8px;
  line-height: 1.5;
}

.reset-link {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 576px) {
  .login-box {
    padding: 40px 30px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
