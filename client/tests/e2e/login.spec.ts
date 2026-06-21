import { test, expect } from '@playwright/test'

test.describe('登录页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('显示登录表单', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '登录' })).toBeVisible()
    await expect(page.locator('input')).toHaveCount(2) // 邮箱、密码
  })

  test('显示注册链接', async ({ page }) => {
    await expect(page.getByText('立即注册')).toBeVisible()
  })

  test('空表单提交显示警告', async ({ page }) => {
    await page.getByRole('main').getByRole('button', { name: '登录' }).click()
    // 应该显示提示信息
    await expect(page.locator('.el-message')).toBeVisible()
  })

  test('点击注册链接跳转', async ({ page }) => {
    await page.getByText('立即注册').click()
    await expect(page).toHaveURL(/.*register/)
  })
})
