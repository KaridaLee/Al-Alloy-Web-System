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
          <div style="font-weight:700;">化学成分（%）</div>
        </template>

        <el-table :data="chemistryRows" border stripe style="width:100%;">
          <el-table-column prop="field" label="元素" width="100" />
          <el-table-column prop="value" label="含量" />
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
import { computed } from 'vue'

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
  return Object.entries(props.record.chemistry).map(([key, value]) => ({
    field: key,
    value: formatValue(value)
  }))
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