<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>🏥 医疗预检工作台</h1>
        <p style="color:var(--text2);margin-top:4px">Medical Pre-screening Dashboard</p>
      </div>
      <div style="display:flex;gap:12px;align-items:center">
        <el-tag :type="statusType" effect="dark" round>{{ statusText }}</el-tag>
        <el-button type="primary" @click="$router.push('/pre-check')">
          <el-icon><Plus /></el-icon> 新建预检
        </el-button>
        <el-dropdown @command="handleLogout">
          <el-avatar :size="36" icon="UserFilled" />
          <template #dropdown>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Stats Overview -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <div class="stat-card">
          <div class="value" :style="{color:s.color}">{{ s.value }}</div>
          <div class="label">{{ s.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- Case List -->
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span><b>📋 预检案例列表</b></span>
              <el-input v-model="search" placeholder="搜索..." size="small" style="width:200px" clearable />
            </div>
          </template>
          <el-table :data="filteredCases" style="width:100%" max-height="450">
            <el-table-column prop="id" label="编号" width="80" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column label="风险等级" width="110">
              <template #default="{row}">
                <el-tag :type="riskTagType(row.severity)" size="small">{{ riskLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{row}">{{ statusLabel(row.status) }}</template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="120" />
            <el-table-column label="操作" width="160">
              <template #default="{row}">
                <el-button size="small" type="primary" link @click="$router.push('/review/'+row.id)">审核</el-button>
                <el-button size="small" link @click="$router.push('/follow-up?patient='+row.id)">随访</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Side panels -->
      <el-col :span="10">
        <!-- Risk Distribution -->
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>📊 风险等级分布</b></template>
          <v-chart :option="riskChartOption" style="height:180px" autoresize />
        </el-card>

        <!-- AI Safety Alerts -->
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span><b>🚨 AI 安全警示</b></span>
              <el-badge :value="alerts.length" :type="alertBadgeType" />
            </div>
          </template>
          <div v-if="alerts.length === 0" style="text-align:center;padding:20px;color:var(--text2)">
            ✅ 暂无安全警示
          </div>
          <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="'alert-'+alert.level">
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon :size="18" :color="alertColor(alert.level)">
                <WarningFilled />
              </el-icon>
              <div>
                <div style="font-weight:600;font-size:0.9rem">{{ alert.message }}</div>
                <div style="font-size:0.75rem;color:var(--text2)">{{ alert.source }} · {{ alert.timestamp }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore, type PatientCase, type SafetyAlert } from '@/stores/app'
import { ElMessage } from 'element-plus'
import { Plus, WarningFilled } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const router = useRouter()
const store = useAppStore()
const search = ref('')
const statusText = ref('AI 监控运行中')
const statusType = ref<'success' | 'warning' | 'danger'>('success')

// Demo stats
const stats = [
  { label: '待审核案例', value: 12, color: '#E6A23C' },
  { label: '今日预检', value: 48, color: '#409EFF' },
  { label: '高风险预警', value: 3, color: '#F56C6C' },
  { label: '随访完成率', value: '87%', color: '#67C23A' },
]

// Demo cases
const demoCases = ref<PatientCase[]>([
  { id: 'P20240301', name: '张三', gender: '男', age: 45, symptoms: ['胸痛', '呼吸困难', '心悸'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 09:30' },
  { id: 'P20240302', name: '李四', gender: '女', age: 32, symptoms: ['头痛', '眩晕', '恶心'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 10:15' },
  { id: 'P20240303', name: '王五', gender: '男', age: 28, symptoms: ['发热', '咳嗽', '乏力'], severity: 'medium', status: 'approved', createdAt: '2024-03-15 11:00' },
  { id: 'P20240304', name: '赵六', gender: '女', age: 55, symptoms: ['关节痛', '晨僵'], severity: 'low', status: 'completed', createdAt: '2024-03-15 08:45' },
  { id: 'P20240305', name: '孙七', gender: '男', age: 67, symptoms: ['意识模糊', '血压升高', '言语不清'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 13:20' },
  { id: 'P20240306', name: '周八', gender: '女', age: 41, symptoms: ['腹痛', '腹泻', '脱水'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 14:00' },
])

const filteredCases = computed(() => {
  if (!search.value) return demoCases.value
  const q = search.value.toLowerCase()
  return demoCases.value.filter(c => c.name.includes(q) || c.id.toLowerCase().includes(q) || c.symptoms.some(s => s.includes(q)))
})

// Demo alerts
const alerts = ref<SafetyAlert[]>([
  { id: '1', level: 'danger', message: 'P20240301 患者症状匹配心肌梗死模式，请立即审核！', source: 'AI 安全 Agent', timestamp: '09:32' },
  { id: '2', level: 'warning', message: 'P20240305 患者 NIHSS 评分预估 >15，疑似急性脑卒中', source: 'AI 安全 Agent', timestamp: '13:22' },
])

// Risk chart
const riskChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%' },
  series: [{
    type: 'pie',
    radius: ['50%', '80%'],
    avoidLabelOverlap: false,
    label: { show: true, position: 'outside', formatter: '{b}: {c}' },
    data: [
      { value: 2, name: '危急', itemStyle: { color: '#8B0000' } },
      { value: 3, name: '高风险', itemStyle: { color: '#F56C6C' } },
      { value: 8, name: '中风险', itemStyle: { color: '#E6A23C' } },
      { value: 15, name: '低风险', itemStyle: { color: '#67C23A' } },
    ],
  }],
}))

function riskTagType(s: string) {
  const map: Record<string, any> = { critical: 'danger', high: 'danger', medium: 'warning', low: 'success' }
  return map[s] || 'info'
}
function riskLabel(s: string) {
  const map: Record<string, string> = { critical: '🚨 危急', high: '🔴 高风险', medium: '🟡 中风险', low: '🟢 低风险' }
  return map[s] || s
}
function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待审核', reviewing: '审核中', approved: '已通过', completed: '已完成' }
  return map[s] || s
}
function alertColor(l: string) {
  const map: Record<string, string> = { danger: '#F56C6C', warning: '#E6A23C', info: '#409EFF' }
  return map[l] || '#909399'
}
const alertBadgeType = computed(() => alerts.value.some(a => a.level === 'danger') ? 'danger' : 'warning')

function handleLogout(cmd: string) {
  if (cmd === 'logout') {
    store.logout()
    router.push('/login')
    ElMessage.success('已退出')
  }
}
</script>

<style scoped>
.alert-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}
.alert-danger { background: #FFF0F0; border-left: 4px solid #F56C6C; }
.alert-warning { background: #FFF8E1; border-left: 4px solid #E6A23C; }
.alert-info { background: #F0F9FF; border-left: 4px solid #409EFF; }
</style>
