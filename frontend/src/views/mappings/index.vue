<template>
  <div class="mappings-page">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">映射管理</h1>
      <p class="text-gray-600">管理银行流水列名映射和会计科目映射配置</p>
    </div>

    <el-tabs v-model="activeTab" class="mappings-tabs">
      <!-- 列名映射标签页 -->
      <el-tab-pane label="银行流水列名映射" name="columns">
        <div class="tab-content">
          <!-- 操作栏 -->
          <div class="toolbar mb-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <el-input
                v-model="columnSearch.customer"
                placeholder="搜索客户名称"
                clearable
                style="width: 200px"
                @clear="loadColumnMappings"
              />
              <el-input
                v-model="columnSearch.bank"
                placeholder="搜索银行名称"
                clearable
                style="width: 200px"
                @clear="loadColumnMappings"
              />
              <el-button type="primary" :icon="Search" @click="loadColumnMappings">
                搜索
              </el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-button :icon="Download" @click="exportColumnMappings">
                导出Excel
              </el-button>
              <el-button :icon="Upload" @click="showColumnImportDialog">
                导入Excel
              </el-button>
              <el-button type="primary" :icon="Plus" @click="showColumnCreateDialog">
                新增映射
              </el-button>
            </div>
          </div>

          <!-- 列名映射表格 -->
          <el-table
            :data="columnMappings"
            stripe
            border
            v-loading="columnLoading"
            style="width: 100%"
          >
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="customer_name" label="客户名称" width="250" />
            <el-table-column prop="bank_name" label="银行名称" width="100" />
            <el-table-column prop="date" label="日期列名" width="100" />
            <el-table-column prop="counterparty" label="对方户名" width="100" />
            <el-table-column prop="summary" label="摘要列名" width="100" />
            <el-table-column prop="debit" label="借方列名" width="100" />
            <el-table-column prop="credit" label="贷方列名" width="100" />
            <el-table-column prop="amount" label="金额列名" width="100" />
            <el-table-column prop="bank_account" label="银行账号" width="100" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  :icon="Edit"
                  @click="showColumnEditDialog(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                  @click="deleteColumnMapping(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 会计科目映射标签页 -->
      <el-tab-pane label="会计科目映射" name="subjects">
        <div class="tab-content">
          <!-- 操作栏 -->
          <div class="toolbar mb-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <el-input
                v-model="subjectSearch.customer"
                placeholder="搜索客户名称"
                clearable
                style="width: 200px"
                @clear="loadSubjectMappings"
              />
              <el-select
                v-model="subjectSearch.matchType"
                placeholder="匹配方式"
                clearable
                style="width: 150px"
                @clear="loadSubjectMappings"
              >
                <el-option label="对方账户名称" value="对方账户名称" />
                <el-option label="摘要关键字" value="摘要关键字" />
                <el-option label="银行账号" value="银行账号" />
              </el-select>
              <el-input
                v-model="subjectSearch.keyword"
                placeholder="搜索关键字"
                clearable
                style="width: 200px"
                @clear="loadSubjectMappings"
              />
              <el-button type="primary" :icon="Search" @click="loadSubjectMappings">
                搜索
              </el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-button :icon="Download" @click="exportSubjectMappings">
                导出Excel
              </el-button>
              <el-button :icon="Upload" @click="showSubjectImportDialog">
                导入Excel
              </el-button>
              <el-button type="primary" :icon="Plus" @click="showSubjectCreateDialog">
                新增映射
              </el-button>
            </div>
          </div>

          <!-- 会计科目映射表格 -->
          <el-table
            :data="subjectMappings"
            stripe
            border
            v-loading="subjectLoading"
            style="width: 100%"
          >
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="customer_name" label="客户名称" width="100" />
            <el-table-column prop="match_type" label="匹配方式" width="150" />
            <el-table-column prop="counterparty_name" label="对方账户名称" width="280" />
            <el-table-column prop="keywords" label="摘要关键字" width="120" />
            <el-table-column prop="bank_account" label="银行账号" width="220" />
            <el-table-column prop="subject_code" label="会计科目编码" width="150" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  :icon="Edit"
                  @click="showSubjectEditDialog(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                  @click="deleteSubjectMapping(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 列名映射编辑对话框 -->
    <el-dialog
      v-model="columnDialogVisible"
      :title="columnDialogMode === 'create' ? '新增列名映射' : '编辑列名映射'"
      width="600px"
    >
      <el-form
        ref="columnFormRef"
        :model="columnForm"
        :rules="columnRules"
        label-width="120px"
      >
        <el-form-item label="客户名称" prop="customer_name">
          <el-input v-model="columnForm.customer_name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="银行名称" prop="bank_name">
          <el-input v-model="columnForm.bank_name" placeholder="请输入银行名称" />
        </el-form-item>
        <el-form-item label="日期列名" prop="date">
          <el-input v-model="columnForm.date" placeholder="Excel中日期列的列名" />
        </el-form-item>
        <el-form-item label="对方户名" prop="counterparty">
          <el-input v-model="columnForm.counterparty" placeholder="Excel中对方户名列的列名" />
        </el-form-item>
        <el-form-item label="摘要列名" prop="summary">
          <el-input v-model="columnForm.summary" placeholder="Excel中摘要列的列名" />
        </el-form-item>
        <el-form-item label="借方列名" prop="debit">
          <el-input v-model="columnForm.debit" placeholder="Excel中借方列的列名" />
        </el-form-item>
        <el-form-item label="贷方列名" prop="credit">
          <el-input v-model="columnForm.credit" placeholder="Excel中贷方列的列名" />
        </el-form-item>
        <el-form-item label="金额列名" prop="amount">
          <el-input v-model="columnForm.amount" placeholder="单列金额格式（可选）" />
        </el-form-item>
        <el-form-item label="银行账号" prop="bank_account">
          <el-input v-model="columnForm.bank_account" placeholder="Excel中银行账号列的列名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="columnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitColumnForm" :loading="columnSubmitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 会计科目映射编辑对话框 -->
    <el-dialog
      v-model="subjectDialogVisible"
      :title="subjectDialogMode === 'create' ? '新增会计科目映射' : '编辑会计科目映射'"
      width="600px"
    >
      <el-form
        ref="subjectFormRef"
        :model="subjectForm"
        :rules="subjectRules"
        label-width="120px"
      >
        <el-form-item label="客户名称" prop="customer_name">
          <el-input v-model="subjectForm.customer_name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="匹配方式" prop="match_type">
          <el-select v-model="subjectForm.match_type" placeholder="请选择匹配方式" style="width: 100%">
            <el-option label="对方账户名称" value="对方账户名称" />
            <el-option label="摘要关键字" value="摘要关键字" />
            <el-option label="银行账号" value="银行账号" />
          </el-select>
        </el-form-item>
        <el-form-item
          label="对方账户名称"
          prop="counterparty_name"
          v-if="subjectForm.match_type === '对方账户名称'"
        >
          <el-input
            v-model="subjectForm.counterparty_name"
            placeholder="请输入对方账户名称"
          />
        </el-form-item>
        <el-form-item
          label="摘要关键字"
          prop="keywords"
          v-if="subjectForm.match_type === '摘要关键字'"
        >
          <el-input v-model="subjectForm.keywords" placeholder="请输入摘要关键字" />
        </el-form-item>
        <el-form-item
          label="银行账号"
          prop="bank_account"
          v-if="subjectForm.match_type === '银行账号'"
        >
          <el-input
            v-model="subjectForm.bank_account"
            placeholder="请输入银行账号"
          />
        </el-form-item>
        <el-form-item label="会计科目编码" prop="subject_code">
          <el-input v-model="subjectForm.subject_code" placeholder="请输入会计科目编码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subjectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSubjectForm" :loading="subjectSubmitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- Excel导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入Excel" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        :limit="1"
        accept=".xlsx,.xls"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip text-gray-500">
            仅支持 .xlsx 或 .xls 格式的文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importing">
          确定导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  Search,
  Plus,
  Edit,
  Delete,
  Download,
  Upload,
  DocumentCopy,
  UploadFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request, { uploadFile, downloadFile } from '@/utils/request'

// Tab状态
const activeTab = ref('columns')

// 列名映射相关状态
const columnMappings = ref([])
const columnLoading = ref(false)
const columnSearch = reactive({
  customer: '',
  bank: ''
})

// 会计科目映射相关状态
const subjectMappings = ref([])
const subjectLoading = ref(false)
const subjectSearch = reactive({
  customer: '',
  matchType: '',
  keyword: ''
})

// 列名映射对话框
const columnDialogVisible = ref(false)
const columnDialogMode = ref('create') // 'create' | 'edit'
const columnFormRef = ref(null)
const columnSubmitting = ref(false)
const columnForm = reactive({
  customer_name: '',
  bank_name: '',
  date: '',
  counterparty: '',
  summary: '',
  debit: '',
  credit: '',
  amount: '',
  bank_account: '',
  payer_account: '',
  payer_name: '',
  payee_account: '',
  payee_name: ''
})
const columnRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}

// 会计科目映射对话框
const subjectDialogVisible = ref(false)
const subjectDialogMode = ref('create') // 'create' | 'edit'
const subjectFormRef = ref(null)
const subjectSubmitting = ref(false)
const subjectForm = reactive({
  customer_name: '',
  match_type: '',
  counterparty_name: '',
  keywords: '',
  bank_account: '',
  subject_code: ''
})
const subjectRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  match_type: [{ required: true, message: '请选择匹配方式', trigger: 'change' }],
  subject_code: [{ required: true, message: '请输入会计科目编码', trigger: 'blur' }]
}

// Excel导入相关
const importDialogVisible = ref(false)
const importType = ref('') // 'columns' | 'subjects'
const importing = ref(false)
const uploadRef = ref(null)
const fileList = ref([])

// ==================== 列名映射方法 ====================

const loadColumnMappings = async () => {
  try {
    columnLoading.value = true
    const params = {}
    if (columnSearch.customer) params.customer_name = columnSearch.customer
    if (columnSearch.bank) params.bank_name = columnSearch.bank

    const response = await request.get('/mappings/columns', { params })
    columnMappings.value = response.mappings
  } catch (error) {
    ElMessage.error('加载列名映射失败: ' + (error.message || '未知错误'))
  } finally {
    columnLoading.value = false
  }
}

const showColumnCreateDialog = () => {
  columnDialogMode.value = 'create'
  resetColumnForm()
  columnDialogVisible.value = true
}

const showColumnEditDialog = (row) => {
  columnDialogMode.value = 'edit'
  Object.assign(columnForm, row)
  columnDialogVisible.value = true
}

const resetColumnForm = () => {
  Object.keys(columnForm).forEach(key => {
    columnForm[key] = ''
  })
  columnFormRef.value?.resetFields()
}

const submitColumnForm = async () => {
  try {
    await columnFormRef.value.validate()
    columnSubmitting.value = true

    if (columnDialogMode.value === 'create') {
      await request.post('/mappings/columns', columnForm)
      ElMessage.success('创建成功')
    } else {
      await request.put(`/mappings/columns/${columnForm.id}`, columnForm)
      ElMessage.success('更新成功')
    }

    columnDialogVisible.value = false
    loadColumnMappings()
  } catch (error) {
    if (error.message) {
      ElMessage.error('操作失败: ' + error.message)
    }
  } finally {
    columnSubmitting.value = false
  }
}

const deleteColumnMapping = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户"${row.customer_name}"的银行"${row.bank_name}"映射吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.delete(`/mappings/columns/${row.id}`)
    ElMessage.success('删除成功')
    loadColumnMappings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

const exportColumnMappings = async () => {
  try {
    const blob = await downloadFile('/mappings/columns/export')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '银行流水列名mapping.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  }
}


// ==================== 会计科目映射方法 ====================

const loadSubjectMappings = async () => {
  try {
    subjectLoading.value = true
    const params = {}
    if (subjectSearch.customer) params.customer_name = subjectSearch.customer
    if (subjectSearch.matchType) params.match_type = subjectSearch.matchType
    if (subjectSearch.keyword) params.search = subjectSearch.keyword

    const response = await request.get('/mappings/subjects', { params })
    subjectMappings.value = response.mappings
  } catch (error) {
    ElMessage.error('加载会计科目映射失败: ' + (error.message || '未知错误'))
  } finally {
    subjectLoading.value = false
  }
}

const showSubjectCreateDialog = () => {
  subjectDialogMode.value = 'create'
  resetSubjectForm()
  subjectDialogVisible.value = true
}

const showSubjectEditDialog = (row) => {
  subjectDialogMode.value = 'edit'
  Object.assign(subjectForm, row)
  subjectDialogVisible.value = true
}

const resetSubjectForm = () => {
  Object.keys(subjectForm).forEach(key => {
    subjectForm[key] = ''
  })
  subjectFormRef.value?.resetFields()
}

const submitSubjectForm = async () => {
  try {
    await subjectFormRef.value.validate()
    subjectSubmitting.value = true

    if (subjectDialogMode.value === 'create') {
      await request.post('/mappings/subjects', subjectForm)
      ElMessage.success('创建成功')
    } else {
      await request.put(`/mappings/subjects/${subjectForm.id}`, subjectForm)
      ElMessage.success('更新成功')
    }

    subjectDialogVisible.value = false
    loadSubjectMappings()
  } catch (error) {
    if (error.message) {
      ElMessage.error('操作失败: ' + error.message)
    }
  } finally {
    subjectSubmitting.value = false
  }
}

const deleteSubjectMapping = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户"${row.customer_name}"的科目"${row.subject_code}"映射吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.delete(`/mappings/subjects/${row.id}`)
    ElMessage.success('删除成功')
    loadSubjectMappings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

const exportSubjectMappings = async () => {
  try {
    const blob = await downloadFile('/mappings/subjects/export')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '会计科目mapping.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  }
}


// ==================== Excel导入方法 ====================

const showColumnImportDialog = () => {
  importType.value = 'columns'
  fileList.value = []
  importDialogVisible.value = true
}

const showSubjectImportDialog = () => {
  importType.value = 'subjects'
  fileList.value = []
  importDialogVisible.value = true
}

const handleFileChange = (file, files) => {
  fileList.value = files
}

const submitImport = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  try {
    importing.value = true
    const formData = new FormData()
    formData.append('file', fileList.value[0].raw)

    const endpoint = importType.value === 'columns'
      ? '/mappings/columns/import'
      : '/mappings/subjects/import'

    // 使用 uploadFile 函数上传文件，它会正确处理 FormData
    const response = await uploadFile(endpoint, formData)

    // 解析响应
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '导入失败')
    }

    const result = await response.json()
    ElMessage.success(result.message || '导入成功')
    importDialogVisible.value = false

    // 刷新列表
    if (importType.value === 'columns') {
      loadColumnMappings()
    } else {
      loadSubjectMappings()
    }
  } catch (error) {
    ElMessage.error('导入失败: ' + (error.message || '未知错误'))
  } finally {
    importing.value = false
  }
}

// ==================== 初始化 ====================

onMounted(() => {
  loadColumnMappings()
  loadSubjectMappings()
})
</script>

<style scoped>
.mappings-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.mappings-tabs {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.tab-content {
  padding: 20px 0;
}

.toolbar {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
