<template>
  <div class="wework-login">
    <div v-if="!enabled" class="wework-disabled">
      <el-alert
        title="企业微信登录未启用"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <div v-else class="wework-qr-section">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" size="32">
          <Loading />
        </el-icon>
        <p>正在加载企业微信登录...</p>
      </div>

      <div v-else-if="error" class="error-container">
        <el-alert
          :title="error"
          type="error"
          :closable="false"
          show-icon
        />
        <el-button type="primary" size="small" @click="loadWeWorkConfig" style="margin-top: 12px;">
          重新加载
        </el-button>
      </div>

      <!-- 始终渲染容器，用 v-show 控制显示 -->
      <div id="wework-qr-container" class="qr-container" v-show="!loading && !error"></div>

      <p class="wework-hint">使用企业微信扫码登录</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const enabled = ref(false)
const config = ref(null)

const loadWeWorkConfig = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await request.get('/auth/wework/config')

    if (!response.enabled) {
      enabled.value = false
      loading.value = false
      return
    }

    enabled.value = true
    config.value = response

    // 等待DOM更新完成后再初始化二维码
    await nextTick()
    // 额外延迟以确保DOM完全渲染
    setTimeout(() => {
      initWeWorkQR()
    }, 50)
  } catch (err) {
    console.error('获取企业微信配置失败:', err)
    error.value = '获取企业微信配置失败，请稍后重试'
    loading.value = false
  }
}

const initWeWorkQR = () => {
  if (!config.value) {
    error.value = '企业微信配置无效'
    loading.value = false
    return
  }

  // 先设置 loading 为 false，让 DOM 容器显示出来
  loading.value = false

  // 加载企业微信JS SDK
  if (typeof window.WwLogin === 'undefined') {
    // 显示加载状态
    loading.value = true
    const script = document.createElement('script')
    script.src = 'https://rescdn.qqmail.com/node/ww/wwopenmng/js/sso/wwLogin-1.0.0.js'
    script.onload = () => {
      loading.value = false
      // 再次等待 DOM 更新后渲染
      setTimeout(() => {
        renderQRCode()
      }, 50)
    }
    script.onerror = () => {
      error.value = '加载企业微信SDK失败'
      loading.value = false
    }
    document.head.appendChild(script)
  } else {
    // SDK 已加载，直接渲染
    setTimeout(() => {
      renderQRCode()
    }, 50)
  }
}

const renderQRCode = () => {
  try {
    // 检查容器是否存在
    const container = document.getElementById('wework-qr-container')
    if (!container) {
      console.error('企业微信二维码容器未找到')
      error.value = '二维码容器未准备好，请刷新页面重试'
      return
    }

    // 清空容器
    container.innerHTML = ''

    // 检查WwLogin是否可用
    if (typeof window.WwLogin !== 'function') {
      console.error('WwLogin SDK未正确加载')
      error.value = '企业微信SDK未正确加载'
      return
    }

    // 生成二维码
    new window.WwLogin({
      id: 'wework-qr-container',
      appid: config.value.corp_id,
      agentid: config.value.agent_id,
      redirect_uri: encodeURIComponent(config.value.redirect_uri),
      state: config.value.state,
      href: '', // 可以自定义样式CSS URL
    })

    console.log('企业微信二维码渲染成功')
  } catch (err) {
    console.error('渲染企业微信二维码失败:', err)
    error.value = `渲染企业微信二维码失败: ${err.message || '未知错误'}`
  }
}

onMounted(() => {
  loadWeWorkConfig()
})
</script>

<style scoped>
.wework-login {
  margin-top: 0;
}

.wework-disabled {
  text-align: center;
}

.wework-qr-section {
  text-align: center;
}

.loading-container {
  padding: 40px 20px;
}

.loading-container p {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.error-container {
  padding: 20px 0;
}

.qr-container {
  display: inline-block;
  margin: 0 auto;
}

.wework-hint {
  margin-top: 16px;
  color: #606266;
  font-size: 14px;
}

/* 调整企业微信二维码容器样式 */
:deep(#wework-qr-container iframe) {
  width: 300px !important;
  height: 360px !important;
  border: none;
}
</style>
