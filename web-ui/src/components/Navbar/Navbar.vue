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
        <!-- 语言切换 -->
        <el-dropdown @command="handleLangChange" class="lang-dropdown">
          <el-button text>
            <el-icon>
              <MoreFilled />
            </el-icon>
            {{ currentLangLabel }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="en-US" :class="{ 'is-active': locale === 'en-US' }">
                En
              </el-dropdown-item>
              <el-dropdown-item command="zh-CN" :class="{ 'is-active': locale === 'zh-CN' }">
                中文
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- GitHub Stars -->
        <a href="https://github.com/talesofai/comfyui-browser" target="_blank" class="github-link">
          <img src="https://img.shields.io/github/stars/talesofai/comfyui-browser?style=social" alt="GitHub stars" />
        </a>

        <!-- Discord -->
        <a href="https://discord.gg/f49R9dTKwM" target="_blank" class="discord-link">
          <svg class="discord-icon" viewBox="0 -28.5 256 256" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M216.856339,16.5966031 C200.285002,8.84328665 182.566144,3.2084988 164.041564,0 C161.766523,4.11318106 159.108624,9.64549908 157.276099,14.0464379 C137.583995,11.0849896 118.072967,11.0849896 98.7430163,14.0464379 C96.9108417,9.64549908 94.1925838,4.11318106 91.8971895,0 C73.3526068,3.2084988 55.6133949,8.86399117 39.0420583,16.6376612 C5.61752293,67.146514 -3.4433191,116.400813 1.08711069,164.955721 C23.2560196,181.510915 44.7403634,191.567697 65.8621325,198.148576 C71.0772151,190.971126 75.7283628,183.341335 79.7352139,175.300261 C72.104019,172.400575 64.7949724,168.822202 57.8887866,164.667963 C59.7209612,163.310589 61.5131304,161.891452 63.2445898,160.431257 C105.36741,180.133187 151.134928,180.133187 192.754523,160.431257 C194.506336,161.891452 196.298154,163.310589 198.110326,164.667963 C191.183787,168.842556 183.854737,172.420929 176.223542,175.320965 C180.230393,183.341335 184.861538,190.991831 190.096624,198.16893 C211.238746,191.588051 232.743023,181.531619 254.911949,164.955721 C260.227747,108.668201 245.831087,59.8662432 216.856339,16.5966031 Z M85.4738752,135.09489 C72.8290281,135.09489 62.4592217,123.290155 62.4592217,108.914901 C62.4592217,94.5396472 72.607595,82.7145587 85.4738752,82.7145587 C98.3405064,82.7145587 108.709962,94.5189427 108.488529,108.914901 C108.508531,123.290155 98.3405064,135.09489 85.4738752,135.09489 Z M170.525237,135.09489 C157.88039,135.09489 147.510584,123.290155 147.510584,108.914901 C147.510584,94.5396472 157.658606,82.7145587 170.525237,82.7145587 C183.391518,82.7145587 193.761324,94.5189427 193.539891,108.914901 C193.539891,123.290155 183.391518,135.09489 170.525237,135.09489 Z"
              fill="#5764f2" />
          </svg>
        </a>
      </div>
    </el-menu>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Picture, Collection, Promotion, Box, MoreFilled } from '@element-plus/icons-vue'
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

    const currentLangLabel = computed(() => {
      return locale.value === 'zh-CN' ? '中文' : 'En'
    })

    return {
      t,
      locale,
      currentLangLabel
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
  .navbar {
    margin-bottom: 10px;
  }

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

  .lang-dropdown {
    :deep(.el-button) {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .github-link,
  .discord-link {
    display: flex;
    align-items: center;
    text-decoration: none;

    img {
      height: 20px;
    }
  }

  .discord-icon {
    width: 24px;
    height: 24px;
    opacity: 0.6;
    transition: opacity 0.3s;

    &:hover {
      opacity: 1;
    }
  }

  :deep(.el-dropdown-menu__item.is-active) {
    color: var(--el-color-primary);
    font-weight: bold;
  }
</style>
