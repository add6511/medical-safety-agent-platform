/**
 * GET/POST    /knowledge/documents
 * POST        /knowledge/search
 * DELETE      /knowledge/documents/{id}
 * snake_case 返回 → 适配层转 camelCase
 */
import { aiClient } from '../client'
import { env } from '../env'
import type { KnowledgeDocument, KnowledgeListResponse, KnowledgeSearchResponse } from '@/types/dto'

export async function listDocuments(): Promise<KnowledgeListResponse> {
  if (env.USE_MOCK) {
    return { total: 2, documents: [
      { id: '1', title: '教学参考-筛查提示', content: '检测到红旗症状组合时需人工复核。', source: '教学知识库', createdAt: '2024-03-01', tags: ['教学'] },
      { id: '2', title: '教学参考-风险评估', content: 'AI辅助筛查基于模拟数据，置信度仅供参考。', source: '教学知识库', createdAt: '2024-03-01', tags: ['教学'] },
    ]}
  }
  const { data } = await aiClient.get('/knowledge/documents')
  // snake_case → camelCase
  const raw = data as any
  return {
    total: raw.total || (Array.isArray(raw) ? raw.length : 0),
    documents: (raw.documents || (Array.isArray(raw) ? raw : [])).map((d: any) => ({
      id: d.id, title: d.title, content: d.content, source: d.source,
      createdAt: d.created_at || d.createdAt, tags: d.tags || [],
    })),
  }
}

export async function createDocument(payload: Omit<KnowledgeDocument, 'id' | 'createdAt'>): Promise<KnowledgeDocument> {
  if (env.USE_MOCK) return { id: Date.now().toString(), ...payload, createdAt: new Date().toISOString() }
  const { data } = await aiClient.post('/knowledge/documents', payload)
  const d: any = data as any
  return { id: d.id, title: d.title, content: d.content, source: d.source, createdAt: d.created_at || d.createdAt, tags: d.tags || [] }
}

export async function searchKnowledge(query: string, topK = 3): Promise<KnowledgeSearchResponse> {
  if (env.USE_MOCK) {
    return { query, topK: topK, results: [{ document: { id: '1', title: '教学参考', content: '模拟检索结果', source: 'Mock', createdAt: '', tags: [] }, score: 0.95, highlights: ['教学参考'] }], disclaimer: '本结果为教学演示，不构成真实医学建议。' }
  }
  const { data } = await aiClient.post('/knowledge/search', { query, top_k: topK })
  const raw = data as any
  return {
    query: raw.query || query,
    topK: raw.top_k || raw.topK || topK,
    results: (raw.results || []).map((r: any) => ({
      document: { id: r.document?.id, title: r.document?.title, content: r.document?.content, source: r.document?.source, createdAt: r.document?.created_at || r.document?.createdAt || '', tags: r.document?.tags || [] },
      score: r.score, highlights: r.highlights || [],
    })),
    disclaimer: raw.disclaimer || (env.USE_MOCK ? '教学演示结果' : ''),
  }
}

export async function deleteDocument(id: string): Promise<void> {
  if (!env.USE_MOCK) await aiClient.delete(`/knowledge/documents/${id}`)
}
