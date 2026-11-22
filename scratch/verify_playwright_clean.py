import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}") if msg.type in ['error', 'warn'] else None)
        
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        # Switch to Tab 3
        await page.click('.tab-item[data-tab="tab-gtc-tong"]')
        await page.wait_for_timeout(2000)
        await page.screenshot(path=r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_tab3_clean.png', full_page=False)
        
        # Check elements in DOM
        check = await page.evaluate('''() => {
            return {
                hasOldTable: !!document.getElementById('table-bc-canh-bao'),
                hasOldOverviewTable: !!document.getElementById('table-bc-canh-bao-overview'),
                tab3CardTitles: Array.from(document.querySelectorAll('#tab-gtc-tong .report-card-title')).map(el => el.innerText.trim())
            };
        }''')
        print("DOM Check:", check)
        print("Errors encountered:", len(errors))
        if errors:
            print("Errors:", errors)
            
        await browser.close()

asyncio.run(main())
