import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        # Click tab 3
        await page.click('.tab-item[data-tab="tab-gtc-tong"]')
        await page.wait_for_timeout(2000)
        
        out_path = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_tab3_restored.png'
        await page.screenshot(path=out_path, full_page=False)
        print("Tab 3 screenshot captured successfully!")
        
        await browser.close()

asyncio.run(main())

