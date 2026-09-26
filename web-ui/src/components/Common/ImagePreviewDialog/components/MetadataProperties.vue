<template>
  <div class="property-columns" :class="{ single: propertyColumns.length === 1 }">
  <div v-for="column in propertyColumns" :key="column.id" class="property-column">
  <section v-for="group in column.groups" :key="group.id" class="property-group">
    <h5>{{ t(`metadata.groups.${group.id}`) }}</h5>
    <div class="property-grid">
      <div v-for="(property, index) in group.properties" :key="`${property.id}-${index}`" class="property" :class="{ wide: isWide(property) }">
        <div class="property-label">
          <el-tooltip :content="propertyTip(property)" placement="top" :z-index="4000" :show-after="250" popper-class="metadata-help-tooltip">
            <span class="label-help" tabindex="0">{{ propertyLabel(property) }}</span>
          </el-tooltip>
          <span v-if="channelLabel(property)" class="channel">{{ channelLabel(property) }}</span>
          <button v-if="property.state !== 'unknown'" class="copy-button" type="button" :title="t('imagePreview.copyPrompt')" :aria-label="t('imagePreview.copyPrompt') + ': ' + propertyLabel(property)" @click="copyValue(property.value, `${group.id}-${index}`)">{{ copiedKey === `${group.id}-${index}` ? '✓' : '⧉' }}</button>
        </div>
        <div class="property-value">{{ formatValue(property.value, property.state) }}</div>
        <p v-if="property.reason" class="reason">{{ t(`metadata.reasons.${property.reason}`) }}</p>
      </div>
    </div>

  </section>
  </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import i18n from '@/i18n'
import type { MetadataProperty } from '@/types'

export default defineComponent({
  name: 'MetadataProperties',
  props: { properties: { type: Array as PropType<MetadataProperty[]>, required: true } },
  data() { return { copiedKey: '' } },
  computed: {
    propertyColumns(): Array<{ id: string; groups: Array<{ id: string; properties: MetadataProperty[] }> }> {
      if (!this.groupedProperties.some(group => group.id === 'prompts')) return this.groupedProperties.map(group => ({ id: group.id, groups: [group] }))
      return [
        { id: 'prompts', groups: this.groupedProperties.filter(group => group.id === 'prompts') },
        { id: 'parameters', groups: this.groupedProperties.filter(group => group.id !== 'prompts') },
      ].filter(column => column.groups.length)
    },
    groupedProperties(): Array<{ id: string; properties: MetadataProperty[] }> {
      return ['prompts', 'models', 'sampling', 'dimensions', 'control', 'processing']
        .map(id => ({ id, properties: this.properties.filter(property => property.group === id).slice().sort((a, b) => Number(a.id === 'model_settings') - Number(b.id === 'model_settings')) }))
        .filter(group => group.properties.length)
    },
  },
  methods: {
    t(key: string) { return i18n.global.t(key) },
    propertyLabel(property: MetadataProperty): string {
      if (property.id === 'conditioning' && ['positive', 'negative'].includes(property.channel || '')) return this.t(`metadata.attributes.${property.channel}`)
      if ((property.id.endsWith('_settings') || property.id === 'conditioning') && property.channel) return i18n.global.te('metadata.fieldLabels.' + property.channel) ? this.t('metadata.fieldLabels.' + property.channel) : property.channel
      return this.t(`metadata.attributes.${property.id}`)
    },
    propertyTip(property: MetadataProperty): string {
      const fieldTip = 'metadata.fieldTips.' + property.channel
      return property.id.endsWith('_settings') && i18n.global.te(fieldTip) ? this.t(fieldTip) : this.t(`metadata.tips.${property.id}`)
    },
    channelLabel(property: MetadataProperty): string {
      if (property.id.endsWith('_settings') || property.id === 'conditioning' || property.channel === 'prompt') return ''
      return property.channel || ''
    },
    isWide(property: MetadataProperty): boolean {
      return property.state === 'unknown' || property.group === 'prompts' || (property.group === 'models' && property.id !== 'model_settings') || property.id === 'seed' || typeof property.value === 'object' || this.formatValue(property.value, property.state).length > 22
    },
    formatValue(value: unknown, state = 'recorded'): string {
      if (state === 'unknown') return this.t('metadata.unknown')
      if (value === '') return this.t('metadata.emptyText')
      if (value === null || value === undefined) return '—'
      if (typeof value === 'boolean') return this.t(value ? 'metadata.enabled' : 'metadata.disabled')
      if (typeof value === 'object') {
        const record = value as Record<string, unknown>
        if ('builtin_checkpoint' in record) return `${this.t('metadata.builtin')}: ${record.builtin_checkpoint}`
        if ('name' in record && 'strength_model' in record) {
          return `${record.name}\n${this.t('metadata.modelStrength')}: ${record.strength_model ?? '—'}\n${this.t('metadata.clipStrength')}: ${record.strength_clip ?? '—'}`
        }
        return JSON.stringify(value, null, 2)
      }
      if (value === 'zeroed') return this.t('metadata.zeroed')
      if (typeof value === 'string' && ['default', 'enable', 'disable', 'enabled', 'disabled'].includes(value)) return this.t('metadata.values.' + value)
      return String(value)
    },
    async copyValue(value: unknown, key: string) {
      try { await navigator.clipboard.writeText(this.formatValue(value)); this.copiedKey = key }
      catch (error) { console.error('复制元数据失败', error) }
    },
  },
})
</script>

<style scoped>
.property-columns { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.property-columns.single { grid-template-columns: minmax(0, 1fr); }
.property-column { min-width: 0; }
.property-group h5 { margin: 6px 0 3px; color: var(--el-text-color-secondary); font-size: 12px; }
.property-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 2px 10px; }
.property { min-width: 0; padding: 2px 0; }
.property:not(.wide) { position: relative; display: flex; align-items: center; gap: 6px; min-height: 20px; }
.property:not(.wide) .property-label { flex: 1; min-width: 0; }
.property:not(.wide) .property-value { margin: 0; flex-shrink: 0; max-width: 50%; }
.property:not(.wide) .copy-button { position: absolute; right: 2px; top: -4px; opacity: 0; background: var(--el-bg-color); border-radius: 3px; padding: 0 3px; }
.property:not(.wide):hover .copy-button, .property:not(.wide):focus-within .copy-button { opacity: 1; }
.property.wide { grid-column: 1 / -1; }
.property-label { display: flex; gap: 4px; align-items: baseline; font-size: 11px; line-height: 16px; color: var(--el-text-color-secondary); }
.label-help { cursor: help; }
.channel, .reason { font-size: 11px; color: var(--el-text-color-secondary); overflow-wrap: anywhere; }
.property-value { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.5; font-size: 12px; margin-top: 2px; }
button { border: 0; color: var(--el-color-primary); background: none; cursor: pointer; white-space: nowrap; font-size: 11px; line-height: 16px; padding: 0; }
.copy-button { margin-left: auto; flex: none; font-size: 12px; line-height: 16px; }
.reason { margin: 3px 0 0; }
@media (max-width: 900px) { .property-columns { grid-template-columns: minmax(0, 1fr); gap: 6px; } }
</style>
<style>
.metadata-help-tooltip { max-width: 300px; line-height: 1.6; }
</style>
