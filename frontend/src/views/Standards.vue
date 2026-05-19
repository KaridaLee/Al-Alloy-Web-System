<template>
  <div>
    <div class="page-title">企业标准管理 — 企标范围</div>

    <el-row :gutter="18">
      <el-col :span="10">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:700;">受控企标文件</span>
              <el-input
                v-model="searchBrand"
                placeholder="筛选牌号"
                size="small"
                clearable
                style="width: 140px"
                @input="fetchStandards"
              />
            </div>
          </template>

          <el-table 
            :data="tableData" 
            border 
            stripe 
            highlight-current-row
            style="width:100%; cursor:pointer;"
            @current-change="handleRowSelect"
          >
            <el-table-column prop="brand_name" label="标准对应牌号" />
            <el-table-column prop="updated_at" label="提取时间" width="160" align="center" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700; color: #1e293b;">
              {{ activeBrand ? `【${activeBrand}】化学元素内控技术范围要求` : '请在左侧选择企标查看对应成分范围' }}
            </div>
          </template>

          <div v-if="activeBrand">
            <el-table :data="elementGridData" border stripe style="width:100%;">
              <el-table-column prop="element" label="受控元素" width="100" align="center" />
              <el-table-column prop="tech" label="技术范围要求 (规程线)" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.tech" type="info" effect="plain">{{ row.tech }}</el-tag>
                  <span v-else style="color: #94a3b8; font-size: 12px;">0% - 100% (默认宽松)</span>
                </template>
              </el-table-column>
              <el-table-column prop="ctrl" label="企业内控要求 (精炼线)" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.ctrl" type="success" effect="light">{{ row.ctrl }}</el-tag>
                  <span v-else style="color: #94a3b8; font-size: 12px;">0% - 100% (默认宽松)</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-empty v-else description="暂未选中任何企标存根记录"></el-empty>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { searchStandards, getStandardDetail } from '../api'

const searchBrand = ref('')
const tableData = ref([])
const activeBrand = ref('')
const selectedStandard = ref(null)

const fetchStandards = async () => {
  const { data } = await searchStandards({ brand_name: searchBrand.value })
  tableData.value = data.items || []
  // 默认取消选中，保持干净
  activeBrand.value = ''
  selectedStandard.value = null
}

const handleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeBrand.value = currentRow.brand_name
  
  const { data } = await getStandardDetail({ brand_name: currentRow.brand_name })
  if (data.success) {
    selectedStandard.value = data.standard
  }
}

// 高灵活性扁平化映射计算
const elementGridData = computed(() => {
  if (!selectedStandard.value) return []
  const tech = selectedStandard.value.tech_req || {}
  const ctrl = selectedStandard.value.ctrl_req || {}
  
  // 兼顾所有在技术或内控中露过脸的合金成分，实现完美容错
  const allElements = Array.from(new Set([...Object.keys(tech), ...Object.keys(ctrl)]))
  
  return allElements.map(el => ({
    element: el,
    tech: tech[el],
    ctrl: ctrl[el]
  }))
})

onMounted(() => {
  fetchStandards()
})
</script>

<style scoped>
.block-card {
  border-radius: 12px;
  transition: all 0.3s;
  min-height: 480px;
}
.block-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #1e293b;
}
</style>