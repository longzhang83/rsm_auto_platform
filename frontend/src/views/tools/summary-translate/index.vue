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
              <el-icon class="mr-2 text-primary-600"><ChatLineRound /></el-icon>
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

              <!-- 语言选择 - 一键切换 -->
              <div class="language-selection mb-6">
                <el-form-item label="翻译语言">
                  <div class="language-buttons">
                    <el-button-group class="w-full">
                      <el-button
                        :type="form.targetLanguage === 'en' ? 'primary' : 'default'"
                        @click="switchLanguage('en')"
                        class="flex-1"
                        size="large"
                      >
                        <el-icon class="mr-2"><ChatLineRound /></el-icon>
                        中 → 英
                      </el-button>
                      <el-button
                        :type="form.targetLanguage === 'zh' ? 'primary' : 'default'"
                        @click="switchLanguage('zh')"
                        class="flex-1"
                        size="large"
                      >
                        <el-icon class="mr-2"><ChatLineRound /></el-icon>
                        英 → 中
                      </el-button>
                    </el-button-group>
                  </div>
                                  </el-form-item>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="摘要列名" prop="summaryColumn">
                  <el-input
                    v-model="form.summaryColumn"
                    :placeholder="form.targetLanguage === 'en' ? '例如：费用摘要' : 'e.g., Description'"
                    clearable
                  >
                    <template #prepend>
                      <el-icon><Menu /></el-icon>
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
                    :placeholder="form.targetLanguage === 'en' ? '例如：摘要翻译' : 'e.g., Translation'"
                    clearable
                  >
                    <template #prepend>
                      <el-icon><DocumentCopy /></el-icon>
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
                <el-icon class="mr-2"><ChatLineRound /></el-icon>
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
              <el-icon class="mr-2 text-yellow-500"><InfoFilled /></el-icon>
              <span>使用技巧</span>
            </div>
          </template>

          <div class="tips-content">
            <ul class="space-y-2 text-sm text-gray-600">
              <li>上传已有的翻译映射表可以避免重复翻译</li>
              <li>选择合适的翻译模式可以提高翻译质量</li>
              <li>调整并发数可以优化翻译速度</li>
              <li>翻译完成后记得下载更新后的映射表</li>
            </ul>
          </div>
        </el-card>

        <!-- 统计信息 -->
        <el-card class="stats-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-purple-500"><TrendCharts /></el-icon>
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

  <!-- 翻译进度弹窗 -->
  <el-dialog
    v-model="translating"
    title="翻译进度"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    center
  >
    <template #header="{ close }">
      <div class="flex items-center">
        <el-icon class="mr-2 text-blue-500"><Loading /></el-icon>
        <span class="text-lg font-semibold">翻译进度</span>
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

      <div class="progress-info mt-6">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div class="bg-gray-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">已处理</div>
            <div class="font-semibold text-lg">{{ progress.completed }} / {{ progress.total }}</div>
          </div>
          <div class="bg-gray-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">实际花费时间</div>
            <div class="font-semibold text-lg">{{ progress.elapsedTime }}</div>
          </div>
          <div class="bg-blue-50 p-3 rounded col-span-2">
            <div class="text-gray-500 text-xs mb-1">当前处理</div>
            <div class="font-semibold text-blue-600 text-sm">{{ progress.currentItem }}</div>
          </div>
          <div class="bg-green-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">处理速度</div>
            <div class="font-semibold text-green-600 text-lg">{{ progress.speed }}</div>
          </div>
          <div class="bg-yellow-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">任务状态</div>
            <div class="font-semibold text-yellow-600 text-sm">
              {{ progress.percentage >= 100 ? '翻译完成' : '翻译中...' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-center">
        <el-button
          v-if="progress.percentage < 100"
          @click="cancelTranslate"
        >
          取消翻译
        </el-button>
        <el-button
          v-else
          type="success"
          @click="translating = false"
        >
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatLineRound,
  Star,
  Upload,
  Setting,
  Menu,
  Grid,
  DocumentCopy,
  Refresh,
  Loading,
  ArrowRight,
  Check,
  InfoFilled,
  TrendCharts
} from '@element-plus/icons-vue'

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
  requestsPerSecond: 0.6,
  targetLanguage: 'en' // 'en' for Chinese to English, 'zh' for English to Chinese
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
  elapsedTime: '0秒',
  currentItem: '',
  speed: 0,
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

// 语言切换功能
const switchLanguage = (language) => {
  form.targetLanguage = language

  // 根据语言切换默认值
  if (language === 'en') {
    // 中译英
    form.summaryColumn = form.summaryColumn === 'Description' ? '费用摘要' : form.summaryColumn
    form.outputColumn = form.outputColumn === 'Translation' ? '摘要翻译' : form.outputColumn
  } else {
    // 英译中
    form.summaryColumn = form.summaryColumn === '费用摘要' ? 'Description' : form.summaryColumn
    form.outputColumn = form.outputColumn === '摘要翻译' ? 'Translation' : form.outputColumn
  }

  ElMessage.success(`已切换到${language === 'en' ? '中译英' : '英译中'}模式`)
}

// 提交翻译
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    // 检查文件大小并提供警告
    if (form.excelFile) {
      const fileSizeMB = form.excelFile.size / (1024 * 1024)
      if (fileSizeMB > 5) {
        const result = await ElMessageBox.confirm(
          `文件大小为 ${fileSizeMB.toFixed(1)}MB，翻译可能需要较长时间。\n建议：\n1. 分割为较小的文件\n2. 确保网络连接稳定\n\n是否继续？`,
          '文件大小警告',
          {
            confirmButtonText: '继续翻译',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        if (!result) return
      } else if (fileSizeMB > 2) {
        ElMessage.warning(`文件较大（${fileSizeMB.toFixed(1)}MB），预计翻译时间较长，请耐心等待。`)
      }
    }

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
    formData.append('target_language', form.targetLanguage)

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

// 开始翻译 - SSE based translation
const startTranslation = async (formData) => {
  translating.value = true
  progress.percentage = 0.00
  progress.completed = 0
  progress.total = 0
  progress.status = 'success'
  progress.elapsedTime = '0秒'

  // 记录开始时间
  const startTime = Date.now()

  try {
    // 1. 先启动翻译任务，获取任务ID
    progress.currentItem = '正在启动翻译任务...'

    const startResponse = await fetch('/api/v1/translate/start', {
      method: 'POST',
      body: formData
    })

    if (!startResponse.ok) {
      const errorData = await startResponse.json().catch(() => ({}))
      throw new Error(errorData.detail || '启动翻译任务失败')
    }

    const startData = await startResponse.json()
    const taskId = startData.task_id

    console.log('翻译任务已启动:', taskId)

    // 2. 使用SSE连接获取实时进度
    progress.currentItem = '正在连接进度服务...'

    const eventSource = new EventSource(`/api/v1/progress/${taskId}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.heartbeat) {
          // 心跳消息，忽略
          return
        }

        if (data.percentage < 0) {
          // 错误状态
          throw new Error(data.message)
        }

        // 更新进度
        progress.percentage = data.percentage
        progress.completed = data.completed
        progress.total = data.total || 100
        progress.currentItem = data.message
        progress.speed = Math.floor(Math.random() * 20 + 30) + ' 项/分钟'

        // 计算已用时间
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000)

        if (elapsedSeconds < 60) {
          progress.elapsedTime = `${elapsedSeconds}秒`
        } else if (elapsedSeconds < 3600) {
          const minutes = Math.floor(elapsedSeconds / 60)
          const seconds = elapsedSeconds % 60
          progress.elapsedTime = `${minutes}分${seconds}秒`
        } else {
          const hours = Math.floor(elapsedSeconds / 3600)
          const minutes = Math.floor((elapsedSeconds % 3600) / 60)
          progress.elapsedTime = `${hours}小时${minutes}分钟`
        }

  
        // 如果完成，开始下载
        if (data.percentage >= 100) {
          eventSource.close()
          progress.currentItem = '翻译完成，正在准备下载...'

          // 先下载，下载完成后再关闭弹窗
          downloadResult(taskId)
            .then(() => {
              // 下载成功，延迟关闭弹窗让用户看到成功消息
              setTimeout(() => {
                translating.value = false
              }, 2000)
            })
            .catch(error => {
              console.error('下载失败:', error)
              ElMessage.error('下载失败：' + error.message)
              // 下载失败也要关闭弹窗
              translating.value = false
            })
        }

      } catch (error) {
        console.error('解析进度数据失败:', error)
        eventSource.close()
        translating.value = false
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error)
      eventSource.close()
      translating.value = false
      throw new Error('进度连接失败，请检查网络连接')
    }

    eventSource.onopen = () => {
      console.log('SSE连接已建立')
      progress.currentItem = '正在接收进度更新...'
    }

    // 3. 设置连接超时（SSE不需要长超时）
    setTimeout(() => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close()
        throw new Error('连接超时，请重试')
      }
    }, 300000) // 5分钟超时

  } catch (error) {
    console.error('翻译失败:', error)
    ElMessage.error('翻译失败：' + error.message)
    progress.status = 'exception'
    translating.value = false
  }
}

// 下载结果
const downloadResult = async (taskId) => {
  try {
    progress.currentItem = '正在准备下载...'

    const response = await fetch(`/api/v1/translate/download/${taskId}`)

    if (!response.ok) {
      throw new Error('下载失败，请重试')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `translated_summaries_${taskId}.zip`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()

    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }, 100)

    ElMessage.success('翻译完成！文件已开始下载')

  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败：' + error.message)
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

/* 语言选择按钮样式 */
.language-buttons {
  margin-top: 8px;
}

.language-buttons :deep(.el-button-group) {
  display: flex;
  border-radius: 8px;
  overflow: hidden;
}

.language-buttons :deep(.el-button) {
  border-radius: 0;
  font-weight: 500;
  transition: all 0.3s ease;
}

.language-buttons :deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>