<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-4">
    <div class="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
      <!-- 标题 -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">重置密码</h1>
        <p class="text-gray-600">请输入您的新密码</p>
      </div>

      <!-- 成功提示 -->
      <div v-if="resetSuccess" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-green-500 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <div class="flex-1">
            <p class="text-green-800 font-medium">密码重置成功！</p>
            <p class="text-green-700 text-sm mt-1">{{ successMessage }}</p>
            <button
              @click="goToLogin"
              class="mt-3 text-sm text-green-600 hover:text-green-700 font-medium"
            >
              前往登录 →
            </button>
          </div>
        </div>
      </div>

      <!-- 表单 -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-700 text-sm">{{ errorMessage }}</p>
        </div>

        <!-- Token输入（仅在没有从URL获取token时显示） -->
        <div v-if="!tokenFromUrl">
          <label for="token" class="block text-sm font-medium text-gray-700 mb-2">
            重置Token
          </label>
          <input
            id="token"
            v-model="token"
            type="text"
            required
            placeholder="请输入重置token"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all font-mono text-sm"
            :disabled="loading"
          >
        </div>

        <!-- 新密码输入 -->
        <div>
          <label for="newPassword" class="block text-sm font-medium text-gray-700 mb-2">
            新密码
          </label>
          <input
            id="newPassword"
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            placeholder="请输入新密码（至少6个字符）"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            :disabled="loading"
          >
        </div>

        <!-- 确认密码输入 -->
        <div>
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-2">
            确认新密码
          </label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            minlength="6"
            placeholder="请再次输入新密码"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            :disabled="loading"
          >
          <p v-if="confirmPassword && newPassword !== confirmPassword" class="mt-1 text-sm text-red-600">
            两次输入的密码不一致
          </p>
        </div>

        <!-- 提交按钮 -->
        <button
          type="submit"
          :disabled="loading || (newPassword !== confirmPassword)"
          class="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="flex items-center justify-center">
            <svg class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            重置中...
          </span>
          <span v-else>重置密码</span>
        </button>
      </form>

      <!-- 返回登录 -->
      <div class="mt-6 text-center">
        <router-link
          to="/login"
          class="text-purple-600 hover:text-purple-700 font-medium text-sm"
        >
          ← 返回登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { resetPassword } from '@/api/auth'

const router = useRouter()
const route = useRoute()

const token = ref('')
const tokenFromUrl = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const resetSuccess = ref(false)
const successMessage = ref('')

onMounted(() => {
  // 从URL参数获取token
  const urlToken = route.query.token
  if (urlToken) {
    token.value = urlToken
    tokenFromUrl.value = true
  }
})

const handleSubmit = async () => {
  // 验证密码
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  if (newPassword.value.length < 6) {
    errorMessage.value = '密码长度至少为6个字符'
    return
  }

  errorMessage.value = ''
  loading.value = true

  try {
    const response = await resetPassword({
      token: token.value,
      new_password: newPassword.value
    })
    resetSuccess.value = true
    successMessage.value = response.message || '密码重置成功，请使用新密码登录'

    // 3秒后自动跳转到登录页
    setTimeout(() => {
      goToLogin()
    }, 3000)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '重置失败，请检查token是否有效'
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>
