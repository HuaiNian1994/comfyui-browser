import axios, { type AxiosInstance } from 'axios'

/**
 * Axios 实例，用于所有 API 请求
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: '/browser',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (!axios.isCancel(error)) console.error('响应错误:', error)
    return Promise.reject(error)
  }
)

export default apiClient
