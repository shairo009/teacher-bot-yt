import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the giant explanation section with the new properly sized container, but KEEPING BIG FONTS
old_cards_section = re.search(r'<!-- Explanation Cards -->(.*?)</div>\s*</div>\s*<script>', html, flags=re.DOTALL)
if old_cards_section:
    old_str = old_cards_section.group(1)
    
    # Using BIG fonts: 80px for option letter, 70px for the detailed explanation
    new_str = '''
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
    '''
    html = html.replace(old_str, new_str)

# Remove auto-fit for Explain page so it uses our hardcoded 80px/70px
js_to_remove_regex = r"let expQEl = document\.getElementById\('question-text-exp'\);.*?for \(let i = 0; i < 4; i\+\) \{.*?if\(expOptEl\).*?\n\s*\}"
html = re.sub(js_to_remove_regex, "", html, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Now update dummy data to the VERY detailed text
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

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

print("Applied full screen layout with BIG FONTS and properly fitting containers!")
