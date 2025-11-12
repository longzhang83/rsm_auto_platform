<template>
  <div id="userLayout" class="w-full h-full relative">
    <!-- 背景图片 -->
    <div class="fixed inset-0 w-full h-full" style="background-color: rgb(255, 255, 255);">
      <img src="/images/login_background.jpg" draggable="false" class="absolute inset-0 w-full h-full"
        style="width: 100%; height: 100vh;" alt="Background" />
    </div>

    <!-- 半透明遮罩 -->
    <div class="fixed inset-0 bg-black bg-opacity-30"></div>

    <!-- 企业微信登录容器 -->
    <div class="login-container">
      <div class="login-box">
        <!-- 返回密码登录按钮 -->
        <div class="back-to-login">
          <el-button text @click="goToPasswordLogin" class="back-button">
            <el-icon class="mr-1"><ArrowLeft /></el-icon>
            返回密码登录
          </el-button>
        </div>

        <div class="login-header">
          <img src="/images/logo.png" alt="Logo" class="logo" />
          <h1 class="title">容诚税务师事务所</h1>
          <p class="subtitle">智能化自动化工具平台</p>
        </div>

        <!-- 企业微信登录组件 -->
        <WeWorkLoginQR />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import WeWorkLoginQR from '@/components/WeWorkLogin.vue'

const router = useRouter()

const goToPasswordLogin = () => {
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

.back-to-login {
  position: absolute;
  top: 20px;
  left: 20px;
}

.back-button {
  color: #667eea;
  font-size: 14px;
}

.back-button:hover {
  color: #764ba2;
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

@media (max-width: 576px) {
  .login-box {
    padding: 40px 30px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
