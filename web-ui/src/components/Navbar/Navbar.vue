<template>
  <div class="navbar">
    <el-menu :default-active="activeTab" mode="horizontal" @select="handleSelect" class="navbar-menu">
      <el-menu-item index="files">
        <el-icon>
          <Picture />
        </el-icon>
        <span>{{ t('navbar.outputs') }}</span>
      </el-menu-item>
      <el-menu-item index="collections">
        <el-icon>
          <Collection />
        </el-icon>
        <span>{{ t('navbar.saves') }}</span>
      </el-menu-item>
      <el-menu-item index="sources">
        <el-icon>
          <Promotion />
        </el-icon>
        <span>{{ t('navbar.sources') }}</span>
      </el-menu-item>
      <el-menu-item index="models">
        <el-icon>
          <Box />
        </el-icon>
        <span>{{ t('navbar.models') }}</span>
      </el-menu-item>

      <div class="navbar-right">
        <!-- 主题切换 -->
        <el-switch
          v-model="isDark"
          inline-prompt
          :active-icon="Moon"
          :inactive-icon="Sunny"
          @change="toggleTheme"
          style="margin-right: 16px"
        />

        <!-- 语言切换 -->
        <el-dropdown @command="handleLangChange" class="lang-dropdown">
          <el-button link text="plain">
            {{ currentLangLabel }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="en-US" :class="{ 'is-active': locale === 'en-US' }">
                English
              </el-dropdown-item>
              <el-dropdown-item command="zh-CN" :class="{ 'is-active': locale === 'zh-CN' }">
                中文
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- GitHub Stars -->
        <a href="https://github.com/HuaiNian1994/comfyui-browser" target="_blank" class="github-link">
          <img src="https://img.shields.io/github/stars/HuaiNian1994/comfyui-browser?style=social" alt="GitHub stars" />
        </a>

      </div>
    </el-menu>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Picture, Collection, Promotion, Box, MoreFilled, Sunny, Moon } from '@element-plus/icons-vue'
import { setLocale } from '@/i18n'

export default defineComponent({
  name: 'Navbar',
  components: {
    Picture,
    Collection,
    Promotion,
    Box,
    MoreFilled
  },
  props: {
    activeTab: {
      type: String,
      required: true
    }
  },
  emits: ['update:active-tab'],
  setup() {
    const { t, locale } = useI18n()
    const isDark = ref(false)

    const toggleTheme = (val: boolean) => {
      if (val) {
        document.documentElement.classList.add('dark')
        localStorage.setItem('theme', 'dark')
      } else {
        document.documentElement.classList.remove('dark')
        localStorage.setItem('theme', 'light')
      }
    }

    onMounted(() => {
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        isDark.value = true
        document.documentElement.classList.add('dark')
      } else {
        isDark.value = false
        document.documentElement.classList.remove('dark')
      }
    })

    const currentLangLabel = computed(() => {
      return locale.value === 'zh-CN' ? '中文' : 'En'
    })

    return {
      t,
      locale,
      currentLangLabel,
      isDark,
      toggleTheme,
      Sunny,
      Moon
    }
  },
  methods: {
    handleSelect(key: string) {
      this.$emit('update:active-tab', key)
    },
    handleLangChange(lang: string) {
      setLocale(lang)
    }
  }
})
</script>

<style scoped lang="scss">


  .navbar-menu {
    position: relative;
    display: flex;
    align-items: center;
  }

  .navbar-right {
    position: absolute;
    right: 0;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 20px;
  }






</style>
