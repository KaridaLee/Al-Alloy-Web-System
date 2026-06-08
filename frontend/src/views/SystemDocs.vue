<template>
  <div>
    <div class="page-title">体系文件</div>

    <el-card class="block-card">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700;">系统关联文件资源库</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索名称..."
            size="small"
            clearable
            :style="{ width: isMobile ? '160px' : '260px' }"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table v-loading="loading" :data="paginatedDocs" border stripe style="width:100%;" max-height="650">
        <el-table-column label="序号" width="70" align="center">
          <template #default="{ $index }">{{ (currentPage - 1) * pageSize + $index + 1 }}</template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span :style="getFileDotStyle(row.ext)"></span>
              <span style="font-weight: 500;">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ext" label="格式" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getTagType(row.ext)" effect="light">{{ row.ext.replace('.', '').toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handlePreview(row)">预览</el-button>
            <el-button type="success" link @click="handleDownload(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 18px; display: flex; justify-content: flex-end;">
        <el-pagination
          background
          :layout="isMobile ? 'prev, pager, next' : 'total, prev, pager, next, jumper'"
          :total="filteredDocs.length"
          :page-size="pageSize"
          v-model:current-page="currentPage"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="previewVisible"
      :title="'阅览：' + activeDoc.filename"
      :width="isMobile ? '95%' : '80%'"
      top="4vh"
      destroy-on-close
      @closed="clearPreviewData"
    >
      <div 
        style="height: 78vh; border: 1px solid #e2e8f0; border-radius: 4px; display: flex; flex-direction: column; background: #f8fafc; overflow: hidden;"
        v-loading="previewLoading"
        element-loading-text="引擎正在解析转换文档中，请稍候..."
      >
        <iframe v-if="renderMode === 'pdf'" :src="'/api/system/docs/file?path=' + encodeURIComponent(activeDoc.rel_path)" width="100%" height="100%" frameborder="0" style="display: block; flex: 1;"></iframe>
        <div v-else-if="renderMode === 'html'" style="flex: 1; overflow-y: auto; padding: 10px;" v-html="officeHtmlContent"></div>
        <div v-else-if="renderMode === 'unsupported'" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
          <div style="font-size: 64px; margin-bottom: 20px;">📄</div>
          <div style="font-size: 16px; font-weight: bold; color: #334155; margin-bottom: 12px; padding: 0 16px;">不支持旧版（{{ activeDoc.ext }}）在线解析，请下载阅览或另存为新版格式</div>
          <el-button type="primary" size="large" @click="handleDownload(activeDoc)">📥 下载到本地</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onBeforeUnmount } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getSystemDocs, getSystemDocHtmlPreview } from '../api'

const isMobile = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }

const docsList = ref([])
const searchQuery = ref('')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(15)
const previewVisible = ref(false)
const previewLoading = ref(false)
const activeDoc = ref({})
const renderMode = ref('')
const officeHtmlContent = ref('')

const fetchDocs = async () => {
  loading.value = true
  try {
    const { data } = await getSystemDocs()
    docsList.value = data.items || []
  } catch (e) {
  } finally { loading.value = false }
}

const filteredDocs = computed(() => {
  let list = [...docsList.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(item => item.filename.toLowerCase().includes(q))
  }
  return list
})

const paginatedDocs = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  return filteredDocs.value.slice(startIndex, startIndex + pageSize.value)
})

watch(searchQuery, () => { currentPage.value = 1 })

const handlePreview = async (row) => {
  activeDoc.value = row
  previewVisible.value = true
  if (row.ext === '.pdf') { renderMode.value = 'pdf' } 
  else if (row.ext === '.docx' || row.ext === '.xlsx') {
    renderMode.value = 'html'; previewLoading.value = true
    try {
      const { data } = await getSystemDocHtmlPreview({ path: row.rel_path })
      if (data.success) { officeHtmlContent.value = data.html } 
      else { renderMode.value = 'unsupported' }
    } catch (error) { renderMode.value = 'unsupported' } 
    finally { previewLoading.value = false }
  } else { renderMode.value = 'unsupported' }
}

const clearPreviewData = () => { officeHtmlContent.value = ''; renderMode.value = ''; activeDoc.value = {} }
const handleDownload = (row) => { window.open(`/api/system/docs/file?path=${encodeURIComponent(row.rel_path)}&download=true`, '_blank') }

const getTagType = (ext) => {
  if (ext === '.pdf') return 'danger'
  if (['.xls', '.xlsx'].includes(ext)) return 'success'
  if (['.doc', '.docx'].includes(ext)) return 'primary'
  return 'info'
}

const getFileDotStyle = (ext) => {
  let color = '#94a3b8'
  if (ext === '.pdf') color = '#ef4444'
  else if (['.xls', '.xlsx'].includes(ext)) color = '#10b981'
  else if (['.doc', '.docx'].includes(ext)) color = '#3b82f6'
  return { display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color }
}

onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile); fetchDocs() })
onBeforeUnmount(() => { window.removeEventListener('resize', checkMobile) })
</script>

<style scoped>
.block-card { border-radius: 12px; }
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 20px; color: #1e293b; }
:deep(.el-dialog__body) { padding: 10px 20px 20px 20px; }
</style>