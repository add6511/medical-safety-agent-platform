<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <el-icon :size="48" color="#409EFF">
          <Monitor />
        </el-icon>
        <h2>医疗预检安全预警平台</h2>
        <p>Medical Pre-screening Safety Platform（教学演示）</p>
      </div>

      <el-alert
        type="info"
        title="真实后端联调"
        description="当前连接 Spring Boot Demo 环境，所有账号和病例均为合成教学数据。"
        :closable="false"
        style="margin-bottom: 16px"
        show-icon
      />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="roles">
        <el-tag
          v-for="account in demoAccounts"
          :key="account.username"
          style="cursor: pointer; margin: 4px"
          @click="quickLogin(account)"
        >
          {{ account.label }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api'

interface DemoAccount {
  label: string
  username: string
  password: string
}

interface ApiErrorResponse {
  message?: string
}

const router = useRouter()
const store = useAppStore()

const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    {
      required: true,
      message: '请输入用户名',
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: 'blur',
    },
  ],
}

const demoAccounts: DemoAccount[] = [
  {
    label: '👨‍⚕️ 教学演示-医务人员',
    username: 'demo_medical',
    password: 'demo123',
  },
  {
    label: '🧑‍💻 教学演示-管理员',
    username: 'demo_admin',
    password: 'demo123',
  },
  {
    label: '👤 教学演示-模拟患者',
    username: 'demo_patient',
    password: 'demo123',
  },
  {
    label: '📋 教学演示-随访人员',
    username: 'demo_followup',
    password: 'demo123',
  },
]

const roleMapping: Record<string, string> = {
  PATIENT: 'patient',
  MEDICAL_STAFF: 'doctor',
  FOLLOWUP_STAFF: 'followup',
  ADMIN: 'admin',
  AI_SERVICE: 'ai_service',
}

function mapBackendRole(roles: string[]): string {
  const priority = [
    'ADMIN',
    'MEDICAL_STAFF',
    'FOLLOWUP_STAFF',
    'PATIENT',
    'AI_SERVICE',
  ]

  const matchedRole = priority.find((role) => roles.includes(role))
  return matchedRole ? roleMapping[matchedRole] : 'unknown'
}

function quickLogin(account: DemoAccount) {
  form.username = account.username
  form.password = account.password
  void handleLogin()
}

 async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)

  if (!valid) {
    return
  }

  loading.value = true

  try {
    const response = await authApi.login({
      username: form.username.trim(),
      password: form.password,
    })

    const data = response.data
    const frontendRole = mapBackendRole(data.roles)

    store.login(
  data.userId,
  data.username,
  frontendRole,
  data.accessToken,
)

    ElMessage.success(`登录成功：${data.username}`)
    await router.push('/dashboard')
  } catch (error: unknown) {
   

    const axiosError = error as AxiosError<ApiErrorResponse>

    

    const message =
      axiosError.response?.data?.message ||
      (error instanceof Error ? error.message : '未知错误')

    ElMessage.error(`登录失败：${message}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 460px;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.logo {
  text-align: center;
  margin-bottom: 24px;
}

.logo h2 {
  margin-top: 12px;
  color: #303133;
  font-size: 1.3rem;
}

.logo p {
  margin-top: 4px;
  color: #909399;
  font-size: 0.8rem;
}

.roles {
  margin-top: 16px;
  text-align: center;
}
</style>