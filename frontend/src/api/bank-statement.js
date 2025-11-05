// 获取可用的客户列表
export async function getBankStatementCustomers() {
  try {
    const response = await fetch('/api/v1/bank-statements/customers')
    if (!response.ok) {
      throw new Error('获取客户列表失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取客户列表失败:', error)
    throw error
  }
}

// 获取客户的映射配置
export async function getBankStatementMapping(customerName) {
  try {
    const response = await fetch(`/api/v1/bank-statements/mapping/${encodeURIComponent(customerName)}`)
    if (!response.ok) {
      throw new Error('获取客户映射配置失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取客户映射配置失败:', error)
    throw error
  }
}

// 预览银行流水数据
export async function previewBankStatementData(formData) {
  try {
    const response = await fetch('/api/v1/bank-statements/preview', {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      throw new Error('预览数据失败')
    }
    return await response.json()
  } catch (error) {
    console.error('预览数据失败:', error)
    throw error
  }
}

// 生成银行流水凭证
export async function generateBankStatementVouchers(formData) {
  try {
    const response = await fetch('/api/v1/bank-statements/generate', {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || '生成凭证失败')
    }
    return await response.json()
  } catch (error) {
    console.error('生成凭证失败:', error)
    throw error
  }
}

// 异步生成银行流水凭证（带进度显示）
export async function generateBankStatementVouchersAsync(formData, onProgress) {
  try {
    // 第一步：启动任务
    const startResponse = await fetch('/api/v1/bank-statements/generate/start', {
      method: 'POST',
      body: formData
    })
    if (!startResponse.ok) {
      const errorText = await startResponse.text()
      throw new Error(errorText || '启动生成任务失败')
    }
    const { task_id, message } = await startResponse.json()

    // 第二步：监听进度
    if (onProgress) {
      const eventSource = new EventSource(`/api/v1/progress/${task_id}`)

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.heartbeat) {
            // 心跳包，忽略
            return
          }

          if (data.cancelled) {
            eventSource.close()
            throw new Error('任务已取消')
          }

          if (data.percentage < 0) {
            // 任务失败
            eventSource.close()
            throw new Error(data.message || '任务失败')
          }

          // 更新进度
          onProgress(data)

          if (data.percentage >= 100) {
            // 任务完成
            eventSource.close()
          }
        } catch (e) {
          if (e.message !== '任务已取消') {
            console.error('解析进度数据失败:', e)
          }
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error)
        eventSource.close()
        throw new Error('进度连接中断')
      }

      eventSource.onopen = () => {
        console.log('SSE连接已建立')
      }

      // 等待任务完成
      await new Promise((resolve, reject) => {
        const checkResult = async () => {
          try {
            const resultResponse = await fetch(`/api/v1/bank-statements/generate/result/${task_id}`)
            if (resultResponse.ok) {
              const result = await resultResponse.json()
              eventSource.close()
              resolve(result)
            } else {
              // 结果还没准备好，继续等待
              setTimeout(checkResult, 500)
            }
          } catch (error) {
            reject(error)
          }
        }

        // 开始检查结果
        setTimeout(checkResult, 500)
      })

      return await new Promise((resolve, reject) => {
        // 这里实际上已经在上面的checkResult中处理了
      })
    }

    // 如果没有进度回调，使用简单轮询
    let result = null
    while (!result) {
      const resultResponse = await fetch(`/api/v1/bank-statements/generate/result/${task_id}`)
      if (resultResponse.ok) {
        result = await resultResponse.json()
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    return result

  } catch (error) {
    console.error('异步生成凭证失败:', error)
    throw error
  }
}

// 下载银行流水凭证文件
export async function downloadBankStatementFile(filename) {
  try {
    const response = await fetch(`/api/v1/bank-statements/download/${encodeURIComponent(filename)}`)
    if (!response.ok) {
      throw new Error('下载文件失败')
    }
    return response.blob()
  } catch (error) {
    console.error('下载文件失败:', error)
    throw error
  }
}

// 验证银行流水文件
export async function validateBankStatementFile(file) {
  try {
    const formData = new FormData()
    formData.append('bank_statement_file', file)

    const response = await fetch('/api/v1/bank-statements/validate', {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      throw new Error('验证文件失败')
    }
    return await response.json()
  } catch (error) {
    console.error('验证文件失败:', error)
    throw error
  }
}

// 获取银行流水功能信息
export async function getBankStatementInfo() {
  try {
    const response = await fetch('/api/v1/bank-statements/info')
    if (!response.ok) {
      throw new Error('获取功能信息失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取功能信息失败:', error)
    throw error
  }
}