<template>
  <div>
    <div class="page-title">首页总览</div>

    <el-row :gutter="18">
      <el-col :span="6">
        <StatCard
          title="工作表数量"
          :value="overview.sheetCount || 0"
          desc="当前数据库已同步的工作表"
          cardClass="gradient-card"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="总炉数"
          :value="overview.totalRows || 0"
          desc="按工作表去重统计后的炉数"
          cardClass="gradient-card-green"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="最近新增"
          :value="overview.lastSync?.added_count || 0"
          desc="最近一次同步新增"
          cardClass="gradient-card-purple"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="最近修改"
          :value="overview.lastSync?.updated_count || 0"
          desc="最近一次同步修改"
          cardClass="gradient-card-orange"
        />
      </el-col>
    </el-row>

    <el-row :gutter="18" style="margin-top:18px;">
      <el-col :span="12">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">各工作表数据量</div>
          </template>
          <div ref="sheetChartRef" style="height:340px;"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">牌号分布</div>
          </template>
          <div ref="brandChartRef" style="height:340px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="block-card" style="margin-top:18px;">
      <template #header>
        <div style="font-weight:700;">工作表明细</div>
      </template>

      <el-table :data="overview.sheetStats || []" border stripe>
        <el-table-column prop="sheetName" label="工作表名称" />
        <el-table-column prop="tableName" label="数据库表名" />
        <el-table-column prop="rowCount" label="炉数" width="120" />
        <el-table-column prop="lastSyncTime" label="最后同步时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import StatCard from '../components/StatCard.vue'
import { getOverview } from '../api'

const overview = ref({})

const sheetChartRef = ref(null)
const brandChartRef = ref(null)

let sheetChartInstance = null
let brandChartInstance = null
let sheetChartTimer = null
let currentSheetPage = 0

const SHEET_PAGE_SIZE = 10
const SHEET_SWITCH_INTERVAL = 4000

const loadData = async () => {
  const { data } = await getOverview()
  overview.value = data
  await renderCharts()
}

const getSheetPages = () => {
  const all = overview.value.sheetStats || []
  const pages = []
  for (let i = 0; i < all.length; i += SHEET_PAGE_SIZE) {
    pages.push(all.slice(i, i + SHEET_PAGE_SIZE))
  }
  return pages
}

const renderSheetChartPage = () => {
  if (!sheetChartInstance) return

  const pages = getSheetPages()
  if (pages.length === 0) {
    sheetChartInstance.clear()
    return
  }

  if (currentSheetPage >= pages.length) {
    currentSheetPage = 0
  }

  const currentPageData = pages[currentSheetPage]

  sheetChartInstance.setOption({
    tooltip: {
      trigger: 'axis'
    },
    grid: { left: 40, right: 20, top: 30, bottom: 60 },
    xAxis: {
      type: 'category',
      data: currentPageData.map(i => i.sheetName),
      axisLabel: {
        rotate: 20,
        interval: 0
      }
    },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      barWidth: 30,
      data: currentPageData.map(i => i.rowCount),
      itemStyle: {
        borderRadius: [8, 8, 0, 0],
        color: '#3b82f6'
      }
    }],
    graphic: [
      {
        type: 'text',
        right: 20,
        top: 8,
        style: {
          text: `第 ${currentSheetPage + 1} / ${pages.length} 组`,
          fill: '#64748b',
          fontSize: 12
        }
      }
    ]
  })
}

const startSheetChartCarousel = () => {
  if (sheetChartTimer) {
    clearInterval(sheetChartTimer)
  }

  const pages = getSheetPages()
  if (pages.length <= 1) return

  sheetChartTimer = setInterval(() => {
    currentSheetPage += 1
    if (currentSheetPage >= pages.length) {
      currentSheetPage = 0
    }
    renderSheetChartPage()
  }, SHEET_SWITCH_INTERVAL)
}

const renderBrandChart = () => {
  if (!brandChartInstance) return

  brandChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}<br/>数量：${params.value}<br/>占比：${params.percent}%`
      }
    },
    series: [{
      name: '牌号',
      type: 'pie',
      radius: ['38%', '68%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      label: {
        show: false
      },
      labelLine: {
        show: false
      },
      data: (overview.value.brandStats || []).map(i => ({
        name: i.name,
        value: i.count
      }))
    }]
  })
}

const renderCharts = async () => {
  await nextTick()

  if (sheetChartRef.value) {
    if (sheetChartInstance) {
      sheetChartInstance.dispose()
    }
    sheetChartInstance = echarts.init(sheetChartRef.value)
    currentSheetPage = 0
    renderSheetChartPage()
    startSheetChartCarousel()
  }

  if (brandChartRef.value) {
    if (brandChartInstance) {
      brandChartInstance.dispose()
    }
    brandChartInstance = echarts.init(brandChartRef.value)
    renderBrandChart()
  }
}

onMounted(loadData)

onBeforeUnmount(() => {
  if (sheetChartTimer) {
    clearInterval(sheetChartTimer)
  }
  if (sheetChartInstance) {
    sheetChartInstance.dispose()
  }
  if (brandChartInstance) {
    brandChartInstance.dispose()
  }
})
</script>