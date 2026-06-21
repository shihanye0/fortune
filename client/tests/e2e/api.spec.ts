import { test, expect } from '@playwright/test'

test.describe('API 接口测试', () => {
  test('健康检查接口正常', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health')
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.status).toBe('ok')
  })

  test('注册接口正常', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        username: 'e2e测试用户',
        email: `e2e_${Date.now()}@test.com`,
        password: 'Test1234',
        birth_year: 1990,
        birth_month: 5,
        birth_day: 15,
        birth_hour: 8,
        gender: 1,
      },
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.data.token).toBeTruthy()
  })

  test('登录接口正常', async ({ request }) => {
    // 先注册
    const email = `e2e_login_${Date.now()}@test.com`
    await request.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        username: '登录测试',
        email,
        password: 'Test1234',
        birth_year: 1990,
        birth_month: 5,
        birth_day: 15,
        birth_hour: 8,
        gender: 1,
      },
    })

    // 再登录
    const response = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email, password: 'Test1234' },
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.data.token).toBeTruthy()
  })

  test('获取运势需要认证', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/fortunes/today')
    expect(response.status()).toBe(401)
  })

  test('获取占卜记录需要认证', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/divination/records')
    expect(response.status()).toBe(401)
  })
})
