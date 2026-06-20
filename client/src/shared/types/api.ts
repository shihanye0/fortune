/** 统一 API 响应格式 */
export interface ApiResponse<T = unknown> {
  success: boolean
  data: T
  error: ApiError | null
  meta: PaginationMeta | null
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, string[]>
}

export interface PaginationMeta {
  total: number
  page: number
  limit: number
  totalPages: number
}

/** 分页请求参数 */
export interface PaginationParams {
  page: number
  limit: number
}
