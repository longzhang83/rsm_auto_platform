<template>
  <div id="userLayout" class="w-full h-full relative">
    <!-- 背景图片 -->
    <div class="fixed inset-0 w-full h-full" style="background-color: rgb(255, 255, 255);">
      <img src="/images/login_background.jpg" draggable="false" class="absolute inset-0 w-full h-full"
        style="width: 100%; height: 100vh;" alt="Background" />
    </div>

    <!-- 半透明遮罩 -->
    <div class="fixed inset-0 bg-black bg-opacity-30"></div>

    <!-- 登录表单容器 -->
    <div class="login-container">
      <div class="login-box">
        <!-- 翻页切换按钮 -->
        <div class="page-flip-button" @click="goToWeWorkLogin" title="企业微信登录">
          <div class="flip-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 22V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 12L2 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 12L22 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M17 4.5L7 9.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="flip-text">企微登录</span>
        </div>

        <div class="login-header">
          <img src="/images/logo.png" alt="Logo" class="logo" />
          <h1 class="title">容诚税务师事务所</h1>
          <p class="subtitle">智能化自动化工具平台</p>
        </div>

        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form"
          @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="loginForm.username" placeholder="用户名" size="large" prefix-icon="User" clearable />
          </el-form-item>

          <el-form-item prop="password">
            <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" prefix-icon="Lock"
              show-password clearable />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="login-button" :loading="loading" @click="handleLogin">
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>

          <div class="footer-links">
            <div class="register-link">
              还没有账号？
              <router-link to="/register" class="link">立即注册</router-link>
            </div>
            <div class="forgot-password-link">
              <router-link to="/forgot-password" class="link">忘记密码？</router-link>
            </div>
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

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref(null)
const loading = ref(false)

const goToWeWorkLogin = () => {
  router.push('/wework-login')
}

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    // 验证表单
    await loginFormRef.value.validate()

    loading.value = true
    try {
      const success = await authStore.login({
        username: loginForm.username,
        password: loginForm.password
      })

      if (success) {
        router.push('/')
      }
    } finally {
      loading.value = false
    }
  } catch (error) {
    // 表单验证失败，不做任何操作（Element Plus 会自动显示错误信息）
    console.log('表单验证失败:', error)
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

/* 翻页按钮样式 */
.page-flip-button {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 12px;
  background: linear-gradient(135deg, #49e670ff 0%, #0095d7 100%);
  border-radius: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.page-flip-button:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.page-flip-button:active {
  transform: translateY(0) scale(0.98);
}

.flip-icon {
  width: 32px;
  height: 32px;
  color: white;
  animation: flipAnimation 3s ease-in-out infinite;
}

.flip-icon svg {
  width: 100%;
  height: 100%;
}

.flip-text {
  color: white;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

/* 翻页动画 */
@keyframes flipAnimation {
  0%, 100% {
    transform: perspective(400px) rotateY(0deg);
  }
  25% {
    transform: perspective(400px) rotateY(180deg);
  }
  50% {
    transform: perspective(400px) rotateY(180deg);
  }
  75% {
    transform: perspective(400px) rotateY(360deg);
  }
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

.footer-links {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  font-size: 14px;
}

.register-link {
  color: #7f8c8d;
}

.forgot-password-link {
  /* 右侧链接 */
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
  .login-box {
    padding: 40px 30px;
  }

  .title {
    font-size: 24px;
  }

  .footer-links {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
}
</style>
