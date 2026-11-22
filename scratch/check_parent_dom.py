import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://127.0.0.1:3000/hop', wait_until='domcontentloaded')
        
        info = await page.evaluate('''() => {
            const el = document.getElementById('tab-gtc-tong');
            const parent = el.parentElement;
            return {
                parentTagName: parent.tagName,
                parentId: parent.id,
                parentClass: parent.className,
                parentOuterHead: parent.outerHTML.substring(0, 200)
            };
        }''')
        print(info)
        await browser.close()

asyncio.run(main())

