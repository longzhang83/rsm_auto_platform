<template>
  <div class="wework-login">
    <div class="divider">
      <span>或</span>
    </div>

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

      <div v-else id="wework-qr-container" class="qr-container"></div>

      <p class="wework-hint">使用企业微信扫码登录</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import request from '@/api/request'

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

    // 等待下一个tick，确保DOM已更新
    setTimeout(() => {
      initWeWorkQR()
    }, 100)
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

  // 加载企业微信JS SDK
  if (typeof window.WwLogin === 'undefined') {
    const script = document.createElement('script')
    script.src = 'https://rescdn.qqmail.com/node/ww/wwopenmng/js/sso/wwLogin-1.0.0.js'
    script.onload = () => {
      renderQRCode()
    }
    script.onerror = () => {
      error.value = '加载企业微信SDK失败'
      loading.value = false
    }
    document.head.appendChild(script)
  } else {
    renderQRCode()
  }
}

const renderQRCode = () => {
  try {
    // 清空容器
    const container = document.getElementById('wework-qr-container')
    if (container) {
      container.innerHTML = ''
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

    loading.value = false
  } catch (err) {
    console.error('渲染企业微信二维码失败:', err)
    error.value = '渲染企业微信二维码失败'
    loading.value = false
  }
}

onMounted(() => {
  loadWeWorkConfig()
})
</script>

<style scoped>
.wework-login {
  margin-top: 30px;
}

.divider {
  position: relative;
  text-align: center;
  margin: 30px 0;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e4e7ed;
}

.divider span {
  position: relative;
  display: inline-block;
  padding: 0 15px;
  background: white;
  color: #909399;
  font-size: 14px;
  z-index: 1;
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
