import { test, expect } from '@playwright/test'

test.describe('导航功能', () => {
  test('未登录时导航栏显示登录注册', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('header').getByRole('button', { name: '登录' })).toBeVisible()
    await expect(page.locator('header').getByRole('button', { name: '注册' })).toBeVisible()
  })

  test('未登录时点击运势跳转登录页', async ({ page }) => {
    await page.goto('/')
    // 点击运势菜单
    await page.locator('.el-menu-item').filter({ hasText: '运势' }).click()
    // 应该跳转到登录页（因为需要认证）
    await expect(page).toHaveURL(/.*login/)
  })

  test('未登录时点击占卜跳转登录页', async ({ page }) => {
    await page.goto('/')
    await page.locator('.el-menu-item').filter({ hasText: '占卜' }).click()
    await expect(page).toHaveURL(/.*login/)
  })

  test('点击首页菜单跳转首页', async ({ page }) => {
    await page.goto('/login')
    await page.locator('.el-menu-item').filter({ hasText: '首页' }).click()
    await expect(page).toHaveURL('/')
  })
})
