<template>
  <div class="collections-tab">
    <!-- 顶部同步栏 -->
    <div class="sync-bar">
      <el-link href="https://github.com/talesofai/comfyui-browser/wiki/How-to-use-Sync-in-the-Saves-tab" target="_blank"
        :underline="false" class="help-icon">
        <el-icon :size="24">
          <QuestionFilled />
        </el-icon>
      </el-link>

      <el-input v-model="configGitRepo" :placeholder="t('collectionsTab.gitPlaceholder')" class="git-input" />

      <el-button v-if="configGitRepo !== originalGitRepo" type="success" plain @click="handleSaveConfig">
        {{ t('collectionsTab.save') }}
      </el-button>

      <el-button type="primary" plain :loading="syncing" @click="handleSync">
        {{ syncing ? t('collectionsTab.syncing') : t('collectionsTab.sync') }}
      </el-button>
    </div>

    <!-- 导航和搜索 -->
    <div class="toolbar">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item>
          <el-button link @click="navigateToPath(-1)">{{ t('common.rootDir') }}</el-button>
        </el-breadcrumb-item>
        <el-breadcrumb-item v-for="(pathPart, index) in currentPathParts" :key="index">
          <el-button link @click="navigateToPath(index)">{{ pathPart }}</el-button>
        </el-breadcrumb-item>
      </el-breadcrumb>

      <el-input v-model="searchQuery" :placeholder="t('collectionsTab.searchPlaceholder')" clearable
        class="search-input">
        <template #prefix>
          <el-icon>
            <Search />
          </el-icon>
        </template>
      </el-input>
    </div>

    <!-- 文件列表 -->
    <FileCardList :files="displayedFiles" :loading="loading" :enable-image-preview="true" :folder-type="folderType"
      :folder-path="currentFolderPath" @file-click="handleFileClick">
      <template #actions="{ file }">
        <div class="collections-file-wrapper">
          <div class="collections-file-header">
            <el-input v-if="file.fileType !== 'dir'" :value="file.name" class="filename-input"
              @blur="updateFilename($event, file)" @keyup.enter="($event.target as HTMLInputElement).blur()" />
            <span v-else class="dirname" @click="handleFileClick(file)">{{ file.name }}</span>
          </div>

          <div class="collections-file-actions">
            <el-button v-if="file.fileType !== 'dir'" link type="primary" size="small"
              @click="handleLoadWorkflow(file)">
              {{ t('common.btn.load') }}
            </el-button>
            <el-button link type="danger" size="small" @click="handleDeleteFile(file)">
              <el-icon>
                <Delete />
              </el-icon> {{ t('common.btn.delete') }}
            </el-button>
          </div>

          <div class="collections-file-notes" v-if="file.fileType !== 'dir'">
            <el-input v-model="file.notes" type="textarea" :rows="3" :placeholder="t('collectionsTab.notePlaceholder')"
              resize="none" @blur="handleUpdateNotes(file)" />
          </div>
        </div>
      </template>
    </FileCardList>

    <!-- 加载更多 -->
    <div class="load-more">
      <el-button v-if="filteredFiles.length > displayCursor" @click="loadMoreFiles">
        {{ t('common.loadMore') }}
      </el-button>
      <p v-else-if="filteredFiles.length > 0" class="no-more-text">
        {{ t('common.noMore') }}
      </p>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="filteredFiles.length === 0 && !loading" :description="t('collectionsTab.emptyText')" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete, QuestionFilled } from '@element-plus/icons-vue'
import { fetchFilesList, deleteFile, updateFile } from '@/api/files'
import { getBrowserConfig, updateBrowserConfig, syncCollections } from '@/api/collections'
import type { FileInfo, FolderType } from '@/types'
import { processFileInfo, processDirectoryInfo } from '@/utils'
import FileCardList from '@/components/Common/FileCardList.vue'

export default defineComponent({
  name: 'CollectionsTab',
  components: {
    Search,
    Delete,
    QuestionFilled,
    FileCardList
  },
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      folderType: 'collections' as FolderType,
      currentFolderPath: '',
      allFiles: [] as FileInfo[],
      loading: false,
      syncing: false,
      searchQuery: '',
      displayCursor: 20,
      comfyApp: null as any,
      configGitRepo: '',
      originalGitRepo: ''
    }
  },
  computed: {
    currentPathParts(): string[] {
      return this.currentFolderPath ? this.currentFolderPath.split('/') : []
    },
    filteredFiles(): FileInfo[] {
      if (!this.searchQuery.trim()) {
        return this.allFiles
      }

      const searchLower = this.searchQuery.toLowerCase()
      return this.allFiles.filter(file =>
        file.name.toLowerCase().includes(searchLower) ||
        (file.notes && file.notes.toLowerCase().includes(searchLower))
      )
    },
    displayedFiles(): FileInfo[] {
      return this.filteredFiles.slice(0, this.displayCursor)
    }
  },
  mounted() {
    this.loadFiles()
    this.loadConfig()
    this.setupComfyApp()
    this.setupScrollListener()
  },
  methods: {
    async loadFiles() {
      this.loading = true
      try {
        const response = await fetchFilesList(
          this.folderType,
          this.currentFolderPath || undefined
        )

        const processedFiles: FileInfo[] = []
        response.files.forEach((file) => {
          let processed: FileInfo | null = null
          if (file.type === 'dir') {
            processed = processDirectoryInfo(file)
          } else {
            processed = processFileInfo(file, this.folderType, response.files)
          }

          if (processed) {
            processedFiles.push(processed)
          }
        })

        this.allFiles = processedFiles
        this.displayCursor = 20
      } catch (error) {
        console.error('加载收藏列表失败:', error)
        ElMessage.error(this.t('collectionsTab.loadFailed'))
      } finally {
        this.loading = false
      }
    },
    async loadConfig() {
      try {
        const config = await getBrowserConfig()
        if (config && config.git_repo) {
          this.configGitRepo = config.git_repo
          this.originalGitRepo = config.git_repo
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    },
    async handleSaveConfig() {
      try {
        await updateBrowserConfig({ git_repo: this.configGitRepo })
        this.originalGitRepo = this.configGitRepo
        ElMessage.success(this.t('collectionsTab.configUpdated'))
      } catch (error) {
        console.error('更新配置失败:', error)
        ElMessage.error(this.t('collectionsTab.configUpdateFailed'))
      }
    },
    async handleSync() {
      this.syncing = true
      try {
        await syncCollections()
        ElMessage.success(this.t('collectionsTab.syncSuccess'))
        this.currentFolderPath = ''
        this.loadFiles()
      } catch (error) {
        console.error('同步失败:', error)
        ElMessage.error(this.t('collectionsTab.syncFailed'))
      } finally {
        this.syncing = false
      }
    },
    navigateToPath(index: number) {
      if (index === -1) {
        this.currentFolderPath = ''
      } else {
        this.currentFolderPath = this.currentPathParts
          .slice(0, index + 1)
          .join('/')
      }
      this.loadFiles()
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
    async updateFilename(e: Event, file: FileInfo) {
      const input = e.target as HTMLInputElement
      const newName = input.value

      if (newName === file.name) return

      if (!newName.trim()) {
        ElMessage.warning(this.t('collectionsTab.invalidFilename'))
        input.value = file.name // 恢复原名
        return
      }

      const validFilenameRegex = /^[a-zA-Z0-9-_|\u4E00-\u9FFF]+(\.[a-zA-Z0-9]+)?$/
      if (!validFilenameRegex.test(newName)) {
        ElMessage.warning(this.t('collectionsTab.invalidFilename'))
        input.value = file.name // 恢复原名
        return
      }

      try {
        await updateFile(
          this.folderType,
          file.name,
          { filename: newName },
          file.folder_path || undefined
        )

        file.name = newName // 更新本地状态
        ElMessage.success(this.t('collectionsTab.renameSuccess'))
      } catch (error) {
        console.error('重命名失败:', error)
        ElMessage.error(this.t('collectionsTab.renameFailed'))
        input.value = file.name // 恢复原名
      }
    },
    async handleUpdateNotes(file: FileInfo) {
      try {
        await updateFile(
          this.folderType,
          file.name,
          { notes: file.notes },
          file.folder_path || undefined
        )
      } catch (error) {
        console.error('更新备注失败:', error)
        ElMessage.error(this.t('collectionsTab.updateNotesFailed'))
      }
    },
    async handleDeleteFile(file: FileInfo) {
      try {
        await ElMessageBox.confirm(
          `${this.t('collectionsTab.deleteConfirm')} ${file.name}？`,
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

        ElMessage.success(this.t('collectionsTab.deleteSuccess'))
        this.loadFiles()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除文件失败:', error)
          ElMessage.error(this.t('collectionsTab.deleteFailed'))
        }
      }
    },
    loadMoreFiles() {
      this.displayCursor += 20
    },
    setupComfyApp() {
      this.comfyApp = (window.top as any)?.app

      if (window.top) {
        window.top.addEventListener('comfyuiBrowserShow', () => {
          this.loadFiles()
        })
      }
    },
    setupScrollListener() {
      window.addEventListener('scroll', () => {
        const documentHeight = document.documentElement.scrollHeight
        const scrollPosition = window.innerHeight + window.scrollY

        if (scrollPosition >= documentHeight && this.filteredFiles.length > this.displayCursor) {
          this.loadMoreFiles()
        }
      })
    }
  }
})
</script>

<style scoped lang="scss">
  .collections-tab {
    padding: 16px;
  }

  .sync-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color);

    .help-icon {
      font-size: 24px;
      color: var(--el-text-color-secondary);

      &:hover {
        color: var(--el-color-primary);
      }
    }

    .git-input {
      flex: 1;
      max-width: 500px;
    }
  }

  .toolbar {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    align-items: center;
  }

  .breadcrumb {
    flex: 1;
  }

  .search-input {
    width: 300px;
  }

  .load-more {
    text-align: center;
    padding: 24px 0;
  }

  .no-more-text {
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }

  // Collections特有的样式
  .collections-file-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .collections-file-header {
    .filename-input {
      font-weight: bold;
    }

    .dirname {
      font-weight: bold;
      cursor: pointer;

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }

  .collections-file-actions {
    display: flex;
    gap: 12px;
  }

  .collections-file-notes {
    width: 100%;
  }
</style>
