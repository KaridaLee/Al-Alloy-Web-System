<template>
  <el-drawer v-model="visibleInner" title="记录详情" size="35%">
    <div v-if="record">
      <el-card class="block-card" style="margin-bottom:16px;">
        <template #header>
          <div style="font-weight:700;">基础信息</div>
        </template>

        <el-table :data="baseInfoRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </el-card>

      <el-card class="block-card" style="margin-bottom:16px;">
        <template #header>
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
            <span style="font-weight:700;">化学成分（%）</span>
            <el-select
              v-model="overrideBrand"
              placeholder="临时套用其他牌号标准"
              size="small"
              style="width: 180px;"
              clearable
              @change="handleOverrideChange"
            >
              <el-option
                v-for="b in allBrands"
                :key="b.brand_name"
                :label="b.brand_name"
                :value="b.brand_name"
              />
            </el-select>
          </div>
        </template>

        <el-table :data="chemistryRows" border stripe style="width:100%;" :cell-style="getCellStyle">
          <el-table-column prop="element" label="元素符号" width="80" align="center">
            <template #default="{ row }"><strong>{{ row.element }}</strong></template>
          </el-table-column>
          <el-table-column prop="tech_min" label="技术下限" align="center" />
          <el-table-column prop="ctrl_min" label="内控下限" align="center" />
          <el-table-column prop="value" label="元素含量" align="center" />
          <el-table-column prop="ctrl_max" label="内控上限" align="center" />
          <el-table-column prop="tech_max" label="技术上限" align="center" />
        </el-table>
      </el-card>

      <el-card v-if="otherRows.length > 0" class="block-card">
        <template #header>
          <div style="font-weight:700;">其他字段</div>
        </template>

        <el-table :data="otherRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </el-card>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getStandardDetail, searchStandards } from '../api'

const props = defineProps({
  modelValue: Boolean,
  record: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['update:modelValue'])

const visibleInner = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const defaultBrand = ref('')
const overrideBrand = ref('')
const currentStandard = ref(null)
const allBrands = ref([])

watch(visibleInner, async (newVal) => {
  if (newVal && props.record) {
    const baseInfo = props.record.baseInfo || {}
    defaultBrand.value = baseInfo['牌号'] || ''
    
    if (defaultBrand.value) {
      loadStandardData(defaultBrand.value)
    }
    
    try {
      const { data } = await searchStandards({ brand_name: '' })
      allBrands.value = data.items || []
    } catch (e) {
      console.error('加载套用牌号下拉失败', e)
    }
  } else {
    defaultBrand.value = ''
    overrideBrand.value = ''
    currentStandard.value = null
    allBrands.value = []
  }
})

const loadStandardData = async (brandName) => {
  try {
    const { data } = await getStandardDetail({ brand_name: brandName })
    if (data.success) {
      currentStandard.value = data.standard
    }
  } catch (e) {
    console.error('读取牌号指标发生错误:', e)
  }
}

const handleOverrideChange = (val) => {
  if (val) {
    loadStandardData(val)
  } else if (defaultBrand.value) {
    loadStandardData(defaultBrand.value)
  } else {
    currentStandard.value = null
  }
}

const labelMap = {
  '__source_file': '来源文件',
  '__source_sheet': '来源工作表',
  '班组_班长': '班组/班长',
  '检测时间时间': '检测时间',
  '检测时间': '检测时间'
}

const formatLabel = (key) => labelMap[key] || key

const formatValue = (val) => {
  if (val === '' || val === null || val === undefined) return '-'
  return String(val).trim()
}

const baseInfoRows = computed(() => {
  if (!props.record || !props.record.baseInfo) return []
  return Object.entries(props.record.baseInfo).map(([key, value]) => ({
    field: formatLabel(key),
    value: formatValue(value)
  }))
})

const chemistryRows = computed(() => {
  if (!props.record || !props.record.chemistry) return []
  
  const techReq = currentStandard.value?.tech_req || {}
  
  return Object.entries(props.record.chemistry).map(([key, value]) => {
    const std = techReq[key] || {}
    return {
      element: key,
      tech_min: std.tech_min || '-',
      ctrl_min: std.ctrl_min || '-',
      value: formatValue(value),
      ctrl_max: std.ctrl_max || '-',
      tech_max: std.tech_max || '-'
    }
  })
})

const otherRows = computed(() => {
  if (!props.record || !props.record.others) return []
  return Object.entries(props.record.others).map(([key, value]) => ({
    field: formatLabel(key),
    value: formatValue(value)
  }))
})

// ==========================================
// 核心逻辑：动态计算化学元素的越界颜色预警
// ==========================================
const getCellStyle = ({ row }) => {
  // 将实际含量转为浮点数
  const val = parseFloat(row.value)
  if (isNaN(val)) return {}

  // 解析上下限数值
  const t_min = parseFloat(row.tech_min)
  const c_min = parseFloat(row.ctrl_min)
  const c_max = parseFloat(row.ctrl_max)
  const t_max = parseFloat(row.tech_max)
  
  // 辅助函数：判断是否配置了该界限
  const isNum = (n) => !isNaN(n)

  // 1. 低于技术下限 (最严重偏低，#f54616，透明度50%用 rgba 换算即 245,70,22,0.5)
  if (isNum(t_min) && val < t_min) {
    return { backgroundColor: 'rgba(245, 70, 22, 0.5)' }
  }
  
  // 2. 低于内控下限但没有低于技术下限 (#faaf3e，250,175,62,0.5)
  if (isNum(c_min) && val < c_min) {
    return { backgroundColor: 'rgba(250, 175, 62, 0.5)' }
  }
  
  // 3. 超过技术上限 (最严重偏高，#2024fa，32,36,250,0.5)
  if (isNum(t_max) && val > t_max) {
    return { backgroundColor: 'rgba(32, 36, 250, 0.5)' }
  }
  
  // 4. 高于内控上限但不高于技术上限 (#40bfff，64,191,255,0.5)
  if (isNum(c_max) && val > c_max) {
    return { backgroundColor: 'rgba(64, 191, 255, 0.5)' }
  }

  // 完全在内控范围内，或者是没有配置任何限制的情况，保持原样
  return {}
}
</script>

<style scoped>
.block-card {
  border-radius: 8px;
}
</style>