import { expect, test, type Page } from '@playwright/test'

const response = (data: unknown) => ({ success: true, data, error: null, meta: null })

const weeklyForecast = [
  {
    date: '2026-09-18', weekday: '周五', heavenly_stem: '甲', earthly_branch: '子',
    overall_score: 3, overall_level: '平',
    focus: { key: 'career', label: '事业', score: 3, detail: '先完成最需要专注的核心事项。' }, caution: null,
  },
  {
    date: '2026-09-19', weekday: '周六', heavenly_stem: '乙', earthly_branch: '丑',
    overall_score: 4, overall_level: '偏吉',
    focus: { key: 'love', label: '关系', score: 4, detail: '适合主动沟通，确认彼此的安排。' },
    caution: { key: 'wealth', label: '财务', score: 2, detail: '避免冲动消费。' },
  },
  {
    date: '2026-09-20', weekday: '周日', heavenly_stem: '丙', earthly_branch: '寅',
    overall_score: 2, overall_level: '谨慎',
    focus: { key: 'health', label: '身心', score: 3, detail: '留出休整时间。' },
    caution: { key: 'career', label: '事业', score: 2, detail: '重要事项避免临时加码。' },
  },
  {
    date: '2026-09-21', weekday: '周一', heavenly_stem: '丁', earthly_branch: '卯',
    overall_score: 3, overall_level: '平',
    focus: { key: 'wealth', label: '财务', score: 3, detail: '按预算处理支出。' }, caution: null,
  },
  {
    date: '2026-09-22', weekday: '周二', heavenly_stem: '戊', earthly_branch: '辰',
    overall_score: 5, overall_level: '顺势',
    focus: { key: 'career', label: '事业', score: 5, detail: '适合推进需要决断的工作。' },
    caution: { key: 'health', label: '身心', score: 3, detail: '也要按时休息。' },
  },
  {
    date: '2026-09-23', weekday: '周三', heavenly_stem: '己', earthly_branch: '巳',
    overall_score: 4, overall_level: '偏吉',
    focus: { key: 'love', label: '关系', score: 4, detail: '适合把想法说清楚。' },
    caution: { key: 'wealth', label: '财务', score: 2, detail: '避免为情绪买单。' },
  },
  {
    date: '2026-09-24', weekday: '周四', heavenly_stem: '庚', earthly_branch: '午',
    overall_score: 3, overall_level: '平',
    focus: { key: 'health', label: '身心', score: 3, detail: '保持稳定作息。' }, caution: null,
  },
]

const todayFortune = {
  id: 1, date: '2026-09-18', overall_score: 3, overall_level: '平',
  career: { score: 3, detail: '先完成最需要专注的核心事项。' },
  wealth: { score: 3, detail: '按预算处理支出。' },
  love: { score: 3, detail: '和重要的人保持自然沟通。' },
  health: { score: 3, detail: '规律作息，留意休息。' },
  lucky_color: '蓝色', lucky_number: '3, 8', lucky_direction: '东方', hourly_fortunes: null,
  interpretation: '今天适合稳步推进既定事务。',
  user_rating: null, user_feedback_tags: [], user_feedback_text: null, accuracy_mark: null,
}

async function mockFortuneApi(page: Page) {
  await page.route('**/api/v1/fortunes**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith('/fortunes/week')) return route.fulfill({ json: response(weeklyForecast) })
    if (path.endsWith('/fortunes/today')) return route.fulfill({ json: response(todayFortune) })
    return route.fulfill({ json: { ...response([]), meta: { total: 0, page: 1, limit: 20, total_pages: 0 } } })
  })
}

test.describe('七日节奏预览', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('token', 'fortune-ui-test-token'))
    await mockFortuneApi(page)
  })

  test('展示七天、最佳日并可切换行动提示', async ({ page }) => {
    await page.goto('/fortune')

    await expect(page.getByRole('heading', { name: '七日节奏' })).toBeVisible()
    await expect(page.getByText('本周最佳 · 周二')).toBeVisible()
    const days = page.locator('.week-forecast-day')
    await expect(days).toHaveCount(7)

    await days.nth(1).click()
    await expect(page.getByText('优先安排 关系')).toBeVisible()
    await expect(page.getByText('避免冲动消费。')).toBeVisible()
  })

  test('窄屏只在预览条内横向滚动，页面本身不溢出', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/fortune')

    await expect(page.getByRole('heading', { name: '七日节奏' })).toBeVisible()
    await expect(page.locator('.week-forecast-days')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  })
})
