import { test, expect } from '@playwright/test'

test.describe('首页', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('显示页面标题', async ({ page }) => {
    await expect(page).toHaveTitle('命理运势系统')
  })

  test('显示Logo', async ({ page }) => {
    const logo = page.locator('.logo-text')
    await expect(logo).toContainText('命理运势')
  })

  test('显示导航菜单', async ({ page }) => {
    const menuItems = page.locator('.el-menu-item')
    await expect(menuItems).toHaveCount(3) // 首页、运势、占卜
  })

  test('显示注册按钮（未登录）', async ({ page }) => {
    // 使用 header 中的注册按钮
    const registerBtn = page.locator('header').getByRole('button', { name: '注册' })
    await expect(registerBtn).toBeVisible()
  })

  test('显示功能卡片', async ({ page }) => {
    await expect(page.getByText('每日运势')).toBeVisible()
    await expect(page.getByText('六爻占卜')).toBeVisible()
    await expect(page.getByText('奇门遁甲')).toBeVisible()
  })

  test('点击注册按钮跳转到注册页', async ({ page }) => {
    // 使用 header 中的注册按钮
    await page.locator('header').getByRole('button', { name: '注册' }).click()
    await expect(page).toHaveURL(/.*register/)
  })

  test('点击登录按钮跳转到登录页', async ({ page }) => {
    await page.locator('header').getByRole('button', { name: '登录' }).click()
    await expect(page).toHaveURL(/.*login/)
  })
})
