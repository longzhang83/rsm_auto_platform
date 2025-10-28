<template>
  <div class="app-wrapper">
    <!-- 侧边栏 -->
    <div class="sidebar-container" :class="{ 'is-collapse': !appStore.sidebar.opened }">
      <div class="sidebar-logo">
        <img src="/logo.png" alt="容诚税务师事务所" class="logo-img" />
        <span v-show="appStore.sidebar.opened" class="logo-text">容诚税务师事务所</span>
      </div>

      <el-scrollbar class="sidebar-scrollbar">
        <el-menu
          :default-active="$route.path"
          :collapse="!appStore.sidebar.opened"
          :unique-opened="true"
          :collapse-transition="false"
          mode="vertical"
          background-color="#1f2937"
          text-color="#f3f4f6"
          active-text-color="#ffffff"
          class="sidebar-menu"
          router
        >
          <sidebar-item v-for="route in menuRoutes" :key="route.path" :item="route" :base-path="route.path" />
        </el-menu>
      </el-scrollbar>
    </div>

    <!-- 主内容区 -->
    <div class="main-container" :class="{ 'is-collapse': !appStore.sidebar.opened }">
      <!-- 顶部导航栏 -->
      <div class="navbar">
        <div class="navbar-left">
          <el-button
            type="text"
            class="toggle-sidebar"
            @click="toggleSidebar"
          >
            <el-icon><Expand v-if="!appStore.sidebar.opened" /><Fold v-else /></el-icon>
          </el-button>

          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="navbar-right">
          <el-dropdown trigger="click" class="avatar-container">
            <div class="avatar-wrapper">
              <img :src="authStore.user.avatar" class="user-avatar" />
              <span class="user-name">{{ authStore.user.name }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 页面内容 -->
      <div class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SidebarItem from './components/SidebarItem.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

// 菜单路由
const menuRoutes = computed(() => {
  return router.options.routes[0].children.filter(route => !route.meta?.hidden)
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title
  }))
})

// 切换侧边栏
const toggleSidebar = () => {
  appStore.toggleSidebar()
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
  @apply bg-gray-800 transition-all duration-300;
  width: 250px;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1001;
  overflow: hidden;
}

.sidebar-container.is-collapse {
  width: 64px;
}

.sidebar-logo {
  @apply flex items-center justify-center h-16 bg-gray-900 border-b border-gray-700;
  padding: 0 16px;
}

.logo-img {
  @apply w-8 h-8 rounded;
}

.logo-text {
  @apply ml-3 text-white text-lg font-semibold;
}

.sidebar-scrollbar {
  @apply h-full;
}

.sidebar-menu {
  @apply border-none;
}

.main-container {
  @apply flex-1 flex flex-col;
  margin-left: 250px;
  transition: margin-left 0.3s;
  min-height: 100vh;
}

.main-container.is-collapse {
  margin-left: 64px;
}

.navbar {
  @apply flex items-center justify-between h-16 bg-white shadow-sm px-4;
}

.navbar-left {
  @apply flex items-center flex-1;
}

.toggle-sidebar {
  @apply text-gray-600 hover:text-gray-900;
}

.breadcrumb {
  @apply ml-4;
}

.navbar-right {
  @apply flex items-center;
}

.avatar-container {
  @apply cursor-pointer;
}

.avatar-wrapper {
  @apply flex items-center;
}

.user-avatar {
  @apply w-8 h-8 rounded-full;
}

.user-name {
  @apply ml-2 text-gray-700 text-sm;
}

.app-main {
  @apply flex-1 p-6 overflow-auto;
}

/* 路由过渡动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>