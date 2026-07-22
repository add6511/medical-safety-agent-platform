<template>
  <el-container style="min-height:100vh">
    <!-- Sidebar -->
    <el-aside :width="collapsed?'64px':'220px'" class="sidebar">
      <div class="logo" @click="$router.push('/dashboard')">
        <span v-if="!collapsed">🏥 医疗预检平台</span>
        <span v-else>🏥</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        background-color="#001529"
        text-color="#ffffffa0"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/pre-check">
          <el-icon><Edit /></el-icon>
          <span>预检问诊</span>
        </el-menu-item>
        <el-menu-item index="/review-list">
          <el-icon><Checked /></el-icon>
          <span>审核列表</span>
        </el-menu-item>
        <el-menu-item index="/follow-up">
          <el-icon><Calendar /></el-icon>
          <span>随访计划</span>
        </el-menu-item>
        <el-menu-item index="/agent-runs">
          <el-icon><Cpu /></el-icon>
          <span>Agent 日志</span>
        </el-menu-item>
        <el-menu-item index="/safety-audit">
          <el-icon><Warning /></el-icon>
          <span>安全审计</span>
        </el-menu-item>
      </el-menu>
      <div class="collapse-btn" @click="collapsed=!collapsed">
        <el-icon><component :is="collapsed?'DArrowRight':'DArrowLeft'" /></el-icon>
      </div>
    </el-aside>

    <!-- Main Content -->
    <el-container>
      <el-header class="topbar">
        <div style="display:flex;align-items:center;gap:12px">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{path:'/dashboard'}">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="pageTitle">{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <el-badge :value="pendingCount" :hidden="pendingCount===0">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <el-dropdown @command="handleCommand">
            <span style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <el-avatar :size="32" icon="UserFilled" />
              <span>{{ userName }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'
import { DataBoard, Edit, Checked, Calendar, Cpu, Warning, Bell, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const store = useAppStore()
const collapsed = ref(false)
const userName = computed(() => store.user?.name || '用户')
const pendingCount = ref(5)

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/review')) return '/review-list'
  return path
})

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/dashboard': '工作台',
    '/pre-check': '预检问诊',
    '/review-list': '审核列表',
    '/follow-up': '随访计划',
    '/agent-runs': 'Agent 执行日志',
    '/safety-audit': '安全审计',
  }
  return map[route.path] || ''
})

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    store.logout()
    router.push('/login')
    ElMessage.success('已退出')
  }
}
</script>

<style scoped>
.sidebar {
  background: #001529;
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  overflow: hidden;
}
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  border-bottom: 1px solid #ffffff10;
}
.collapse-btn {
  margin-top: auto;
  padding: 12px;
  text-align: center;
  color: #ffffff60;
  cursor: pointer;
  border-top: 1px solid #ffffff10;
}
.collapse-btn:hover { color: #fff; }
.topbar {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #E4E7EC;
  padding: 0 20px;
  height: 56px;
}
.el-menu { border-right: none; }
</style>
