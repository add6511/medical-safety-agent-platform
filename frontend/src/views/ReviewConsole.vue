<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div>
        <h2 style="font-size:1.3rem">🔍 医务人员审核控制台（合成教学案例）</h2>
        <p style="color:var(--text2);font-size:0.85rem">⚠️ 所有数据和AI提示均为教学演示，不能替代专业医疗判断</p>
      </div>
      <el-button @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>👤 教学案例信息</b></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="案例编号">SYN-20240301</el-descriptions-item>
            <el-descriptions-item label="名称">合成案例001</el-descriptions-item>
            <el-descriptions-item label="性别">男</el-descriptions-item>
            <el-descriptions-item label="年龄">45 岁</el-descriptions-item>
            <el-descriptions-item label="模拟红旗标志">
              <el-tag v-for="s in ['红旗标志A','红旗标志B','红旗标志C']" :key="s" size="small" type="danger" style="margin:2px">{{ s }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模拟持续时间">3-7天</el-descriptions-item>
            <el-descriptions-item label="自评严重度"><el-rate :model-value="5" disabled show-text text="严重" /></el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card shadow="never">
          <template #header><div style="display:flex;justify-content:space-between;align-items:center"><b>🤖 AI辅助筛查结果</b><el-tag type="danger">置信度 94.2%</el-tag></div></template>
          <el-alert title="检测到红旗症状组合" type="error" description="案例存在多个红旗标志，建议医务人员进行综合评估。AI辅助筛查结果仅供辅助参考，不能替代专业判断。" show-icon :closable="false" style="margin-bottom:12px" />
          <div style="font-size:0.85rem;color:var(--text2)">
            <p>📌 建议科室：待医务人员确定</p>
            <p>📌 紧急程度：建议优先处理</p>
            <p>📌 红旗标志数量：3个</p>
            <p style="margin-top:8px;color:var(--warning)">⚠️ 本案例为合成教学数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>📋 审核决策</b></template>
          <el-form label-width="100px">
            <el-form-item label="审核结论"><el-radio-group v-model="decision"><el-radio value="approved">✅ 通过</el-radio><el-radio value="modified">📝 需调整</el-radio><el-radio value="rejected">❌ 驳回</el-radio><el-radio value="escalated">🚨 升级处理</el-radio></el-radio-group></el-form-item>
            <el-form-item label="医务人员意见"><el-input v-model="doctorNote" type="textarea" :rows="3" placeholder="人工审核意见..." /></el-form-item>
            <el-form-item label="建议科室"><el-select v-model="referDepartment" style="width:200px"><el-option v-for="d in departments" :key="d" :label="d" :value="d" /></el-select></el-form-item>
            <el-form-item><el-button type="primary" @click="submitReview">提交审核</el-button><el-button @click="$router.push('/dashboard')">暂存</el-button></el-form-item>
          </el-form>
        </el-card>
        <el-card shadow="never">
          <template #header><b>⏱️ 事件时间线（教学演示）</b></template>
          <el-timeline>
            <el-timeline-item timestamp="2024-03-15 09:30" type="danger"><b>提交预检</b><br/>录入模拟红旗标志：A、B、C</el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:32" type="warning"><b>AI辅助筛查触发</b><br/>检测到多个红旗标志</el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:35" type="primary"><b>AI辅助筛查完成</b><br/>生成风险提示，建议人工审核</el-timeline-item>
            <el-timeline-item timestamp="2024-03-15 09:40" color="#909399"><b>等待医务人员审核</b></el-timeline-item>
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
const doctorNote = ref('')
const referDepartment = ref('待确定')
const departments = ['待确定', '内科', '外科', '急诊科', '神经科', '儿科', '妇产科', '骨科']

function submitReview() { ElMessage.success('审核已提交（教学演示）'); router.push('/dashboard') }
</script>
