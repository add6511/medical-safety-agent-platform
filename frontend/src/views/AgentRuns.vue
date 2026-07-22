<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">🤖 Agent 执行日志</h2>
        <p style="color:var(--text2);font-size:0.85rem">查看 AI Agent 执行过程、检索资源和推理链路</p>
      </div>
      <el-input v-model="search" placeholder="搜索 Agent ID 或案例..." style="width:280px" clearable :prefix-icon="Search" />
    </div>

    <el-table :data="filteredRuns" style="width:100%" max-height="500">
      <el-table-column prop="id" label="Agent ID" width="100" />
      <el-table-column prop="caseId" label="关联案例" width="130" />
      <el-table-column prop="type" label="类型" width="130">
        <template #default="{row}">
          <el-tag :type="typeColor(row.type)" size="small">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="row.status==='完成'?'success':row.status==='运行中'?'warning':'danger'" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="80" />
      <el-table-column prop="tokens" label="Token" width="80" />
      <el-table-column prop="startedAt" label="开始时间" width="160" />
      <el-table-column label="操作" width="120">
        <template #default="{row}">
          <el-button size="small" type="primary" link @click="showDetail(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="Agent 执行详情" width="700px" top="5vh">
      <template v-if="selectedRun">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="Agent ID">{{ selectedRun.id }}</el-descriptions-item>
          <el-descriptions-item label="关联案例">{{ selectedRun.caseId }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedRun.type }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selectedRun.status }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ selectedRun.duration }}</el-descriptions-item>
          <el-descriptions-item label="Token 消耗">{{ selectedRun.tokens }}</el-descriptions-item>
          <el-descriptions-item label="模型版本">deepseek-chat v4</el-descriptions-item>
          <el-descriptions-item label="Prompt 版本">v2.3-medical-triage</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">推理链路</el-divider>
        <el-timeline>
          <el-timeline-item v-for="(step, i) in selectedRun.steps" :key="i"
            :type="step.type" :timestamp="step.time" placement="top">
            <div style="font-weight:600">{{ step.title }}</div>
            <div style="font-size:0.8rem;color:var(--text2)">{{ step.detail }}</div>
          </el-timeline-item>
        </el-timeline>

        <el-divider content-position="left">检索资源</el-divider>
        <div v-for="(cite, i) in selectedRun.citations" :key="i"
          style="padding:8px 12px;background:#F8FAFC;border-radius:8px;margin-bottom:8px">
          <el-tag size="small" style="margin-right:8px">📚 {{ cite.source }}</el-tag>
          <span style="font-size:0.85rem">{{ cite.content }}</span>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface AgentRun {
  id: string; caseId: string; type: string; status: string; duration: string;
  tokens: number; startedAt: string; steps: any[]; citations: any[];
}

const search = ref('')
const detailVisible = ref(false)
const selectedRun = ref<AgentRun | null>(null)

const demoRuns: AgentRun[] = [
  {
    id: 'RUN-001', caseId: 'P20240301', type: '安全预检 Agent', status: '完成',
    duration: '1.2s', tokens: 1847, startedAt: '2024-03-15 09:30:15',
    steps: [
      { type: 'primary', time: '09:30:15', title: '接收症状输入', detail: '主诉：胸痛、呼吸困难、心悸' },
      { type: 'primary', time: '09:30:16', title: 'RAG 知识检索', detail: '检索心血管疾病指南，匹配 3 条相关文献' },
      { type: 'warning', time: '09:30:16', title: '风险预警触发', detail: '症状组合匹配心肌梗死模式 (置信度 94.2%)' },
      { type: 'danger', time: '09:30:17', title: '生成安全警示', detail: '标记为危急级别，建议立即 ECG 检查' },
    ],
    citations: [
      { source: '中华心血管病学指南 2023', content: '对于急性胸痛患者，应在首次医疗接触后10分钟内完成ECG检查。' },
      { source: '中国高血压防治指南 2024', content: '高血压急症需在1小时内将血压降低25%，避免过度降压。' },
      { source: '急性冠脉综合征诊疗规范', content: '肌钙蛋白是诊断心肌梗死的首选生物标志物。' },
    ],
  },
  {
    id: 'RUN-002', caseId: 'P20240305', type: '安全检查 Agent', status: '完成',
    duration: '0.8s', tokens: 1256, startedAt: '2024-03-15 13:20:08',
    steps: [
      { type: 'primary', time: '13:20:08', title: '接收症状输入', detail: '主诉：意识模糊、血压升高、言语不清' },
      { type: 'warning', time: '13:20:09', title: 'NIHSS 评估', detail: 'NIHSS 评分预估 >15，疑似急性脑卒中' },
      { type: 'danger', time: '13:20:09', title: '生成安全警示', detail: '标记为危急级别，建议立即神经内科会诊' },
    ],
    citations: [
      { source: '中国急性缺血性脑卒中诊治指南 2023', content: '发病4.5小时内是静脉溶栓的黄金时间窗。' },
      { source: 'NIHSS 评分标准', content: 'NIHSS评分>15提示大血管闭塞可能，需考虑血管内治疗。' },
    ],
  },
  {
    id: 'RUN-003', caseId: 'P20240302', type: '安全预检 Agent', status: '运行中',
    duration: '0.5s', tokens: 623, startedAt: '2024-03-15 14:30:00',
    steps: [{ type: 'primary', time: '14:30:00', title: '正在处理中...', detail: '分析症状组合' }],
    citations: [],
  },
]

const filteredRuns = computed(() => {
  if (!search.value) return demoRuns
  const q = search.value.toLowerCase()
  return demoRuns.filter(r => r.id.toLowerCase().includes(q) || r.caseId.toLowerCase().includes(q))
})

function typeColor(t: string) {
  const m: Record<string, string> = { '安全预检 Agent': 'primary', '安全检查 Agent': 'warning' }
  return m[t] || 'info'
}

function showDetail(run: AgentRun) {
  selectedRun.value = run
  detailVisible.value = true
}
</script>
