<template>
  <div id="app" class="min-h-screen bg-gray-50">
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

/* Element Plus 主题定制 */
:root {
  --el-color-primary: #dc2626;
  --el-color-primary-light-3: #ef4444;
  --el-color-primary-light-5: #f87171;
  --el-color-primary-light-7: #fca5a5;
  --el-color-primary-light-8: #fecaca;
  --el-color-primary-light-9: #fee2e2;
  --el-color-primary-dark-2: #b91c1c;
  --el-color-success: #16a34a;
  --el-color-warning: #d97706;
  --el-color-danger: #dc2626;
  --el-color-error: #dc2626;
  --el-color-info: #0ea5e9;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>