<template>
  <div class="app-wrapper">
    <!-- 侧边栏 -->
    <div class="sidebar-container" :class="{ 'is-collapse': !appStore.sidebar.opened }">
      <div class="sidebar-logo">
        <div class="logo-wrapper">
          <div class="logo-img-container">
            <img src="/images/logo.png" alt="容诚税务师事务所" class="logo-img" />
            <div class="logo-glow"></div>
            <div class="logo-shine"></div>
          </div>
          <transition name="logo-fade">
            <div v-show="appStore.sidebar.opened" class="logo-content">
              <h3 class="logo-text">容诚税务师事务所</h3>
              <p class="logo-subtitle">智能自动化平台</p>
            </div>
          </transition>
        </div>
        </div>

      <el-scrollbar class="sidebar-scrollbar">
        <div class="menu-section">
          <div v-show="appStore.sidebar.opened" class="section-title">
            <span>主要功能</span>
          </div>
          <el-menu
            :default-active="$route.path"
            :collapse="!appStore.sidebar.opened"
            :unique-opened="true"
            :collapse-transition="false"
            mode="vertical"
            background-color="transparent"
            text-color="rgba(255, 255, 255, 0.8)"
            active-text-color="#ffffff"
            class="sidebar-menu"
            router
          >
            <sidebar-item v-for="route in menuRoutes" :key="route.path" :item="route" :base-path="'/'" />
          </el-menu>
        </div>
      </el-scrollbar>

      <!-- 侧边栏底部装饰 -->
      <div class="sidebar-footer">
        <div v-show="appStore.sidebar.opened" class="footer-content">
          <div class="system-info">
            <div class="status-indicator online"></div>
            <span class="status-text">系统运行正常</span>
          </div>
          <div class="version-info">v1.0.0</div>
        </div>
        <div v-show="!appStore.sidebar.opened" class="footer-collapsed">
          <div class="status-indicator online"></div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container" :class="{ 'is-collapse': !appStore.sidebar.opened }">
      <!-- 顶部导航栏 -->
      <div class="navbar">
        <div class="navbar-left">
          <div class="nav-actions">
            <button class="toggle-sidebar" @click="toggleSidebar">
              <el-icon><Expand v-if="!appStore.sidebar.opened" /><Fold v-else /></el-icon>
            </button>
          </div>

          <div class="breadcrumb-container">
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
                {{ item.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>

        <div class="navbar-right">
          <!-- 快捷操作按钮组 -->
          <div class="quick-actions">
            <button class="action-btn notification-btn">
              <el-icon><Bell /></el-icon>
              <span class="notification-dot"></span>
            </button>
            <!-- 主题切换按钮 - 暂时禁用功能 -->
            <button class="action-btn theme-btn" title="主题切换（开发中）">
              <el-icon><Sunny /></el-icon>
            </button>
            <button class="action-btn settings-btn" @click="navigateToSettings">
              <el-icon><Setting /></el-icon>
            </button>
          </div>

          <!-- 用户信息 -->
          <div class="user-section">
            <div class="user-stats">
              <div class="stat-item">
                <span class="stat-value">156</span>
                <span class="stat-label">今日处理</span>
              </div>
            </div>

            <el-dropdown trigger="click" class="avatar-container" v-if="authStore.user">
              <div class="avatar-wrapper">
                <div class="user-avatar-wrapper">
                  <div class="user-avatar-placeholder">{{ userInitials }}</div>
                  <div class="user-status online"></div>
                </div>
                <div class="user-info">
                  <span class="user-name">{{ authStore.user.username }}</span>
                  <span class="user-role">会计师</span>
                </div>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu class="user-dropdown">
                  <el-dropdown-item class="dropdown-header">
                    <div class="header-info">
                      <div class="header-avatar-placeholder">{{ userInitials }}</div>
                      <div class="header-text">
                        <div class="header-name">{{ authStore.user.username }}</div>
                        <div class="header-role">会计师</div>
                      </div>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="navigateToProfile">
                    <el-icon><User /></el-icon>
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item @click="navigateToHistory">
                    <el-icon><DocumentCopy /></el-icon>
                    我的记录
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout" class="logout-item">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 页面内容 -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <div class="route-wrapper">
              <component :is="Component" />
            </div>
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SidebarItem from './components/SidebarItem.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

// 初始化主题
onMounted(() => {
  appStore.initTheme()
})

// 菜单路由
const menuRoutes = computed(() => {
  // 找到 Layout 路由（path 为 '/'）
  const layoutRoute = router.options.routes.find(route => route.path === '/')
  return layoutRoute?.children?.filter(route => !route.meta?.hidden) || []
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title
  }))
})

// 用户头像首字母
const userInitials = computed(() => {
  if (!authStore.user?.username) return 'U'
  return authStore.user.username.substring(0, 1).toUpperCase()
})

// 切换侧边栏
const toggleSidebar = () => {
  appStore.toggleSidebar()
}

// 切换主题
const toggleTheme = () => {
  appStore.toggleTheme()
}

// 导航到系统设置
const navigateToSettings = () => {
  router.push('/settings')
}

// 导航到个人中心/账户设置
const navigateToProfile = () => {
  router.push('/profile')
}

// 导航到我的记录
const navigateToHistory = () => {
  router.push('/history')
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-wrapper {
  @apply flex h-screen bg-gray-50;
}

.sidebar-container {
  background: white;
  transition: all 0.3s ease;
  width: 280px;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1001;
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--neutral-200);
}

.sidebar-container.is-collapse {
  width: 80px;
}

.sidebar-logo {
  background: transparent;
  padding: 32px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}


.logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.logo-img-container {
  position: relative;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 16px;
  padding: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-img-container:hover {
  transform: translateY(-2px) scale(1.05);
}

.logo-img {
  width: 32px;
  height: 32px;
  border-radius: 0;
  filter: brightness(1.1) contrast(1.1);
  transition: all 0.3s ease;
}

.logo-glow {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  background: linear-gradient(135deg, var(--primary-400) 0%, var(--primary-600) 50%, var(--primary-400) 100%);
  border-radius: 20px;
  opacity: 0;
  transition: all 0.3s ease;
  z-index: -1;
  filter: blur(8px);
}

.logo-img-container:hover .logo-glow {
  opacity: 0.6;
  transform: scale(1.1);
}

.logo-shine {
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  height: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, transparent 100%);
  border-radius: 14px 14px 0 0;
  pointer-events: none;
}

.logo-content {
  margin-left: 16px;
  animation: slideInRight 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-text {
  color: var(--neutral-800);
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.logo-subtitle {
  color: var(--primary-600);
  font-size: 11px;
  margin: 4px 0 0 0;
  font-weight: 500;
  letter-spacing: 0.5px;
  opacity: 0.8;
}


.sidebar-scrollbar {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.sidebar-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-scrollbar::-webkit-scrollbar-thumb {
  background: var(--neutral-300);
  border-radius: 2px;
}

.sidebar-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--neutral-400);
}

.menu-section {
  padding: 24px 16px;
}

.section-title {
  color: var(--neutral-500);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  padding: 0 12px;
}

.section-title::before {
  display: none;
}

.sidebar-menu {
  border: none;
  background: transparent;
}

.sidebar-footer {
  padding: 24px;
  border-top: 1px solid var(--neutral-200);
  background: var(--neutral-50);
  margin-top: auto;
}

.footer-content {
  animation: slideInUp 0.3s ease-out;
}

.system-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-indicator.online {
  background: var(--accent-500);
}

.status-text {
  color: var(--neutral-600);
  font-size: 12px;
  font-weight: 500;
}

.version-info {
  color: var(--neutral-400);
  font-size: 10px;
  text-align: center;
  font-weight: 400;
}

.footer-collapsed {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 过渡动画 */
.logo-fade-enter-active,
.logo-fade-leave-active {
  transition: all 0.3s ease;
}

.logo-fade-enter-from,
.logo-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes slideInLogo {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-3px);
  }
}

.main-container {
  @apply flex-1 flex flex-col;
  margin-left: 280px;
  transition: margin-left 0.3s ease;
  min-height: 100vh;
  background: var(--neutral-50);
}

.main-container.is-collapse {
  margin-left: 80px;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  background: white;
  padding: 0 32px;
  border-bottom: 1px solid var(--neutral-200);
  position: relative;
}

.navbar-left {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 24px;
}

.nav-actions {
  display: flex;
  align-items: center;
}

.toggle-sidebar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--neutral-600);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 18px;
}

.toggle-sidebar:hover {
  background: var(--neutral-100);
  color: var(--primary-600);
}

.breadcrumb-container {
  position: relative;
}

.breadcrumb {
  display: flex;
  align-items: center;
}

.breadcrumb :deep(.el-breadcrumb__item) {
  font-weight: 500;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  color: var(--neutral-600);
  font-size: 14px;
  transition: all 0.2s ease;
}

.breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: var(--primary-600);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--neutral-500);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  font-size: 16px;
}

.action-btn:hover {
  background: var(--neutral-100);
  color: var(--neutral-700);
}

.notification-btn {
  position: relative;
}

.notification-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  background: var(--accent-500);
  border-radius: 50%;
  border: 1px solid white;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-stats {
  display: none; /* 隐藏统计数据，使界面更简洁 */
}

.avatar-container {
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.avatar-container:hover {
  background: var(--neutral-100);
}

.avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-avatar-placeholder:hover {
  transform: scale(1.05);
}

.user-status {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
}

.user-status.online {
  background: var(--accent-500);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--neutral-800);
  line-height: 1.2;
}

.user-role {
  font-size: 12px;
  color: var(--neutral-500);
  font-weight: 400;
  margin-top: 2px;
}

.dropdown-icon {
  color: var(--neutral-400);
  font-size: 14px;
  transition: all 0.2s ease;
}

.avatar-container:hover .dropdown-icon {
  color: var(--neutral-600);
}

.app-main {
  @apply flex-1 p-8 overflow-auto;
  background: var(--neutral-50);
}

.route-wrapper {
  width: 100%;
  height: 100%;
}

/* 增强的路由过渡动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px) scale(0.98);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px) scale(1.02);
}

/* 侧边栏菜单基础样式 - 具体样式由 SidebarItem 组件管理 */
.sidebar-menu {
  /* 菜单样式已移至 SidebarItem.vue 组件中以支持多层级嵌套 */
}

/* 简洁用户下拉菜单样式 */
.user-dropdown {
  border: 1px solid var(--neutral-200);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  min-width: 220px;
  background: white;
}

.user-dropdown :deep(.el-dropdown-menu__item) {
  padding: 10px 16px;
  font-size: 14px;
  color: var(--neutral-700);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-dropdown :deep(.el-dropdown-menu__item:hover) {
  background: var(--neutral-50);
  color: var(--primary-600);
}

.user-dropdown :deep(.el-dropdown-menu__item.is-divided) {
  border-top: 1px solid var(--neutral-200);
  margin-top: 4px;
  padding-top: 12px;
}

.dropdown-header {
  padding: 16px !important;
  background: var(--neutral-50);
  border-bottom: 1px solid var(--neutral-200);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.header-text {
  flex: 1;
}

.header-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--neutral-800);
  margin-bottom: 2px;
}

.header-role {
  font-size: 12px;
  color: var(--neutral-500);
}

.logout-item {
  color: var(--accent-600) !important;
}

.logout-item:hover {
  background: var(--accent-50) !important;
  color: var(--accent-700) !important;
}

.user-dropdown :deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--neutral-400);
}

.user-dropdown :deep(.el-dropdown-menu__item:hover .el-icon) {
  color: var(--primary-600);
}
</style>