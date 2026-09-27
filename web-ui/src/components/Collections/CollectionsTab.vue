<template>
  <div class="collections-tab">
    <div v-if="directoryErrors.length || summaryPaused || reindexStatus" class="directory-status">
      <span v-for="path in directoryErrors" :key="path">目录 {{ path || '/' }} 加载失败 <el-button link @click="requestScopeRefresh(path)">重试</el-button></span>
      <span v-if="summaryPaused">摘要更新已暂停 <el-button link @click="retrySummary">重试</el-button></span>
      <span v-if="reindexStatus">重建状态：{{ ({ queued: '排队中', running: '进行中', complete: '完成', failed: '失败', expired: '已过期', unknown: '创建结果未知，可重新发起'  } as Record<string, string>)[reindexStatus] }}；成功 {{ reindexCounts.success_count }}，失败 {{ reindexCounts.failed_count }}，已被新版本替代 {{ reindexCounts.superseded_count }}</span>
    </div>
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

    <!-- 文件列表 -->
    <FileCardList :scope-revision="scopeRevision" @visible-files="updateVisibleFiles" @stale="requestScopeRefresh" @reindex="startReindex" :files="allFiles" :loading="loading" :enable-image-preview="true" :folder-type="folderType"
      :folder-path="currentFolderPath" :empty-description="t('collectionsTab.emptyText')" @file-click="handleFileClick" @refresh="loadFiles">
      <template #header>
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item>
            <el-button link @click="handleBreadcrumbClick(-1)">{{ t('common.rootDir') }}</el-button>
          </el-breadcrumb-item>
          <el-breadcrumb-item v-for="(pathPart, index) in currentPathParts" :key="index">
            <el-button link @click="handleBreadcrumbClick(index)">{{ pathPart }}</el-button>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </template>

      <template #batch-actions="{ selectedFiles, clearSelection }">
        <el-button type="danger" @click="handleBatchDelete(selectedFiles, clearSelection)">
          {{ t('common.batchDelete') }}
        </el-button>
      </template>

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
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import directoryPage from '@/utils/directory-page'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, QuestionFilled } from '@element-plus/icons-vue'
import { deleteFile, updateFile, openFolderOnSystem } from '@/api/files'
import { getBrowserConfig, updateBrowserConfig, syncCollections } from '@/api/collections'
import type { FileInfo, FolderType } from '@/types'
import { batchDeleteFiles } from '@/utils/batch-actions'
import FileCardList from '@/components/Common/FileCardList.vue'

export default defineComponent({
  mixins: [directoryPage],
  name: 'CollectionsTab',
  components: {
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
      comfyApp: null as any,
      configGitRepo: '',
      originalGitRepo: ''
    }
  },
  computed: {
    currentPathParts(): string[] {
      return this.currentFolderPath ? this.currentFolderPath.split('/') : []
    }
  },
  mounted() {
    this.loadFiles()
    this.loadConfig()
    this.setupComfyApp()
  },
  methods: {
    async loadFiles() {
      await this.loadDirectoryScope(this.folderType, [this.currentFolderPath])
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
      if (this.syncing) return

      this.syncing = true
      try {
        const result = await syncCollections()
        if (result.success) {
          ElMessage.success(this.t('collectionsTab.syncSuccess'))
          this.loadFiles()
        } else {
          ElMessage.warning(this.t('collectionsTab.syncPartial') + (result.message ? `: ${result.message}` : ''))
        }
      } catch (error) {
        console.error('同步失败:', error)
        ElMessage.error(this.t('collectionsTab.syncFailed'))
      } finally {
        this.syncing = false
      }
    },
    async handleBreadcrumbClick(index: number) {
      const targetPath = index === -1
        ? ''
        : this.currentPathParts
          .slice(0, index + 1)
          .join('/')
      await this.openFolderInExplorer(targetPath)
      this.navigateToPath(index)
    },
    async openFolderInExplorer(targetPath: string) {
      try {
        await openFolderOnSystem(this.folderType, targetPath || undefined)
      } catch (error) {
        console.error('打开文件夹失败:', error)
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
    setupComfyApp() {
      this.comfyApp = (window.top as any)?.app

      this.registerBrowserShow()
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
