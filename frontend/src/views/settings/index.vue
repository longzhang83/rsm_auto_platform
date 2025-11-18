<template>
  <div class="settings-page">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">系统设置</h1>
      <p class="text-gray-600">配置平台参数和个人偏好设置</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主要设置区域 -->
      <div class="lg:col-span-2 space-y-6">
        <!-- 基本设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-blue-500"><Setting /></el-icon>
              <span class="text-lg font-semibold">基本设置</span>
            </div>
          </template>

          <el-form :model="settings.basic" label-width="120px" class="settings-form">
            <el-form-item label="系统名称">
              <el-input v-model="settings.basic.systemName" />
            </el-form-item>

            <el-form-item label="公司名称">
              <el-input v-model="settings.basic.companyName" />
            </el-form-item>

            <el-form-item label="默认制单人">
              <el-input v-model="settings.basic.defaultPreparer" />
            </el-form-item>

            <el-form-item label="默认凭证类别">
              <el-select v-model="settings.basic.defaultVoucherCategory" style="width: 200px">
                <el-option label="记" value="记" />
                <el-option label="收" value="收" />
                <el-option label="付" value="付" />
                <el-option label="转" value="转" />
              </el-select>
            </el-form-item>

            <el-form-item label="默认贷方科目">
              <el-input v-model="settings.basic.defaultCreditAccount" style="width: 200px" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings" :disabled="!isAdmin">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- API设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-green-500"><Key /></el-icon>
              <span class="text-lg font-semibold">API设置</span>
            </div>
          </template>

          <el-form :model="settings.api" label-width="150px" class="settings-form">
            <el-form-item label="单个API密钥">
              <el-input
                v-model="settings.api.zhipuApiKey"
                type="password"
                show-password
                placeholder="单个API密钥（可选）"
              />
            </el-form-item>

            <el-form-item label="多个API密钥">
              <el-input
                v-model="settings.api.zhipuApiKeys"
                type="textarea"
                :rows="3"
                placeholder="多个API密钥，用逗号分隔（推荐用于负载均衡）"
              />
              <div class="text-gray-500 text-xs mt-1">支持多个密钥，系统会自动负载均衡</div>
            </el-form-item>

            <el-form-item label="翻译模型">
              <el-select v-model="settings.api.zhipuModel" style="width: 200px">
                <el-option label="glm-4.5-flash" value="glm-4.5-flash" />
                <el-option label="glm-4" value="glm-4" />
                <el-option label="glm-3-turbo" value="glm-3-turbo" />
              </el-select>
            </el-form-item>

            <el-form-item label="单账号速率限制">
              <el-input-number
                v-model="settings.api.zhipuRps"
                :min="0.1"
                :max="30"
                :step="0.1"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">请求/秒/账号</span>
            </el-form-item>

            <el-form-item label="翻译并发数">
              <el-input-number
                v-model="settings.api.translationMaxWorkers"
                :min="1"
                :max="50"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">个</span>
            </el-form-item>

            <el-form-item label="翻译总速率">
              <el-input-number
                v-model="settings.api.translationRequestsPerSecond"
                :min="0.1"
                :max="100"
                :step="0.1"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">请求/秒</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveApiSettings" :disabled="!isAdmin">保存设置</el-button>
              <el-button @click="testApiConnection" :disabled="!isAdmin">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 文件设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-purple-500"><Folder /></el-icon>
              <span class="text-lg font-semibold">文件设置</span>
            </div>
          </template>

          <el-form :model="settings.file" label-width="120px" class="settings-form">
            <el-form-item label="文件大小限制">
              <el-input-number
                v-model="settings.file.maxFileSize"
                :min="1"
                :max="100"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">MB</span>
            </el-form-item>

            <el-form-item label="保存路径">
              <el-input v-model="settings.file.savePath" readonly>
                <template #append>
                  <el-button @click="selectSavePath">选择</el-button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="自动清理">
              <el-switch
                v-model="settings.file.autoCleanup"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>

            <el-form-item v-if="settings.file.autoCleanup" label="清理周期">
              <el-select v-model="settings.file.cleanupPeriod" style="width: 150px">
                <el-option label="每天" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveFileSettings" :disabled="!isAdmin">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- 侧边栏 -->
      <div class="lg:col-span-1 space-y-6">
        <!-- 系统信息 -->
        <el-card class="info-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-orange-500"><InfoFilled /></el-icon>
              <span>系统信息</span>
            </div>
          </template>

          <div class="system-info">
            <div class="info-item">
              <span class="label">应用名称</span>
              <span class="value">{{ systemInfo.app_name || '-' }}</span>
            </div>

            <div class="info-item">
              <span class="label">版本号</span>
              <span class="value">{{ systemInfo.app_version || 'v1.0.0' }}</span>
            </div>

            <div class="info-item">
              <span class="label">运行环境</span>
              <span class="value">{{ systemInfo.environment || 'Production' }}</span>
            </div>

            <div class="info-item">
              <span class="label">Python版本</span>
              <span class="value">{{ systemInfo.python_version || '-' }}</span>
            </div>

            <div class="info-item">
              <span class="label">数据库</span>
              <span class="value">{{ systemInfo.database || '-' }}</span>
            </div>

            <div class="info-item">
              <span class="label">缓存系统</span>
              <span class="value">{{ systemInfo.cache_system || '-' }}</span>
            </div>
          </div>
        </el-card>

        <!-- 快速操作 -->
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-red-500"><Operation /></el-icon>
              <span>快速操作</span>
            </div>
          </template>

          <div class="quick-actions space-y-3">
            <el-button type="primary" plain class="w-full" @click="exportSettings">
              <el-icon class="mr-2"><Download /></el-icon>
              导出设置
            </el-button>

            <el-button type="success" plain class="w-full" @click="importSettings">
              <el-icon class="mr-2"><Upload /></el-icon>
              导入设置
            </el-button>

            <el-button type="warning" plain class="w-full" @click="clearCache">
              <el-icon class="mr-2"><Delete /></el-icon>
              清理缓存
            </el-button>

            <el-button type="danger" plain class="w-full" @click="resetSettings">
              <el-icon class="mr-2"><RefreshLeft /></el-icon>
              重置设置
            </el-button>
          </div>
        </el-card>

        <!-- 帮助链接 -->
        <el-card class="help-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-blue-500"><QuestionFilled /></el-icon>
              <span>帮助支持</span>
            </div>
          </template>

          <div class="help-links space-y-2">
            <a href="#" class="help-link">
              <el-icon class="mr-2"><Document /></el-icon>
              使用文档
            </a>

            <a href="#" class="help-link">
              <el-icon class="mr-2"><VideoPlay /></el-icon>
              视频教程
            </a>

            <a href="#" class="help-link">
              <el-icon class="mr-2"><ChatDotRound /></el-icon>
              在线客服
            </a>

            <a href="#" class="help-link">
              <el-icon class="mr-2"><Phone /></el-icon>
              联系支持
            </a>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const systemInfo = ref({})

// 设置数据
const settings = reactive({
  basic: {
    systemName: '',
    companyName: '',
    defaultPreparer: '',
    defaultVoucherCategory: '记',
    defaultCreditAccount: ''
  },
  api: {
    zhipuApiKey: '',
    zhipuApiKeys: '',
    zhipuModel: 'glm-4.5-flash',
    zhipuRps: 18.0,
    translationMaxWorkers: 12,
    translationRequestsPerSecond: 30.0
  },
  file: {
    maxFileSize: 50,
    allowedExtensions: ['.xlsx', '.xls', '.csv']
  },
  email: {
    smtpServer: '',
    smtpPort: 587,
    smtpUsername: '',
    smtpPassword: '',
    emailFromName: '',
    allowedEmailDomains: '',
    verificationCodeExpiry: 300
  },
  wework: {
    weworkEnabled: false,
    weworkCorpId: '',
    weworkAgentId: '',
    weworkSecret: '',
    weworkCallbackUrl: ''
  },
  log: {
    logLevel: 'INFO',
    logEnableConsole: true,
    logEnableFile: true,
    logEnableJson: false,
    logColoredConsole: true,
    logMaxFileSize: 10485760,
    logBackupCount: 5,
    logRetentionDays: 30
  }
})

// 检查是否为管理员
const isAdmin = computed(() => authStore.user?.is_admin || false)

// 加载系统设置
const loadSettings = async () => {
  loading.value = true
  try {
    const data = await request.get('/settings')

    // 更新设置数据
    if (data.basic) {
      settings.basic.systemName = data.basic.system_name
      settings.basic.companyName = data.basic.company_name
      settings.basic.defaultPreparer = data.basic.default_preparer
      settings.basic.defaultVoucherCategory = data.basic.default_voucher_category
      settings.basic.defaultCreditAccount = data.basic.default_credit_account
    }

    if (data.api) {
      settings.api.zhipuApiKey = data.api.zhipu_api_key || ''
      settings.api.zhipuApiKeys = data.api.zhipu_api_keys || ''
      settings.api.zhipuModel = data.api.zhipu_model || 'glm-4.5-flash'
      settings.api.zhipuRps = data.api.zhipu_rps
      settings.api.translationMaxWorkers = data.api.translation_max_workers
      settings.api.translationRequestsPerSecond = data.api.translation_requests_per_second
    }

    if (data.file) {
      settings.file.maxFileSize = data.file.max_file_size / (1024 * 1024) // 转换为MB
      settings.file.allowedExtensions = data.file.allowed_extensions || []
    }

    if (data.email) {
      settings.email.smtpServer = data.email.smtp_server
      settings.email.smtpPort = data.email.smtp_port
      settings.email.smtpUsername = data.email.smtp_username || ''
      settings.email.smtpPassword = data.email.smtp_password || ''
      settings.email.emailFromName = data.email.email_from_name
      settings.email.allowedEmailDomains = data.email.allowed_email_domains
      settings.email.verificationCodeExpiry = data.email.verification_code_expiry
    }

    if (data.wework) {
      settings.wework.weworkEnabled = data.wework.wework_enabled
      settings.wework.weworkCorpId = data.wework.wework_corp_id || ''
      settings.wework.weworkAgentId = data.wework.wework_agent_id || ''
      settings.wework.weworkSecret = data.wework.wework_secret || ''
      settings.wework.weworkCallbackUrl = data.wework.wework_callback_url || ''
    }

    if (data.log) {
      settings.log.logLevel = data.log.log_level
      settings.log.logEnableConsole = data.log.log_enable_console
      settings.log.logEnableFile = data.log.log_enable_file
      settings.log.logEnableJson = data.log.log_enable_json
      settings.log.logColoredConsole = data.log.log_colored_console
      settings.log.logMaxFileSize = data.log.log_max_file_size
      settings.log.logBackupCount = data.log.log_backup_count
      settings.log.logRetentionDays = data.log.log_retention_days
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

// 加载系统信息
const loadSystemInfo = async () => {
  try {
    const data = await request.get('/settings/info')
    systemInfo.value = data
  } catch (error) {
    console.error('加载系统信息失败:', error)
  }
}

// 保存设置
const saveBasicSettings = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以修改设置')
    return
  }

  try {
    await request.put('/settings', {
      basic: {
        system_name: settings.basic.systemName,
        company_name: settings.basic.companyName,
        default_preparer: settings.basic.defaultPreparer,
        default_voucher_category: settings.basic.defaultVoucherCategory,
        default_credit_account: settings.basic.defaultCreditAccount
      }
    })
    ElMessage.success('基本设置已保存')
  } catch (error) {
    console.error('保存基本设置失败:', error)
    ElMessage.error('保存基本设置失败')
  }
}

const saveApiSettings = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以修改设置')
    return
  }

  try {
    await request.put('/settings', {
      api: {
        zhipu_api_key: settings.api.zhipuApiKey || null,
        zhipu_api_keys: settings.api.zhipuApiKeys || null,
        zhipu_model: settings.api.zhipuModel || null,
        zhipu_rps: settings.api.zhipuRps,
        translation_max_workers: settings.api.translationMaxWorkers,
        translation_requests_per_second: settings.api.translationRequestsPerSecond
      }
    })
    ElMessage.success('API设置已保存')
  } catch (error) {
    console.error('保存API设置失败:', error)
    ElMessage.error('保存API设置失败')
  }
}

const saveFileSettings = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以修改设置')
    return
  }

  try {
    await request.put('/settings', {
      file: {
        max_file_size: settings.file.maxFileSize * 1024 * 1024, // 转换为字节
        allowed_extensions: settings.file.allowedExtensions
      }
    })
    ElMessage.success('文件设置已保存')
  } catch (error) {
    console.error('保存文件设置失败:', error)
    ElMessage.error('保存文件设置失败')
  }
}

// 测试API连接
const testApiConnection = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以测试API')
    return
  }

  const apiKey = settings.api.zhipuApiKey || settings.api.zhipuApiKeys?.split(',')[0]
  if (!apiKey) {
    ElMessage.warning('请先配置API密钥')
    return
  }

  const loadingMsg = ElMessage.loading('正在测试连接...')
  try {
    const result = await request.post('/settings/test-api', {
      api_key: apiKey.trim(),
      model: settings.api.zhipuModel
    })

    loadingMsg.close()
    if (result.success) {
      ElMessage.success(`连接测试成功 (延迟: ${result.latency}秒)`)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    loadingMsg.close()
    console.error('测试API连接失败:', error)
    ElMessage.error('测试API连接失败')
  }
}

// 选择保存路径
const selectSavePath = () => {
  ElMessage.info('文件路径在服务器上配置，无需客户端选择')
}

// 快速操作
const exportSettings = async () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以导出设置')
    return
  }

  try {
    const result = await request.post('/settings/export')

    // 下载JSON文件
    const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `settings-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    ElMessage.success('设置导出成功')
  } catch (error) {
    console.error('导出设置失败:', error)
    ElMessage.error('导出设置失败')
  }
}

const importSettings = () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以导入设置')
    return
  }

  ElMessage.info('导入设置功能开发中...')
}

const clearCache = () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以清理缓存')
    return
  }

  ElMessageBox.confirm('确定要清理翻译缓存吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const result = await request.post('/settings/clear-cache')
      if (result.success) {
        ElMessage.success(`缓存清理完成，共清理 ${result.cleared_items} 条缓存`)
      } else {
        ElMessage.error(result.message)
      }
    } catch (error) {
      console.error('清理缓存失败:', error)
      ElMessage.error('清理缓存失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

const resetSettings = () => {
  if (!isAdmin.value) {
    ElMessage.warning('只有管理员可以重置设置')
    return
  }

  ElMessageBox.confirm('确定要重置所有设置吗？此操作不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    loadSettings()
    ElMessage.success('设置已重置')
  }).catch(() => {
    // 用户取消
  })
}

// 组件挂载时加载数据
onMounted(() => {
  loadSettings()
  loadSystemInfo()
})
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.settings-card :deep(.el-card__body) {
  padding: 1.5rem;
}

.settings-form {
  max-width: 600px;
}

.system-info {
  space-y: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #666;
  font-weight: 500;
}

.info-item .value {
  color: #333;
  font-weight: 600;
}

.quick-actions .el-button {
  justify-content: flex-start;
}

.help-links {
  space-y: 0.5rem;
}

.help-link {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  color: #666;
  text-decoration: none;
  transition: color 0.3s ease;
}

.help-link:hover {
  color: #409eff;
}
</style>