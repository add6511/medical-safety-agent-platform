<template>
  <div>
    <div class="page-header" style="margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">🏥 医疗预检工作台（合成教学案例）</h2>
        <p style="color:var(--text2);font-size:0.85rem">⚠️ 所有案例均为虚构合成数据，仅用于教学演示。AI提示仅供辅助参考，不能替代专业判断。</p>
      </div>
      <div style="display:flex;gap:12px;align-items:center">
        <el-tag :type="statusType" effect="dark" round>{{ statusText }}</el-tag>
        <el-button type="primary" @click="$router.push('/pre-check')">
          <el-icon><Plus /></el-icon> 新建预检（教学演示）
        </el-button>
      </div>
    </div>
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6" v-for="s in stats" :key="s.label"><div class="stat-card"><div class="value" :style="{color:s.color}">{{ s.value }}</div><div class="label">{{ s.label }}</div></div></el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never"><template #header><div style="display:flex;justify-content:space-between;align-items:center"><span><b>📋 合成教学案例列表</b></span><el-input v-model="search" placeholder="搜索..." size="small" style="width:200px" clearable /></div></template>
          <el-table :data="filteredCases" max-height="450">
            <el-table-column prop="id" label="编号" width="120" />
            <el-table-column label="案例" width="130"><template #default="{row}"><el-tag size="small" type="info">{{ row.name }}</el-tag></template></el-table-column>
            <el-table-column label="红旗标志" width="150"><template #default="{row}"><el-tag :type="riskTagType(row.severity)" size="small">{{ row.symptoms.length }} 个红旗标志</el-tag></template></el-table-column>
            <el-table-column label="状态" width="100"><template #default="{row}">{{ statusLabel(row.status) }}</template></el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="130" />
            <el-table-column label="操作" width="160"><template #default="{row}"><el-button size="small" type="primary" link @click="$router.push('/review/'+row.id)">审核</el-button></template></el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom:16px"><template #header><b>📊 风险等级分布（合成数据）</b></template><v-chart :option="riskChartOption" style="height:180px" autoresize /></el-card>
        <el-card shadow="never"><template #header><div style="display:flex;justify-content:space-between;align-items:center"><span><b>🚨 AI 辅助安全提示</b></span><el-badge :value="alerts.length" :type="alertBadgeType" /></div></template>
          <div v-if="alerts.length===0" style="text-align:center;padding:20px;color:var(--text2)">✅ 暂无安全提示</div>
          <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="'alert-'+alert.level">
            <div style="display:flex;align-items:center;gap:8px"><el-icon :size="18" :color="alertColor(alert.level)"><WarningFilled /></el-icon><div><div style="font-weight:600;font-size:0.9rem">{{ alert.message }}</div><div style="font-size:0.75rem;color:var(--text2)">{{ alert.source }} · {{ alert.timestamp }}</div></div></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { type SafetyAlert } from '@/stores/app'
import { Plus, WarningFilled } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const router = useRouter()
const search = ref('')
const statusText = ref('AI 辅助监控运行中')
const statusType = ref<'success'>('success')

const stats = [
  { label: '待审核（合成案例）', value: 2, color: '#E6A23C' },
  { label: '今日预检（模拟）', value: 48, color: '#409EFF' },
  { label: '需重点关注', value: 3, color: '#F56C6C' },
  { label: '教学演示完成率', value: '87%', color: '#67C23A' },
]

interface DemoCase { id: string; name: string; symptoms: string[]; severity: string; status: string; createdAt: string }
const demoCases = ref<DemoCase[]>([
  { id: 'SYN-20240301', name: '合成案例001', symptoms: ['红旗标志A','红旗标志B','红旗标志C'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 09:30' },
  { id: 'SYN-20240302', name: '合成案例002', symptoms: ['模拟症状D','模拟症状E','模拟症状F'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 10:15' },
  { id: 'SYN-20240303', name: '合成案例003', symptoms: ['模拟症状G','模拟症状H'], severity: 'medium', status: 'approved', createdAt: '2024-03-15 11:00' },
  { id: 'SYN-20240304', name: '合成案例004', symptoms: ['模拟症状J','模拟症状K'], severity: 'low', status: 'completed', createdAt: '2024-03-15 08:45' },
  { id: 'SYN-20240305', name: '合成案例005', symptoms: ['红旗标志L','红旗标志M','红旗标志N'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 13:20' },
  { id: 'SYN-20240306', name: '合成案例006', symptoms: ['模拟症状O','模拟症状P','模拟症状Q'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 14:00' },
])

const filteredCases = computed(() => {
  if (!search.value) return demoCases.value
  const q = search.value.toLowerCase()
  return demoCases.value.filter(c => c.id.toLowerCase().includes(q) || c.name.includes(q))
})

const alerts = ref<SafetyAlert[]>([
  { id: '1', level: 'danger', message: 'SYN-20240301 检测到多个红旗症状组合，请立即人工审核！', source: 'AI辅助筛查', timestamp: '09:32' },
  { id: '2', level: 'warning', message: 'SYN-20240305 检测到需要重点关注的风险指标', source: 'AI辅助筛查', timestamp: '13:22' },
])

const riskChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: '0%', textStyle: { fontSize: 11 } },
  series: [{
    type: 'pie', radius: ['50%', '80%'], avoidLabelOverlap: false,
    label: { show: true, position: 'outside', formatter: '{b}: {c}' },
    data: [
      { value: 2, name: '需紧急审核', itemStyle: { color: '#8B0000' } },
      { value: 3, name: '需重点关注', itemStyle: { color: '#F56C6C' } },
      { value: 8, name: '常规关注', itemStyle: { color: '#E6A23C' } },
      { value: 15, name: '低风险', itemStyle: { color: '#67C23A' } },
    ],
  }],
}))

function riskTagType(s: string) { const m: Record<string,string>={critical:'danger',high:'danger',medium:'warning',low:'success'}; return m[s]||'info' }
function statusLabel(s: string) { const m: Record<string,string>={pending:'待审核',reviewing:'审核中',approved:'已通过',completed:'已完成'}; return m[s]||s }
function alertColor(l: string) { const m: Record<string,string>={danger:'#F56C6C',warning:'#E6A23C',info:'#409EFF'}; return m[l]||'#909399' }
const alertBadgeType = computed(() => 'danger')
</script>

<style scoped>
.alert-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; }
.alert-danger { background: #FFF0F0; border-left: 4px solid #F56C6C; }
.alert-warning { background: #FFF8E1; border-left: 4px solid #E6A23C; }
.alert-info { background: #F0F9FF; border-left: 4px solid #409EFF; }
</style>
