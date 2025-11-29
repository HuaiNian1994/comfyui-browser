<template>
  <div class="models-tab">
    <div class="sidebar">
      <div class="menu-list">
        <div class="menu-item" :class="{ active: activeTab === 'downloadNewModel' }"
          @click="activeTab = 'downloadNewModel'">
          {{ t('modelsTab.downloadNewModel') }}
        </div>
        <div class="menu-item" :class="{ active: activeTab === 'downloadHistory' }"
          @click="activeTab = 'downloadHistory'">
          {{ t('modelsTab.downloadHistory') }}
        </div>
      </div>
    </div>

    <div class="content">
      <keep-alive>
        <component :is="activeComponent" @download-started="handleDownloadStarted" />
      </keep-alive>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import NewDownload from './NewDownload.vue'
import DownloadHistory from './DownloadHistory.vue'

export default defineComponent({
  name: 'ModelsTab',
  components: {
    NewDownload,
    DownloadHistory
  },
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      activeTab: 'downloadNewModel'
    }
  },
  computed: {
    activeComponent(): string {
      return this.activeTab === 'downloadNewModel' ? 'NewDownload' : 'DownloadHistory'
    }
  },
  methods: {
    handleDownloadStarted() {
      this.activeTab = 'downloadHistory'
    }
  }
})
</script>

<style scoped lang="scss">
  .models-tab {
    display: flex;
    height: 100%;
    overflow: hidden;
  }

  .sidebar {
    width: 200px;
    border-right: 1px solid var(--el-border-color);
    background-color: var(--el-bg-color-page);
    flex-shrink: 0;
  }

  .menu-list {
    padding: 8px 0;
  }

  .menu-item {
    padding: 12px 20px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    &.active {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-right: 3px solid var(--el-color-primary);
    }
  }

  .content {
    flex: 1;
    overflow: hidden;
    background-color: var(--el-bg-color);
  }
</style>