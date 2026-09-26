/** 当前页面和详情共享同一文件的元数据请求，最后一个订阅释放时停止轮询。 */
import { fetchImageMetadata } from './files'
import type { FolderType, ImageMetadata } from '@/types'

interface Subscription {
  callbacks: Set<(value: ImageMetadata) => void>
  timer?: ReturnType<typeof setTimeout>
  controller?: AbortController
  result?: ImageMetadata
  attempt: number
  generation: number
}

const subscriptions = new Map<string, Subscription>()
let activeRequests = 0

export function subscribeMetadata(
  folderType: FolderType,
  filename: string,
  folderPath: string,
  callback: (value: ImageMetadata) => void,
  refresh = false,
): () => void {
  const key = JSON.stringify([folderType, folderPath, filename])
  let entry = subscriptions.get(key)
  const created = !entry
  if (!entry) {
    entry = { callbacks: new Set(), attempt: 0, generation: 0 }
    subscriptions.set(key, entry)
  }
  const current = entry
  current.callbacks.add(callback)
  if (current.result && !refresh) callback(current.result)

  async function requestMetadata(force: boolean, poll: boolean) {
    if (subscriptions.get(key) !== current || !current.callbacks.size) return
    if (activeRequests >= 5) {
      current.timer = setTimeout(() => void requestMetadata(force, poll), 150)
      return
    }
    const generation = current.generation
    const controller = new AbortController()
    current.controller = controller
    activeRequests += 1
    try {
      const result = await fetchImageMetadata(folderType, filename, folderPath, { refresh: force, poll, signal: controller.signal })
      if (generation !== current.generation || subscriptions.get(key) !== current) return
      current.result = result
      current.callbacks.forEach(listener => listener(result))
      if (result.index_status === 'waiting' || result.index_status === 'processing') {
        current.attempt += 1
        current.timer = setTimeout(() => void requestMetadata(false, true), Math.min(4000, 300 * 2 ** Math.min(current.attempt, 4)))
      }
    } catch (error) {
      if (controller.signal.aborted || generation !== current.generation || subscriptions.get(key) !== current) return
      console.error('读取图片元数据失败', error)
      current.result = { positive: '', negative: '', has_metadata: false, index_status: 'failed' }
      current.callbacks.forEach(listener => listener(current.result!))
    } finally {
      activeRequests -= 1
    }
  }

  if (created || refresh) {
    clearTimeout(current.timer)
    current.controller?.abort()
    current.generation += 1
    current.attempt = 0
    void requestMetadata(refresh, false)
  }
  return () => {
    current.callbacks.delete(callback)
    if (current.callbacks.size === 0) {
      clearTimeout(current.timer)
      current.controller?.abort()
      if (subscriptions.get(key) === current) subscriptions.delete(key)
    }
  }
}
