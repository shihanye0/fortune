import { test, expect } from '@playwright/test'

test('ziwei page renders chart for logged-in user', async ({ page }) => {
  const username = `zw${Date.now()}`
  const password = 'Zw123456!'
  const reg = await page.request.post('/api/v1/auth/register', {
    data: { username, password, email: `${username}@t.com`, birth_year: 1990, birth_month: 8, birth_day: 15, birth_hour: 7, gender: 0 },
  })
  expect(reg.ok()).toBeTruthy()
  const body = await reg.json()
  const token = body.data.token
  await page.addInitScript((t) => localStorage.setItem('token', t), token)
  await page.goto('/ziwei')
  await expect(page.getByText('命盘十二宫')).toBeVisible()
  await expect(page.getByText('土五局').first()).toBeVisible()
  // 十二宫格：12 个宫位格 + 中央面板
  const cells = page.locator('.palace-cell')
  await expect(cells).toHaveCount(12)
  const center = page.locator('.center-panel')
  await expect(center).toContainText('五行局')
})
