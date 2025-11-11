/**
 * 统一的HTTP请求工具
 * 基于fetch API，自动添加认证token和统一错误处理
 */

const BASE_URL = '/api/v1'
const TOKEN_KEY = 'rsm_access_token'

/**
 * 获取存储的token
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 设置token
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 清除token
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * 统一的请求拦截器 - 自动添加Authorization header
 * @param {string} url - 请求URL
 * @param {Object} options - fetch配置选项
 * @returns {Promise<Response>}
 */
async function fetchWithAuth(url, options = {}) {
  // 构建完整URL
  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`

  // 添加Authorization header
  const token = getToken()
  if (token) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  }

  try {
    const response = await fetch(fullUrl, options)

    // 统一处理401未授权错误
    if (response.status === 401) {
      console.warn('Token已过期或无效，跳转到登录页')
      removeToken()
      // 跳转到登录页
      window.location.href = '/login'
      throw new Error('未授权，请重新登录')
    }

    return response
  } catch (error) {
    console.error('Request error:', error)
    throw error
  }
}

/**
 * 统一的请求方法 - 支持JSON数据
 * @param {Object} options - 请求选项
 * @param {string} options.url - 请求URL
 * @param {string} options.method - 请求方法
 * @param {Object} options.data - 请求数据
 * @param {Object} options.headers - 额外的请求头
 * @returns {Promise}
 */
async function request(options) {
  const { url, method = 'GET', data, headers = {} } = options

  // 构建请求配置
  const config = {
    method: method.toUpperCase(),
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  }

  // 添加请求体
  if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
    config.body = JSON.stringify(data)
  }

  const response = await fetchWithAuth(url, config)

  // 处理响应
  const contentType = response.headers.get('content-type')
  let responseData

  if (contentType && contentType.includes('application/json')) {
    responseData = await response.json()
  } else {
    responseData = await response.text()
  }

  if (!response.ok) {
    // HTTP错误
    throw {
      response: {
        status: response.status,
        data: responseData
      }
    }
  }

  return responseData
}

/**
 * 上传文件 - 支持FormData
 * @param {string} url - 请求URL
 * @param {FormData} formData - 表单数据
 * @param {Object} options - 额外选项
 * @returns {Promise<Response>}
 */
export async function uploadFile(url, formData, options = {}) {
  const config = {
    method: 'POST',
    body: formData,
    ...options
  }

  // 注意：上传FormData时不要设置Content-Type，让浏览器自动设置
  return fetchWithAuth(url, config)
}

/**
 * 下载文件 - 返回Blob
 * @param {string} url - 请求URL
 * @returns {Promise<Blob>}
 */
export async function downloadFile(url) {
  const response = await fetchWithAuth(url, { method: 'GET' })

  if (!response.ok) {
    throw new Error('下载失败')
  }

  return response.blob()
}

// 添加便捷方法到 request 函数
request.get = function(url, options = {}) {
  // 处理查询参数
  let finalUrl = url
  if (options.params) {
    const queryString = new URLSearchParams(options.params).toString()
    finalUrl = queryString ? `${url}?${queryString}` : url
    // 移除 params，避免传递给 request 函数
    const { params, ...restOptions } = options
    return request({
      url: finalUrl,
      method: 'GET',
      ...restOptions
    })
  }

  return request({
    url: finalUrl,
    method: 'GET',
    ...options
  })
}

request.post = function(url, data, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

request.put = function(url, data, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

request.delete = function(url, options = {}) {
  return request({
    url,
    method: 'DELETE',
    ...options
  })
}

request.patch = function(url, data, options = {}) {
  return request({
    url,
    method: 'PATCH',
    data,
    ...options
  })
}

export default request
export { fetchWithAuth }
