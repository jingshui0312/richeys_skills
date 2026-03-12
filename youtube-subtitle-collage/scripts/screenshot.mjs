#!/usr/bin/env node
/**
 * Full-page screenshot utility using Playwright
 * Usage: node screenshot.mjs <html_file_path> <output_png_path> [width]
 */

import { chromium } from 'playwright';
import path from 'path';

const htmlFile = process.argv[2];
const outputFile = process.argv[3];
const width = parseInt(process.argv[4] || '900', 10);

if (!htmlFile || !outputFile) {
  console.error('Usage: node screenshot.mjs <html_file> <output_png> [width]');
  process.exit(1);
}

const htmlPath = path.resolve(htmlFile);
const outputPath = path.resolve(outputFile);

async function capture() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewportSize({ width: width, height: 800 });

  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });

  // Wait for fonts to load
  await page.waitForTimeout(2000);

  // Get actual content height
  const bodyHeight = await page.evaluate(() => {
    return document.documentElement.scrollHeight;
  });

  // Resize viewport to full height
  await page.setViewportSize({ width: width, height: bodyHeight });
  await page.waitForTimeout(500);

  await page.screenshot({
    path: outputPath,
    fullPage: true,
    type: 'png'
  });

  console.log(`Screenshot saved: ${outputPath} (${width}x${bodyHeight})`);

  await browser.close();
}

capture().catch(err => {
  console.error('Screenshot error:', err.message);
  process.exit(1);
});
