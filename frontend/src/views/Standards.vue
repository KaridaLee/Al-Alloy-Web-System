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
      标准样品数据管理
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
            <el-table-column prop="sample_name" label="样品名称 (点击配置内部标准值)" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
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

    <el-dialog
      v-model="importJsonDialogVisible"
      title="导入 JSON 配置数据"
      width="50%"
      destroy-on-close
    >
      <div style="margin-bottom: 12px; font-size: 13px; color: #64748b;">
        请将符合格式要求的 JSON 文本粘贴在下方，系统会自动解析范围规则（如 ≤ 会自动解析下限为 0）。
      </div>
      <el-input
        v-model="jsonInputData"
        type="textarea"
        :rows="12"
        placeholder='{"牌号命名":"...", "化学成分":{"Si":{"技术要求":"11.0-12.5","内控要求":"11.2-11.8"}}}'
      />
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
import { Search } from '@element-plus/icons-vue'
import { 
  searchStandards, getStandardDetail, getStandardPdfs, saveStandardDetail,
  getStandardSamples, getStandardSampleDetail, saveStandardSample, deleteStandardSample
} from '../api'

const ELEMENTS_ORDER = [
  "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
  "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
  "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]

// ==============================================================================
// 1. PDF 企标原件库逻辑
// ==============================================================================
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
    list = list.filter(item => 
      item.filename.toLowerCase().includes(pdfSearchQuery.value.toLowerCase())
    )
  }
  // 自然文本和数字混合排序引擎 (如 标样22 会排在 标样3 后面)
  return list.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' }))
})

const openPdfViewer = (filename) => {
  activePdfFile.value = filename
  pdfDialogVisible.value = true
}


// ==============================================================================
// 2. 企业标准指标范围配置逻辑
// ==============================================================================
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
  
  // 自然序列正序重新排列企业牌号名
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
  }).map(el => ({
    element: el,
    ...selectedStandard.value.tech_req[el]
  }))
})

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

const parseRangeString = (strVal) => {
  let min = ''
  let max = ''
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
  if (!jsonInputData.value) {
    ElMessage.warning('请输入 JSON 数据')
    return
  }
  
  try {
    const parsedData = JSON.parse(jsonInputData.value)
    const chemData = parsedData['化学成分'] || parsedData['成分要求']
    
    if (!chemData) {
      ElMessage.warning('未在 JSON 中找到“化学成分”字段')
      return
    }
    
    if (parsedData['牌号命名'] && !parsedData['牌号命名'].includes(activeBrand.value) && !activeBrand.value.includes(parsedData['牌号命名'])) {
      ElMessage.warning(`提示：JSON牌号【${parsedData['牌号命名']}】与当前所选【${activeBrand.value}】似乎不一致`)
    }
    
    let importedCount = 0
    Object.entries(chemData).forEach(([el, rules]) => {
      if (editFormData.value[el]) {
        const techStr = rules['技术要求'] || ''
        const ctrlStr = rules['内控要求'] || ''
        
        const techObj = parseRangeString(techStr)
        const ctrlObj = parseRangeString(ctrlStr)
        
        editFormData.value[el].tech_min = techObj.min
        editFormData.value[el].tech_max = techObj.max
        editFormData.value[el].ctrl_min = ctrlObj.min
        editFormData.value[el].ctrl_max = ctrlObj.max
        importedCount++
      }
    })
    
    ElMessage.success(`导入成功，共解析了 ${importedCount} 个元素的指标（点击“保存至数据库”生效）`)
    importJsonDialogVisible.value = false
    jsonInputData.value = ''
    
  } catch (error) {
    ElMessage.error('JSON 格式异常，请检查是否符合标准的键值对规范！')
    console.error(error)
  }
}

const saveEdit = async () => {
  saving.value = true
  
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
      handleRowSelect({ brand_name: activeBrand.value })
    }
  } catch (e) {
    ElMessage.error('保存失败，请检查网络或控制台日志')
  } finally {
    saving.value = false
  }
}


// ==============================================================================
// 3. 新增功能：标准样品自主维护控制流
// ==============================================================================
const sampleTableData = ref([])
const newSampleName = ref('')
const activeSample = ref('')
const selectedSampleValues = ref({})
const isSampleEditing = ref(false)
const sampleSaving = ref(false)
const sampleEditFormData = ref({})

// 获取标准样品名册
const fetchSamples = async () => {
  try {
    const { data } = await getStandardSamples()
    const items = data.items || []
    // 样品名称应用自然文本序列进行前端正序排列
    items.sort((a, b) => a.sample_name.localeCompare(b.sample_name, undefined, { numeric: true, sensitivity: 'base' }))
    sampleTableData.value = items
  } catch (e) {
    console.error('拉取标准样品名册失败:', e)
  }
}

// 选中样品切换右侧面板数据展示
const handleSampleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeSample.value = currentRow.sample_name
  isSampleEditing.value = false
  
  try {
    const { data } = await getStandardSampleDetail({ sample_name: currentRow.sample_name })
    if (data.success) {
      selectedSampleValues.value = data.values || {}
    }
  } catch (e) {
    console.error('拉取指定样品元素参考值失效:', e)
  }
}

// 过滤非空样品元素标准值以构建表格渲染源
const sampleViewGridData = computed(() => {
  if (!selectedSampleValues.value) return []
  return ELEMENTS_ORDER.filter(el => {
    const val = selectedSampleValues.value[el]
    return val !== undefined && val !== null && val !== ''
  }).map(el => ({
    element: el,
    value: selectedSampleValues.value[el]
  }))
})

// 添加新样品建档
const handleAddSample = async () => {
  const name = newSampleName.value.trim()
  if (!name) {
    ElMessage.warning('请输入要创立的标准样品名称或编号')
    return
  }
  if (sampleTableData.value.some(s => s.sample_name.toLowerCase() === name.toLowerCase())) {
    ElMessage.warning('该标准样品编码已在名册中登记，切勿重复录入')
    return
  }
  
  try {
    const { data } = await saveStandardSample({ sample_name: name, elements: {} })
    if (data.success) {
      ElMessage.success(`标准样品【${name}】档案建立成功`)
      newSampleName.value = ''
      await fetchSamples()
    }
  } catch (e) {
    ElMessage.error('样品登记发生网络调用错误')
  }
}

// 移除某个标准样品信息
const handleDeleteSample = async (row) => {
  try {
    await ElMessageBox.confirm(`此操作将永久卸载标准样品【${row.sample_name}】的所有成分指标数据，是否确认？`, '删除警告', {
      confirmButtonText: '强制删除',
      cancelButtonText: '容我想想',
      type: 'warning'
    })
    
    const { data } = await deleteStandardSample({ sample_name: row.sample_name })
    if (data.success) {
      ElMessage.success('该标样档案已成功移除')
      if (activeSample.value === row.sample_name) {
        activeSample.value = ''
        selectedSampleValues.value = {}
        isSampleEditing.value = false
      }
      await fetchSamples()
    }
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

// 进入样品指标修改模式
const enterSampleEditMode = () => {
  const initData = {}
  ELEMENTS_ORDER.forEach(el => {
    initData[el] = selectedSampleValues.value[el] || ''
  })
  sampleEditFormData.value = initData
  isSampleEditing.value = true
}

const cancelSampleEdit = () => {
  isSampleEditing.value = false
}

// 提交样品化学成分录入数据
const saveSampleEdit = async () => {
  sampleSaving.value = true
  try {
    const payload = {
      sample_name: activeSample.value,
      elements: sampleEditFormData.value
    }
    const { data } = await saveStandardSample(payload)
    if (data.success) {
      ElMessage.success('标准参考值入库成功！')
      isSampleEditing.value = false
      
      // 变动完成后立即刷新最新的详情试图
      const detailRes = await getStandardSampleDetail({ sample_name: activeSample.value })
      selectedSampleValues.value = detailRes.data.values || {}
    }
  } catch (e) {
    ElMessage.error('样品指标写入异常')
  } finally {
    sampleSaving.value = false
  }
}


// 生命周期初始化钩子
onMounted(() => {
  fetchPdfList()
  fetchStandards()
  fetchSamples() // 页面初始化自动抓取标样列表
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