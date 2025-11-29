<template>
  <div class="new-download-container">
    <el-form label-position="top" class="download-form">
      <el-form-item :label="t('modelsTab.downloadUrl')" required>
        <el-input v-model="downloadUrl" placeholder="https://civitai.com/api/download/models/35516" clearable />
      </el-form-item>

      <el-form-item :label="t('modelsTab.filename')">
        <el-input v-model="filename" clearable />
      </el-form-item>

      <el-form-item :label="t('modelsTab.selectModelType')" required>
        <el-select v-model="modelType" class="w-full">
          <el-option v-for="item in modelTypes" :key="item.value" :label="item.text" :value="item.value" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="overwrite">{{ t('modelsTab.overwrite') }}</el-checkbox>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleDownload" :loading="loading">
          {{ t('modelsTab.download') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { createDownload } from '@/api/models'

export default defineComponent({
  name: 'NewDownload',
  emits: ['download-started'],
  setup() {
    const { t } = useI18n()
    return { t }
  },
  data() {
    return {
      downloadUrl: '',
      filename: '',
      modelType: 'checkpoints',
      overwrite: false,
      loading: false,
      modelTypes: [
        { text: 'Checkpoint', value: 'checkpoints' },
        { text: 'LoRA', value: 'loras' },
        { text: 'VAE', value: 'vae' },
        { text: 'Embedding', value: 'embeddings' },
        { text: 'ControlNet', value: 'controlnet' },
      ]
    }
  },
  methods: {
    async handleDownload() {
      if (!this.downloadUrl) {
        ElMessage.warning(this.t('modelsTab.enterUrl'))
        return
      }

      this.loading = true
      try {
        await createDownload({
          download_url: this.downloadUrl,
          save_in: this.modelType,
          filename: this.filename,
          overwrite: this.overwrite
        })

        ElMessage.success(this.t('modelsTab.downloadStarted'))
        this.$emit('download-started')

        // Reset form
        this.downloadUrl = ''
        this.filename = ''
        this.overwrite = false
      } catch (error) {
        console.error('Download failed:', error)
        ElMessage.error(this.t('modelsTab.downloadFailed'))
      } finally {
        this.loading = false
      }
    }
  }
})
</script>

<style scoped>
  .new-download-container {
    padding: 20px;
    max-width: 600px;
  }

  .w-full {
    width: 100%;
  }
</style>