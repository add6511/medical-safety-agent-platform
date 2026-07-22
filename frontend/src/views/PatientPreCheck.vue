<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>📝 分层预检问诊</h1>
        <p style="color:var(--text2)">Tiered Pre-check Consultation</p>
      </div>
      <el-button @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>

    <!-- Progress Steps -->
    <el-steps :active="step" finish-status="success" align-center style="margin-bottom:32px">
      <el-step title="基本信息" />
      <el-step title="症状录入" />
      <el-step title="风险初筛" />
      <el-step title="AI 辅助建议" />
    </el-steps>

    <!-- Step 1: Basic Info -->
    <el-card v-if="step === 0" shadow="never">
      <template #header><b>👤 患者基本信息</b></template>
      <el-form :model="form" label-width="100px" style="max-width:600px">
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="性别" required>
              <el-select v-model="form.gender" style="width:100%">
                <el-option label="男" value="male" /><el-option label="女" value="female" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年龄" required><el-input-number v-model="form.age" :min="0" :max="120" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="联系方式"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="既往病史">
          <el-select v-model="form.history" multiple placeholder="请选择（可多选）" style="width:100%">
            <el-option v-for="h in historyOptions" :key="h" :label="h" :value="h" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="step=1" :disabled="!form.name||!form.gender||!form.age">下一步</el-button></el-form-item>
      </el-form>
    </el-card>

    <!-- Step 2: Symptoms -->
    <el-card v-if="step === 1" shadow="never">
      <template #header><b>🤒 症状录入</b></template>
      <div style="margin-bottom:16px">
        <el-tag v-for="s in form.symptoms" :key="s" closable @close="form.symptoms=form.symptoms.filter(x=>x!==s)" style="margin:4px">
          {{ s }}
        </el-tag>
      </div>
      <el-input v-model="symptomInput" placeholder="输入症状后按回车添加" @keyup.enter="addSymptom" style="max-width:400px" />
      <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px">
        <el-tag v-for="s in quickSymptoms" :key="s" @click="addQuick(s)" style="cursor:pointer" :type="form.symptoms.includes(s)?'':''|'info'">
          {{ s }}
        </el-tag>
      </div>
      <el-form-item label="症状持续时间">
        <el-select v-model="form.duration" style="width:200px">
          <el-option v-for="d in durations" :key="d" :label="d" :value="d" />
        </el-select>
      </el-form-item>
      <el-form-item label="严重程度自评">
        <el-rate v-model="form.selfRate" :max="5" show-text :texts="['很轻','轻度','中度','较重','严重']" />
      </el-form-item>
      <el-form-item>
        <el-button @click="step=0">上一步</el-button>
        <el-button type="primary" @click="step=2" :disabled="form.symptoms.length===0">下一步：AI 风险初筛</el-button>
      </el-form-item>
    </el-card>

    <!-- Step 3: AI Risk Screening -->
    <el-card v-if="step === 2" shadow="never">
      <template #header><b>🤖 AI 风险初筛</b></template>
      <div style="text-align:center;padding:20px" v-if="screening">
        <el-icon :size="48" color="#409EFF"><Loading /></el-icon>
        <p>AI 正在分析症状，请稍候...</p>
      </div>
      <div v-else>
        <el-alert :title="'风险等级：' + result.riskLevel" :type="result.urgency === '紧急' ? 'error' : result.urgency === '需关注' ? 'warning' : 'success'" :description="result.recommendations.join('；')" show-icon :closable="false" style="margin-bottom:16px" />
        <el-descriptions border :column="2">
          <el-descriptions-item label="风险等级">{{ result.riskLevel }}</el-descriptions-item>
          <el-descriptions-item label="紧急程度">{{ result.urgency }}</el-descriptions-item>
          <el-descriptions-item label="建议科室">{{ result.department }}</el-descriptions-item>
          <el-descriptions-item label="AI 置信度">{{ (result.aiConfidence * 100).toFixed(1) }}%</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:16px">
          <el-button @click="step=1">上一步</el-button>
          <el-button type="primary" @click="step=3">查看 AI 辅助建议</el-button>
        </div>
      </div>
    </el-card>

    <!-- Step 4: AI Guidelines -->
    <el-card v-if="step === 3" shadow="never">
      <template #header><b>💡 AI 辅助建议 & 医疗指南</b></template>
      <div v-for="(g, i) in guidelines" :key="i" style="margin-bottom:16px;padding:12px;background:#F8FAFC;border-radius:8px">
        <div style="font-weight:600">{{ g.title }}</div>
        <div style="color:var(--text2);font-size:0.85rem;margin-top:4px">{{ g.content }}</div>
        <el-tag size="small" style="margin-top:8px">📚 来源：{{ g.source }}</el-tag>
      </div>
      <el-button type="success" @click="submitCase" :loading="submitting">✅ 提交预检案例</el-button>
      <el-button @click="step=2">上一步</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()
const step = ref(0)
const symptomInput = ref('')
const screening = ref(false)
const submitting = ref(false)

const form = reactive({
  name: '', gender: '', age: 0, contact: '', history: [] as string[],
  symptoms: [] as string[], duration: '', selfRate: 3,
})

const historyOptions = ['高血压', '糖尿病', '心脏病', '哮喘', '肾病', '肝病', '肿瘤', '手术史', '过敏史', '精神疾病']
const quickSymptoms = ['发热', '头痛', '胸痛', '腹痛', '咳嗽', '呼吸困难', '眩晕', '恶心', '乏力', '关节痛', '心悸', '皮疹', '腹泻', '失眠', '焦虑']
const durations = ['< 24小时', '1-3天', '3-7天', '1-2周', '2周-1月', '> 1个月', '反复发作']

const result = reactive({ riskLevel: '', urgency: '', department: '', recommendations: [] as string[], aiConfidence: 0 })
const guidelines = ref([
  { title: '急性心肌梗死鉴别指南', content: '对于胸痛+呼吸困难+心悸组合，建议立即进行 ECG 和肌钙蛋白检测。时间窗口：症状开始后 30 分钟内。', source: '中华医学会心血管病学分会指南 2023' },
  { title: '高血压急症处理规范', content: '血压 >180/120mmHg 伴靶器官损害征象时，应在 1 小时内将血压降低 25%。', source: '中国高血压防治指南 2024' },
])

function addSymptom() {
  const s = symptomInput.value.trim()
  if (s && !form.symptoms.includes(s)) { form.symptoms.push(s) }
  symptomInput.value = ''
}
function addQuick(s: string) {
  if (!form.symptoms.includes(s)) form.symptoms.push(s)
}

async function submitCase() {
  submitting.value = true
  setTimeout(() => {
    ElMessage.success('预检案例已提交，等待医务人员审核')
    router.push('/dashboard')
    submitting.value = false
  }, 1000)
}
</script>
