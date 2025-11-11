/**
 * 认证相关API
 */
import request from '@/utils/request'

/**
 * 发送邮箱验证码
 * @param {Object} data - 请求数据
 * @param {string} data.email - 邮箱地址
 * @returns {Promise}
 */
export function sendVerificationCode(data) {
  return request({
    url: '/auth/send-verification-code',
    method: 'post',
    data
  })
}

/**
 * 用户注册
 * @param {Object} data - 注册数据
 * @param {string} data.username - 用户名
 * @param {string} data.email - 邮箱
 * @param {string} data.password - 密码
 * @param {string} data.verification_code - 邮箱验证码
 * @returns {Promise}
 */
export function register(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

/**
 * 用户登录
 * @param {Object} data - 登录数据
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @returns {Promise}
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

/**
 * 获取当前用户信息
 * @returns {Promise}
 */
export function getCurrentUser() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}

/**
 * 请求重置密码
 * @param {Object} data - 重置请求数据
 * @param {string} data.email - 注册邮箱
 * @returns {Promise}
 */
export function forgotPassword(data) {
  return request({
    url: '/auth/forgot-password',
    method: 'post',
    data
  })
}

/**
 * 重置密码
 * @param {Object} data - 重置密码数据
 * @param {string} data.token - 重置token
 * @param {string} data.new_password - 新密码
 * @returns {Promise}
 */
export function resetPassword(data) {
  return request({
    url: '/auth/reset-password',
    method: 'post',
    data
  })
}
