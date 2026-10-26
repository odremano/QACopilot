import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

// Carpeta de salida (reporte JSON y evidencias). En el contenedor vive en el volumen de evidencias.
const salida = process.env.PW_SALIDA_DIR ?? '/data/evidencias/smoke';

export default defineConfig({
  testDir: '.',
  // Uso responsable del SUT (RNF-09): un navegador, sin paralelismo ni reintentos.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  outputDir: path.join(salida, 'artefactos'),
  reporter: [['list'], ['json', { outputFile: path.join(salida, 'reporte.json') }]],
  use: {
    baseURL: process.env.SUT_BASE_URL ?? 'https://www.saucedemo.com',
    headless: true,
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
