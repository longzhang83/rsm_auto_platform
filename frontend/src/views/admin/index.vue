<template>
  <div class="admin-page">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">管理后台</h1>
      <p class="text-gray-600">查看系统用户统计信息</p>
    </div>

    <!-- 权限检查 -->
    <el-alert
      v-if="!isAdmin"
      title="无权限访问"
      type="error"
      :closable="false"
      show-icon
      class="mb-6"
    >
      您没有管理员权限，无法访问此页面。
    </el-alert>

    <div v-else>
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bg-blue-100">
              <el-icon color="#409eff" size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总用户数</div>
              <div class="stat-value text-blue-500">{{ stats.total_users || 0 }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bg-green-100">
              <el-icon color="#67c23a" size="32"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">密码登录</div>
              <div class="stat-value text-green-500">{{ stats.password_users || 0 }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bg-orange-100">
              <el-icon color="#e6a23c" size="32"><ChatLineSquare /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">企业微信</div>
              <div class="stat-value text-orange-500">{{ stats.wework_users || 0 }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon bg-purple-100">
              <el-icon color="#9c27b0" size="32"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">管理员</div>
              <div class="stat-value text-purple-500">{{ stats.admin_users || 0 }}</div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 登录方式分布 -->
        <el-card shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2"><PieChart /></el-icon>
              <span class="font-semibold">登录方式分布</span>
            </div>
          </template>

          <div v-if="loading" class="text-center py-8">
            <el-icon class="is-loading" size="32"><Loading /></el-icon>
            <p class="mt-2 text-gray-500">加载中...</p>
          </div>

          <el-empty v-else-if="!stats.login_type_distribution?.length" description="暂无数据" />

          <div v-else class="login-type-list">
            <div
              v-for="item in stats.login_type_distribution"
              :key="item.login_type"
              class="login-type-item"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="type-label">
                  <el-tag :type="item.login_type === 'wework' ? 'success' : 'primary'" size="small">
                    {{ item.login_type === 'wework' ? '企业微信' : '密码登录' }}
                  </el-tag>
                </span>
                <span class="type-count">
                  {{ item.count }} 人 ({{ item.percentage }}%)
                </span>
              </div>
              <el-progress
                :percentage="item.percentage"
                :color="item.login_type === 'wework' ? '#67c23a' : '#409eff'"
              />
            </div>
          </div>
        </el-card>

        <!-- 最近注册用户 -->
        <el-card shadow="hover">
          <template #header>
            <div class="flex items-center">
              <el-icon class="mr-2"><Clock /></el-icon>
              <span class="font-semibold">最近注册用户</span>
            </div>
          </template>

          <div v-if="loading" class="text-center py-8">
            <el-icon class="is-loading" size="32"><Loading /></el-icon>
            <p class="mt-2 text-gray-500">加载中...</p>
          </div>

          <el-empty v-else-if="!stats.recent_users?.length" description="暂无数据" />

          <div v-else class="recent-users-list">
            <div
              v-for="user in stats.recent_users"
              :key="user.id"
              class="user-item"
            >
              <div class="user-info">
                <div class="user-name">
                  {{ user.username }}
                  <el-tag v-if="user.is_admin" type="danger" size="small">管理员</el-tag>
                </div>
                <div class="user-meta">
                  <span class="user-email">{{ user.email }}</span>
                  <span class="user-time">{{ formatTime(user.created_at) }}</span>
                </div>
              </div>
              <el-tag :type="user.login_type === 'wework' ? 'success' : 'primary'" size="small">
                {{ user.login_type === 'wework' ? '企业微信' : '密码' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 用户列表（可选） -->
      <el-card shadow="hover" class="mt-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <el-icon class="mr-2"><List /></el-icon>
              <span class="font-semibold">用户列表</span>
            </div>
            <el-button type="primary" size="small" @click="loadStats">
              <el-icon class="mr-1"><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div v-if="userListLoading" class="text-center py-8">
          <el-icon class="is-loading" size="32"><Loading /></el-icon>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>

        <el-empty v-else-if="!userList.length" description="暂无用户数据" />

        <div v-else>
          <el-table :data="userList" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="email" label="邮箱" min-width="200" />
            <el-table-column label="登录方式" width="120">
              <template #default="{ row }">
                <el-tag :type="row.login_type === 'wework' ? 'success' : 'primary'" size="small">
                  {{ row.login_type === 'wework' ? '企业微信' : '密码' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
                <el-tag v-else type="info" size="small">普通用户</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="注册时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <div class="mt-4 flex justify-end">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="totalUsers"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadUserList"
              @size-change="loadUserList"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

// 启用 dayjs 时区插件
dayjs.extend(utc)
dayjs.extend(timezone)

const authStore = useAuthStore()
const loading = ref(false)
const userListLoading = ref(false)
const stats = ref({})
const userList = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalUsers = ref(0)

// 检查是否为管理员
const isAdmin = computed(() => authStore.user?.is_admin || false)

// 格式化时间（处理 UTC 时间转东八区）
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  // 数据库存储的是 UTC 时间，需要转换为本地时区显示
  // 方式1: 如果后端返回的时间字符串已包含 'Z' 或时区信息，dayjs 会自动处理
  // 方式2: 如果没有时区信息，明确指定为 UTC 然后转为本地时区
  if (!timeStr.endsWith('Z') && !timeStr.includes('+')) {
    // 没有时区标记，视为 UTC 时间
    return dayjs.utc(timeStr).local().format('YYYY-MM-DD HH:mm')
  }
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

// 加载统计数据
const loadStats = async () => {
  if (!isAdmin.value) return

  loading.value = true
  try {
    const data = await request.get('/admin/stats')
    stats.value = data
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

// 加载用户列表
const loadUserList = async () => {
  if (!isAdmin.value) return

  userListLoading.value = true
  try {
    const data = await request.get('/admin/users', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
      },
    })
    userList.value = data.users || []
    totalUsers.value = data.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    userListLoading.value = false
  }
}

onMounted(() => {
  if (isAdmin.value) {
    loadStats()
    loadUserList()
  }
})
</script>

<style scoped>
.admin-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.login-type-list {
  space-y: 1.5rem;
}

.login-type-item {
  padding: 0.75rem 0;
}

.type-count {
  font-weight: 600;
  color: #333;
}

.recent-users-list {
  space-y: 0.5rem;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.user-item:hover {
  background-color: #f9fafb;
}

.user-item:last-child {
  border-bottom: none;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-meta {
  display: flex;
  gap: 1rem;
  font-size: 12px;
  color: #666;
}

.user-email {
  flex: 1;
}
</style>
