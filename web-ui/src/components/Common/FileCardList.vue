<template>
  <div class="file-card-list">
    <!-- 顶部工具栏 -->
    <div class="list-toolbar">
      <div class="toolbar-items">
        <div class="header-slot">
          <slot name="header"></slot>
        </div>
        <el-input v-model="internalSearchQuery" :placeholder="t('common.searchPlaceholder')" clearable
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
          layout="prev, pager, next, sizes, jumper, ->, total" background class="toolbar-pagination"
          @current-change="handlePageChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- 文件网格 -->
    <div v-loading="loading" class="files-grid">
      <div v-for="file in paginatedFiles" :key="file.path || file.name" class="file-card">
        <!-- 文件预览 -->
        <div class="file-preview" @click="handlePreviewClick(file)">
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

        <!-- 操作按钮 -->
        <div class="file-actions">
          <slot name="actions" :file="file">
            <!-- 默认无操作按钮,由父组件通过slot提供 -->
          </slot>
        </div>
      </div>
    </div>

    <!-- 图片预览对话框 -->
    <ImagePreviewDialog v-if="enableImagePreview" v-model="showImagePreview" :image-url="previewImageUrl"
      :image-name="previewImageName" :folder-type="folderType" :folder-path="folderPath" />

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
  emits: ['file-click', 'page-change'],
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
      internalSearchQuery: ''
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
    }
  },
  watch: {
    files() {
      this.handleFilesChange()
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
    handlePreviewClick(file: FileInfo) {
      if (file.fileType === 'dir') {
        // 文件夹点击,触发导航
        this.$emit('file-click', file)
      } else if (file.fileType === 'image' && this.enableImagePreview) {
        // 图片点击,打开预览
        this.previewImageUrl = file.previewUrl || ''
        this.previewImageName = file.name
        this.showImagePreview = true
      }
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

    :deep(.el-button) {
      padding: 0;
    }
  }
</style>
