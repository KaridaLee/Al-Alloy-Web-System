<template>
  <div>
    <div class="page-title">首页总览</div>

    <el-row :gutter="18">
      <el-col :span="6">
        <StatCard title="工作表数量" :value="overview.sheetCount || 0" desc="当前数据库已同步的工作表" cardClass="gradient-card" />
      </el-col>
      <el-col :span="6">
        <StatCard title="总炉数" :value="overview.totalRows || 0" desc="按工作表去重统计后的炉数" cardClass="gradient-card-green" />
      </el-col>
      <el-col :span="6">
        <StatCard title="最近新增" :value="overview.lastSync?.added_count || 0" desc="最近一次同步新增" cardClass="gradient-card-purple" />
      </el-col>
      <el-col :span="6">
        <StatCard title="最近修改" :value="overview.lastSync?.updated_count || 0" desc="最近一次同步修改" cardClass="gradient-card-orange" />
      </el-col>
    </el-row>

    <el-row :gutter="18" style="margin-top:18px;">
      <el-col :span="12">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">各工作表数据量</div>
          </template>
          <div ref="sheetChartRef" style="height:300px;"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="block-card">
          <template #header>
            <div style="font-weight:700;">牌号分布</div>
          </template>
          <div ref="brandChartRef" style="height:300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18" style="margin-top:18px;">
      <el-col :span="12" v-for="(item, index) in trendModules" :key="index" style="margin-bottom:18px;">
        <el-card class="block-card">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="font-weight:700;">
                {{ item.selectedBrand || ('趋势轮播 - 模块 ' + (index + 1)) }}
              </div>
              <el-select 
                v-model="item.selectedBrand" 
                placeholder="请选择牌号" 
                size="small" 
                style="width: 150px"
                @change="handleBrandChange(index)"
              >
                <el-option 
                  v-for="b in overview.brandStats" 
                  :key="b.name" 
                  :label="b.name" 
                  :value="b.name" 
                />
              </el-select>
            </div>
          </template>
          <div :ref="el => trendChartRefs[index] = el" style="height:300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, reactive } from 'vue'
import * as echarts from 'echarts'
import StatCard from '../components/StatCard.vue'
import { getOverview, getBrandTrends } from '../api'

const overview = ref({})
const sheetChartRef = ref(null)
const brandChartRef = ref(null)
const trendChartRefs = ref([])

let sheetChartInstance = null
let brandChartInstance = null
const trendChartInstances = [null, null, null, null]
const trendIntervals = [null, null, null, null]

// 4个模块的状态
const trendModules = reactive([
  { selectedBrand: '', currentElementIdx: 0, data: null },
  { selectedBrand: '', currentElementIdx: 0, data: null },
  { selectedBrand: '', currentElementIdx: 0, data: null },
  { selectedBrand: '', currentElementIdx: 0, data: null }
])

const loadData = async () => {
  const { data } = await getOverview()
  overview.value = data
  
  // 默认给4个模块赋初始牌号（如果存在）
  if (data.brandStats && data.brandStats.length > 0) {
    for (let i = 0; i < 4; i++) {
      if (!trendModules[i].selectedBrand) {
        // 自动分配前四个热门牌号
        const brandObj = data.brandStats[i % data.brandStats.length]
        trendModules[i].selectedBrand = brandObj.name
        handleBrandChange(i)
      }
    }
  }

  await renderBaseCharts()
}

// 渲染基础的两个图表（工作表数据量柱状图 & 牌号分布饼图）
const renderBaseCharts = async () => {
  await nextTick()
  if (sheetChartRef.value) {
    sheetChartInstance = echarts.init(sheetChartRef.value)
    sheetChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 60 },
      xAxis: { type: 'category', data: (overview.value.sheetStats || []).map(i => i.sheetName), axisLabel: { rotate: 20 } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: (overview.value.sheetStats || []).map(i => i.rowCount), itemStyle: { color: '#3b82f6' } }]
    })
  }
  if (brandChartRef.value) {
    brandChartInstance = echarts.init(brandChartRef.value)
    brandChartInstance.setOption({
      tooltip: { trigger: 'item' },
      series: [{ type: 'pie', radius: ['40%', '70%'], data: (overview.value.brandStats || []).map(i => ({ name: i.name, value: i.count })) }]
    })
  }
}

// 处理牌号切换逻辑
const handleBrandChange = async (index) => {
  const module = trendModules[index]
  if (!module.selectedBrand) return

  // 清除旧的定时任务
  if (trendIntervals[index]) clearInterval(trendIntervals[index])

  try {
    const { data } = await getBrandTrends(module.selectedBrand)
    module.data = data
    module.currentElementIdx = 0
    
    await nextTick()
    if (!trendChartInstances[index]) {
      trendChartInstances[index] = echarts.init(trendChartRefs.value[index])
    }
    
    renderTrendChart(index)
    startTrendCarousel(index)
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

// 渲染具体的趋势折线图（单帧元素展示）
const renderTrendChart = (index) => {
  const instance = trendChartInstances[index]
  const module = trendModules[index]
  if (!instance || !module.data || !module.data.elements || module.data.elements.length === 0) return

  const element = module.data.elements[module.currentElementIdx]
  const values = module.data.trends[element]

  instance.setOption({
    title: {
      text: `当前轮播元素: ${element}`,
      left: 'center',
      textStyle: { fontSize: 13, color: '#94a3b8', fontWeight: 'normal' }
    },
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: module.data.furnace_nos,
      name: '炉号',
      nameLocation: 'end',
      axisLabel: { fontSize: 10, rotate: 30 }
    },
    yAxis: { 
      type: 'value', 
      scale: true,
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }
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

// 启动 5 秒一次的元素轮播定时器
const startTrendCarousel = (index) => {
  trendIntervals[index] = setInterval(() => {
    const module = trendModules[index]
    if (module.data && module.data.elements && module.data.elements.length > 0) {
      module.currentElementIdx = (module.currentElementIdx + 1) % module.data.elements.length
      renderTrendChart(index)
    }
  }, 5000)
}

onMounted(loadData)

onBeforeUnmount(() => {
  // 销毁所有图表实例和定时器，释放内存
  if (sheetChartInstance) sheetChartInstance.dispose()
  if (brandChartInstance) brandChartInstance.dispose()
  trendChartInstances.forEach(ins => ins && ins.dispose())
  trendIntervals.forEach(inv => inv && clearInterval(inv))
})
</script>

<style scoped>
.block-card {
  border-radius: 12px;
  transition: all 0.3s;
}
.block-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.05);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #1e293b;
}
</style>