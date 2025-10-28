import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/index.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/index.vue'),
          meta: { title: '工作台', icon: 'Odometer' }
        },
        {
          path: 'expense-to-voucher',
          name: 'ExpenseToVoucher',
          component: () => import('@/views/tools/expense-to-voucher/index.vue'),
          meta: { title: '费用清单转凭证', icon: 'DocumentCopy' }
        },
        {
          path: 'summary-translate',
          name: 'SummaryTranslate',
          component: () => import('@/views/tools/summary-translate/index.vue'),
          meta: { title: '摘要翻译', icon: 'Document' }
        },
        {
          path: 'bank-to-voucher',
          name: 'BankToVoucher',
          component: () => import('@/views/tools/bank-to-voucher/index.vue'),
          meta: { title: '银行流水转凭证', icon: 'CreditCard', disabled: true }
        },
        {
          path: 'history',
          name: 'History',
          component: () => import('@/views/history/index.vue'),
          meta: { title: '处理记录', icon: 'Clock' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/index.vue'),
          meta: { title: '系统设置', icon: 'Setting' }
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

export default router