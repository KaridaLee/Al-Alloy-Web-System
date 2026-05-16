import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Settings from '../views/Settings.vue'
import Standards from '../views/Standards.vue' // 新增

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'home', component: Home },
      { path: 'search', name: 'search', component: Search },
      { path: 'settings', name: 'settings', component: Settings },
      { path: 'standards', name: 'standards', component: Standards } // 新增
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router