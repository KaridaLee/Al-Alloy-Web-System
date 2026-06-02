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
        :data="filteredDocs" 
        border 
        stripe 
        style="width:100%;" 
        max-height="650"
      >
        <el-table-column type="index" label="序号" width="70" align="center" />
        
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
    </el-card>

    <el-dialog
      v-model="previewVisible"
      :title="'文件查阅：' + activeDoc.filename"
      width="75%"
      top="5vh"
      destroy-on-close
    >
      <div style="height: 75vh; border: 1px solid #e2e8f0; border-radius: 4px; display: flex; flex-direction: column; background: #f8fafc;">
        
        <iframe
          v-if="activeDoc.ext === '.pdf'"
          :src="'/api/system/docs/file?path=' + encodeURIComponent(activeDoc.rel_path)"
          width="100%"
          height="100%"
          frameborder="0"
          style="display: block; flex: 1;"
        ></iframe>
        
        <div v-else style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
          <div style="font-size: 64px; margin-bottom: 20px;">📄</div>
          <div style="font-size: 18px; font-weight: bold; color: #334155; margin-bottom: 12px;">
            当前格式（{{ activeDoc.ext }}）不支持内嵌在线预览
          </div>
          <div style="color: #64748b; margin-bottom: 24px; max-width: 400px;">
            由于浏览器安全与渲染内核限制，Word 或 Excel 档案需传输至本地机器后使用专业 Office 软件进行阅览。
          </div>
          <el-button type="primary" size="large" @click="handleDownload(activeDoc)">
            📥 立即下载到本地
          </el-button>
        </div>

      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getSystemDocs } from '../api'

const docsList = ref([])
const searchQuery = ref('')
const loading = ref(false)

const previewVisible = ref(false)
const activeDoc = ref({})

// 初始化加载目录全量文件
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

// 动态检索过滤
const filteredDocs = computed(() => {
  let list = [...docsList.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(item => item.filename.toLowerCase().includes(q))
  }
  return list
})

// 触发预览操作
const handlePreview = (row) => {
  activeDoc.value = row
  previewVisible.value = true
}

// 触发强制下载操作
const handleDownload = (row) => {
  const url = `/api/system/docs/file?path=${encodeURIComponent(row.rel_path)}&download=true`
  window.open(url, '_blank')
}

// 样式辅助：类型标签颜色映射
const getTagType = (ext) => {
  if (ext === '.pdf') return 'danger'
  if (['.xls', '.xlsx'].includes(ext)) return 'success'
  if (['.doc', '.docx'].includes(ext)) return 'primary'
  return 'info'
}

// 样式辅助：文件名前的小圆点装饰
const getFileDotStyle = (ext) => {
  let color = '#94a3b8'
  if (ext === '.pdf') color = '#ef4444' // 红
  else if (['.xls', '.xlsx'].includes(ext)) color = '#10b981' // 绿
  else if (['.doc', '.docx'].includes(ext)) color = '#3b82f6' // 蓝
  
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
</style>