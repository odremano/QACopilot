import { test, expect } from '@playwright/test';

// Spike R-06: demuestra que Chromium headless corre dentro del contenedor, sin red ni SUT.
test('Chromium headless renderiza contenido en el contenedor', async ({ page }) => {
  await page.setContent('<h1 data-test="titulo">QA Copilot</h1>');
  await expect(page.locator('[data-test="titulo"]')).toHaveText('QA Copilot');
});
