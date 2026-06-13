from jinja2 import Template
import asyncio
from playwright.async_api import async_playwright

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    t = f.read()

rendered = Template(t).render(
    subject_hi='भारतीय राजव्यवस्था',
    chapter_hi='अध्याय 1: संविधान का निर्माण',
    topic_hi='संविधान सभा',
    subject='INDIAN POLITY', chapter='CH 1', topic='CONSTITUENT ASSEMBLY',
    question_hi='भारत का संविधान कब लागू हुआ?',
    question_en='When did Constitution of India come into force?',
    opt0_hi='26 जनवरी 1950', opt0_en='26 January 1950',
    opt1_hi='15 अगस्त 1947', opt1_en='15 August 1947',
    opt2_hi='26 नवंबर 1949', opt2_en='26 November 1949',
    opt3_hi='30 जनवरी 1948', opt3_en='30 January 1948',
    exp0='सही! 26 जनवरी 1950 को संविधान लागू हुआ।',
    exp1='15 अगस्त 1947 को स्वतंत्रता मिली।',
    exp2='26 नवंबर 1949 को संविधान अपनाया गया।',
    exp3='यह गलत तारीख है।',
    correct_idx=0
)

with open('templates/quiz_preview.html', 'w', encoding='utf-8') as f:
    f.write(rendered)

async def ss():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        for i in range(3):
            page = await b.new_page(viewport={'width':2160,'height':3840})
            await page.goto('file:///C:/Users/1001s/teacher-bot-temp/templates/quiz_preview.html', wait_until='networkidle')
            await page.evaluate("window.setQuizState('reveal', 1, null)")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=rf'C:\Users\1001s\teacher-bot-temp\outputs\viral_preview_random_{i}.png')
        await b.close()
    print('Done generating 3 random previews!')

asyncio.run(ss())
