export interface User {
  id: number
  username: string
  email: string
  birthDate: string | null
  birthHour: number | null
  gender: string | null
  birthPlace: string | null
  pushEnabled: boolean
  pushChannel: string | null
  pushTime: string | null
  feishuWebhook: string | null
  createdAt: string
  updatedAt: string
}
