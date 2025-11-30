<template>
  <div class="file-card-list">
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

    <!-- 分页器 -->
    <div v-if="pagination && files.length > pageSize" class="pagination-container">
      <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="files.length"
        layout="total, prev, pager, next, jumper" background @current-change="handlePageChange" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { Folder, Document } from '@element-plus/icons-vue'
import type { FileInfo, FolderType } from '@/types'
import ImagePreviewDialog from './ImagePreviewDialog.vue'

export default defineComponent({
  name: 'FileCardList',
  components: {
    Folder,
    Document,
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
    }
  },
  emits: ['file-click', 'page-change'],
  data() {
    return {
      showImagePreview: false,
      previewImageUrl: '',
      previewImageName: '',
      currentPage: 1
    }
  },
  computed: {
    paginatedFiles(): FileInfo[] {
      if (!this.pagination) {
        return this.files
      }
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.files.slice(start, end)
    }
  },
  watch: {
    files() {
      // 当文件列表变化时，如果当前页码超出范围，重置为1
      // 或者如果列表被清空/搜索结果变化，通常也希望重置
      // 这里简单处理：如果当前页为空且不是第一页，则往前翻
      // 但更常见的行为是搜索/筛选时重置为1。
      // 既然我们不知道外部是因为搜索变了还是只是数据刷新，
      // 比较安全的做法是：如果 files 变了，且 current page 现在的 start index 超过了 length，就重置。
      // 为了简单且符合直觉（比如搜索），默认重置到第一页可能更好？
      // 不，如果用户只是删除了当前页的一个文件，导致列表变短，不应该跳回第一页。
      // 只有当 currentPage 超过最大页数时才调整。
      const maxPage = Math.ceil(this.files.length / this.pageSize) || 1
      if (this.currentPage > maxPage) {
        this.currentPage = maxPage
      }
    }
  },
  methods: {
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
    }
  }
})
</script>

<style scoped lang="scss">
  .file-card-list {
    width: 100%;
  }

  .files-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 24px;
    padding-bottom: 24px;
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
