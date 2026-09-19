import { test, expect } from '@playwright/test'

test.describe('个人中心命盘基础', () => {
  test('已登录用户可查看可核对的命盘与计算口径', async ({ page }) => {
    const email = `bazi-${Date.now()}@example.com`
    const registerResponse = await page.request.post('/api/v1/auth/register', {
      data: {
        username: '命盘验收用户',
        email,
        password: 'Pass1234',
        birth_year: 1990,
        birth_month: 5,
        birth_day: 15,
        birth_hour: 8,
        gender: 1,
      },
    })
    expect(registerResponse.status()).toBe(201)
    const { data } = await registerResponse.json()

    await page.addInitScript((token) => localStorage.setItem('token', token), data.token)
    await page.goto('/profile')

    await expect(page.getByRole('heading', { name: '个人中心' })).toBeVisible()
    await expect(page.getByText('命盘基础')).toBeVisible()
    await expect(page.getByText('年柱')).toBeVisible()
    await expect(page.getByText('月柱')).toBeVisible()
    await expect(page.getByText('日柱')).toBeVisible()
    await expect(page.getByText('时柱')).toBeVisible()
    await expect(page.getByText('按节气差起运')).toBeVisible()
    await expect(page.getByText('计算口径')).toBeVisible()
    await expect(page.getByText(/不应用于医疗、法律或投资等重要决策/)).toBeVisible()
    await expect(page.getByText('服务器默认 · DeepSeek')).toBeVisible()
    await expect(page.getByText('当前不使用个人 Key')).toBeVisible()
  })

  test('窄屏下命盘仍可阅读', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const email = `bazi-mobile-${Date.now()}@example.com`
    const registerResponse = await page.request.post('/api/v1/auth/register', {
      data: {
        username: '窄屏验收用户',
        email,
        password: 'Pass1234',
        birth_year: 1990,
        birth_month: 5,
        birth_day: 15,
        birth_hour: 8,
        gender: 1,
      },
    })
    expect(registerResponse.status()).toBe(201)
    const { data } = await registerResponse.json()

    await page.addInitScript((token) => localStorage.setItem('token', token), data.token)
    await page.goto('/profile')

    await expect(page.getByText('命盘基础')).toBeVisible()
    const pillars = page.locator('.pillar-item')
    await expect(pillars).toHaveCount(4)
    const firstRow = await pillars.nth(0).boundingBox()
    const secondRow = await pillars.nth(2).boundingBox()
    expect(firstRow).not.toBeNull()
    expect(secondRow).not.toBeNull()
    expect(secondRow!.y).toBeGreaterThan(firstRow!.y)

    await expect(page.getByText('服务器默认 · DeepSeek')).toBeVisible()
    await expect(page.locator('.llm-source-banner')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  })
})
