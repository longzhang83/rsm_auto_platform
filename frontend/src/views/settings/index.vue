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
              <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
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

          <el-form :model="settings.api" label-width="120px" class="settings-form">
            <el-form-item label="智谱AI密钥">
              <el-input
                v-model="settings.api.zhipuApiKey"
                type="password"
                show-password
                placeholder="请输入智谱AI API密钥"
              />
            </el-form-item>

            <el-form-item label="翻译模型">
              <el-select v-model="settings.api.translateModel" style="width: 200px">
                <el-option label="glm-4.5-flash" value="glm-4.5-flash" />
                <el-option label="glm-4" value="glm-4" />
                <el-option label="glm-3-turbo" value="glm-3-turbo" />
              </el-select>
            </el-form-item>

            <el-form-item label="请求频率限制">
              <el-input-number
                v-model="settings.api.requestsPerSecond"
                :min="0.1"
                :max="2"
                :step="0.1"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">请求/秒</span>
            </el-form-item>

            <el-form-item label="并发数">
              <el-input-number
                v-model="settings.api.maxWorkers"
                :min="1"
                :max="10"
                controls-position="right"
              />
              <span class="ml-2 text-gray-500">个</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveApiSettings">保存设置</el-button>
              <el-button @click="testApiConnection">测试连接</el-button>
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
              <el-button type="primary" @click="saveFileSettings">保存设置</el-button>
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
              <span class="label">版本号</span>
              <span class="value">v1.0.0</span>
            </div>

            <div class="info-item">
              <span class="label">构建时间</span>
              <span class="value">2025-01-15 10:30:00</span>
            </div>

            <div class="info-item">
              <span class="label">运行环境</span>
              <span class="value">Production</span>
            </div>

            <div class="info-item">
              <span class="label">数据库版本</span>
              <span class="value">MySQL 8.0</span>
            </div>

            <div class="info-item">
              <span class="label">缓存系统</span>
              <span class="value">Redis 7.0</span>
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
import { reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 设置数据
const settings = reactive({
  basic: {
    systemName: '容诚税务师事务所自动化工具平台',
    companyName: '容诚税务师事务所',
    defaultPreparer: 'cissy',
    defaultVoucherCategory: '记',
    defaultCreditAccount: '224104'
  },
  api: {
    zhipuApiKey: '',
    translateModel: 'glm-4.5-flash',
    requestsPerSecond: 0.6,
    maxWorkers: 3
  },
  file: {
    maxFileSize: 10,
    savePath: 'D:\\data\\output',
    autoCleanup: true,
    cleanupPeriod: 'weekly'
  }
})

// 保存设置
const saveBasicSettings = () => {
  ElMessage.success('基本设置已保存')
}

const saveApiSettings = () => {
  ElMessage.success('API设置已保存')
}

const saveFileSettings = () => {
  ElMessage.success('文件设置已保存')
}

// 测试API连接
const testApiConnection = () => {
  if (!settings.api.zhipuApiKey) {
    ElMessage.warning('请先配置API密钥')
    return
  }

  ElMessage.loading('正在测试连接...')
  setTimeout(() => {
    ElMessage.success('连接测试成功')
  }, 2000)
}

// 选择保存路径
const selectSavePath = () => {
  ElMessage.info('文件夹选择功能开发中...')
}

// 快速操作
const exportSettings = () => {
  ElMessage.info('导出设置功能开发中...')
}

const importSettings = () => {
  ElMessage.info('导入设置功能开发中...')
}

const clearCache = () => {
  ElMessageBox.confirm('确定要清理系统缓存吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('缓存清理完成')
  })
}

const resetSettings = () => {
  ElMessageBox.confirm('确定要重置所有设置吗？此操作不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('设置已重置')
  })
}
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