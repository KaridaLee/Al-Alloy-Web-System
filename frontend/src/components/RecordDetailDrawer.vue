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

        <el-table :data="chemistryRows" border stripe style="width:100%;">
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

// 状态管理变量
const defaultBrand = ref('')
const overrideBrand = ref('')
const currentStandard = ref(null)
const allBrands = ref([])

// 监听抽屉开启与关闭状态
watch(visibleInner, async (newVal) => {
  if (newVal && props.record) {
    // 1. 自动提取当前点击行的原始牌号
    const baseInfo = props.record.baseInfo || {}
    defaultBrand.value = baseInfo['牌号'] || ''
    
    // 2. 加载默认牌号在标准库里的区间数据
    if (defaultBrand.value) {
      loadStandardData(defaultBrand.value)
    }
    
    // 3. 拉取系统已知的所有可用牌号列表，供套用选择器使用
    try {
      const { data } = await searchStandards({ brand_name: '' })
      allBrands.value = data.items || []
    } catch (e) {
      console.error('加载套用牌号下拉失败', e)
    }
  } else {
    // 4. 【核心机制】退出抽屉时，彻底清空销毁临时重写变量，确保下次打开依然还原为默认值
    defaultBrand.value = ''
    overrideBrand.value = ''
    currentStandard.value = null
    allBrands.value = []
  }
})

// 加载指定牌号的技术与内控标准
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

// 联动选择事件：如果清空则回退到原始默认牌号标准，否则去拉取新选择的指标
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

// 【核心机制】动态组装化学成分表格：混合实际测量值与当前选定的（默认或临时套用）上下限要求
const chemistryRows = computed(() => {
  if (!props.record || !props.record.chemistry) return []
  
  // 取出当前绑定的标准集合
  const techReq = currentStandard.value?.tech_req || {}
  
  return Object.entries(props.record.chemistry).map(([key, value]) => {
    // 获取该元素对应的五宫格模型数据
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
</script>

<style scoped>
.block-card {
  border-radius: 8px;
}
</style>