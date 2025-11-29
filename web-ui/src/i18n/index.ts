import { createI18n } from 'vue-i18n'
import enUS from './en-US.json'
import zhCN from './zh-CN.json'

const LANG_KEY = 'lang'
const DEFAULT_LOCALE = 'en-US'

// 获取初始语言
function getInitialLocale(): string {
  // 1. 先检查 localStorage
  const savedLang = localStorage.getItem(LANG_KEY)
  if (savedLang) {
    return savedLang
  }

  // 2. 使用浏览器语言
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) {
    return 'zh-CN'
  }

  return DEFAULT_LOCALE
}

const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: {
    'en-US': enUS,
    'zh-CN': zhCN
  },
  missingWarn: false,
  fallbackWarn: false
})

// 监听语言变化，保存到 localStorage
export function setLocale(locale: string) {
  i18n.global.locale.value = locale as 'en-US' | 'zh-CN'
  localStorage.setItem(LANG_KEY, locale)
}

export default i18n
