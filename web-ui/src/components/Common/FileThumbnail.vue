<template><div><img v-if="imageUrl" :src="imageUrl" loading="lazy" style="width: 100%; height: 100%; object-fit: cover" @error="fallbackOriginal" /></div></template>
<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import type { FileInfo, FolderType } from '@/types'
export default defineComponent({
  name: 'FileThumbnail',
  props: { file: { type: Object as PropType<FileInfo>, required: true }, folderType: { type: String as PropType<FolderType>, required: true }, displaySize: { type: Number, default: 256 } },
  emits: ['stale'],
  data() { return { inViewport: false, observer: null as IntersectionObserver | null, loadedKey: '', imageUrl: '', objectUrl: '', controller: null as AbortController | null, failedVersion: '', active: true, generation: 0 } },
  computed: {
    requestKey(): string { return JSON.stringify([this.file.folder_path, this.file.name, this.file.file_version, this.size]) },
    size(): number { const pixels = this.displaySize * (window.devicePixelRatio || 1); return pixels <= 256 ? 256 : pixels <= 512 ? 512 : 1024 },
  },
  watch: { requestKey() { this.fetchThumbnail() } },
  mounted() { this.observeVisibility() },
  activated() { if (!this.active) { this.active = true; this.observeVisibility() } },
  deactivated() { this.releaseThumbnail() },
  beforeUnmount() { this.releaseThumbnail() },
  methods: {
    observeVisibility() {
      if (typeof IntersectionObserver === 'undefined') { this.inViewport = true; this.fetchThumbnail(); return }
      this.observer = new IntersectionObserver(entries => {
        this.inViewport = entries.some(entry => entry.isIntersecting)
        if (this.inViewport) this.fetchThumbnail()
        else { this.generation++; this.controller?.abort() }
      })
      this.observer.observe(this.$el)
    },
    releaseThumbnail() { this.observer?.disconnect(); this.observer = null; this.inViewport = false; this.active = false; this.generation++; this.controller?.abort(); if (this.objectUrl) URL.revokeObjectURL(this.objectUrl); this.objectUrl = ''; this.loadedKey = ''; this.imageUrl = '' },
    fallbackOriginal() {
      if (!this.active || !this.inViewport) return
      const version = JSON.stringify([this.file.folder_path, this.file.name, this.file.file_version])
      if (this.failedVersion === version) return
      this.failedVersion = version
      this.loadedKey = this.requestKey
      this.imageUrl = this.file.previewUrl || ''
    },
    async fetchThumbnail() {
      if (!this.active || !this.inViewport || (this.loadedKey === this.requestKey && this.imageUrl)) return
      const generation = ++this.generation
      this.controller?.abort()
      if (!this.file.file_version) { this.fallbackOriginal(); return }
      const controller = this.controller = new AbortController()
      const params = new URLSearchParams({ folder_type: this.folderType, folder_path: this.file.folder_path || '', filename: this.file.name, file_version: this.file.file_version, size: String(this.size) })
      const url = `/browser/files/thumbnail?${params}`
      this.file.thumbnailUrl = url
      try {
        // 受控读取可识别 409，原图仅在同一版本失败时回退一次。
        const response = await fetch(url, { signal: controller.signal })
        if (generation !== this.generation) return
        if (response.status === 409) { this.$emit('stale', this.file.folder_path || ''); return }
        if (!response.ok) throw new Error(`缩略图请求失败：${response.status}`)
        const blob = await response.blob()
        if (generation !== this.generation) return
        if (this.objectUrl) URL.revokeObjectURL(this.objectUrl)
        this.objectUrl = URL.createObjectURL(blob)
        this.loadedKey = this.requestKey
        this.imageUrl = this.objectUrl
      } catch (error) { if (!controller.signal.aborted && generation === this.generation) { console.error('读取缩略图失败', error); this.fallbackOriginal() } }
    },
  },
})
</script>
