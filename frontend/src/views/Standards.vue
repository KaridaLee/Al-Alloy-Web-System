<template>
  <div>
    <div class="page-title">企业标准管理</div>

    <el-card class="block-card" style="margin-bottom: 24px;">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700;">企业标准原件预览 (PDF)</span>
          <el-input
            v-model="pdfSearchQuery"
            placeholder="搜索 PDF 文件名称"
            size="small"
            clearable
            style="width: 240px"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="filteredPdfList" border stripe style="width:100%;" max-height="450">
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
      
      <div v-if="filteredPdfList.length === 0" style="text-align: center; color: #94a3b8; padding: 20px 0;">
        没有找到对应的 PDF 文件
      </div>
    </el-card>

    <div style="font-size: 18px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">
      企标元素范围数据
    </div>
    
    <el-row :gutter="18">
      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:700;">所有已知牌号列表</span>
              <el-input
                v-model="searchBrand"
                placeholder="筛选牌号"
                size="small"
                clearable
                style="width: 130px"
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
            max-height="600"
            @current-change="handleRowSelect"
          >
            <el-table-column prop="brand_name" label="牌号名称 (点击可编辑范围)" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="font-weight:700; color: #1e293b;">
                {{ activeBrand ? `【${activeBrand}】化学元素内控技术范围要求` : '请在左侧选择牌号进行配置' }}
              </div>
              <div v-if="activeBrand">
                <el-button v-if="!isEditing" type="primary" size="small" @click="enterEditMode">
                  编辑范围指标
                </el-button>
                <div v-else>
                  <el-button size="small" @click="cancelEdit">取消</el-button>
                  <el-button type="success" size="small" :loading="saving" @click="saveEdit">
                    保存至数据库
                  </el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-if="activeBrand">
            <el-table v-if="!isEditing" :data="viewGridData" border stripe style="width:100%;">
              <el-table-column prop="tech_min" label="技术下限" align="center" />
              <el-table-column prop="ctrl_min" label="内控下限" align="center" />
              <el-table-column prop="element" label="元素" align="center" width="80">
                <template #default="{ row }"><strong>{{ row.element }}</strong></template>
              </el-table-column>
              <el-table-column prop="ctrl_max" label="内控上限" align="center" />
              <el-table-column prop="tech_max" label="技术上限" align="center" />
            </el-table>
            
            <div v-if="!isEditing && viewGridData.length === 0" style="text-align: center; color: #94a3b8; padding: 40px 0;">
              暂未配置指标，请点击右上角“编辑范围指标”进行填写。
            </div>

            <el-table v-if="isEditing" :data="ELEMENTS_ORDER" border stripe size="small" style="width:100%;" max-height="600">
              <el-table-column label="技术下限" align="center">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].tech_min" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="内控下限" align="center">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].ctrl_min" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="元素" align="center" width="80">
                <template #default="{ row }"><strong>{{ row }}</strong></template>
              </el-table-column>
              <el-table-column label="内控上限" align="center">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].ctrl_max" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="技术上限" align="center">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].tech_max" placeholder="-" clearable />
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-empty v-else description="请先在左侧列表中点击选择一项牌号"></el-empty>
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
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { searchStandards, getStandardDetail, getStandardPdfs, saveStandardDetail } from '../api'

const ELEMENTS_ORDER = [
  "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
  "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
  "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]

// --- PDF 模块相关 ---
const pdfList = ref([])
const pdfSearchQuery = ref('')
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

const filteredPdfList = computed(() => {
  if (!pdfSearchQuery.value) return pdfList.value
  return pdfList.value.filter(item => 
    item.filename.toLowerCase().includes(pdfSearchQuery.value.toLowerCase())
  )
})

const openPdfViewer = (filename) => {
  activePdfFile.value = filename
  pdfDialogVisible.value = true
}


// --- DB 数据模块相关 ---
const searchBrand = ref('')
const tableData = ref([])
const activeBrand = ref('')
const selectedStandard = ref(null)

const isEditing = ref(false)
const saving = ref(false)
const editFormData = ref({})

const fetchStandards = async () => {
  const { data } = await searchStandards({ brand_name: searchBrand.value })
  tableData.value = data.items || []
  if (!activeBrand.value) {
    selectedStandard.value = null
    isEditing.value = false
  }
}

const handleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeBrand.value = currentRow.brand_name
  isEditing.value = false
  
  const { data } = await getStandardDetail({ brand_name: currentRow.brand_name })
  if (data.success) {
    selectedStandard.value = data.standard
  }
}

// 提取有数据的行，用于视图模式显示
const viewGridData = computed(() => {
  if (!selectedStandard.value || !selectedStandard.value.tech_req) return []
  return ELEMENTS_ORDER.filter(el => {
    const v = selectedStandard.value.tech_req[el]
    return v && (v.tech_min || v.tech_max || v.ctrl_min || v.ctrl_max)
  }).map(el => ({
    element: el,
    ...selectedStandard.value.tech_req[el]
  }))
})

// 进入编辑模式时，初始化 29 个元素的表单模型
const enterEditMode = () => {
  const initData = {}
  ELEMENTS_ORDER.forEach(el => {
    initData[el] = { tech_min: '', ctrl_min: '', ctrl_max: '', tech_max: '' }
  })
  
  if (selectedStandard.value && selectedStandard.value.tech_req) {
    Object.entries(selectedStandard.value.tech_req).forEach(([el, vals]) => {
      if (initData[el] && typeof vals === 'object') {
        initData[el] = { ...initData[el], ...vals }
      }
    })
  }
  
  editFormData.value = initData
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

// 保存数据
const saveEdit = async () => {
  saving.value = true
  
  // 过滤掉完全没填的空行数据，减轻数据库负担
  const validElements = {}
  Object.entries(editFormData.value).forEach(([el, vals]) => {
    if (vals.tech_min || vals.ctrl_min || vals.ctrl_max || vals.tech_max) {
      validElements[el] = vals
    }
  })
  
  const payload = {
    brand_name: activeBrand.value,
    elements: validElements
  }
  
  try {
    const { data } = await saveStandardDetail(payload)
    if (data.success) {
      ElMessage.success('指标保存成功！')
      isEditing.value = false
      // 刷新当前牌号的数据呈现
      handleRowSelect({ brand_name: activeBrand.value })
    }
  } catch (e) {
    ElMessage.error('保存失败，请检查网络或控制台日志')
  } finally {
    saving.value = false
  }
}

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