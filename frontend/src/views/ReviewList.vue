<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">📋 审核案例列表</h2>
        <p style="color:var(--text2);font-size:0.85rem">待审核预检案例 · AI 预筛结果标注 · 医务人员最终审核</p>
      </div>
      <el-radio-group v-model="statusFilter" size="small">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="reviewing">审核中</el-radio-button>
        <el-radio-button value="completed">已完成</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="filteredCases" max-height="500" @row-click="goReview" style="cursor:pointer">
      <el-table-column type="index" width="50" label="#" />
      <el-table-column prop="id" label="编号" width="110" />
      <el-table-column prop="name" label="姓名" width="80" />
      <el-table-column prop="gender" label="性别" width="60" />
      <el-table-column prop="age" label="年龄" width="60" />
      <el-table-column label="症状" min-width="180">
        <template #default="{row}">
          <el-tag v-for="s in row.symptoms" :key="s" size="small" style="margin:1px">{{ s }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="AI 风险" width="120">
        <template #default="{row}">
          <el-tag :type="riskColor(row.severity)" size="small" effect="dark">
            {{ riskLabel(row.severity) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{row}">
          <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="提交时间" width="120" />
      <el-table-column label="操作" width="100">
        <template #default="{row}">
          <el-button size="small" type="primary" @click.stop="$router.push('/review/'+row.id)">审核</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const statusFilter = ref('all')

const cases = [
  { id: 'P20240301', name: '张三', gender: '男', age: 45, symptoms: ['胸痛','呼吸困难','心悸'], severity: 'critical', status: '待审核', createdAt: '03-15 09:30' },
  { id: 'P20240305', name: '孙七', gender: '男', age: 67, symptoms: ['意识模糊','血压升高','言语不清'], severity: 'critical', status: '待审核', createdAt: '03-15 13:20' },
  { id: 'P20240302', name: '李四', gender: '女', age: 32, symptoms: ['头痛','眩晕','恶心'], severity: 'high', status: '审核中', createdAt: '03-15 10:15' },
  { id: 'P20240306', name: '周八', gender: '女', age: 41, symptoms: ['腹痛','腹泻','脱水'], severity: 'high', status: '审核中', createdAt: '03-15 14:00' },
  { id: 'P20240303', name: '王五', gender: '男', age: 28, symptoms: ['发热','咳嗽','乏力'], severity: 'medium', status: '已完成', createdAt: '03-15 11:00' },
  { id: 'P20240304', name: '赵六', gender: '女', age: 55, symptoms: ['关节痛','晨僵'], severity: 'low', status: '已完成', createdAt: '03-15 08:45' },
]

const filteredCases = computed(() => {
  if (statusFilter.value === 'all') return cases
  return cases.filter(c => c.status === statusFilter.value)
})

function goReview(row: any) { router.push('/review/' + row.id) }
function riskColor(s: string) { const m: Record<string,string>={critical:'',high:'danger',medium:'warning',low:'success'}; return m[s]||'info' }
function riskLabel(s: string) { const m: Record<string,string>={critical:'🚨危急',high:'🔴高',medium:'🟡中',low:'🟢低'}; return m[s]||s }
function statusColor(s: string) { const m: Record<string,string>={'待审核':'danger','审核中':'warning','已完成':'success'}; return m[s]||'info' }
</script>
