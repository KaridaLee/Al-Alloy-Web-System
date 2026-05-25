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
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button type="success" link @click="openPdfViewer(row.filename)">查看原件</el-button>
            <el-button type="danger" link @click="handleDeletePdf(row.filename)">删除</el-button>
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
                <div v-else style="display: flex; gap: 8px;">
                  <el-button type="warning" size="small" @click="importJsonDialogVisible = true">导入 JSON</el-button>
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

    <div style="font-size: 18px; font-weight: 700; margin-top: 32px; margin-bottom: 12px; color: #1e293b;">
      标准样品基础管理
    </div>
    
    <el-row :gutter="18">
      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; flex-direction: column; gap: 10px;">
              <span style="font-weight:700;">标准样品自主建立名册</span>
              <div style="display:flex; gap: 8px;">
                <el-input
                  v-model="newSampleName"
                  placeholder="输入新样品编码/名称"
                  size="small"
                  clearable
                />
                <el-button type="primary" size="small" @click="handleAddSample">添加建档</el-button>
              </div>
            </div>
          </template>

          <el-table 
            :data="sampleTableData" 
            border 
            stripe 
            highlight-current-row
            style="width:100%; cursor:pointer;"
            max-height="500"
            @current-change="handleSampleRowSelect"
          >
            <el-table-column prop="sample_name" label="样品名称" />
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click.stop="handleRenameSample(row)">重命名</el-button>
                <el-button type="danger" link size="small" @click.stop="handleDeleteSample(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="font-weight:700; color: #1e293b;">
                {{ activeSample ? `【${activeSample}】各化学元素含量标准值 (%)` : '请在左侧选择或创建一个标准样品' }}
              </div>
              <div v-if="activeSample">
                <el-button v-if="!isSampleEditing" type="primary" size="small" @click="enterSampleEditMode">
                  编辑标准值
                </el-button>
                <div v-else style="display: flex; gap: 8px;">
                  <el-button size="small" @click="cancelSampleEdit">取消</el-button>
                  <el-button type="success" size="small" :loading="sampleSaving" @click="saveSampleEdit">
                    保存至样品库
                  </el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-if="activeSample">
            <el-table v-if="!isSampleEditing" :data="sampleViewGridData" border stripe style="width:100%;" max-height="500">
              <el-table-column prop="element" label="元素符号" align="center" width="150">
                <template #default="{ row }"><strong>{{ row.element }}</strong></template>
              </el-table-column>
              <el-table-column prop="value" label="标准参考含量值 (%)" align="center" />
            </el-table>
            
            <div v-if="!isSampleEditing && sampleViewGridData.length === 0" style="text-align: center; color: #94a3b8; padding: 40px 0;">
              该样品暂未录入任何元素的具体参考值，请点击右上角进行编辑。
            </div>

            <el-table v-if="isSampleEditing" :data="ELEMENTS_ORDER" border stripe size="small" style="width:100%;" max-height="500">
              <el-table-column label="元素符号" align="center" width="150">
                <template #default="{ row }"><strong>{{ row }}</strong></template>
              </el-table-column>
              <el-table-column label="标准含量输入值 (%)" align="center">
                <template #default="{ row }">
                  <el-input v-model="sampleEditFormData[row]" placeholder="未检出 / 不作要求请留空" clearable />
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-empty v-else description="请先在左侧名册中选定某个标准样品以展现数据矩阵"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <div style="font-size: 18px; font-weight: 700; margin-top: 32px; margin-bottom: 12px; color: #1e293b;">
      标准样品智能推荐系统
    </div>
    
    <el-row :gutter="18" style="margin-bottom: 40px;">
      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <span style="font-weight:700;">1. 设置目标元素参数</span>
          </template>
          
          <div v-for="(item, index) in targetElements" :key="index" style="display:flex; gap:8px; margin-bottom:12px;">
            <el-select v-model="item.element" placeholder="选择元素" style="width: 120px;">
              <el-option 
                v-for="el in ELEMENTS_ORDER" 
                :key="el" 
                :label="el" 
                :value="el" 
                :disabled="isElementSelected(el, index)" 
              />
            </el-select>
            <el-input v-model="item.value" placeholder="目标值 (%)" type="number" style="flex: 1;" />
            <el-button type="danger" circle @click="removeTargetElement(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          
          <el-button type="primary" plain style="width: 100%; margin-bottom: 16px;" @click="addTargetElement">
            + 添加目标元素
          </el-button>
          
          <el-button type="success" style="width: 100%;" @click="handleMatchSamples" :loading="matching">
            🔍 智能检索最佳标样
          </el-button>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="block-card" style="min-height: 250px;">
          <template #header>
            <span style="font-weight:700;">2. 智能匹配推荐结果 (Top 3)</span>
          </template>
          
          <div v-if="matchResults.length > 0">
            <el-card 
              v-for="(res, idx) in matchResults" 
              :key="idx" 
              style="margin-bottom: 16px; border: 1px solid #e2e8f0;" 
              shadow="hover"
            >
              <template #header>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="font-weight:700; color: #1e293b; font-size: 16px;">
                    {{ idx === 0 ? '🏆 最佳匹配' : (idx === 1 ? '🥈 优选备用 1' : '🥉 优选备用 2') }} : {{ res.sample_name }}
                  </span>
                  <el-tag :type="idx === 0 ? 'success' : (idx === 1 ? 'warning' : 'info')" size="large" effect="dark">
                    综合匹配度: {{ res.match_rate }}%
                  </el-tag>
                </div>
              </template>
              
              <el-table :data="getMatchDetailData(res)" border stripe size="small">
                <el-table-column prop="element" label="元素" width="80" align="center">
                  <template #default="{ row }"><strong>{{ row.element }}</strong></template>
                </el-table-column>
                <el-table-column prop="target" label="目标值 (%)" align="center" />
                <el-table-column prop="sample" label="标样实际值 (%)" align="center" />
                <el-table-column prop="diff" label="相对误差 (标样比目标)" align="center">
                  <template #default="{ row }">
                    <span :style="{ color: row.diff === 0 ? '#10b981' : (row.diff > 0 ? '#f59e0b' : '#3b82f6'), fontWeight: 'bold' }">
                      {{ row.diff > 0 ? '+' : '' }}{{ row.diff }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
          <el-empty v-else description="请先在左侧输入产品目标值并点击智能匹配"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="pdfDialogVisible" :title="'原件预览：' + activePdfFile" width="75%" top="5vh" destroy-on-close>
      <div style="height: 75vh; border: 1px solid #e2e8f0; border-radius: 4px;">
        <iframe v-if="activePdfFile" :src="'/api/search/standards/pdfs/' + encodeURIComponent(activePdfFile)" width="100%" height="100%" frameborder="0" style="display: block;"></iframe>
      </div>
    </el-dialog>

    <el-dialog v-model="importJsonDialogVisible" title="导入 JSON 配置数据" width="50%" destroy-on-close>
      <div style="margin-bottom: 12px; font-size: 13px; color: #64748b;">
        请将符合格式要求的 JSON 文本粘贴在下方，系统会自动解析范围规则。
      </div>
      <el-input v-model="jsonInputData" type="textarea" :rows="12" placeholder='{"牌号命名":"...", "化学成分":{"Si":{"技术要求":"11.0-12.5","内控要求":"11.2-11.8"}}}' />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importJsonDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleImportJson">解析并填入表单</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue' // 新引入了 Delete 图标
import { 
  searchStandards, getStandardDetail, getStandardPdfs, saveStandardDetail,
  getStandardSamples, getStandardSampleDetail, saveStandardSample, deleteStandardSample,
  deleteStandardPdf, renameStandardSample, matchStandardSample // 引入智能匹配 API
} from '../api'

const ELEMENTS_ORDER = [
  "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
  "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
  "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]

// === PDF 处理 ===
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
  let list = [...pdfList.value]
  if (pdfSearchQuery.value) {
    list = list.filter(item => item.filename.toLowerCase().includes(pdfSearchQuery.value.toLowerCase()))
  }
  return list.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' }))
})

const openPdfViewer = (filename) => {
  activePdfFile.value = filename
  pdfDialogVisible.value = true
}

const handleDeletePdf = async (filename) => {
  try {
    await ElMessageBox.confirm(`确定要从服务器彻底删除原件【${filename}】吗？此操作无法恢复。`, '危险操作确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    const { data } = await deleteStandardPdf({ filename })
    if (data.success) {
      ElMessage.success(data.message)
      await fetchPdfList()
    } else {
      ElMessage.error(data.message)
    }
  } catch (e) {}
}

// === 企标范围处理 ===
const searchBrand = ref('')
const tableData = ref([])
const activeBrand = ref('')
const selectedStandard = ref(null)
const isEditing = ref(false)
const saving = ref(false)
const editFormData = ref({})
const importJsonDialogVisible = ref(false)
const jsonInputData = ref('')

const fetchStandards = async () => {
  const { data } = await searchStandards({ brand_name: searchBrand.value })
  const items = data.items || []
  items.sort((a, b) => a.brand_name.localeCompare(b.brand_name, undefined, { numeric: true, sensitivity: 'base' }))
  tableData.value = items
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

const viewGridData = computed(() => {
  if (!selectedStandard.value || !selectedStandard.value.tech_req) return []
  return ELEMENTS_ORDER.filter(el => {
    const v = selectedStandard.value.tech_req[el]
    return v && (v.tech_min || v.tech_max || v.ctrl_min || v.ctrl_max)
  }).map(el => ({ element: el, ...selectedStandard.value.tech_req[el] }))
})

const enterEditMode = () => {
  const initData = {}
  ELEMENTS_ORDER.forEach(el => initData[el] = { tech_min: '', ctrl_min: '', ctrl_max: '', tech_max: '' })
  if (selectedStandard.value && selectedStandard.value.tech_req) {
    Object.entries(selectedStandard.value.tech_req).forEach(([el, vals]) => {
      if (initData[el] && typeof vals === 'object') initData[el] = { ...initData[el], ...vals }
    })
  }
  editFormData.value = initData
  isEditing.value = true
}

const cancelEdit = () => isEditing.value = false

const parseRangeString = (strVal) => {
  let min = '', max = ''
  if (!strVal || strVal === '-' || strVal === '—') return { min, max }
  const cleanedVal = strVal.trim()
  if (cleanedVal.includes('-')) {
    const parts = cleanedVal.split('-')
    min = parts[0].trim()
    max = parts[1].trim()
  } else if (cleanedVal.includes('≤')) {
    min = '0'
    max = cleanedVal.replace('≤', '').trim()
  } else if (cleanedVal.includes('<')) {
    min = '0'
    max = cleanedVal.replace('<', '').trim()
  } else {
    max = cleanedVal
  }
  return { min, max }
}

const handleImportJson = () => {
  if (!jsonInputData.value) return ElMessage.warning('请输入 JSON 数据')
  try {
    const parsedData = JSON.parse(jsonInputData.value)
    const chemData = parsedData['化学成分'] || parsedData['成分要求']
    if (!chemData) return ElMessage.warning('未在 JSON 中找到“化学成分”字段')
    
    let importedCount = 0
    Object.entries(chemData).forEach(([el, rules]) => {
      if (editFormData.value[el]) {
        const techObj = parseRangeString(rules['技术要求'] || '')
        const ctrlObj = parseRangeString(rules['内控要求'] || '')
        editFormData.value[el].tech_min = techObj.min
        editFormData.value[el].tech_max = techObj.max
        editFormData.value[el].ctrl_min = ctrlObj.min
        editFormData.value[el].ctrl_max = ctrlObj.max
        importedCount++
      }
    })
    ElMessage.success(`解析成功 ${importedCount} 条（点击“保存至数据库”生效）`)
    importJsonDialogVisible.value = false
    jsonInputData.value = ''
  } catch (error) {
    ElMessage.error('JSON 格式异常')
  }
}

const saveEdit = async () => {
  saving.value = true
  const validElements = {}
  Object.entries(editFormData.value).forEach(([el, vals]) => {
    if (vals.tech_min || vals.ctrl_min || vals.ctrl_max || vals.tech_max) validElements[el] = vals
  })
  try {
    const { data } = await saveStandardDetail({ brand_name: activeBrand.value, elements: validElements })
    if (data.success) {
      ElMessage.success('保存成功！')
      isEditing.value = false
      handleRowSelect({ brand_name: activeBrand.value })
    }
  } catch (e) {
    ElMessage.error('保存异常')
  } finally {
    saving.value = false
  }
}

// === 标准样品库处理 ===
const sampleTableData = ref([])
const newSampleName = ref('')
const activeSample = ref('')
const selectedSampleValues = ref({})
const isSampleEditing = ref(false)
const sampleSaving = ref(false)
const sampleEditFormData = ref({})

const fetchSamples = async () => {
  try {
    const { data } = await getStandardSamples()
    const items = data.items || []
    items.sort((a, b) => a.sample_name.localeCompare(b.sample_name, undefined, { numeric: true, sensitivity: 'base' }))
    sampleTableData.value = items
  } catch (e) {}
}

const handleSampleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeSample.value = currentRow.sample_name
  isSampleEditing.value = false
  try {
    const { data } = await getStandardSampleDetail({ sample_name: currentRow.sample_name })
    if (data.success) selectedSampleValues.value = data.values || {}
  } catch (e) {}
}

const sampleViewGridData = computed(() => {
  if (!selectedSampleValues.value) return []
  return ELEMENTS_ORDER.filter(el => {
    const val = selectedSampleValues.value[el]
    return val !== undefined && val !== null && val !== ''
  }).map(el => ({ element: el, value: selectedSampleValues.value[el] }))
})

const handleAddSample = async () => {
  const name = newSampleName.value.trim()
  if (!name) return ElMessage.warning('请输入名称')
  if (sampleTableData.value.some(s => s.sample_name.toLowerCase() === name.toLowerCase())) {
    return ElMessage.warning('不可建立同名样品档案')
  }
  try {
    const { data } = await saveStandardSample({ sample_name: name, elements: {} })
    if (data.success) {
      ElMessage.success('建立成功')
      newSampleName.value = ''
      await fetchSamples()
    }
  } catch (e) {}
}

const handleRenameSample = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(`当前正在重命名【${row.sample_name}】`, '标准样品重命名', {
      confirmButtonText: '保存更改',
      cancelButtonText: '取消',
      inputValue: row.sample_name,
      inputPattern: /\S+/,
      inputErrorMessage: '样品名称不能为空格'
    })
    if (value && value.trim() !== row.sample_name) {
      const { data } = await renameStandardSample({ old_name: row.sample_name, new_name: value.trim() })
      if (data.success) {
        ElMessage.success('重命名成功')
        if (activeSample.value === row.sample_name) activeSample.value = value.trim()
        await fetchSamples()
      } else {
        ElMessage.error(data.message)
      }
    }
  } catch (e) {}
}

const handleDeleteSample = async (row) => {
  try {
    await ElMessageBox.confirm(`永久删除样品【${row.sample_name}】的所有记录？`, '警告', { type: 'warning' })
    const { data } = await deleteStandardSample({ sample_name: row.sample_name })
    if (data.success) {
      ElMessage.success('已删除')
      if (activeSample.value === row.sample_name) {
        activeSample.value = ''
        selectedSampleValues.value = {}
        isSampleEditing.value = false
      }
      await fetchSamples()
    }
  } catch (e) {}
}

const enterSampleEditMode = () => {
  const initData = {}
  ELEMENTS_ORDER.forEach(el => initData[el] = selectedSampleValues.value[el] || '')
  sampleEditFormData.value = initData
  isSampleEditing.value = true
}

const cancelSampleEdit = () => isSampleEditing.value = false

const saveSampleEdit = async () => {
  sampleSaving.value = true
  try {
    const { data } = await saveStandardSample({ sample_name: activeSample.value, elements: sampleEditFormData.value })
    if (data.success) {
      ElMessage.success('保存成功')
      isSampleEditing.value = false
      const detailRes = await getStandardSampleDetail({ sample_name: activeSample.value })
      selectedSampleValues.value = detailRes.data.values || {}
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    sampleSaving.value = false
  }
}

// === 智能标样匹配处理逻辑 ===
const targetElements = ref([{ element: '', value: '' }])
const matchResults = ref([])
const matching = ref(false)

const isElementSelected = (el, currentIndex) => {
  return targetElements.value.some((item, idx) => idx !== currentIndex && item.element === el)
}

const addTargetElement = () => {
  targetElements.value.push({ element: '', value: '' })
}

const removeTargetElement = (index) => {
  targetElements.value.splice(index, 1)
}

const handleMatchSamples = async () => {
  const payloadTargets = {}
  for (const item of targetElements.value) {
    if (item.element && item.value !== '') {
      payloadTargets[item.element] = parseFloat(item.value)
    }
  }

  if (Object.keys(payloadTargets).length === 0) {
    ElMessage.warning('请至少输入一个有效的目标元素和数值！')
    return
  }

  matching.value = true
  try {
    const { data } = await matchStandardSample({ targets: payloadTargets })
    if (data.success) {
      matchResults.value = data.items || []
      if (matchResults.value.length === 0) {
        ElMessage.info('您的系统库中暂未录入任何标准样品数据，无法进行匹配。')
      } else {
        ElMessage.success('检索完毕！请查看右侧推荐结果。')
      }
    } else {
      ElMessage.error(data.message || '系统匹配算法出现故障')
    }
  } catch (e) {
    ElMessage.error('网络或服务器响应错误')
  } finally {
    matching.value = false
  }
}

const getMatchDetailData = (res) => {
  return Object.keys(res.detail_diff).map(el => ({
    element: el,
    target: res.detail_diff[el].target,
    sample: res.detail_diff[el].sample,
    diff: res.detail_diff[el].diff
  }))
}

onMounted(() => {
  fetchPdfList()
  fetchStandards()
  fetchSamples()
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