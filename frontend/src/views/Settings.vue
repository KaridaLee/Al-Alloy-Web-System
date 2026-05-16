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
    </el-card>

    <el-card class="block-card">
      <template #header>
        <div style="font-weight:700;">Excel 台账原始文件直传</div>
      </template>
      
      <div style="max-width: 600px; margin: 10px 0;">
        <el-upload
          drag
          action=""
          :http-request="handleCustomUpload"
          accept=".xlsx"
          :show-file-list="true"
          multiple
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将需要转换的台账 .xlsx 文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip" style="color: #94a3b8; margin-top: 8px;">
              提示：上传后文件将直接保存在系统的同步源目录中（当前配置为: {{ settings.sourceDir }}）。上传完成后，可点击上方的“立即同步目录全部Excel”进行本地指纹库增量解析。
            </div>
          </template>
        </el-upload>
      </div>
    </el-card>

    <el-alert
      style="margin-top:18px;"
      title="说明"
      type="info"
      :closable="false"
      description="当前同步模式支持手动同步和Cron定时同步。目录同步与上传功能会自动对应设置目录。通过指纹识别引擎，系统将仅对有改动或新增的数据进行数据库操作。"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getSettings, saveSettings, syncAllExcels, uploadExcel } from '../api'

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
    ElMessage.success('设置已成功保存')
  } catch (e) {
    console.error(e)
    ElMessage.error('保存设置失败')
  } fill: {
    saving.value = false
  }
}

const handleSyncAll = async () => {
  syncing.value = true
  try {
    const { data } = await syncAllExcels()
    if (data.success) {
      ElMessage.success(`增量同步完成！新增: ${data.added_count} 条，修改: ${data.updated_count} 条，删除: ${data.deleted_count} 条`)
    } else {
      ElMessage.warning(data.message || '没有检测到待同步文件')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('同步出现严重异常，请检查本地源目录文件')
  } finally {
    syncing.value = false
  }
}

// 处理自定义文件上传逻辑
const handleCustomUpload = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  
  try {
    const { data } = await uploadExcel(formData)
    if (data.success) {
      ElMessage.success(data.message || '文件上传并保存成功')
      options.onSuccess(data)
    } else {
      ElMessage.error(data.message || '文件保存失败')
      options.onError(new Error(data.message))
    }
  } catch (err) {
    console.error('上传接口调用异常:', err)
    ElMessage.error('上传服务发生错误，请检查后端运行状态')
    options.onError(err)
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.block-card {
  border-radius: 12px;
  transition: all 0.3s;
}
.block-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.05);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #1e293b;
}
</style>