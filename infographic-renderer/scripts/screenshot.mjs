#!/usr/bin/env node
/**
 * Full-page screenshot utility using Playwright
 * Usage: node screenshot.mjs <html_file_path> <output_png_path> [width]
 */

import { chromium } from 'playwright';
import path from 'path';

const htmlFile = process.argv[2];
const outputFile = process.argv[3];
const width = parseInt(process.argv[4] || '780', 10);

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

  // Get actual content bounding box (precise, no extra whitespace)
  const contentBox = await page.evaluate(() => {
    const body = document.body;
    const html = document.documentElement;
    // Use getBoundingClientRect on body for precise content bounds
    const rect = body.getBoundingClientRect();
    const lastChild = body.lastElementChild;
    let bottom = 0;
    if (lastChild) {
      const lastRect = lastChild.getBoundingClientRect();
      bottom = lastRect.bottom;
    }
    return {
      height: Math.max(rect.bottom, bottom, html.scrollHeight),
      // fallback to scrollHeight if rect is zero
    };
  });

  // Add small padding (20px) at bottom
  const cropHeight = Math.ceil(contentBox.height) + 20;

  // Resize viewport to content height
  await page.setViewportSize({ width: width, height: cropHeight });
  await page.waitForTimeout(500);

  // Clip screenshot to exact content area
  await page.screenshot({
    path: outputPath,
    clip: { x: 0, y: 0, width: width, height: cropHeight },
    type: 'png'
  });

  console.log(`Screenshot saved: ${outputPath} (${width}x${cropHeight})`);

  await browser.close();
}

capture().catch(err => {
  console.error('Screenshot error:', err.message);
  process.exit(1);
});
