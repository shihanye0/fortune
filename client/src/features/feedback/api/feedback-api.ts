import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'
import type {
  AccuracyStats,
  PredictionOutcome,
  PredictionOutcomeRequest,
} from '../types/feedback.types'

/**
 * 提交运势准确性标记
 * @param fortuneId - 运势记录 ID
 * @param accuracyMark - 准确性标记：1=准, 0=不准
 */
export async function submitFortuneAccuracy(
  fortuneId: number,
  accuracyMark: number,
): Promise<ApiResponse<null>> {
  const res = await client.post(`/api/v1/fortunes/${fortuneId}/accuracy`, {
    accuracy_mark: accuracyMark,
  })
  return res.data
}

/**
 * 提交占卜准确性标记
 * @param recordId - 占卜记录 ID
 * @param accuracyMark - 准确性标记：1=准, 0=不准
 */
export async function submitDivinationAccuracy(
  recordId: number,
  accuracyMark: number,
): Promise<ApiResponse<null>> {
  const res = await client.post(`/api/v1/divination/${recordId}/accuracy`, {
    accuracy_mark: accuracyMark,
  })
  return res.data
}

/**
 * 提交预测结果验证
 * @param data - 预测结果数据
 */
export async function submitPredictionOutcome(
  data: PredictionOutcomeRequest,
): Promise<ApiResponse<PredictionOutcome>> {
  const res = await client.post('/api/v1/prediction-outcomes', data)
  return res.data
}

/**
 * 获取准确率统计
 * 返回运势/占卜/维度准确率统计数据
 */
export async function getAccuracyStats(): Promise<ApiResponse<AccuracyStats>> {
  const res = await client.get('/api/v1/users/me/accuracy-stats')
  return res.data
}
