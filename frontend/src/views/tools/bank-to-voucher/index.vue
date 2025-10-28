<template>
  <div class="bank-to-voucher">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">银行流水转凭证</h1>
      <p class="text-gray-600">自动识别银行流水数据，智能分类并生成对应会计凭证，支持多银行格式</p>
    </div>

    <!-- 开发中提示 -->
    <el-card class="development-card" shadow="hover">
      <div class="development-content">
        <div class="text-center py-12">
          <el-icon class="development-icon text-6xl text-gray-400 mb-4">
            <Tools />
          </el-icon>
          <h2 class="text-2xl font-bold text-gray-700 mb-4">功能开发中</h2>
          <p class="text-gray-500 mb-6 max-w-2xl mx-auto">
            银行流水转凭证功能正在紧锣密鼓地开发中，该功能将支持自动识别银行流水数据、智能分类、
            多银行格式适配、自动科目匹配等强大功能，敬请期待！
          </p>

          <!-- 功能预览 -->
          <div class="features-preview mt-8">
            <h3 class="text-lg font-semibold text-gray-700 mb-6">即将推出的功能</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div class="feature-preview-item">
                <div class="feature-icon bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-blue-600"><CreditCard /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">多银行支持</h4>
                <p class="text-sm text-gray-500">
                  支持主流银行流水格式导入，自动识别交易类型
                </p>
              </div>

              <div class="feature-preview-item">
                <div class="feature-icon bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-green-600"><Magic /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">智能分类</h4>
                <p class="text-sm text-gray-500">
                  AI驱动的交易分类，自动识别收入、支出、转账等
                </p>
              </div>

              <div class="feature-preview-item">
                <div class="feature-icon bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-purple-600"><Tickets /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">科目匹配</h4>
                <p class="text-sm text-gray-500">
                  智能匹配会计科目，支持自定义映射规则
                </p>
              </div>

              <div class="feature-preview-item">
                <div class="feature-icon bg-yellow-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-yellow-600"><Document /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">批量处理</h4>
                <p class="text-sm text-gray-500">
                  支持大批量流水数据处理，提高工作效率
                </p>
              </div>

              <div class="feature-preview-item">
                <div class="feature-icon bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-red-600"><Warning /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">异常检测</h4>
                <p class="text-sm text-gray-500">
                  自动识别异常交易，提供风险预警
                </p>
              </div>

              <div class="feature-preview-item">
                <div class="feature-icon bg-indigo-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <el-icon class="text-2xl text-indigo-600"><DataAnalysis /></el-icon>
                </div>
                <h4 class="font-semibold text-gray-700 mb-2">数据统计</h4>
                <p class="text-sm text-gray-500">
                  提供详细的交易统计和分析报告
                </p>
              </div>
            </div>
          </div>

          <!-- 通知订阅 -->
          <div class="notification-section mt-8">
            <el-divider>
              <span class="text-gray-500">功能上线通知</span>
            </el-divider>
            <div class="notification-form mt-6 max-w-md mx-auto">
              <el-form :model="notificationForm" inline>
                <el-form-item>
                  <el-input
                    v-model="notificationForm.email"
                    placeholder="输入您的邮箱地址"
                    clearable
                    style="width: 250px"
                  >
                    <template #prepend>
                      <el-icon><Message /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="subscribeNotification">
                    <el-icon class="mr-1"><Bell /></el-icon>
                    订阅通知
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <!-- 预计上线时间 -->
          <div class="timeline-section mt-8">
            <el-divider>
              <span class="text-gray-500">开发进度</span>
            </el-divider>
            <div class="timeline mt-6">
              <el-steps :active="2" align-center>
                <el-step title="需求分析" description="已完成" />
                <el-step title="功能设计" description="已完成" />
                <el-step title="开发实现" description="进行中" />
                <el-step title="测试验证" description="待开始" />
                <el-step title="正式发布" description="预计2025年Q2" />
              </el-steps>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const notificationForm = reactive({
  email: ''
})

const subscribeNotification = () => {
  if (!notificationForm.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(notificationForm.email)) {
    ElMessage.warning('请输入正确的邮箱地址')
    return
  }

  ElMessage.success('订阅成功！功能上线后会第一时间通知您')
  notificationForm.email = ''
}
</script>

<style scoped>
.bank-to-voucher {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.development-card {
  min-height: 600px;
}

.development-content {
  padding: 2rem;
}

.development-icon {
  font-size: 4rem;
}

.features-preview {
  text-align: left;
}

.feature-preview-item {
  text-align: center;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
}

.feature-preview-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  transition: transform 0.3s ease;
}

.feature-preview-item:hover .feature-icon {
  transform: scale(1.1);
}

.notification-section {
  background-color: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
}

.timeline-section {
  padding: 2rem 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .features-preview .grid {
    grid-template-columns: 1fr;
  }

  .notification-form .el-form {
    flex-direction: column;
    align-items: center;
  }

  .notification-form .el-form-item {
    margin-right: 0;
    margin-bottom: 1rem;
  }

  .notification-form .el-button {
    width: 100%;
  }
}
</style>