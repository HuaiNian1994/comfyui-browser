<template>
  <div class="file-card-list">
    <!-- 文件网格 -->
    <div v-loading="loading" class="files-grid">
      <div v-for="file in files" :key="file.path || file.name" class="file-card">
        <!-- 文件预览 -->123456
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
    }
  },
  emits: ['file-click'],
  data() {
    return {
      showImagePreview: false,
      previewImageUrl: '',
      previewImageName: ''
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
