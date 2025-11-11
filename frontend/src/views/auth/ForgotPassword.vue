<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-4">
    <div class="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
      <!-- 标题 -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">忘记密码</h1>
        <p class="text-gray-600">输入您的注册邮箱，我们将发送重置密码链接</p>
      </div>

      <!-- 成功提示 -->
      <div v-if="resetSent" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-green-500 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <div class="flex-1">
            <p class="text-green-800 font-medium">重置链接已生成</p>
            <p class="text-green-700 text-sm mt-1">{{ successMessage }}</p>
            <!-- 开发环境显示token -->
            <div v-if="resetToken" class="mt-3 p-3 bg-white rounded border border-green-300">
              <p class="text-xs text-gray-600 mb-1">开发环境 - 重置Token:</p>
              <p class="text-xs font-mono break-all text-gray-800">{{ resetToken }}</p>
              <button
                @click="copyToken"
                class="mt-2 text-xs text-green-600 hover:text-green-700 font-medium"
              >
                复制Token
              </button>
            </div>
            <button
              @click="goToResetPassword"
              class="mt-3 text-sm text-green-600 hover:text-green-700 font-medium"
            >
              前往重置密码页面 →
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

        <!-- 邮箱输入 -->
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            邮箱地址
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="请输入注册邮箱"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            :disabled="loading"
          >
        </div>

        <!-- 提交按钮 -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="flex items-center justify-center">
            <svg class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            发送中...
          </span>
          <span v-else>发送重置链接</span>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { forgotPassword } from '@/api/auth'

const router = useRouter()

const email = ref('')
const loading = ref(false)
const errorMessage = ref('')
const resetSent = ref(false)
const successMessage = ref('')
const resetToken = ref('')

const handleSubmit = async () => {
  errorMessage.value = ''
  loading.value = true

  try {
    const response = await forgotPassword({ email: email.value })
    resetSent.value = true
    successMessage.value = response.message || '重置链接已发送到您的邮箱'
    resetToken.value = response.reset_token || ''
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '发送失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const copyToken = () => {
  navigator.clipboard.writeText(resetToken.value)
  alert('Token已复制到剪贴板')
}

const goToResetPassword = () => {
  if (resetToken.value) {
    router.push(`/reset-password?token=${resetToken.value}`)
  } else {
    router.push('/reset-password')
  }
}
</script>
