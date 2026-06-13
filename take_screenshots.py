import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        
        file_url = f"file:///{os.path.abspath('templates/quiz_shorts_template.html').replace(chr(92), '/')}"
        
        for i in range(1, 4):
            await page.goto(file_url)
            await page.wait_for_timeout(1000)
            
            # Show the reveal state to display everything (Border, Option, Subscribe Box, Timer)
            await page.evaluate("setQuizState('reveal')")
            await page.wait_for_timeout(500)
            
            output_path = os.path.abspath(f"screenshot_theme_{i}.png")
            await page.screenshot(path=output_path)
            print(f"Saved {output_path}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
