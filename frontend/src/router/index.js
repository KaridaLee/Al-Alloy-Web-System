import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Settings from '../views/Settings.vue'
import Standards from '../views/Standards.vue'
import SystemDocs from '../views/SystemDocs.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'home', component: Home },
      { path: 'search', name: 'search', component: Search },
      { path: 'standards', name: 'standards', component: Standards },
      { path: 'system-docs', name: 'system-docs', component: SystemDocs }, // 已修改此处，避开后端 API 文档冲突
      { path: 'settings', name: 'settings', component: Settings }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router