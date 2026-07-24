<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">📝 分层预检问诊（合成教学案例）</h2>
        <p style="color:var(--text2);font-size:0.85rem">⚠️ 本页面为教学演示。所有数据均为虚构，AI提示仅供辅助参考。</p>
      </div>
      <el-button @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>

    <el-steps :active="step" finish-status="success" align-center style="margin-bottom:32px">
      <el-step title="基本信息" /><el-step title="症状录入" /><el-step title="AI辅助初筛" /><el-step title="筛查提示" />
    </el-steps>

    <!-- Step 1 -->
    <el-card v-if="step===0" shadow="never">
      <template #header><b>👤 教学案例基本信息</b></template>
      <el-form :model="form" label-width="100px" style="max-width:600px">
        <el-form-item label="案例编号" required><el-input v-model="form.name" placeholder="如：教学案例001" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="性别"><el-select v-model="form.gender" style="width:100%"><el-option label="男" value="male" /><el-option label="女" value="female" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="年龄"><el-input-number v-model="form.age" :min="0" :max="120" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="step=1" :disabled="!form.name">下一步</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Step 2 -->
    <el-card v-if="step===1" shadow="never">
      <template #header><b>🏷️ 模拟症状录入</b></template>
      <div style="margin-bottom:16px">
        <el-tag v-for="s in form.symptoms" :key="s" closable @close="form.symptoms=form.symptoms.filter(x=>x!==s)" style="margin:4px">{{ s }}</el-tag>
      </div>
      <el-input v-model="symptomInput" placeholder="输入症状描述后按回车添加" @keyup.enter="addSymptom" style="max-width:400px" />
      <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px">
        <el-tag v-for="s in quickSymptoms" :key="s" @click="addQuick(s)" style="cursor:pointer" :type="form.symptoms.includes(s) ? '' : 'info'">
          {{ s }}
        </el-tag>
      </div>
      <el-form-item label="模拟持续时间" style="margin-top:16px">
        <el-select v-model="form.duration" style="width:200px">
          <el-option v-for="d in durations" :key="d" :label="d" :value="d" />
        </el-select>
      </el-form-item>
      <el-form-item label="严重程度自评">
        <el-rate v-model="form.selfRate" :max="5" show-text :texts="['很轻','轻度','中度','较重','严重']" />
      </el-form-item>
      <el-form-item>
        <el-button @click="step=0">上一步</el-button>
        <el-button type="primary" @click="doScreening" :disabled="form.symptoms.length===0">下一步：AI辅助初筛</el-button>
      </el-form-item>
    </el-card>

    <!-- Step 3 -->
    <el-card v-if="step===2" shadow="never">
      <template #header><b>🤖 AI辅助初筛结果</b></template>
      <div style="text-align:center;padding:20px" v-if="screening"><el-icon :size="48" color="#409EFF"><Loading /></el-icon><p>AI正在分析，请稍候...</p></div>
      <div v-else>
        <el-alert :title="'风险提示：' + result.riskLevel" :type="result.urgency==='紧急'?'error':result.urgency==='常规'?'success':'warning'" :description="result.recommendations.join('；')" show-icon :closable="false" style="margin-bottom:16px" />
        <el-descriptions border :column="2">
          <el-descriptions-item label="风险等级">{{ result.riskLevel }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ result.urgency }}</el-descriptions-item>
          <el-descriptions-item label="建议科室">{{ result.department }}</el-descriptions-item>
          <el-descriptions-item label="AI置信度">{{ (result.aiConfidence*100).toFixed(1) }}%</el-descriptions-item>
        </el-descriptions>
        <el-alert type="warning" title="⚠️ 注意" description="以上为AI辅助筛查结果，不能替代专业医疗判断。请由医务人员进行最终审核。" :closable="false" style="margin-top:16px" />
        <div style="margin-top:16px"><el-button @click="step=1">上一步</el-button><el-button type="primary" @click="step=3">查看辅助提示</el-button></div>
      </div>
    </el-card>

    <!-- Step 4 -->
    <el-card v-if="step===3" shadow="never">
      <template #header><b>💡 AI辅助筛查提示（教学参考）</b></template>
      <div v-for="(g,i) in guidelines" :key="i" style="margin-bottom:16px;padding:12px;background:#F8FAFC;border-radius:8px">
        <div style="font-weight:600">{{ g.title }}</div>
        <div style="color:var(--text2);font-size:0.85rem;margin-top:4px">{{ g.content }}</div>
        <el-tag size="small" style="margin-top:8px" type="info">📚 教学参考（未核验）</el-tag>
      </div>
      <el-alert type="warning" title="⚠️ 免责声明" description="本页面所有提示为教学演示内容，不构成医疗建议。实际应用中应由医务人员结合临床判断做出决策。" :closable="false" style="margin-bottom:16px" />
      <el-button type="success" @click="submitCase" :loading="submitting">✅ 提交教学案例</el-button>
      <el-button @click="step=2">上一步</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import {
  medicalRecordApi,
  preConsultationApi,
} from '@/api'

interface ApiErrorResponse {
  message?: string
}

const router = useRouter()
const store = useAppStore()

const step = ref(0)
const symptomInput = ref('')
const screening = ref(false)
const submitting = ref(false)

const form = reactive({
  name: '',
  gender: '',
  age: 0,
  symptoms: [] as string[],
  duration: '',
  selfRate: 3,
})

const quickSymptoms = [
  '模拟症状-A',
  '模拟症状-B',
  '模拟症状-C',
  '模拟症状-D',
  '模拟症状-E',
  '红旗标志-F',
  '红旗标志-G',
  '模拟症状-H',
]

const durations = [
  '< 24小时',
  '1-3天',
  '3-7天',
  '1-2周',
  '> 1个月',
]

const result = reactive({
  riskLevel: '',
  urgency: '',
  department: '',
  recommendations: [] as string[],
  aiConfidence: 0,
})

const guidelines = ref([
  {
    title: 'AI辅助筛查提示示例',
    content:
      '检测到红旗症状组合时，AI辅助筛查系统会提示医务人员进行人工复核。本提示为教学示例，不构成实际医疗建议。',
  },
  {
    title: '关于风险评估的说明',
    content:
      'AI辅助筛查结果基于模拟训练数据，置信度仅供参考。所有最终诊断和处置方案应由具备资质的医务人员确定。',
  },
])

function addSymptom() {
  const symptom = symptomInput.value.trim()

  if (
    symptom &&
    !form.symptoms.includes(symptom)
  ) {
    form.symptoms.push(symptom)
  }

  symptomInput.value = ''
}

function addQuick(symptom: string) {
  if (!form.symptoms.includes(symptom)) {
    form.symptoms.push(symptom)
  }
}

function mapSeverity(
  selfRate: number,
): 'MILD' | 'MODERATE' | 'SEVERE' {
  if (selfRate <= 2) {
    return 'MILD'
  }

  if (selfRate <= 4) {
    return 'MODERATE'
  }

  return 'SEVERE'
}

function buildCaseCode(): string {
  return `SYN-${Date.now()}`
}

async function doScreening() {
  screening.value = true

  const flagCount = form.symptoms.filter(
    (symptom) => symptom.startsWith('红旗'),
  ).length

  window.setTimeout(() => {
    result.riskLevel =
      flagCount >= 2
        ? '检测到多个红旗标志，需人工审核'
        : '常规风险水平'

    result.urgency =
      flagCount >= 2
        ? '紧急'
        : '常规'

    result.department = '待医务人员确定'

    result.recommendations =
      flagCount >= 2
        ? [
            '检测到红旗症状组合，请医务人员立即进行人工审核',
            '建议综合评估后确定处置方案',
            '本结果为AI辅助提示，不能替代专业判断',
          ]
        : [
            '已完成本地教学规则预览',
            '请医务人员根据实际情况综合判断',
          ]

    result.aiConfidence = 0.85
    screening.value = false
    step.value = 2
  }, 800)
}

async function submitCase() {
  if (!store.user) {
    ElMessage.error('登录状态已失效，请重新登录')
    await router.push('/login')
    return
  }

  if (store.user.role !== 'patient') {
    ElMessage.warning(
      '当前阶段请使用“教学演示-模拟患者”账号发起预问诊',
    )
    return
  }

  if (!form.name.trim()) {
    ElMessage.warning('请填写案例编号')
    step.value = 0
    return
  }

  if (form.symptoms.length === 0) {
    ElMessage.warning('请至少录入一个症状')
    step.value = 1
    return
  }

  submitting.value = true

  try {
    const caseCode = buildCaseCode()

    // 1. 创建真实病例
    const recordResponse =
      await medicalRecordApi.create({
        patientId: store.user.userId,
        caseCode,
        chiefComplaint:
          `${form.name.trim()}：${form.symptoms.join('、')}`,
        presentIllness: [
          `性别：${form.gender || '未填写'}`,
          `年龄：${form.age || '未填写'}`,
          `持续时间：${form.duration || '未填写'}`,
          `严重程度自评：${form.selfRate}/5`,
        ].join('；'),
        pastHistory: '合成教学数据：未提供既往史',
        allergyHistory: '合成教学数据：未提供过敏史',
      })

    const record = recordResponse.data

    // 2. 保存每一条真实症状
    for (const symptomName of form.symptoms) {
      await medicalRecordApi.addSymptom(
        record.id,
        {
          recordId: record.id,
          symptomName,
          severity: mapSeverity(form.selfRate),
          durationDesc:
            form.duration || '未填写',
          notes: '由模拟患者在教学演示页面录入',
        },
      )
    }

    // 3. 发起真实预问诊
    const preConsultationResponse =
      await preConsultationApi.create({
        recordId: record.id,
      })

    const preConsultation =
      preConsultationResponse.data

    ElMessage.success(
      `提交成功：病例 ${record.caseCode}，预问诊 ID ${preConsultation.id}`,
    )

    await router.push('/dashboard')
  } catch (error: unknown) {
    const axiosError =
      error as AxiosError<ApiErrorResponse>

    const message =
      axiosError.response?.data?.message ||
      (error instanceof Error
        ? error.message
        : '未知错误')

    ElMessage.error(`提交失败：${message}`)
  } finally {
    submitting.value = false
  }
}
</script>