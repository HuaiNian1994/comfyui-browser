import { defineComponent, markRaw } from 'vue'
import apiClient from '@/api/client'
import { DirectoryCoordinator } from '@/api/directory-coordinator'
import type { FileInfo, FolderType } from '@/types'

/** 三个目录页面共享取消、激活与后台任务状态，具体范围由页面提供。 */
export default defineComponent({
  data() {
    return {
      directoryCoordinator: null as DirectoryCoordinator | null,
      directoryActive: true,
      directoryScope: '',
      directoryErrors: [] as string[],
      summaryPaused: false,
      scopeRevision: 0,
      staleDirectoryPaths: new Set<string>(),
      refreshTimer: undefined as ReturnType<typeof setTimeout> | undefined,
      reindexStatus: '',
      reindexJobId: '',
      reindexCounts: { success_count: 0, failed_count: 0, superseded_count: 0 },
      reindexController: null as AbortController | null,
      reindexTimer: undefined as ReturnType<typeof setTimeout> | undefined,
      browserShowListener: null as (() => void) | null,
    }
  },
  activated() {
    if (this.directoryActive) return
    this.directoryActive = true
    ;(this as any).loadFiles()
    if (this.reindexJobId) void this.pollReindex()
  },
  deactivated() { this.stopDirectoryRequests() },
  beforeUnmount() {
    this.stopDirectoryRequests()
    if (this.browserShowListener) window.top?.removeEventListener('comfyuiBrowserShow', this.browserShowListener)
  },
  methods: {
    requestScopeRefresh(paths: string | string[] = '') {
      if (!this.directoryActive) return
      for (const path of Array.isArray(paths) ? paths : [paths]) this.staleDirectoryPaths.add(path)
      if (this.refreshTimer) return
      this.refreshTimer = setTimeout(() => {
        this.refreshTimer = undefined
        const paths = [...this.staleDirectoryPaths]
        this.staleDirectoryPaths.clear()
        if (this.directoryActive) void this.directoryCoordinator?.refreshDirectories(paths)
      }, 50)
    },
    stopDirectoryRequests() {
      this.directoryActive = false
      this.directoryCoordinator?.stop()
      this.reindexController?.abort()
      clearTimeout(this.reindexTimer)
      clearTimeout(this.refreshTimer)
      this.refreshTimer = undefined
      this.staleDirectoryPaths.clear()
      if (!this.reindexJobId && this.reindexStatus === 'queued') this.reindexStatus = 'unknown'
    },
    registerBrowserShow() {
      this.browserShowListener = () => { if (this.directoryActive) (this as any).loadFiles() }
      window.top?.addEventListener('comfyuiBrowserShow', this.browserShowListener)
    },
    async loadDirectoryScope(type: FolderType, paths: string[]) {
      if (!this.directoryActive) return
      clearTimeout(this.refreshTimer)
      this.refreshTimer = undefined
      this.staleDirectoryPaths.clear()
      const page = this as any
      const scope = JSON.stringify([type, paths])
      if (scope !== this.directoryScope) {
        this.directoryScope = scope
        this.scopeRevision++
        page.allFiles = []
      }
      if (!this.directoryCoordinator) {
        this.directoryCoordinator = markRaw(new DirectoryCoordinator(type, (files, errors) => {
          page.allFiles = type === 'outputs' ? files.filter(file => file.fileType !== 'dir') : files
          this.directoryErrors = errors
        }, paths => this.requestScopeRefresh(paths), value => { this.summaryPaused = value }))
      }
      page.loading = true
      page.loadingFiles = true
      const request = this.directoryCoordinator.load(paths)
      const generation = this.directoryCoordinator.generation
      await request
      if (this.directoryActive && generation === this.directoryCoordinator.generation) { page.loading = false; page.loadingFiles = false }
    },
    updateVisibleFiles(files: FileInfo[]) { this.directoryCoordinator?.setVisible(files) },
    retrySummary() { this.directoryCoordinator?.retry() },
    async startReindex() {
      if (!this.directoryActive || ['queued', 'running'].includes(this.reindexStatus)) return
      const [folder_type, folder_paths] = JSON.parse(this.directoryScope || '["outputs",[]]')
      if (!folder_paths.length) return
      this.reindexStatus = 'queued'
      this.reindexCounts = { success_count: 0, failed_count: 0, superseded_count: 0 }
      const controller = this.reindexController = new AbortController()
      try {
        const result = await apiClient.post('/files/reindex', { folder_type, folder_paths }, { signal: controller.signal })
        if (controller.signal.aborted) return
        this.reindexJobId = result.data.job_id
        if (this.directoryActive) void this.pollReindex()
      } catch (error) {
        if (controller.signal.aborted) return
        console.error('创建重建任务失败', error)
        this.reindexStatus = 'failed'
      }
    },
    async pollReindex() {
      if (!this.directoryActive || !this.reindexJobId) return
      const controller = this.reindexController = new AbortController()
      try {
        const response = await apiClient.get(`/files/reindex/${encodeURIComponent(this.reindexJobId)}`, { signal: controller.signal })
        if (controller.signal.aborted || !this.directoryActive) return
        this.reindexCounts = response.data
        this.reindexStatus = response.data.status
        if (['queued', 'running'].includes(this.reindexStatus)) this.reindexTimer = setTimeout(() => void this.pollReindex(), 1000)
        else { this.reindexJobId = ''; (this as any).loadFiles() }
      } catch (error: any) {
        if (controller.signal.aborted) return
        console.error('读取重建任务失败', error)
        this.reindexStatus = error.response?.status === 404 ? 'expired' : 'failed'
        this.reindexJobId = ''
      }
    },
  },
})
