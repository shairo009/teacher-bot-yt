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
        
        body_box = await page.locator("body").bounding_box()
        page_quiz_box = await page.locator("#page-quiz").bounding_box()
        q_card_box = await page.locator("#question-card").bounding_box()
        options_header = page.locator("h4:has-text('OPTIONS')")
        opt_header_box = await options_header.bounding_box()
        options_container_box = await page.locator("#options-container").bounding_box()
        
        # Option cards
        opt0_box = await page.locator("#opt-0").bounding_box()
        opt3_box = await page.locator("#opt-3").bounding_box()
        
        print("--- PHASE: question (progress=0.0) ---")
        print(f"Body: {body_box}")
        print(f"Page Quiz: {page_quiz_box}")
        print(f"Question Card: {q_card_box}")
        print(f"OPTIONS Header: {opt_header_box}")
        print(f"Options Container: {options_container_box}")
        print(f"Option A: {opt0_box}")
        print(f"Option D: {opt3_box}")
        
        # Test scaled state
        # Set progress during transition when qScale is maximum (factor = 1.0)
        # Let's see: timings has start_question, end_question.
        # Wait, the script has a timings object. Let's pass a dummy timings to test zoom.
        timings = {
            "start_question": 1.0, "end_question": 4.0,
            "start_opt0": 5.0, "end_opt0": 6.0,
            "start_opt1": 6.0, "end_opt1": 7.0,
            "start_opt2": 7.0, "end_opt2": 8.0,
            "start_opt3": 8.0, "end_opt3": 9.0
        }
        
        await page.evaluate(f"window.setQuizState('question', 2.0, {timings})")
        q_card_zoomed_box = await page.locator("#question-card").bounding_box()
        opt_header_zoomed_box = await options_header.bounding_box()
        
        print("\n--- PHASE: question (zoomed qScale = 1.08) ---")
        print(f"Question Card Zoomed: {q_card_zoomed_box}")
        print(f"OPTIONS Header Zoomed: {opt_header_zoomed_box}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
