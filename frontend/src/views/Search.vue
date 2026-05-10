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

        <el-form-item label="时间">
          <el-date-picker
            v-model="startTime"
            type="datetime"
            placeholder="选择起始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :style="{ width: isMobile ? '100%' : '240px' }"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
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

      <el-table :data="items" border stripe style="width:100%;">
        <el-table-column prop="_sheet_name" label="工作表" width="120" />
        <el-table-column prop="炉号" label="炉号" width="120" />
        <el-table-column prop="牌号" label="牌号" width="180" />
        <el-table-column prop="批次号" label="批次号" width="160" />
        <el-table-column prop="检测时间时间" label="检测时间" width="190" />
        <el-table-column label="判定" width="100">
          <template #default="{ row }">
            <el-tag :type="row['判定'] === '合格' ? 'success' : 'warning'">
              {{ row['判定'] || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="备注" label="备注" />
        <el-table-column prop="__source_file" label="来源文件" width="220" />
        <el-table-column label="操作" width="100" fixed="right">
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
import { searchRecords, getRecordDetail } from '../api'
import RecordDetailDrawer from '../components/RecordDetailDrawer.vue'

const furnaceNo = ref('')
const gradeNo = ref('')
const startTime = ref('')

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const items = ref([])

const drawerVisible = ref(false)
const currentRecord = ref(null)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

const handleSearch = async () => {
  if (!furnaceNo.value.trim() && !gradeNo.value.trim() && !startTime.value) {
    ElMessage.warning('请至少输入一个搜索条件')
    return
  }

  const { data } = await searchRecords({
    furnace_no: furnaceNo.value,
    grade_no: gradeNo.value,
    start_time: startTime.value,
    page: page.value,
    page_size: pageSize.value
  })

  total.value = data.total
  items.value = data.items
}

const handleReset = () => {
  furnaceNo.value = ''
  gradeNo.value = ''
  startTime.value = ''
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

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>