<template>
  <div class="bank-to-voucher">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">银行流水转凭证</h1>
      <p class="text-gray-600">将银行流水数据转化为会计凭证数据，方便企业进行财务核算和报表生成</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主要操作区域 -->
      <div class="lg:col-span-2">
        <el-card class="form-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-brand-600"><CreditCard /></el-icon>
              <span class="text-lg font-semibold">银行流水转凭证</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="voucher-form"
          >
            <!-- 客户选择 -->
            <el-form-item label="客户名称" prop="customerName">
              <el-select
                v-model="form.customerName"
                placeholder="请选择客户"
                style="width: 100%"
                :loading="loadingCustomers"
                @change="handleCustomerChange"
              >
                <el-option
                  v-for="customer in customers"
                  :key="customer.name || customer"
                  :label="customer.name || customer"
                  :value="customer.name || customer"
                />
              </el-select>
            </el-form-item>

            <!-- 银行选择 -->
            <el-form-item v-if="form.customerName" label="银行名称" prop="bankName">
              <el-select
                v-model="form.bankName"
                placeholder="请选择银行（可选）"
                style="width: 100%"
                :loading="loadingBanks"
                @change="handleBankChange"
                clearable
                :no-data-text="loadingBanks ? '加载中...' : '该客户暂无银行配置，将使用通用配置'"
              >
                <el-option
                  v-for="bank in availableBanks"
                  :key="bank"
                  :label="bank"
                  :value="bank"
                />
              </el-select>
              <div class="mt-1 text-xs text-gray-500">
                选择银行可以获得更精确的映射配置，如无匹配银行将使用通用配置
              </div>
            </el-form-item>

            <!-- 银行流水文件上传 -->
            <el-form-item label="银行流水文件" prop="bankStatementFile">
              <el-upload
                ref="bankStatementUpload"
                class="upload-demo"
                drag
                :auto-upload="false"
                :limit="1"
                :on-change="handleBankStatementFileChange"
                :on-remove="handleBankStatementFileRemove"
                accept=".xlsx,.xls,.csv"
                :before-upload="beforeFileUpload"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .xlsx/.xls/.csv 格式，文件大小不超过 10MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>

  
            <!-- 翻译设置 -->
            <el-divider content-position="left">
              <span class="text-sm font-medium text-gray-700">翻译设置</span>
            </el-divider>
            <el-form-item>
              <div class="translation-setting">
                <div class="setting-header">
                  <el-switch
                    v-model="form.enableTranslation"
                    active-text="启用翻译"
                    inactive-text="跳过翻译"
                    size="default"
                  />
                </div>
                <div class="setting-description">
                  <div v-if="form.enableTranslation" class="status-enabled">
                    <div class="status-icon">✅</div>
                    <div class="status-text">
                      <div class="status-title">翻译已启用</div>
                      <div class="status-detail">将生成中英双语格式的摘要</div>
                    </div>
                  </div>
                  <div v-else class="status-disabled">
                    <div class="status-icon">⏸️</div>
                    <div class="status-text">
                      <div class="status-title">翻译已跳过</div>
                      <div class="status-detail">将使用原始中文摘要格式</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-form-item>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                :loading="generating"
                @click="generateVouchers"
                :disabled="!canGenerate"
              >
                <el-icon class="mr-1"><DocumentCopy /></el-icon>
                生成凭证
              </el-button>

              <el-button
                size="large"
                @click="previewData"
                :disabled="!canPreview"
                :loading="previewing"
              >
                <el-icon class="mr-1"><View /></el-icon>
                预览数据
              </el-button>

              <el-button size="large" @click="resetForm">
                <el-icon class="mr-1"><RefreshLeft /></el-icon>
                重置
              </el-button>
            </div>
          </el-form>
        </el-card>

        <!-- 数据预览 -->
        <el-card v-if="previewInfo" class="preview-card mt-6" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <el-icon class="mr-2 text-brand-600"><View /></el-icon>
                <span class="text-lg font-semibold">数据预览</span>
              </div>
              <el-tag type="info">{{ previewInfo.totalRows }} 条记录</el-tag>
            </div>
          </template>

          <div class="preview-content">
            <div class="mapping-info mb-4">
              <h4 class="font-semibold mb-2">字段映射</h4>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                <div><strong>日期:</strong> {{ previewInfo.mapping.date }}</div>
                <div><strong>对方户名:</strong> {{ previewInfo.mapping.counterparty }}</div>
                <div><strong>摘要:</strong> {{ previewInfo.mapping.summary }}</div>
                <div><strong>借方:</strong> {{ previewInfo.mapping.debit }}</div>
                <div><strong>贷方:</strong> {{ previewInfo.mapping.credit }}</div>
              </div>
            </div>

            <el-table
              :data="previewInfo.data"
              border
              stripe
              max-height="400"
              class="preview-table"
            >
              <el-table-column
                v-for="(column, index) in previewInfo.columns"
                :key="index"
                :prop="index.toString()"
                :label="column"
                min-width="120"
              />
            </el-table>
          </div>
        </el-card>
      </div>

      <!-- 侧边栏信息 -->
      <div class="lg:col-span-1">
        <!-- 功能说明 -->
        <el-card class="info-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-brand-600"><InfoFilled /></el-icon>
              <span class="font-semibold">功能说明</span>
            </div>
          </template>

          <div class="info-content">
            <div class="info-item">
              <h4 class="font-semibold mb-2">🎯 主要功能</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li>支持Excel/CSV格式银行流水导入</li>
                <li>自动数据标准化和字段映射</li>
                <li>三重智能科目匹配系统</li>
                <li>自动生成标准会计凭证</li>
                <li>支持多客户和多银行配置</li>
                <li>可选中英双语摘要翻译</li>
              </ul>
            </div>

            <div class="info-item">
              <h4 class="font-semibold mb-2">📋 数据格式支持</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li>双金额列：分别标注借方/贷方</li>
                <li>单金额列：正数=借方，负数=贷方</li>
                <li>必需字段：日期、摘要、金额</li>
                <li>推荐字段：对方户名、银行账号</li>
              </ul>
            </div>

            <div class="info-item">
              <h4 class="font-semibold mb-2">🔧 三重科目映射</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li><strong>1. 银行账户映射</strong><br/>
                    <span class="text-xs">根据银行账号匹配银行科目</span>
                </li>
                <li><strong>2. 摘要关键字映射</strong><br/>
                    <span class="text-xs">根据摘要关键词匹配交易科目</span>
                </li>
                <li><strong>3. 对方户名映射</strong><br/>
                    <span class="text-xs">根据交易对方名称匹配科目</span>
                </li>
              </ul>
            </div>

            <div class="info-item">
              <h4 class="font-semibold mb-2">⚡ 处理特点</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li>全内存处理，无临时文件</li>
                <li>实时进度反馈</li>
                <li>标准Excel格式输出</li>
                <li>支持大批量数据处理</li>
              </ul>
            </div>
          </div>
        </el-card>

        <!-- 客户映射信息 -->
        <el-card v-if="form.customerName && customerMapping" class="mapping-card mt-6" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-brand-600"><Setting /></el-icon>
              <span class="font-semibold">客户映射配置</span>
            </div>
          </template>

          <div class="mapping-content">
            <!-- 客户和银行信息 -->
            <div class="mapping-header mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">客户名称</span>
                <el-tag type="primary" size="small">{{ form.customerName }}</el-tag>
              </div>
              <div v-if="form.bankName" class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700">银行名称</span>
                <el-tag type="success" size="small">{{ form.bankName }}</el-tag>
              </div>
              <div v-else class="text-xs text-gray-500 mt-1">
                未指定银行，使用通用配置
              </div>
            </div>

            <el-divider />

            <!-- 字段映射 -->
            <div class="mapping-section">
              <h4 class="font-semibold mb-3 text-sm flex items-center">
                <el-icon class="mr-1"><Document /></el-icon>
                字段映射
              </h4>
              <div class="mapping-list space-y-2">
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">日期列:</span>
                    <span class="font-mono font-medium text-blue-600">{{ customerMapping.column_mapping.date }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">用于记录交易日期</div>
                </div>
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">对方户名列:</span>
                    <span class="font-mono font-medium text-blue-600">{{ customerMapping.column_mapping.counterparty }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">用于三重映射中的对方户名匹配</div>
                </div>
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">摘要列:</span>
                    <span class="font-mono font-medium text-blue-600">{{ customerMapping.column_mapping.summary }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">
                    <strong>获取逻辑:</strong> 如有"摘要"或"备注"列则使用，若有"用途"或"附言"列则使用，否则尝试使用"交易附言"或"对方账号附言"列
                  </div>
                </div>
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">金额列:</span>
                    <span class="font-mono font-medium text-blue-600">
                      {{ customerMapping.column_mapping.amount || '（使用借方/贷方列）' }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">
                    单金额列模式（正数=借方，负数=贷方）；若为空则使用双列模式
                  </div>
                </div>
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">借方列:</span>
                    <span class="font-mono font-medium text-blue-600">{{ customerMapping.column_mapping.debit }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">借方金额（双列模式，可为空）</div>
                </div>
                <div class="mapping-item">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">贷方列:</span>
                    <span class="font-mono font-medium text-blue-600">{{ customerMapping.column_mapping.credit }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-0.5">贷方金额（双列模式，可为空）</div>
                </div>
              </div>
            </div>

            <el-divider />

            <!-- 科目映射 -->
            <div class="mapping-section">
              <h4 class="font-semibold mb-3 text-sm flex items-center">
                <el-icon class="mr-1"><Compass /></el-icon>
                三重科目映射
                <el-tag size="small" type="info" class="ml-2">
                  {{ customerMapping.subject_mapping_count }} 条规则
                </el-tag>
              </h4>
              <div class="subject-preview space-y-2">
                <div class="mapping-rule">
                  <div class="flex items-center mb-1">
                    <el-icon class="text-blue-500 mr-1"><Location /></el-icon>
                    <span class="text-xs font-semibold">银行账户 → 银行科目</span>
                  </div>
                  <div class="text-xs text-gray-500">
                    根据银行账号自动匹配对应的银行科目
                  </div>
                </div>
                <div class="mapping-rule">
                  <div class="flex items-center mb-1">
                    <el-icon class="text-green-500 mr-1"><ChatLineSquare /></el-icon>
                    <span class="text-xs font-semibold">摘要关键字 → 交易科目</span>
                  </div>
                  <div class="text-xs text-gray-500">
                    根据摘要中的关键字匹配交易对方科目
                  </div>
                </div>
                <div class="mapping-rule">
                  <div class="flex items-center mb-1">
                    <el-icon class="text-purple-500 mr-1"><User /></el-icon>
                    <span class="text-xs font-semibold">对方户名 → 交易科目</span>
                  </div>
                  <div class="text-xs text-gray-500">
                    根据交易对方名称匹配对应的会计科目
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 处理结果 -->
        <el-card v-if="result" class="result-card mt-6" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-green-600"><CircleCheckFilled /></el-icon>
              <span class="font-semibold">处理结果</span>
            </div>
          </template>

          <div class="result-content">
            <div class="result-stats grid grid-cols-2 gap-4 mb-4">
              <div class="stat-item text-center p-3 bg-blue-50 rounded">
                <div class="text-2xl font-bold text-blue-600">{{ result.processed_records }}</div>
                <div class="text-xs text-gray-600">处理记录</div>
              </div>
              <div class="stat-item text-center p-3 bg-green-50 rounded">
                <div class="text-2xl font-bold text-green-600">{{ result.generated_vouchers }}</div>
                <div class="text-xs text-gray-600">生成凭证</div>
              </div>
            </div>

            <div class="download-section">
              <el-button
                type="primary"
                plain
                class="w-full"
                @click="downloadResult"
                :loading="downloading"
              >
                <el-icon class="mr-1"><Download /></el-icon>
                下载凭证文件
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 翻译进度组件 -->
    <TranslationProgress
      v-model="showProgress"
      title="银行流水转凭证进度"
      :processing="generating"
      :cancellable="true"
      @cancel="handleCancelProgress"
      @close="handleCloseProgress"
      ref="translationProgressRef"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CreditCard,
  DocumentCopy,
  View,
  RefreshLeft,
  UploadFilled,
  InfoFilled,
  Setting,
  CircleCheckFilled,
  Download,
  Check,
  Close,
  Document,
  Compass,
  Location,
  ChatLineSquare,
  User
} from '@element-plus/icons-vue'
import { generateBankStatementVouchers, getBankStatementCustomers, getCustomerBanks, getBankStatementMapping, previewBankStatementData } from '@/api/bank-statement'
import { generateBankVouchers, translationService } from '@/utils/translationService'
import TranslationProgress from '@/components/TranslationProgress.vue'

// 响应式数据
const formRef = ref()
const bankStatementUpload = ref()
const translationProgressRef = ref()

const form = reactive({
  customerName: '',
  bankName: '',
  enableTranslation: false
})

const rules = {
  customerName: [
    { required: true, message: '请选择客户名称', trigger: 'change' }
  ]
}

// 状态管理
const loadingCustomers = ref(false)
const loadingBanks = ref(false)
const generating = ref(false)
const previewing = ref(false)
const downloading = ref(false)

// 数据
const customers = ref([])
const availableBanks = ref([])
const customerMapping = ref(null)
const previewInfo = ref(null)
const result = ref(null)

// 进度管理
const showProgress = ref(false)

// 文件管理
const bankStatementFile = ref(null)

// 计算属性
const canGenerate = computed(() => {
  return form.customerName && bankStatementFile.value
})

const canPreview = computed(() => {
  return form.customerName && bankStatementFile.value
})

// 生命周期
onMounted(() => {
  loadCustomers()
})

// 方法
const loadCustomers = async () => {
  try {
    loadingCustomers.value = true
    const response = await getBankStatementCustomers()
    customers.value = response.customers || []

    if (customers.value.length === 0) {
      ElMessage.warning('暂无可用的客户配置，请先配置银行流水列名映射')
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
    ElMessage.error('加载客户列表失败')
  } finally {
    loadingCustomers.value = false
  }
}

const handleCustomerChange = async (customerName) => {
  if (!customerName) {
    customerMapping.value = null
    availableBanks.value = []
    form.bankName = ''
    return
  }

  try {
    // 重置银行选择
    availableBanks.value = []
    form.bankName = ''

    // 并行加载客户映射和银行列表
    const [mapping, banksResponse] = await Promise.all([
      getBankStatementMapping(customerName),
      loadCustomerBanks(customerName)
    ])

    customerMapping.value = mapping
  } catch (error) {
    console.error('加载客户映射失败:', error)
    ElMessage.error('加载客户映射配置失败')
    customerMapping.value = null
    availableBanks.value = []
    form.bankName = ''
  }
}

const loadCustomerBanks = async (customerName) => {
  try {
    loadingBanks.value = true
    const response = await getCustomerBanks(customerName)
    availableBanks.value = response.banks || []

    // 自动选择第一个银行作为默认值
    if (availableBanks.value.length > 0) {
      form.bankName = availableBanks.value[0]
    } else {
      form.bankName = ''
    }

    return response
  } catch (error) {
    console.error('加载客户银行列表失败:', error)
    availableBanks.value = []
    form.bankName = ''
    throw error
  } finally {
    loadingBanks.value = false
  }
}

const handleBankChange = async (bankName) => {
  if (!form.customerName) {
    return
  }

  try {
    // 重新加载映射，传递银行名称
    const mapping = await getBankStatementMapping(form.customerName, bankName)
    customerMapping.value = mapping
  } catch (error) {
    console.error('加载银行映射配置失败:', error)
    ElMessage.error('加载银行映射配置失败')
  }
}

const handleBankStatementFileChange = (file) => {
  bankStatementFile.value = file.raw

  // 如果已选择客户，清除预览数据
  if (previewInfo.value) {
    previewInfo.value = null
  }
}

const handleBankStatementFileRemove = () => {
  bankStatementFile.value = null
  previewInfo.value = null
}

const beforeFileUpload = (file) => {
  const isValidType = ['.xlsx', '.xls', '.csv'].some(ext =>
    file.name.toLowerCase().endsWith(ext)
  )
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('只支持 .xlsx/.xls/.csv 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const previewData = async () => {
  if (!canPreview.value) return

  try {
    previewing.value = true
    const formData = new FormData()
    formData.append('bank_statement_file', bankStatementFile.value)
    formData.append('customer_name', form.customerName)
    if (form.bankName) {
      formData.append('bank_name', form.bankName)
    }
    formData.append('max_rows', 10)

    const response = await previewBankStatementData(formData)

    if (response.success) {
      previewInfo.value = response.data
      ElMessage.success('数据预览加载成功')
    } else {
      ElMessage.error('数据预览失败')
    }
  } catch (error) {
    console.error('预览数据失败:', error)
    ElMessage.error('预览数据失败: ' + (error.message || '未知错误'))
  } finally {
    previewing.value = false
  }
}

const generateVouchers = async () => {
  if (!canGenerate.value) return

  try {
    // 表单验证
    await formRef.value.validate()

    generating.value = true
    showProgress.value = true

    const formData = new FormData()
    formData.append('bank_statement_file', bankStatementFile.value)
    formData.append('customer_name', form.customerName)
    if (form.bankName) {
      formData.append('bank_name', form.bankName)
    }
    formData.append('enable_translation', form.enableTranslation.toString())

    // 使用新的翻译服务，支持统一进度管理
    const response = await generateBankVouchers(formData, {
      onProgress: (progressData) => {
        // 更新翻译进度组件
        if (translationProgressRef.value) {
          translationProgressRef.value.updateProgress(progressData)
        }
      },
      onComplete: async (downloadResult) => {
        console.log('银行流水转凭证完成:', downloadResult)

        try {
          // 获取结果信息
          const resultUrl = `/api/v1/bank-statements/generate/result/${downloadResult.task_id}`
          const resultResponse = await fetch(resultUrl)

          if (!resultResponse.ok) {
            throw new Error('获取结果信息失败')
          }

          const resultInfo = await resultResponse.json()
          console.log('结果信息:', resultInfo)

          // 更新结果数据
          result.value = {
            download_url: `/api/v1/bank-statements/download/${downloadResult.task_id}`,
            processed_records: resultInfo.processed_records || downloadResult.completed || 0,
            generated_vouchers: resultInfo.generated_vouchers || Math.floor((downloadResult.completed || 0) * 0.8),
            task_id: downloadResult.task_id
          }

          // 自动触发下载
          if (result.value.download_url) {
            handleDownload(result.value.download_url)
          }
        } catch (error) {
          console.error('获取结果信息失败:', error)
          ElMessage.error('获取结果信息失败，请重试')
        }

        ElMessage.success(`成功生成凭证！处理了 ${result.value.processed_records} 条记录，生成约 ${result.value.generated_vouchers} 个凭证`)
      },
      onError: (error) => {
        console.error('生成凭证失败:', error)
        ElMessage.error('生成凭证失败: ' + (error.message || '未知错误'))
      },
      timeout: 7200000 // 2小时超时，匹配后端SSE超时时间
    })

  } catch (error) {
    console.error('生成凭证失败:', error)
    ElMessage.error('生成凭证失败: ' + (error.message || '未知错误'))
  } finally {
    generating.value = false
    translationService.cleanup()
  }
}

// 进度组件事件处理
const handleCancelProgress = async () => {
  try {
    await translationService.cancel()
    generating.value = false
    showProgress.value = false
    ElMessage.info('任务已取消')
  } catch (error) {
    console.error('取消任务时发生错误:', error)
    ElMessage.warning('取消任务时发生错误，但进度窗口已关闭')
    generating.value = false
    showProgress.value = false
  }
}

const handleCloseProgress = () => {
  showProgress.value = false
  generating.value = false
}

const handleDownload = async (downloadUrl) => {
  if (!downloadUrl) return

  try {
    console.log('开始下载文件:', downloadUrl)

    const response = await fetch(downloadUrl)
    if (!response.ok) {
      throw new Error('下载失败，请重试')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bank_vouchers_${Date.now()}.xlsx`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()

    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }, 100)

    ElMessage.success('文件下载已开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  }
}

const downloadResult = async () => {
  if (!result.value?.download_url) return

  try {
    downloading.value = true
    await handleDownload(result.value.download_url)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  } finally {
    downloading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  bankStatementUpload.value?.clearFiles()

  bankStatementFile.value = null
  availableBanks.value = []
  customerMapping.value = null
  previewInfo.value = null
  result.value = null

  // 重置为默认值
  form.enableTranslation = false

  ElMessage.success('表单已重置')
}
</script>

<style scoped>
.bank-to-voucher {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.form-card,
.info-card,
.mapping-card,
.result-card,
.preview-card {
  margin-bottom: 1.5rem;
}

.voucher-form {
  padding: 1rem 0;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding: 2rem 0 1rem;
  border-top: 1px solid #e5e7eb;
}

.info-content,
.mapping-content,
.result-content {
  color: #374151;
}

.info-item,
.mapping-section {
  margin-bottom: 1.5rem;
}

.info-item:last-child,
.mapping-section:last-child {
  margin-bottom: 0;
}

.info-item h4,
.mapping-section h4 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.info-item ul {
  list-style: none;
  padding-left: 0;
}

.info-item ul li {
  padding-left: 1rem;
  position: relative;
}

.info-item ul li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.6em;
  width: 4px;
  height: 4px;
  background-color: #3b82f6;
  border-radius: 50%;
}

.mapping-header {
  background-color: #f8fafc;
  padding: 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid #e5e7eb;
}

.mapping-item {
  padding: 0.75rem;
  background-color: #fafbfc;
  border-radius: 0.375rem;
  border: 1px solid #f0f1f3;
  transition: all 0.2s ease;
}

.mapping-item:hover {
  background-color: #f0f9ff;
  border-color: #bfdbfe;
}

.mapping-rule {
  padding: 0.75rem;
  background-color: #f8fafc;
  border-radius: 0.375rem;
  border-left: 3px solid #e5e7eb;
  transition: all 0.2s ease;
}

.mapping-rule:hover {
  background-color: #f0f9ff;
  border-left-color: #3b82f6;
}

.result-stats {
  margin-bottom: 1rem;
}

.stat-item {
  border-radius: 0.5rem;
  transition: transform 0.2s;
}

.stat-item:hover {
  transform: translateY(-1px);
}

.preview-content {
  max-height: 500px;
  overflow-y: auto;
}

.mapping-info {
  background-color: #f8fafc;
  padding: 1rem;
  border-radius: 0.5rem;
  border-left: 4px solid #3b82f6;
}

.preview-table {
  font-size: 0.875rem;
}


/* 上传组件样式优化 */
:deep(.el-upload-dragger) {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  width: 100%;
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #3b82f6;
  background-color: #f0f9ff;
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #3b82f6;
  background-color: #dbeafe;
}

/* 折叠面板样式 */
:deep(.el-collapse-item__header) {
  font-weight: 500;
  color: #374151;
}

/* 翻译设置美化样式 */
.translation-setting {
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.translation-setting:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.setting-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.setting-description {
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid #f1f5f9;
  transition: all 0.2s ease;
}

.status-enabled,
.status-disabled {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.status-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.status-text {
  flex: 1;
}

.status-title {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.status-detail {
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.4;
}

.status-enabled .status-title {
  color: #059669;
}

.status-disabled .status-title {
  color: #6b7280;
}

.status-enabled .status-detail {
  color: #047857;
}

.status-disabled .status-detail {
  color: #9ca3af;
}

.status-enabled .setting-description {
  border-left: 3px solid #10b981;
  background: linear-gradient(90deg, #ecfdf5 0%, white 100%);
}

.status-disabled .setting-description {
  border-left: 3px solid #9ca3af;
  background: linear-gradient(90deg, #f9fafb 0%, white 100%);
}

.setting-header :deep(.el-switch__label) {
  font-weight: 500;
  color: #374151;
}

/* 表格样式优化 */
:deep(.el-table) {
  font-size: 0.875rem;
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #374151;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 1.5rem;
  }

  .grid-cols-1.md\:grid-cols-2 {
    grid-template-columns: 1fr;
  }

  .result-stats {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
</style>