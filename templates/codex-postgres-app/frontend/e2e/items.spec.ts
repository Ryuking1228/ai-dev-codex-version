import { test, expect } from '@playwright/test';

test('追加した項目は再読込しても残り、削除できる', async ({ page, request }) => {
  const title = 'e2e-' + crypto.randomUUID();
  await page.goto('/');
  await page.getByLabel('新しい項目').fill(title);
  await page.getByRole('button', { name: '追加', exact: true }).click();
  try {
    await expect(page.getByText(title, { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText(title, { exact: true })).toBeVisible();
    await page.getByRole('button', { name: `${title}を削除` }).click();
    await expect(page.getByText(title, { exact: true })).toHaveCount(0);
  } finally {
    const response = await request.get('/api/items');
    if (response.ok()) for (const item of await response.json()) {
      if (item.title === title) await request.delete(`/api/items/${item.id}`);
    }
  }
});

test('モバイル画面で横にはみ出さない', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
