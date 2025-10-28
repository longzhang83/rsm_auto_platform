import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    sidebar: {
      opened: true,
      withoutAnimation: false
    },
    device: 'desktop',
    size: 'default',
    theme: 'light',
    language: 'zh-cn'
  }),

  getters: {
    isDesktop: (state) => state.device === 'desktop',
    isMobile: (state) => state.device === 'mobile'
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
    },

    setLanguage(language) {
      this.language = language
    }
  }
})