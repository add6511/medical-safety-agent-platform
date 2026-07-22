<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div><h2 style="font-size:1.3rem">🤖 Agent 执行日志（教学演示）</h2><p style="color:var(--text2);font-size:0.85rem">查看 AI 辅助筛查执行过程、检索资源和推理链路</p></div>
      <el-input v-model="search" placeholder="搜索 Agent ID..." style="width:280px" clearable :prefix-icon="Search" />
    </div>
    <el-table :data="filteredRuns" max-height="500">
      <el-table-column prop="id" label="Agent ID" width="100" />
      <el-table-column prop="caseId" label="关联案例" width="130" />
      <el-table-column prop="type" label="类型" width="150"><template #default="{row}"><el-tag type="primary" size="small">{{ row.type }}</el-tag></template></el-table-column>
      <el-table-column prop="status" label="状态" width="100"><template #default="{row}"><el-tag :type="row.status==='完成'?'success':row.status==='运行中'?'warning':'danger'" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="duration" label="耗时" width="80" />
      <el-table-column prop="tokens" label="Token" width="80" />
      <el-table-column prop="startedAt" label="开始时间" width="160" />
      <el-table-column label="操作" width="120"><template #default="{row}"><el-button size="small" type="primary" link @click="showDetail(row)">查看详情</el-button></template></el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="Agent 执行详情" width="700px" top="5vh">
      <template v-if="selectedRun">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="Agent ID">{{ selectedRun.id }}</el-descriptions-item>
          <el-descriptions-item label="关联案例">{{ selectedRun.caseId }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedRun.type }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selectedRun.status }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ selectedRun.duration }}</el-descriptions-item>
          <el-descriptions-item label="Token 消耗">{{ selectedRun.tokens }}</el-descriptions-item>
        </el-descriptions>
        <el-divider content-position="left">推理链路（教学演示）</el-divider>
        <el-timeline><el-timeline-item v-for="(step,i) in selectedRun.steps" :key="i" :type="step.type" :timestamp="step.time" placement="top"><div style="font-weight:600">{{ step.title }}</div><div style="font-size:0.8rem;color:var(--text2)">{{ step.detail }}</div></el-timeline-item></el-timeline>
        <el-divider content-position="left">检索资源（教学参考）</el-divider>
        <div v-for="(cite,i) in selectedRun.citations" :key="i" style="padding:8px 12px;background:#F8FAFC;border-radius:8px;margin-bottom:8px"><el-tag size="small" style="margin-right:8px" type="info">📚 教学参考</el-tag><span style="font-size:0.85rem">{{ cite.content }}</span></div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface AgentRun { id: string; caseId: string; type: string; status: string; duration: string; tokens: number; startedAt: string; steps: any[]; citations: any[] }

const search = ref('')
const detailVisible = ref(false)
const selectedRun = ref<AgentRun | null>(null)

const demoRuns: AgentRun[] = [
  { id: 'RUN-001', caseId: 'SYN-20240301', type: '辅助筛查 Agent', status: '完成', duration: '1.2s', tokens: 1847, startedAt: '2024-03-15 09:30:15',
    steps: [
      { type: 'primary', time: '09:30:15', title: '接收症状输入', detail: '输入：红旗标志A、红旗标志B、红旗标志C' },
      { type: 'primary', time: '09:30:16', title: 'AI辅助分析', detail: '检索教学参考资源，匹配 3 条相关参考' },
      { type: 'warning', time: '09:30:16', title: '风险提示生成', detail: '检测到红旗症状组合，建议人工审核' },
      { type: 'danger', time: '09:30:17', title: '生成辅助安全提示', detail: '标记为需紧急人工审核级别' },
    ],
    citations: [
      { content: '【教学参考】多个红旗症状组合出现时，建议优先安排医务人员进行综合评估。本参考为教学示例。' },
      { content: '【教学参考】AI辅助筛查系统的提示应作为医务人员决策的参考信息，而非最终诊断。' },
      { content: '【教学参考】所有教学案例数据均为虚构，不反映真实临床情况。' },
    ],
  },
  { id: 'RUN-002', caseId: 'SYN-20240305', type: '辅助筛查 Agent', status: '完成', duration: '0.8s', tokens: 1256, startedAt: '2024-03-15 13:20:08',
    steps: [
      { type: 'primary', time: '13:20:08', title: '接收症状输入', detail: '输入：红旗标志L、红旗标志M、红旗标志N' },
      { type: 'warning', time: '13:20:09', title: '风险指标评估', detail: '检测到多个红旗标志，建议重点关注' },
      { type: 'danger', time: '13:20:09', title: '生成辅助安全提示', detail: '标记为需紧急人工审核级别' },
    ],
    citations: [{ content: '【教学参考】多个红旗标志同时出现时，建议在医务人员指导下进行综合评估。' }],
  },
]

const filteredRuns = computed(() => {
  if (!search.value) return demoRuns
  const q = search.value.toLowerCase()
  return demoRuns.filter(r => r.id.toLowerCase().includes(q) || r.caseId.toLowerCase().includes(q))
})

function showDetail(run: AgentRun) { selectedRun.value = run; detailVisible.value = true }
</script>
