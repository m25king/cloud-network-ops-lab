import { test, expect } from '@playwright/test';
test('real API: filter, refresh URL, details, CSV download', async ({page}) => {
  await page.goto('/assets?size=2');
  await expect(page.getByRole('button',{name:'demo-core-1',exact:true})).toBeVisible();
  await page.getByPlaceholder('搜索资产名称').fill('branch');
  await expect(page).toHaveURL(/q=branch/);
  await expect(page.getByRole('button',{name:'demo-branch-1',exact:true})).toBeVisible();
  await page.reload();
  await expect(page.getByPlaceholder('搜索资产名称')).toHaveValue('branch');
  await page.getByRole('button',{name:'demo-branch-1',exact:true}).click();
  await expect(page.getByText('资产详情', {exact:true})).toBeVisible();
  await page.keyboard.press('Escape');
  const download = page.waitForEvent('download');
  await page.getByRole('button',{name:'导出当前页'}).click();
  expect((await download).suggestedFilename()).toBe('assets-current-page.csv');
  await page.getByPlaceholder('搜索资产名称').fill('does-not-exist');
  await expect(page.getByText('没有匹配的资产，试试调整筛选条件。')).toBeVisible();
});
test('historical report, invalid local import and failed samples', async ({page}) => {
  await page.goto('/inspections');
  await expect(page.getByRole('button',{name:'local-healthy',exact:true})).toBeVisible();
  await page.getByText('仅异常',{exact:true}).click();
  await expect(page.getByRole('button',{name:'local-healthy',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'local-dependency-down',exact:true}).click();
  await expect(page.getByText('逐次采样详情',{exact:true})).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByLabel('选择巡检 JSON 文件').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{}')});
  await expect(page.getByRole('alert')).toContainText('报告格式不正确');
});
test('503 then retry restores real database response', async ({page}) => {
  await page.route('**/api/assets?**', route => route.fulfill({status:503,body:'{}'}));
  await page.goto('/assets');
  await expect(page.getByRole('alert')).toContainText('后端服务暂不可用');
  await page.unroute('**/api/assets?**');
  await page.getByRole('button',{name:'重试',exact:true}).click();
  await expect(page.getByRole('button',{name:'demo-core-1',exact:true})).toBeVisible();
});
test('desktop overview and mobile navigation fit viewport', async ({page}) => {
  await page.setViewportSize({width:1440,height:1000}); await page.goto('/');
  await expect(page.getByText('查询正常',{exact:true})).toBeVisible();
  await page.screenshot({path:'test-results/overview-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/overview-mobile.png',fullPage:true});
  await page.getByRole('link',{name:'故障记录',exact:true}).click();
  await expect(page.getByText('当前后端未加载演练记录',{exact:true})).toBeVisible();
});
