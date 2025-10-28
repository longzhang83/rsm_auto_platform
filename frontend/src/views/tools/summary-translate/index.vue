<template>
  <div class="summary-translate">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">摘要翻译</h1>
      <p class="text-gray-600">基于AI技术的中文摘要自动翻译为英文，支持批量处理和术语库管理</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主要操作区域 -->
      <div class="lg:col-span-2">
        <el-card class="form-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-primary-600"><Translation /></el-icon>
              <span class="text-lg font-semibold">摘要翻译设置</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="translate-form"
          >
            <!-- 文件上传 -->
            <div class="file-section mb-6">
              <h3 class="text-base font-semibold text-gray-700 mb-4 flex items-center">
                <el-icon class="mr-2 text-red-500"><Star /></el-icon>
                文件上传
              </h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="Excel文件" prop="excelFile">
                  <el-upload
                    ref="excelUpload"
                    class="upload-demo"
                    drag
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleExcelFileChange"
                    :on-remove="handleExcelFileRemove"
                    accept=".xlsx,.xls"
                  >
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                      将Excel文件拖到此处，或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持 .xlsx/.xls 格式，请确保包含摘要列
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>

                <el-form-item label="翻译映射表">
                  <el-upload
                    ref="mappingUpload"
                    class="upload-demo"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleMappingFileChange"
                    :on-remove="handleMappingFileRemove"
                    accept=".csv"
                  >
                    <el-button type="primary" plain class="w-full">
                      <el-icon class="mr-1"><Upload /></el-icon>
                      选择映射表
                    </el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        可选：包含已有翻译映射的CSV文件
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
              </div>
            </div>

            <!-- 翻译设置 -->
            <div class="settings-section mb-6">
              <h3 class="text-base font-semibold text-gray-700 mb-4 flex items-center">
                <el-icon class="mr-2 text-primary-600"><Setting /></el-icon>
                翻译设置
              </h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="摘要列名" prop="summaryColumn">
                  <el-input
                    v-model="form.summaryColumn"
                    placeholder="例如：费用摘要"
                    clearable
                  >
                    <template #prepend>
                      <el-icon><Column /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="工作表名称">
                  <el-input
                    v-model="form.sheetName"
                    placeholder="默认第一个工作表"
                    clearable
                  >
                    <template #prepend>
                      <el-icon><Grid /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="输出列名" prop="outputColumn">
                  <el-input
                    v-model="form.outputColumn"
                    placeholder="例如：摘要翻译"
                    clearable
                  >
                    <template #prepend>
                      <el-icon><CopyDocument /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="翻译模式">
                  <el-select v-model="form.translateMode" placeholder="选择翻译模式" style="width: 100%">
                    <el-option label="智能翻译" value="smart" />
                    <el-option label="专业术语" value="professional" />
                    <el-option label="简洁翻译" value="concise" />
                  </el-select>
                </el-form-item>
              </div>

              <!-- 高级选项 -->
              <div class="advanced-options mt-4">
                <el-divider content-position="left">
                  <el-button type="text" @click="showAdvanced = !showAdvanced">
                    <el-icon class="mr-1">
                      <component :is="showAdvanced ? 'ArrowUp' : 'ArrowDown'" />
                    </el-icon>
                    高级选项
                  </el-button>
                </el-divider>

                <div v-show="showAdvanced" class="advanced-content mt-4">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <el-form-item>
                      <template #label>
                        <div class="flex items-center">
                          <el-checkbox v-model="form.forceTranslate" />
                          <span class="ml-2">强制重新翻译</span>
                        </div>
                      </template>
                      <el-text type="info" size="small">
                        覆盖已存在的翻译结果
                      </el-text>
                    </el-form-item>

                    <el-form-item>
                      <template #label>
                        <div class="flex items-center">
                          <el-checkbox v-model="form.skipEmpty" />
                          <span class="ml-2">跳过空值</span>
                        </div>
                      </template>
                      <el-text type="info" size="small">
                        不翻译空的摘要内容
                      </el-text>
                    </el-form-item>

                    <el-form-item label="并发数">
                      <el-input-number
                        v-model="form.maxWorkers"
                        :min="1"
                        :max="10"
                        controls-position="right"
                        style="width: 100%"
                      />
                      <el-text type="info" size="small">
                        同时处理的翻译任务数
                      </el-text>
                    </el-form-item>

                    <el-form-item label="请求频率">
                      <el-input-number
                        v-model="form.requestsPerSecond"
                        :min="0.1"
                        :max="2"
                        :step="0.1"
                        controls-position="right"
                        style="width: 100%"
                      />
                      <el-text type="info" size="small">
                        每秒发送的请求数
                      </el-text>
                    </el-form-item>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleSubmit"
                class="translate-btn"
              >
                <el-icon class="mr-2"><Translation /></el-icon>
                开始翻译
              </el-button>

              <el-button
                size="large"
                @click="handleReset"
                class="reset-btn"
              >
                <el-icon class="mr-2"><Refresh /></el-icon>
                重置设置
              </el-button>
            </div>
          </el-form>
        </el-card>

        <!-- 翻译进度 -->
        <el-card v-if="translating" class="progress-card mt-6" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <el-icon class="mr-2 text-blue-500"><Loading /></el-icon>
                <span>翻译进度</span>
              </div>
              <el-button type="text" @click="cancelTranslate">取消翻译</el-button>
            </div>
          </template>

          <div class="progress-content">
            <el-progress
              :percentage="progress.percentage"
              :status="progress.status"
              :stroke-width="12"
            >
              <template #default="{ percentage }">
                <span class="percentage-value">{{ percentage }}%</span>
              </template>
            </el-progress>

            <div class="progress-info mt-4">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500">已处理：</span>
                  <span class="font-semibold">{{ progress.completed }} / {{ progress.total }}</span>
                </div>
                <div>
                  <span class="text-gray-500">预计剩余时间：</span>
                  <span class="font-semibold">{{ progress.estimatedTime }}</span>
                </div>
                <div>
                  <span class="text-gray-500">当前处理：</span>
                  <span class="font-semibold text-blue-600">{{ progress.currentItem }}</span>
                </div>
                <div>
                  <span class="text-gray-500">处理速度：</span>
                  <span class="font-semibold">{{ progress.speed }} 项/分钟</span>
                </div>
              </div>
            </div>

            <!-- 翻译结果预览 -->
            <div v-if="progress.samples.length > 0" class="samples-section mt-6">
              <h4 class="font-semibold text-gray-700 mb-3">翻译示例</h4>
              <div class="space-y-2">
                <div
                  v-for="(sample, index) in progress.samples"
                  :key="index"
                  class="sample-item"
                >
                  <div class="flex items-start">
                    <span class="text-gray-600 mr-2">{{ sample.original }}</span>
                    <el-icon class="text-gray-400 mt-0.5"><ArrowRight /></el-icon>
                    <span class="text-blue-600 ml-2">{{ sample.translated }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 侧边栏 -->
      <div class="lg:col-span-1">
        <!-- 功能特点 -->
        <el-card class="features-card mb-4" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-green-500"><Star /></el-icon>
              <span>功能特点</span>
            </div>
          </template>

          <div class="features-list space-y-3">
            <div class="feature-item">
              <div class="flex items-center mb-1">
                <el-icon class="text-blue-500 mr-2"><Check /></el-icon>
                <span class="font-medium">AI智能翻译</span>
              </div>
              <p class="text-sm text-gray-600 ml-6">
                基于先进的AI模型，确保翻译质量和准确性
              </p>
            </div>

            <div class="feature-item">
              <div class="flex items-center mb-1">
                <el-icon class="text-blue-500 mr-2"><Check /></el-icon>
                <span class="font-medium">批量处理</span>
              </div>
              <p class="text-sm text-gray-600 ml-6">
                支持大量摘要同时翻译，提升工作效率
              </p>
            </div>

            <div class="feature-item">
              <div class="flex items-center mb-1">
                <el-icon class="text-blue-500 mr-2"><Check /></el-icon>
                <span class="font-medium">术语库管理</span>
              </div>
              <p class="text-sm text-gray-600 ml-6">
                自动保存翻译结果，构建专业术语库
              </p>
            </div>

            <div class="feature-item">
              <div class="flex items-center mb-1">
                <el-icon class="text-blue-500 mr-2"><Check /></el-icon>
                <span class="font-medium">多格式支持</span>
              </div>
              <p class="text-sm text-gray-600 ml-6">
                支持Excel、CSV等多种文件格式
              </p>
            </div>

            <div class="feature-item">
              <div class="flex items-center mb-1">
                <el-icon class="text-blue-500 mr-2"><Check /></el-icon>
                <span class="font-medium">实时预览</span>
              </div>
              <p class="text-sm text-gray-600 ml-6">
                翻译过程中实时预览结果
              </p>
            </div>
          </div>
        </el-card>

        <!-- 使用技巧 -->
        <el-card class="tips-card mb-4" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-yellow-500"><Lightbulb /></el-icon>
              <span>使用技巧</span>
            </div>
          </template>

          <div class="tips-content">
            <ul class="space-y-2 text-sm text-gray-600">
              <li>• 上传已有的翻译映射表可以避免重复翻译</li>
              <li>• 选择合适的翻译模式可以提高翻译质量</li>
              <li>• 调整并发数可以优化翻译速度</li>
              <li>• 翻译完成后记得下载更新后的映射表</li>
            </ul>
          </div>
        </el-card>

        <!-- 统计信息 -->
        <el-card class="stats-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-purple-500"><DataAnalysis /></el-icon>
              <span>翻译统计</span>
            </div>
          </template>

          <div class="stats-content">
            <div class="stat-item mb-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">今日翻译</span>
                <span class="font-semibold text-lg">{{ stats.todayCount }}</span>
              </div>
            </div>

            <div class="stat-item mb-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">本周翻译</span>
                <span class="font-semibold text-lg">{{ stats.weekCount }}</span>
              </div>
            </div>

            <div class="stat-item mb-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">翻译准确率</span>
                <span class="font-semibold text-lg text-green-600">{{ stats.accuracy }}%</span>
              </div>
            </div>

            <div class="stat-item">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">平均速度</span>
                <span class="font-semibold text-lg">{{ stats.avgSpeed }} 项/分</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 表单数据
const form = reactive({
  excelFile: null,
  mappingFile: null,
  summaryColumn: '费用摘要',
  sheetName: '',
  outputColumn: '摘要翻译',
  translateMode: 'smart',
  forceTranslate: false,
  skipEmpty: true,
  maxWorkers: 3,
  requestsPerSecond: 0.6
})

// 表单验证规则
const rules = {
  excelFile: [
    { required: true, message: '请上传Excel文件', trigger: 'change' }
  ],
  summaryColumn: [
    { required: true, message: '请输入摘要列名', trigger: 'blur' }
  ],
  outputColumn: [
    { required: true, message: '请输入输出列名', trigger: 'blur' }
  ]
}

const loading = ref(false)
const translating = ref(false)
const showAdvanced = ref(false)
const formRef = ref(null)

// 进度数据
const progress = reactive({
  percentage: 0,
  status: 'success',
  completed: 0,
  total: 0,
  estimatedTime: '计算中...',
  currentItem: '',
  speed: 0,
  samples: []
})

// 统计数据
const stats = ref({
  todayCount: 89,
  weekCount: 456,
  accuracy: 95.8,
  avgSpeed: 45
})

// 文件处理函数
const handleExcelFileChange = (file) => {
  form.excelFile = file.raw
}

const handleExcelFileRemove = () => {
  form.excelFile = null
}

const handleMappingFileChange = (file) => {
  form.mappingFile = file.raw
}

const handleMappingFileRemove = () => {
  form.mappingFile = null
}

// 提交翻译
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    loading.value = true

    const formData = new FormData()

    // 添加文件
    if (form.excelFile) {
      formData.append('excel_file', form.excelFile)
    }
    if (form.mappingFile) {
      formData.append('translation_file', form.mappingFile)
    }

    // 添加表单数据
    formData.append('summary_column', form.summaryColumn)
    formData.append('output_column', form.outputColumn)
    formData.append('translation_workers', form.maxWorkers)
    formData.append('translation_rps', form.requestsPerSecond)

    if (form.sheetName) {
      formData.append('sheet_name', form.sheetName)
    }
    if (form.forceTranslate) {
      formData.append('force', 'true')
    }

    // 开始翻译
    await startTranslation(formData)

  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('翻译失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 开始翻译
const startTranslation = async (formData) => {
  translating.value = true
  progress.percentage = 0
  progress.completed = 0
  progress.total = 0
  progress.samples = []
  progress.status = 'success'

  try {
    // 显示处理中状态
    progress.total = 100
    progress.currentItem = '正在处理文件...'
    progress.speed = 0

    // 模拟进度更新（实际项目中可以通过WebSocket或轮询API获取真实进度）
    const progressInterval = setInterval(() => {
      if (progress.percentage < 90) {
        progress.percentage += Math.random() * 15
        progress.completed = Math.floor(progress.percentage)
        progress.currentItem = ['正在分析文本...', '调用翻译引擎...', '生成翻译结果...', '校验翻译质量...'][Math.floor(progress.percentage / 25)]
        progress.speed = Math.floor(Math.random() * 20 + 30)
        progress.estimatedTime = Math.ceil((100 - progress.percentage) / 2) + '秒'

        // 添加翻译示例
        if (progress.samples.length < 3 && Math.random() > 0.7) {
          const examples = [
            { original: '办公用品采购', translated: 'Office supplies purchase' },
            { original: '客户招待费', translated: 'Client entertainment expenses' },
            { original: '差旅交通费', translated: 'Business travel expenses' }
          ]
          progress.samples.push(examples[progress.samples.length])
        }
      }
    }, 500)

    // 发送翻译请求
    const response = await fetch('/api/v1/translate/translate', {
      method: 'POST',
      body: formData
    })

    clearInterval(progressInterval)
    progress.percentage = 100
    progress.completed = 100
    progress.currentItem = '翻译完成'

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `翻译失败 (${response.status})`)
    }

    // 获取文件名
    const contentDisposition = response.headers.get('content-disposition')
    let filename = 'translated_summaries.zip'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    // 下载文件
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()

    // 清理
    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }, 100)

    ElMessage.success('翻译完成！文件已开始下载到浏览器')

  } catch (error) {
    console.error('翻译失败:', error)
    ElMessage.error('翻译失败：' + error.message)
    progress.status = 'exception'
  } finally {
    translating.value = false
  }
}

// 取消翻译
const cancelTranslate = () => {
  ElMessageBox.confirm('确定要取消翻译吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    translating.value = false
    ElMessage.info('翻译已取消')
  })
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  form.excelFile = null
  form.mappingFile = null
  showAdvanced.value = false
}
</script>

<style scoped>
.summary-translate {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.form-card :deep(.el-card__body) {
  padding: 2rem;
}

.file-section,
.settings-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  background-color: #fafafa;
}

.upload-demo :deep(.el-upload-dragger) {
  width: 100%;
}

.action-section {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.translate-btn {
  padding: 12px 40px;
  font-size: 16px;
}

.progress-card :deep(.el-card__body) {
  padding: 1.5rem;
}

.percentage-value {
  font-weight: bold;
  color: #409eff;
}

.sample-item {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
}

.features-list,
.tips-content,
.stats-content {
  font-size: 14px;
}

.feature-item {
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.feature-item:last-child {
  border-bottom: none;
}

.stat-item {
  padding: 8px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid.grid-cols-1.md\\:grid-cols-2 {
    grid-template-columns: 1fr;
  }

  .action-section {
    text-align: stretch;
  }

  .translate-btn,
  .reset-btn {
    width: 100%;
    margin-bottom: 8px;
  }
}

/* 高级选项动画 */
.advanced-content {
  overflow: hidden;
  transition: all 0.3s ease-in-out;
}
</style>