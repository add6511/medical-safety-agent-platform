<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo"><el-icon :size="48" color="#409EFF"><Monitor /></el-icon><h2>医疗预检安全预警平台</h2><p>Medical Pre-screening Safety Platform（教学演示）</p></div>
      <el-alert type="warning" title="⚠️ 演示模式" description="当前使用MOCK Token，仅供教学演示。生产环境需配置真实JWT认证。" :closable="false" style="margin-bottom:16px" show-icon />
      <el-form :model="form" :rules="rules" ref="formRef" size="large">
        <el-form-item prop="email"><el-input v-model="form.email" placeholder="邮箱" :prefix-icon="Message" /></el-form-item>
        <el-form-item prop="password"><el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password /></el-form-item>
        <el-form-item><el-button type="primary" @click="handleLogin" :loading="loading" style="width:100%">登录（演示）</el-button></el-form-item>
      </el-form>
      <div class="roles"><el-tag v-for="r in demoRoles" :key="r.role" @click="quickLogin(r)" style="cursor:pointer;margin:4px">{{ r.label }}</el-tag></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const store = useAppStore()
const loading = ref(false)
const formRef = ref()
const form = reactive({ email: '', password: '' })
const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码（演示模式任意密码均可）', trigger: 'blur' }],
}

const demoRoles = [
  { label: '👨‍⚕️ 教学演示-医务人员', role: 'doctor', email: 'doctor@hospital.com', password: 'demo' },
  { label: '🧑‍💻 教学演示-管理员', role: 'admin', email: 'admin@hospital.com', password: 'demo' },
  { label: '👤 教学演示-模拟患者', role: 'patient', email: 'patient@demo.com', password: 'demo' },
]

function quickLogin(r: any) { form.email = r.email; form.password = r.password; handleLogin() }

async function handleLogin() {
  await formRef.value?.validate()
  loading.value = true
  setTimeout(() => {
    const role = demoRoles.find(r => r.email === form.email)?.role || 'doctor'
    // 使用明确标注的MOCK Token
    store.login('MOCK_' + role, role, 'MOCK_TOKEN_' + role.toUpperCase() + '_' + Date.now())
    ElMessage.warning('当前为MOCK演示模式，Token为模拟数据')
    router.push('/dashboard')
    loading.value = false
  }, 600)
}
</script>

<style scoped>
.login-page { min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); }
.login-card { width:460px;padding:40px;background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.logo { text-align:center;margin-bottom:24px; }
.logo h2 { font-size:1.3rem;color:#303133;margin-top:12px; }
.logo p { font-size:0.8rem;color:#909399;margin-top:4px; }
.roles { text-align:center;margin-top:16px; }
</style>
