import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: {
      name: '容诚税务师',
      email: 'admin@rongcheng.com',
      avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
      role: 'admin'
    },
    permissions: ['expense-to-voucher', 'summary-translate', 'bank-to-voucher']
  }),

  getters: {
    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission)
    }
  },

  actions: {
    updateUserInfo(userInfo) {
      this.user = { ...this.user, ...userInfo }
    },

    logout() {
      this.user = null
      this.permissions = []
    }
  }
})