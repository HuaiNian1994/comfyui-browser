<template>
  <div class="files-tab">
    <!-- 文件列表 -->
    <FileCardList :files="allFiles" :loading="loading" :enable-image-preview="true" :folder-type="folderType"
      :folder-path="currentFolderPath" :empty-description="t('filesTab.emptyText')" @file-click="handleFileClick" @refresh="loadFiles">
      <template #header>
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item>
            <el-button link @click="navigateToPath(-1)">{{ t('common.rootDir') }}</el-button>
          </el-breadcrumb-item>
          <el-breadcrumb-item v-for="(pathPart, index) in currentPathParts" :key="index">
            <el-button link @click="navigateToPath(index)">{{ pathPart }}</el-button>
          </el-breadcrumb-item>
        </el-breadcrumb>
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
import { fetchFilesList, deleteFile } from '@/api/files'
import type { FileInfo, FolderType } from '@/types'
import { processFileInfo, processDirectoryInfo } from '@/utils'
import { batchDeleteFiles, batchCollectFiles } from '@/utils/batch-actions'
import apiClient from '@/api/client'
import FileCardList from '@/components/Common/FileCardList.vue'

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
      currentFolderPath: '',
      allFiles: [] as FileInfo[],
      loading: false,
      comfyApp: null as any
    }
  },
  computed: {
    currentPathParts(): string[] {
      return this.currentFolderPath ? this.currentFolderPath.split('/') : []
    }
  },
  mounted() {
    this.loadFiles()
    this.setupComfyApp()
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
  }
</style>
