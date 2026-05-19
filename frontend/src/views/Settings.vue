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
          <el-button type="warning" @click="handleSyncStandards" :loading="syncingStandards">提取目录全部企业标准 (Word)</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="block-card">
      <template #header>
        <div style="font-weight:700;">台账数据 / 规程Word 直传</div>
      </template>
      
      <div style="max-width: 600px; margin: 10px 0;">
        <el-upload
          drag
          action=""
          :http-request="handleCustomUpload"
          accept=".xlsx,.doc,.docx"
          :show-file-list="true"
          multiple
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 <em>.xlsx (台账文件)</em> 或 <em>.doc/.docx (企标Word)</em> 拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip" style="color: #94a3b8; margin-top: 8px;">
              提示：系统会自动识别文件分流路径：<br/>
              - <strong>.xlsx 生产台账</strong> 将直接进入源数据池等待扫描增量指纹。<br/>
              - <strong>.doc / .docx 企业规程</strong> 将保存在 data/word 目录下。上传后请及时点击上方的【提取目录全部企业标准 (Word)】按钮完成静态指标爬取。
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
      description="当前同步模式支持手动同步和Cron定时同步。变更规格和标准后，点击一键批处理提取将自动清洗出高精度的元素指标数据库。"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getSettings, saveSettings, syncAllExcels, uploadExcel, syncAllStandards } from '../api'

const saving = ref(false)
const syncing = ref(false)
const syncingStandards = ref(false)

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
    ElMessage.success('同步配置已成功落地')
  } catch (e) {
    console.error(e)
    ElMessage.error('落地失败')
  } finally {
    saving.value = false
  }
}

const handleSyncAll = async () => {
  syncing.value = true
  try {
    const { data } = await syncAllExcels()
    if (data.success) {
      ElMessage.success(`台账增量同步完成！新增: ${data.added_count} 条，修改: ${data.updated_count} 条`)
    } else {
      ElMessage.warning(data.message || '无台账变更')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('同步异常')
  } finally {
    syncing.value = false
  }
}

const handleSyncStandards = async () => {
  syncingStandards.value = true
  try {
    const { data } = await syncAllStandards()
    if (data.success) {
      if (data.failed_list && data.failed_list.length > 0) {
        ElMessage.warning(`提取完成！成功处理: ${data.success_count} 个，失败: ${data.failed_list.length} 个。`)
      } else {
        ElMessage.success(`Word范围爬取大获成功！共计录入并更新了 ${data.success_count} 组牌号核心控流网格。`)
      }
    } else {
      ElMessage.warning(data.message)
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('后端爬虫解析异常')
  } finally {
    syncingStandards.value = false
  }
}

const handleCustomUpload = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const { data } = await uploadExcel(formData)
    if (data.success) {
      ElMessage.success(data.message)
      options.onSuccess(data)
    } else {
      ElMessage.error(data.message)
      options.onError(new Error(data.message))
    }
  } catch (err) {
    ElMessage.error('直传中转崩溃')
    options.onError(err)
  }
}

onMounted(() => {
  loadSettings()
})
</script>