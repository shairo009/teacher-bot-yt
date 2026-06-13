import re
import os

# 1. Recover original template
try:
    with open('templates_quiz_shorts_template_copy.html', 'r', encoding='utf-16') as f:
        content = f.read()
except Exception:
    with open('templates_quiz_shorts_template_copy.html', 'r', encoding='utf-8') as f:
        content = f.read()

# Apply random_timers.py
content = content.replace('const tStyles = ["classic", "diamond", "thick", "dotted"];', 'const tStyles = ["diamond", "thick", "dotted"];')
old_shifting_border = '`<div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:16px solid ${mainColor}; filter: hue-rotate(0deg); animation: rotateHue 8s linear infinite; box-shadow: inset 0 0 50px ${mainColor}, 0 0 50px ${mainColor};"></div>`'
new_double_pulse = '`<div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:16px solid ${mainColor}; color:${mainColor}; animation: pulseGlow 4s ease-in-out infinite; box-shadow: inset 0 0 50px ${mainColor}, 0 0 50px ${mainColor};"></div>`'
content = content.replace(old_shifting_border, new_double_pulse)

# Apply final_user_requests.py (don't fade other options)
content = content.replace('card.style.opacity = "0";', 'card.style.opacity = "1"; /* User requested not to hide */')

# 2. Fix subscribe button
old_btn = r'''    <!-- SUBSCRIBE BUTTON -->
    <div style="display:flex;justify-content:center;margin-top:auto;">
      <div class="subscribe-btn">
        <span style="font-size:60px;font-weight:900;color:white;letter-spacing:4px;">SUBSCRIBE</span>
        <span style="font-size:70px;">🔔</span>
      </div>
    </div>'''
new_btn = '''    <!-- SUBSCRIBE BUTTON -->
    <div style="display:flex;justify-content:center;margin-top:auto;margin-bottom:100px;position:relative;z-index:1000;">
      <div class="subscribe-btn">
        <span style="font-size:60px;font-weight:900;color:white;letter-spacing:4px;">SUBSCRIBE</span>
        <span style="font-size:70px;">👍</span>
      </div>
    </div>'''
content = content.replace(old_btn, new_btn)

# 3. Fix Explain Page (Full Screen, BIG FONTS)
# Hide top row
content = content.replace(
    '''<!-- TOP ROW -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:50px;">''',
    '''<!-- TOP ROW (HIDDEN PER USER REQUEST) -->
    <div style="display:none;align-items:flex-start;justify-content:space-between;margin-bottom:50px;">'''
)
# Hide question
content = content.replace(
    '''<!-- Repeated question -->
    <div style="height:650px; display:flex; align-items:center; justify-content:center; text-align:center; margin-bottom:100px;">''',
    '''<!-- Repeated question (HIDDEN PER USER REQUEST) -->
    <div style="display:none; height:650px; align-items:center; justify-content:center; text-align:center; margin-bottom:100px;">'''
)

# Extract Explanation Cards container safely!
# We will just replace everything between <!-- Explanation Cards --> and </div>\n    </div>\n  </div>\n\n  <script>
exp_cards_pattern = r'<!-- Explanation Cards -->(.*?)</div>\s*</div>\s*</div>\s*<script>'
new_cards = '''<!-- Explanation Cards -->
    <div style="display:flex;flex-direction:column;gap:30px;width:100%;height:100%;justify-content:center;padding:40px 0;">
      <div id="exp-card-0" class="option-card" style="padding:30px 50px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-0" style="font-weight:900;color:white;font-size:80px;">A. {{opt0_hi}}</span>
        <p style="font-size:70px;font-weight:600;color:#bbb;line-height:1.4;margin:0;">{{exp0}}</p>
      </div>
      <div id="exp-card-1" class="option-card" style="padding:30px 50px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-1" style="font-weight:900;color:white;font-size:80px;">B. {{opt1_hi}}</span>
        <p style="font-size:70px;font-weight:600;color:#bbb;line-height:1.4;margin:0;">{{exp1}}</p>
      </div>
      <div id="exp-card-2" class="option-card" style="padding:30px 50px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-2" style="font-weight:900;color:white;font-size:80px;">C. {{opt2_hi}}</span>
        <p style="font-size:70px;font-weight:600;color:#bbb;line-height:1.4;margin:0;">{{exp2}}</p>
      </div>
      <div id="exp-card-3" class="option-card" style="padding:30px 50px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-3" style="font-weight:900;color:white;font-size:80px;">D. {{opt3_hi}}</span>
        <p style="font-size:70px;font-weight:600;color:#bbb;line-height:1.4;margin:0;">{{exp3}}</p>
      </div>
    </div>
  </div>
  <script>'''
content = re.sub(exp_cards_pattern, new_cards, content, flags=re.DOTALL)

# Delete the expQEl scaling loop from javascript so our big fonts don't get touched
js_loop = r"let expQEl = document\.getElementById\('question-text-exp'\);.*?for \(let i = 0; i < 4; i\+\) \{.*?if\(expOptEl\).*?\n\s*\}"
content = re.sub(js_loop, "", content, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Update render_video_test.py
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

# Make sure it uses explain3
py_code = py_code.replace("window.setQuizState('explanation', 1, 0)", "window.setQuizState('explain3', 1, 0)")
# Re-apply detailed explanations
replace_block_regex = r"html = html\.replace\('\{\{subject_hi\}\}', 'भारतीय राजव्यवस्था'\).*?html = html\.replace\('\{\{exp3\}\}', '.*?'\)"
new_replace_block = """html = html.replace('{{subject_hi}}', 'भारतीय राजव्यवस्था')
    html = html.replace('{{chapter_hi}}', 'अध्याय 1: संविधान का निर्माण')
    html = html.replace('{{topic_hi}}', 'संविधान सभा')
    html = html.replace('{{question_hi}}', 'संविधान सभा की प्रथम बैठक कब हुई थी?')
    html = html.replace('{{opt0_hi}}', '9 दिसंबर 1946')
    html = html.replace('{{opt1_hi}}', '11 दिसंबर 1946')
    html = html.replace('{{opt2_hi}}', '15 अगस्त 1947')
    html = html.replace('{{opt3_hi}}', '26 जनवरी 1950')
    html = html.replace('{{correct_idx}}', '0')
    html = html.replace('{{exp0}}', '9 दिसंबर 1946 को संविधान सभा की पहली बैठक दिल्ली के ऐतिहासिक संसद भवन में हुई थी। इसमें डॉ. सच्चिदानंद सिन्हा को अस्थायी अध्यक्ष चुना गया था।')
    html = html.replace('{{exp1}}', '11 दिसंबर 1946 को संविधान सभा की दूसरी बैठक हुई, जिसमें डॉ. राजेंद्र प्रसाद को स्थायी अध्यक्ष और एच.सी. मुखर्जी को उपाध्यक्ष चुना गया था।')
    html = html.replace('{{exp2}}', '15 अगस्त 1947 भारत की आज़ादी का ऐतिहासिक दिन है। हालाँकि यह भारत के इतिहास का सबसे महत्वपूर्ण दिन है, यह संविधान सभा की बैठक से नहीं जुड़ा है।')
    html = html.replace('{{exp3}}', '26 जनवरी 1950 को भारत का संविधान पूर्ण रूप से लागू हुआ और भारत एक गणतंत्र देश बना। संविधान को बनने में 2 साल, 11 महीने और 18 दिन लगे थे।')"""

py_code = re.sub(replace_block_regex, new_replace_block, py_code, flags=re.DOTALL)

with open('render_video_test.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print("Ultimate Fix Applied!")
