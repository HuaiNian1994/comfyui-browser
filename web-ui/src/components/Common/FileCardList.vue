<template>
  <div class="file-card-list" :class="{ 'list-view': viewMode === 'list' }">
    <!-- 顶部工具栏 -->
    <div class="list-toolbar">
      <!-- 第一行: 操作和视图切换 -->
      <div class="toolbar-row primary-row">
        <div class="left-actions">
          <div class="header-slot">
            <slot name="header"></slot>
          </div>

          <!-- 管理模式按钮 -->
          <el-button v-if="hasBatchActions" :type="isManagementMode ? 'primary' : 'default'"
            @click="toggleManagementMode">
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
        </div>

        <div class="right-actions">

          <!-- 缩放滑块 (仅Grid模式) -->
          <div class="scale-slider" v-if="viewMode === 'grid'">
            <el-slider v-model="cardScale" :min="0.5" :max="3" :step="0.1" :show-tooltip="false" />
          </div>

          <el-button :loading="isReindexing" @click="handleReindex">
            <el-icon>
              <Refresh />
            </el-icon>
            {{ t('common.btn.refresh') }}
          </el-button>

          <!-- 视图切换 -->
          <el-button-group class="view-toggle">
            <el-button :type="viewMode === 'grid' ? 'primary' : 'default'" @click="viewMode = 'grid'">
              <el-icon>
                <Grid />
              </el-icon>
            </el-button>
            <el-button :type="viewMode === 'list' ? 'primary' : 'default'" @click="viewMode = 'list'">
              <el-icon>
                <Menu />
              </el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 第二行: 搜索栏 -->
      <div class="toolbar-row search-row" v-if="!isManagementMode">
        <div class="search-container">
          <el-select v-model="selectedTags" multiple collapse-tags collapse-tags-tooltip
            :placeholder="t('common.filterTags')" style="width: 200px; margin-right: 12px;" clearable class="tag-filter">
            <template #prefix>
              <el-icon>
                <Filter />
              </el-icon>
            </template>
            <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
          </el-select>

          <!-- 搜索输入框 + 维度选择 搜索框的输入搜索的是所下拉勾选的维度的取值 -->
          <el-input v-model="internalSearchQuery" :placeholder="t('common.searchPlaceholder')" clearable
            class="search-input full-width">
            <template #prepend>
               <el-select v-model="selectedSearchDimensions" multiple collapse-tags collapse-tags-tooltip
                :placeholder="t('common.searchDimensions')" class="dimension-select" style="width: 180px">
                <template #header>
                  <div class="select-header"
                    style="padding: 4px 12px; display: flex; justify-content: space-between; border-bottom: 1px solid var(--el-border-color-light);">
                    <el-button size="small" link @click="selectAllDimensions">{{ t('common.selectAll') }}</el-button>
                    <el-button size="small" link @click="invertDimensions">{{ t('common.invertSelect') }}</el-button>
                  </div>
                </template>
                <el-option v-for="dim in searchDimensionsOptions" :key="dim.value" :label="dim.label" :value="dim.value" />
              </el-select>
            </template>
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>

          <el-pagination v-if="pagination && filteredFiles.length > 0" v-model:current-page="currentPage"
            v-model:page-size="internalPageSize" :page-sizes="[20, 50, 100]" :total="filteredFiles.length"
            layout="prev, pager, next, sizes, jumper, ->, total" size="small" :pager-count="5"
            @current-change="handlePageChange" @size-change="handleSizeChange" />
        </div>
      </div>
    </div>

    <!-- 文件列表/网格 -->
    <div v-loading="loading || isBatchProcessing"
      :class="['files-container', viewMode === 'grid' ? 'files-grid' : 'files-list']"
      :style="viewMode === 'grid' ? { '--card-min-width': (200 * cardScale) + 'px', '--preview-height': (150 * cardScale) + 'px' } : {}">

      <!-- List View Header -->
      <div v-if="viewMode === 'list'" class="list-header">
        <div class="col-preview">Preview</div>
        <div class="col-name">Name</div>
        <div class="col-info">Info</div>
        <div class="col-meta">Date / Size</div>
        <div class="col-path">Path</div>
        <div class="col-tags">Tags</div>
        <div class="col-actions">Actions</div>
      </div>

      <div v-for="file in paginatedFiles" :key="file.path || file.name" class="file-item"
        :class="{ 'file-card': viewMode === 'grid', 'file-row': viewMode === 'list', 'is-selected': isSelected(file), 'is-management': isManagementMode }"
        @click="handleCardClick(file)">
        <!-- 选择遮罩 -->
        <div v-if="isManagementMode" class="selection-overlay">
          <el-checkbox :model-value="isSelected(file)" @click.stop="toggleSelection(file)" />
        </div>

        <!-- Grid View Content -->
        <template v-if="viewMode === 'grid'">
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

            <!-- 详细元数据展示 -->
            <div v-if="file.formatted_info" class="file-details">
              <el-tag v-if="file.formatted_info.width && file.formatted_info.height" size="small" type="info"
                effect="plain" class="detail-tag">
                {{ file.formatted_info.width }}x{{ file.formatted_info.height }}
              </el-tag>
              <el-tooltip v-if="file.formatted_info.models && file.formatted_info.models.length > 0"
                :content="file.formatted_info.models.join(', ')" placement="top">
                <el-tag size="small" type="success" effect="plain" class="detail-tag model-tag">
                  {{ file.formatted_info.models[0] }}
                </el-tag>
              </el-tooltip>
            </div>

            <p class="file-meta">{{ file.formattedDatetime }}</p>
            <p v-if="file.formattedSize" class="file-meta">{{ file.formattedSize }}</p>

            <!-- 标签展示 -->
            <div class="file-tags" @click.stop>
              <el-tag v-for="tag in file.tags" :key="tag" class="tag-item" closable size="small"
                @close="handleCloseTag(file, tag)">
                {{ tag }}
              </el-tag>
              <el-input v-if="inputVisibleMap[file.name]" ref="tagInputRef" v-model="inputValueMap[file.name]"
                class="input-new-tag" size="small" @keyup.enter="handleTagInputConfirm(file)"
                @blur="handleTagInputConfirm(file)" />
              <el-button v-else class="button-new-tag" size="small" :icon="Plus"
                @click="showTagInput(file)"></el-button>
            </div>
          </div>

          <!-- 操作按钮 (仅非管理模式显示) -->
          <div v-if="!isManagementMode" class="file-actions" @click.stop>
            <slot name="actions" :file="file">
              <!-- 默认无操作按钮,由父组件通过slot提供 -->
            </slot>
          </div>
        </template>

        <!-- List View Content -->
        <template v-else>
          <div class="col-preview">
            <el-image v-if="file.fileType === 'image'" :src="file.previewUrl" fit="cover" class="list-preview-img" lazy
              :preview-src-list="[file.previewUrl || '']" :preview-teleported="true" @click.stop />
            <video v-else-if="file.fileType === 'video'" :src="file.previewUrl" class="list-preview-video" />
            <el-icon v-else :size="32">
              <Folder v-if="file.fileType === 'dir'" />
              <Document v-else />
            </el-icon>
          </div>
          <div class="col-name" :title="file.name">{{ file.name }}</div>
          <div class="col-info">
            <div v-if="file.formatted_info?.models?.length" class="info-group">
              <span class="label">Models:</span>
              <span class="value">{{ file.formatted_info.models.join(', ') }}</span>
            </div>
            <div v-if="file.formatted_info?.loras?.length" class="info-group">
              <span class="label">LoRAs:</span>
              <span class="value">{{ file.formatted_info.loras.join(', ') }}</span>
            </div>
            <div v-if="file.formatted_info?.width" class="info-group">
              <span class="label">Res:</span>
              <span class="value">{{ file.formatted_info.width }}x{{ file.formatted_info.height }}</span>
            </div>
          </div>
          <div class="col-meta">
            <div>{{ file.formattedDatetime }}</div>
            <div v-if="file.formattedSize">{{ file.formattedSize }}</div>
          </div>
          <div class="col-path" :title="file.folder_path || file.path">{{ file.folder_path || file.path }}</div>
          <div class="col-tags" @click.stop>
            <el-tag v-for="tag in file.tags" :key="tag" class="tag-item" closable size="small"
              @close="handleCloseTag(file, tag)">
              {{ tag }}
            </el-tag>
            <el-input v-if="inputVisibleMap[file.name]" ref="tagInputRef" v-model="inputValueMap[file.name]"
              class="input-new-tag" size="small" @keyup.enter="handleTagInputConfirm(file)"
              @blur="handleTagInputConfirm(file)" />
            <el-button v-else class="button-new-tag" size="small" :icon="Plus" circle
              @click="showTagInput(file)"></el-button>
          </div>
          <div class="col-actions" @click.stop>
            <slot name="actions" :file="file"></slot>
          </div>
        </template>
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

    <!-- 底部工具栏 (依然保留底部页码选择，但精简分页器为纯信息或仅页码选择，此处用户要求是挪到上方，故移除或简化底部) -->
    <!-- 用户未明确说移除底部，但通常“挪到”意味着位置改变。我会暂时移除底部主要分页器，只保留 total 信息或者直接移除。 -->
    <!-- 考虑到用户习惯，底部保留 total 和 sizes 也是好的，但用户指令是 "分页器挪到搜索框上方"，所以我将上面放主要的分页控制。 -->
    <div class="bottom-toolbar">
      <span class="total-info" v-if="filteredFiles.length > 0">Total: {{ filteredFiles.length }}</span>
      <!-- 如果用户需要底部也能翻页，可以再放一个，但目前仅遵循挪动指令 -->
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType, ref, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Folder, Document, Search, ZoomIn, ZoomOut, Plus, Filter, Menu, Grid, Refresh } from '@element-plus/icons-vue'
import {
  ElMessage,
  ElInput,
  ElSelect,
  ElOption,
  ElTag,
  ElTooltip,
  ElButton,
  ElButtonGroup,
  ElSlider,
  ElPagination,
  ElImage,
  ElIcon,
  ElCheckbox,
  ElEmpty
} from 'element-plus'
import type { FileInfo, FolderType } from '@/types'
import { subscribeMetadata } from '@/api/metadata-subscription'
import ImagePreviewDialog from './ImagePreviewDialog/ImagePreviewDialog.vue'
import { addFileTag, removeFileTag, fetchAllTags, reindexFiles } from '@/api/files'

export default defineComponent({
  name: 'FileCardList',
  components: {
    Folder,
    Document,
    Search,
    ZoomIn,
    ZoomOut,
    Plus,
    Filter,
    Menu,
    Grid,
    Refresh,
    ImagePreviewDialog,
    ElInput,
    ElSelect,
    ElOption,
    ElTag,
    ElTooltip,
    ElButton,
    ElButtonGroup,
    ElSlider,
    ElPagination,
    ElImage,
    ElIcon,
    ElCheckbox,
    ElEmpty
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
  emits: ['file-click', 'page-change', 'refresh', 'update-file'],
  setup(props) {
    const { t } = useI18n()

    // Tag Input Refs
    const tagInputRef = ref<InstanceType<typeof ElInput>>()

    // Tag management state
    const inputVisibleMap = ref<Record<string, boolean>>({})
    const inputValueMap = ref<Record<string, string>>({})

    // Search & Filter state
    const allTags = ref<string[]>([])
    const selectedTags = ref<string[]>([])

    const loadTags = async () => {
      try {
        allTags.value = await fetchAllTags()
      } catch (e) {
        console.error("Failed to load tags", e)
      }
    }

    onMounted(() => {
      loadTags()
    })

    const showTagInput = (file: FileInfo) => {
      inputVisibleMap.value[file.name] = true
      nextTick(() => {
        tagInputRef.value?.input?.focus()
      })
    }

    const handleTagInputConfirm = async (file: FileInfo) => {
      const inputValue = inputValueMap.value[file.name]
      if (inputValue) {
        try {
          const targetFolderPath = file.folder_path || props.folderPath
          const { tags } = await addFileTag(props.folderType, file.name, inputValue, targetFolderPath)
          // Update local file data
          if (file.tags) {
            file.tags = tags
          } else {
            file.tags = tags
          }
          // Refresh global tag list if it's a new tag
          if (!allTags.value.includes(inputValue)) {
            allTags.value.push(inputValue)
            allTags.value.sort()
          }
          ElMessage.success(t('common.addSuccess'))
        } catch (error) {
          console.error('Failed to add tag:', error)
          ElMessage.error(t('common.addFailed'))
        }
      }
      inputVisibleMap.value[file.name] = false
      inputValueMap.value[file.name] = ''
    }

    const handleCloseTag = async (file: FileInfo, tag: string) => {
      try {
        const targetFolderPath = file.folder_path || props.folderPath
        const { tags } = await removeFileTag(props.folderType, file.name, tag, targetFolderPath)
        // Update local file data
        if (file.tags) {
          file.tags = tags
        }
        ElMessage.success(t('common.deleteSuccess'))
      } catch (error) {
        console.error('Failed to remove tag:', error)
        ElMessage.error(t('common.deleteFailed'))
      }
    }

    return {
      t,
      tagInputRef,
      inputVisibleMap,
      inputValueMap,
      allTags,
      selectedTags,
      showTagInput,
      handleTagInputConfirm,
      handleCloseTag,
      Plus
    }
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
      selectedFiles: new Set<string>(), // 存储选中文件的唯一标识
      isBatchProcessing: false,
      cardScale: 1,
      // 新增状态
      viewMode: 'grid' as 'grid' | 'list',
      selectedSearchDimensions: [] as string[],
      isReindexing: false,
      metadataSubscriptions: [] as Array<() => void>
    }
  },
  computed: {
    // 动态计算维度选项，支持国际化
    searchDimensionsOptions(): Array<{ label: string, value: string }> {
      return [
        { label: this.t('common.dimensions.name'), value: 'name' },
        { label: this.t('common.dimensions.date'), value: 'formattedDatetime' },
        { label: this.t('common.dimensions.size'), value: 'formattedSize' },
        { label: this.t('common.dimensions.models'), value: 'models' },
        { label: this.t('common.dimensions.loras'), value: 'loras' },
        { label: this.t('common.dimensions.tags'), value: 'tags' },
        { label: this.t('common.dimensions.path'), value: 'path' }
      ]
    },
    filteredFiles(): FileInfo[] {
      // 1. Tag Filtering
      let result = this.files
      if (this.selectedTags.length > 0) {
        result = result.filter(file => {
          if (!file.tags) return false
          // File must have ALL selected tags (AND logic)
          return this.selectedTags.every(tag => file.tags!.includes(tag))
        })
      }

      if (!this.internalSearchQuery.trim()) {
        return result
      }

      const terms = this.internalSearchQuery.trim().split(/\s+/)
      const includeTerms = terms.filter(t => !t.startsWith('-')).map(t => t.toLowerCase())
      const excludeTerms = terms.filter(t => t.startsWith('-') && t.length > 1).map(t => t.slice(1).toLowerCase())

      const checkFile = (file: FileInfo) => {
        // Gather values based on dimensions
        const valuesToCheck: string[] = []
        const dims = this.selectedSearchDimensions.length > 0 ? this.selectedSearchDimensions : this.searchDimensionsOptions.map(d => d.value)

        if (dims.includes('name') && file.name) valuesToCheck.push(file.name)
        if (dims.includes('formattedDatetime') && file.formattedDatetime) valuesToCheck.push(file.formattedDatetime)
        if (dims.includes('formattedSize') && file.formattedSize) valuesToCheck.push(file.formattedSize)
        if (dims.includes('path')) valuesToCheck.push(file.folder_path || file.path || '')

        if (file.formatted_info) {
          if (dims.includes('models') && file.formatted_info.models) valuesToCheck.push(...file.formatted_info.models)
          if (dims.includes('loras') && file.formatted_info.loras) valuesToCheck.push(...file.formatted_info.loras)
        }

        if (dims.includes('tags') && file.tags) valuesToCheck.push(...file.tags)

        const content = valuesToCheck.join(' ').toLowerCase()
        const hasAllIncludes = includeTerms.every(term => content.includes(term))
        const hasNoExcludes = excludeTerms.every(term => !content.includes(term))

        return hasAllIncludes && hasNoExcludes
      }

      return result.filter(checkFile)
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
      return this.filteredFiles.every(f => this.selectedFiles.has(this.getFileKey(f)))
    },
    selectedFilesArray(): FileInfo[] {
      const selectedKeys = this.selectedFiles
      return this.files.filter(f => selectedKeys.has(this.getFileKey(f)))
    },
    hasBatchActions(): boolean {
      return !!this.$slots['batch-actions']
    }
  },
  mounted() {
    this.scheduleMetadataWarmup()
  },
  beforeUnmount() {
    this.metadataSubscriptions.forEach(unsubscribe => unsubscribe())
  },
  watch: {
    paginatedFiles() {
      this.scheduleMetadataWarmup()
    },
    files() {
      this.handleFilesChange()
      // 文件列表变化时，清理不在列表中的选中项
      if (this.isManagementMode) {
        const currentKeys = new Set(this.files.map(f => this.getFileKey(f)))
        for (const key of this.selectedFiles) {
          if (!currentKeys.has(key)) {
            this.selectedFiles.delete(key)
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
      this.scheduleMetadataWarmup()
    },
    /**
     * 将缺失图片元数据的文件加入队列，分批异步补齐，避免首屏卡顿。
     */
    scheduleMetadataWarmup() {
      this.metadataSubscriptions.forEach(unsubscribe => unsubscribe())
      this.metadataSubscriptions = []
      this.paginatedFiles.forEach(file => {
        if (file.fileType !== 'image' || (file.formatted_info?.parser_version && !file.metadata_pending)) return
        const folderPath = file.folder_path ?? this.folderPath ?? ''
        this.metadataSubscriptions.push(subscribeMetadata(this.folderType as FolderType, file.name, folderPath, metadata => {
          if (metadata.formatted_info) file.formatted_info = metadata.formatted_info
          if (metadata.tags) file.tags = metadata.tags
          file.metadata_pending = metadata.metadata_pending ?? false
        }))
      })
    },
    getFileKey(file: FileInfo): string {
      if (file.hash) {
        return file.hash
      }
      if (file.folder_path) {
        return `${file.folder_path}/${file.name}`
      }
      return file.name
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
      this.currentPreviewIndex = this.previewableFiles.findIndex(f => this.getFileKey(f) === this.getFileKey(file))
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
      return this.selectedFiles.has(this.getFileKey(file))
    },
    toggleSelection(file: FileInfo) {
      const key = this.getFileKey(file)
      if (this.selectedFiles.has(key)) {
        this.selectedFiles.delete(key)
      } else {
        this.selectedFiles.add(key)
      }
    },
    handleSelectAll() {
      if (this.isAllSelected) {
        this.selectedFiles.clear()
      } else {
        this.filteredFiles.forEach(f => this.selectedFiles.add(this.getFileKey(f)))
      }
    },
    handleInvertSelect() {
      this.filteredFiles.forEach(f => {
        const key = this.getFileKey(f)
        if (this.selectedFiles.has(key)) {
          this.selectedFiles.delete(key)
        } else {
          this.selectedFiles.add(key)
        }
      })
    },
    clearSelection() {
      this.selectedFiles.clear()
      this.isManagementMode = false
    },
    // 维度选择方法
    selectAllDimensions() {
      this.selectedSearchDimensions = this.searchDimensionsOptions.map(d => d.value)
    },
    invertDimensions() {
      const all = this.searchDimensionsOptions.map(d => d.value)
      this.selectedSearchDimensions = all.filter(d => !this.selectedSearchDimensions.includes(d))
    },
    async handleReindex() {
      if (this.isReindexing) {
        return
      }
      this.isReindexing = true
      try {
        await reindexFiles(this.folderType as FolderType, this.folderPath || undefined)
        this.$emit('refresh')
        ElMessage.success(this.t('common.reindexSuccess'))
      } catch (error) {
        console.error('Reindex files failed:', error)
        ElMessage.error(this.t('common.reindexFailed'))
      } finally {
        this.isReindexing = false
      }
    }
  }
})
</script>

<style scoped lang="scss">
  .file-card-list {
    width: 100%;
    display: flex;
    flex-direction: column;
    min-height: 400px;
  }

  .list-toolbar {
    margin-bottom: 16px;
  }

  .toolbar-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 12px;

    &.primary-row {
      justify-content: space-between;
    }

    &.search-row {
      background-color: var(--el-fill-color-light);
      padding: 12px;
      border-radius: 8px;
    }
  }

  .left-actions,
  .right-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .left-actions {
    flex: 1 1 auto;
    min-width: 0;
  }

  .header-slot {
    flex: 0 1 60vw;
    max-width: 60vw;
    min-width: 0;
    width: 60vw;
  }

  .search-container {
    display: flex;
    width: 100%;
    gap: 12px;
  }

  .full-width {
    flex: 1;
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

  .files-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(var(--card-min-width, 200px), 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .files-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 24px;
  }

  .scale-slider {
    display: flex;
    align-items: center;
    width: 100px;
  }

  /* File Item Base */
  .file-item {
    background: var(--el-bg-color-page);
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    transition: all 0.2s;
    position: relative;

    &.is-selected {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }

    &.is-management {
      cursor: pointer;
    }
  }

  /* Grid View Specifics */
  .file-card {
    overflow: hidden;

    &:hover {
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }

    &.is-selected {
      box-shadow: 0 0 0 1px var(--el-color-primary);
    }

    .file-preview {
      width: 100%;
      height: var(--preview-height, 150px);
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--el-fill-color-light);
      cursor: pointer;
      overflow: hidden;
    }

    .file-info {
      padding: 12px;
    }

    .file-actions {
      padding: 0 12px 12px;
      display: flex;
      gap: 8px;
    }
  }

  /* List View Specifics */
  .list-header {
    display: flex;
    padding: 8px 16px;
    background-color: var(--el-fill-color);
    border-radius: 4px;
    margin-bottom: 8px;
    font-weight: 600;
    font-size: 13px;
    color: var(--el-text-color-regular);

    div {
      padding: 0 8px;
    }
  }

  .file-row {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    gap: 0; // Handled by column padding

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    .col-preview,
    .col-name,
    .col-info,
    .col-meta,
    .col-path,
    .col-tags,
    .col-actions {
      padding: 0 8px;
      overflow: hidden;
    }
  }

  /* Column Widths */
  .col-preview {
    width: 60px;
    display: flex;
    justify-content: center;
  }

  .col-name {
    width: 200px;
    font-weight: 500;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .col-info {
    flex: 1;
    font-size: 12px;
  }

  .col-meta {
    width: 140px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .col-path {
    width: 120px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .col-tags {
    width: 180px;
  }

  .col-actions {
    width: 120px;
    display: flex;
    gap: 4px;
    justify-content: flex-end;
  }

  .list-preview-img,
  .list-preview-video {
    width: 40px;
    height: 40px;
    border-radius: 4px;
    object-fit: cover;
    cursor: pointer;
  }

  .info-group {
    display: flex;
    gap: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;

    .label {
      color: var(--el-text-color-secondary);
    }

    .value {
      font-weight: 500;
    }
  }

  .selection-overlay {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    pointer-events: none;

    :deep(.el-checkbox) {
      pointer-events: auto;

      .el-checkbox__inner {
        background-color: white;
      }
    }
  }

  .file-row .selection-overlay {
    top: 50%;
    transform: translateY(-50%);
    left: 8px;
    // Adjust padding for first col if management mode
  }

  // Shift content if selection visible in list mode?
  // Actually overlay is absolute. In list mode, maybe put it in a separate small col or just overlap preview.

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

  .file-details {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 4px;
  }

  .detail-tag {
    height: 20px;
    padding: 0 4px;
    font-size: 10px;
  }

  .model-tag {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .file-tags {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .tag-item {
    margin-right: 0;
  }

  .button-new-tag {
    height: 24px;
    width: 24px;
    padding: 0;
  }

  .input-new-tag {
    width: 90px;
    height: 24px;
    font-size: 12px;
  }

  .bottom-toolbar {
    display: flex;
    justify-content: flex-end;
    margin-top: auto;
    padding-top: 16px;

    .total-info {
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }
</style>