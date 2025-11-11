/**
 * Dashboard API
 */
import request from './request'

/**
 * 获取统计数据
 */
export function getDashboardStats() {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}

/**
 * 获取最近处理记录
 * @param {number} limit - 返回记录数量
 */
export function getRecentRecords(limit = 10) {
  return request({
    url: `/dashboard/recent-records?limit=${limit}`,
    method: 'get'
  })
}

/**
 * 获取完整Dashboard数据
 */
export function getDashboardData() {
  return request({
    url: '/dashboard/data',
    method: 'get'
  })
}

/**
 * 获取指定记录
 * @param {string} recordId - 记录ID
 */
export function getRecord(recordId) {
  return request({
    url: `/dashboard/record/${recordId}`,
    method: 'get'
  })
}

/**
 * 清空统计数据（仅测试）
 */
export function clearStats() {
  return request({
    url: '/dashboard/clear-stats',
    method: 'post'
  })
}

/**
 * 清空处理记录（仅测试）
 */
export function clearRecords() {
  return request({
    url: '/dashboard/clear-records',
    method: 'post'
  })
}
