import { expect, test } from '@playwright/test'

const ORIGINAL_CLIENT_TIMEOUT_MS = 10_000
const SLOW_INTERPRETATION_DELAY_MS = ORIGINAL_CLIENT_TIMEOUT_MS + 1_000

async function prepareDivinationPage(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'e2e-test-token')
  })

  await page.route('**/api/v1/divination/records**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: [],
        error: null,
        meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
      }),
    })
  })

  await page.route('**/api/v1/probability-events/today', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { date: '2026-08-02', events: [] }, error: null, meta: null }),
    })
  })

  await page.goto('/divination')
  await expect(page.getByRole('heading', { name: '占卜中心' })).toBeVisible()
}

for (const scenario of [
  { type: 'liuyao', button: /起卦/, endpoint: '**/api/v1/divination/liuyao', text: '六爻慢响应解读' },
  { type: 'qimen', button: /起盘/, endpoint: '**/api/v1/divination/qimen', text: '奇门慢响应解读' },
] as const) {
  test(`${scenario.type} 等待超过默认超时时间后仍显示解读`, async ({ page }) => {
    test.setTimeout(30_000)
    const browserErrors: string[] = []
    page.on('console', (message) => {
      if (message.type() === 'error') browserErrors.push(message.text())
    })
    page.on('pageerror', (error) => browserErrors.push(error.message))

    await page.route(scenario.endpoint, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, SLOW_INTERPRETATION_DELAY_MS))
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { id: 1, question: '测试问题', interpretation: scenario.text },
          error: null,
          meta: null,
        }),
      })
    })

    await prepareDivinationPage(page)

    if (scenario.type === 'qimen') {
      await page.locator('.method-selector').getByText('奇门遁甲').click()
    }
    await page.getByRole('button', { name: scenario.button }).click()

    await expect(page.getByText(scenario.text)).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('网络错误，请稍后重试')).toHaveCount(0)
    expect(browserErrors).toEqual([])
  })
}
