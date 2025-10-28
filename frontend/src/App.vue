<template>
  <div id="app" class="min-h-screen" style="background: var(--neutral-50);">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('容诚税务师事务所自动化工具平台已启动')
})
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 清新简约主题配色 */
:root {
  /* 主色调 - 定制清新蓝 */
  --primary-50: #F0FBFF;
  --primary-100: #E0F7FF;
  --primary-200: #BAE7FF;
  --primary-300: #7DD3FC;
  --primary-400: #38BDF8;
  --primary-500: #0EA5E9;
  --primary-600: #0095D7;
  --primary-700: #0284C7;
  --primary-800: #0369A1;
  --primary-900: #075985;

  /* 辅助色 - 温和绿 */
  --accent-50: #F0FDF4;
  --accent-100: #DCFCE7;
  --accent-200: #BBF7D0;
  --accent-300: #86EFAC;
  --accent-400: #4ADE80;
  --accent-500: #22C55E;
  --accent-600: #16A34A;
  --accent-700: #15803D;
  --accent-800: #166534;
  --accent-900: #14532D;

  /* 点缀色 - 柔和橙 */
  --highlight-50: #FFFBEB;
  --highlight-100: #FEF3C7;
  --highlight-200: #FDE68A;
  --highlight-300: #FCD34D;
  --highlight-400: #FBBF24;
  --highlight-500: #F59E0B;
  --highlight-600: #D97706;
  --highlight-700: #B45309;
  --highlight-800: #92400E;
  --highlight-900: #78350F;

  /* 中性色系 */
  --neutral-50: #FAFAFA;
  --neutral-100: #F5F5F5;
  --neutral-200: #E5E5E5;
  --neutral-300: #D4D4D4;
  --neutral-400: #A3A3A3;
  --neutral-500: #737373;
  --neutral-600: #525252;
  --neutral-700: #404040;
  --neutral-800: #262626;
  --neutral-900: #171717;

  /* 品牌色映射 */
  --brand-primary: var(--primary-600);
  --brand-primary-light: var(--primary-400);
  --brand-primary-lighter: var(--primary-300);
  --brand-primary-dark: var(--primary-700);
  --brand-primary-darker: var(--primary-800);

  --brand-secondary: var(--accent-500);
  --brand-secondary-light: var(--accent-400);
  --brand-secondary-lighter: var(--accent-300);
  --brand-secondary-dark: var(--accent-600);
  --brand-secondary-darker: var(--accent-700);

  --brand-accent: var(--highlight-500);
  --brand-success: var(--accent-500);
  --brand-warning: var(--highlight-500);
  --brand-info: var(--primary-500);

  --brand-gray-50: var(--neutral-50);
  --brand-gray-100: var(--neutral-100);
  --brand-gray-200: var(--neutral-200);
  --brand-gray-300: var(--neutral-300);
  --brand-gray-400: var(--neutral-400);
  --brand-gray-500: var(--neutral-500);
  --brand-gray-600: var(--neutral-600);
  --brand-gray-700: var(--neutral-700);
  --brand-gray-800: var(--neutral-800);
  --brand-gray-900: var(--neutral-900);

  /* Element Plus 主题映射 */
  --el-color-primary: var(--brand-primary);
  --el-color-primary-light-3: var(--brand-primary-light);
  --el-color-primary-light-5: var(--brand-primary-lighter);
  --el-color-primary-light-7: var(--accent-300);
  --el-color-primary-light-8: var(--accent-200);
  --el-color-primary-light-9: var(--primary-50);
  --el-color-primary-dark-2: var(--brand-primary-dark);
  --el-color-success: var(--brand-success);
  --el-color-warning: var(--brand-warning);
  --el-color-danger: var(--accent-600);
  --el-color-error: var(--accent-600);
  --el-color-info: var(--brand-info);
}

/* 品牌色滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--brand-gray-100);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--brand-gray-400);
  border-radius: 4px;
  transition: background 0.2s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--brand-primary-light);
}
</style>