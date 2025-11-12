<template>
  <div class="history-page">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">处理记录</h1>
      <p class="text-gray-600">查看所有工具的处理历史和统计信息</p>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card mb-6" shadow="hover">
      <el-form :model="filters" :inline="true" class="filter-form">
        <el-form-item label="工具类型">
          <el-select v-model="filters.tool" placeholder="全部" clearable style="width: 150px">
            <el-option label="费用清单转凭证" value="expense" />
            <el-option label="摘要翻译" value="translate" />
            <el-option label="银行流水转凭证" value="bank" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="处理中" value="processing" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon class="mr-1"><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon class="mr-1"><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <el-icon class="mr-2 text-blue-500"><Clock /></el-icon>
            <span class="text-lg font-semibold">处理记录</span>
            <el-tag class="ml-3" type="info" size="small">共 {{ total }} 条记录</el-tag>
          </div>
          <div class="flex items-center">
            <el-button type="text" @click="handleExport">
              <el-icon class="mr-1"><Download /></el-icon>
              导出记录
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="tableData"
        v-loading="loading"
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="time" label="处理时间" width="180" sortable="custom">
          <template #default="scope">
            <div>
              <div>{{ formatTime(scope.row.time) }}</div>
              <div class="text-xs text-gray-500">{{ formatDate(scope.row.time) }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="tool" label="使用工具" width="140">
          <template #default="scope">
            <el-tag :type="getToolTagType(scope.row.tool)" size="small">
              {{ getToolName(scope.row.tool) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="fileName" label="文件名称" min-width="200">
          <template #default="scope">
            <div class="flex items-center">
              <el-icon class="mr-2 text-gray-400"><Document /></el-icon>
              <span class="truncate">{{ scope.row.fileName }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="user" label="操作用户" width="120">
          <template #default="scope">
            <div class="flex items-center">
              <img :src="scope.row.avatar" class="w-6 h-6 rounded-full mr-2" />
              <span>{{ scope.row.user }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)" size="small">
              {{ getStatusName(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="处理时长" width="100" sortable="custom">
          <template #default="scope">
            <span class="text-gray-600">{{ scope.row.duration }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="resultCount" label="结果数量" width="100">
          <template #default="scope">
            <span class="font-semibold">{{ scope.row.resultCount }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container mt-4">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import request from '@/utils/request'

dayjs.extend(utc)
dayjs.extend(timezone)

// 筛选器
const filters = reactive({
  tool: '',
  status: '',
  dateRange: []
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20
})

const total = ref(0)
const loading = ref(false)

// 表格数据
const tableData = ref([])

// 映射前端工具类型到后端
const toolMap = {
  'expense': '费用清单转凭证',
  'translate': '摘要翻译',
  'bank': '银行流水转凭证'
}

// 映射前端状态到后端
const statusMap = {
  'success': '成功',
  'failed': '失败',
  'processing': '处理中'
}

// 映射后端工具类型到前端
const reversedToolMap = {
  '费用清单转凭证': 'expense',
  '摘要翻译': 'translate',
  '银行流水转凭证': 'bank'
}

// 映射后端状态到前端
const reversedStatusMap = {
  '成功': 'success',
  '失败': 'failed',
  '处理中': 'processing'
}

// 加载处理记录
const loadRecords = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params = {
      page: pagination.page,
      page_size: pagination.size
    }

    // 添加过滤条件
    if (filters.tool) {
      params.tool = toolMap[filters.tool]
    }

    if (filters.status) {
      params.status = statusMap[filters.status]
    }

    // 添加日期范围过滤
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = dayjs(filters.dateRange[0]).format('YYYY-MM-DD')
      params.end_date = dayjs(filters.dateRange[1]).format('YYYY-MM-DD')
    }

    // 调用 API
    const response = await request.get('/dashboard/records', { params })

    // 映射数据到表格格式
    tableData.value = response.records.map(record => ({
      id: record.id,
      time: record.time,
      tool: reversedToolMap[record.tool] || record.tool,
      fileName: record.file_name,
      user: record.user || '-',
      avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
      status: reversedStatusMap[record.status] || record.status,
      duration: record.duration,
      resultCount: record.record_count
    }))

    total.value = response.total
  } catch (error) {
    console.error('加载处理记录失败:', error)
    ElMessage.error('加载处理记录失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 工具类型映射
const getToolName = (tool) => {
  const toolMap = {
    expense: '费用清单转凭证',
    translate: '摘要翻译',
    bank: '银行流水转凭证'
  }
  return toolMap[tool] || tool
}

const getToolTagType = (tool) => {
  const typeMap = {
    expense: 'success',
    translate: 'primary',
    bank: 'warning'
  }
  return typeMap[tool] || 'info'
}

// 状态映射
const getStatusName = (status) => {
  const statusMap = {
    success: '成功',
    failed: '失败',
    processing: '处理中'
  }
  return statusMap[status] || status
}

const getStatusTagType = (status) => {
  const typeMap = {
    success: 'success',
    failed: 'danger',
    processing: 'warning'
  }
  return typeMap[status] || 'info'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  // 处理 UTC 时间，转换为本地时间
  if (!time.endsWith('Z') && !time.includes('+')) {
    return dayjs.utc(time).local().format('HH:mm:ss')
  }
  return dayjs(time).format('HH:mm:ss')
}

const formatDate = (time) => {
  if (!time) return '-'
  // 处理 UTC 时间，转换为本地时间
  if (!time.endsWith('Z') && !time.includes('+')) {
    return dayjs.utc(time).local().format('YYYY-MM-DD')
  }
  return dayjs(time).format('YYYY-MM-DD')
}

// 事件处理
const handleSearch = () => {
  pagination.page = 1 // 重置到第一页
  loadRecords()
}

const handleReset = () => {
  Object.assign(filters, {
    tool: '',
    status: '',
    dateRange: []
  })
  pagination.page = 1
  loadRecords()
}

const handleSortChange = ({ prop, order }) => {
  console.log('排序:', prop, order)
  // 实现排序逻辑（暂不实现）
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1 // 重置到第一页
  loadRecords()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadRecords()
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

const viewRecord = (record) => {
  console.log('查看记录:', record)
  ElMessage.info('查看详情功能开发中...')
}

const downloadRecord = (record) => {
  console.log('下载记录:', record)
  ElMessage.success('开始下载...')
}

const retryRecord = (record) => {
  console.log('重试记录:', record)
  ElMessage.info('重试功能开发中...')
}

// 页面加载时获取数据
onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.history-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.filter-card :deep(.el-card__body) {
  padding: 1.5rem;
}

.filter-form {
  margin: 0;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.pagination-container {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  background-color: #fafafa;
}

.truncate {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
