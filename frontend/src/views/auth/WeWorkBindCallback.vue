<template>
  <div class="callback-container">
    <div class="callback-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" size="48">
          <Loading />
        </el-icon>
        <p class="status-text">正在绑定企业微信账号...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <el-icon size="48" color="#f56c6c">
          <CircleClose />
        </el-icon>
        <p class="status-text error">绑定失败</p>
        <p class="error-message">{{ error }}</p>
        <el-button type="primary" @click="goToProfile" class="mt-4">
          返回个人中心
        </el-button>
      </div>

      <div v-else class="success-state">
        <el-icon size="48" color="#67c23a">
          <CircleCheck />
        </el-icon>
        <p class="status-text success">绑定成功！</p>
        <p class="sub-text">企业微信账号已成功绑定</p>
        <p class="redirect-text">{{ countdown }}秒后自动跳转...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref('')
const countdown = ref(3)

const goToProfile = () => {
  router.push('/profile')
}

const handleBind = async () => {
  try {
    const code = route.query.code
    const state = route.query.state

    if (!code) {
      error.value = '未获取到授权码'
      loading.value = false
      return
    }

    // 调用绑定API
    const response = await request.post('/auth/wework/bind', { code, state })

    if (response.success) {
      loading.value = false
      ElMessage.success('企业微信账号绑定成功！')

      // 刷新用户信息
      await authStore.initAuth()

      // 倒计时跳转
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(timer)
          router.push('/profile')
        }
      }, 1000)
    } else {
      error.value = response.message || '绑定失败'
      loading.value = false
    }
  } catch (err) {
    console.error('绑定企业微信失败:', err)
    error.value = err.response?.data?.detail || '绑定过程中发生错误，请重试'
    loading.value = false
  }
}

onMounted(() => {
  handleBind()
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.callback-content {
  text-align: center;
  padding: 60px 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  min-width: 400px;
}

.status-text {
  font-size: 24px;
  font-weight: 600;
  margin-top: 20px;
  color: #2c3e50;
}

.status-text.error {
  color: #f56c6c;
}

.status-text.success {
  color: #67c23a;
}

.sub-text {
  font-size: 16px;
  color: #7f8c8d;
  margin-top: 12px;
}

.error-message {
  font-size: 14px;
  color: #f56c6c;
  margin-top: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 8px;
}

.redirect-text {
  font-size: 14px;
  color: #95a5a6;
  margin-top: 20px;
}

.loading-state,
.error-state,
.success-state {
  padding: 20px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
