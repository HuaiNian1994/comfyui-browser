<template>
  <el-dialog v-model="visible" :fullscreen="true" :show-close="true" class="image-preview-dialog" @close="handleClose">
    <div :class="['preview-container', layoutClass]">
      <div class="image-section">
        <img :src="imageUrl" @load="onImageLoad" class="preview-image" alt="Preview" />
      </div>
      <div class="prompts-section">
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span>{{ t('sourcesTab.imagePreview.loadingMetadata') }}</span>
        </div>
        <div v-else-if="!metadata.has_metadata" class="no-metadata">
          <el-icon>
            <WarningFilled />
          </el-icon>
          <span>{{ t('sourcesTab.imagePreview.noMetadata') }}</span>
        </div>
        <div v-else class="prompts-content">
          <!-- 正向提示词 -->
          <div class="prompt-block">
            <h3>{{ t('sourcesTab.imagePreview.positivePrompt') }}</h3>
            <div class="prompt-text">{{ metadata.positive || t('sourcesTab.imagePreview.noPrompt') }}</div>
            <el-button v-if="metadata.positive" size="small" @click="copyPrompt(metadata.positive)">
              <el-icon>
                <CopyDocument />
              </el-icon>
              {{ t('sourcesTab.imagePreview.copyPrompt') }}
            </el-button>
          </div>

          <!-- 反向提示词 -->
          <div class="prompt-block">
            <h3>{{ t('sourcesTab.imagePreview.negativePrompt') }}</h3>
            <div class="prompt-text">{{ metadata.negative || t('sourcesTab.imagePreview.noPrompt') }}</div>
            <el-button v-if="metadata.negative" size="small" @click="copyPrompt(metadata.negative)">
              <el-icon>
                <CopyDocument />
              </el-icon>
              {{ t('sourcesTab.imagePreview.copyPrompt') }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled, CopyDocument } from '@element-plus/icons-vue'
import { fetchImageMetadata } from '@/api/files'
import type { FolderType, ImageMetadata } from '@/types'

export default defineComponent({
  name: 'ImagePreviewDialog',
  components: {
    Loading,
    WarningFilled,
    CopyDocument
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    imageUrl: {
      type: String,
      default: ''
    },
    imageName: {
      type: String,
      default: ''
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
      layoutClass: 'layout-vertical',
      loading: false,
      metadata: {
        positive: '',
        negative: '',
        has_metadata: false
      } as ImageMetadata
    }
  },
  computed: {
    visible: {
      get(): boolean {
        return this.modelValue
      },
      set(value: boolean) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  watch: {
    modelValue(newVal: boolean) {
      if (newVal && this.imageName) {
        this.loadMetadata()
      }
    }
  },
  methods: {
    onImageLoad(event: Event) {
      const img = event.target as HTMLImageElement
      const aspectRatio = img.naturalHeight / img.naturalWidth

      // 高比宽长(竖图):左右布局,其他:上下布局
      this.layoutClass = aspectRatio > 1 ? 'layout-horizontal' : 'layout-vertical'
    },

    async loadMetadata() {
      if (!this.imageName) return

      this.loading = true
      try {
        this.metadata = await fetchImageMetadata(
          this.folderType,
          this.imageName,
          this.folderPath
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
        ElMessage.success(this.t('sourcesTab.imagePreview.copySuccess'))
      } catch (error) {
        console.error('Failed to copy:', error)
        ElMessage.error(this.t('sourcesTab.imagePreview.copyFailed'))
      }
    },

    handleClose() {
      this.visible = false
      // 重置状态
      this.metadata = {
        positive: '',
        negative: '',
        has_metadata: false
      }
      this.layoutClass = 'layout-vertical'
    }
  }
})
</script>

<style scoped lang="scss">
  .image-preview-dialog {
    :deep(.el-dialog__body) {
      padding: 0;
      height: 100%;
    }
  }

  .preview-container {
    display: flex;
    height: 100vh;
    background-color: var(--el-bg-color-page);

    &.layout-horizontal {
      flex-direction: row;

      .image-section {
        flex: 1;
        max-width: 60%;
      }

      .prompts-section {
        flex: 1;
        max-width: 40%;
      }
    }

    &.layout-vertical {
      flex-direction: column;

      .image-section {
        flex: 1;
        max-height: 60%;
      }

      .prompts-section {
        flex: 1;
        max-height: 40%;
      }
    }
  }

  .image-section {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #000;
    padding: 20px;

    .preview-image {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
  }

  .prompts-section {
    display: flex;
    flex-direction: column;
    padding: 24px;
    overflow-y: auto;
    background-color: var(--el-bg-color);
  }

  .loading-container,
  .no-metadata {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 100%;
    color: var(--el-text-color-secondary);

    .el-icon {
      font-size: 48px;
    }
  }

  .prompts-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .prompt-block {
    h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .prompt-text {
      padding: 12px;
      background-color: var(--el-fill-color-light);
      border-radius: 4px;
      margin-bottom: 12px;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.6;
      max-height: 300px;
      overflow-y: auto;
    }
  }
</style>
