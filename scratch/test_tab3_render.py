import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}"))
        
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        # Check overview visibility
        overview_visible = await page.is_visible('#tab-overview')
        print("Overview visible on load:", overview_visible)
        
        # Click tab 3
        await page.click('.tab-item[data-tab="tab-gtc-tong"]')
        await page.wait_for_timeout(2000)
        
        tab3_visible = await page.is_visible('#tab-gtc-tong')
        print("Tab 3 visible after click:", tab3_visible)
        
        # Get bounding box and display style of tab-gtc-tong
        style_info = await page.evaluate('''() => {
            const el = document.getElementById('tab-gtc-tong');
            if (!el) return 'el not found';
            const cs = window.getComputedStyle(el);
            return {
                className: el.className,
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                height: el.offsetHeight,
                childrenCount: el.children.length,
                firstElementChild: el.firstElementChild ? el.firstElementChild.className : null
            };
        }''')
        print("Tab 3 style info:", style_info)
        
        # Capture screenshot of full page
        await page.screenshot(path=r'C:\Users\lap4all\.gemini\antigravity\brain\625531f0-1d8b-4045-9660-66234e684dbd\screenshot_tab3_full.png', full_page=True)
        print("Page errors:", errors)
        await browser.close()

asyncio.run(main())

