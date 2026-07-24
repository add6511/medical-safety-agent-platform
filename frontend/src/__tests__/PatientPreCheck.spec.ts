import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'
import {
  flushPromises,
  mount,
  type VueWrapper,
} from '@vue/test-utils'
import {
  createPinia,
  setActivePinia,
} from 'pinia'
import ElementPlus from 'element-plus'
import {
  AxiosHeaders,
  type AxiosResponse,
} from 'axios'

import PatientPreCheck from '@/views/PatientPreCheck.vue'
import { useAppStore } from '@/stores/app'
import {
  medicalRecordApi,
  preConsultationApi,
} from '@/api'
import type {
  MedicalRecordResponse,
  PreConsultationResponse,
  SymptomResponse,
  TriageResultResponse,
} from '@/api'

const routerPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
}))

vi.mock('@/api', () => ({
  medicalRecordApi: {
    create: vi.fn(),
    addSymptom: vi.fn(),
  },
  preConsultationApi: {
    create: vi.fn(),
    executeAiTriage: vi.fn(),
  },
}))

function createAxiosResponse<T>(
  data: T,
): AxiosResponse<T> {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: new AxiosHeaders(),
    config: {
      headers: new AxiosHeaders(),
    },
  }
}

function mountPage(): VueWrapper {
  const pinia = createPinia()

  setActivePinia(pinia)

  const store = useAppStore()

  store.login(
    1,
    'demo_patient',
    'patient',
    'test-jwt-token',
  )

  return mount(PatientPreCheck, {
    global: {
      plugins: [
        pinia,
        ElementPlus,
      ],
    },
  })
}

function findButton(
  wrapper: VueWrapper,
  text: string,
) {
  const button = wrapper
    .findAll('button')
    .find((item) =>
      item.text().includes(text),
    )

  if (!button) {
    throw new Error(`未找到按钮：${text}`)
  }

  return button
}

async function fillCaseAndSymptoms(
  wrapper: VueWrapper,
) {
  const caseNameInput = wrapper.find(
    'input[placeholder="如：胸部不适教学案例"]',
  )

  expect(caseNameInput.exists()).toBe(true)

  await caseNameInput.setValue(
    '胸部不适真实AI测试',
  )

  await findButton(
    wrapper,
    '下一步',
  ).trigger('click')

  await flushPromises()

  const chestSymptomTag = wrapper
    .findAll('.el-tag')
    .find((tag) =>
      tag.text().includes(
        '持续胸部不适',
      ),
    )

  if (!chestSymptomTag) {
    throw new Error(
      '未找到“持续胸部不适”快捷症状',
    )
  }

  await chestSymptomTag.trigger('click')
  await flushPromises()
}

function createMedicalRecordResponse():
MedicalRecordResponse {
  return {
    id: 10,
    patientId: 1,
    caseCode:
      'SYN-11111111-1111-1111-1111-111111111111',
    chiefComplaint:
      '胸部不适真实AI测试：持续胸部不适',
    presentIllness:
      '年龄：45；持续时间：< 24小时',
    pastHistory:
      '合成教学数据',
    allergyHistory:
      '合成教学数据',
    status: 'CREATED',
    createdBy: 1,
    createdAt:
      '2026-07-24T16:00:00',
    updatedAt:
      '2026-07-24T16:00:00',
    symptoms: [],
  }
}

function createSymptomResponse():
SymptomResponse {
  return {
    id: 20,
    recordId: 10,
    symptomName:
      '持续胸部不适',
    bodyPart: null,
    severity: 'SEVERE',
    durationDesc: '未填写',
    onsetTime: null,
    notes:
      '由模拟患者在教学演示页面录入',
    createdAt:
      '2026-07-24T16:00:00',
    updatedAt:
      '2026-07-24T16:00:00',
  }
}

function createPreConsultationResponse():
PreConsultationResponse {
  return {
    id: 30,
    recordId: 10,
    patientId: 1,
    status: 'INITIATED',
    initiatedBy: 1,
    reviewedBy: null,
    reviewComment: null,
    reviewedAt: null,
    completedAt: null,
    createdAt:
      '2026-07-24T16:00:00',
    updatedAt:
      '2026-07-24T16:00:00',
  }
}

function createTriageResultResponse(
  traceId: string,
  id = 40,
): TriageResultResponse {
  return {
    id,
    preConsultationId: 30,
    urgencyLevel: 'URGENT',
    suggestedDepartment:
      '待医务人员确认',
    riskFlags: JSON.stringify({
      redFlags: [
        'persistent_chest_discomfort',
      ],
      safetyFlags: [],
      safetyStatus:
        'human_review',
      needsHumanReview: true,
    }),
    reasoningSummary:
      '症状摘要：持续胸部不适；风险等级：HIGH；安全状态：human_review',
    referenceSources:
      JSON.stringify({
        traceId,
        citations: [],
        evidence: [],
      }),
    createdAt:
      '2026-07-24T16:00:01',
  }
}

function mockSuccessfulApiFlow() {
  vi.mocked(
    medicalRecordApi.create,
  ).mockResolvedValue(
    createAxiosResponse(
      createMedicalRecordResponse(),
    ),
  )

  vi.mocked(
    medicalRecordApi.addSymptom,
  ).mockResolvedValue(
    createAxiosResponse(
      createSymptomResponse(),
    ),
  )

  vi.mocked(
    preConsultationApi.create,
  ).mockResolvedValue(
    createAxiosResponse(
      createPreConsultationResponse(),
    ),
  )

  vi.mocked(
    preConsultationApi.executeAiTriage,
  ).mockResolvedValue(
    createAxiosResponse(
      createTriageResultResponse(
        'trace-frontend-test-001',
      ),
    ),
  )
}

describe(
  'PatientPreCheck.vue',
  () => {
    beforeEach(() => {
      vi.clearAllMocks()
      localStorage.clear()

      vi.stubGlobal('crypto', {
        randomUUID: vi.fn(
          () =>
            '11111111-1111-1111-1111-111111111111',
        ),
      })
    })

    it(
      '显示真实AI分诊流程说明',
      () => {
        const wrapper = mountPage()

        expect(
          wrapper.text(),
        ).toContain(
          '分层预检问诊',
        )

        expect(
          wrapper.text(),
        ).toContain(
          '真实AI初筛',
        )

        expect(
          wrapper.text(),
        ).toContain(
          '所有数据均为虚构',
        )
      },
    )

    it(
      '完成病例、症状、预问诊和AI分诊调用',
      async () => {
        mockSuccessfulApiFlow()

        const wrapper = mountPage()

        await fillCaseAndSymptoms(
          wrapper,
        )

        await findButton(
          wrapper,
          '执行真实AI初筛',
        ).trigger('click')

        await flushPromises()
        await flushPromises()

        expect(
          medicalRecordApi.create,
        ).toHaveBeenCalledTimes(1)

        expect(
          medicalRecordApi.create,
        ).toHaveBeenCalledWith(
          expect.objectContaining({
            patientId: 1,
            caseCode:
              'SYN-11111111-1111-1111-1111-111111111111',
          }),
        )

        expect(
          medicalRecordApi.addSymptom,
        ).toHaveBeenCalledTimes(1)

        expect(
          medicalRecordApi.addSymptom,
        ).toHaveBeenCalledWith(
          10,
          expect.objectContaining({
            recordId: 10,
            symptomName:
              '持续胸部不适',
          }),
        )

        expect(
          preConsultationApi.create,
        ).toHaveBeenCalledWith({
          recordId: 10,
        })

        expect(
          preConsultationApi
            .executeAiTriage,
        ).toHaveBeenCalledWith(30)

        expect(
          wrapper.text(),
        ).toContain(
          '高风险（HIGH）',
        )

        expect(
          wrapper.text(),
        ).toContain(
          '优先处理（URGENT）',
        )

        expect(
          wrapper.text(),
        ).toContain(
          '持续胸部不适',
        )

        expect(
          wrapper.text(),
        ).toContain(
          '需要人工审核',
        )

        expect(
          wrapper.text(),
        ).toContain(
          'trace-frontend-test-001',
        )
      },
    )

    it(
      'AI调用失败后重试不会重复创建病例',
      async () => {
        vi.mocked(
          medicalRecordApi.create,
        ).mockResolvedValue(
          createAxiosResponse(
            createMedicalRecordResponse(),
          ),
        )

        vi.mocked(
          medicalRecordApi.addSymptom,
        ).mockResolvedValue(
          createAxiosResponse(
            createSymptomResponse(),
          ),
        )

        vi.mocked(
          preConsultationApi.create,
        ).mockResolvedValue(
          createAxiosResponse(
            createPreConsultationResponse(),
          ),
        )

        vi.mocked(
          preConsultationApi
            .executeAiTriage,
        )
          .mockRejectedValueOnce({
            response: {
              data: {
                message:
                  'AI服务连接失败',
              },
            },
          })
          .mockResolvedValueOnce(
            createAxiosResponse(
              createTriageResultResponse(
                'trace-retry-001',
                41,
              ),
            ),
          )

        const wrapper = mountPage()

        await fillCaseAndSymptoms(
          wrapper,
        )

        await findButton(
          wrapper,
          '执行真实AI初筛',
        ).trigger('click')

        await flushPromises()
        await flushPromises()

        expect(
          medicalRecordApi.create,
        ).toHaveBeenCalledTimes(1)

        expect(
          medicalRecordApi.addSymptom,
        ).toHaveBeenCalledTimes(1)

        expect(
          preConsultationApi.create,
        ).toHaveBeenCalledTimes(1)

        expect(
          preConsultationApi
            .executeAiTriage,
        ).toHaveBeenCalledTimes(1)

        await findButton(
          wrapper,
          '执行真实AI初筛',
        ).trigger('click')

        await flushPromises()
        await flushPromises()

        expect(
          medicalRecordApi.create,
        ).toHaveBeenCalledTimes(1)

        expect(
          medicalRecordApi.addSymptom,
        ).toHaveBeenCalledTimes(1)

        expect(
          preConsultationApi.create,
        ).toHaveBeenCalledTimes(1)

        expect(
          preConsultationApi
            .executeAiTriage,
        ).toHaveBeenCalledTimes(2)

        expect(
          wrapper.text(),
        ).toContain(
          'trace-retry-001',
        )
      },
    )
  },
)