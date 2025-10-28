<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section mb-6">
      <div class="bg-gradient-to-r from-brand-600 to-brand-800 rounded-xl p-8 text-white">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold mb-2">欢迎使用容诚税务师事务所自动化工具平台</h1>
            <p class="text-brand-100 text-lg">智能化税务处理，提升工作效率，降低人工成本</p>
          </div>
          <div class="text-right">
            <p class="text-brand-100 mb-1">当前时间</p>
            <p class="text-2xl font-semibold">{{ currentTime }}</p>
            <p class="text-brand-100">{{ currentDate }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具卡片 -->
    <div class="tools-section mb-8">
      <h2 class="text-2xl font-bold text-gray-800 mb-6">核心工具</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- 费用清单转凭证 -->
        <div
          class="tool-card card-shadow bg-white rounded-xl p-6 cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-xl"
          @click="navigateToTool('/expense-to-voucher')"
        >
          <div class="flex items-center mb-4">
            <div class="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mr-4">
              <el-icon class="text-2xl text-success-600"><DocumentCopy /></el-icon>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-800">费用清单转凭证</h3>
              <p class="text-sm text-gray-500">高效处理</p>
            </div>
          </div>
          <p class="text-gray-600 mb-4">将费用报销清单自动转换为标准会计凭证格式，支持多种费用类型和科目映射。</p>
          <div class="flex items-center justify-between">
            <el-tag type="success" size="small">可用</el-tag>
            <el-icon class="text-gray-400"><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 摘要翻译 -->
        <div
          class="tool-card card-shadow bg-white rounded-xl p-6 cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-xl"
          @click="navigateToTool('/summary-translate')"
        >
          <div class="flex items-center mb-4">
            <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mr-4">
              <el-icon class="text-2xl text-primary-600"><Translation /></el-icon>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-800">摘要翻译</h3>
              <p class="text-sm text-gray-500">AI智能翻译</p>
            </div>
          </div>
          <p class="text-gray-600 mb-4">基于AI技术的中文摘要自动翻译为英文，支持批量处理和术语库管理。</p>
          <div class="flex items-center justify-between">
            <el-tag type="success" size="small">可用</el-tag>
            <el-icon class="text-gray-400"><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 银行流水转凭证 -->
        <div class="tool-card card-shadow bg-white rounded-xl p-6 opacity-75 cursor-not-allowed">
          <div class="flex items-center mb-4">
            <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mr-4">
              <el-icon class="text-2xl text-gray-400"><CreditCard /></el-icon>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-800">银行流水转凭证</h3>
              <p class="text-sm text-gray-500">开发中</p>
            </div>
          </div>
          <p class="text-gray-600 mb-4">自动识别银行流水数据，智能分类并生成对应会计凭证，支持多银行格式。</p>
          <div class="flex items-center justify-between">
            <el-tag type="info" size="small">开发中</el-tag>
            <el-icon class="text-gray-400"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计数据 -->
    <div class="stats-section mb-8">
      <h2 class="text-2xl font-bold text-gray-800 mb-6">今日统计</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="bg-white rounded-lg p-6 card-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-500">处理凭证数量</span>
            <el-icon class="text-green-500"><TrendCharts /></el-icon>
          </div>
          <div class="text-3xl font-bold text-gray-800">{{ stats.voucherCount }}</div>
          <div class="text-sm text-green-600 mt-2">较昨日 +12%</div>
        </div>

        <div class="bg-white rounded-lg p-6 card-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-500">翻译摘要数量</span>
            <el-icon class="text-blue-500"><ChatDotRound /></el-icon>
          </div>
          <div class="text-3xl font-bold text-gray-800">{{ stats.translateCount }}</div>
          <div class="text-sm text-blue-600 mt-2">较昨日 +8%</div>
        </div>

        <div class="bg-white rounded-lg p-6 card-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-500">处理总金额</span>
            <el-icon class="text-yellow-500"><Money /></el-icon>
          </div>
          <div class="text-3xl font-bold text-gray-800">¥{{ stats.totalAmount.toLocaleString() }}</div>
          <div class="text-sm text-yellow-600 mt-2">较昨日 +5%</div>
        </div>

        <div class="bg-white rounded-lg p-6 card-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-500">平均处理时间</span>
            <el-icon class="text-purple-500"><Timer /></el-icon>
          </div>
          <div class="text-3xl font-bold text-gray-800">{{ stats.avgProcessTime }}s</div>
          <div class="text-sm text-purple-600 mt-2">较昨日 -15%</div>
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
          <el-table-column prop="tool" label="使用工具" width="120">
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
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="text" size="small" @click="viewRecord(scope.row)">查看</el-button>
              <el-button type="text" size="small" @click="downloadRecord(scope.row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'

const router = useRouter()

// 时间相关
const currentTime = ref('')
const currentDate = ref('')
let timeInterval = null

// 统计数据
const stats = ref({
  voucherCount: 156,
  translateCount: 89,
  totalAmount: 456780,
  avgProcessTime: 3.2
})

// 最近记录
const recentRecords = ref([
  {
    time: '2025-01-15 14:32:15',
    tool: '费用清单转凭证',
    fileName: '2025年1月费用报销表.xlsx',
    status: '成功',
    duration: '2.8s'
  },
  {
    time: '2025-01-15 14:28:42',
    tool: '摘要翻译',
    fileName: '费用摘要翻译.xlsx',
    status: '成功',
    duration: '1.5s'
  },
  {
    time: '2025-01-15 14:15:30',
    tool: '费用清单转凭证',
    fileName: '差旅费报销单.xlsx',
    status: '失败',
    duration: '5.2s'
  },
  {
    time: '2025-01-15 13:52:18',
    tool: '摘要翻译',
    fileName: 'Q4费用报表.xlsx',
    status: '成功',
    duration: '3.1s'
  }
])

// 更新时间
const updateTime = () => {
  currentTime.value = dayjs().format('HH:mm:ss')
  currentDate.value = dayjs().format('YYYY年MM月DD日 dddd')
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

// 查看记录
const viewRecord = (record) => {
  console.log('查看记录:', record)
}

// 下载记录
const downloadRecord = (record) => {
  console.log('下载记录:', record)
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.tool-card {
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.tool-card:hover {
  border-color: #dc2626;
}

.welcome-section {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
}

/* 统计卡片动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-section > div > div {
  animation: fadeInUp 0.6s ease-out;
}

.stats-section > div > div:nth-child(1) { animation-delay: 0.1s; }
.stats-section > div > div:nth-child(2) { animation-delay: 0.2s; }
.stats-section > div > div:nth-child(3) { animation-delay: 0.3s; }
.stats-section > div > div:nth-child(4) { animation-delay: 0.4s; }
</style>