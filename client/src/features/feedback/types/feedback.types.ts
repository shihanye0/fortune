/** 单项准确率统计 */
export interface AccuracyStatItem {
  total: number
  accurate: number
  rate: number
}

/** 维度准确率统计 */
export interface DimensionStatItem {
  total: number
  accurate: number
  rate: number
}

/** 整体准确率统计 */
export interface AccuracyStats {
  fortune_accuracy: AccuracyStatItem
  divination_accuracy: AccuracyStatItem
  dimension_accuracy: Record<string, DimensionStatItem>
}

/** 预测结果记录 */
export interface PredictionOutcome {
  id: number
  source_type: 'fortune' | 'divination'
  source_id: number
  outcome_text: string
  verified: boolean | null
  verified_at: string | null
  created_at: string
}

/** 提交预测结果请求 */
export interface PredictionOutcomeRequest {
  source_type: 'fortune' | 'divination'
  source_id: number
  outcome_text: string
  verified: boolean
}
