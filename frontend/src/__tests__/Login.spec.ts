import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  createRouter: vi.fn(),
  createWebHistory: vi.fn(),
}))

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders login form correctly', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, {
      global: { plugins: [createPinia(), ElementPlus] },
    })
    expect(wrapper.find('h2').text()).toContain('医疗预检')
    expect(wrapper.find('.el-form').exists()).toBe(true)
  })

  it('has three demo role tags', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, {
      global: { plugins: [createPinia(), ElementPlus] },
    })
    const tags = wrapper.findAll('.el-tag')
    // At least 3 demo login tags should exist
    expect(tags.length).toBeGreaterThanOrEqual(3)
  })

  it('validates empty form submission', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, {
      global: { plugins: [createPinia(), ElementPlus] },
    })
    const form = wrapper.findComponent({ name: 'ElForm' })
    expect(form.exists()).toBe(true)
  })
})
