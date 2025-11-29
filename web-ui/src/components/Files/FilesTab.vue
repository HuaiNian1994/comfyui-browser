<template>
  <div class="files-tab">
    <!-- Breadcrumb和搜索栏 -->
    <div class="toolbar">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item>
          <el-button link @click="navigateToPath(-1)">{{ t('common.rootDir') }}</el-button>
        </el-breadcrumb-item>
        <el-breadcrumb-item v-for="(pathPart, index) in currentPathParts" :key="index">
          <el-button link @click="navigateToPath(index)">{{ pathPart }}</el-button>
        </el-breadcrumb-item>
      </el-breadcrumb>

      <el-input v-model="searchQuery" :placeholder="t('filesTab.searchPlaceholder')" clearable class="search-input">
        <template #prefix>
          <el-icon>
            <Search />
          </el-icon>
        </template>
      </el-input>
    </div>

    <!-- 文件网格 -->
    <div v-loading="loading" class="files-grid">
      <div v-for="file in displayedFiles" :key="file.name" class="file-card">
        <!-- 文件预览 -->
        <div class="file-preview" @click="handleFileClick(file)">
          <el-image v-if="file.fileType === 'image'" :src="file.previewUrl" fit="cover" class="preview-image" lazy />
          <video v-else-if="file.fileType === 'video'" :src="file.previewUrl" class="preview-video" />
          <div v-else-if="file.fileType === 'dir'" class="preview-folder">
            <el-icon :size="48">
              <Folder />
            </el-icon>
          </div>
          <div v-else class="preview-file">
            <el-icon :size="48">
              <Document />
            </el-icon>
          </div>
        </div>

        <!-- 文件信息 -->
        <div class="file-info">
          <p class="file-name" :title="file.name">{{ file.name }}</p>
          <p class="file-meta">{{ file.formattedDatetime }}</p>
          <p class="file-meta">{{ file.formattedSize }}</p>
        </div>

        <!-- 操作按钮 -->
        <div class="file-actions">
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
        </div>
      </div>
    </div>

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
    <el-empty v-if="filteredFiles.length === 0 && !loading" :description="t('filesTab.emptyText')" />

    <!-- 返回顶部按钮 -->
    <el-backtop :right="40" :bottom="40" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Folder, Document, Delete } from '@element-plus/icons-vue'
import { fetchFilesList, deleteFile } from '@/api/files'
import type { FileInfo, FolderType } from '@/types'
import { processFileInfo, processDirectoryInfo } from '@/utils'
import apiClient from '@/api/client'

export default defineComponent({
  name: 'FilesTab',
  components: {
    Search,
    Folder,
    Document,
    Delete
  },
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      folderType: 'outputs' as FolderType,
      currentFolderPath: '',
      allFiles: [] as FileInfo[],
      loading: false,
      searchQuery: '',
      displayCursor: 20,
      comfyApp: null as any
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
        file.name.toLowerCase().includes(searchLower)
      )
    },
    displayedFiles(): FileInfo[] {
      return this.filteredFiles.slice(0, this.displayCursor)
    }
  },
  mounted() {
    this.loadFiles()
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
        console.error('加载文件列表失败:', error)
        ElMessage.error(this.t('filesTab.loadFailed'))
      } finally {
        this.loading = false
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
  .files-tab {
    padding: 16px;
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

  .files-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .file-card {
    background: var(--el-bg-color-page);
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }
  }

  .file-preview {
    width: 100%;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--el-fill-color-light);
    cursor: pointer;
    overflow: hidden;
  }

  .preview-image,
  .preview-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .preview-folder,
  .preview-file {
    color: var(--el-text-color-secondary);
  }

  .file-info {
    padding: 12px;
  }

  .file-name {
    font-weight: 600;
    font-size: 14px;
    margin: 0 0 8px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-meta {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 4px 0;
  }

  .file-actions {
    padding: 0 12px 12px;
    display: flex;
    gap: 8px;

    .el-button {
      padding: 0;
    }
  }

  .load-more {
    text-align: center;
    padding: 24px 0;
  }

  .no-more-text {
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }
</style>
