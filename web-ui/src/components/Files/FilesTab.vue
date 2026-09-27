<template>
  <div class="files-tab">
    <div v-if="directoryErrors.length || summaryPaused || reindexStatus" class="directory-status">
      <span v-for="path in directoryErrors" :key="path">目录 {{ directoryErrorLabel(path) }} 加载失败 <el-button link @click="requestScopeRefresh(path)">重试</el-button></span>
      <span v-if="summaryPaused">摘要更新已暂停 <el-button link @click="retrySummary">重试</el-button></span>
      <span v-if="reindexStatus">重建状态：{{ ({ queued: '排队中', running: '进行中', complete: '完成', failed: '失败', expired: '已过期', unknown: '创建结果未知，可重新发起'  } as Record<string, string>)[reindexStatus] }}；成功 {{ reindexCounts.success_count }}，失败 {{ reindexCounts.failed_count }}，已被新版本替代 {{ reindexCounts.superseded_count }}</span>
    </div>
    <!-- 文件列表 -->
    <FileCardList :scope-revision="scopeRevision" @visible-files="updateVisibleFiles" @stale="requestScopeRefresh" @reindex="startReindex" :files="allFiles" :loading="loading" :enable-image-preview="true" :folder-type="folderType"
      :folder-path="currentFolderPath" :empty-description="t('filesTab.emptyText')" @refresh="loadFiles">
      <template #header>
        <div class="directory-manager">
          <el-select v-model="selectedDirectoryKeys" multiple filterable clearable class="directory-select"
            :loading="initializingDirectories" :placeholder="t('filesTab.directorySelectPlaceholder')"
            @change="handleDirectorySelectionChange">
            <template #header>
              <div class="select-header" @click.stop @keydown.stop>
                <el-input v-model="newDirectoryInput" :disabled="initializingDirectories || addingDirectory" size="small"
                  class="inline-input" placeholder="服务器绝对目录或输出目录下的相对路径" @keyup.enter.stop.prevent="handleAddDirectory" />
                <el-button type="primary" size="small" :loading="addingDirectory" :disabled="initializingDirectories" @click.stop="handleAddDirectory">添加</el-button>
              </div>
              <div v-if="directorySetupError" class="directory-error" role="alert" @click.stop>
                {{ directorySetupError }} <el-button link size="small" :loading="initializingDirectories" @click.stop="initializeDirectories">重试</el-button>
              </div>
            </template>
            <template #label="{ label, value }">
              <span class="directory-tag-label" role="button" tabindex="0" title="打开文件夹"
                @click.stop="openFolderInExplorer(value)" @keydown.enter.stop.prevent="openFolderInExplorer(value)" @keydown.space.stop.prevent="openFolderInExplorer(value)">{{ label }}</span>
            </template>
            <el-option v-for="dir in managedDirectories" :key="dir.relativePath" :label="dir.name" :value="dir.relativePath">
              <div class="directory-option">
                <div class="option-label">
                  <span class="dir-name">{{ dir.name }}</span>
                  <span class="dir-path">{{ dir.absolutePath }}</span>
                </div>
                <el-button link size="small" :title="'打开文件夹：' + dir.absolutePath" :aria-label="'打开文件夹：' + dir.name"
                  @keydown.stop @click.stop="openFolderInExplorer(dir.relativePath)"><el-icon><FolderOpened /></el-icon></el-button>
              </div>
            </el-option>
          </el-select>
        </div>
      </template>
      <template #batch-actions="{ selectedFiles, clearSelection }">
        <el-button type="primary" @click="handleBatchCollect(selectedFiles, clearSelection)">
          {{ t('common.batchCollect') }}
        </el-button>
        <el-button type="danger" @click="handleBatchDelete(selectedFiles, clearSelection)">
          {{ t('common.batchDelete') }}
        </el-button>
      </template>

      <template #actions="{ file }">
        <el-button v-if="file.fileType !== 'dir'" link type="primary" size="small" @click="handleLoadWorkflow(file)">
          {{ t('common.btn.load') }}
        </el-button>
        <el-button link type="primary" size="small" @click="handleCollectFile(file)">
          {{ t('filesTab.addToSaves') }}
        </el-button>
        <el-button link type="danger" size="small" @click="handleDeleteFile(file)">
          <el-icon>
            <Delete />
          </el-icon> {{ t('common.btn.delete') }}
        </el-button>
      </template>
    </FileCardList>

    <!-- 返回顶部按钮 -->
    <el-backtop :right="40" :bottom="40" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import directoryPage from '@/utils/directory-page'
import i18n from '@/i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, FolderOpened } from '@element-plus/icons-vue'
import { deleteFile, openFolderOnSystem } from '@/api/files'
import { fetchRegisteredDirectories, registerDirectory, type RegisteredDirectory } from '@/api/directories'
import { getBrowserConfig } from '@/api/collections'
import type { FileInfo, FolderType } from '@/types'
import {
  normalizeRelativePath,
  buildAbsolutePath,
  extractDirectoryName,
  getDirectoryPreferences,
  hasDirectoryPreferences,
  setDirectoryPreferences,
} from '@/utils/index'
import { batchDeleteFiles, batchCollectFiles } from '@/utils/batch-actions'
import apiClient from '@/api/client'
import FileCardList from '@/components/Common/FileCardList.vue'

type ManagedDirectory = {
  name: string
  relativePath: string
  absolutePath: string
  checked: boolean
}

export default defineComponent({
  mixins: [directoryPage],
  name: 'FilesTab',
  components: {
    Delete,
    FolderOpened,    FileCardList
  },
  data() {
    return {
      folderType: 'outputs' as FolderType,
      directoryListId: 'outputs-file-list',
      currentFolderPath: '',
      allFiles: [] as FileInfo[],
      loading: false,
      comfyApp: null as any,
      managedDirectories: [] as ManagedDirectory[],
      selectedDirectoryKeys: [] as string[],
      newDirectoryInput: '',
      directoryBasePath: '',
      directoriesReady: false,
      initializingDirectories: false,
      addingDirectory: false,
      directorySetupError: '',
      registeredDirectories: [] as RegisteredDirectory[],
      registryController: null as AbortController | null,
    }
  },
  mounted() {
    this.initializeDirectories()
    this.setupComfyApp()
  },
  activated() { if (!this.directoriesReady) void this.initializeDirectories() },
  deactivated() {
    this.registryController?.abort()
    this.initializingDirectories = false
    this.addingDirectory = false
    this.directoriesReady = false
  },
  beforeUnmount() { this.registryController?.abort() },
  methods: {
    directoryErrorLabel(path: string): string {
      if (!path) return this.t('filesTab.outputsRoot')
      const directory = this.managedDirectories.find(item => item.relativePath === path)
      return directory?.absolutePath || directory?.name || path
    },
    t(key: string, params?: Record<string, unknown>): string {
      return params ? i18n.global.t(key, params) : i18n.global.t(key)
    },
    async initializeDirectories() {
      if (this.initializingDirectories) return
      this.initializingDirectories = true
      this.directoriesReady = false
      this.directorySetupError = ''
      this.registryController?.abort()
      const controller = this.registryController = new AbortController()
      try {
        const [, directories] = await Promise.all([this.loadBrowserConfig(controller.signal), fetchRegisteredDirectories(controller.signal)])
        if (controller.signal.aborted) return
        this.registeredDirectories = directories
        this.restoreDirectories()
        this.directoriesReady = true
        await this.loadFiles()
      } catch (error) {
        if (controller.signal.aborted) return
        console.error('读取目录配置失败', error)
        this.directorySetupError = '读取目录配置失败，请重试。'
      } finally {
        if (this.registryController === controller) this.initializingDirectories = false
      }
    },
    async loadBrowserConfig(signal?: AbortSignal) {
      try {
        const config = await getBrowserConfig(signal)
        if (signal?.aborted) return
        this.directoryBasePath = config.outputs
      } catch (error) {
        if (signal?.aborted) return
        console.error('加载配置失败:', error)
        throw error
      } finally {
        this.refreshAbsolutePaths()
      }
    },
    refreshAbsolutePaths() {
      this.managedDirectories = this.managedDirectories.map(dir => this.createManagedDirectory(dir.relativePath, dir.checked))
    },
    restoreDirectories() {
      const preferences = getDirectoryPreferences(this.directoryListId)
      const firstVisit = !hasDirectoryPreferences(this.directoryListId)
      const selected = new Set(firstVisit ? [''] : preferences.filter(pref => pref.checked).map(pref => pref.path))
      const paths = new Set(['', ...this.registeredDirectories.map(dir => dir.path), ...preferences.map(pref => pref.path)])
      this.managedDirectories = [...paths].map(path => this.createManagedDirectory(path, selected.has(path)))
      this.selectedDirectoryKeys = [...selected]
      if (firstVisit) this.persistDirectories()
    },
    createManagedDirectory(relativePath: string, checked: boolean): ManagedDirectory {
      const normalized = normalizeRelativePath(relativePath)
      const registered = this.registeredDirectories.find(dir => dir.path === normalized)
      return {
        name: registered?.name || extractDirectoryName(normalized, this.t('filesTab.outputsRoot')),
        relativePath: normalized,
        absolutePath: registered?.absolute_path || (normalized.startsWith('@external/') ? normalized : buildAbsolutePath(this.directoryBasePath, normalized)),
        checked
      }
    },
    persistDirectories() {
      if (!this.directoryListId) {
        return
      }
      setDirectoryPreferences(
        this.directoryListId,
        this.managedDirectories.map((dir) => ({
          path: dir.relativePath,
          checked: dir.checked
        }))
      )
    },
    handleDirectorySelectionChange(value: string[]) {
      this.currentFolderPath = ''
      this.selectedDirectoryKeys = value
      this.managedDirectories = this.managedDirectories.map((dir) => ({
        ...dir,
        checked: value.includes(dir.relativePath)
      }))
      this.persistDirectories()
      this.loadFiles()
    },
    async handleAddDirectory() {
      if (this.addingDirectory || this.initializingDirectories) return
      const path = this.newDirectoryInput.trim()
      if (!path) { this.directorySetupError = '请输入服务器本地目录。'; return }
      this.addingDirectory = true
      this.directorySetupError = ''
      const controller = this.registryController = new AbortController()
      try {
        // 服务器负责验证绝对目录并返回不透明路径标识，前端原样保存该标识。
        const directory = await registerDirectory(path, controller.signal)
        if (controller.signal.aborted) return
        this.registeredDirectories = [...this.registeredDirectories.filter(dir => dir.path !== directory.path), directory]
        const entry = this.createManagedDirectory(directory.path, true)
        this.managedDirectories = [...this.managedDirectories.filter(dir => dir.relativePath !== directory.path), entry]
        this.selectedDirectoryKeys = [...new Set([...this.selectedDirectoryKeys, directory.path])]
        this.persistDirectories()
        this.newDirectoryInput = ''
        await this.loadFiles()
      } catch (error) {
        if (controller.signal.aborted) return
        console.error('添加服务器目录失败', error)
        this.directorySetupError = '添加目录失败，请检查服务器路径及读取权限后重试。'
      } finally { if (this.registryController === controller) this.addingDirectory = false }
    },
    getTargetFolderPaths(): string[] { return [...this.selectedDirectoryKeys] },
    async loadFiles() {
      if (!this.directoriesReady) return
      await this.loadDirectoryScope(this.folderType, this.getTargetFolderPaths())
    },
    async openFolderInExplorer(targetPath: string) {
      try {
        await openFolderOnSystem(this.folderType, targetPath || undefined)
      } catch (error) {
        console.error('打开文件夹失败:', error)
        this.directorySetupError = '打开服务器文件夹失败。'
      }
    },
    async handleLoadWorkflow(file: FileInfo) {
      if (!this.comfyApp || !file.url) {
        return
      }

      try {
        const response = await fetch(file.url)
        const blob = await response.blob()
        const fileObj = new File([blob], file.name, {
          type: response.headers.get('Content-Type') || '',
        })

        const originalLoadFn = this.comfyApp.loadGraphData.bind(this.comfyApp)
        this.comfyApp.loadGraphData = async (graphData: any) => {
          const modal = (window.top as any)?.document.getElementById('comfy-browser-dialog')
          if (modal) {
            modal.style.display = 'none'
          }
          await originalLoadFn(graphData)
        }

        await this.comfyApp.handleFile(fileObj)
        console.log('工作流已加载')
      } catch (error) {
        console.error('加载工作流失败:', error)
      }
    },
    async handleCollectFile(file: FileInfo) {
      try {
        await apiClient.post('/collections', {
          filename: file.name,
          folder_path: file.folder_path,
          folder_type: this.folderType,
        })
        ElMessage.success(this.t('filesTab.addToSavesSuccess'))
      } catch (error) {
        console.error('收藏文件失败:', error)
        ElMessage.error(this.t('filesTab.addToSavesFailed'))
      }
    },
    async handleDeleteFile(file: FileInfo) {
      try {
        await ElMessageBox.confirm(
          `${this.t('filesTab.deleteConfirm')} ${file.name}？`,
          this.t('common.btn.delete'),
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )

        await deleteFile(
          this.folderType,
          file.name,
          file.folder_path || undefined
        )

        ElMessage.success(this.t('filesTab.deleteSuccess'))
        this.loadFiles()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除文件失败:', error)
          ElMessage.error(this.t('filesTab.deleteFailed'))
        }
      }
    },
    async handleBatchDelete(files: FileInfo[], clearSelection: () => void) {
      try {
        const result = await batchDeleteFiles(files, this.folderType, this.currentFolderPath, this.t)
        if (result.successCount > 0) {
          this.loadFiles()
          clearSelection()
        }
      } catch (e) {
        // cancelled
      }
    },
    async handleBatchCollect(files: FileInfo[], clearSelection: () => void) {
      const result = await batchCollectFiles(files, this.folderType, this.currentFolderPath, this.t)
      if (result.successCount > 0) {
        clearSelection()
      }
    },
    setupComfyApp() {
      this.comfyApp = (window.top as any)?.app

      this.registerBrowserShow()
    }
  }
})
</script>

<style scoped lang="scss">
  .files-tab {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }



  .directory-option { display: flex; align-items: center; gap: 8px; }
  .directory-option .option-label { flex: 1; min-width: 0; gap: 0; padding: 0; }
  .directory-tag-label { cursor: pointer; }
  .directory-error { padding: 0 12px 8px; font-size: 12px; color: var(--el-color-danger); max-width: 420px; white-space: normal; }

  .directory-select {
     flex: 1 1 auto;
     min-width: 0;
    width: 100%;
  }



   .select-header {
     display: flex;
     align-items: center;
     gap: 8px;
     padding: 8px 12px;
   }

   .inline-input {
     flex: 1;
   }

   .option-label {
     display: flex;
     flex-direction: column;
     line-height: 1.2;
     gap: 2px;
     padding: 4px 0;
   }

  .dir-name {
    font-weight: 600;
  }

  .dir-path {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    word-break: break-all;
  }




</style>
