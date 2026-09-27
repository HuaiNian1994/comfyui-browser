import apiClient from './client'
import type { BrowserConfig } from '@/types'

/**
 * 获取浏览器配置
 */
export const getBrowserConfig = async (signal?: AbortSignal): Promise<BrowserConfig> => {
  const response = await apiClient.get<BrowserConfig>('/config', { signal })
  return response.data
}

/**
 * 更新浏览器配置
 */
export const updateBrowserConfig = async (config: { git_repo: string }) => {
  const response = await apiClient.put('/config', config)
  return response.data
}

/**
 * 同步收藏
 */
export const syncCollections = async () => {
  const response = await apiClient.post('/collections/sync')
  return response.data
}

/**
 * 添加到收藏
 */
export const addToCollections = async (data: {
  filename: string
  folder_path?: string
  folder_type: string
}) => {
  const response = await apiClient.post('/collections', data)
  return response.data
}
