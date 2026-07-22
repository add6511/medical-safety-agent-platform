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
    const vm = wrapper.vm as any
    expect(vm.statusFilter).toBe('all')
    // The computed should return all 6 cases
    expect(vm.filteredCases).toHaveLength(6)
  })

  it('筛选待审核过滤出2条案例', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    const vm = wrapper.vm as any
    vm.statusFilter = '待审核'
    await wrapper.vm.$nextTick()
    expect(vm.filteredCases).toHaveLength(2)
    expect(vm.filteredCases[0].status).toBe('待审核')
    expect(vm.filteredCases[1].status).toBe('待审核')
  })

  it('筛选审核中过滤出2条案例', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    const vm = wrapper.vm as any
    vm.statusFilter = '审核中'
    await wrapper.vm.$nextTick()
    expect(vm.filteredCases).toHaveLength(2)
  })

  it('筛选已完成过滤出2条案例', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    const vm = wrapper.vm as any
    vm.statusFilter = '已完成'
    await wrapper.vm.$nextTick()
    expect(vm.filteredCases).toHaveLength(2)
  })

  it('案例编号使用SYN-前缀', async () => {
    const { default: ReviewList } = await import('@/views/ReviewList.vue')
    const wrapper = mount(ReviewList, { global: { plugins: [createPinia(), ElementPlus] } })
    const vm = wrapper.vm as any
    expect(vm.filteredCases.length).toBeGreaterThan(0)
    for (const c of vm.filteredCases) {
      expect(c.id).toMatch(/^SYN-/)
    }
  })
})
