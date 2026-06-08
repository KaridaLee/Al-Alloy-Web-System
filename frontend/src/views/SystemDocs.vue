<template>
  <div>
    <div class="page-title">体系文件</div>

    <el-card class="block-card">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700;">系统关联文件资源库</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索文件名称..."
            size="small"
            clearable
            style="width: 260px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table 
        v-loading="loading" 
        :data="paginatedDocs" 
        border 
        stripe 
        style="width:100%;" 
        max-height="650"
      >
        <el-table-column label="序号" width="70" align="center">
          <template #default="{ $index }">
            {{ (currentPage - 1) * pageSize + $index + 1 }}
          </template>
        </el-table-column>
        
        <el-table-column prop="filename" label="文件名称" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span :style="getFileDotStyle(row.ext)"></span>
              <span style="font-weight: 500;">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ext" label="格式" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getTagType(row.ext)" effect="light">
              {{ row.ext.replace('.', '').toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handlePreview(row)">预览</el-button>
            <el-button type="success" link @click="handleDownload(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && filteredDocs.length === 0" style="text-align: center; color: #94a3b8; padding: 40px 0;">
        未能找到匹配的文件记录，请检查检索词或确保存放目录内存在文件。
      </div>

      <div style="margin-top: 18px; display: flex; justify-content: flex-end;">
        <el-pagination
          background
          layout="total, prev, pager, next, jumper"
          :total="filteredDocs.length"
          :page-size="pageSize"
          v-model:current-page="currentPage"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="previewVisible"
      :title="'文件阅览：' + activeDoc.filename"
      width="80%"
      top="4vh"
      destroy-on-close
      @closed="clearPreviewData"
    >
      <div 
        style="height: 78vh; border: 1px solid #e2e8f0; border-radius: 4px; display: flex; flex-direction: column; background: #f8fafc; overflow: hidden;"
        v-loading="previewLoading"
        element-loading-text="引擎正在解析转换文档中，请稍候..."
      >
        
        <iframe
          v-if="renderMode === 'pdf'"
          :src="'/api/system/docs/file?path=' + encodeURIComponent(activeDoc.rel_path)"
          width="100%"
          height="100%"
          frameborder="0"
          style="display: block; flex: 1;"
        ></iframe>

        <div 
          v-else-if="renderMode === 'html'" 
          style="flex: 1; overflow-y: auto; padding: 10px;"
          v-html="officeHtmlContent"
        >
        </div>
        
        <div v-else-if="renderMode === 'unsupported'" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
          <div style="font-size: 64px; margin-bottom: 20px;">📄</div>
          <div style="font-size: 18px; font-weight: bold; color: #334155; margin-bottom: 12px;">
            系统暂不支持旧版二进制格式（{{ activeDoc.ext }}）的在线解析
          </div>
          <div style="color: #64748b; margin-bottom: 24px; max-width: 450px; line-height: 1.6;">
            提示：现代系统已原生支持秒开预览 <b>.xlsx</b> 以及 <b>.docx</b> 格式的文件。<br/>您可以将此旧文件在电脑上“另存为”新版格式后放入目录，即可获得丝滑预览体验。
          </div>
          <el-button type="primary" size="large" @click="handleDownload(activeDoc)">
            📥 立即下载到本地查阅
          </el-button>
        </div>

      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getSystemDocs, getSystemDocHtmlPreview } from '../api'

const docsList = ref([])
const searchQuery = ref('')
const loading = ref(false)

// 分页状态管理
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
    console.error('体系文件列表拉取失败:', e)
  } finally {
    loading.value = false
  }
}

// 第一层：根据搜索词过滤全量数据
const filteredDocs = computed(() => {
  let list = [...docsList.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(item => item.filename.toLowerCase().includes(q))
  }
  return list
})

// 第二层：根据分页状态截取当前页的数据展示
const paginatedDocs = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  const endIndex = startIndex + pageSize.value
  return filteredDocs.value.slice(startIndex, endIndex)
})

// 监听搜索词变化，一旦进行搜索，页码强制回归第一页
watch(searchQuery, () => {
  currentPage.value = 1
})

const handlePreview = async (row) => {
  activeDoc.value = row
  previewVisible.value = true
  
  if (row.ext === '.pdf') {
    renderMode.value = 'pdf'
  } 
  else if (row.ext === '.docx' || row.ext === '.xlsx') {
    renderMode.value = 'html'
    previewLoading.value = true
    try {
      const { data } = await getSystemDocHtmlPreview({ path: row.rel_path })
      if (data.success) {
        officeHtmlContent.value = data.html
      } else {
        renderMode.value = 'unsupported'
        ElMessage.error(data.message || '文档转化引擎解析失败')
      }
    } catch (error) {
      renderMode.value = 'unsupported'
      ElMessage.error('服务器解析请求超时')
    } finally {
      previewLoading.value = false
    }
  } 
  else {
    renderMode.value = 'unsupported'
  }
}

const clearPreviewData = () => {
  officeHtmlContent.value = ''
  renderMode.value = ''
  activeDoc.value = {}
}

const handleDownload = (row) => {
  const url = `/api/system/docs/file?path=${encodeURIComponent(row.rel_path)}&download=true`
  window.open(url, '_blank')
}

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
  
  return {
    display: 'inline-block',
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: color
  }
}

onMounted(() => {
  fetchDocs()
})
</script>

<style scoped>
.block-card {
  border-radius: 12px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #1e293b;
}

:deep(.el-dialog__body) {
  padding: 10px 20px 20px 20px;
}
</style>