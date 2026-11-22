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
        
        # Click Tab 9: Rớt Luân Chuyển
        await page.click('.tab-item[data-tab="tab-rot-lc"]')
        await page.wait_for_timeout(2000)
        
        # Check chart labels
        chart_labels = await page.evaluate('''() => {
            const chart = Chart.getChart('chart-rot-lc-bar');
            return chart ? chart.data.labels : null;
        }''')
        
        # Check Table 1 (AMs)
        am_table_rows = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('#table-rot-am-detailed tbody tr')).map(r => {
                const tds = r.querySelectorAll('td');
                return {
                    rank: tds[0]?.innerText.trim(),
                    am: tds[1]?.innerText.trim(),
                    vol: tds[2]?.innerText.trim(),
                    rot: tds[3]?.innerText.trim(),
                    rate_w45: tds[6]?.innerText.trim()
                };
            });
        }''')
        
        # Check Table 2 (Provinces)
        tinh_table_rows = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('#table-rot-tinh-detailed tbody tr')).map(r => {
                const tds = r.querySelectorAll('td');
                return {
                    rank: tds[0]?.innerText.trim(),
                    tinh: tds[1]?.innerText.trim(),
                    vol: tds[2]?.innerText.trim(),
                    rot: tds[3]?.innerText.trim(),
                    rate_w45: tds[6]?.innerText.trim()
                };
            });
        }''')
        
        print(f"Chart labels count: {len(chart_labels) if chart_labels else 0}")
        print("Chart labels:", chart_labels)
        print(f"\nAM table rows count: {len(am_table_rows)}")
        for r in am_table_rows:
            print(f"  {r['rank']} | {r['am']} | Vol: {r['vol']} | Rớt: {r['rot']} | %W45: {r['rate_w45']}")
            
        print(f"\nTinh table rows count: {len(tinh_table_rows)}")
        for r in tinh_table_rows:
            print(f"  {r['rank']} | {r['tinh']} | Vol: {r['vol']} | Rớt: {r['rot']} | %W45: {r['rate_w45']}")
            
        print(f"\nErrors: {len(errors)}")
        
        # Take screenshot of chart and province table
        out_chart = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_rot_chart_20am.png'
        chart_el = page.locator('#chart-rot-lc-bar').locator('xpath=./ancestor::div[contains(@class, "report-card")]').first
        await chart_el.screenshot(path=out_chart)
        print("Chart screenshot saved to:", out_chart)
        
        out_tinh = r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_rot_tinh_5tinh.png'
        tinh_el = page.locator('#table-rot-tinh-detailed').locator('xpath=./ancestor::div[contains(@class, "report-card")]').first
        await tinh_el.screenshot(path=out_tinh)
        print("Tinh table screenshot saved to:", out_tinh)
        
        await browser.close()

asyncio.run(main())

