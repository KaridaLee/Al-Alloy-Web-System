<template>
  <div>
    <div class="page-title">企业标准管理</div>

    <el-card class="block-card" style="margin-bottom: 24px;">
      <template #header>
        <div style="font-weight:700;">企业标准原件预览 (PDF)</div>
      </template>

      <el-table :data="pdfList" border stripe style="width:100%;" max-height="300">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="filename" label="PDF 原件名称" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="success" link @click="openPdfViewer(row.filename)">
              查看原件
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="pdfList.length === 0" style="text-align: center; color: #94a3b8; padding: 20px 0;">
        data/standards 目录下暂无 PDF 文件
      </div>
    </el-card>

    <div style="font-size: 18px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">
      企标元素范围数据
    </div>
    
    <el-row :gutter="18">
      <el-col :span="10">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:700;">已解析标准数据</span>
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
                  <span v-else style="color: #94a3b8; font-size: 12px;">0% - 100% (默认)</span>
                </template>
              </el-table-column>
              <el-table-column prop="ctrl" label="企业内控要求 (精炼线)" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.ctrl" type="success" effect="light">{{ row.ctrl }}</el-tag>
                  <span v-else style="color: #94a3b8; font-size: 12px;">0% - 100% (默认)</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-empty v-else description="暂未选中任何企标存根记录"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="pdfDialogVisible"
      :title="'原件预览：' + activePdfFile"
      width="75%"
      top="5vh"
      destroy-on-close
    >
      <div style="height: 75vh; border: 1px solid #e2e8f0; border-radius: 4px;">
        <iframe
          v-if="activePdfFile"
          :src="'/api/search/standards/pdfs/' + encodeURIComponent(activePdfFile)"
          width="100%"
          height="100%"
          frameborder="0"
          style="display: block;"
        ></iframe>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { searchStandards, getStandardDetail, getStandardPdfs } from '../api'

// --- PDF 模块相关 ---
const pdfList = ref([])
const pdfDialogVisible = ref(false)
const activePdfFile = ref('')

const fetchPdfList = async () => {
  try {
    const { data } = await getStandardPdfs()
    pdfList.value = data.items || []
  } catch (e) {
    console.error('获取 PDF 列表失败', e)
  }
}

const openPdfViewer = (filename) => {
  activePdfFile.value = filename
  pdfDialogVisible.value = true
}

// --- DB/Word 数据模块相关 ---
const searchBrand = ref('')
const tableData = ref([])
const activeBrand = ref('')
const selectedStandard = ref(null)

const fetchStandards = async () => {
  const { data } = await searchStandards({ brand_name: searchBrand.value })
  tableData.value = data.items || []
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

const elementGridData = computed(() => {
  if (!selectedStandard.value) return []
  const tech = selectedStandard.value.tech_req || {}
  const ctrl = selectedStandard.value.ctrl_req || {}
  
  const allElements = Array.from(new Set([...Object.keys(tech), ...Object.keys(ctrl)]))
  
  return allElements.map(el => ({
    element: el,
    tech: tech[el],
    ctrl: ctrl[el]
  }))
})

onMounted(() => {
  fetchPdfList()
  fetchStandards()
})
</script>

<style scoped>
.block-card {
  border-radius: 12px;
  transition: all 0.3s;
  min-height: 200px;
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