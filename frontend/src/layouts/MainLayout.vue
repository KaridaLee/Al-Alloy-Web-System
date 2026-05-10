<template>
  <el-container style="height: 100vh;">
    <el-aside width="240px" style="background:linear-gradient(180deg,#0f172a,#1e293b);color:#fff;">
      <div style="padding:22px 20px;border-bottom:1px solid rgba(255,255,255,.08);">
        <div style="font-size:20px;font-weight:800;">铝锭成分台账系统</div>
        <div style="font-size:12px;color:#94a3b8;margin-top:6px;">一体化查询面板</div>
      </div>

      <el-menu
        router
        background-color="transparent"
        text-color="#cbd5e1"
        active-text-color="#60a5fa"
        :default-active="$route.path"
      >
        <el-menu-item index="/">
          <span>首页总览</span>
        </el-menu-item>
        <el-menu-item index="/search">
          <span>数据搜索</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="background:#fff;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:18px;font-weight:700;color:#0f172a;">服务控制台</div>
        </div>
        <el-tag type="success" size="large">运行中</el-tag>
      </el-header>

      <el-main style="padding:20px 24px;background:#f8fafc;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSystemStatus } from '../api'

const hostText = ref('加载中...')

onMounted(async () => {
  const { data } = await getSystemStatus()
  hostText.value = `${data.host}:${data.port}`
})
</script>