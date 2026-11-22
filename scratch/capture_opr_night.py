import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        await page.click('.tab-item[data-tab="tab-opr-tts"]')
        await page.wait_for_timeout(2000)
        
        out_path = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_opr_night_fixed.png'
        await page.locator('#table-opr-night-detailed').screenshot(path=out_path)
        print("Screenshot saved to:", out_path)
        
        await browser.close()

asyncio.run(main())

