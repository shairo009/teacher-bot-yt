import asyncio
from playwright.async_api import async_playwright

async def ss():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        for i in range(5):
            page = await b.new_page(viewport={'width':2160,'height':3840})
            await page.goto('file:///C:/Users/1001s/teacher-bot-temp/templates/quiz_shorts_template.html', wait_until='networkidle')
            await page.evaluate(f"window.borderDesignType = {i}; window.setQuizState('reveal', 1, null)")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=rf'C:\Users\1001s\teacher-bot-temp\outputs\viral_preview_border_{i}.png')
        await b.close()
    print('Done generating 5 border previews!')

asyncio.run(ss())
