<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="!processing"
    center
  >
    <template #header>
      <div class="flex items-center">
        <el-icon class="mr-2" :class="processing ? 'text-blue-500' : 'text-green-500'">
          <Loading v-if="processing" />
          <CircleCheckFilled v-else />
        </el-icon>
        <span class="text-lg font-semibold">{{ title }}</span>
      </div>
    </template>

    <div class="progress-content">
      <!-- 进度条 -->
      <el-progress
        :percentage="progress.percentage"
        :status="progress.status"
        :stroke-width="12"
      >
        <template #default="{ percentage }">
          <span class="percentage-value">{{ percentage }}%</span>
        </template>
      </el-progress>

      <!-- 进度信息 -->
      <div class="progress-info mt-6">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <!-- 已处理进度 -->
          <div class="bg-gray-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">已处理</div>
            <div class="font-semibold text-lg">{{ progress.completed }} / {{ progress.total }}</div>
          </div>

          <!-- 已用时间 -->
          <div class="bg-gray-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">已用时间</div>
            <div class="font-semibold text-lg">{{ progress.elapsedTime }}</div>
          </div>

          <!-- 当前处理项 -->
          <div class="bg-blue-50 p-3 rounded col-span-2" v-if="progress.currentItem">
            <div class="text-gray-500 text-xs mb-1">当前处理</div>
            <div class="font-semibold text-blue-600 text-sm truncate">{{ progress.currentItem }}</div>
          </div>

          <!-- 处理速度 -->
          <div class="bg-green-50 p-3 rounded" v-if="progress.speed">
            <div class="text-gray-500 text-xs mb-1">处理速度</div>
            <div class="font-semibold text-green-600 text-sm">{{ progress.speed }}</div>
          </div>

          <!-- 任务状态 -->
          <div class="bg-yellow-50 p-3 rounded">
            <div class="text-gray-500 text-xs mb-1">任务状态</div>
            <div class="font-semibold text-yellow-600 text-sm">
              {{ progress.percentage >= 100 ? '处理完成' : '处理中...' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-center">
        <el-button
          v-if="progress.percentage < 100 && processing"
          @click="handleCancel"
          :disabled="!cancellable"
        >
          取消处理
        </el-button>
        <el-button
          v-else
          type="success"
          @click="handleClose"
        >
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, CircleCheckFilled } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '处理进度'
  },
  processing: {
    type: Boolean,
    default: false
  },
  cancellable: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'cancel', 'close'])

// 进度数据
const progress = reactive({
  percentage: 0,
  status: 'success',
  completed: 0,
  total: 0,
  elapsedTime: '0秒',
  currentItem: '',
  speed: ''
})

// 开始时间
const startTime = ref(null)

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 更新进度
const updateProgress = (data) => {
  console.log('翻译进度更新:', data)

  progress.percentage = Math.round(data.percentage || 0)
  progress.completed = data.completed || 0
  progress.total = data.total || 0
  progress.currentItem = data.current_item || data.message || ''
  progress.status = (data.percentage >= 100) ? 'success' : 'success'

  // 计算处理速度
  if (progress.completed > 0) {
    const elapsedSeconds = startTime.value ? Math.floor((Date.now() - startTime.value) / 1000) : 0
    const speed = elapsedSeconds > 0 ? Math.floor(progress.completed / elapsedSeconds * 60) : 0
    progress.speed = `${speed} 项/分钟`
  } else {
    progress.speed = '0 项/分钟'
  }

  // 更新已用时间
  if (startTime.value) {
    const elapsedSeconds = Math.floor((Date.now() - startTime.value) / 1000)
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
  } else {
    progress.elapsedTime = '0秒'
  }
}

// 重置进度
const resetProgress = () => {
  progress.percentage = 0
  progress.completed = 0
  progress.total = 0
  progress.elapsedTime = '0秒'
  progress.currentItem = ''
  progress.speed = '0 项/分钟'
  progress.status = 'success'
}

// 完全重置（包括开始时间）
const fullReset = () => {
  resetProgress()
  startTime.value = null
}

// 开始处理
const startProcessing = () => {
  fullReset()
  startTime.value = Date.now()
}

// 完成处理
const completeProcessing = () => {
  progress.percentage = 100
  progress.currentItem = '处理完成！'
  progress.status = 'success'
}

// 取消处理
const handleCancel = () => {
  ElMessageBox.confirm('确定要取消处理吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '继续处理',
    type: 'warning'
  }).then(() => {
    emit('cancel')
  }).catch(() => {
    // 用户取消，不做任何操作
  })
}

// 关闭对话框
const handleClose = () => {
  emit('close')
}

// 监听处理状态变化
watch(() => props.processing, (newVal) => {
  if (newVal) {
    startProcessing()
  } else {
    completeProcessing()
  }
})

// 暴露方法给父组件
defineExpose({
  updateProgress,
  resetProgress,
  startProcessing,
  completeProcessing
})
</script>

<style scoped>
.progress-content {
  padding: 1rem 0;
}

.percentage-value {
  font-weight: bold;
  color: #409eff;
}

.progress-info {
  margin-top: 1.5rem;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>