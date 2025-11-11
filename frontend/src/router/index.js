import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { title: '登录', requiresAuth: false }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/Register.vue'),
      meta: { title: '注册', requiresAuth: false }
    },
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('@/views/auth/ForgotPassword.vue'),
      meta: { title: '忘记密码', requiresAuth: false }
    },
    {
      path: '/reset-password',
      name: 'ResetPassword',
      component: () => import('@/views/auth/ResetPassword.vue'),
      meta: { title: '重置密码', requiresAuth: false }
    },
    {
      path: '/auth/wework/callback',
      name: 'WeWorkCallback',
      component: () => import('@/views/auth/WeWorkCallback.vue'),
      meta: { title: '企业微信登录', requiresAuth: false }
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/index.vue'),
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/index.vue'),
          meta: { title: '工作台', icon: 'Odometer', requiresAuth: true }
        },
        {
          path: 'expense-to-voucher',
          name: 'ExpenseToVoucher',
          component: () => import('@/views/tools/expense-to-voucher/index.vue'),
          meta: { title: '费用清单转凭证', icon: 'DocumentCopy', requiresAuth: true }
        },
        {
          path: 'summary-translate',
          name: 'SummaryTranslate',
          component: () => import('@/views/tools/summary-translate/index.vue'),
          meta: { title: '摘要翻译', icon: 'Document', requiresAuth: true }
        },
        {
          path: 'bank-to-voucher',
          name: 'BankToVoucher',
          component: () => import('@/views/tools/bank-to-voucher/index.vue'),
          meta: { title: '银行流水转凭证', icon: 'CreditCard', requiresAuth: true }
        },
        {
          path: 'history',
          name: 'History',
          component: () => import('@/views/history/index.vue'),
          meta: { title: '处理记录', icon: 'Clock', requiresAuth: true }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/index.vue'),
          meta: { title: '系统设置', icon: 'Setting', requiresAuth: true }
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/profile/index.vue'),
          meta: { title: '个人资料', icon: 'User', requiresAuth: true }
        },
        {
          path: 'admin',
          name: 'Admin',
          component: () => import('@/views/admin/index.vue'),
          meta: { title: '管理后台', icon: 'Setting', requiresAuth: true, requiresAdmin: true }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/404.vue')
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 初始化认证状态（从token恢复）
  if (!authStore.user && authStore.token) {
    await authStore.initAuth()
  }

  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    if (authStore.isLoggedIn) {
      next()
    } else {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    }
  } else {
    // 如果已登录，访问登录/注册/忘记密码页面时重定向到首页
    const authPages = ['/login', '/register', '/forgot-password']
    if (authPages.includes(to.path) && authStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
