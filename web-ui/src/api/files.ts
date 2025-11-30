import apiClient from './client'
import type { FilesResponse, FolderType, ImageMetadata } from '@/types'

/**
 * 获取文件列表
 */
export const fetchFilesList = async (
  folderType: FolderType,
  folderPath?: string
): Promise<FilesResponse> => {
  const params: Record<string, string> = { folder_type: folderType }
  if (folderPath) {
    params.folder_path = folderPath
  }

  const response = await apiClient.get<FilesResponse>('/files', { params })
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
 * 更新文件（重命名、移动或修改备注）
 */
export const updateFile = async (
  folderType: FolderType,
  filename: string,
  newData: { filename?: string; notes?: string; folder_path?: string },
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
  folderPath?: string
): Promise<ImageMetadata> => {
  const params: Record<string, string> = {
    folder_type: folderType,
    filename: filename,
  }
  if (folderPath) {
    params.folder_path = folderPath
  }

  const response = await apiClient.get<ImageMetadata>('/files/metadata', { params })
  return response.data
}
