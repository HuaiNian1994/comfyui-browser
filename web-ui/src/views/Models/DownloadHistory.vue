<template>
  <div class="download-history">
    <div class="toolbar">
      <el-button type="primary" plain @click="refreshHistory">{{ t('modelsTab.refresh') }}</el-button>
      <div class="auto-refresh">
        <span>{{ t('modelsTab.autoRefresh') }}</span>
        <el-switch v-model="autoRefresh" />
      </div>
    </div>

    <div class="history-list">
      <el-empty v-if="downloads.length === 0" :description="t('modelsTab.noDownloads')" />

      <div v-for="dl in downloads" :key="dl.uuid" class="history-item">
        <div class="item-header">
          <span class="item-title">{{ dl.filename || dl.uuid }}</span>
          <span class="item-status" :class="getStatusClass(dl)">{{ dl.result || t('modelsTab.downloading') }}</span>
        </div>

        <div class="item-meta">
          <p>{{ t('modelsTab.createdAt') }}: {{ dl.formattedCreatedAt }}</p>
          <p>{{ t('modelsTab.updatedAt') }}: {{ dl.formattedUpdatedAt }}</p>
          <p>{{ t('modelsTab.url') }}: {{ dl.download_url }}</p>
          <p>{{ t('modelsTab.saveIn') }}: {{ dl.save_in }}</p>
        </div>

        <div v-if="dl.total_size !== 0" class="item-progress">
          <div class="progress-info">
            <span>{{ dl.formattedDownloadedSize }} / {{ dl.formattedTotalSize }}</span>
            <span>{{ dl.percentStr }}</span>
          </div>
          <el-progress :percentage="calculatePercentage(dl)" :status="getProgressStatus(dl)" />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { fetchDownloads } from '@/api/models'
import type { DownloadLog } from '@/api/models'
import { formatFileSize } from '@/utils'

export default defineComponent({
  name: 'DownloadHistory',
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      downloads: [] as DownloadLog[],
      autoRefresh: true,
      refreshInterval: null as number | null
    }
  },
  watch: {
    autoRefresh(val) {
      if (val) {
        this.startAutoRefresh()
      } else {
        this.stopAutoRefresh()
      }
    }
  },
  mounted() {
    this.refreshHistory()
    if (this.autoRefresh) {
      this.startAutoRefresh()
    }
  },
  beforeUnmount() {
    this.stopAutoRefresh()
  },
  methods: {
    async refreshHistory() {
      try {
        const response = await fetchDownloads()
        const timeFormat = 'YYYY-MM-DD HH:mm:ss'

        this.downloads = response.download_logs.map(dl => {
          const percent = dl.total_size > 0 ? Math.floor((dl.downloaded_size / dl.total_size) * 100) : 0

          return {
            ...dl,
            formattedCreatedAt: dayjs.unix(dl.created_at).format(timeFormat),
            formattedUpdatedAt: dayjs.unix(dl.updated_at).format(timeFormat),
            percentStr: `${percent}%`,
            formattedDownloadedSize: formatFileSize(dl.downloaded_size),
            formattedTotalSize: formatFileSize(dl.total_size)
          }
        })
      } catch (error) {
        console.error('Failed to refresh history:', error)
        // You might want to show error message here if needed, but console error was original
      }
    },
    startAutoRefresh() {
      if (this.refreshInterval) return
      this.refreshInterval = window.setInterval(this.refreshHistory, 1000)
    },
    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },
    calculatePercentage(dl: DownloadLog) {
      if (dl.total_size === 0) return 0
      return Math.floor((dl.downloaded_size / dl.total_size) * 100)
    },
    getProgressStatus(dl: DownloadLog) {
      if (dl.result === 'Success') return 'success'
      if (dl.result === 'Failed') return 'exception'
      return ''
    },
    getStatusClass(dl: DownloadLog) {
      if (dl.result === 'Success') return 'text-success'
      if (dl.result === 'Failed') return 'text-danger'
      return 'text-primary'
    }
  }
})
</script>

<style scoped lang="scss">
  .download-history {
    padding: 16px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .auto-refresh {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }

  .history-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .history-item {
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    padding: 16px;
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .item-title {
    font-weight: bold;
    font-size: 16px;
  }

  .item-status {
    font-size: 14px;
    font-weight: bold;
  }

  .text-success {
    color: var(--el-color-success);
  }

  .text-danger {
    color: var(--el-color-danger);
  }

  .text-primary {
    color: var(--el-color-primary);
  }

  .item-meta {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px;
    margin-bottom: 12px;

    p {
      margin: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .item-progress {
    .progress-info {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      margin-bottom: 4px;
    }
  }
</style>