<template>
  <el-container style="height: 100vh;">
    <el-aside
      v-if="!isMobile"
      width="250px"
      style="background: #1e293b; color: #fff; display: flex; flex-direction: column; border-right: 1px solid #334155;"
    >
      <div style="padding: 24px 20px; background: #0f172a; border-bottom: 1px solid #334155;">
        <div style="font-size: 18px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;">铝锭成分台账系统</div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 6px; font-family: monospace;">Local Control Center</div>
      </div>

      <el-menu
        router
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#ffffff"
        :default-active="$route.path"
        class="modern-menu"
        style="border-right: none; padding: 12px 10px; flex: 1;"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页总览</span>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon>
          <span>数据搜索</span>
        </el-menu-item>
        <el-menu-item index="/standards">
          <el-icon><Management /></el-icon>
          <span>企业标准</span>
        </el-menu-item>
        <el-menu-item index="/system-docs">
          <el-icon><Document /></el-icon>
          <span>体系文件</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-drawer
      v-if="isMobile"
      v-model="mobileMenuVisible"
      direction="ltr"
      size="250px"
      :with-header="false"
      style="background: #1e293b;"
    >
      <div style="padding: 24px 20px; background: #0f172a; color: #fff; border-bottom: 1px solid #334155;">
        <div style="font-size: 18px; font-weight: 800;">铝锭成分台账系统</div>
      </div>
      <el-menu
        router
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#ffffff"
        :default-active="$route.path"
        class="modern-menu"
        style="border-right: none; padding: 12px 10px;"
        @select="mobileMenuVisible = false"
      >
        <el-menu-item index="/"><span>首页总览</span></el-menu-item>
        <el-menu-item index="/search"><span>数据搜索</span></el-menu-item>
        <el-menu-item index="/standards"><span>企业标准</span></el-menu-item>
        <el-menu-item index="/system-docs"><span>体系文件</span></el-menu-item>
        <el-menu-item v-if="isAdmin" index="/settings"><span>系统设置</span></el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container>
      <el-header
        style="
          background: #ffffff;
          border-bottom: 1px solid #e2e8f0;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0 24px;
          height: 64px;
          box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        "
      >
        <div style="display: flex; align-items: center; gap: 16px;">
          <el-button
            v-if="isMobile"
            circle
            @click="mobileMenuVisible = true"
          >
            ☰
          </el-button>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a;">本地服务控制台</div>
        </div>
        
        <div style="display: flex; align-items: center; gap: 12px;">
          <el-tag type="success" size="large" effect="light">运行中</el-tag>
          <div style="width: 1px; height: 16px; background-color: #cbd5e1; margin: 0 4px;"></div>
          
          <el-button 
            v-if="!isAdmin" 
            type="primary" 
            size="small" 
            plain 
            @click="showLoginDialog"
          >
            登录管理员
          </el-button>
          
          <el-dropdown v-else trigger="click" @command="handleUserCommand">
            <span style="cursor: pointer; display: flex; align-items: center; gap: 6px; font-weight: 600; color: #334155; font-size: 14px; padding: 4px 8px; border-radius: 6px; transition: background 0.2s;">
              <el-avatar :size="24" style="background-color: #3b82f6; font-size: 11px; font-weight: bold;">AD</el-avatar>
              系统管理员
              <el-icon style="font-size: 12px; margin-left: 2px;"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-menu-item command="logout">
                  <span style="color: #ef4444; font-weight: bold;">退出安全登录</span>
                </el-dropdown-menu-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main
        style="
          padding: 24px;
          background: #f8fafc;
          overflow-y: auto;
        "
      >
        <router-view />
      </el-main>
    </el-container>

    <el-dialog
      v-model="loginVisible"
      title="管理员权限认证"
      width="380px"
      append-to-body
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="管理员账号">
          <el-input v-model="loginForm.username" placeholder="请输入管理员用户名 (默认: admin)" clearable />
        </el-form-item>
        <el-form-item label="安全密码">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入登录密码" 
            show-password 
            @keyup.enter="executeLogin"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
          <el-button @click="loginVisible = false">取消</el-button>
          <el-button type="primary" :loading="logining" @click="executeLogin">验证登录</el-button>
        </div>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { HomeFilled, Search, Management, Document, Setting, ArrowDown } from '@element-plus/icons-vue'
import { loginAdmin } from '../api'

const route = useRoute()
const router = useRouter()

const isMobile = ref(false)
const mobileMenuVisible = ref(false)

const isAdmin = ref(sessionStorage.getItem('isAdmin') === 'true')
const loginVisible = ref(false)
const logining = ref(false)
const loginForm = ref({ username: '', password: '' })

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

const showLoginDialog = () => {
  loginForm.value = { username: '', password: '' }
  loginVisible.value = true
}

const executeLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('账号或密码不能为空')
    return
  }
  
  logining.value = true
  try {
    const { data } = await loginAdmin(loginForm.value)
    
    if (data.success) {
      sessionStorage.setItem('isAdmin', 'true')
      isAdmin.value = true
      loginVisible.value = false
      ElMessage.success('管理员认证通过，已开放高级权限项')
      window.dispatchEvent(new Event('admin-state-changed'))
    } else {
      ElMessage.error(data.message || '密码验证失败')
    }
  } catch (e) {
    ElMessage.error('登录请求异常，请检查服务器连接')
  } finally {
    logining.value = false
  }
}

const handleUserCommand = (command) => {
  if (command === 'logout') {
    sessionStorage.removeItem('isAdmin')
    isAdmin.value = false
    ElMessage.info('已安全登出')
    window.dispatchEvent(new Event('admin-state-changed'))
    if (route.path === '/settings') {
      router.push('/')
    }
  }
}

watch(() => route.path, (newPath) => {
  if (newPath === '/settings' && !isAdmin.value) {
    ElMessage.error('权限受阻：您未登录管理员，已将其重定向至首页')
    router.push('/')
  }
}, { immediate: true })

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.modern-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin-bottom: 6px;
  border-radius: 8px;
  padding: 0 16px !important;
  transition: all 0.25s ease;
}

.modern-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #f8fafc !important;
}

.modern-menu :deep(.el-menu-item.is-active) {
  background-color: #3b82f6 !important;
  color: #ffffff !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.modern-menu :deep(.el-menu-item .el-icon) {
  margin-right: 12px;
  font-size: 18px;
  color: inherit;
}
</style>