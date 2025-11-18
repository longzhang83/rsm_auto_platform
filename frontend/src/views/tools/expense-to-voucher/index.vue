<template>
  <div class="expense-to-voucher">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">费用清单转凭证</h1>
      <p class="text-gray-600">将费用报销清单自动转换为标准会计凭证格式，提升财务工作效率</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主要操作区域 -->
      <div class="lg:col-span-2">
        <el-card class="form-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-brand-600"><DocumentCopy /></el-icon>
              <span class="text-lg font-semibold">费用清单上传</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="voucher-form"
          >
            <!-- 必填文件 -->
            <div class="file-section mb-6">
              <h3 class="text-base font-semibold text-gray-700 mb-4 flex items-center">
                <el-icon class="mr-2 text-red-500"><Star /></el-icon>
                必填文件
              </h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="费用报销表" prop="expenseFile">
                  <el-upload
                    ref="expenseUpload"
                    class="upload-demo"
                    drag
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleExpenseFileChange"
                    :on-remove="handleExpenseFileRemove"
                    accept=".xlsx,.xls"
                  >
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                      将文件拖到此处，或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持 .xlsx/.xls 格式，文件大小不超过 10MB
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
              </div>
            </div>

            <!-- 可选文件 -->
            <div class="file-section mb-6">
              <h3 class="text-base font-semibold text-gray-700 mb-4 flex items-center">
                <el-icon class="mr-2 text-gray-400"><Plus /></el-icon>
                可选文件
              </h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="人员列表">
                  <el-upload
                    ref="employeeUpload"
                    class="upload-demo"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleEmployeeFileChange"
                    :on-remove="handleEmployeeFileRemove"
                    accept=".xlsx,.xls"
                  >
                    <el-button type="primary" plain>
                      <el-icon class="mr-1"><Upload /></el-icon>
                      选择文件
                    </el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        员工信息表，用于匹配员工编号和部门
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>

                <el-form-item label="科目映射">
                  <el-upload
                    ref="subjectUpload"
                    class="upload-demo"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleSubjectFileChange"
                    :on-remove="handleSubjectFileRemove"
                    accept=".csv"
                  >
                    <el-button type="primary" plain>
                      <el-icon class="mr-1"><Upload /></el-icon>
                      选择文件
                    </el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        科目名称与编码映射表
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>

                <el-form-item label="翻译映射表">
                  <el-upload
                    ref="translationUpload"
                    class="upload-demo"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleTranslationFileChange"
                    :on-remove="handleTranslationFileRemove"
                    accept=".csv"
                  >
                    <el-button type="primary" plain>
                      <el-icon class="mr-1"><Upload /></el-icon>
                      选择文件
                    </el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        中英文摘要翻译映射，用于复用翻译结果
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
              </div>
            </div>

            <!-- 凭证设置 -->
            <div class="settings-section mb-6">
              <div
                class="settings-header cursor-pointer flex items-center justify-between mb-4"
                @click="toggleSettings"
              >
                <h3 class="text-base font-semibold text-gray-700 flex items-center">
                  <el-icon class="mr-2 text-brand-600"><Setting /></el-icon>
                  凭证设置
                </h3>
                <el-icon
                  class="text-gray-400 transition-transform duration-300"
                  :class="{ 'rotate-180': settingsExpanded }"
                >
                  <ArrowDown />
                </el-icon>
              </div>

              <transition
                name="slide"
                mode="out-in"
                @enter="enter"
                @after-enter="afterEnter"
                @leave="leave"
                @after-leave="afterLeave"
              >
                <div v-show="settingsExpanded" class="settings-content">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <el-form-item label="会计期间" prop="period">
                  <el-input
                    v-model="form.period"
                    placeholder="例如：202501"
                    clearable
                  >
                    <template #suffix>
                      <el-tooltip content="格式：YYYYMM，留空使用工作表名">
                        <el-icon class="cursor-pointer"><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="费用表工作表">
                  <el-input
                    v-model="form.sheetName"
                    placeholder="默认第一个工作表"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="制单人" prop="preparer">
                  <el-input
                    v-model="form.preparer"
                    placeholder="制单人姓名"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="凭证类别" prop="category">
                  <el-select v-model="form.category" placeholder="选择凭证类别" style="width: 100%">
                    <el-option label="记" value="记" />
                    <el-option label="收" value="收" />
                    <el-option label="付" value="付" />
                    <el-option label="转" value="转" />
                  </el-select>
                </el-form-item>

                <el-form-item label="默认贷方科目" prop="creditAccount">
                  <el-input
                    v-model="form.creditAccount"
                    placeholder="例如：224104"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="起始流水号">
                  <el-input-number
                    v-model="form.startSeq"
                    :min="0"
                    :max="9999"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>
                  </div>
                </div>
              </transition>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                @click="handleSubmit"
                class="submit-btn"
              >
                <el-icon class="mr-2"><Document /></el-icon>
                生成凭证
              </el-button>

              <el-button
                size="large"
                @click="handleReset"
                class="reset-btn"
              >
                <el-icon class="mr-2"><Refresh /></el-icon>
                重置表单
              </el-button>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 侧边栏 -->
      <div class="lg:col-span-1">
        <!-- 帮助信息 -->
        <el-card class="help-card mb-4" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-blue-500"><QuestionFilled /></el-icon>
              <span>使用帮助</span>
            </div>
          </template>

          <div class="help-content">
            <div class="help-item mb-4">
              <h4 class="font-semibold text-gray-700 mb-2">文件格式要求</h4>
              <ol class="text-sm text-gray-600 space-y-1">
                <li>费用报销表：Excel格式，包含费用明细</li>
                <li>人员列表：Excel格式，包含员工信息</li>
                <li>科目映射：CSV格式，科目名称与编码对应</li>
                <li>翻译映射：CSV格式，中英文摘要对应</li>
              </ol>
            </div>

            <div class="help-item mb-4">
              <h4 class="font-semibold text-gray-700 mb-2">处理流程</h4>
              <ol class="text-sm text-gray-600 space-y-1">
                <li>上传费用报销表（必填）</li>
                <li>上传可选的辅助文件</li>
                <li>配置凭证参数</li>
                <li>点击生成凭证</li>
                <li>下载处理结果</li>
              </ol>
            </div>

            <div class="help-item">
              <h4 class="font-semibold text-gray-700 mb-2">常见问题</h4>
              <div class="text-sm text-gray-600 space-y-2">
                <div>
                  <span class="font-medium">Q: 为什么上传失败？</span>
                  <p>A: 请检查文件格式是否正确，文件大小是否超过限制。</p>
                </div>
                <div>
                  <span class="font-medium">Q: 如何处理编码问题？</span>
                  <p>A: 确保文件使用UTF-8编码，避免出现乱码。</p>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 模板下载 -->
        <el-card class="template-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-green-500"><Download /></el-icon>
              <span>模板下载</span>
            </div>
          </template>

          <div class="template-list space-y-2">
            <div class="template-button-container">
              <el-button
                type="primary"
                plain
                size="small"
                @click="downloadTemplate('subject')"
                class="template-btn w-full"
              >
                <span class="template-btn-content">
                  <el-icon class="template-icon"><Tickets /></el-icon>
                  <span class="template-text">科目映射模板</span>
                </span>
              </el-button>
            </div>

            <div class="template-info mt-4 text-sm text-gray-500">
              <p>其他模板文件说明：</p>
              <ul class="mt-2 space-y-1">
                <li>• 费用报销表：请参考实际业务数据格式</li>
                <li>• 人员列表：可选文件，用于匹配员工信息</li>
                <li>• 翻译映射：系统会自动生成并缓存</li>
              </ul>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 进度对话框 -->
    <TranslationProgress
      v-model="showProgress"
      :title="'生成凭证'"
      :processing="generating"
      @cancel="handleCancelProgress"
      @close="handleCloseProgress"
      ref="translationProgressRef"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadFile } from '@/utils/request'
import TranslationProgress from '@/components/TranslationProgress.vue'
import { generateVouchers, translationService } from '@/utils/translationService'

// 表单数据
const form = reactive({
  expenseFile: null,
  employeeFile: null,
  subjectFile: null,
  translationFile: null,
  period: '',
  sheetName: '',
  preparer: 'cissy',
  category: '记',
  creditAccount: '224104',
  startSeq: 0
})

// 表单验证规则
const rules = {
  expenseFile: [
    { required: true, message: '请上传费用报销表', trigger: 'change' }
  ],
  preparer: [
    { required: true, message: '请输入制单人', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择凭证类别', trigger: 'change' }
  ],
  creditAccount: [
    { required: true, message: '请输入默认贷方科目', trigger: 'blur' }
  ]
}

const loading = ref(false)
const formRef = ref(null)
const translationProgressRef = ref()
const showProgress = ref(false)
const generating = ref(false)

// 凭证设置收缩状态
const settingsExpanded = ref(false) // 默认收缩

// 切换设置显示/隐藏
const toggleSettings = () => {
  settingsExpanded.value = !settingsExpanded.value
}

// 动画钩子函数
const enter = (element) => {
  element.style.height = '0'
  element.style.overflow = 'hidden'
}

const afterEnter = (element) => {
  element.style.height = element.scrollHeight + 'px'
  setTimeout(() => {
    element.style.height = 'auto'
    element.style.overflow = 'visible'
  }, 300)
}

const leave = (element) => {
  element.style.height = element.scrollHeight + 'px'
  element.style.overflow = 'hidden'
  setTimeout(() => {
    element.style.height = '0'
  }, 10)
}

const afterLeave = (element) => {
  element.style.overflow = 'visible'
}

// 文件处理函数
const handleExpenseFileChange = (file) => {
  form.expenseFile = file.raw
}

const handleExpenseFileRemove = () => {
  form.expenseFile = null
}

const handleEmployeeFileChange = (file) => {
  form.employeeFile = file.raw
}

const handleEmployeeFileRemove = () => {
  form.employeeFile = null
}

const handleSubjectFileChange = (file) => {
  form.subjectFile = file.raw
}

const handleSubjectFileRemove = () => {
  form.subjectFile = null
}

const handleTranslationFileChange = (file) => {
  form.translationFile = file.raw
}

const handleTranslationFileRemove = () => {
  form.translationFile = null
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    generating.value = true
    showProgress.value = true

    const formData = new FormData()

    // 添加文件
    if (form.expenseFile) {
      formData.append('expense_file', form.expenseFile)
    }
    if (form.employeeFile) {
      formData.append('employee_file', form.employeeFile)
    }
    if (form.subjectFile) {
      formData.append('subject_file', form.subjectFile)
    }
    if (form.translationFile) {
      formData.append('translation_file', form.translationFile)
    }

    // 添加表单数据
    formData.append('preparer', form.preparer)
    formData.append('voucher_category', form.category)
    formData.append('credit_account', form.creditAccount)
    formData.append('start_seq', form.startSeq)

    if (form.period) {
      formData.append('expense_period', form.period)
    }
    if (form.sheetName) {
      formData.append('expense_sheet', form.sheetName)
    }

    // 使用异步生成模式，带进度跟踪
    await generateVouchers(formData, {
      onProgress: (progressData) => {
        if (translationProgressRef.value) {
          translationProgressRef.value.updateProgress(progressData)
        }
      },
      onComplete: async (downloadResult) => {
        // 自动下载生成的文件
        const downloadUrl = `/api/v1/vouchers/download/${downloadResult.task_id}`
        try {
          const response = await uploadFile(downloadUrl, null, 'GET')
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = 'vouchers_bundle.zip'
          document.body.appendChild(link)
          link.click()
          link.remove()
          window.URL.revokeObjectURL(url)

          ElMessage.success('凭证生成成功！')
        } catch (error) {
          console.error('下载失败:', error)
          ElMessage.error('下载失败：' + error.message)
        }
      },
      onError: (error) => {
        console.error('生成失败:', error)
        ElMessage.error('生成失败：' + error.message)
      },
      timeout: 7200000 // 2小时超时
    })

  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败：' + error.message)
  } finally {
    generating.value = false
    translationService.cleanup()
  }
}

// 取消进度
const handleCancelProgress = async () => {
  await translationService.cancel()
  generating.value = false
  showProgress.value = false
  ElMessage.info('已取消生成任务')
}

// 关闭进度对话框
const handleCloseProgress = () => {
  showProgress.value = false
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  form.expenseFile = null
  form.employeeFile = null
  form.subjectFile = null
  form.translationFile = null
}

// 下载模板
const downloadTemplate = async (type) => {
  const templates = {
    subject: '科目映射.csv',
  }

  try {
    // 只支持科目映射模板（使用 data 目录中的实际文件）
    if (!templates[type]) {
      ElMessage.warning('该模板暂不支持下载')
      return
    }

    ElMessage.info(`正在下载 ${templates[type]}...`)

    // 调用后端 API 下载模板
    const response = await uploadFile(`/api/v1/vouchers/templates/${type}`, null, 'GET')
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = templates[type]
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`${templates[type]} 下载成功！`)

  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(`下载失败：${error.message}`)
  }
}
</script>

<style scoped>
.expense-to-voucher {
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

.settings-header {
  user-select: none;
}

.settings-header:hover .el-icon {
  color: #6b7280;
}

.settings-content {
  overflow: hidden;
  transition: all 0.3s ease-in-out;
}

/* 收缩动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.slide-enter-from {
  max-height: 0;
  opacity: 0;
}

.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-enter-to {
  max-height: 500px;
  opacity: 1;
}

.slide-leave-from {
  max-height: 500px;
  opacity: 1;
}

/* 箭头旋转动画 */
.rotate-180 {
  transform: rotate(180deg);
}

.upload-demo :deep(.el-upload-dragger) {
  width: 100%;
}

.action-section {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.submit-btn {
  padding: 12px 40px;
  font-size: 16px;
}

.help-content {
  font-size: 14px;
}

.help-item h4 {
  color: #374151;
  margin-bottom: 8px;
}

.template-button-container {
  margin-bottom: 8px;
}

.template-btn {
  text-align: left !important;
  justify-content: flex-start !important;
}

.template-btn-content {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  text-align: left !important;
}

.template-icon {
  margin-right: 8px !important;
  flex-shrink: 0;
}

.template-text {
  flex: 1;
  text-align: left;
}

/* 确保Element Plus按钮样式被覆盖 */
.template-btn :deep(.el-button) {
  text-align: left !important;
  justify-content: flex-start !important;
}

.template-btn :deep(.el-button > span) {
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  text-align: left !important;
  justify-content: flex-start !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid.grid-cols-1.md\\:grid-cols-2 {
    grid-template-columns: 1fr;
  }

  .action-section {
    text-align: stretch;
  }

  .submit-btn,
  .reset-btn {
    width: 100%;
    margin-bottom: 8px;
  }
}
</style>
