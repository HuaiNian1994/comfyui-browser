<template>
  <el-config-provider :locale="elLocale">
    <div class="app-container">
      <Navbar :active-tab="activeTab" @update:active-tab="handleTabChange" />
      
      <div class="content-container">
        <keep-alive>
          <component :is="currentTabComponent" />
        </keep-alive>
      </div>
    </div>
  </el-config-provider>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElConfigProvider } from 'element-plus'
// @ts-ignore
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
// @ts-ignore
import en from 'element-plus/dist/locale/en.mjs'
import Navbar from './components/Navbar/Navbar.vue'
import FilesTab from './components/Files/FilesTab.vue'
import CollectionsTab from './components/Collections/CollectionsTab.vue'
import SourcesTab from './components/Sources/SourcesTab.vue'
import ModelsTab from './components/Models/ModelsTab.vue'

export default defineComponent({
  name: 'App',
  components: {
    ElConfigProvider,
    Navbar,
    FilesTab,
    CollectionsTab,
    SourcesTab,
    ModelsTab
  },
  setup() {
    const { locale } = useI18n()
    
    const elLocale = computed(() => {
      return locale.value === 'zh-CN' ? zhCn : en
    })

    return {
      elLocale
    }
  },
  data() {
    return {
      activeTab: 'files'
    }
  },
  computed: {
    currentTabComponent(): string {
      switch (this.activeTab) {
        case 'files':
          return 'FilesTab'
        case 'collections':
          return 'CollectionsTab'
        case 'sources':
          return 'SourcesTab'
        case 'models':
          return 'ModelsTab'
        default:
          return 'FilesTab'
      }
    }
  },
  methods: {
    handleTabChange(tab: string) {
      this.activeTab = tab
    }
  }
})
</script>

<style scoped lang="scss">
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.content-container {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
</style>
