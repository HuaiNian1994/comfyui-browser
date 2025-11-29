import dayjs from 'dayjs'
import type { FileInfo, FolderType, FileType } from '@/types'

/**
 * 图片扩展名列表
 */
export const IMAGE_EXTENSIONS = ['png', 'webp', 'jpeg', 'jpg', 'gif']

/**
 * 视频扩展名列表
 */
export const VIDEO_EXTENSIONS = ['mp4', 'webm', 'mov', 'avi', 'mkv']

/**
 * JSON 扩展名列表
 */
export const JSON_EXTENSIONS = ['json']

/**
 * 白名单扩展名列表
 */
export const WHITELIST_EXTENSIONS = ['html', 'image', 'video', 'json', 'dir']

/**
 * localStorage 键名
 */
export const LOCAL_STORAGE_KEY = 'comfyui-browser'

/**
 * 获取文件 URL
 */
export const getFileUrl = (folderType: string, file: FileInfo): string => {
  const basePath = `/browser/s/${folderType}`
  if (file.folder_path) {
    return `${basePath}/${file.folder_path}/${file.name}`
  }
  return `${basePath}/${file.name}`
}

/**
 * 根据文件名和扩展名查找文件
 */
export const findFileByNameAndExtensions = (
  filename: string,
  extensions: string[],
  files: FileInfo[]
): FileInfo | undefined => {
  const nameParts = filename.split('.')
  nameParts.pop()
  const baseFilename = nameParts.join('.')

  return files.find((file) => {
    const fileParts = file.name.split('.')
    const fileExtension = fileParts.pop()?.toLowerCase()
    const fileBasename = fileParts.join('.')

    return fileBasename === baseFilename && fileExtension && extensions.includes(fileExtension)
  })
}

/**
 * 处理文件信息
 */
export const processFileInfo = (
  file: FileInfo,
  folderType: FolderType,
  allFiles: FileInfo[]
): FileInfo | null => {
  const extensionParts = file.name.split('.')
  const extension = extensionParts.pop()?.toLowerCase()

  if (!extension) return null

  // 确定文件类型
  let fileType: FileType | undefined

  if (WHITELIST_EXTENSIONS.includes(extension)) {
    fileType = extension as FileType

    // 如果是 JSON 文件，检查是否有对应的图片/视频文件
    if (extension === 'json') {
      const hasMediaFile = findFileByNameAndExtensions(
        file.name,
        [...IMAGE_EXTENSIONS, ...VIDEO_EXTENSIONS],
        allFiles
      )
      if (hasMediaFile) {
        return null // 不单独显示JSON文件，它会作为元数据附加到媒体文件上
      }
    }
  }

  if (IMAGE_EXTENSIONS.includes(extension)) {
    fileType = 'image'
  }

  if (VIDEO_EXTENSIONS.includes(extension)) {
    fileType = 'video'
  }

  if (!fileType) {
    return null
  }

  file.fileType = fileType
  file.url = getFileUrl(folderType, file)

  // 对于图片和视频，设置预览URL和查找JSON元数据
  if (fileType === 'image' || fileType === 'video') {
    file.previewUrl = getFileUrl(folderType, file)

    const jsonFile = findFileByNameAndExtensions(file.name, JSON_EXTENSIONS, allFiles)
    if (jsonFile) {
      file.url = getFileUrl(folderType, jsonFile)
    }
  }

  // 格式化日期和文件大小
  file.formattedDatetime = dayjs.unix(file.created_at).format('YYYY-MM-DD HH:mm:ss')
  file.formattedSize = formatFileSize(file.bytes)

  return file
}

/**
 * 处理目录信息
 */
export const processDirectoryInfo = (directory: FileInfo): FileInfo => {
  directory.fileType = 'dir'

  const newFolderPath = directory.folder_path
    ? `${directory.folder_path}/${directory.name}`
    : directory.name
  directory.path = newFolderPath

  directory.formattedDatetime = dayjs.unix(directory.created_at).format('YYYY-MM-DD HH:mm:ss')
  directory.formattedSize = '0 KB'

  return directory
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (sizeInBytes: number): string => {
  const sizeInMB = sizeInBytes / 1024 / 1024
  if (sizeInMB > 1) {
    return `${sizeInMB.toFixed(2)} MB`
  }
  const sizeInKB = Math.round(sizeInBytes / 1024)
  return `${sizeInKB} KB`
}

/**
 * 获取本地配置
 */
export const getLocalConfig = (): Record<string, unknown> => {
  const localConfigString = localStorage.getItem(LOCAL_STORAGE_KEY)
  if (!localConfigString) {
    return {}
  }

  try {
    return JSON.parse(localConfigString)
  } catch (error) {
    console.error('解析本地配置失败:', error)
    return {}
  }
}

/**
 * 设置本地配置
 */
export const setLocalConfig = (key: string, value: unknown): void => {
  const localConfig = getLocalConfig()
  localConfig[key] = value
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(localConfig))
}
