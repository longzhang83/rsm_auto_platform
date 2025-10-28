<template>
  <div class="not-found">
    <div class="content">
      <div class="number">404</div>
      <div class="message">页面不存在</div>
      <div class="description">
        抱歉，您访问的页面不存在或已被移除
      </div>
      <div class="actions">
        <el-button type="primary" @click="goHome">
          <el-icon class="mr-1"><House /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
    </div>

    <div class="illustration">
      <el-icon class="icon"><DocumentRemove /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.content {
  text-align: center;
  z-index: 1;
}

.number {
  font-size: 8rem;
  font-weight: bold;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.message {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.description {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.illustration {
  margin-left: 4rem;
}

.icon {
  font-size: 12rem;
  opacity: 0.3;
}

@media (max-width: 768px) {
  .not-found {
    flex-direction: column;
    text-align: center;
  }

  .number {
    font-size: 6rem;
  }

  .message {
    font-size: 1.5rem;
  }

  .illustration {
    margin-left: 0;
    margin-top: 2rem;
  }

  .actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>