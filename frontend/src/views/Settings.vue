<template>
  <div>
    <div class="page-title">系统设置</div>

    <el-card class="block-card" style="margin-bottom:18px;">
      <template #header>
        <div style="font-weight:700;">同步设置</div>
      </template>

      <el-form label-width="140px">
        <el-form-item label="Excel目录">
          <el-input v-model="settings.sourceDir" placeholder="例如：data/source" />
        </el-form-item>

        <el-form-item label="同步模式">
          <el-radio-group v-model="settings.syncMode">
            <el-radio label="manual">手动同步</el-radio>
            <el-radio label="cron">定时同步</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="Cron表达式" v-if="settings.syncMode === 'cron'">
          <el-input v-model="settings.cron" placeholder="例如：0 */30 * * * *" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存设置</el-button>
          <el-button type="success" @click="handleSyncAll" :loading="syncing">立即同步目录全部Excel</el-button>
        </el-form-item>
      </el-form>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-top:12px;"
        title="说明"
        description="当前同步模式支持手动同步和Cron定时同步。目录同步会扫描设置目录下所有 xlsx 文件并导入同一个数据库。"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, saveSettings, syncAllExcels } from '../api'

const saving = ref(false)
const syncing = ref(false)

const settings = reactive({
  sourceDir: 'data/source',
  syncMode: 'manual',
  cron: '0 0/30 * * * *'
})

const loadSettings = async () => {
  try {
    const { data } = await getSettings()
    settings.sourceDir = data.sourceDir || 'data/source'
    settings.syncMode = data.syncMode || 'manual'
    settings.cron = data.cron || '0 0/30 * * * *'
  } catch (e) {
    console.error(e)
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await saveSettings({
      sourceDir: settings.sourceDir,
      syncMode: settings.syncMode,
      cron: settings.cron
    })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleSyncAll = async () => {
  syncing.value = true
  try {
    await syncAllExcels()
    ElMessage.success('目录同步完成')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '目录同步失败')
  } finally {
    syncing.value = false
  }
}

onMounted(loadSettings)
</script>