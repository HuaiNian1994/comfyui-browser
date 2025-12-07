<template>
  <div v-if="modelValue" class="image-preview-wrapper">
    <el-image-viewer
      :url-list="previewUrls"
      :initial-index="initialIndex"
      @close="handleClose"
      @switch="handleSwitch"
    />
    
    <!-- Metadata Sidebar -->
    <div class="preview-sidebar" @click.stop>
      <div class="sidebar-content" v-loading="loading">
        <div class="sidebar-header">
          <h3>{{ t('imagePreview.metadata') || 'Metadata' }}</h3>
          <el-button link @click="handleClose">
            <el-icon :size="20"><Close /></el-icon>
          </el-button>
        </div>

        <div v-if="currentFile" class="file-basic-info">
          <p class="file-name" :title="currentFile.name">{{ currentFile.name }}</p>
          <p class="file-meta">{{ currentFile.formattedDatetime }}</p>
          <p v-if="currentFile.formattedSize" class="file-meta">{{ currentFile.formattedSize }}</p>
          <div class="file-actions">
            <slot name="actions" :file="currentFile"></slot>
          </div>
        </div>

        <div v-if="!metadata.has_metadata && !loading" class="no-metadata">
          <el-icon><WarningFilled /></el-icon>
          <span>{{ t('imagePreview.noMetadata') }}</span>
        </div>

        <div v-else class="prompts-content">
          <!-- Positive Prompt -->
          <div class="prompt-block">
            <h4>{{ t('imagePreview.positivePrompt') }}</h4>
            <div class="prompt-text">{{ metadata.positive || t('imagePreview.noPrompt') }}</div>
            <el-button v-if="metadata.positive" size="small" @click="copyPrompt(metadata.positive)" text bg>
              <el-icon><CopyDocument /></el-icon>
              {{ t('imagePreview.copyPrompt') }}
            </el-button>
          </div>

          <!-- Negative Prompt -->
          <div class="prompt-block">
            <h4>{{ t('imagePreview.negativePrompt') }}</h4>
            <div class="prompt-text">{{ metadata.negative || t('imagePreview.noPrompt') }}</div>
            <el-button v-if="metadata.negative" size="small" @click="copyPrompt(metadata.negative)" text bg>
              <el-icon><CopyDocument /></el-icon>
              {{ t('imagePreview.copyPrompt') }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElImageViewer, ElMessage } from 'element-plus'
import { Loading, WarningFilled, CopyDocument, Close } from '@element-plus/icons-vue'
import { fetchImageMetadata } from '@/api/files'
import type { FolderType, ImageMetadata, FileInfo } from '@/types'

export default defineComponent({
  name: 'ImagePreviewDialog',
  components: {
    ElImageViewer,
    Loading,
    WarningFilled,
    CopyDocument,
    Close
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    previewFileList: {
      type: Array as PropType<FileInfo[]>,
      default: () => []
    },
    initialIndex: {
      type: Number,
      default: 0
    },
    folderType: {
      type: String as PropType<FolderType>,
      default: 'sources'
    },
    folderPath: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      currentIndex: this.initialIndex,
      loading: false,
      metadata: {
        positive: '',
        negative: '',
        has_metadata: false
      } as ImageMetadata
    }
  },
  computed: {
    previewUrls(): string[] {
      return this.previewFileList.map(file => file.previewUrl || '')
    },
    currentFile(): FileInfo | undefined {
      return this.previewFileList[this.currentIndex]
    }
  },
  watch: {
    modelValue(val) {
      if (val) {
        this.currentIndex = this.initialIndex
        this.loadMetadata()
      }
    },
    // Watch initialIndex in case it changes while open (unlikely but safe)
    initialIndex(val) {
      if (this.modelValue) {
        this.currentIndex = val
      }
    }
  },
  mounted() {
    if (this.modelValue) {
      this.loadMetadata()
    }
  },
  methods: {
    handleClose() {
      this.$emit('update:modelValue', false)
    },
    handleSwitch(index: number) {
      this.currentIndex = index
      this.loadMetadata()
    },
    async loadMetadata() {
      const file = this.currentFile
      if (!file) return

      this.loading = true
      try {
        const targetFolderPath = file.folder_path || this.folderPath
        this.metadata = await fetchImageMetadata(
          this.folderType,
          file.name,
          targetFolderPath
        )
      } catch (error) {
        console.error('Failed to load image metadata:', error)
        this.metadata = {
          positive: '',
          negative: '',
          has_metadata: false
        }
      } finally {
        this.loading = false
      }
    },
    async copyPrompt(text: string) {
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success(this.t('imagePreview.copySuccess'))
      } catch (error) {
        console.error('Failed to copy:', error)
        ElMessage.error(this.t('imagePreview.copyFailed'))
      }
    }
  }
})
</script>

<style scoped lang="scss">
.image-preview-wrapper {
  position: relative;
  z-index: 2000;

  .preview-sidebar {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 320px;
    background: var(--el-bg-color);
    box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
    z-index: 3000; /* Higher than el-image-viewer (usually around 2000) */
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease;

    .sidebar-content {
      height: 100%;
      display: flex;
      flex-direction: column;
      overflow: hidden;

      .sidebar-header {
        padding: 16px;
        border-bottom: 1px solid var(--el-border-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-shrink: 0;

        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }
      }

      .file-basic-info {
        padding: 16px;
        border-bottom: 1px solid var(--el-border-color);
        flex-shrink: 0;

        .file-name {
          font-weight: 600;
          font-size: 14px;
          margin: 0 0 8px 0;
          word-break: break-word;
        }

        .file-meta {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          margin: 4px 0;
        }

        .file-actions {
          margin-top: 12px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
      }

      .prompts-content {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 24px;

        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-thumb {
          background-color: var(--el-border-color);
          border-radius: 3px;
        }

        &::-webkit-scrollbar-track {
          background-color: transparent;
        }

        .prompt-block {
          h4 {
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }

          .prompt-text {
            padding: 12px;
            background-color: var(--el-fill-color-light);
            border-radius: 4px;
            margin-bottom: 8px;
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 13px;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            color: var(--el-text-color-regular);
          }
        }
      }

      .no-metadata {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        color: var(--el-text-color-secondary);

        .el-icon {
          font-size: 48px;
        }
      }
    }
  }
}
</style>
