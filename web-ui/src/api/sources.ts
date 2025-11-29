import apiClient from './client'

export interface Source {
  name: string
  url: string
  author: string
  description?: string
  homepage?: string
  title?: string
}

export interface SourcesResponse {
  sources: Source[]
}

/**
 * 获取已添加的源列表
 */
export const fetchSources = async (): Promise<SourcesResponse> => {
  const response = await apiClient.get<SourcesResponse>('/sources')
  return response.data
}

/**
 * 获取所有推荐源列表
 */
export const fetchAllSources = async (): Promise<SourcesResponse> => {
  const response = await apiClient.get<SourcesResponse>('/sources/all')
  return response.data
}

/**
 * 添加源
 */
export const addSource = async (repoUrl: string): Promise<void> => {
  await apiClient.post('/sources', { repo_url: repoUrl })
}

/**
 * 删除源
 */
export const deleteSource = async (name: string): Promise<void> => {
  await apiClient.delete(`/sources/${name}`)
}

/**
 * 同步源
 */
export const syncSource = async (name: string): Promise<void> => {
  await apiClient.post(`/sources/sync/${name}`)
}
