<template>
  <el-drawer v-model="visibleInner" title="记录详情" size="70%">
    <div v-if="record">
      <el-card class="block-card" style="margin-bottom:16px;">
        <template #header>
          <div style="font-weight:700;">基础信息</div>
        </template>

        <el-table :data="baseInfoRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="字段" width="220" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </el-card>

      <el-card class="block-card" style="margin-bottom:16px;">
        <template #header>
          <div style="font-weight:700;">化学成分（%）</div>
        </template>

        <el-table :data="chemistryRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="元素" width="160" />
          <el-table-column prop="value" label="含量" />
        </el-table>
      </el-card>

      <el-card v-if="otherRows.length > 0" class="block-card">
        <template #header>
          <div style="font-weight:700;">其他字段</div>
        </template>

        <el-table :data="otherRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="字段" width="220" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </el-card>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  record: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const visibleInner = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const labelMap = {
  '__source_file': '来源文件',
  '__source_sheet': '来源工作表',
  '班组_班长': '班组/班长',
  '检测时间时间': '检测时间'
}

const formatLabel = (key) => labelMap[key] || key

const formatValue = (val) => {
  if (val === '' || val === null || val === undefined) return '-'

  const str = String(val).trim()

  // 仅处理科学计数法/数值字符串
  if (/^-?\d+(\.\d+)?e[-+]?\d+$/i.test(str) || /^-?\d+(\.\d+)?$/.test(str)) {
    const num = Number(str)
    if (!Number.isNaN(num)) {
      // 保留较高精度，再去掉末尾多余0
      let fixed = num.toFixed(10)
      fixed = fixed.replace(/\.?0+$/, '')
      return fixed
    }
  }

  return str
}

const toRows = (obj) => {
  if (!obj || typeof obj !== 'object') return []
  return Object.keys(obj).map((key) => ({
    field: formatLabel(key),
    value: formatValue(obj[key])
  }))
}

const baseInfoRows = computed(() => toRows(props.record?.baseInfo))
const chemistryRows = computed(() => toRows(props.record?.chemistry))
const otherRows = computed(() => toRows(props.record?.others))
</script>