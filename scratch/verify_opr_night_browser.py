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
        await page.wait_for_timeout(2000)
        
        # Click tab 8 (%OPR TikTok Shop)
        await page.click('.tab-item[data-tab="tab-opr-tts"]')
        await page.wait_for_timeout(2000)
        
        # Check day table headers
        day_headers = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('#table-opr-day-detailed thead th')).map(th => th.innerText.trim());
        }''')
        
        # Check night table headers
        night_headers = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('#table-opr-night-detailed thead th')).map(th => th.innerText.trim());
        }''')
        
        # Check first 3 rows of night table
        night_rows = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('#table-opr-night-detailed tbody tr')).slice(0, 5).map(tr => {
                return Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
            });
        }''')
        
        # Check row 15 (Trần Thị Nhung)
        row_nhung = await page.evaluate('''() => {
            const tr = Array.from(document.querySelectorAll('#table-opr-night-detailed tbody tr')).find(r => r.innerText.includes('Trần Thị Nhung'));
            return tr ? Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim()) : null;
        }''')
        
        print("Day headers:", day_headers)
        print("Night headers:", night_headers)
        print("Night rows (first 5):", night_rows)
        print("Row Trần Thị Nhung:", row_nhung)
        print("Errors encountered:", len(errors))
        
        # Take screenshot of the table
        night_card = page.locator('#table-opr-night-detailed').locator('xpath=./ancestor::div[contains(@class, "report-card")]')
        out_path = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_opr_night_fixed.png'
        await night_card.screenshot(path=out_path)
        print("Screenshot saved to:", out_path)
        
        await browser.close()

asyncio.run(main())

