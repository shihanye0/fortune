import { test, expect } from '@playwright/test'

test.describe('注册页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register')
  })

  test('显示注册表单', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '注册' })).toBeVisible()
    await expect(page.getByText('用户名')).toBeVisible()
    await expect(page.getByText('邮箱')).toBeVisible()
    await expect(page.getByText('密码', { exact: true })).toBeVisible()
    await expect(page.getByText('确认密码')).toBeVisible()
  })

  test('显示生辰信息区域', async ({ page }) => {
    await expect(page.getByText('生辰信息')).toBeVisible()
    await expect(page.getByText('出生日期')).toBeVisible()
    await expect(page.getByText('出生时辰')).toBeVisible()
  })

  test('显示登录链接', async ({ page }) => {
    await expect(page.getByText('立即登录')).toBeVisible()
  })

  test('点击登录链接跳转', async ({ page }) => {
    await page.getByText('立即登录').click()
    await expect(page).toHaveURL(/.*login/)
  })
})
