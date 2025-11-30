<template>
  <div class="file-card-list">
    <!-- 顶部工具栏 -->
    <div class="list-toolbar">
      <div class="toolbar-items">
        <div class="header-slot">
          <slot name="header"></slot>
        </div>
        
        <!-- 管理模式按钮 -->
        <el-button 
          v-if="hasBatchActions"
          :type="isManagementMode ? 'primary' : 'default'" 
          @click="toggleManagementMode"
        >
          {{ isManagementMode ? t('common.exitManage') : t('common.manage') }}
        </el-button>

        <!-- 批量操作工具栏 -->
        <template v-if="isManagementMode">
          <el-button-group>
            <el-button @click="handleSelectAll">{{ t('common.selectAll') }}</el-button>
            <el-button @click="handleInvertSelect">{{ t('common.invertSelect') }}</el-button>
          </el-button-group>
          
          <span class="selection-count" v-if="selectedCount > 0">
            {{ t('common.selected', { count: selectedCount }) }}
          </span>

          <div class="batch-actions" v-if="selectedCount > 0">
             <slot name="batch-actions" :selected-files="selectedFilesArray" :clear-selection="clearSelection">
               <!-- 默认无批量操作按钮 -->
             </slot>
          </div>
        </template>

        <!-- 搜索框 (仅在非管理模式或空间足够时显示) -->
        <el-input v-if="!isManagementMode" v-model="internalSearchQuery" :placeholder="t('common.searchPlaceholder')" clearable
          class="search-input">
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>
        
        <div class="spacer"></div>
        <!-- 分页器 -->
        <el-pagination v-if="pagination && filteredFiles.length > 0" v-model:current-page="currentPage"
          v-model:page-size="internalPageSize" :page-sizes="[20, 50, 100]" :total="filteredFiles.length"
          layout="prev, pager, next, sizes, jumper, ->, total" size="small" class="toolbar-pagination"
          @current-change="handlePageChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- 文件网格 -->
    <div v-loading="loading || isBatchProcessing" class="files-grid">
      <div 
        v-for="file in paginatedFiles" 
        :key="file.path || file.name" 
        class="file-card"
        :class="{ 'is-selected': isSelected(file), 'is-management': isManagementMode }"
        @click="handleCardClick(file)"
      >
        <!-- 选择遮罩 -->
        <div v-if="isManagementMode" class="selection-overlay">
          <el-checkbox :model-value="isSelected(file)" @click.stop="toggleSelection(file)" />
        </div>

        <!-- 文件预览 -->
        <div class="file-preview">
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
          <p v-if="file.formattedSize" class="file-meta">{{ file.formattedSize }}</p>
        </div>

        <!-- 操作按钮 (仅非管理模式显示) -->
        <div v-if="!isManagementMode" class="file-actions" @click.stop>
          <slot name="actions" :file="file">
            <!-- 默认无操作按钮,由父组件通过slot提供 -->
          </slot>
        </div>
      </div>
    </div>

    <!-- 图片预览对话框 -->
    <ImagePreviewDialog v-if="enableImagePreview" v-model="showImagePreview" :preview-file-list="previewableFiles"
      :initial-index="currentPreviewIndex" :folder-type="folderType" :folder-path="folderPath">
      <template #actions="{ file }">
        <slot name="actions" :file="file">
        </slot>
      </template>
    </ImagePreviewDialog>

    <!-- 空状态 -->
    <el-empty v-if="filteredFiles.length === 0 && !loading" :description="emptyDescription || t('common.emptyList')" />
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { useI18n } from 'vue-i18n'
import { Folder, Document, Search } from '@element-plus/icons-vue'
import type { FileInfo, FolderType } from '@/types'
import ImagePreviewDialog from './ImagePreviewDialog.vue'

export default defineComponent({
  name: 'FileCardList',
  components: {
    Folder,
    Document,
    Search,
    ImagePreviewDialog
  },
  props: {
    files: {
      type: Array as PropType<FileInfo[]>,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    enableImagePreview: {
      type: Boolean,
      default: true
    },
    folderType: {
      type: String as PropType<FolderType>,
      required: true
    },
    folderPath: {
      type: String,
      default: ''
    },
    pagination: {
      type: Boolean,
      default: true
    },
    pageSize: {
      type: Number,
      default: 20
    },
    emptyDescription: {
      type: String,
      default: ''
    }
  },
  emits: ['file-click', 'page-change', 'refresh'],
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      showImagePreview: false,
      previewImageUrl: '',
      previewImageName: '',
      currentPage: 1,
      internalPageSize: this.pageSize,
      internalSearchQuery: '',
      currentPreviewIndex: -1,
      // 管理模式相关
      isManagementMode: false,
      selectedFiles: new Set<string>(), // 存储选中文件的 name
      isBatchProcessing: false
    }
  },
  computed: {
    filteredFiles(): FileInfo[] {
      if (!this.internalSearchQuery.trim()) {
        return this.files
      }

      const terms = this.internalSearchQuery.trim().split(/\s+/)
      const includeTerms = terms.filter(t => !t.startsWith('-')).map(t => t.toLowerCase())
      const excludeTerms = terms.filter(t => t.startsWith('-') && t.length > 1).map(t => t.slice(1).toLowerCase())

      const getDisplayValues = (file: FileInfo): string => {
        const values = []
        if (file.name) values.push(file.name)
        if (file.formattedDatetime) values.push(file.formattedDatetime)
        if (file.formattedSize) values.push(file.formattedSize)
        return values.join(' ')
      }

      return this.files.filter(file => {
        const content = getDisplayValues(file).toLowerCase()

        const hasAllIncludes = includeTerms.every(term => content.includes(term))
        const hasNoExcludes = excludeTerms.every(term => !content.includes(term))

        return hasAllIncludes && hasNoExcludes
      })
    },
    paginatedFiles(): FileInfo[] {
      if (!this.pagination) {
        return this.filteredFiles
      }
      const start = (this.currentPage - 1) * this.internalPageSize
      const end = start + this.internalPageSize
      return this.filteredFiles.slice(start, end)
    },
    previewableFiles(): FileInfo[] {
      return this.filteredFiles.filter(f => f.fileType === 'image')
    },
    hasPrev(): boolean {
      return this.currentPreviewIndex > 0
    },
    hasNext(): boolean {
      return this.currentPreviewIndex >= 0 && this.currentPreviewIndex < this.previewableFiles.length - 1
    },
    // 管理模式计算属性
    selectedCount(): number {
      return this.selectedFiles.size
    },
    isAllSelected(): boolean {
      if (this.filteredFiles.length === 0) return false
      return this.filteredFiles.every(f => this.selectedFiles.has(f.name))
    },
    selectedFilesArray(): FileInfo[] {
      const selectedNames = this.selectedFiles
      return this.files.filter(f => selectedNames.has(f.name))
    },
    hasBatchActions(): boolean {
      return !!this.$slots['batch-actions']
    }
  },
  watch: {
    files() {
      this.handleFilesChange()
      // 文件列表变化时，清理不在列表中的选中项
      if (this.isManagementMode) {
        const currentNames = new Set(this.files.map(f => f.name))
        for (const name of this.selectedFiles) {
          if (!currentNames.has(name)) {
            this.selectedFiles.delete(name)
          }
        }
      }
    },
    pageSize(newVal) {
      this.internalPageSize = newVal
    },
    internalSearchQuery() {
      this.currentPage = 1
    }
  },
  methods: {
    handleFilesChange() {
      const maxPage = Math.ceil(this.filteredFiles.length / this.internalPageSize) || 1
      if (this.currentPage > maxPage) {
        this.currentPage = maxPage
      }
    },
    handleCardClick(file: FileInfo) {
      if (this.isManagementMode) {
        this.toggleSelection(file)
      } else {
        this.handlePreviewClick(file)
      }
    },
    handlePreviewClick(file: FileInfo) {
      if (file.fileType === 'dir') {
        // 文件夹点击,触发导航
        this.$emit('file-click', file)
      } else if (file.fileType === 'image' && this.enableImagePreview) {
        // 图片点击,打开预览
        this.updatePreviewState(file)
        this.showImagePreview = true
      }
    },
    updatePreviewState(file: FileInfo) {
      this.previewImageUrl = file.previewUrl || ''
      this.previewImageName = file.name
      this.currentPreviewIndex = this.previewableFiles.findIndex(f => f.name === file.name)
    },
    handlePageChange(page: number) {
      this.currentPage = page
      this.$emit('page-change', page)
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    handleSizeChange(size: number) {
      this.internalPageSize = size
      this.currentPage = 1
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    // 管理模式方法
    toggleManagementMode() {
      this.isManagementMode = !this.isManagementMode
      if (!this.isManagementMode) {
        this.selectedFiles.clear()
      }
    },
    isSelected(file: FileInfo): boolean {
      return this.selectedFiles.has(file.name)
    },
    toggleSelection(file: FileInfo) {
      if (this.selectedFiles.has(file.name)) {
        this.selectedFiles.delete(file.name)
      } else {
        this.selectedFiles.add(file.name)
      }
    },
    handleSelectAll() {
      if (this.isAllSelected) {
        this.selectedFiles.clear()
      } else {
        this.filteredFiles.forEach(f => this.selectedFiles.add(f.name))
      }
    },
    handleInvertSelect() {
      this.filteredFiles.forEach(f => {
        if (this.selectedFiles.has(f.name)) {
          this.selectedFiles.delete(f.name)
        } else {
          this.selectedFiles.add(f.name)
        }
      })
    },
    clearSelection() {
      this.selectedFiles.clear()
      this.isManagementMode = false
    }
  }
})
</script>

<style scoped lang="scss">
  .file-card-list {
    width: 100%;
  }

  .list-toolbar {
    margin-bottom: 16px;
  }

  .toolbar-items {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;

    .header-slot {
      display: flex;
      align-items: center;
    }

    .search-input {
      width: 300px;
    }

    .selection-count {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      font-weight: 600;
    }

    .batch-actions {
      display: flex;
      gap: 8px;
    }

    .spacer {
      flex: 1;
    }

    .toolbar-pagination {
      :deep(.el-pagination__total) {
        margin-right: 12px;
      }
    }
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
    position: relative;

    &:hover {
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }

    &.is-selected {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
      box-shadow: 0 0 0 1px var(--el-color-primary);
    }

    &.is-management {
      cursor: pointer;
    }
  }

  .selection-overlay {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    pointer-events: none; // Let clicks pass through to card, but we handle checkbox click specifically

    :deep(.el-checkbox) {
      pointer-events: auto;
      
      .el-checkbox__inner {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border-width: 2px;
        
        &::after {
          height: 10px;
          left: 6px;
          width: 4px;
        }
      }
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

    :deep(.el-button) {
      padding: 0;
    }
  }
</style>
