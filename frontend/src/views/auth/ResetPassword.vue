<template>
  <div id="userLayout" class="w-full h-full relative">
    <!-- 背景图片 -->
    <div class="fixed inset-0 w-full h-full" style="background-color: rgb(255, 255, 255);">
      <img src="/images/login_background.jpg" draggable="false" class="absolute inset-0 w-full h-full" style="width: 100%; height: 100vh;" alt="Background" />
    </div>

    <!-- 半透明遮罩 -->
    <div class="fixed inset-0 bg-black bg-opacity-30"></div>

    <!-- 重置密码表单容器 -->
    <div class="login-container">
      <div class="login-box">
      <div class="login-header">
        <img src="/images/logo.png" alt="Logo" class="logo" />
        <h1 class="title">重置密码</h1>
        <p class="subtitle">请输入您的新密码</p>
      </div>

      <!-- 成功提示 -->
      <el-alert
        v-if="resetSuccess"
        type="success"
        :closable="false"
        class="success-alert"
      >
        <template #title>
          <div class="alert-content">
            <p class="alert-title">密码重置成功！</p>
            <p class="alert-message">{{ successMessage }}</p>
            <el-button
              type="success"
              text
              class="reset-link"
              @click="goToLogin"
            >
              前往登录 →
            </el-button>
          </div>
        </template>
      </el-alert>

      <!-- 表单 -->
      <el-form
        v-else
        ref="resetFormRef"
        :model="resetForm"
        :rules="resetRules"
        class="login-form"
        @keyup.enter="handleSubmit"
      >
        <!-- Token输入（仅在没有从URL获取token时显示） -->
        <el-form-item v-if="!tokenFromUrl" prop="token">
          <el-input
            v-model="resetForm.token"
            placeholder="请输入重置token"
            size="large"
            prefix-icon="Key"
            clearable
          />
        </el-form-item>

        <el-form-item prop="newPassword">
          <el-input
            v-model="resetForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6个字符）"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="resetForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            size="large"
            prefix-icon="Lock"
            show-password
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
            {{ loading ? '重置中...' : '重置密码' }}
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { resetPassword } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const resetFormRef = ref(null)
const loading = ref(false)
const resetSuccess = ref(false)
const successMessage = ref('')
const tokenFromUrl = ref(false)

const resetForm = reactive({
  token: '',
  newPassword: '',
  confirmPassword: ''
})

// 自定义验证规则：确认密码必须与新密码一致
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== resetForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const resetRules = {
  token: [
    { required: true, message: '请输入重置token', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

onMounted(() => {
  // 从URL参数获取token
  const urlToken = route.query.token
  if (urlToken) {
    resetForm.token = urlToken
    tokenFromUrl.value = true
  }
})

const handleSubmit = async () => {
  if (!resetFormRef.value) return

  try {
    // 验证表单
    await resetFormRef.value.validate()

    loading.value = true
    try {
      const response = await resetPassword({
        token: resetForm.token,
        new_password: resetForm.newPassword
      })
      resetSuccess.value = true
      successMessage.value = response.message || '密码重置成功，请使用新密码登录'

      // 3秒后自动跳转到登录页
      setTimeout(() => {
        goToLogin()
      }, 3000)
    } catch (error) {
      console.error('重置密码失败:', error)
      ElMessage.error(error.response?.data?.detail || '重置失败，请检查token是否有效')
    } finally {
      loading.value = false
    }
  } catch (error) {
    // 表单验证失败，不做任何操作（Element Plus 会自动显示错误信息）
    console.log('表单验证失败:', error)
  }
}

const goToLogin = () => {
  router.push('/login')
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
