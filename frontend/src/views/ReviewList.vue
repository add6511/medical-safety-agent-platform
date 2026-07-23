<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <div><h2 style="font-size:1.3rem">📋 审核案例列表（合成教学案例）</h2><p style="color:var(--text2);font-size:0.85rem">待审核预检案例 · AI辅助筛查结果标注</p></div>
      <el-radio-group v-model="statusFilter" size="small"><el-radio-button value="all">全部</el-radio-button><el-radio-button value="待审核">待审核</el-radio-button><el-radio-button value="审核中">审核中</el-radio-button><el-radio-button value="已完成">已完成</el-radio-button></el-radio-group>
    </div>
    <div v-if="error" style="text-align:center;padding:40px"><el-alert type="error" title="加载失败" :description="error" show-icon :closable="false" /><el-button type="primary" size="small" @click="fetchCases" style="margin-top:12px">重试</el-button></div>
    <div v-else-if="filteredCases.length===0" style="text-align:center;padding:40px"><el-empty :description="statusFilter==='all'?'暂无案例数据':'没有匹配该状态的案例'" /></div>
    <el-table v-else v-loading="loading" :data="filteredCases" max-height="500" @row-click="goReview" style="cursor:pointer">
      <el-table-column type="index" width="50" label="#" /><el-table-column prop="id" label="编号" width="120" />
      <el-table-column label="案例" width="130"><template #default="{row}"><el-tag size="small" type="info">{{ row.name }}</el-tag></template></el-table-column>
      <el-table-column label="红旗标志" min-width="180"><template #default="{row}"><el-tag v-for="s in row.symptoms" :key="s" size="small" style="margin:1px">{{ s }}</el-tag></template></el-table-column>
      <el-table-column label="AI风险提示" width="150"><template #default="{row}"><el-tag :type="riskColor(row.severity)" size="small" effect="dark">{{ riskLabel(row.severity) }}</el-tag></template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{row}"><el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="createdAt" label="提交时间" width="130" /><el-table-column label="操作" width="100"><template #default="{row}"><el-button size="small" type="primary" @click.stop="$router.push('/review/'+row.id)">审核</el-button></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; import { useRouter } from 'vue-router'
const router = useRouter(); const statusFilter = ref('all'); const loading = ref(false); const error = ref('')
const cases = ref<any[]>([])

const fetchCases = async () => { loading.value = true; error.value = ''
  try { await new Promise(r=>setTimeout(r,200))
    cases.value = [
      {id:'SYN-20240301',name:'合成案例001',symptoms:['红旗标志A','红旗标志B','红旗标志C'],severity:'critical',status:'待审核',createdAt:'03-15 09:30'},
      {id:'SYN-20240305',name:'合成案例005',symptoms:['红旗标志L','红旗标志M','红旗标志N'],severity:'critical',status:'待审核',createdAt:'03-15 13:20'},
      {id:'SYN-20240302',name:'合成案例002',symptoms:['模拟症状D','模拟症状E','模拟症状F'],severity:'high',status:'审核中',createdAt:'03-15 10:15'},
      {id:'SYN-20240306',name:'合成案例006',symptoms:['模拟症状O','模拟症状P','模拟症状Q'],severity:'high',status:'审核中',createdAt:'03-15 14:00'},
      {id:'SYN-20240303',name:'合成案例003',symptoms:['模拟症状G','模拟症状H'],severity:'medium',status:'已完成',createdAt:'03-15 11:00'},
      {id:'SYN-20240304',name:'合成案例004',symptoms:['模拟症状J','模拟症状K'],severity:'low',status:'已完成',createdAt:'03-15 08:45'},
    ]
  } catch { error.value = '无法加载案例列表' } finally { loading.value = false }
}
onMounted(fetchCases)

const filteredCases = computed(() => { if(statusFilter.value==='all') return cases.value; return cases.value.filter(c=>c.status===statusFilter.value) })
function goReview(r:any){router.push('/review/'+r.id)}
function riskColor(s:string){const m:Record<string,string>={critical:'',high:'danger',medium:'warning',low:'success'};return m[s]||'info'}
function riskLabel(s:string){const m:Record<string,string>={critical:'🚨需紧急审核',high:'🔴需关注',medium:'🟡常规',low:'🟢低风险'};return m[s]||s}
function statusColor(s:string){const m:Record<string,string>={'待审核':'danger','审核中':'warning','已完成':'success'};return m[s]||'info'}
</script>
