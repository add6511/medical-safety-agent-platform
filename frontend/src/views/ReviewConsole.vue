<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>🔍 医务人员审核控制台</h1>
        <p style="color:var(--text2)">Medical Staff Review Console</p>
      </div>
      <el-button @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>

    <el-row :gutter="16">
      <!-- Patient Info -->
      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>👤 患者信息</b></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="姓名">张三</el-descriptions-item>
            <el-descriptions-item label="性别">男</el-descriptions-item>
            <el-descriptions-item label="年龄">45 岁</el-descriptions-item>
            <el-descriptions-item label="既往病史">高血压、高血脂</el-descriptions-item>
            <el-descriptions-item label="症状">
              <el-tag v-for="s in ['胸痛','呼吸困难','心悸']" :key="s" size="small" style="margin:2px">{{ s }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="持续时间">3-7天</el-descriptions-item>
            <el-descriptions-item label="自评严重度">
              <el-rate :model-value="5" disabled show-text text="严重" />
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- AI Triage Result -->
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <b>🤖 AI 预筛结果</b>
              <el-tag type="danger">置信度 94.2%</el-tag>
            </div>
          </template>
          <el-alert title="危急" type="error" description="症状组合与急性心肌梗死高度匹配，建议立即进行 ECG 和肌钙蛋白检测" show-icon :closable="false" style="margin-bottom:12px" />
          <div style="font-size:0.85rem;color:var(--text2)">
            <p>📌 建议科室：心血管内科 / 急诊科</p>
            <p>📌 紧急程度：立即处理</p>
            <p>📌 关键鉴别：主动脉夹层、肺栓塞、心包炎</p>
          </div>
        </el-card>
      </el-col>

      <!-- Review Actions -->
      <el-col :span="14">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>📋 审核决策</b></template>
          <el-form label-width="100px">
            <el-form-item label="审核结论">
              <el-radio-group v-model="decision">
                <el-radio value="approved">✅ 通过 — AI 判断正确</el-radio>
                <el-radio value="modified">📝 修正 — 调整后通过</el-radio>
                <el-radio value="rejected">❌ 驳回 — 需要补充信息</el-radio>
                <el-radio value="escalated">🚨 升级 — 立即转急诊</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="调整风险等级" v-if="decision==='modified'">
              <el-select v-model="adjustedRisk" style="width:200px">
                <el-option label="危急" value="critical" /><el-option label="高风险" value="high" />
                <el-option label="中风险" value="medium" /><el-option label="低风险" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="医生意见">
              <el-input v-model="doctorNote" type="textarea" :rows="3" placeholder="补充诊断意见..." />
            </el-form-item>
            <el-form-item label="建议科室">
              <el-select v-model="referDepartment" style="width:200px">
                <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitReview">提交审核</el-button>
              <el-button @click="$router.push('/dashboard')">暂存</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Timeline -->
        <el-card shadow="never">
          <template #header><b>⏱️ 症状时间线</b></template>
          <el-timeline>
            <el-timeline-item timestamp="2024-03-15 09:30" type="danger">
              <b>患者提交预检</b><br/>主诉胸痛、呼吸困难、心悸
            </el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:32" type="warning">
              <b>AI 安全 Agent 触发预警</b><br/>症状匹配心肌梗死模式
            </el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:35" type="primary">
              <b>RAG 检索相关指南</b><br/>匹配心血管病学指南 3 条
            </el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:40" color="#909399">
              <b>等待医务人员审核</b>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const decision = ref('approved')
const adjustedRisk = ref('high')
const doctorNote = ref('')
const referDepartment = ref('心血管内科')

const departments = ['心血管内科', '急诊科', '神经内科', '呼吸内科', '消化内科', '骨科', '内分泌科', '精神科', '普外科']

function submitReview() {
  ElMessage.success('审核已提交')
  router.push('/dashboard')
}
</script>
