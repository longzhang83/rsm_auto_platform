<template>
  <div class="callback-container">
    <div class="callback-box">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" size="48" color="#667eea">
          <Loading />
        </el-icon>
        <h2>正在登录...</h2>
        <p>请稍候，正在验证您的企业微信账号</p>
      </div>

      <div v-else-if="error" class="error-state">
        <el-icon size="48" color="#f56c6c">
          <CircleClose />
        </el-icon>
        <h2>登录失败</h2>
        <p>{{ error }}</p>
        <el-button type="primary" @click="redirectToLogin">
          返回登录页
        </el-button>
      </div>

      <div v-else class="success-state">
        <el-icon size="48" color="#67c23a">
          <CircleCheck />
        </el-icon>
        <h2>登录成功</h2>
        <p>正在跳转...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Loading, CircleClose, CircleCheck } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const error = ref('')

const redirectToLogin = () => {
  router.push('/login')
}

const handleCallback = async () => {
  try {
    // 获取URL参数
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')

    // 检查是否有错误
    const errorParam = urlParams.get('error')
    if (errorParam) {
      error.value = `授权失败: ${urlParams.get('error_description') || errorParam}`
      loading.value = false
      return
    }

    // 检查code
    if (!code) {
      error.value = '未获取到授权码，请重新扫码登录'
      loading.value = false
      return
    }

    // 调用后端接口完成登录
    try {
      const response = await request.post('/auth/wework/callback', {
        code,
        state: state || '',
      })

      // 保存token和用户信息
      if (response.access_token && response.user) {
        // 使用auth store的方法保存token和用户信息
        localStorage.setItem('token', response.access_token)
        authStore.user = response.user
        authStore.isAuthenticated = true

        ElMessage.success('登录成功！')

        // 延迟跳转，让用户看到成功提示
        loading.value = false
        setTimeout(() => {
          router.push('/')
        }, 1000)
      } else {
        error.value = '登录响应格式错误'
        loading.value = false
      }
    } catch (err) {
      console.error('企业微信登录失败:', err)
      error.value = err.response?.data?.detail || err.message || '登录失败，请重试'
      loading.value = false
    }
  } catch (err) {
    console.error('处理回调失败:', err)
    error.value = '处理登录回调失败'
    loading.value = false
  }
}

onMounted(() => {
  handleCallback()
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.callback-box {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  padding: 60px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.loading-state,
.error-state,
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-state h2,
.error-state h2,
.success-state h2 {
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0;
}

.loading-state p,
.error-state p,
.success-state p {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
}

.error-state .el-button {
  margin-top: 12px;
}

@media (max-width: 576px) {
  .callback-box {
    padding: 40px 30px;
  }

  .loading-state h2,
  .error-state h2,
  .success-state h2 {
    font-size: 20px;
  }
}
</style>
