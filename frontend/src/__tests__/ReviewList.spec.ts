import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  createRouter: vi.fn(),
  createWebHistory: vi.fn(),
}))

describe('ReviewList.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('组件正常挂载并显示标题', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('审核案例列表')
    expect(wrapper.text()).toContain('合成教学案例')
  })

  it('默认全部筛选值显示所有案例', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    await new Promise(r => setTimeout(r, 500))
    const vm = wrapper.vm as any
    expect(vm.filteredCases.length).toBe(6)
  })

  it('合成教学案例编号使用SYN-前缀', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    await new Promise(r => setTimeout(r, 500))
    const vm = wrapper.vm as any
    vm.filteredCases.forEach((c: any) => expect(c.id).toContain('SYN-'))
  })
})
