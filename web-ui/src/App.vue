<template>
  <div class="app-container">
    <Navbar :active-tab="activeTab" @update:active-tab="handleTabChange" />
    
    <div class="content-container">
      <keep-alive>
        <component :is="currentTabComponent" />
      </keep-alive>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import Navbar from './components/Navbar/Navbar.vue'
import FilesTab from './views/Files/FilesTab.vue'
import CollectionsTab from './views/Collections/CollectionsTab.vue'
import SourcesTab from './views/Sources/SourcesTab.vue'
import ModelsTab from './views/Models/ModelsTab.vue'

export default defineComponent({
  name: 'App',
  components: {
    Navbar,
    FilesTab,
    CollectionsTab,
    SourcesTab,
    ModelsTab
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
