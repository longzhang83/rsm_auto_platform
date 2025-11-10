import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi, getCurrentUser } from '@/api/auth'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'rsm_access_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem(TOKEN_KEY) || null,
    permissions: ['expense-to-voucher', 'summary-translate', 'bank-to-voucher']
  }),

  getters: {
    isLoggedIn: (state) => !!state.token && !!state.user,

    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission)
    },

    userInfo: (state) => state.user
  },

  actions: {
    /**
     * 用户登录
     */
    async login(credentials) {
      try {
        const response = await loginApi(credentials)
        const { access_token, user } = response.data

        // 保存token和用户信息
        this.token = access_token
        this.user = user
        localStorage.setItem(TOKEN_KEY, access_token)

        ElMessage.success('登录成功')
        return true
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
        return false
      }
    },

    /**
     * 用户注册
     */
    async register(userData) {
      try {
        await registerApi(userData)
        ElMessage.success('注册成功，请登录')
        return true
      } catch (error) {
        console.error('注册失败:', error)
        ElMessage.error(error.response?.data?.detail || '注册失败，请稍后重试')
        return false
      }
    },

    /**
     * 获取当前用户信息
     */
    async fetchUserInfo() {
      try {
        const response = await getCurrentUser()
        this.user = response.data
        return true
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果获取用户信息失败，清除token
        this.logout()
        return false
      }
    },

    /**
     * 退出登录
     */
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem(TOKEN_KEY)
      ElMessage.info('已退出登录')
    },

    /**
     * 初始化用户状态（从token恢复）
     */
    async initAuth() {
      if (this.token && !this.user) {
        await this.fetchUserInfo()
      }
    }
  }
})