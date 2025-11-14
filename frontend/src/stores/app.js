import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    sidebar: {
      opened: true,
      withoutAnimation: false
    },
    device: 'desktop',
    size: 'default',
    theme: localStorage.getItem('theme') || 'light', // 从localStorage读取主题
    language: 'zh-cn'
  }),

  getters: {
    isDesktop: (state) => state.device === 'desktop',
    isMobile: (state) => state.device === 'mobile',
    isDark: (state) => state.theme === 'dark'
  },

  actions: {
    toggleSidebar() {
      this.sidebar.opened = !this.sidebar.opened
      this.sidebar.withoutAnimation = false
    },

    closeSidebar(withoutAnimation) {
      this.sidebar.opened = false
      this.sidebar.withoutAnimation = withoutAnimation
    },

    toggleDevice(device) {
      this.device = device
    },

    setSize(size) {
      this.size = size
    },

    setTheme(theme) {
      this.theme = theme
      localStorage.setItem('theme', theme) // 持久化主题设置
      // 应用主题到document
      if (theme === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },

    toggleTheme() {
      const newTheme = this.theme === 'light' ? 'dark' : 'light'
      this.setTheme(newTheme)
    },

    setLanguage(language) {
      this.language = language
    },

    // 初始化主题
    initTheme() {
      const savedTheme = localStorage.getItem('theme') || 'light'
      this.setTheme(savedTheme)
    }
  }
})