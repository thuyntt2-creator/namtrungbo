import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        await page.wait_for_timeout(1000)
        
        # Click tab 3
        await page.click('.tab-item[data-tab="tab-gtc-tong"]')
        await page.wait_for_timeout(1000)
        
        matched_rules = await page.evaluate('''() => {
            const el = document.getElementById('tab-gtc-tong');
            const rules = [];
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.selectorText && el.matches(rule.selectorText)) {
                            rules.push({ selector: rule.selectorText, css: rule.cssText });
                        }
                    }
                } catch(e) {}
            }
            return {
                inlineStyle: el.getAttribute('style'),
                rules: rules,
                parentDisplay: window.getComputedStyle(el.parentElement).display,
                parentHeight: el.parentElement.offsetHeight,
                elOffsetTop: el.offsetTop,
                elOffsetHeight: el.offsetHeight,
                firstCard: el.querySelector('.report-card') ? {
                    display: window.getComputedStyle(el.querySelector('.report-card')).display,
                    height: el.querySelector('.report-card').offsetHeight,
                    opacity: window.getComputedStyle(el.querySelector('.report-card')).opacity
                } : null
            };
        }''')
        print("Matched rules:", matched_rules)
        await browser.close()

asyncio.run(main())

