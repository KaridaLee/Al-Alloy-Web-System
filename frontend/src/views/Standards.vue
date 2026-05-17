<template>
  <div>
    <div class="page-title">企业标准管理</div>

    <el-card class="block-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="合金牌号">
          <el-input
            v-model="searchBrand"
            placeholder="输入牌号名称进行检索 (如 ADC12)"
            clearable
            style="width: 280px"
            @keyup.enter="fetchStandards"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchStandards">检索标准</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="block-card" style="margin-top:18px;">
      <template #header>
        <div style="font-weight:700;">受控企标存存根 (共 {{ tableData.length }} 项)</div>
      </template>

      <el-table :data="tableData" border stripe style="width:100%;">
        <el-table-column prop="brand_name" label="标准对应牌号" width="260" />
        <el-table-column prop="updated_at" label="解析同步时间" width="220" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetailDrawer(row.brand_name)">
              指标详情
            </el-button>
            <el-button type="success" link @click="openPdfViewer(row.brand_name)">
              查看原件
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" title="标准指标对标详情" size="35%">
      <div v-if="selectedStandard" style="padding-bottom: 24px;">
        <h3 style="margin-top:0;color:#1e293b;">牌号：{{ selectedStandard.brand_name }}</h3>
        
        <el-card class="box-card" style="margin-bottom:14px;" shadow="never">
          <template #header><span style="font-weight:700;">化学元素成分范围要求</span></template>
          <el-table :data="elementGridData" border stripe size="small" style="width:100%;">
            <el-table-column prop="element" label="元素" width="80" align="center" />
            <el-table-column prop="tech" label="技术范围要求">
              <template #default="{ row }">{{ row.tech || '0% - 100% (默认)' }}</template>
            </el-table-column>
            <el-table-column prop="ctrl" label="企业内控要求">
              <template #default="{ row }">{{ row.ctrl || '0% - 100% (默认)' }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-drawer>

    <el-dialog
      v-model="pdfDialogVisible"
      :title="'企标物理原件：' + activePdfBrand"
      width="60%"
      top="4vh"
      destroy-on-close
    >
      <div v-loading="pdfLoading" style="height: 72vh; overflow-y: auto; background:#e2e8f0; text-align: center; padding: 16px;">
        <div v-if="!pdfLoading && totalPdfPages > 0">
          <div v-for="pageIndex in totalPdfPages" :key="pageIndex" style="margin-bottom: 16px;">
            <img 
              :src="getPageUrl(pageIndex - 1)" 
              style="max-width: 100%; box-shadow: 0 8px 16px rgba(0,0,0,0.1); border-radius: 4px; display: block; margin: 0 auto;" 
              loading="lazy" 
              alt="标准原件页"
            />
          </div>
        </div>
        <el-empty v-if="!pdfLoading && totalPdfPages === 0" description="未找到可用的原件或解析失败"></el-empty>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { searchStandards, getStandardDetail, getStandardPdfInfo } from '../api'

const searchBrand = ref('')
const tableData = ref([])

const drawerVisible = ref(false)
const selectedStandard = ref(null)

const pdfDialogVisible = ref(false)
const activePdfBrand = ref('')
const totalPdfPages = ref(0)
const pdfLoading = ref(false)

const fetchStandards = async () => {
  const { data } = await searchStandards({ brand_name: searchBrand.value })
  tableData.value = data.items || []
}

const openDetailDrawer = async (brandName) => {
  const { data } = await getStandardDetail({ brand_name: brandName })
  if (data.success) {
    selectedStandard.value = data.standard
    drawerVisible.value = true
  }
}

const openPdfViewer = async (brandName) => {
  activePdfBrand.value = brandName
  totalPdfPages.value = 0
  pdfDialogVisible.value = true
  pdfLoading.value = true

  try {
    const { data } = await getStandardPdfInfo({ brand_name: brandName })
    if (data.success) {
      totalPdfPages.value = data.totalPages
    } else {
      ElMessage.error(data.message || '获取 PDF 结构信息失败')
    }
  } catch (e) {
    ElMessage.error('请求原件失败')
  } finally {
    pdfLoading.value = false
  }
}

const getPageUrl = (pageIndex) => {
  return `/api/search/standards/file/${encodeURIComponent(activePdfBrand.value)}/page/${pageIndex}`
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
  fetchStandards()
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
:deep(.box-card .el-card__header) {
  padding: 10px 14px !important;
  background-color: #f8fafc;
  font-size: 13px;
}
</style>