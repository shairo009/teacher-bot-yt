import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_ROOT = Path("C:/Users/1001s/teacher-bot-temp")

async def main():
    html_path = PROJECT_ROOT / "templates/quiz_shorts.html"
    file_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        
        await page.goto(file_url)
        await page.wait_for_timeout(1000)
        
        # Phase 1: Question
        await page.evaluate("window.setQuizState('question', 0.0)")
        await page.screenshot(path=str(PROJECT_ROOT / "outputs/test_question.png"))
        
        # Phase 2: Countdown (50%)
        await page.evaluate("window.setQuizState('countdown', 0.5)")
        await page.screenshot(path=str(PROJECT_ROOT / "outputs/test_countdown.png"))
        
        # Phase 3: Reveal
        await page.evaluate("window.setQuizState('reveal', 1.0)")
        await page.screenshot(path=str(PROJECT_ROOT / "outputs/test_reveal.png"))
        
        # Phase 4: Explain (Option B active, progress 0.5)
        await page.evaluate("window.setQuizState('explain1', 0.5)")
        await page.screenshot(path=str(PROJECT_ROOT / "outputs/test_explain.png"))
        
        await browser.close()
    print("Test renders saved in outputs/ directory!")

if __name__ == "__main__":
    asyncio.run(main())
