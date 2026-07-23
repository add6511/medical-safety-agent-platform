<template>
  <div class="login-page"><div class="login-card">
    <div class="logo"><el-icon :size="48" color="#409EFF"><Monitor /></el-icon><h2>医疗预检安全预警平台</h2><p>Medical Pre-screening Safety Platform（教学演示）</p></div>
    <el-alert v-if="env.USE_MOCK" type="warning" title="⚠️ 演示模式" description="当前使用MOCK Token。生产环境需配置 VITE_USE_MOCK=false" :closable="false" style="margin-bottom:16px" show-icon />
    <el-form :model="form" :rules="rules" ref="formRef" size="large">
      <el-form-item prop="username"><el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" /></el-form-item>
      <el-form-item prop="password"><el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password /></el-form-item>
      <el-form-item><el-button type="primary" @click="handleLogin" :loading="loading" style="width:100%">{{ loading ? '登录中...' : '登 录' }}</el-button></el-form-item>
    </el-form>
    <div class="roles"><el-tag v-for="r in demoRoles" :key="r.role" @click="quickLogin(r)" style="cursor:pointer;margin:4px">{{ r.label }}</el-tag></div>
  </div></div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { env, loginReal } from '@/api'
import { mapBackendRole } from '@/types/dto'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter(); const store = useAppStore(); const loading = ref(false); const formRef = ref()
const form = reactive({ username: '', password: '' })
const rules = { username: [{ required: true, message: '请输入用户名', trigger: 'blur' }], password: [{ required: true, message: '请输入密码', trigger: 'blur' }] }

const demoRoles = [
  { label: '👨‍⚕️ 教学-医务人员', role: 'doctor', username: 'doctor', password: 'demo' },
  { label: '🧑‍💻 教学-管理员', role: 'admin', username: 'admin', password: 'demo' },
  { label: '👤 教学-患者', role: 'patient', username: 'patient', password: 'demo' },
  { label: '📋 教学-随访员', role: 'followup', username: 'followup', password: 'demo' },
]

function quickLogin(r: any) { form.username = r.username; form.password = r.password; handleLogin() }

async function handleLogin() {
  await formRef.value?.validate(); loading.value = true
  try {
    const resp = await loginReal({ username: form.username, password: form.password })
    const role = mapBackendRole(resp.roles?.[0] || (env.USE_MOCK ? 'MEDICAL_STAFF' : 'PATIENT'))
    store.login(resp.username || form.username, role, resp.accessToken)
    if (env.USE_MOCK) ElMessage.warning('当前为MOCK演示模式')
    router.push('/dashboard')
  } catch {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); }
.login-card { width:460px;padding:40px;background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.logo { text-align:center;margin-bottom:24px; } .logo h2 { font-size:1.3rem;color:#303133;margin-top:12px; } .logo p { font-size:0.8rem;color:#909399;margin-top:4px; }
.roles { text-align:center;margin-top:16px; }
</style>
