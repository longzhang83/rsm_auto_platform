<template>
  <div class="profile-page">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">个人资料</h1>
      <p class="text-gray-600">管理您的账号信息和安全设置</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 主要内容区域 -->
      <div class="lg:col-span-2 space-y-6">
        <!-- 基本信息 -->
        <el-card class="profile-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-blue-500"><User /></el-icon>
              <span class="text-lg font-semibold">基本信息</span>
            </div>
          </template>

          <div class="user-info">
            <div class="info-item">
              <span class="label">用户名</span>
              <span class="value">{{ userInfo.username }}</span>
            </div>

            <div class="info-item">
              <span class="label">邮箱</span>
              <span class="value">{{ userInfo.email }}</span>
            </div>

            <div class="info-item">
              <span class="label">注册时间</span>
              <span class="value">{{ formatDate(userInfo.created_at) }}</span>
            </div>

            <div class="info-item">
              <span class="label">登录方式</span>
              <el-tag :type="userInfo.login_type === 'wework' ? 'success' : 'primary'">
                {{ userInfo.login_type === 'wework' ? '企业微信' : '密码登录' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 企业微信绑定 -->
        <el-card class="profile-card" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <el-icon class="mr-2 text-green-500"><Link /></el-icon>
                <span class="text-lg font-semibold">企业微信绑定</span>
              </div>
              <el-tag v-if="userInfo.wework_userid" type="success" size="small">已绑定</el-tag>
              <el-tag v-else type="info" size="small">未绑定</el-tag>
            </div>
          </template>

          <div v-if="userInfo.wework_userid" class="wework-info">
            <div class="wework-header">
              <el-avatar
                v-if="userInfo.wework_avatar"
                :src="userInfo.wework_avatar"
                :size="60"
                class="mr-4"
              />
              <div>
                <div class="wework-name">{{ userInfo.wework_name }}</div>
                <div class="wework-userid text-gray-500">ID: {{ userInfo.wework_userid }}</div>
                <div v-if="userInfo.wework_department" class="wework-dept text-gray-500">
                  部门: {{ userInfo.wework_department }}
                </div>
              </div>
            </div>

            <el-divider />

            <el-alert
              v-if="!userInfo.hashed_password"
              type="warning"
              :closable="false"
              show-icon
              class="mb-4"
            >
              <template #title>
                <span class="font-semibold">纯企业微信账号</span>
              </template>
              您当前账号仅通过企业微信登录，未设置密码。如需解绑企业微信，请先设置密码。
            </el-alert>

            <div class="flex space-x-3">
              <el-button
                type="danger"
                plain
                :disabled="!userInfo.hashed_password"
                @click="handleUnbind"
              >
                <el-icon class="mr-1"><Close /></el-icon>
                解除绑定
              </el-button>
            </div>
          </div>

          <div v-else class="wework-unbind">
            <el-empty description="未绑定企业微信账号" :image-size="80">
              <el-button type="success" @click="showBindDialog = true">
                <el-icon class="mr-1"><Link /></el-icon>
                绑定企业微信
              </el-button>
            </el-empty>
          </div>
        </el-card>

        <!-- 安全设置 -->
        <el-card class="profile-card" shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2 text-orange-500"><Lock /></el-icon>
              <span class="text-lg font-semibold">安全设置</span>
            </div>
          </template>

          <div class="security-settings">
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">登录密码</div>
                <div class="security-desc text-gray-500">
                  {{ userInfo.hashed_password ? '已设置' : '未设置（仅企业微信登录）' }}
                </div>
              </div>
              <el-button type="primary" plain @click="showPasswordDialog = true">
                {{ userInfo.hashed_password ? '修改密码' : '设置密码' }}
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 侧边栏 -->
      <div class="lg:col-span-1 space-y-6">
        <!-- 用户头像卡片 -->
        <el-card class="avatar-card text-center" shadow="hover">
          <el-avatar
            :src="userInfo.wework_avatar || undefined"
            :size="100"
            class="mb-4"
          >
            {{ userInfo.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="username text-xl font-bold mb-2">{{ userInfo.username }}</div>
          <div class="email text-gray-500">{{ userInfo.email }}</div>
        </el-card>

        <!-- 账号统计 -->
        <el-card class="stats-card" shadow="hover">
          <template #header>
            <span class="font-semibold">账号统计</span>
          </template>
          <div class="stats">
            <div class="stat-item">
              <div class="stat-value text-blue-500">{{ stats.totalTasks }}</div>
              <div class="stat-label">处理任务</div>
            </div>
            <div class="stat-item">
              <div class="stat-value text-green-500">{{ stats.successRate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      :title="userInfo.hashed_password ? '修改密码' : '设置密码'"
      width="500px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item v-if="userInfo.hashed_password" label="当前密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码（6-100字符）"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 绑定企业微信对话框 -->
    <el-dialog v-model="showBindDialog" title="绑定企业微信" width="500px">
      <div class="bind-wework-content text-center">
        <p class="mb-4 text-gray-600">请使用企业微信扫描二维码完成绑定</p>

        <div v-if="bindLoading" class="loading-container">
          <el-icon class="is-loading" size="48">
            <Loading />
          </el-icon>
          <p class="mt-4">正在加载二维码...</p>
        </div>

        <div v-else-if="bindError" class="error-container">
          <el-alert type="error" :closable="false" show-icon>
            {{ bindError }}
          </el-alert>
          <el-button type="primary" class="mt-4" @click="loadBindQRCode">
            重新加载
          </el-button>
        </div>

        <div v-else id="bind-qr-container" class="qr-container mx-auto"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import dayjs from 'dayjs'

const authStore = useAuthStore()
const passwordFormRef = ref(null)
const showPasswordDialog = ref(false)
const showBindDialog = ref(false)
const passwordLoading = ref(false)
const bindLoading = ref(false)
const bindError = ref('')
const bindConfig = ref(null)

// 用户信息
const userInfo = computed(() => authStore.user || {})

// 账号统计（模拟数据，实际应从API获取）
const stats = reactive({
  totalTasks: 156,
  successRate: 98
})

// 修改密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码验证规则
const passwordRules = computed(() => {
  const rules = {
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: '请再次输入新密码', trigger: 'blur' },
      {
        validator: (rule, value, callback) => {
          if (value !== passwordForm.newPassword) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ]
  }

  // 如果已有密码，添加当前密码验证
  if (userInfo.value.hashed_password) {
    rules.oldPassword = [
      { required: true, message: '请输入当前密码', trigger: 'blur' }
    ]
  }

  return rules
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()

    passwordLoading.value = true
    try {
      await request.post('/auth/change-password', {
        old_password: passwordForm.oldPassword || null,
        new_password: passwordForm.newPassword
      })

      ElMessage.success('密码修改成功')
      showPasswordDialog.value = false
      resetPasswordForm()

      // 刷新用户信息
      await authStore.initAuth()
    } finally {
      passwordLoading.value = false
    }
  } catch (error) {
    // 验证失败，不做处理
  }
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

// 解绑企业微信
const handleUnbind = async () => {
  try {
    await ElMessageBox.confirm(
      '解绑后将无法使用企业微信扫码登录，确定要解除绑定吗？',
      '确认解绑',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.post('/auth/wework/unbind')
    ElMessage.success('企业微信账号已解绑')

    // 刷新用户信息
    await authStore.initAuth()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('解绑失败:', error)
    }
  }
}

// 加载绑定二维码
const loadBindQRCode = async () => {
  bindLoading.value = true
  bindError.value = ''

  try {
    const config = await request.get('/auth/wework/config')

    if (!config.enabled) {
      bindError.value = '企业微信登录未启用'
      bindLoading.value = false
      return
    }

    bindConfig.value = config

    // 等待DOM更新
    setTimeout(() => {
      renderBindQRCode()
    }, 100)
  } catch (error) {
    console.error('获取企业微信配置失败:', error)
    bindError.value = '获取企业微信配置失败'
    bindLoading.value = false
  }
}

// 渲染绑定二维码
const renderBindQRCode = () => {
  if (!bindConfig.value) return

  // 加载企业微信JS SDK
  if (typeof window.WwLogin === 'undefined') {
    const script = document.createElement('script')
    script.src = 'https://rescdn.qqmail.com/node/ww/wwopenmng/js/sso/wwLogin-1.0.0.js'
    script.onload = () => {
      createQRCode()
    }
    script.onerror = () => {
      bindError.value = '加载企业微信SDK失败'
      bindLoading.value = false
    }
    document.head.appendChild(script)
  } else {
    createQRCode()
  }
}

// 创建二维码
const createQRCode = () => {
  try {
    const container = document.getElementById('bind-qr-container')
    if (container) {
      container.innerHTML = ''
    }

    new window.WwLogin({
      id: 'bind-qr-container',
      appid: bindConfig.value.corp_id,
      agentid: bindConfig.value.agent_id,
      redirect_uri: encodeURIComponent(window.location.origin + '/profile/wework/bind/callback'),
      state: bindConfig.value.state,
      href: '',
    })

    bindLoading.value = false
  } catch (error) {
    console.error('创建二维码失败:', error)
    bindError.value = '创建二维码失败'
    bindLoading.value = false
  }
}

// 监听绑定对话框打开
watch(showBindDialog, (newVal) => {
  if (newVal) {
    loadBindQRCode()
  }
})

// 监听密码对话框关闭
watch(showPasswordDialog, (newVal) => {
  if (!newVal) {
    resetPasswordForm()
  }
})

onMounted(() => {
  // 如果用户信息为空，尝试初始化
  if (!authStore.user) {
    authStore.initAuth()
  }
})
</script>

<style scoped>
.profile-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.profile-card :deep(.el-card__body) {
  padding: 1.5rem;
}

.user-info,
.security-settings {
  space-y: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #666;
  font-weight: 500;
}

.info-item .value {
  color: #333;
  font-weight: 600;
}

.wework-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.wework-name {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.wework-userid,
.wework-dept {
  font-size: 14px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.security-item:last-child {
  border-bottom: none;
}

.security-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.security-desc {
  font-size: 14px;
}

.avatar-card {
  padding: 1.5rem;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.qr-container {
  display: inline-block;
}

:deep(#bind-qr-container iframe) {
  width: 300px !important;
  height: 360px !important;
  border: none;
}

.loading-container,
.error-container {
  padding: 40px 20px;
  text-align: center;
}
</style>
