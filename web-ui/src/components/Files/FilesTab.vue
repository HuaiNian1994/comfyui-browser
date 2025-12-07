<template>
  <div class="files-tab">
    <!-- 文件列表 -->
    <FileCardList :files="allFiles" :loading="loading" :enable-image-preview="true" :folder-type="folderType"
      :folder-path="currentFolderPath" :empty-description="t('filesTab.emptyText')" @file-click="handleFileClick" @refresh="loadFiles">
      <template #header>
        <div v-if="directoryListId" class="directory-manager">
          <div class="manager-row">
            <el-select v-model="selectedDirectoryKeys" multiple filterable class="directory-select"
              :placeholder="t('filesTab.directorySelectPlaceholder')" @change="handleDirectorySelectionChange">
              <template #header>
                <div class="select-header">
                  <span class="base-path" :title="directoryBasePath || ''">
                    {{ directoryBasePath || t('filesTab.unknownBasePath') }}
                  </span>
                  <el-input v-model="newDirectoryInput" :placeholder="directoryInputPlaceholder" size="small"
                    class="inline-input" @keyup.enter.stop.prevent="handleAddDirectory" />
                  <el-button type="primary" size="small" @click="handleAddDirectory">
                    {{ t('common.btn.add') }}
                  </el-button>
                </div>
              </template>
              <template #tag="tagProps">
                <el-tag closable :disable-transitions="false" @close="handleTagClose(tagProps.value)">
                  <span class="tag-clickable" @mousedown.prevent.stop="openDirectoryFromTag(tagProps.value)">
                    {{ getDirectoryLabel(tagProps.value) }}
                  </span>
                </el-tag>
              </template>
              <el-option v-for="dir in managedDirectories" :key="dir.relativePath || 'root'" :label="dir.name"
                :value="dir.relativePath">
                <div class="option-label" @mousedown.prevent.stop="openDirectoryFromTag(dir.relativePath)">
                  <span class="dir-name">{{ dir.name }}</span>
                  <span class="dir-path">{{ dir.absolutePath }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
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
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Grid, Menu } from '@element-plus/icons-vue'
import { fetchFilesList, deleteFile, openFolderOnSystem } from '@/api/files'
import { getBrowserConfig } from '@/api/collections'
import type { FileInfo, FolderType, BrowserConfig } from '@/types'
import {
  processFileInfo,
  processDirectoryInfo,
  normalizeRelativePath,
  buildAbsolutePath,
  extractDirectoryName,
  getDirectoryPreferences,
  setDirectoryPreferences,
  type DirectoryPreference
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
  name: 'FilesTab',
  components: {
    Delete,
    Grid,
    Menu,
    FileCardList
  },
  setup() {
    const { t } = useI18n()
    return { t }
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
      browserConfig: null as BrowserConfig | null
    }
  },
  computed: {
    currentPathParts(): string[] {
      return this.currentFolderPath ? this.currentFolderPath.split('/') : []
    },
    directoryInputPlaceholder(): string {
      return this.t('filesTab.directoryInputPlaceholder')
    }
  },
  mounted() {
    this.initializeDirectories()
    this.setupComfyApp()
  },
  methods: {
    async initializeDirectories() {
      await this.loadBrowserConfig()
      this.restoreDirectories()
      this.directoriesReady = true
      this.loadFiles()
    },
    async loadBrowserConfig() {
      try {
        const config = await getBrowserConfig()
        this.browserConfig = config
        this.directoryBasePath = this.resolveBasePath(config)
      } catch (error) {
        console.error('加载配置失败:', error)
        this.directoryBasePath = ''
      } finally {
        this.refreshAbsolutePaths()
      }
    },
    resolveBasePath(config: BrowserConfig | null): string {
      if (!config) {
        return ''
      }
      if (this.folderType === 'collections') {
        return config.collections
      }
      if (this.folderType === 'sources') {
        return config.sources
      }
      return config.outputs
    },
    refreshAbsolutePaths() {
      if (!this.directoryBasePath) {
        return
      }
      this.managedDirectories = this.managedDirectories.map((dir) => ({
        ...dir,
        absolutePath: buildAbsolutePath(this.directoryBasePath, dir.relativePath)
      }))
    },
    restoreDirectories() {
      if (!this.directoryListId) {
        return
      }
      const preferences = getDirectoryPreferences(this.directoryListId)
      if (preferences.length === 0) {
        const defaultDir = this.createManagedDirectory('', true)
        this.managedDirectories = [defaultDir]
        this.selectedDirectoryKeys = [defaultDir.relativePath]
        this.persistDirectories()
        return
      }

      this.managedDirectories = preferences.map((pref: DirectoryPreference) => this.createManagedDirectory(pref.path, pref.checked))
      this.selectedDirectoryKeys = this.managedDirectories.filter((dir) => dir.checked).map((dir) => dir.relativePath)

      if (this.selectedDirectoryKeys.length === 0 && this.managedDirectories.length > 0) {
        const firstDirectory = this.managedDirectories[0]
        if (firstDirectory) {
          firstDirectory.checked = true
          this.selectedDirectoryKeys = [firstDirectory.relativePath]
          this.persistDirectories()
        }
      }
    },
    createManagedDirectory(relativePath: string, checked: boolean): ManagedDirectory {
      const normalized = normalizeRelativePath(relativePath)
      const name = extractDirectoryName(normalized, this.t('filesTab.outputsRoot'))
      return {
        name,
        relativePath: normalized,
        absolutePath: buildAbsolutePath(this.directoryBasePath, normalized),
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
      this.selectedDirectoryKeys = value
      this.managedDirectories = this.managedDirectories.map((dir) => ({
        ...dir,
        checked: value.includes(dir.relativePath)
      }))
      this.persistDirectories()
      this.loadFiles()
    },
    async handleAddDirectory() {
      const rawInput = this.newDirectoryInput.trim()
      if (!rawInput) {
        ElMessage.warning(this.t('filesTab.directoryPathRequired'))
        return
      }

       const normalizedBase = this.directoryBasePath.replace(/\\/g, '/').replace(/\/+$/g, '')
       const normalizedInput = rawInput.replace(/\\/g, '/')

       let relativePath = normalizeRelativePath(rawInput)
       if (normalizedBase && normalizedInput.toLowerCase().startsWith(normalizedBase.toLowerCase())) {
         const rest = normalizedInput.slice(normalizedBase.length)
         relativePath = normalizeRelativePath(rest)
       }

      if (relativePath.includes('..')) {
        ElMessage.warning(this.t('filesTab.directoryInvalid'))
        return
      }

      const exists = this.managedDirectories.find((dir) => dir.relativePath === relativePath)
      if (exists) {
        if (!exists.checked) {
          exists.checked = true
          this.selectedDirectoryKeys.push(exists.relativePath)
        }
        this.selectedDirectoryKeys = Array.from(new Set(this.selectedDirectoryKeys))
        this.persistDirectories()
        if (!this.currentFolderPath) {
          this.loadFiles()
        }
        this.newDirectoryInput = ''
        ElMessage.success(this.t('common.addSuccess'))
        return
      }

      const newDir = this.createManagedDirectory(relativePath, true)
      this.managedDirectories.push(newDir)
      this.selectedDirectoryKeys = Array.from(new Set([...this.selectedDirectoryKeys, newDir.relativePath]))
      this.persistDirectories()
      this.newDirectoryInput = ''
      if (!this.currentFolderPath) {
        this.loadFiles()
      }
      ElMessage.success(this.t('common.addSuccess'))
    },
    handleTagClose(path: string) {
      this.selectedDirectoryKeys = this.selectedDirectoryKeys.filter((key) => key !== path)
      this.managedDirectories = this.managedDirectories.map((dir) => ({
        ...dir,
        checked: this.selectedDirectoryKeys.includes(dir.relativePath)
      }))
      this.persistDirectories()
      if (!this.currentFolderPath) {
        this.loadFiles()
      }
    },
    removeDirectory(directory: ManagedDirectory) {
      if (!this.directoryListId) {
        return
      }
      this.managedDirectories = this.managedDirectories.filter((dir) => dir.relativePath !== directory.relativePath)
      this.selectedDirectoryKeys = this.selectedDirectoryKeys.filter((key) => key !== directory.relativePath)

      if (this.managedDirectories.length === 0) {
        const fallback = this.createManagedDirectory('', true)
        this.managedDirectories = [fallback]
        this.selectedDirectoryKeys = [fallback.relativePath]
      }

      this.persistDirectories()

      if (directory.relativePath && this.currentFolderPath.startsWith(directory.relativePath)) {
        this.currentFolderPath = ''
      }

      if (!this.currentFolderPath) {
        this.loadFiles()
      }
    },
    getDirectoryLabel(path: string): string {
      const dir = this.managedDirectories.find((item) => item.relativePath === path)
      return dir ? dir.name : (path || this.t('filesTab.outputsRoot'))
    },
    getCheckedDirectoryPaths(): string[] {
      if (!this.directoryListId) {
        return [this.currentFolderPath || '']
      }
      const checked = this.managedDirectories.filter((dir) => dir.checked).map((dir) => dir.relativePath)
      if (checked.length === 0 && this.managedDirectories.length > 0) {
        const firstDirectory = this.managedDirectories[0]
        return firstDirectory ? [firstDirectory.relativePath] : []
      }
      return checked
    },
    getTargetFolderPaths(): string[] {
      if (!this.directoryListId) {
        return [this.currentFolderPath || '']
      }
      if (this.currentFolderPath) {
        return [this.currentFolderPath]
      }
      const checked = this.getCheckedDirectoryPaths()
      return checked.length > 0 ? checked : ['']
    },
    async openDirectoryFromTag(path: string) {
      await this.openFolderInExplorer(path || '')
    },
    async loadFiles() {
      if (this.directoryListId && !this.directoriesReady) {
        return
      }
      if (!this.directoryListId && this.currentFolderPath === '') {
        // 无目录管理模式时保持现状
      } else {
        // 勾选变动时重置当前子路径，始终按选中目录刷新
        this.currentFolderPath = ''
      }
      const targetPaths = this.getTargetFolderPaths()
      if (targetPaths.length === 0) {
        this.allFiles = []
        return
      }

      this.loading = true
      try {
        const allProcessed: FileInfo[] = []

        const responses = await Promise.all(
          targetPaths.map((path) =>
            fetchFilesList(
              this.folderType,
              path || undefined
            )
          )
        )

        responses.forEach((response, index) => {
          const folderPath = targetPaths[index]
          response.files.forEach((file) => {
            let processed: FileInfo | null = null
            if (file.type === 'dir') {
              processed = processDirectoryInfo(file)
            } else {
              processed = processFileInfo(file, this.folderType, response.files)
            }

            if (processed) {
              if (!processed.folder_path && folderPath) {
                processed.folder_path = folderPath
              }
              allProcessed.push(processed)
            }
          })
        })

        allProcessed.sort((a, b) => (b.created_at || 0) - (a.created_at || 0))
        this.allFiles = allProcessed
      } catch (error) {
        console.error('加载文件列表失败:', error)
        ElMessage.error(this.t('filesTab.loadFailed'))
      } finally {
        this.loading = false
      }
    },
    async openFolderInExplorer(targetPath: string) {
      try {
        await openFolderOnSystem(this.folderType, targetPath || undefined)
      } catch (error) {
        console.error('打开文件夹失败:', error)
      }
    },
    handleFileClick(file: FileInfo) {
      if (file.fileType === 'dir') {
        this.currentFolderPath = file.path || ''
        this.loadFiles()
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

      if (window.top) {
        window.top.addEventListener('comfyuiBrowserShow', () => {
          this.loadFiles()
        })
      }
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


   .manager-row {
     display: flex;
     gap: 8px;
     align-items: center;
     width: 100%;
   }

  .directory-select {
     flex: 1 1 auto;
     min-width: 0;
    width: 100%;
  }

  .directory-input {
    flex: 1;
  }

   .base-path {
     display: inline-block;
     max-width: 220px;
     overflow: hidden;
     text-overflow: ellipsis;
     white-space: nowrap;
     font-size: 12px;
     color: var(--el-text-color-secondary);
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

  .directory-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .tag-content {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
  }

  .tag-name {
    font-weight: 600;
  }

  .tag-path {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
</style>
