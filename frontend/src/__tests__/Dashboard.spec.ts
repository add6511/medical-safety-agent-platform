import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ path: '/dashboard' }),
  createRouter: vi.fn(),
  createWebHistory: vi.fn(),
}))

describe('MedicalDashboard.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('显示合成教学案例标注', async () => {
    const { default: MedicalDashboard } = await import('@/views/MedicalDashboard.vue')
    const wrapper = mount(MedicalDashboard, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('合成教学案例')
  })

  it('显示教学演示免责声明', async () => {
    const { default: MedicalDashboard } = await import('@/views/MedicalDashboard.vue')
    const wrapper = mount(MedicalDashboard, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('所有案例均为虚构合成数据')
  })

  it('案例使用SYN前缀编号', async () => {
    const { default: MedicalDashboard } = await import('@/views/MedicalDashboard.vue')
    const wrapper = mount(MedicalDashboard, { global: { plugins: [createPinia(), ElementPlus] } })
    const html = wrapper.html()
    expect(html).toContain('SYN-')
  })

  it('红旗案例显示人工审核提示', async () => {
    const { default: MedicalDashboard } = await import('@/views/MedicalDashboard.vue')
    const wrapper = mount(MedicalDashboard, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('人工审核')
  })
})
