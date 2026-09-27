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
export interface GenerationTiming {
  version: number
  total_ms: number
  sampling_ms?: number
  iterations?: number
  source: 'image' | 'database'
  scope: 'whole_task'
  sampling_complete?: boolean
  iterations_complete?: boolean
}

export interface FormattedInfo {
  generation_timing?: GenerationTiming
  timing_pending?: boolean
  parser_version?: number
  parse_status?: 'complete' | 'partial' | 'missing' | 'invalid' | 'unsupported_container'
  index_status?: 'complete' | 'failed'
  has_metadata?: boolean
  image_format?: string
  error_code?: string
  branches?: MetadataBranch[]
  stages?: MetadataStage[]
  unassigned?: MetadataProperty[]
  diagnostics?: MetadataDiagnostic[]
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
  metadata_pending?: boolean
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
 * 浏览器配置
 */
export interface BrowserConfig {
  outputs: string
  collections: string
  sources: string
  download_logs: string
  git_repo?: string
}

/**
 * 图片元数据接口
 */
export interface ImageMetadata {
  timing_pending?: boolean
  index_status?: 'waiting' | 'processing' | 'complete' | 'failed'
  metadata_pending?: boolean
  positive: string
  negative: string
  has_metadata: boolean
  formatted_info?: FormattedInfo
  tags?: string[]
}

export interface MetadataSource {
  node_id: string
  class_type: string
  field: string
  output_port?: number
}

export interface MetadataProperty {
  id: string
  group: string
  value: unknown
  state: 'recorded' | 'derived' | 'unknown'
  sources: MetadataSource[]
  channel?: string
  reason?: string
}

export interface MetadataDiagnostic {
  code: string
  node_id: string
  class_type: string
  field: string
  detail: string
}

export interface MetadataStage {
  id: string
  node_id: string
  class_type: string
  kind: 'sampling' | 'processing'
  properties: MetadataProperty[]
  depends_on: string[]
}

export interface MetadataBranch {
  id: string
  output_node_id: string | null
  association: 'unique' | 'unconfirmed'
  stage_ids: string[]
}
