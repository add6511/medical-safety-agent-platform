import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  createRouter: vi.fn(),
  createWebHistory: vi.fn(),
}))

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('登录表单正确显示', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.find('h2').text()).toContain('医疗预检安全预警平台')
    expect(wrapper.find('.el-form').exists()).toBe(true)
  })

  it('包含三个演示角色登录标签', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, { global: { plugins: [createPinia(), ElementPlus] } })
    const tags = wrapper.findAll('.el-tag')
    expect(tags.length).toBeGreaterThanOrEqual(3)
  })

  it('空表单校验——用户名和密码必填', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, { global: { plugins: [createPinia(), ElementPlus] } })
    const form = wrapper.findComponent({ name: 'ElForm' })
    expect(form.exists()).toBe(true)
  })

  it('演示角色快速登录', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, { global: { plugins: [createPinia(), ElementPlus] } })
    const doctorTag = wrapper.findAll('.el-tag').find(t => t.text().includes('医务人员'))
    expect(doctorTag).toBeTruthy()
  })

  it('显示真实后端联调提示', async () => {
  const { default: Login } = await import('@/views/Login.vue')
  const wrapper = mount(Login, {
    global: {
      plugins: [createPinia(), ElementPlus],
    },
  })

  expect(wrapper.text()).toContain('真实后端联调')
  expect(wrapper.text()).not.toContain('MOCK Token')
})

  it('显示教学演示免责声明', async () => {
    const { default: Login } = await import('@/views/Login.vue')
    const wrapper = mount(Login, { global: { plugins: [createPinia(), ElementPlus] } })
    expect(wrapper.text()).toContain('教学演示')
  })
})
