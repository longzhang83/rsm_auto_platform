/**
 * 统一的HTTP请求工具
 * 基于fetch API，自动添加认证token
 */

const BASE_URL = '/api/v1'
const TOKEN_KEY = 'rsm_access_token'

/**
 * 获取存储的token
 */
function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 统一的请求方法
 * @param {Object} options - 请求选项
 * @param {string} options.url - 请求URL
 * @param {string} options.method - 请求方法
 * @param {Object} options.data - 请求数据
 * @param {Object} options.headers - 额外的请求头
 * @returns {Promise}
 */
async function request(options) {
  const { url, method = 'GET', data, headers = {} } = options

  // 构建完整URL
  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`

  // 构建请求配置
  const config = {
    method: method.toUpperCase(),
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  }

  // 添加Authorization header
  const token = getToken()
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }

  // 添加请求体
  if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
    config.body = JSON.stringify(data)
  }

  try {
    const response = await fetch(fullUrl, config)

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

    return {
      data: responseData,
      status: response.status,
      headers: response.headers
    }
  } catch (error) {
    console.error('Request error:', error)
    throw error
  }
}

export default request
