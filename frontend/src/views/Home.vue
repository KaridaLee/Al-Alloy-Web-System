<template>
  <div>
    <div class="page-title">首页总览</div>

    <el-row :gutter="18">
      <el-col :xs="24" :sm="12" :md="6" style="margin-bottom: 16px;">
        <StatCard title="工作表数量" :value="overview.sheetCount || 0" desc="当前数据库已同步的工作表" cardClass="gradient-card" />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" style="margin-bottom: 16px;">
        <StatCard title="总炉数" :value="overview.totalRows || 0" desc="按工作表去重统计后的炉数" cardClass="gradient-card-green" />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" style="margin-bottom: 16px;">
        <StatCard title="最近新增" :value="overview.lastSync?.added_count || 0" desc="最近一次同步新增" cardClass="gradient-card-purple" />
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" style="margin-bottom: 16px;">
        <StatCard title="最近修改" :value="overview.lastSync?.updated_count || 0" desc="最近一次同步修改" cardClass="gradient-card-orange" />
      </el-col>
    </el-row>

    <el-row :gutter="18" style="margin-top:2px;">
      <el-col :xs="24" :md="12" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">牌号数据量</div>
          </template>
          <div ref="brandChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">工作表数据量分布</div>
          </template>
          <div ref="sheetChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <div style="font-size: 18px; font-weight: 700; margin-top: 12px; margin-bottom: 12px; color: #1e293b;">
      近期各牌号关键元素波动趋势 (轮播)
    </div>

    <el-row :gutter="18">
      <el-col :xs="24" :md="8" v-for="(module, index) in trendModules" :key="index" style="margin-bottom: 16px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:700;">{{ module.brand }} 波动趋势</span>
              <el-tag size="small" type="info">
                当前: {{ module.data?.elements?.[module.currentElementIdx] || '-' }}
              </el-tag>
            </div>
          </template>
          <div :ref="el => trendChartRefs[index] = el" style="height: 250px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import StatCard from '../components/StatCard.vue'
import { getOverview, getBrandTrends } from '../api'

const overview = ref({})
const sheetChartRef = ref(null)
const brandChartRef = ref(null)
let sheetChartInstance = null
let brandChartInstance = null

const trendModules = ref([
  { brand: 'JZJL-ADC12', data: null, currentElementIdx: 0, chartInstance: null },
  { brand: 'JZJL-A380', data: null, currentElementIdx: 0, chartInstance: null },
  { brand: 'JZJL-AlSi9Cu3', data: null, currentElementIdx: 0, chartInstance: null }
])
const trendChartRefs = ref([])
const trendIntervals = []

const loadData = async () => {
  const { data } = await getOverview()
  overview.value = data

  await nextTick()
  initSheetChart(data.sheetStats)
  initBrandChart(data.brandStats)

  for (let i = 0; i < trendModules.value.length; i++) {
    const res = await getBrandTrends(trendModules.value[i].brand)
    if (res.data.success) {
      trendModules.value[i].data = res.data
      renderTrendChart(i)
      startTrendCarousel(i)
    }
  }
}

const initSheetChart = (stats) => {
  sheetChartInstance = echarts.init(sheetChartRef.value)
  sheetChartInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      data: stats.map(s => ({ name: s.sheet_name, value: s.count }))
    }]
  })
}

const initBrandChart = (stats) => {
  brandChartInstance = echarts.init(brandChartRef.value)
  const keys = Object.keys(stats)
  const vals = Object.values(stats)
  brandChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: keys, axisLabel: { interval: 0, rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: vals,
      itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }
    }]
  })
}

const renderTrendChart = (index) => {
  const module = trendModules.value[index]
  const dom = trendChartRefs.value[index]
  if (!dom || !module.data || module.data.elements.length === 0) return

  if (!module.chartInstance) {
    module.chartInstance = echarts.init(dom)
  }

  const element = module.data.elements[module.currentElementIdx]
  const values = module.data.trends[element]

  module.chartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: module.data.furnaces, show: false },
    yAxis: { 
      type: 'value', 
      scale: true,
      min: (value) => {
        const range = value.max - value.min
        return Number((value.min - range * 0.3).toFixed(4))
      },
      max: (value) => {
        const range = value.max - value.min
        return Number((value.max + range * 0.3).toFixed(4))
      }
    },
    series: [{
      name: element,
      type: 'line',
      data: values,
      smooth: true,
      symbolSize: 8,
      itemStyle: { color: '#8b5cf6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
          { offset: 1, color: 'rgba(139, 92, 246, 0)' }
        ])
      }
    }]
  }, true)
}

const startTrendCarousel = (index) => {
  trendIntervals[index] = setInterval(() => {
    const module = trendModules.value[index]
    if (module.data && module.data.elements && module.data.elements.length > 0) {
      module.currentElementIdx = (module.currentElementIdx + 1) % module.data.elements.length
      renderTrendChart(index)
    }
  }, 5000)
}

// 监听窗口大小变化以重绘 Echarts
const handleResize = () => {
  if (sheetChartInstance) sheetChartInstance.resize()
  if (brandChartInstance) brandChartInstance.resize()
  trendModules.value.forEach(m => {
    if (m.chartInstance) m.chartInstance.resize()
  })
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (sheetChartInstance) sheetChartInstance.dispose()
  if (brandChartInstance) brandChartInstance.dispose()
  trendModules.value.forEach(m => {
    if (m.chartInstance) m.chartInstance.dispose()
  })
  trendIntervals.forEach(t => clearInterval(t))
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.block-card { border-radius: 12px; }
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 20px; color: #1e293b; }
</style>