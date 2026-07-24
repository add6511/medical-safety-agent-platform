<template>
  <div>
    <div
      style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
      "
    >
      <div>
        <h2 style="font-size: 1.3rem">
          📝 分层预检问诊（合成教学案例）
        </h2>

        <p
          style="
            color: var(--text2);
            font-size: 0.85rem;
          "
        >
          ⚠️ 本页面为教学演示。所有数据均为虚构，AI
          提示仅供辅助参考。
        </p>
      </div>

      <el-button @click="router.push('/dashboard')">
        返回工作台
      </el-button>
    </div>

    <el-steps
      :active="step"
      finish-status="success"
      align-center
      style="margin-bottom: 32px"
    >
      <el-step title="基本信息" />
      <el-step title="症状录入" />
      <el-step title="真实AI初筛" />
      <el-step title="安全提示" />
    </el-steps>

    <!-- 第一步：基本信息 -->
    <el-card
      v-if="step === 0"
      shadow="never"
    >
      <template #header>
        <b>👤 教学案例基本信息</b>
      </template>

      <el-form
        :model="form"
        label-width="100px"
        style="max-width: 600px"
      >
        <el-form-item
          label="案例名称"
          required
        >
          <el-input
            v-model="form.name"
            placeholder="如：胸部不适教学案例"
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select
                v-model="form.gender"
                style="width: 100%"
              >
                <el-option
                  label="男"
                  value="male"
                />

                <el-option
                  label="女"
                  value="female"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="年龄">
              <el-input-number
                v-model="form.age"
                :min="0"
                :max="120"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button
            type="primary"
            :disabled="!form.name.trim()"
            @click="step = 1"
          >
            下一步
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 第二步：症状录入 -->
    <el-card
      v-if="step === 1"
      shadow="never"
    >
      <template #header>
        <b>🏷️ 模拟症状录入</b>
      </template>

      <div style="margin-bottom: 16px">
        <el-tag
          v-for="symptom in form.symptoms"
          :key="symptom"
          closable
          style="margin: 4px"
          @close="removeSymptom(symptom)"
        >
          {{ symptom }}
        </el-tag>
      </div>

      <el-input
        v-model="symptomInput"
        placeholder="输入症状描述后按回车添加"
        style="max-width: 400px"
        @keyup.enter="addSymptom"
      />

      <div
        style="
          margin-top: 16px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        "
      >
        <el-tag
          v-for="symptom in quickSymptoms"
          :key="symptom"
          :type="
            form.symptoms.includes(symptom)
              ? ''
              : 'info'
          "
          style="cursor: pointer"
          @click="addQuick(symptom)"
        >
          {{ symptom }}
        </el-tag>
      </div>

      <el-form-item
        label="模拟持续时间"
        style="margin-top: 16px"
      >
        <el-select
          v-model="form.duration"
          style="width: 200px"
        >
          <el-option
            v-for="duration in durations"
            :key="duration"
            :label="duration"
            :value="duration"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="严重程度自评">
        <el-rate
          v-model="form.selfRate"
          :max="5"
          show-text
          :texts="[
            '很轻',
            '轻度',
            '中度',
            '较重',
            '严重',
          ]"
        />
      </el-form-item>

      <el-alert
        type="info"
        title="真实联调说明"
        description="点击下一步后，系统会保存病例和症状，创建预问诊，并通过 Spring Boot 调用 FastAPI 执行真实安全分诊。"
        :closable="false"
        style="margin-bottom: 16px"
      />

      <el-form-item>
        <el-button
          :disabled="screening"
          @click="step = 0"
        >
          上一步
        </el-button>

        <el-button
          type="primary"
          :loading="screening"
          :disabled="form.symptoms.length === 0"
          @click="doScreening"
        >
          下一步：执行真实AI初筛
        </el-button>
      </el-form-item>
    </el-card>

    <!-- 第三步：真实 AI 结果 -->
    <el-card
      v-if="step === 2"
      shadow="never"
    >
      <template #header>
        <b>🤖 真实 AI 辅助初筛结果</b>
      </template>

      <div
        v-if="screening"
        style="
          text-align: center;
          padding: 30px;
        "
      >
        <el-icon
          class="is-loading"
          :size="48"
          color="#409EFF"
        >
          <Loading />
        </el-icon>

        <p>正在保存病例并执行 AI 安全分诊……</p>
      </div>

      <div v-else>
        <el-alert
          :title="`风险提示：${riskLevelLabel(result.riskLevel)}`"
          :type="getAlertType(result.urgencyLevel)"
          :description="result.reasoningSummary || 'AI 服务未返回详细说明'"
          show-icon
          :closable="false"
          style="margin-bottom: 16px"
        />

        <el-descriptions
          border
          :column="2"
        >
          <el-descriptions-item label="病例编号">
            {{ result.caseCode }}
          </el-descriptions-item>

          <el-descriptions-item label="预问诊ID">
            {{ result.preConsultationId }}
          </el-descriptions-item>

          <el-descriptions-item label="风险等级">
            {{ riskLevelLabel(result.riskLevel) }}
          </el-descriptions-item>

          <el-descriptions-item label="紧急程度">
            {{ urgencyLevelLabel(result.urgencyLevel) }}
          </el-descriptions-item>

          <el-descriptions-item label="建议科室">
            {{ result.department }}
          </el-descriptions-item>

          <el-descriptions-item label="安全状态">
            {{ safetyStatusLabel(result.safetyStatus) }}
          </el-descriptions-item>

          <el-descriptions-item label="追踪ID">
            {{ result.traceId || '未返回' }}
          </el-descriptions-item>

          <el-descriptions-item label="是否需要人工审核">
            <el-tag
              :type="
                result.needsHumanReview
                  ? 'danger'
                  : 'success'
              "
            >
              {{
                result.needsHumanReview
                  ? '需要'
                  : '暂不需要'
              }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 20px">
          <h4 style="margin-bottom: 10px">
            🚩 红旗标志
          </h4>

          <div v-if="result.redFlags.length > 0">
            <el-tag
              v-for="flag in result.redFlags"
              :key="flag"
              type="danger"
              effect="dark"
              style="margin: 4px"
            >
              {{ redFlagLabel(flag) }}
            </el-tag>
          </div>

          <el-empty
            v-else
            description="未检测到明确红旗标志"
            :image-size="60"
          />
        </div>

        <div
          v-if="result.safetyFlags.length > 0"
          style="margin-top: 20px"
        >
          <h4 style="margin-bottom: 10px">
            🛡️ 安全检查标志
          </h4>

          <el-tag
            v-for="flag in result.safetyFlags"
            :key="flag"
            type="warning"
            style="margin: 4px"
          >
            {{ flag }}
          </el-tag>
        </div>

        <el-alert
          v-if="result.needsHumanReview"
          type="error"
          title="必须进行人工审核"
          description="AI 安全分诊认为该案例需要医务人员进一步复核。请勿将本结果直接作为诊断或处置依据。"
          :closable="false"
          show-icon
          style="margin-top: 20px"
        />

        <el-alert
          v-else
          type="warning"
          title="AI 结果仍需专业判断"
          description="即使当前未触发强制人工审核，AI 结果也只能作为辅助信息，不能替代医务人员判断。"
          :closable="false"
          show-icon
          style="margin-top: 20px"
        />

        <div style="margin-top: 20px">
          <el-button
            type="primary"
            @click="step = 3"
          >
            查看安全提示
          </el-button>

          <el-button
            @click="router.push('/dashboard')"
          >
            返回工作台
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 第四步：安全提示 -->
    <el-card
      v-if="step === 3"
      shadow="never"
    >
      <template #header>
        <b>💡 AI 辅助筛查安全提示</b>
      </template>

      <div
        v-for="(guideline, index) in guidelines"
        :key="index"
        style="
          margin-bottom: 16px;
          padding: 12px;
          background: #f8fafc;
          border-radius: 8px;
        "
      >
        <div style="font-weight: 600">
          {{ guideline.title }}
        </div>

        <div
          style="
            color: var(--text2);
            font-size: 0.85rem;
            margin-top: 4px;
          "
        >
          {{ guideline.content }}
        </div>

        <el-tag
          size="small"
          style="margin-top: 8px"
          type="info"
        >
          📚 教学安全说明
        </el-tag>
      </div>

      <el-alert
        type="warning"
        title="免责声明"
        description="本页面所有病例均为合成教学数据，AI 分诊结果不构成医疗建议。实际应用必须由具备资质的医务人员结合临床情况作出判断。"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />

      <el-button
        @click="step = 2"
      >
        返回 AI 结果
      </el-button>

      <el-button
        type="success"
        @click="router.push('/dashboard')"
      >
        ✅ 完成并返回工作台
      </el-button>
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
import type {
  TriageResultResponse,
} from '@/api'

interface ApiErrorResponse {
  message?: string
}

interface RiskFlagsPayload {
  redFlags?: string[]
  safetyFlags?: string[]
  safetyStatus?: string
  needsHumanReview?: boolean
}

interface ReferenceSourcesPayload {
  traceId?: string
  citations?: unknown[]
  evidence?: unknown[]
}

interface ScreeningResult {
  caseCode: string
  preConsultationId: number | null
  riskLevel: string
  urgencyLevel:
    | 'EMERGENCY'
    | 'URGENT'
    | 'SEMI_URGENT'
    | 'ROUTINE'
  department: string
  reasoningSummary: string
  redFlags: string[]
  safetyFlags: string[]
  safetyStatus: string
  needsHumanReview: boolean
  traceId: string
}

const router = useRouter()
const store = useAppStore()

const step = ref(0)
const symptomInput = ref('')
const screening = ref(false)

const savedPreConsultationId =
  ref<number | null>(null)

const savedCaseCode = ref('')

const form = reactive({
  name: '',
  gender: '',
  age: 0,
  symptoms: [] as string[],
  duration: '',
  selfRate: 3,
})

const quickSymptoms = [
  '发热',
  '头痛',
  '咳嗽',
  '腹痛',
  '恶心',
  '持续胸部不适',
  '严重呼吸困难',
  '意识不清',
  '大量出血',
]

const durations = [
  '< 24小时',
  '1-3天',
  '3-7天',
  '1-2周',
  '> 1个月',
]

const result = reactive<ScreeningResult>({
  caseCode: '',
  preConsultationId: null,
  riskLevel: '',
  urgencyLevel: 'ROUTINE',
  department: '',
  reasoningSummary: '',
  redFlags: [],
  safetyFlags: [],
  safetyStatus: '',
  needsHumanReview: false,
  traceId: '',
})

const guidelines = [
  {
    title: 'AI 结果不能替代诊断',
    content:
      '本系统只提供风险分层和安全提示，不直接给出最终诊断、处方或治疗方案。',
  },
  {
    title: '红旗症状优先处理',
    content:
      '检测到持续胸部不适、严重呼吸困难、意识改变或无法控制的出血等红旗症状时，应优先转交医务人员人工审核。',
  },
  {
    title: 'AI 服务异常时必须降级',
    content:
      'AI 服务无法连接、响应超时或结果字段缺失时，不应继续自动决策，应保留病例并转入人工处理流程。',
  },
]

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

function removeSymptom(symptom: string) {
  form.symptoms = form.symptoms.filter(
    (item) => item !== symptom,
  )
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
  return `SYN-${crypto.randomUUID()}`
}

function parseJson<T>(
  value: string | null,
  fallback: T,
): T {
  if (!value) {
    return fallback
  }

  try {
    return JSON.parse(value) as T
  } catch {
    return fallback
  }
}

function extractRiskLevel(
  reasoningSummary: string | null,
  urgencyLevel: TriageResultResponse['urgencyLevel'],
): string {
  const matched =
    reasoningSummary?.match(
      /风险等级[：:]\s*(LOW|MEDIUM|HIGH|CRITICAL)/i,
    )

  if (matched?.[1]) {
    return matched[1].toUpperCase()
  }

  switch (urgencyLevel) {
    case 'EMERGENCY':
      return 'CRITICAL'

    case 'URGENT':
      return 'HIGH'

    case 'SEMI_URGENT':
      return 'MEDIUM'

    default:
      return 'LOW'
  }
}

function applyTriageResult(
  data: TriageResultResponse,
  caseCode: string,
) {
  const riskFlags =
    parseJson<RiskFlagsPayload>(
      data.riskFlags,
      {},
    )

  const references =
    parseJson<ReferenceSourcesPayload>(
      data.referenceSources,
      {},
    )

  result.caseCode = caseCode
  result.preConsultationId =
    data.preConsultationId

  result.riskLevel = extractRiskLevel(
    data.reasoningSummary,
    data.urgencyLevel,
  )

  result.urgencyLevel =
    data.urgencyLevel

  result.department =
    data.suggestedDepartment ||
    '待医务人员确认'

  result.reasoningSummary =
    data.reasoningSummary ||
    'AI 服务未返回详细推理摘要'

  result.redFlags =
    riskFlags.redFlags || []

  result.safetyFlags =
    riskFlags.safetyFlags || []

  result.safetyStatus =
    riskFlags.safetyStatus || 'unknown'

  result.needsHumanReview =
    Boolean(riskFlags.needsHumanReview)

  result.traceId =
    references.traceId || ''
}

function getErrorMessage(
  error: unknown,
): string {
  const axiosError =
    error as AxiosError<ApiErrorResponse>

  return (
    axiosError.response?.data?.message ||
    (error instanceof Error
      ? error.message
      : '未知错误')
  )
}

async function createPreConsultationData():
Promise<number> {
  if (!store.user) {
    throw new Error(
      '登录状态已失效，请重新登录',
    )
  }

  const caseCode = buildCaseCode()

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
      pastHistory:
        '合成教学数据：未提供既往史',
      allergyHistory:
        '合成教学数据：未提供过敏史',
    })

  const record = recordResponse.data

  for (const symptomName of form.symptoms) {
    await medicalRecordApi.addSymptom(
      record.id,
      {
        recordId: record.id,
        symptomName,
        severity:
          mapSeverity(form.selfRate),
        durationDesc:
          form.duration || '未填写',
        notes:
          '由模拟患者在教学演示页面录入',
      },
    )
  }

  const preConsultationResponse =
    await preConsultationApi.create({
      recordId: record.id,
    })

  savedCaseCode.value = record.caseCode

  savedPreConsultationId.value =
    preConsultationResponse.data.id

  return preConsultationResponse.data.id
}

async function doScreening() {
  if (!store.user) {
    ElMessage.error(
      '登录状态已失效，请重新登录',
    )

    await router.push('/login')
    return
  }

  if (store.user.role !== 'patient') {
    ElMessage.warning(
      '请使用“教学演示-模拟患者”账号执行预问诊',
    )
    return
  }

  if (!form.name.trim()) {
    ElMessage.warning('请填写案例名称')
    step.value = 0
    return
  }

  if (form.symptoms.length === 0) {
    ElMessage.warning('请至少录入一个症状')
    return
  }

  screening.value = true

  try {
    let preConsultationId =
      savedPreConsultationId.value

    if (!preConsultationId) {
      preConsultationId =
        await createPreConsultationData()
    }

    const triageResponse =
      await preConsultationApi
        .executeAiTriage(
          preConsultationId,
        )

    applyTriageResult(
      triageResponse.data,
      savedCaseCode.value,
    )

    step.value = 2

    ElMessage.success(
      `AI 分诊完成：${urgencyLevelLabel(result.urgencyLevel)}`,
    )
  } catch (error: unknown) {
    const message =
      getErrorMessage(error)

    if (savedPreConsultationId.value) {
      ElMessage.error(
        `病例已保存，但 AI 分诊失败：${message}。请确认 FastAPI 服务正常后重试。`,
      )
    } else {
      ElMessage.error(
        `病例提交失败：${message}`,
      )
    }
  } finally {
    screening.value = false
  }
}

function riskLevelLabel(
  riskLevel: string,
): string {
  switch (riskLevel) {
    case 'CRITICAL':
      return '危急风险（CRITICAL）'

    case 'HIGH':
      return '高风险（HIGH）'

    case 'MEDIUM':
      return '中等风险（MEDIUM）'

    case 'LOW':
      return '低风险（LOW）'

    default:
      return riskLevel || '未知'
  }
}

function urgencyLevelLabel(
  urgencyLevel:
    TriageResultResponse['urgencyLevel'],
): string {
  switch (urgencyLevel) {
    case 'EMERGENCY':
      return '紧急处置（EMERGENCY）'

    case 'URGENT':
      return '优先处理（URGENT）'

    case 'SEMI_URGENT':
      return '尽快处理（SEMI_URGENT）'

    case 'ROUTINE':
      return '常规处理（ROUTINE）'
  }
}

function safetyStatusLabel(
  status: string,
): string {
  switch (status) {
    case 'human_review':
      return '需要人工审核'

    case 'pass':
      return '安全检查通过'

    case 'blocked':
      return '已被安全机制拦截'

    default:
      return status || '未知'
  }
}

function getAlertType(
  urgencyLevel:
    TriageResultResponse['urgencyLevel'],
): 'error' | 'warning' | 'success' {
  if (
    urgencyLevel === 'EMERGENCY' ||
    urgencyLevel === 'URGENT'
  ) {
    return 'error'
  }

  if (urgencyLevel === 'SEMI_URGENT') {
    return 'warning'
  }

  return 'success'
}

function redFlagLabel(
  flag: string,
): string {
  const labels: Record<string, string> = {
    consciousness_change:
      '意识状态改变',
    severe_breathing_difficulty:
      '严重呼吸困难',
    persistent_chest_discomfort:
      '持续胸部不适',
    uncontrolled_bleeding:
      '无法控制的出血',
    self_harm_risk:
      '自伤风险',
    pregnancy_emergency_signal:
      '妊娠期紧急信号',
  }

  return labels[flag] || flag
}
</script>