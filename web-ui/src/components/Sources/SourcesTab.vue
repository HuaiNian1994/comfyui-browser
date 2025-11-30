<template>
  <div class="sources-tab">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-button type="primary" plain class="add-btn" @click="showAddModal = true">
          <el-icon>
            <Plus />
          </el-icon> {{ t('sourcesTab.addSource') }}
        </el-button>
      </div>

      <div class="sources-list">
        <div v-for="source in sources" :key="source.name" class="source-item"
          :class="{ active: currentSource?.name === source.name }" @click="handleSourceClick(source)">
          <div class="source-icon">
            <el-icon v-if="!source.homepage">
              <Document />
            </el-icon>
            <a v-else :href="source.homepage" target="_blank" @click.stop>
              <img v-if="source.homepage.includes('github.com')" src="https://github.com/favicon.ico"
                class="github-icon" />
              <el-icon v-else>
                <Link />
              </el-icon>
            </a>
          </div>

          <div class="source-name" :title="source.name">
            {{ source.name }}
          </div>

          <div class="source-actions">
            <el-button link type="primary" :loading="syncingSource === source.name"
              @click.stop="handleSyncSource(source)">
              <el-icon>
                <Refresh />
              </el-icon>
            </el-button>
            <el-button link type="danger" @click.stop="handleDeleteSource(source)">
              <el-icon>
                <Delete />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="content">
      <div v-if="!currentSource" class="empty-selection">
        <el-empty :description="t('sourcesTab.selectSource')" />
      </div>

      <!-- 文件列表 -->
      <FileCardList v-else :files="allFiles" :loading="loadingFiles" :enable-image-preview="true"
        :folder-type="'sources'" :folder-path="currentFolderPath" :empty-description="t('sourcesTab.emptyFiles')" @file-click="handleFileClick">
        <template #header>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item>
              <el-button link @click="navigateToPath(-1)">{{ currentSource.name }}</el-button>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-for="(pathPart, index) in currentPathParts" :key="index">
              <el-button link @click="navigateToPath(index)">{{ pathPart }}</el-button>
            </el-breadcrumb-item>
          </el-breadcrumb>
        </template>
        <template #actions="{ file }">
          <el-button v-if="file.fileType !== 'dir'" link type="primary" size="small"
            @click="handleLoadWorkflow(file)">
            {{ t('common.btn.load') }}
          </el-button>
        </template>
      </FileCardList>
    </div>

    <!-- Add Source Dialog -->
    <el-dialog v-model="showAddModal" :title="t('sourcesTab.addSource')" width="80%" class="add-source-dialog">
      <div class="add-source-header">
        <el-input v-model="inputRepoUrl" :placeholder="t('sourcesTab.inputPlaceholder')" class="repo-input">
          <template #append>
            <el-button type="primary" :loading="addingSource" :disabled="!inputRepoUrl"
              @click="handleAddSource(inputRepoUrl)">
              {{ addingSource ? t('sourcesTab.subscribing') : t('sourcesTab.subscribe') }}
            </el-button>
          </template>
        </el-input>
      </div>

      <div v-loading="loadingAllSources" class="recommended-sources">
        <div v-for="s in allSources" :key="s.url" class="source-recommendation">
          <div class="rec-icon">
            <img :src="`https://github.com/${s.author}.png`" :alt="s.author" />
          </div>
          <div class="rec-info">
            <div class="rec-title">
              <a :href="s.url" target="_blank" class="rec-link">{{ s.author }}/{{ s.title }}</a>
              <img :src="`https://img.shields.io/github/stars${getRepoPath(s.url)}?style=flat-square`" alt="stars"
                class="stars-badge" />
            </div>
            <p class="rec-desc">{{ s.description }}</p>
          </div>
          <div class="rec-action">
            <el-button type="primary" plain :loading="addingSource && inputRepoUrl === s.url"
              @click="handleAddSource(s.url)">
              {{ (addingSource && inputRepoUrl === s.url) ? t('sourcesTab.subscribing') : t('sourcesTab.subscribe') }}
            </el-button>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <p>
          {{ t('sourcesTab.prText') }} <a
            href="https://github.com/talesofai/comfyui-browser/edit/main/data/sources.json" target="_blank">PR</a> {{
              t('sourcesTab.issueText') }}
          <a href="https://github.com/talesofai/comfyui-browser/issues" target="_blank">Issue</a> {{
            t('sourcesTab.addRepoText') }}
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Link, Refresh, Delete } from '@element-plus/icons-vue'
import { fetchSources, fetchAllSources, addSource, deleteSource, syncSource } from '@/api/sources'
import { fetchFilesList } from '@/api/files'
import type { Source } from '@/api/sources'
import type { FileInfo, FolderType } from '@/types'
import { processFileInfo, processDirectoryInfo } from '@/utils'
import FileCardList from '@/components/Common/FileCardList.vue'

export default defineComponent({
  name: 'SourcesTab',
  components: {
    Plus,
    Document,
    Link,
    Refresh,
    Delete,
    FileCardList
  },
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      sources: [] as Source[],
      allSources: [] as Source[],
      currentSource: null as Source | null,
      currentFolderPath: '',

      // Files logic
      allFiles: [] as FileInfo[],
      loadingFiles: false,

      // UI states
      showAddModal: false,
      inputRepoUrl: '',
      syncingSource: '',
      addingSource: false,
      loadingAllSources: false,

      comfyApp: null as any
    }
  },
  computed: {
    currentPathParts(): string[] {
      if (!this.currentFolderPath) return []
      // currentFolderPath includes source.name as the first part, we only show the rest
      const parts = this.currentFolderPath.split('/')
      return parts.slice(1)
    }
  },
  mounted() {
    this.loadSources()
    this.loadAllSources()
    this.setupComfyApp()
  },
  methods: {
    getRepoPath(url: string) {
      try {
        return new URL(url).pathname
      } catch (e) {
        return ''
      }
    },
    async loadSources() {
      try {
        const response = await fetchSources()
        this.sources = response.sources.map(s => {
          // Process homepage
          let homepage = ''
          if (s.url.startsWith('https://')) {
            homepage = s.url
            if (homepage.endsWith('.git')) {
              homepage = homepage.slice(0, -4)
            }
          }
          return { ...s, homepage }
        })
      } catch (error) {
        console.error('Failed to load sources:', error)
        ElMessage.error(this.t('sourcesTab.loadSourcesFailed'))
      }
    },
    async loadAllSources() {
      this.loadingAllSources = true
      try {
        const response = await fetchAllSources()
        this.allSources = response.sources
      } catch (error) {
        console.error('Failed to load recommended sources:', error)
        ElMessage.error(this.t('sourcesTab.loadRecommendedFailed'))
      } finally {
        this.loadingAllSources = false
      }
    },
    async handleSourceClick(source: Source) {
      this.currentSource = source
      this.currentFolderPath = source.name
      this.loadFiles()
    },
    async handleSyncSource(source: Source) {
      this.syncingSource = source.name
      try {
        await syncSource(source.name)
        ElMessage.success(this.t('sourcesTab.syncSuccess'))
        this.loadSources()
        if (this.currentSource?.name === source.name) {
          this.loadFiles()
        }
      } catch (error) {
        console.error('Sync failed:', error)
        ElMessage.error(this.t('sourcesTab.syncFailed'))
      } finally {
        this.syncingSource = ''
      }
    },
    async handleDeleteSource(source: Source) {
      try {
        await ElMessageBox.confirm(
          this.t('sourcesTab.deleteConfirm'),
          this.t('common.btn.delete'),
          {
            confirmButtonText: this.t('common.btn.delete'),
            cancelButtonText: this.t('common.btn.cancel'),
            type: 'warning'
          }
        )

        await deleteSource(source.name)
        ElMessage.success(this.t('sourcesTab.deleteSuccess'))
        this.loadSources()
        if (this.currentSource?.name === source.name) {
          this.currentSource = null
          this.allFiles = []
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Delete failed:', error)
          ElMessage.error(this.t('sourcesTab.deleteFailed'))
        }
      }
    },
    async handleAddSource(url: string) {
      if (!url) return

      this.addingSource = true
      try {
        await addSource(url)
        ElMessage.success(this.t('sourcesTab.addSuccess'))
        this.showAddModal = false
        this.inputRepoUrl = ''
        this.loadSources()
      } catch (error) {
        console.error('Add source failed:', error)
        ElMessage.error(this.t('sourcesTab.addFailed'))
      } finally {
        this.addingSource = false
      }
    },

    // File List Methods
    async loadFiles() {
      if (!this.currentSource) return

      this.loadingFiles = true
      try {
        const response = await fetchFilesList(
          'sources' as FolderType,
          this.currentFolderPath
        )

        const processedFiles: FileInfo[] = []
        response.files.forEach((file) => {
          let processed: FileInfo | null = null
          if (file.type === 'dir') {
            processed = processDirectoryInfo(file)
          } else {
            processed = processFileInfo(file, 'sources' as FolderType, response.files)
          }

          if (processed) {
            processedFiles.push(processed)
          }
        })

        this.allFiles = processedFiles
      } catch (error) {
        console.error('Load files failed:', error)
        ElMessage.error(this.t('sourcesTab.loadFilesFailed'))
      } finally {
        this.loadingFiles = false
      }
    },
    navigateToPath(index: number) {
      if (!this.currentSource) return

      if (index === -1) {
        this.currentFolderPath = this.currentSource.name
      } else {
        const parts = this.currentFolderPath.split('/')
        // parts[0] is source name
        // index is relative to parts.slice(1)
        // so we need parts.slice(0, index + 2) (source name + index + 1 path parts)
        this.currentFolderPath = parts.slice(0, index + 2).join('/')
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
      if (!this.comfyApp || !file.url) return

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
      } catch (error) {
        console.error('Load workflow failed:', error)
        ElMessage.error(this.t('sourcesTab.loadWorkflowFailed'))
      }
    },
    setupComfyApp() {
      this.comfyApp = (window.top as any)?.app
    }
  }
})
</script>

<style scoped lang="scss">
  .sources-tab {
    display: flex;
    height: 100%;
    overflow: hidden;
  }

  .sidebar {
    width: 250px;
    border-right: 1px solid var(--el-border-color);
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color-page);
    flex-shrink: 0;
  }

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color);

    .add-btn {
      width: 100%;
    }
  }

  .sources-list {
    flex: 1;
    overflow-y: auto;
  }

  .source-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    &.active {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
    }
  }

  .source-icon {
    margin-right: 12px;
    display: flex;
    align-items: center;

    .github-icon {
      width: 16px;
      height: 16px;
    }
  }

  .source-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 14px;
  }

  .source-actions {
    display: flex;
    opacity: 0;
    transition: opacity 0.2s;

    .source-item:hover & {
      opacity: 1;
    }
  }

  .content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 16px;
  }

  .empty-selection {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .files-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* Dialog Styles */
  .add-source-header {
    margin-bottom: 24px;
  }

  .recommended-sources {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
  }

  .source-recommendation {
    display: flex;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color);
    gap: 16px;

    &:last-child {
      border-bottom: none;
    }
  }

  .rec-icon img {
    width: 48px;
    height: 48px;
    border-radius: 50%;
  }

  .rec-info {
    flex: 1;
  }

  .rec-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;

    .rec-link {
      font-size: 16px;
      font-weight: bold;
      color: var(--el-color-primary);
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }

    .stars-badge {
      height: 20px;
    }
  }

  .rec-desc {
    font-size: 14px;
    color: var(--el-text-color-regular);
    line-height: 1.4;
  }

  .dialog-footer {
    margin-top: 16px;
    text-align: center;
    font-size: 12px;
    color: var(--el-text-color-secondary);

    a {
      color: var(--el-color-primary);
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }
  }
</style>