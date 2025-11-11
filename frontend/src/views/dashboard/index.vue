<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section mb-8">
      <div class="welcome-gradient rounded-2xl p-10 text-white relative overflow-hidden">
        <!-- 装饰性背景元素 -->
        <div class="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-32 -mt-32"></div>
        <div class="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-24 -mb-24"></div>

        <div class="relative z-10 flex items-center justify-between">
          <div class="max-w-2xl">
            <div class="flex items-center mb-4">
              <div class="w-3 h-3 bg-white rounded-full mr-3 animate-pulse"></div>
              <h1 class="text-4xl font-bold mb-0 tracking-tight">容诚税务师事务所</h1>
            </div>
            <h2 class="text-2xl font-light mb-4 text-blue-100">智能化自动化工具平台</h2>
            <p class="text-lg text-blue-50 leading-relaxed">基于人工智能的税务处理系统，显著提升工作效率，大幅降低人工成本，让税务工作更加精准高效</p>

            <!-- 快速操作按钮 -->
            <div class="flex space-x-4 mt-8">
              <button class="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1">
                开始使用
              </button>
              <button class="border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-all duration-200">
                了解更多
              </button>
            </div>
          </div>

          <div class="text-right bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg rounded-xl p-6 border border-white border-opacity-20">
            <div class="text-blue-100 text-sm font-medium mb-2">系统时间</div>
            <div class="text-3xl font-bold mb-1">{{ currentTime }}</div>
            <div class="text-blue-100">{{ currentDate }}</div>
            <div class="mt-4 pt-4 border-t border-blue-300 border-opacity-30">
              <div class="flex items-center justify-end text-blue-100">
                <div class="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                <span class="text-sm">系统运行正常</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具卡片 -->
    <div class="tools-section mb-10">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h2 class="text-3xl font-bold text-gray-800 mb-2">核心功能工具</h2>
          <p class="text-gray-600">专业的税务处理工具，提升您的工作效率</p>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-600">所有服务运行正常</span>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <!-- 费用清单转凭证 -->
        <div
          class="enhanced-tool-card bg-white rounded-2xl p-8 cursor-pointer group"
          @click="navigateToTool('/expense-to-voucher')"
        >
          <div class="flex items-start justify-between mb-6">
            <div class="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110">
              <el-icon class="text-3xl text-white"><DocumentCopy /></el-icon>
            </div>
            <div class="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">
              核心功能
            </div>
          </div>

          <div class="mb-6">
            <h3 class="text-xl font-bold text-gray-800 mb-3">费用清单转凭证</h3>
            <p class="text-gray-600 leading-relaxed">智能识别费用类型，自动映射会计科目，一键生成标准会计凭证，支持批量处理多种费用类型。</p>
          </div>

          <div class="flex items-center justify-between pt-6 border-t border-gray-100">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full"></div>
              <span class="text-sm font-medium text-green-700">运行正常</span>
            </div>
            <div class="flex items-center text-blue-600 group-hover:text-blue-700 transition-colors duration-200">
              <span class="text-sm font-medium mr-2">立即使用</span>
              <el-icon class="transform group-hover:translate-x-1 transition-transform duration-200"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <!-- 摘要翻译 -->
        <div
          class="enhanced-tool-card bg-white rounded-2xl p-8 cursor-pointer group"
          @click="navigateToTool('/summary-translate')"
        >
          <div class="flex items-start justify-between mb-6">
            <div class="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110">
              <el-icon class="text-3xl text-white"><Document /></el-icon>
            </div>
            <div class="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
              AI 智能
            </div>
          </div>

          <div class="mb-6">
            <h3 class="text-xl font-bold text-gray-800 mb-3">智能摘要翻译</h3>
            <p class="text-gray-600 leading-relaxed">基于先进的AI翻译引擎，准确翻译中文摘要为英文，支持专业术语库和批量处理功能。</p>
          </div>

          <div class="flex items-center justify-between pt-6 border-t border-gray-100">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span class="text-sm font-medium text-blue-700">运行正常</span>
            </div>
            <div class="flex items-center text-blue-600 group-hover:text-blue-700 transition-colors duration-200">
              <span class="text-sm font-medium mr-2">立即使用</span>
              <el-icon class="transform group-hover:translate-x-1 transition-transform duration-200"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <!-- 银行流水转凭证 -->
        <div
          class="enhanced-tool-card bg-white rounded-2xl p-8 cursor-pointer group"
          @click="navigateToTool('/bank-to-voucher')"
        >
          <div class="flex items-start justify-between mb-6">
            <div class="w-16 h-16 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110">
              <el-icon class="text-3xl text-white"><CreditCard /></el-icon>
            </div>
            <div class="bg-yellow-100 text-yellow-800 text-xs font-semibold px-3 py-1 rounded-full">
              财务工具
            </div>
          </div>

          <div class="mb-6">
            <h3 class="text-xl font-bold text-gray-800 mb-3">银行流水转凭证</h3>
            <p class="text-gray-600 leading-relaxed">自动识别银行流水数据，智能分类交易类型，自动生成对应会计凭证，支持多银行格式。</p>
          </div>

          <div class="flex items-center justify-between pt-6 border-t border-gray-100">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-green-500 rounded-full"></div>
              <span class="text-sm font-medium text-green-700">运行正常</span>
            </div>
            <div class="flex items-center text-blue-600 group-hover:text-blue-700 transition-colors duration-200">
              <span class="text-sm font-medium mr-2">立即使用</span>
              <el-icon class="transform group-hover:translate-x-1 transition-transform duration-200"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计数据 -->
    <div class="stats-section mb-10">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h2 class="text-3xl font-bold text-gray-800 mb-2">实时统计数据</h2>
          <p class="text-gray-600">今日系统运行情况与处理效率分析</p>
        </div>
        <div class="flex items-center space-x-4">
          <span class="text-sm text-gray-500">最后更新: {{ lastUpdateTime }}</span>
          <button @click="refreshStats" class="text-blue-600 hover:text-blue-700 transition-colors duration-200">
            <el-icon class="mr-1"><Refresh /></el-icon>
            刷新
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="stat-card group">
          <div class="stat-card-header">
            <div class="stat-icon green">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-trend positive">
              <el-icon><CaretTop /></el-icon>
              <span>12%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.voucherCount }}</div>
            <div class="stat-label">处理凭证数量</div>
          </div>
          <div class="stat-chart">
            <div class="chart-bar" style="height: 60%"></div>
            <div class="chart-bar" style="height: 80%"></div>
            <div class="chart-bar" style="height: 45%"></div>
            <div class="chart-bar" style="height: 90%"></div>
            <div class="chart-bar" style="height: 70%"></div>
            <div class="chart-bar" style="height: 100%"></div>
          </div>
        </div>

        <div class="stat-card group">
          <div class="stat-card-header">
            <div class="stat-icon blue">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="stat-trend positive">
              <el-icon><CaretTop /></el-icon>
              <span>8%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.translateCount }}</div>
            <div class="stat-label">翻译摘要数量</div>
          </div>
          <div class="stat-chart">
            <div class="chart-bar" style="height: 40%"></div>
            <div class="chart-bar" style="height: 60%"></div>
            <div class="chart-bar" style="height: 55%"></div>
            <div class="chart-bar" style="height: 85%"></div>
            <div class="chart-bar" style="height: 65%"></div>
            <div class="chart-bar" style="height: 75%"></div>
          </div>
        </div>

        <div class="stat-card group">
          <div class="stat-card-header">
            <div class="stat-icon yellow">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-trend positive">
              <el-icon><CaretTop /></el-icon>
              <span>持续增长</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ (stats.timeSavedTotal / 60).toFixed(1) }}h</div>
            <div class="stat-label">累计节约时间</div>
            <div class="time-breakdown mt-3 text-xs text-gray-600 space-y-1">
              <div class="flex justify-between">
                <span>今日:</span>
                <span class="font-semibold">{{ (stats.timeSavedToday / 60).toFixed(1) }}小时</span>
              </div>
              <div class="flex justify-between">
                <span>本周:</span>
                <span class="font-semibold">{{ (stats.timeSavedWeek / 60).toFixed(1) }}小时</span>
              </div>
              <div class="flex justify-between">
                <span>本月:</span>
                <span class="font-semibold">{{ (stats.timeSavedMonth / 60).toFixed(1) }}小时</span>
              </div>
              <div class="flex justify-between">
                <span>本年:</span>
                <span class="font-semibold">{{ (stats.timeSavedYear / 60).toFixed(1) }}小时</span>
              </div>
            </div>
          </div>
        </div>

        <div class="stat-card group">
          <div class="stat-card-header">
            <div class="stat-icon purple">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-trend negative">
              <el-icon><CaretBottom /></el-icon>
              <span>15%</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.avgProcessTime }}s</div>
            <div class="stat-label">平均处理时间</div>
          </div>
          <div class="stat-chart">
            <div class="chart-bar" style="height: 100%"></div>
            <div class="chart-bar" style="height: 85%"></div>
            <div class="chart-bar" style="height: 90%"></div>
            <div class="chart-bar" style="height: 70%"></div>
            <div class="chart-bar" style="height: 60%"></div>
            <div class="chart-bar" style="height: 40%"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近处理记录 -->
    <div class="recent-section">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">最近处理记录</h2>
        <el-button type="text" @click="navigateToTool('/history')">查看全部</el-button>
      </div>
      <div class="bg-white rounded-lg card-shadow">
        <el-table :data="recentRecords" style="width: 100%">
          <el-table-column prop="time" label="处理时间" width="180" />
          <el-table-column prop="tool" label="使用工具" width="140">
            <template #default="scope">
              <el-tag :type="getToolTagType(scope.row.tool)" size="small">
                {{ scope.row.tool }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fileName" label="文件名称" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '成功' ? 'success' : 'danger'" size="small">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="处理时长" width="120" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getDashboardData } from '@/api/dashboard'

const router = useRouter()

// 时间相关
const currentTime = ref('')
const currentDate = ref('')
const lastUpdateTime = ref('')
let timeInterval = null

// 加载状态
const loading = ref(false)

// 统计数据
const stats = ref({
  voucherCount: 0,
  translateCount: 0,
  avgProcessTime: 0,
  timeSavedToday: 0,
  timeSavedWeek: 0,
  timeSavedMonth: 0,
  timeSavedYear: 0,
  timeSavedTotal: 0
})

// 最近记录
const recentRecords = ref([])

// 更新时间
const updateTime = () => {
  currentTime.value = dayjs().format('HH:mm:ss')
  currentDate.value = dayjs().format('YYYY年MM月DD日 dddd')
}

// 加载Dashboard数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    const data = await getDashboardData()

    // 更新统计数据
    stats.value.voucherCount = data.stats.voucher_count
    stats.value.translateCount = data.stats.translate_count
    stats.value.avgProcessTime = data.stats.avg_process_time
    stats.value.timeSavedToday = data.stats.time_saved_today
    stats.value.timeSavedWeek = data.stats.time_saved_week
    stats.value.timeSavedMonth = data.stats.time_saved_month
    stats.value.timeSavedYear = data.stats.time_saved_year
    stats.value.timeSavedTotal = data.stats.time_saved_total

    // 更新最近记录 - 转换字段名
    recentRecords.value = data.recent_records.map(record => ({
      id: record.id,
      time: record.time,
      tool: record.tool,
      fileName: record.file_name,
      status: record.status,
      duration: record.duration,
      recordCount: record.record_count
    }))

    lastUpdateTime.value = data.last_update_time
  } catch (error) {
    console.error('加载Dashboard数据失败:', error)
    ElMessage.error('加载Dashboard数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 刷新统计数据
const refreshStats = async () => {
  await loadDashboardData()
  ElMessage.success('数据已刷新')
}

// 导航到工具页面
const navigateToTool = (path) => {
  router.push(path)
}

// 获取工具标签类型
const getToolTagType = (tool) => {
  const typeMap = {
    '费用清单转凭证': 'success',
    '摘要翻译': 'primary',
    '银行流水转凭证': 'warning'
  }
  return typeMap[tool] || 'info'
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  // 加载Dashboard数据
  loadDashboardData()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* 欢迎区域渐变背景 */
.welcome-gradient {
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-dark) 50%, var(--brand-secondary) 100%);
  position: relative;
  overflow: hidden;
}

.welcome-gradient::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

/* 增强工具卡片 */
.enhanced-tool-card {
  border: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.enhanced-tool-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(30, 79, 175, 0.02) 50%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.enhanced-tool-card:hover::before {
  opacity: 1;
}

.enhanced-tool-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

/* 统计卡片 */
.stat-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-secondary));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-icon.green {
  background: linear-gradient(135deg, #06D6A0 0%, #05A67C 100%);
}

.stat-icon.blue {
  background: linear-gradient(135deg, #118AB2 0%, #0C7B93 100%);
}

.stat-icon.yellow {
  background: linear-gradient(135deg, #FFD166 0%, #FFC43D 100%);
}

.stat-icon.purple {
  background: linear-gradient(135deg, #7209B7 0%, #560BAD 100%);
}

.stat-trend {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 8px;
}

.stat-trend.positive {
  color: #05A67C;
  background: rgba(6, 214, 160, 0.1);
}

.stat-trend.negative {
  color: var(--brand-secondary);
  background: rgba(230, 57, 70, 0.1);
}

.stat-content {
  margin-bottom: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--brand-gray-800);
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--brand-gray-500);
  font-weight: 500;
}

.stat-chart {
  display: flex;
  align-items: end;
  justify-content: space-between;
  height: 40px;
  gap: 4px;
}

.chart-bar {
  flex: 1;
  background: linear-gradient(to top, var(--brand-primary), var(--brand-primary-lighter));
  border-radius: 2px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.stat-card:hover .chart-bar {
  opacity: 1;
}

/* 记录表格样式 */
.recent-section .bg-white {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.recent-section :deep(.el-table) {
  border-radius: 20px;
}

.recent-section :deep(.el-table__header) {
  background: var(--brand-gray-50);
}

.recent-section :deep(.el-table th) {
  background: transparent;
  border: none;
  font-weight: 600;
  color: var(--brand-gray-700);
  padding: 20px 16px;
}

.recent-section :deep(.el-table td) {
  border: none;
  padding: 16px;
  border-bottom: 1px solid var(--brand-gray-100);
}

.recent-section :deep(.el-table tr:hover > td) {
  background: var(--brand-gray-50);
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.welcome-section {
  animation: slideInLeft 0.8s ease-out;
}

.tools-section > div > div {
  animation: fadeInUp 0.6s ease-out;
}

.tools-section > div > div:nth-child(1) { animation-delay: 0.1s; }
.tools-section > div > div:nth-child(2) { animation-delay: 0.2s; }
.tools-section > div > div:nth-child(3) { animation-delay: 0.3s; }

.stats-section > div > div {
  animation: fadeInUp 0.6s ease-out;
}

.stats-section > div > div:nth-child(1) { animation-delay: 0.1s; }
.stats-section > div > div:nth-child(2) { animation-delay: 0.2s; }
.stats-section > div > div:nth-child(3) { animation-delay: 0.3s; }
.stats-section > div > div:nth-child(4) { animation-delay: 0.4s; }

.recent-section {
  animation: fadeInUp 0.8s ease-out 0.6s both;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 0 16px;
  }

  .welcome-gradient {
    padding: 24px !important;
  }

  .welcome-gradient .flex {
    flex-direction: column;
    text-align: center;
  }

  .enhanced-tool-card {
    padding: 24px;
  }

  .stat-card {
    padding: 20px;
  }

  .stat-number {
    font-size: 28px;
  }
}
</style>