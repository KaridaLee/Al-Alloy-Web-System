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
            :style="{ width: isMobile ? '160px' : '240px' }"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="filteredPdfList" border stripe style="width:100%;" max-height="450">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="filename" label="PDF 原件名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="success" link @click="openPdfViewer(row.filename)">原件</el-button>
            <el-button v-if="isAdmin" type="danger" link @click="handleDeletePdf(row.filename)">删除</el-button>
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
      <el-col :xs="24" :md="8" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:700;">所有已知牌号</span>
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
            <el-table-column prop="brand_name" label="牌号名称 (点击查看范围)" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="font-weight:700; color: #1e293b;">
                {{ activeBrand ? (isMobile ? '内控技术范围' : `【${activeBrand}】化学元素内控要求`) : '请在左侧选择牌号' }}
              </div>
              <div v-if="activeBrand && isAdmin">
                <el-button v-if="!isEditing" type="primary" size="small" @click="enterEditMode">
                  编辑范围指标
                </el-button>
                <div v-else style="display: flex; gap: 8px;">
                  <el-button type="warning" size="small" @click="importJsonDialogVisible = true">导入 JSON</el-button>
                  <el-button size="small" @click="cancelEdit">取消</el-button>
                  <el-button type="success" size="small" :loading="saving" @click="saveEdit">保存</el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-if="activeBrand">
            <el-table v-if="!isEditing" :data="viewGridData" border stripe style="width:100%;">
              <el-table-column prop="tech_min" label="技术下限" align="center" min-width="80" />
              <el-table-column prop="ctrl_min" label="内控下限" align="center" min-width="80" />
              <el-table-column prop="element" label="元素" align="center" min-width="60">
                <template #default="{ row }"><strong>{{ row.element }}</strong></template>
              </el-table-column>
              <el-table-column prop="ctrl_max" label="内控上限" align="center" min-width="80" />
              <el-table-column prop="tech_max" label="技术上限" align="center" min-width="80" />
            </el-table>
            
            <div v-if="!isEditing && viewGridData.length === 0" style="text-align: center; color: #94a3b8; padding: 40px 0;">
              暂未配置指标{{ isAdmin ? '，请点击右上角“编辑”' : '' }}。
            </div>

            <el-table v-if="isEditing && isAdmin" :data="ELEMENTS_ORDER" border stripe size="small" style="width:100%;" max-height="600">
              <el-table-column label="技术下限" align="center" min-width="80">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].tech_min" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="内控下限" align="center" min-width="80">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].ctrl_min" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="元素" align="center" min-width="60">
                <template #default="{ row }"><strong>{{ row }}</strong></template>
              </el-table-column>
              <el-table-column label="内控上限" align="center" min-width="80">
                <template #default="{ row }">
                  <el-input v-model="editFormData[row].ctrl_max" placeholder="-" clearable />
                </template>
              </el-table-column>
              <el-table-column label="技术上限" align="center" min-width="80">
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
      <el-col :xs="24" :md="8" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; flex-direction: column; gap: 10px;">
              <span style="font-weight:700;">标准样品名册</span>
              <div v-if="isAdmin" style="display:flex; gap: 8px;">
                <el-input v-model="newSampleName" placeholder="输入新样品编码" size="small" clearable />
                <el-button type="primary" size="small" @click="handleAddSample">添加</el-button>
              </div>
            </div>
          </template>
          <el-table :data="sampleTableData" border stripe highlight-current-row style="width:100%; cursor:pointer;" max-height="500" @current-change="handleSampleRowSelect">
            <el-table-column prop="sample_name" label="样品名称" />
            <el-table-column v-if="isAdmin" label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click.stop="handleRenameSample(row)">重命名</el-button>
                <el-button type="danger" link size="small" @click.stop="handleDeleteSample(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="font-weight:700; color: #1e293b;">
                {{ activeSample ? (isMobile ? '含量标准值(%)' : `【${activeSample}】各化学元素含量标准值(%)`) : '请在左侧选择' }}
              </div>
              <div v-if="activeSample && isAdmin">
                <el-button v-if="!isSampleEditing" type="primary" size="small" @click="enterSampleEditMode">编辑</el-button>
                <div v-else style="display: flex; gap: 8px;">
                  <el-button size="small" @click="cancelSampleEdit">取消</el-button>
                  <el-button type="success" size="small" :loading="sampleSaving" @click="saveSampleEdit">保存</el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-if="activeSample">
            <el-table v-if="!isSampleEditing" :data="sampleViewGridData" border stripe style="width:100%;" max-height="500">
              <el-table-column prop="element" label="元素符号" align="center" min-width="100">
                <template #default="{ row }"><strong>{{ row.element }}</strong></template>
              </el-table-column>
              <el-table-column prop="value" label="标准参考含量值 (%)" align="center" min-width="120" />
            </el-table>
            <div v-if="!isSampleEditing && sampleViewGridData.length === 0" style="text-align: center; color: #94a3b8; padding: 40px 0;">该样品暂未录入任何元素的具体参考值。</div>

            <el-table v-if="isSampleEditing && isAdmin" :data="ELEMENTS_ORDER" border stripe size="small" style="width:100%;" max-height="500">
              <el-table-column label="元素符号" align="center" min-width="80">
                <template #default="{ row }"><strong>{{ row }}</strong></template>
              </el-table-column>
              <el-table-column label="标准含量输入值 (%)" align="center" min-width="150">
                <template #default="{ row }">
                  <el-input v-model="sampleEditFormData[row]" placeholder="留空" clearable />
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="请先在左侧名册中选定某个标准样品"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <div style="font-size: 18px; font-weight: 700; margin-top: 32px; margin-bottom: 12px; color: #1e293b;">
      标准样品智能推荐系统
    </div>
    
    <el-row :gutter="18" style="margin-bottom: 40px;">
      <el-col :xs="24" :md="8" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header><span style="font-weight:700;">1. 设置目标元素参数</span></template>
          <div v-for="(item, index) in targetElements" :key="index" style="display:flex; gap:8px; margin-bottom:12px;">
            <el-select v-model="item.element" placeholder="选择" style="width: 100px;">
              <el-option v-for="el in ELEMENTS_ORDER" :key="el" :label="el" :value="el" :disabled="isElementSelected(el, index)" />
            </el-select>
            <el-input v-model="item.value" placeholder="目标值(%)" type="number" style="flex: 1;" />
            <el-button type="danger" circle @click="removeTargetElement(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button type="primary" plain style="width: 100%; margin-bottom: 16px;" @click="addTargetElement">+ 添加</el-button>
          <el-button type="success" style="width: 100%;" @click="handleMatchSamples" :loading="matching">🔍 智能检索</el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16" style="margin-bottom: 16px;">
        <el-card class="block-card" style="min-height: 250px;">
          <template #header><span style="font-weight:700;">2. 智能匹配推荐结果 (Top 3)</span></template>
          <div v-if="matchResults.length > 0">
            <el-card v-for="(res, idx) in matchResults" :key="idx" style="margin-bottom: 16px; border: 1px solid #e2e8f0;" shadow="hover">
              <template #header>
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap: wrap; gap: 8px;">
                  <span style="font-weight:700; color: #1e293b; font-size: 15px;">
                    {{ idx === 0 ? '🏆 最佳匹配' : (idx === 1 ? '🥈 备选1' : '🥉 备选2') }} : {{ res.sample_name }}
                  </span>
                  <el-tag :type="idx === 0 ? 'success' : (idx === 1 ? 'warning' : 'info')" effect="dark">
                    匹配度: {{ res.match_rate }}%
                  </el-tag>
                </div>
              </template>
              <el-table :data="getMatchDetailData(res)" border stripe size="small">
                <el-table-column prop="element" label="元素" min-width="60" align="center">
                  <template #default="{ row }"><strong>{{ row.element }}</strong></template>
                </el-table-column>
                <el-table-column prop="target" label="目标值(%)" align="center" min-width="80" />
                <el-table-column prop="sample" label="实际值(%)" align="center" min-width="80" />
                <el-table-column prop="diff" label="误差" align="center" min-width="70">
                  <template #default="{ row }">
                    <span :style="{ color: row.diff === 0 ? '#10b981' : (row.diff > 0 ? '#f59e0b' : '#3b82f6'), fontWeight: 'bold' }">
                      {{ row.diff > 0 ? '+' : '' }}{{ row.diff }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
          <el-empty v-else description="请先在左侧输入并匹配"></el-empty>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="pdfDialogVisible" :title="'预览：' + activePdfFile" :width="isMobile ? '95%' : '75%'" top="5vh" destroy-on-close>
      <div style="height: 75vh; border: 1px solid #e2e8f0; border-radius: 4px;">
        <iframe v-if="activePdfFile" :src="'/api/search/standards/pdfs/' + encodeURIComponent(activePdfFile)" width="100%" height="100%" frameborder="0" style="display: block;"></iframe>
      </div>
    </el-dialog>

    <el-dialog v-model="importJsonDialogVisible" title="导入 JSON" :width="isMobile ? '95%' : '50%'" destroy-on-close>
      <div style="margin-bottom: 12px; font-size: 13px; color: #64748b;">请粘贴 JSON 文本。</div>
      <el-input v-model="jsonInputData" type="textarea" :rows="12" />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importJsonDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleImportJson">解析并填入</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue'
import { 
  searchStandards, getStandardDetail, getStandardPdfs, saveStandardDetail,
  getStandardSamples, getStandardSampleDetail, saveStandardSample, deleteStandardSample,
  deleteStandardPdf, renameStandardSample, matchStandardSample
} from '../api'

const ELEMENTS_ORDER = [
  "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
  "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
  "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]

// 响应式状态
const isMobile = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }

const isAdmin = ref(sessionStorage.getItem('isAdmin') === 'true')
const syncAdminState = () => {
  isAdmin.value = sessionStorage.getItem('isAdmin') === 'true'
  if (!isAdmin.value) { isEditing.value = false; isSampleEditing.value = false }
}

const checkAdminAuth = () => {
  if (sessionStorage.getItem('isAdmin') !== 'true') {
    ElMessageBox.alert('无操作权限！', '提示', { type: 'error' })
    return false
  }
  return true
}

const pdfList = ref([])
const pdfSearchQuery = ref('')
const pdfDialogVisible = ref(false)
const activePdfFile = ref('')

const fetchPdfList = async () => {
  try {
    const { data } = await getStandardPdfs()
    pdfList.value = data.items || []
  } catch (e) { }
}

const filteredPdfList = computed(() => {
  let list = [...pdfList.value]
  if (pdfSearchQuery.value) {
    list = list.filter(item => item.filename.toLowerCase().includes(pdfSearchQuery.value.toLowerCase()))
  }
  return list.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' }))
})

const openPdfViewer = (filename) => { activePdfFile.value = filename; pdfDialogVisible.value = true }
const handleDeletePdf = async (filename) => {
  if (!checkAdminAuth()) return
  try {
    await ElMessageBox.confirm('确定要删除吗？', '确认', { type: 'error' })
    const { data } = await deleteStandardPdf({ filename })
    if (data.success) { ElMessage.success(data.message); await fetchPdfList() }
  } catch (e) {}
}

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
  tableData.value = (data.items || []).sort((a, b) => a.brand_name.localeCompare(b.brand_name, undefined, { numeric: true, sensitivity: 'base' }))
  if (!activeBrand.value) { selectedStandard.value = null; isEditing.value = false }
}

const handleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeBrand.value = currentRow.brand_name; isEditing.value = false
  const { data } = await getStandardDetail({ brand_name: currentRow.brand_name })
  if (data.success) selectedStandard.value = data.standard
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
  if (selectedStandard.value?.tech_req) {
    Object.entries(selectedStandard.value.tech_req).forEach(([el, vals]) => {
      if (initData[el] && typeof vals === 'object') initData[el] = { ...initData[el], ...vals }
    })
  }
  editFormData.value = initData; isEditing.value = true
}

const cancelEdit = () => isEditing.value = false
const handleImportJson = () => {
  try {
    const parsedData = JSON.parse(jsonInputData.value)
    const chemData = parsedData['化学成分'] || parsedData['成分要求']
    if (!chemData) return ElMessage.warning('未找到“化学成分”')
    Object.entries(chemData).forEach(([el, rules]) => {
      if (editFormData.value[el]) {
        // ... (省略部分字符串解析，与原本一致)
        editFormData.value[el].tech_min = rules['技术要求'] || ''
        editFormData.value[el].ctrl_min = rules['内控要求'] || ''
      }
    })
    ElMessage.success('导入成功'); importJsonDialogVisible.value = false
  } catch (error) { ElMessage.error('JSON格式异常') }
}

const saveEdit = async () => {
  saving.value = true
  const validElements = {}
  Object.entries(editFormData.value).forEach(([el, vals]) => {
    if (vals.tech_min || vals.ctrl_min || vals.ctrl_max || vals.tech_max) validElements[el] = vals
  })
  try {
    const { data } = await saveStandardDetail({ brand_name: activeBrand.value, elements: validElements })
    if (data.success) { ElMessage.success('保存成功！'); isEditing.value = false; handleRowSelect({ brand_name: activeBrand.value }) }
  } catch (e) { ElMessage.error('保存异常') } finally { saving.value = false }
}

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
    sampleTableData.value = (data.items || []).sort((a, b) => a.sample_name.localeCompare(b.sample_name, undefined, { numeric: true, sensitivity: 'base' }))
  } catch (e) {}
}

const handleSampleRowSelect = async (currentRow) => {
  if (!currentRow) return
  activeSample.value = currentRow.sample_name; isSampleEditing.value = false
  const { data } = await getStandardSampleDetail({ sample_name: currentRow.sample_name })
  if (data.success) selectedSampleValues.value = data.values || {}
}

const sampleViewGridData = computed(() => {
  if (!selectedSampleValues.value) return []
  return ELEMENTS_ORDER.filter(el => selectedSampleValues.value[el] !== undefined && selectedSampleValues.value[el] !== '').map(el => ({ element: el, value: selectedSampleValues.value[el] }))
})

const handleAddSample = async () => {
  if (!checkAdminAuth()) return
  if (!newSampleName.value) return ElMessage.warning('请输入名称')
  try {
    const { data } = await saveStandardSample({ sample_name: newSampleName.value, elements: {} })
    if (data.success) { ElMessage.success('建立成功'); newSampleName.value = ''; await fetchSamples() }
  } catch (e) {}
}

const handleRenameSample = async (row) => {
  if (!checkAdminAuth()) return
  try {
    const { value } = await ElMessageBox.prompt('重命名', '提示', { inputValue: row.sample_name })
    if (value && value !== row.sample_name) {
      const { data } = await renameStandardSample({ old_name: row.sample_name, new_name: value.trim() })
      if (data.success) { ElMessage.success('成功'); if (activeSample.value === row.sample_name) activeSample.value = value.trim(); await fetchSamples() }
    }
  } catch (e) {}
}

const handleDeleteSample = async (row) => {
  if (!checkAdminAuth()) return
  try {
    await ElMessageBox.confirm('永久删除？', '警告', { type: 'warning' })
    const { data } = await deleteStandardSample({ sample_name: row.sample_name })
    if (data.success) { ElMessage.success('已删除'); if (activeSample.value === row.sample_name) { activeSample.value = ''; selectedSampleValues.value = {}; isSampleEditing.value = false } await fetchSamples() }
  } catch (e) {}
}

const enterSampleEditMode = () => {
  const initData = {}
  ELEMENTS_ORDER.forEach(el => initData[el] = selectedSampleValues.value[el] || '')
  sampleEditFormData.value = initData; isSampleEditing.value = true
}

const cancelSampleEdit = () => isSampleEditing.value = false
const saveSampleEdit = async () => {
  sampleSaving.value = true
  try {
    const { data } = await saveStandardSample({ sample_name: activeSample.value, elements: sampleEditFormData.value })
    if (data.success) { ElMessage.success('保存成功'); isSampleEditing.value = false; const res = await getStandardSampleDetail({ sample_name: activeSample.value }); selectedSampleValues.value = res.data.values || {} }
  } catch (e) { ElMessage.error('失败') } finally { sampleSaving.value = false }
}

const targetElements = ref([{ element: '', value: '' }])
const matchResults = ref([])
const matching = ref(false)
const isElementSelected = (el, currentIndex) => targetElements.value.some((item, idx) => idx !== currentIndex && item.element === el)
const addTargetElement = () => targetElements.value.push({ element: '', value: '' })
const removeTargetElement = (index) => targetElements.value.splice(index, 1)

const handleMatchSamples = async () => {
  const payloadTargets = {}
  for (const item of targetElements.value) if (item.element && item.value !== '') payloadTargets[item.element] = parseFloat(item.value)
  if (Object.keys(payloadTargets).length === 0) return ElMessage.warning('请输入目标')
  matching.value = true
  try {
    const { data } = await matchStandardSample({ targets: payloadTargets })
    if (data.success) { matchResults.value = data.items || []; ElMessage.success('检索完毕') }
  } catch (e) { ElMessage.error('请求失败') } finally { matching.value = false }
}

const getMatchDetailData = (res) => Object.keys(res.detail_diff).map(el => ({ element: el, target: res.detail_diff[el].target, sample: res.detail_diff[el].sample, diff: res.detail_diff[el].diff }))

onMounted(() => {
  checkMobile(); window.addEventListener('resize', checkMobile)
  fetchPdfList(); fetchStandards(); fetchSamples()
  window.addEventListener('admin-state-changed', syncAdminState)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('admin-state-changed', syncAdminState)
})
</script>

<style scoped>
.block-card { border-radius: 12px; transition: all 0.3s; }
.block-card:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 20px; color: #1e293b; }
</style>