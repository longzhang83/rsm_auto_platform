/**
 * 翻译服务工具类
 * 统一处理翻译相关的API调用和进度管理
 */

import { fetchWithAuth, downloadFile } from '@/api/request'

export class TranslationService {
  constructor() {
    this.currentEventSource = null
    this.currentTaskId = null
  }

  /**
   * 执行带进度显示的翻译任务
   * @param {Object} options 翻译选项
   * @param {FormData} options.formData 表单数据
   * @param {string} options.startUrl 启动任务的URL
   * @param {string} options.downloadUrl 下载结果的URL
   * @param {Function} options.onProgress 进度回调函数
   * @param {Function} options.onComplete 完成回调函数
   * @param {Function} options.onError 错误回调函数
   * @param {number} options.timeout 超时时间（毫秒）
   * @returns {Promise<Object>} 处理结果
   */
  async executeWithProgress(options) {
    const {
      formData,
      startUrl,
      downloadUrl,
      onProgress,
      onComplete,
      onError,
      timeout = 300000 // 5分钟默认超时
    } = options

    let taskId = null

    try {
      console.log('启动翻译任务:', startUrl)

      // 1. 启动翻译任务（使用统一的请求拦截器，自动添加认证）
      const startResponse = await fetchWithAuth(startUrl, {
        method: 'POST',
        body: formData
      })

      if (!startResponse.ok) {
        const errorData = await startResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || '启动任务失败')
      }

      const startData = await startResponse.json()
      taskId = startData.task_id
      this.currentTaskId = taskId
      console.log('任务已启动:', taskId)

      // 2. 建立SSE连接监听进度
      return await this.listenProgress(taskId, {
        onProgress,
        onComplete,
        onError,
        downloadUrl,
        timeout
      })

    } catch (error) {
      console.error('翻译任务执行失败:', error)
      if (onError) onError(error)
      throw error
    } finally {
      this.cleanup()
    }
  }

  /**
   * 监听任务进度 - 支持自动重连
   * @param {string} taskId 任务ID
   * @param {Object} options 选项
   * @returns {Promise<Object>} 处理结果
   */
  async listenProgress(taskId, options) {
    const {
      onProgress,
      onComplete,
      onError,
      downloadUrl,
      timeout = 7200000  // 2小时超时，匹配后端SSE超时时间
    } = options

    return new Promise((resolve, reject) => {
      let retryCount = 0
      const maxRetries = 10  // 最大重连次数
      const retryDelay = 3000  // 重连延迟（毫秒）
      let timeoutId = null
      let isResolved = false

      const connect = () => {
        try {
          console.log(`建立SSE连接，任务ID: ${taskId}, 重连次数: ${retryCount}`)

          // 直接连接后端SSE，避免Vite代理问题
          this.currentEventSource = new EventSource(`http://localhost:8888/api/v1/progress/${taskId}`)

          // 设置超时
          timeoutId = setTimeout(() => {
            if (!isResolved) {
              console.error('任务超时:', taskId)
              this.cleanup()
              reject(new Error('任务超时，请重试'))
            }
          }, timeout)

          this.currentEventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data)
              console.log('收到进度数据:', data)

              // 心跳包，忽略
              if (data.heartbeat) {
                return
              }

              // SSE监听超时，需要重连
              if (data.sse_timeout) {
                console.log('SSE连接超时，准备重连...')
                this.cleanup()

                if (retryCount < maxRetries) {
                  retryCount++
                  setTimeout(() => {
                    console.log(`第${retryCount}次重连...`)
                    connect()
                  }, retryDelay)
                } else {
                  if (!isResolved) {
                    isResolved = true
                    clearTimeout(timeoutId)
                    reject(new Error('SSE重连次数过多，请刷新页面重试'))
                  }
                }
                return
              }

              // 错误状态
              if (data.percentage < 0) {
                if (!isResolved) {
                  isResolved = true
                  clearTimeout(timeoutId)
                  this.cleanup()
                  const error = new Error(data.message || '任务失败')
                  if (onError) onError(error)
                  reject(error)
                }
                return
              }

              // 更新进度
              if (onProgress) {
                onProgress(data)
              }

              // 任务完成
              if (data.percentage >= 100) {
                if (!isResolved) {
                  isResolved = true
                  clearTimeout(timeoutId)
                  console.log('任务完成，准备下载:', taskId)

                  // 下载结果 - 返回下载URL让前端处理
                  if (downloadUrl) {
                    const finalDownloadUrl = downloadUrl.replace('{taskId}', taskId)
                    console.log('下载URL:', finalDownloadUrl)

                    const result = {
                      success: true,
                      download_url: finalDownloadUrl,
                      task_id: taskId,
                      ...data
                    }

                    if (onComplete) onComplete(result)
                    resolve(result)
                  } else {
                    if (onComplete) onComplete(data)
                    resolve(data)
                  }
                  this.cleanup()
                }
              }

            } catch (error) {
              console.error('解析进度数据失败:', error)
              if (!isResolved) {
                isResolved = true
                clearTimeout(timeoutId)
                this.cleanup()
                if (onError) onError(error)
                reject(error)
              }
            }
          }

          this.currentEventSource.onerror = (error) => {
            console.error('SSE连接错误:', error)
            this.cleanup()

            // 尝试重连
            if (retryCount < maxRetries && !isResolved) {
              retryCount++
              console.log(`SSE连接错误，第${retryCount}次重连...`)
              setTimeout(() => {
                connect()
              }, retryDelay)
            } else if (!isResolved) {
              isResolved = true
              clearTimeout(timeoutId)
              const errorMsg = '进度连接失败，请检查网络连接'
              if (onError) onError(new Error(errorMsg))
              reject(new Error(errorMsg))
            }
          }

          this.currentEventSource.onopen = () => {
            console.log('SSE连接已建立:', taskId)
            retryCount = 0  // 重置重连计数
          }

        } catch (error) {
          console.error('建立SSE连接失败:', error)
          if (!isResolved) {
            isResolved = true
            clearTimeout(timeoutId)
            if (onError) onError(error)
            reject(error)
          }
        }
      }

      // 开始连接
      connect()
    })
  }

  /**
   * 下载处理结果
   * @param {string} downloadUrl 下载URL
   * @param {string} filename 文件名
   * @returns {Promise<Object>} 下载结果
   */
  async downloadResult(downloadUrl, filename = null) {
    try {
      console.log('开始下载:', downloadUrl)

      // 使用统一的下载工具（自动添加认证）
      const blob = await downloadFile(downloadUrl)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `result_${Date.now()}.zip`
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()

      setTimeout(() => {
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }, 100)

      console.log('下载完成')
      return { success: true, filename: link.download }

    } catch (error) {
      console.error('下载失败:', error)
      throw error
    }
  }

  /**
   * 取消当前任务
   */
  async cancel() {
    console.log('取消翻译任务')

    if (this.currentTaskId) {
      try {
        // 调用后端取消API（使用统一的请求拦截器）
        const cancelUrl = `/translate/cancel/${this.currentTaskId}`
        const response = await fetchWithAuth(cancelUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          console.log('后端任务已取消:', this.currentTaskId)
        } else {
          console.warn('取消后端任务失败:', response.status)
        }
      } catch (error) {
        console.error('调用取消API失败:', error)
      }
    }

    // 关闭SSE连接
    this.cleanup()
  }

  /**
   * 清理资源
   */
  cleanup() {
    if (this.currentEventSource) {
      this.currentEventSource.close()
      this.currentEventSource = null
    }
    this.currentTaskId = null
  }
}

// 创建全局实例
export const translationService = new TranslationService()

// 便捷方法：摘要翻译
export async function translateSummary(formData, options = {}) {
  return translationService.executeWithProgress({
    formData,
    startUrl: '/api/v1/translate/start',
    downloadUrl: '/api/v1/translate/download/{taskId}',
    ...options
  })
}

// 便捷方法：银行流水转凭证
export async function generateBankVouchers(formData, options = {}) {
  return translationService.executeWithProgress({
    formData,
    startUrl: '/api/v1/bank-statements/generate/start',
    downloadUrl: '/api/v1/bank-statements/download/{taskId}',
    ...options
  })
}