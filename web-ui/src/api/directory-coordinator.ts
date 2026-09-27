import { reactive } from 'vue'
import apiClient from './client'
import { fetchFilesList } from './files'
import { fileIdentity, processDirectoryFiles } from '@/utils'
import type { FileInfo, FolderType } from '@/types'

/** 页面持有协调器，摘要全集与搜索、分页完全独立。 */
export class DirectoryCoordinator {
  loading = false
  directoryFiles = new Map<string, FileInfo[]>()
  directoryErrors = new Set<string>()
  partialControllers = new Map<string, AbortController>()
  active = true
  generation = 0
  controller?: AbortController
  summaryController?: AbortController
  timer?: ReturnType<typeof setTimeout>
  files: FileInfo[] = []
  pending = new Map<string, FileInfo>()
  visible: FileInfo[] = []
  visibleSignature = ''
  visibleDirty = false
  running = false
  failures = 0
  sessionId = Math.random().toString(36).slice(2)
  type: FolderType
  changed: (files: FileInfo[], errors: string[]) => void
  stale: (paths: string[]) => void
  paused: (value: boolean) => void
  constructor(type: FolderType, changed: (files: FileInfo[], errors: string[]) => void, stale: (paths: string[]) => void, paused: (value: boolean) => void) {
    this.type = type; this.changed = changed; this.stale = stale; this.paused = paused
  }
  stop() {
    this.active = false
    this.generation++
    this.controller?.abort()
    this.summaryController?.abort()
    this.summaryController = undefined
    this.running = false
    for (const controller of this.partialControllers.values()) controller.abort()
    this.partialControllers.clear()
    clearTimeout(this.timer)
  }
  async load(paths: string[]) {
    this.stop()
    this.active = true
    this.loading = true
    this.files = []
    this.pending.clear()
    this.directoryFiles.clear()
    this.directoryErrors.clear()
    const generation = this.generation
    const controller = this.controller = new AbortController()
    this.failures = 0
    this.visible = []
    this.visibleSignature = ''
    this.visibleDirty = false
    this.paused(false)
    const results = await Promise.allSettled(paths.map(path => fetchFilesList(this.type, path, controller.signal)))
    if (!this.active || generation !== this.generation) return
    results.forEach((result, index) => {
      const path = paths[index]!
      if (result.status === 'fulfilled') this.directoryFiles.set(path, reactive(processDirectoryFiles(result.value.files, this.type, path)))
      else { this.directoryFiles.set(path, []); this.directoryErrors.add(path); console.error('读取目录失败', path, result.reason) }
    })
    this.loading = false
    this.publishDirectories()
    this.pending = new Map(this.files.filter(file => this.isPending(file)).map(file => [fileIdentity(this.type, file), file]))
    this.schedule(0)
  }
  isPending(file: FileInfo) { return file.metadata_pending || ['waiting', 'processing'].includes(file.index_status || '') }
  publishDirectories() {
    this.files = reactive([...this.directoryFiles.values()].flat().sort((a, b) => b.created_at - a.created_at))
    this.changed(this.files, [...this.directoryErrors])
  }
  /** 局部失效仅替换对应目录，其他目录的对象、队列位置和完成进度保持。 */
  async refreshDirectories(paths: string[]) {
    if (!this.active || this.loading) return
    const generation = this.generation
    await Promise.all([...new Set(paths)].filter(path => this.directoryFiles.has(path)).map(async path => {
      this.partialControllers.get(path)?.abort()
      const controller = new AbortController()
      this.partialControllers.set(path, controller)
      for (const [key, file] of this.pending) if ((file.folder_path || '') === path) this.pending.delete(key)
      try {
        const result = await fetchFilesList(this.type, path, controller.signal)
        if (!this.active || generation !== this.generation || this.partialControllers.get(path) !== controller) return
        const previous = new Map((this.directoryFiles.get(path) || []).map(file => [fileIdentity(this.type, file), file]))
        const files = reactive(processDirectoryFiles(result.files, this.type, path).map(file => {
          const old = previous.get(fileIdentity(this.type, file))
          return old && old.file_version === file.file_version && old.index_generation === file.index_generation ? Object.assign(old, file) : file
        }))
        this.directoryFiles.set(path, files)
        this.directoryErrors.delete(path)
        for (const file of files) if (this.isPending(file)) this.pending.set(fileIdentity(this.type, file), file)
      } catch (error) {
        if (controller.signal.aborted || generation !== this.generation) return
        console.error('刷新目录失败', path, error)
        this.directoryFiles.set(path, [])
        this.directoryErrors.add(path)
      } finally {
        if (this.partialControllers.get(path) === controller && generation === this.generation) {
          this.partialControllers.delete(path)
          this.publishDirectories()
          const index = new Map(this.files.map(file => [fileIdentity(this.type, file), file]))
          this.setVisible(this.visible.map(file => index.get(fileIdentity(this.type, file))).filter((file): file is FileInfo => !!file))
          if (!this.failures) this.schedule(0)
        }
      }
    }))
  }
  setVisible(files: FileInfo[]) {
    const visible = files.filter(file => file.type !== 'dir' && !this.partialControllers.has(file.folder_path || '')).slice(0, 100)
    const signature = JSON.stringify(visible.map(file => [fileIdentity(this.type, file), file.file_version, file.index_generation]))
    if (signature === this.visibleSignature) return
    this.visibleSignature = signature
    this.visible = visible
    this.visibleDirty = true
    if (this.active && this.failures === 0) this.schedule(0)
  }
  retry() { this.failures = 0; this.paused(false); this.schedule(0) }
  schedule(delay: number) {
    clearTimeout(this.timer)
    if (this.active && !this.loading) this.timer = setTimeout(() => void this.poll(), delay)
  }
  async poll() {
    if (!this.active || this.loading || this.running || (!this.pending.size && !this.visibleDirty)) return
    this.running = true
    const generation = this.generation
    const controller = this.summaryController = new AbortController()
    const batch = [...this.pending.values()].slice(0, 200)
    // 轮转保证隐藏在搜索结果之外的待处理文件也能完成。
    batch.forEach(file => { const key = fileIdentity(this.type, file); this.pending.delete(key); this.pending.set(key, file) })
    const reference = (file: FileInfo) => ({ folder_path: file.folder_path || '', name: file.name, file_version: file.file_version, index_generation: file.index_generation })
    const visible = this.visible.filter(file => !this.partialControllers.has(file.folder_path || ''))
    const requested = new Map([...batch, ...visible].map(file => [fileIdentity(this.type, file), reference(file)]))
    this.visibleDirty = false
    try {
      const response = await apiClient.post('/files/summary-updates', { folder_type: this.type, files: batch.map(reference), visible_files: visible.map(reference), session_id: this.sessionId }, { signal: controller.signal })
      if (!this.active || generation !== this.generation) return
      this.failures = 0
      const stalePaths = new Set<string>()
      const index = new Map(this.files.map(file => [fileIdentity(this.type, file), file]))
      for (const update of response.data.files) {
        const key = fileIdentity(this.type, update)
        const file = index.get(key)
        if (!file || this.partialControllers.has(file.folder_path || '')) continue
        const expected = requested.get(key)
        if (!expected || expected.file_version !== file.file_version || expected.index_generation !== file.index_generation) continue
        if (update.status === 'stale' || update.status === 'missing') { stalePaths.add(file.folder_path || ''); continue }
        if (file.file_version !== update.file_version || file.index_generation !== update.index_generation) continue
        if (update.summary) file.summary = update.summary
        if (update.tags) file.tags = update.tags
        file.index_status = update.status
        file.metadata_pending = ['waiting', 'processing'].includes(update.status)
        if (!file.metadata_pending) this.pending.delete(key)
      }
      if (stalePaths.size) this.stale([...stalePaths])
    } catch (error) {
      if (controller.signal.aborted || generation !== this.generation) return
      console.error('读取摘要失败', error)
      this.failures++

    } finally {
      // 旧请求只释放自身；新范围正在加载时不会重新启动旧摘要队列。
      if (this.summaryController !== controller || generation !== this.generation) return
      this.summaryController = undefined
      this.running = false
      if (this.active && this.failures === 3) {
        clearTimeout(this.timer)
        this.timer = setTimeout(() => { if (this.active && this.failures === 3) this.paused(true) }, 4000)
      } else if (this.active && this.failures < 3) this.schedule(this.failures ? 1000 * 2 ** (this.failures - 1) : this.visibleDirty ? 0 : 1000)
    }
  }
}
