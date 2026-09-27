<template>
  <div v-if="modelValue" class="image-preview-wrapper">
    <el-image-viewer :url-list="previewUrls" :initial-index="initialIndex" @close="closePreview" @switch="switchPreview" />
    <aside class="preview-sidebar" @click.stop>
      <header class="sidebar-header">
        <div class="file-basic-info">
          <h3 class="file-name">{{ currentFile?.name || t('imagePreview.metadata') }}</h3>
          <p v-if="currentFile" class="file-facts">
            <span>{{ currentFile.formattedDatetime }}</span><span>{{ currentFile.formattedSize }}</span>
            <span v-if="formattedInfo?.width">{{ formattedInfo.width }} × {{ formattedInfo.height }} {{ formattedInfo.image_format }}</span>
            <el-tooltip v-for="item in timingItems" :key="item.id" :content="t(`metadata.timing.tips.${item.id}`)" placement="top" :z-index="4000" :show-after="250" popper-class="metadata-help-tooltip">
              <span class="timing-value" tabindex="0">{{ t(`metadata.timing.${item.id}`) }} {{ formatTiming(item) }}</span>
            </el-tooltip>
          </p>
        </div>
        <div class="file-actions">
          <slot v-if="currentFile" name="actions" :file="currentFile" />
          <el-button link :aria-label="t('metadata.close')" @click="closePreview"><el-icon><Close /></el-icon></el-button>
        </div>
      </header>
      <div class="metadata-content" :aria-busy="isLoading || metadata.metadata_pending">
        <div v-if="isLoading || metadata.index_status !== 'complete' || !['complete', 'partial'].includes(formattedInfo?.parse_status || '')" class="status-bar" role="status">
          <span>{{ statusText }}</span>
          <el-button v-if="metadata.index_status === 'failed'" size="small" @click="subscribeToCurrentFile(true)">{{ t('metadata.retry') }}</el-button>
        </div>
        <template v-if="formattedInfo?.branches?.length">
          <details v-for="section in metadataSections" :key="`${currentFile?.name}-${section.id}`" class="branch" open>
            <summary>{{ t(section.shared ? 'metadata.sharedStages' : 'metadata.branch') }} {{ section.branchIds.map(id => '#' + id).join('、') }}</summary>
            <p v-if="section.sharedStageIds.length" class="dependency">{{ t('metadata.usesSharedStages') }} {{ section.sharedStageIds.map(id => '#' + id).join('、') }}</p>
            <details v-for="stage in section.stages" :key="stage.id" class="stage" open>
              <summary><span>{{ t(`metadata.stageKinds.${stage.kind}`) }} #{{ stage.id }}</span><small>{{ stage.class_type }}</small><small v-if="stage.depends_on.length" class="dependency"> · {{ t('metadata.dependencies') }}: {{ stage.depends_on.map(id => '#' + id).join(', ') }}</small></summary>
              <MetadataProperties :key="`${currentFile?.name}-${stage.id}`" :properties="stage.properties" />
            </details>
          </details>
        </template>
        <details v-if="formattedInfo?.unassigned?.length" class="branch">
          <summary>{{ t('metadata.unassigned') }}</summary>
          <MetadataProperties :properties="formattedInfo.unassigned" />
        </details>
        <details v-if="formattedInfo?.diagnostics?.length" class="branch">
          <summary>{{ t('metadata.diagnostics') }} ({{ formattedInfo.diagnostics.length }})</summary>
          <p v-for="(diagnostic, index) in formattedInfo.diagnostics" :key="index" class="diagnostic">
            #{{ diagnostic.node_id }} {{ diagnostic.class_type }} · {{ diagnostic.field }}<br />
            {{ t(`metadata.reasons.${diagnostic.code}`) }} <span v-if="diagnostic.detail">({{ diagnostic.detail }})</span>
          </p>
        </details>
        <p v-if="metadata.index_status === 'complete' && !metadata.has_metadata" class="empty-state">{{ t('metadata.noGraph') }}</p>
      </div>
    </aside>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { ElImageViewer } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import i18n from '@/i18n'
import { subscribeMetadata } from '@/api/metadata-subscription'
import type { FolderType, ImageMetadata, FileInfo, FormattedInfo } from '@/types'
import MetadataProperties from './components/MetadataProperties.vue'
import { formatDuration, timingValues } from './utils/timing-format'
import { buildMetadataSections, type MetadataSection } from './utils/metadata-sections'

export default defineComponent({
  name: 'ImagePreviewDialog',
  components: { ElImageViewer, Close, MetadataProperties },
  props: {
    modelValue: { type: Boolean, required: true },
    previewFileList: { type: Array as PropType<FileInfo[]>, default: () => [] },
    initialIndex: { type: Number, default: 0 },
    folderType: { type: String as PropType<FolderType>, default: 'sources' },
    folderPath: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      currentIndex: this.initialIndex,
      isLoading: false,
      unsubscribe: null as (() => void) | null,
      requestGeneration: 0,
      metadata: { positive: '', negative: '', has_metadata: false } as ImageMetadata,
    }
  },
  computed: {
    timingItems(): Array<{ id: string; value: number }> { return timingValues(this.formattedInfo?.generation_timing) },
    metadataSections(): MetadataSection[] { return buildMetadataSections(this.formattedInfo?.branches || [], this.formattedInfo?.stages || []) },
    previewUrls(): string[] { return this.previewFileList.map(file => file.previewUrl || '') },
    currentFile(): FileInfo | undefined { return this.previewFileList[this.currentIndex] },
    formattedInfo(): FormattedInfo | undefined { return this.metadata.formatted_info || this.currentFile?.formatted_info },
    statusText(): string {
      if (this.isLoading) return this.t('metadata.status.loading')
      if (this.metadata.index_status && this.metadata.index_status !== 'complete') return this.t(`metadata.status.${this.metadata.index_status}`)
      return this.t(`metadata.status.${this.formattedInfo?.parse_status || 'missing'}`)
    },
  },
  watch: {
    modelValue(value: boolean) {
      if (value) { this.currentIndex = this.initialIndex; this.subscribeToCurrentFile() }
      else this.stopSubscription()
    },
    initialIndex(value: number) {
      if (this.modelValue && value !== this.currentIndex) { this.currentIndex = value; this.subscribeToCurrentFile() }
    },
    currentFile(value, previous) {
      if (this.modelValue && (value?.name !== previous?.name || value?.folder_path !== previous?.folder_path)) this.subscribeToCurrentFile()
    },
  },
  mounted() { if (this.modelValue) this.subscribeToCurrentFile() },
  beforeUnmount() { this.stopSubscription() },
  methods: {
    formatTiming(item: { id: string; value: number }): string {
      return item.id === 'average'
        ? `${item.value > 0 && item.value < 10 ? '<0.01' : Number((item.value / 1000).toFixed(2))} s/it`
        : formatDuration(item.value, this.t('metadata.timing.seconds'), this.t('metadata.timing.minutes'))
    },
    t(key: string) { return i18n.global.t(key) },
    stopSubscription() { this.requestGeneration += 1; this.unsubscribe?.(); this.unsubscribe = null },
    closePreview() { this.stopSubscription(); this.$emit('update:modelValue', false) },
    switchPreview(index: number) { this.currentIndex = index },
    subscribeToCurrentFile(refresh = false) {
      this.stopSubscription()
      const file = this.currentFile
      this.metadata = { positive: '', negative: '', has_metadata: false }
      if (!file) { this.isLoading = false; return }
      this.isLoading = true
      const generation = this.requestGeneration
      this.unsubscribe = subscribeMetadata(this.folderType, file.name, file.folder_path ?? this.folderPath, result => {
        if (generation !== this.requestGeneration) return
        this.metadata = result
        this.isLoading = false
      }, refresh)
    },

  },
})
</script>

<style scoped>
.image-preview-wrapper { position: relative; z-index: 2000; --preview-sidebar-width: min(740px, 56vw); }
.image-preview-wrapper :deep(.el-image-viewer__wrapper) { right: var(--preview-sidebar-width); }
.preview-sidebar { position: fixed; top: 0; right: 0; bottom: 0; width: var(--preview-sidebar-width); background: var(--el-bg-color); color: var(--el-text-color-primary); box-shadow: -2px 0 12px #0002; z-index: 3000; display: flex; flex-direction: column; }
.sidebar-header { padding: 8px 12px; border-bottom: 1px solid var(--el-border-color); display: flex; align-items: center; gap: 12px; }
.file-basic-info { min-width: 0; flex: 1; }
.file-name { font-size: 13px; font-weight: 600; margin: 0; overflow-wrap: anywhere; line-height: 1.4; }
.timing-value { cursor: help; white-space: nowrap; }
.file-facts { display: flex; flex-wrap: wrap; gap: 2px 12px; margin: 3px 0 0; font-size: 11px; color: var(--el-text-color-secondary); }
.file-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }
.file-actions :deep(.el-button) { margin-left: 0; }
.metadata-content { flex: 1; min-height: 0; overflow: auto; padding: 8px 12px; }
.status-bar { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--el-text-color-secondary); margin-bottom: 8px; }
.branch { margin-bottom: 8px; }
summary { cursor: pointer; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }
.stage { margin: 5px 0; padding: 5px 0; border-top: 1px solid var(--el-border-color-light); }
.stage summary small { display: inline; margin-left: 8px; font-weight: normal; color: var(--el-text-color-secondary); }
.dependency, .diagnostic, .empty-state { font-size: 12px; color: var(--el-text-color-secondary); line-height: 1.6; overflow-wrap: anywhere; }
@media (max-width: 900px) { .image-preview-wrapper { --preview-sidebar-width: min(450px, 70vw); } }
</style>
