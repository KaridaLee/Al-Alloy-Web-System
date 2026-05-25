<template>
  <div>
    <div class="page-title">数据搜索</div>

    <el-card class="block-card">
      <el-form :inline="!isMobile" label-width="70px">
        <el-form-item label="炉号">
          <el-input
            v-model="furnaceNo"
            placeholder="输入炉号"
            :style="{ width: isMobile ? '100%' : '220px' }"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="牌号">
          <el-input
            v-model="gradeNo"
            placeholder="输入牌号"
            :style="{ width: isMobile ? '100%' : '220px' }"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="时间区间">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :style="{ width: isMobile ? '100%' : '360px' }"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button 
            type="success" 
            :disabled="selectedRows.length === 0" 
            @click="handleExport"
            :loading="exporting"
          >
            导出选中元素 ({{ selectedRows.length }})
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="block-card" style="margin-top:18px;">
      <template #header>
        <div class="table-header">
          <div>
            <div style="font-weight:700;">搜索结果</div>
            <div class="sub-title">共 {{ total }} 条匹配记录</div>
          </div>
        </div>
      </template>

      <el-table :data="items" border stripe style="width:100%;" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        
        <el-table-column prop="_sheet_name" label="工作表" min-width="130" show-overflow-tooltip />
        <el-table-column prop="炉号" label="炉号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="牌号" label="牌号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="批次号" label="批次号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="检测时间时间" label="检测时间" min-width="180" show-overflow-tooltip />
        <el-table-column prop="备注" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column prop="__source_file" label="来源文件" min-width="220" show-overflow-tooltip />
        
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;display:flex;justify-content:flex-end;">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          v-model:current-page="page"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <RecordDetailDrawer v-model="drawerVisible" :record="currentRecord" />
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { searchRecords, getRecordDetail, exportRecords } from '../api'
import RecordDetailDrawer from '../components/RecordDetailDrawer.vue'

const furnaceNo = ref('')
const gradeNo = ref('')
const timeRange = ref([])

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const items = ref([])

const drawerVisible = ref(false)
const currentRecord = ref(null)
const isMobile = ref(false)

const selectedRows = ref([])
const exporting = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

const handleSearch = async () => {
  const startTime = timeRange.value?.[0] || ''
  const endTime = timeRange.value?.[1] || ''

  if (!furnaceNo.value.trim() && !gradeNo.value.trim() && !startTime && !endTime) {
    ElMessage.warning('请至少输入一个搜索条件')
    return
  }

  const { data } = await searchRecords({
    furnace_no: furnaceNo.value,
    grade_no: gradeNo.value,
    start_time: startTime,
    end_time: endTime,
    page: page.value,
    page_size: pageSize.value
  })

  total.value = data.total
  items.value = data.items
}

const handleReset = () => {
  furnaceNo.value = ''
  gradeNo.value = ''
  timeRange.value = []
  page.value = 1
  items.value = []
  total.value = 0
}

const showDetail = async (row) => {
  const { data } = await getRecordDetail({
    sheet: row._sheet_name,
    row_key: row.__row_key
  })
  currentRecord.value = data.item
  drawerVisible.value = true
}

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleExport = async () => {
  if (selectedRows.value.length === 0) return
  
  exporting.value = true
  try {
    const payload = {
      items: selectedRows.value.map(row => ({
        row_key: row.__row_key,
        sheet_name: row._sheet_name || row.__source_sheet
      }))
    }

    const response = await exportRecords(payload)
    
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    const timeStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    link.download = `元素数据导出_${timeStr}.xlsx`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败，请检查网络或控制台日志')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
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
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sub-title {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}
</style>