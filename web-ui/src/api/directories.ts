import apiClient from './client'

export interface RegisteredDirectory {
  path: string
  absolute_path: string
  name: string
}

export async function fetchRegisteredDirectories(signal?: AbortSignal): Promise<RegisteredDirectory[]> {
  const response = await apiClient.get<{ directories: RegisteredDirectory[] }>('/directories', { signal })
  return response.data.directories
}

export async function registerDirectory(path: string, signal?: AbortSignal): Promise<RegisteredDirectory> {
  const response = await apiClient.post<{ directory: RegisteredDirectory }>('/directories', { path }, { signal })
  return response.data.directory
}
