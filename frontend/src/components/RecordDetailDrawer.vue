<template>
  <el-drawer v-model="visibleInner" title="记录详情" :size="isMobile ? '90%' : '40%'">
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
              placeholder="套用其他牌号标准"
              size="small"
              :style="{ width: isMobile ? '120px' : '180px' }"
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

        <el-alert 
          v-if="overrideBrand && overrideBrand !== record.baseInfo['牌号']" 
          :title="`正在使用 【${overrideBrand}】 的内控标准进行预警对比`" 
          type="warning" 
          show-icon 
          style="margin-bottom: 12px;"
          :closable="false"
        />

        <el-table :data="chemistryRows" border style="width:100%;" :row-style="getCellStyle">
          <el-table-column prop="element" label="元素" width="80" align="center">
            <template #default="{ row }"><strong>{{ row.element }}</strong></template>
          </el-table-column>
          <el-table-column prop="value" label="实际检测值" align="center">
             <template #default="{ row }">
              <span style="font-weight: bold; font-size: 15px;">{{ row.value }}</span>
            </template>
          </el-table-column>
          <el-table-column label="企标内控范围" align="center">
            <template #default="{ row }">
              <div style="font-size: 12px; color: #64748b;">
                <span v-if="row.ctrl_min || row.ctrl_max">
                  {{ row.ctrl_min || '0' }} ~ {{ row.ctrl_max || '无上限' }}
                </span>
                <span v-else>-</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="block-card" style="margin-bottom:16px;">
        <template #header>
          <div style="font-weight:700;">其他业务字段</div>
        </template>

        <el-table :data="otherRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="字段" width="120" show-overflow-tooltip />
          <el-table-column prop="value" label="值" show-overflow-tooltip />
        </el-table>
      </el-card>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { searchStandards, getStandardDetail } from '../api'

const props = defineProps({
  modelValue: Boolean,
  record: Object
})

const emit = defineEmits(['update:modelValue'])

const visibleInner = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// === 新增：响应式屏幕检测 ===
const isMobile = ref(false)
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})

const allBrands = ref([])
const overrideBrand = ref('')
const currentStandardData = ref(null)

const fetchAllBrands = async () => {
  const { data } = await searchStandards({ brand_name: '' })
  allBrands.value = data.items || []
}

const loadStandardDetail = async (brandName) => {
  if (!brandName) {
    currentStandardData.value = null
    return
  }
  const { data } = await getStandardDetail({ brand_name: brandName })
  if (data.success) {
    currentStandardData.value = data.standard?.tech_req || null
  }
}

watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    overrideBrand.value = ''
    await fetchAllBrands()
    const originalBrand = props.record?.baseInfo['牌号']
    if (originalBrand) {
      await loadStandardDetail(originalBrand)
    } else {
      currentStandardData.value = null
    }
  }
})

const handleOverrideChange = async (val) => {
  await loadStandardDetail(val || props.record?.baseInfo['牌号'])
}

const formatLabel = (key) => key.replace(/^_+/, '')
const formatValue = (val) => val === null || val === '' ? '-' : val

const baseInfoRows = computed(() => {
  if (!props.record || !props.record.baseInfo) return []
  return Object.entries(props.record.baseInfo).map(([key, value]) => ({
    field: formatLabel(key),
    value: formatValue(value)
  }))
})

const chemistryRows = computed(() => {
  if (!props.record || !props.record.chemistry) return []
  return Object.entries(props.record.chemistry).map(([el, value]) => {
    const std = currentStandardData.value?.[el] || {}
    return {
      element: el,
      value: formatValue(value),
      tech_min: std.tech_min || '',
      ctrl_min: std.ctrl_min || '',
      ctrl_max: std.ctrl_max || '',
      tech_max: std.tech_max || ''
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

const getCellStyle = ({ row }) => {
  const val = parseFloat(row.value)
  if (isNaN(val)) return {}

  const t_min = parseFloat(row.tech_min)
  const c_min = parseFloat(row.ctrl_min)
  const c_max = parseFloat(row.ctrl_max)
  const t_max = parseFloat(row.tech_max)
  
  const isNum = (n) => !isNaN(n)

  if (isNum(t_min) && val < t_min) return { backgroundColor: 'rgba(245, 70, 22, 0.5)' }
  if (isNum(t_max) && val > t_max) return { backgroundColor: 'rgba(245, 70, 22, 0.5)' }
  if (isNum(c_min) && val < c_min) return { backgroundColor: 'rgba(234, 179, 8, 0.4)' }
  if (isNum(c_max) && val > c_max) return { backgroundColor: 'rgba(234, 179, 8, 0.4)' }
  return {}
}
</script>

<style scoped>
.block-card { border-radius: 12px; }
</style>