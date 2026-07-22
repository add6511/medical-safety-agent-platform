<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">🛡️ 安全审计面板</h2>
        <p style="color:var(--text2);font-size:0.85rem">越权检测 · 提示词注入 · 隐私泄露监控 · 模型版本审计</p>
      </div>
      <el-select v-model="timeRange" size="small" style="width:120px">
        <el-option label="今天" value="today" /><el-option label="本周" value="week" /><el-option label="本月" value="month" />
      </el-select>
    </div>

    <!-- Stats -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <div class="audit-stat">
          <div class="audit-val" :style="{color:s.color}">{{ s.value }}</div>
          <div class="audit-label">{{ s.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- Audit Log Table -->
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b>📋 安全审计日志</b>
          <el-radio-group v-model="filter" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="privilege">越权</el-radio-button>
            <el-radio-button value="injection">注入</el-radio-button>
            <el-radio-button value="privacy">隐私</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="filteredLogs" max-height="450">
        <el-table-column prop="timestamp" label="时间" width="160" />
        <el-table-column label="类型" width="100">
          <template #default="{row}">
            <el-tag :type="tagType(row.type)" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="80">
          <template #default="{row}">
            <el-tag :type="row.level==='严重'?'danger':row.level==='警告'?'warning':'info'" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user" label="用户" width="120" />
        <el-table-column prop="action" label="操作" min-width="200" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{row}">
            <el-tag :type="row.result==='已拦截'?'success':'danger'" size="small">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Version Audit -->
    <el-card shadow="never" style="margin-top:16px">
      <template #header><b>📦 模型 / Prompt / 知识库版本审计</b></template>
      <el-table :data="versionLogs" max-height="250">
        <el-table-column prop="component" label="组件" width="180" />
        <el-table-column prop="version" label="版本号" width="150" />
        <el-table-column prop="updatedBy" label="更新人" width="120" />
        <el-table-column prop="updatedAt" label="更新时间" width="170" />
        <el-table-column prop="changeLog" label="变更说明" min-width="200" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const timeRange = ref('today')
const filter = ref('all')

const stats = [
  { value: 3, label: '越权拦截', color: '#F56C6C' },
  { value: 1, label: '注入检测', color: '#E6A23C' },
  { value: 0, label: '隐私泄露', color: '#67C23A' },
  { value: 'v2.3', label: '当前模型版本', color: '#409EFF' },
]

const logs = [
  { timestamp: '2024-03-15 13:25:01', type: '越权访问', level: '严重', user: '模拟患者', action: '尝试访问 /api/admin/users 管理接口', result: '已拦截' },
  { timestamp: '2024-03-15 11:30:15', type: '提示词注入', level: '警告', user: '未知', action: '检测到 Prompt Injection 攻击载荷', result: '已拦截' },
  { timestamp: '2024-03-15 10:45:00', type: '越权访问', level: '严重', user: '模拟患者', action: '尝试修改其他患者病例 P20240303', result: '已拦截' },
  { timestamp: '2024-03-15 09:20:00', type: '越权访问', level: '警告', user: '模拟患者', action: '尝试访问随访计划管理接口', result: '已拦截' },
  { timestamp: '2024-03-14 16:00:00', type: '隐私泄露', level: '警告', user: '系统', action: '日志中检测到未脱敏的手机号输出', result: '已修复' },
]

const versionLogs = [
  { component: 'AI 预检模型', version: 'deepseek-chat v4', updatedBy: '管理员', updatedAt: '2024-03-14 10:00', changeLog: '升级至最新版本，优化心血管疾病识别准确率' },
  { component: 'Triage Prompt', version: 'v2.3-medical-triage', updatedBy: '管理员', updatedAt: '2024-03-13 15:30', changeLog: '增加 NIHSS 评分预估逻辑' },
  { component: '医疗知识库', version: 'v1.8-cardiovascular', updatedBy: '管理员', updatedAt: '2024-03-12 09:00', changeLog: '更新中华心血管病学指南 2023 版' },
  { component: '安全检查 Prompt', version: 'v1.2-safety-check', updatedBy: '管理员', updatedAt: '2024-03-10 14:00', changeLog: '增加提示词注入检测规则' },
]

const filteredLogs = computed(() => {
  if (filter.value === 'all') return logs
  const m: Record<string, string> = { privilege: '越权访问', injection: '提示词注入', privacy: '隐私泄露' }
  return logs.filter(l => l.type === m[filter.value])
})

function tagType(t: string) {
  const m: Record<string, string> = { '越权访问': 'danger', '提示词注入': 'warning', '隐私泄露': 'info' }
  return m[t] || 'info'
}
</script>

<style scoped>
.audit-stat {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  text-align: center;
}
.audit-val { font-size: 2rem; font-weight: 700; }
.audit-label { font-size: 0.85rem; color: var(--text2); margin-top: 4px; }
</style>
