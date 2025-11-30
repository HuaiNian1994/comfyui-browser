import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteFile } from '@/api/files'
import { addToCollections } from '@/api/collections'
import type { FileInfo, FolderType } from '@/types'

export interface BatchActionResult {
  successCount: number
  failCount: number
}

/**
 * 批量删除文件
 */
export const batchDeleteFiles = async (
  files: FileInfo[],
  folderType: FolderType,
  folderPath: string,
  t: (key: string, ...args: any[]) => string
): Promise<BatchActionResult> => {
  if (files.length === 0) {
    return { successCount: 0, failCount: 0 }
  }

  try {
    await ElMessageBox.confirm(
      t('common.deleteConfirm', { count: files.length }),
      t('common.batchDelete'),
      {
        confirmButtonText: t('common.btn.delete'),
        cancelButtonText: t('common.btn.cancel'),
        type: 'warning'
      }
    )
  } catch {
    // 用户取消
    throw 'cancel'
  }

  let successCount = 0
  let failCount = 0

  for (const file of files) {
    try {
      await deleteFile(folderType, file.name, folderPath)
      successCount++
    } catch (error) {
      console.error(`Failed to delete ${file.name}:`, error)
      failCount++
    }
  }

  if (successCount > 0) {
    ElMessage.success(t('common.deleteSuccessCount', { count: successCount }))
  }
  if (failCount > 0) {
    ElMessage.error(t('common.deleteFailCount', { count: failCount }))
  }

  return { successCount, failCount }
}

/**
 * 批量收藏文件
 */
export const batchCollectFiles = async (
  files: FileInfo[],
  folderType: FolderType,
  folderPath: string,
  t: (key: string, ...args: any[]) => string
): Promise<BatchActionResult> => {
  if (files.length === 0) {
    return { successCount: 0, failCount: 0 }
  }

  // 收藏通常不需要二次确认，但如果是批量操作，为了防止误操作，也可以加上
  // 这里我们直接执行

  let successCount = 0
  let failCount = 0

  for (const file of files) {
    try {
      await addToCollections({
        filename: file.name,
        folder_path: folderPath,
        folder_type: folderType
      })
      successCount++
    } catch (error) {
      console.error(`Failed to collect ${file.name}:`, error)
      failCount++
    }
  }

  if (successCount > 0) {
    ElMessage.success(t('common.collectSuccessCount', { count: successCount }))
  }
  if (failCount > 0) {
    ElMessage.error(t('common.collectFailCount', { count: failCount }))
  }

  return { successCount, failCount }
}
