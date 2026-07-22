<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>📅 随访计划管理</h1>
        <p style="color:var(--text2)">Follow-up Plan & Compliance Tracking</p>
      </div>
      <el-button @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>

    <el-row :gutter="16">
      <!-- Compliance Overview -->
      <el-col :span="8">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><b>📊 依从性总览</b></template>
          <div style="text-align:center">
            <el-progress type="dashboard" :percentage="compliance" :color="complianceColor" :stroke-width="12">
              <template #default="{ percentage }">
                <span style="font-size:2rem;font-weight:700">{{ percentage }}%</span>
              </template>
            </el-progress>
            <p style="margin-top:8px;color:var(--text2)">随访依从率</p>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><b>📌 计划概览</b></template>
          <el-statistic title="总任务数" :value="tasks.length" />
          <el-statistic title="已完成" :value="completedCount" style="margin-top:12px" />
          <el-statistic title="逾期未完成" :value="overdueCount" style="margin-top:12px">
            <template #suffix><span style="color:#F56C6C">⚠️</span></template>
          </el-statistic>
        </el-card>
      </el-col>

      <!-- Task List -->
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <b>📋 随访任务列表</b>
              <el-button type="primary" size="small" @click="showAddDialog=true">
                <el-icon><Plus /></el-icon> 添加任务
              </el-button>
            </div>
          </template>

          <el-table :data="tasks" style="width:100%">
            <el-table-column type="index" width="50" label="#" />
            <el-table-column prop="title" label="任务" min-width="150" />
            <el-table-column label="类型" width="110">
              <template #default="{row}">
                <el-tag :type="taskTypeColor(row.type)" size="small">{{ taskTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dueDate" label="截止日期" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="row.completed ? 'success' : (isOverdue(row) ? 'danger' : 'warning')" size="small">
                  {{ row.completed ? '已完成' : (isOverdue(row) ? '已逾期' : '进行中') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{row, $index}">
                <el-button v-if="!row.completed" size="small" type="success" link @click="completeTask($index)">完成</el-button>
                <el-button size="small" type="danger" link @click="removeTask($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- Add Task Dialog -->
    <el-dialog v-model="showAddDialog" title="添加随访任务" width="450px">
      <el-form :model="newTask">
        <el-form-item label="任务标题">
          <el-input v-model="newTask.title" placeholder="如：复查心电图" />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="newTask.type" style="width:100%">
            <el-option label="💊 用药" value="medication" />
            <el-option label="🏥 复查" value="checkup" />
            <el-option label="🏃 生活方式" value="lifestyle" />
            <el-option label="👨‍⚕️ 复诊" value="consultation" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="newTask.dueDate" type="date" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog=false">取消</el-button>
        <el-button type="primary" @click="addTask">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

interface Task { id: string; title: string; dueDate: string; completed: boolean; type: string }

const showAddDialog = ref(false)
const newTask = reactive({ title: '', type: 'checkup', dueDate: '' as any })

const tasks = ref<Task[]>([
  { id: '1', title: '复查心电图 + 肌钙蛋白', dueDate: '2024-03-22', completed: true, type: 'checkup' },
  { id: '2', title: '按时服用阿司匹林 100mg/天', dueDate: '2024-04-15', completed: false, type: 'medication' },
  { id: '3', title: '低盐低脂饮食，每日步行30分钟', dueDate: '2024-04-01', completed: false, type: 'lifestyle' },
  { id: '4', title: '心血管内科复诊', dueDate: '2024-03-30', completed: false, type: 'consultation' },
  { id: '5', title: '血压监测每周2次并记录', dueDate: '2024-03-20', completed: false, type: 'checkup' },
])

const completedCount = computed(() => tasks.value.filter(t => t.completed).length)
const overdueCount = computed(() => tasks.value.filter(t => !t.completed && isOverdue(t)).length)
const compliance = computed(() => tasks.value.length ? Math.round((completedCount.value / tasks.value.length) * 100) : 0)
const complianceColor = computed(() => {
  if (compliance.value >= 80) return '#67C23A'
  if (compliance.value >= 50) return '#E6A23C'
  return '#F56C6C'
})

function isOverdue(t: Task) { return new Date(t.dueDate) < new Date() }
function taskTypeColor(t: string) {
  const map: Record<string, any> = { medication: 'danger', checkup: 'primary', lifestyle: 'success', consultation: 'warning' }
  return map[t] || 'info'
}
function taskTypeLabel(t: string) {
  const map: Record<string, string> = { medication: '💊 用药', checkup: '🏥 复查', lifestyle: '🏃 生活', consultation: '👨‍⚕️ 复诊' }
  return map[t] || t
}

function completeTask(i: number) {
  tasks.value[i].completed = true
  ElMessage.success('任务已完成')
}
function removeTask(i: number) {
  tasks.value.splice(i, 1)
  ElMessage.success('任务已删除')
}
function addTask() {
  if (!newTask.title) return
  tasks.value.push({
    id: Date.now().toString(),
    title: newTask.title,
    type: newTask.type,
    dueDate: newTask.dueDate instanceof Date ? newTask.dueDate.toISOString().split('T')[0] : newTask.dueDate,
    completed: false,
  })
  showAddDialog.value = false
  newTask.title = ''; newTask.type = 'checkup'; newTask.dueDate = null
  ElMessage.success('任务已添加')
}
</script>
