import { expect, test } from '@playwright/test'

const response = (data: unknown) => ({ success: true, data, error: null, meta: null })

test('占卜历史标签使用有效的 Element Plus 类型', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('token', 'divination-ui-test-token'))
  await page.route('**/api/v1/divination/records**', (route) => route.fulfill({
    json: {
      ...response([
        {
          id: 1,
          type: 'liuyao',
          question: '今日运势如何？',
          summary: '今日运势如何？',
          user_rating: null,
          user_feedback_text: null,
          accuracy_mark: null,
          outcome_verified: false,
          created_at: '2026-09-18T10:00:00',
        },
      ]),
      meta: { total: 1, page: 1, limit: 20, total_pages: 1 },
    },
  }))
  await page.route('**/api/v1/probability-events/today', (route) => route.fulfill({
    json: response({ date: '2026-09-18', events: [] }),
  }))

  await page.goto('/divination')

  await expect(page.getByRole('heading', { name: '占卜历史' })).toBeVisible()
  const typeTag = page.locator('.history-type .el-tag')
  await expect(typeTag).toHaveText('六爻')
  await expect(typeTag).toHaveClass(/el-tag--primary/)
})
