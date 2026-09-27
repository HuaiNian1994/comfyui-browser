import apiClient from './client'
import type { FilesResponse, FolderType, ImageMetadata } from '@/types'

/**
 * 获取文件列表
 */
export const fetchFilesList = async (
  folderType: FolderType,
  folderPath?: string,
  signal?: AbortSignal
): Promise<FilesResponse> => {
  const params: Record<string, string> = { folder_type: folderType }
  if (folderPath) {
    params.folder_path = folderPath
  }

  const response = await apiClient.get<FilesResponse>('/files', { params, signal })
  return response.data
}

/**
 * 删除文件
 */
export const deleteFile = async (
  folderType: FolderType,
  filename: string,
  folderPath?: string
): Promise<void> => {
  const data: Record<string, string> = {
    folder_type: folderType,
    filename: filename,
  }
  if (folderPath) {
    data.folder_path = folderPath
  }

  await apiClient.delete('/files', { data })
}

/**
 * 更新文件（重命名、移动、修改备注或标签）
 */
export const updateFile = async (
  folderType: FolderType,
  filename: string,
  newData: { filename?: string; notes?: string; folder_path?: string; tags?: string[] },
  folderPath?: string
): Promise<void> => {
  const data: Record<string, any> = {
    folder_type: folderType,
    filename: filename,
    new_data: newData,
  }
  if (folderPath) {
    data.folder_path = folderPath
  }

  await apiClient.put('/files', data)
}

/**
 * 查看文件
 */
export const viewFile = async (
  folderType: FolderType,
  filename: string,
  folderPath?: string
): Promise<string> => {
  const params: Record<string, string> = {
    folder_type: folderType,
    filename: filename,
  }
  if (folderPath) {
    params.folder_path = folderPath
  }

  const response = await apiClient.get('/files/view', { params })
  return response.data
}

/**
 * 获取图片元数据
 */
export const fetchImageMetadata = async (
  folderType: FolderType,
  filename: string,
  folderPath?: string,
  options: { poll?: boolean; refresh?: boolean; signal?: AbortSignal } = {}
): Promise<ImageMetadata> => {
  const params: Record<string, string> = {
    folder_type: folderType,
    filename: filename,
  }
  if (folderPath) {
    params.folder_path = folderPath
  }

  if (options.poll) params.poll = '1'
  if (options.refresh) params.refresh = '1'
  const response = await apiClient.get<ImageMetadata>('/files/metadata', { params, signal: options.signal })
  return response.data
}

/**
 * 为文件添加标签
 */
export const addFileTag = async (
  folderType: FolderType,
  filename: string,
  tag: string,
  folderPath?: string
): Promise<{ tags: string[] }> => {
  const data: Record<string, any> = {
    folder_type: folderType,
    filename: filename,
    tag: tag,
  }
  if (folderPath) {
    data.folder_path = folderPath
  }

  const response = await apiClient.post<{ tags: string[] }>('/files/tag', data)
  return response.data
}

/**
 * 从文件移除标签
 */
export const removeFileTag = async (
  folderType: FolderType,
  filename: string,
  tag: string,
  folderPath?: string
): Promise<{ tags: string[] }> => {
  const data: Record<string, any> = {
    folder_type: folderType,
    filename: filename,
    tag: tag,
  }
  if (folderPath) {
    data.folder_path = folderPath
  }

  const response = await apiClient.delete<{ tags: string[] }>('/files/tag', { data })
  return response.data
}

/**
 * 获取所有已使用的标签
 */
export const fetchAllTags = async (): Promise<string[]> => {
  const response = await apiClient.get<{ all_tags: string[] }>('/files/tags')
  return response.data.all_tags
}

export interface ReindexResponse {
  folder_type: FolderType
  folder_path?: string
  indexed_folders: number
  indexed_files: number
}

/**
 * 在系统文件管理器中打开指定目录
 */
export const openFolderOnSystem = async (folderType: FolderType, folderPath?: string): Promise<void> => {
  const data: Record<string, string> = { folder_type: folderType }
  if (folderPath) {
    data.folder_path = folderPath
  }
  await apiClient.post('/files/open-folder', data)
}

/**
 * 清空数据库索引并重新索引
 */
export const reindexFiles = async (folderType: FolderType, folderPath?: string): Promise<ReindexResponse> => {
  const data: Record<string, string> = { folder_type: folderType }
  if (folderPath) {
    data.folder_path = folderPath
  }
  const response = await apiClient.post<ReindexResponse>('/files/reindex', data)
  return response.data
}
