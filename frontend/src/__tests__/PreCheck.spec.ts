import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  createRouter: vi.fn(),
  createWebHistory: vi.fn(),
}))

describe('PatientPreCheck.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('显示合成教学案例标注和免责声明', async () => {
    const { default: PatientPreCheck } = await import('@/views/PatientPreCheck.vue')
    const wrapper = mount(PatientPreCheck, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('合成教学案例')
    expect(wrapper.text()).toContain('教学演示')
    expect(wrapper.text()).toContain('AI提示仅供辅助参考')
  })

  it('分步骤表单存在（4个步骤）', async () => {
    const { default: PatientPreCheck } = await import('@/views/PatientPreCheck.vue')
    const wrapper = mount(PatientPreCheck, { global: { plugins: [createPinia(), ElementPlus] } })
    const steps = wrapper.find('.el-steps')
    expect(steps.exists()).toBe(true)
  })

  it('预检问诊步骤切换——初始为步骤0（基本信息）', async () => {
    const { default: PatientPreCheck } = await import('@/views/PatientPreCheck.vue')
    const wrapper = mount(PatientPreCheck, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('基本信息')
    expect(wrapper.text()).toContain('症状录入')
  })
})
