/**
 * Dashboard API
 */
import axios from 'axios'

const BASE_URL = '/api/v1/dashboard'

/**
 * 获取统计数据
 */
export function getDashboardStats() {
  return axios.get(`${BASE_URL}/stats`)
}

/**
 * 获取最近处理记录
 * @param {number} limit - 返回记录数量
 */
export function getRecentRecords(limit = 10) {
  return axios.get(`${BASE_URL}/recent-records`, {
    params: { limit }
  })
}

/**
 * 获取完整Dashboard数据
 */
export function getDashboardData() {
  return axios.get(`${BASE_URL}/data`)
}

/**
 * 获取指定记录
 * @param {string} recordId - 记录ID
 */
export function getRecord(recordId) {
  return axios.get(`${BASE_URL}/record/${recordId}`)
}

/**
 * 清空统计数据（仅测试）
 */
export function clearStats() {
  return axios.post(`${BASE_URL}/clear-stats`)
}

/**
 * 清空处理记录（仅测试）
 */
export function clearRecords() {
  return axios.post(`${BASE_URL}/clear-records`)
}
