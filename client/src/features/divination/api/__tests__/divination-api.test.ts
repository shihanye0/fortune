import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/shared/api/client', () => ({
  default: {
    post: vi.fn(),
  },
}))

import client from '@/shared/api/client'
import { doLiuyao, doQimen } from '../divination-api'

describe('divination API', () => {
  beforeEach(() => {
    vi.mocked(client.post).mockReset()
    vi.mocked(client.post).mockResolvedValue({ data: { success: true } })
  })

  it('allows enough time for LLM-backed liuyao interpretations', async () => {
    await doLiuyao({ question: '最近工作是否顺利', method: 'coin' })

    expect(client.post).toHaveBeenCalledWith(
      '/api/v1/divination/liuyao',
      { question: '最近工作是否顺利', method: 'coin' },
      { timeout: 120000 },
    )
  })

  it('allows enough time for LLM-backed qimen interpretations', async () => {
    await doQimen({ question: '明天面试是否顺利', mode: 'question' })

    expect(client.post).toHaveBeenCalledWith(
      '/api/v1/divination/qimen',
      { question: '明天面试是否顺利', mode: 'question' },
      { timeout: 120000 },
    )
  })
})
