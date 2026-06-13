import asyncio
import os
import time
import subprocess
from playwright.async_api import async_playwright

def get_audio_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 2.0

async def render_video():
    subject_hi = 'भारतीय राजव्यवस्था'
    chapter_hi = 'अध्याय 1: संविधान का निर्माण'
    topic_hi = 'संविधान सभा'
    question_hi = 'संविधान सभा की प्रथम बैठक कब हुई थी?'
    opt0_hi = '9 दिसंबर 1946'
    opt1_hi = '11 दिसंबर 1946'
    opt2_hi = '15 अगस्त 1947'
    opt3_hi = '26 जनवरी 1950'
    correct_idx = '0'
    exp0 = '9 दिसंबर 1946 को संविधान सभा की पहली बैठक दिल्ली के ऐतिहासिक संसद भवन में हुई थी। इसमें डॉ. सच्चिदानंद सिन्हा को अस्थायी अध्यक्ष चुना गया था।'
    exp1 = '11 दिसंबर 1946 को संविधान सभा की दूसरी बैठक हुई, जिसमें डॉ. राजेंद्र प्रसाद को स्थायी अध्यक्ष और एच.सी. मुखर्जी को उपाध्यक्ष चुना गया था।'
    exp2 = '15 अगस्त 1947 भारत की आज़ादी का ऐतिहासिक दिन है। हालाँकि यह भारत के इतिहास का सबसे महत्वपूर्ण दिन है, यह संविधान सभा की बैठक से नहीं जुड़ा है।'
    exp3 = '26 जनवरी 1950 को भारत का संविधान पूर्ण रूप से लागू हुआ और भारत एक गणतंत्र देश बना। संविधान को बनने में 2 साल, 11 महीने और 18 दिन लगे थे।'

    # Generate TTS
    q_text = f"प्रश्न... {question_hi}... दिए गए विकल्पों में से सही उत्तर कमेंट में बताइये।"
    ans_text = f"सही उत्तर है विकल्प ए, {opt0_hi}। {exp0}"
    
    print("Generating TTS...")
    subprocess.run(["edge-tts", "--voice", "hi-IN-SwaraNeural", "--text", q_text, "--write-media", "outputs/voice_q.mp3"])
    subprocess.run(["edge-tts", "--voice", "hi-IN-SwaraNeural", "--text", ans_text, "--write-media", "outputs/voice_ans.mp3"])
    
    q_dur = get_audio_duration("outputs/voice_q.mp3")
    ans_dur = get_audio_duration("outputs/voice_ans.mp3")
    print(f"TTS Durations: Question={q_dur}s, Answer={ans_dur}s")

    # Compile template with dummy data
    with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    html = html.replace('{{subject_hi}}', subject_hi)
    html = html.replace('{{chapter_hi}}', chapter_hi)
    html = html.replace('{{topic_hi}}', topic_hi)
    html = html.replace('{{question_hi}}', question_hi)
    html = html.replace('{{opt0_hi}}', opt0_hi)
    html = html.replace('{{opt1_hi}}', opt1_hi)
    html = html.replace('{{opt2_hi}}', opt2_hi)
    html = html.replace('{{opt3_hi}}', opt3_hi)
    html = html.replace('{{correct_idx}}', correct_idx)
    html = html.replace('{{exp0}}', exp0)
    html = html.replace('{{exp1}}', exp1)
    html = html.replace('{{exp2}}', exp2)
    html = html.replace('{{exp3}}', exp3)

    with open('outputs/temp_test.html', 'w', encoding='utf-8') as f:
        f.write(html)

    q_start_time = 0
    ans_start_time = 0

    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        # 2160x3840 is 9:16
        context = await b.new_context(
            viewport={'width': 2160, 'height': 3840},
            record_video_dir="outputs/",
            record_video_size={'width': 1080, 'height': 1920}  # Scale down to 1080p for performance
        )
        page = await context.new_page()
        
        # Open compiled template
        path = os.path.abspath('outputs/temp_test.html')
        
        start_time = time.time()
        
        await page.goto(f'file:///{path}'.replace('\\\\', '/'), wait_until='networkidle')
        
        # Initialize theme FIRST
        await page.evaluate("window.randomizeTheme();")
        await page.evaluate("window.setQuizState('question', 0, null);")
        
        # Small wait for rendering to settle
        await page.wait_for_timeout(200)
        
        # NOW show everything
        await page.evaluate("document.body.style.opacity = '1';")
        
        q_start_time = time.time() - start_time
        q_wait_ms = int(q_dur * 1000) + 500
        await page.wait_for_timeout(q_wait_ms)
        
        # Simulate countdown
        print("State: Countdown...")
        for step in range(50):
            await page.evaluate(f"window.setQuizState('countdown', {step/50.0}, null)")
            await page.wait_for_timeout(100)
             
        print("State: Reveal...")
        await page.evaluate("window.setQuizState('reveal', 1, null)")
        await page.wait_for_timeout(2000)
        
        print("State: Explanation...")
        await page.evaluate("window.setQuizState('explain3', 1, 0)")
        
        ans_start_time = time.time() - start_time
        ans_wait_ms = int(ans_dur * 1000) + 1000
        await page.wait_for_timeout(ans_wait_ms)
        
        await context.close()
        await b.close()
        print("Done rendering video!")

    # Merge audio and video
    print("Merging video and audio...")
    webm_files = [f for f in os.listdir('outputs') if f.endswith('.webm')]
    if not webm_files:
        print("No webm found!")
        return
    
    # Sort by creation time to get the latest
    webm_files.sort(key=lambda x: os.path.getmtime(os.path.join('outputs', x)))
    webm_path = os.path.join('outputs', webm_files[-1])
    
    q_delay_ms = int(q_start_time * 1000)
    ans_delay_ms = int(ans_start_time * 1000)
    
    out_path = os.path.abspath("C:/Users/1001s/Desktop/final_quiz_video.mp4")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", webm_path,
        "-i", "outputs/voice_q.mp3",
        "-i", "outputs/voice_ans.mp3",
        "-filter_complex",
        f"[1:a]adelay={q_delay_ms}|{q_delay_ms}[a1];"
        f"[2:a]adelay={ans_delay_ms}|{ans_delay_ms}[a2];"
        f"[a1][a2]amix=inputs=2:duration=longest[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast",
        "-ss", "0.3",
        out_path
    ]
    
    subprocess.run(ffmpeg_cmd)
    print(f"Final video saved to {out_path}")

asyncio.run(render_video())
