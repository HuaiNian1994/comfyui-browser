/**
 * 文件夹类型定义
 */
export type FolderType = 'outputs' | 'collections' | 'sources'

/**
 * 文件类型定义
 */
export type FileType = 'image' | 'video' | 'json' | 'dir' | 'html'

/**
 * 格式化后的详细信息
 */
export interface FormattedInfo {
  models?: string[]
  loras?: string[]
  width?: number
  height?: number
  positive_prompt?: string
  negative_prompt?: string
}

/**
 * 文件信息接口
 */
export interface FileInfo {
  name: string
  type: string
  folder_path?: string
  created_at: number
  bytes: number
  fileType?: FileType
  url?: string
  previewUrl?: string
  formattedDatetime?: string
  formattedSize?: string
  path?: string
  notes?: string
  hash?: string
  tags?: string[]
  formatted_info?: FormattedInfo
}

/**
 * 目录信息接口
 */
export interface DirectoryInfo extends FileInfo {
  fileType: 'dir'
  path: string
}

/**
 * API响应接口 - 文件列表
 */
export interface FilesResponse {
  files: FileInfo[]
}

/**
 * Source 配置接口
 */
export interface SourceConfig {
  name: string
  url: string
  type: string
  enabled: boolean
}

/**
 * Collection 接口
 */
export interface Collection {
  name: string
  created_at: number
  items: FileInfo[]
}

/**
 * 下载任务接口
 */
export interface DownloadTask {
  uuid: string
  url: string
  filename: string
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  progress: number
  created_at: number
}

/**
 * 图片元数据接口
 */
export interface ImageMetadata {
  positive: string
  negative: string
  has_metadata: boolean
  formatted_info?: FormattedInfo
  tags?: string[]
}
