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
        <div class="login-header">
          <img src="/images/logo.png" alt="Logo" class="logo" />
          <h1 class="title">容诚税务师事务所</h1>
          <p class="subtitle">智能化自动化工具平台</p>
        </div>

        <!-- 登录方式切换 -->
        <div class="login-tabs">
          <div class="tab-buttons">
            <button
              :class="['tab-button', { active: loginMode === 'password' }]"
              @click="loginMode = 'password'"
            >
              <el-icon class="tab-icon"><Lock /></el-icon>
              <span>密码登录</span>
            </button>
            <button
              :class="['tab-button', { active: loginMode === 'wework' }]"
              @click="loginMode = 'wework'"
            >
              <el-icon class="tab-icon"><Briefcase /></el-icon>
              <span>企业微信</span>
            </button>
          </div>
          <div class="tab-indicator" :style="{ left: loginMode === 'password' ? '0%' : '50%' }"></div>
        </div>

        <!-- 密码登录表单 -->
        <div v-show="loginMode === 'password'" class="login-content">
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

        <!-- 企业微信登录 -->
        <div v-show="loginMode === 'wework'" class="login-content">
          <WeWorkLogin />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Lock, Briefcase } from '@element-plus/icons-vue'
import WeWorkLogin from '@/components/WeWorkLogin.vue'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref(null)
const loading = ref(false)
const loginMode = ref('password') // 'password' 或 'wework'

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

/* 登录方式切换标签 */
.login-tabs {
  position: relative;
  margin-bottom: 30px;
}

.tab-buttons {
  display: flex;
  background: #f5f7fa;
  border-radius: 12px;
  padding: 4px;
  position: relative;
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: #606266;
  font-size: 15px;
  font-weight: 500;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.tab-button .tab-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.tab-button:hover {
  color: var(--brand-primary);
}

.tab-button:hover .tab-icon {
  transform: scale(1.1);
}

.tab-button.active {
  color: white;
}

.tab-indicator {
  position: absolute;
  top: 4px;
  left: 0;
  width: 50%;
  height: calc(100% - 8px);
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-dark) 50%, var(--brand-secondary) 100%);
  border-radius: 10px;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
  box-shadow: 0 2px 8px rgba(0, 149, 215, 0.3);
}

.login-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
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
  color: var(--brand-primary);
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  color: var(--brand-primary-dark);
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
