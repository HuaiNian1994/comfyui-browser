import apiClient from './client'

export interface DownloadLog {
  uuid: string
  created_at: number
  updated_at: number
  download_url: string
  save_in: string
  filename: string
  downloaded_size: number
  total_size: number
  result: string
  // 前端辅助字段
  formattedCreatedAt?: string
  formattedUpdatedAt?: string
  percentStr?: string
  formattedDownloadedSize?: string
  formattedTotalSize?: string
}

export interface DownloadsResponse {
  download_logs: DownloadLog[]
}

export interface DownloadRequest {
  download_url: string
  save_in: string
  filename?: string
  overwrite: boolean
}

/**
 * 获取下载历史
 */
export const fetchDownloads = async (): Promise<DownloadsResponse> => {
  const response = await apiClient.get<DownloadsResponse>('/downloads')
  return response.data
}

/**
 * 创建新下载
 */
export const createDownload = async (data: DownloadRequest): Promise<void> => {
  await apiClient.post('/downloads', data)
}
