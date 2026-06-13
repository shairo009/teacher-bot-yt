import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace hardcoded text with template variables and fix padding/gap to prevent overflow
old_cards_section = re.search(r'<!-- Explanation Cards -->(.*?)</div>\s*</div>\s*<script>', html, flags=re.DOTALL)
if old_cards_section:
    old_str = old_cards_section.group(1)
    
    new_str = '''
    <div style="display:flex;flex-direction:column;gap:30px;width:100%;height:100%;justify-content:center;padding:60px 0;">
      <div id="exp-card-0" class="option-card" style="padding:40px 60px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-0" style="font-weight:900;color:white;font-size:60px;">A. {{opt0_hi}}</span>
        <p style="font-size:45px;font-weight:600;color:#bbb;line-height:1.5;margin:0;">{{exp0}}</p>
      </div>
      <div id="exp-card-1" class="option-card" style="padding:40px 60px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-1" style="font-weight:900;color:white;font-size:60px;">B. {{opt1_hi}}</span>
        <p style="font-size:45px;font-weight:600;color:#bbb;line-height:1.5;margin:0;">{{exp1}}</p>
      </div>
      <div id="exp-card-2" class="option-card" style="padding:40px 60px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-2" style="font-weight:900;color:white;font-size:60px;">C. {{opt2_hi}}</span>
        <p style="font-size:45px;font-weight:600;color:#bbb;line-height:1.5;margin:0;">{{exp2}}</p>
      </div>
      <div id="exp-card-3" class="option-card" style="padding:40px 60px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:20px;opacity:0;min-height:auto;flex-grow:1;">
        <span id="exp-text-3" style="font-weight:900;color:white;font-size:60px;">D. {{opt3_hi}}</span>
        <p style="font-size:45px;font-weight:600;color:#bbb;line-height:1.5;margin:0;">{{exp3}}</p>
      </div>
    '''
    html = html.replace(old_str, new_str)


# 2. Remove the auto-fit for Explain page in JavaScript (so our fixed sizes are preserved)
# Find the block from "let expQEl = document.getElementById('question-text-exp');" 
# to "if(expOptEl) expOptEl.style.fontSize = expSz + "px";"
js_to_remove_regex = r"let expQEl = document.getElementById\('question-text-exp'\);.*?for \(let i = 0; i < 4; i\+\) \{.*?if\(expOptEl\).*?\n\s*\}"
html = re.sub(js_to_remove_regex, "", html, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)


# Update the dummy data in render_video_test.py to have VERY detailed text
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

# Let's make the explanations more substantial and formatting-friendly
new_explanations = {
    "{{exp0}}": "9 दिसंबर 1946 को संविधान सभा की पहली बैठक दिल्ली के ऐतिहासिक संसद भवन में हुई थी। इसमें डॉ. सच्चिदानंद सिन्हा को सबसे बुजुर्ग सदस्य होने के नाते सर्वसम्मति से अस्थायी अध्यक्ष चुना गया था। मुस्लिम लीग ने इस बैठक का बहिष्कार किया था।",
    "{{exp1}}": "11 दिसंबर 1946 को संविधान सभा की दूसरी महत्वपूर्ण बैठक हुई, जिसमें डॉ. राजेंद्र प्रसाद को स्थायी अध्यक्ष (President) और एच.सी. मुखर्जी को उपाध्यक्ष (Vice-President) निर्वाचित किया गया। सर बी.एन. राव को संवैधानिक सलाहकार नियुक्त किया गया।",
    "{{exp2}}": "15 अगस्त 1947 भारत की आज़ादी का ऐतिहासिक दिन है। इस दिन हमारा देश लंबे ब्रिटिश शासन से आज़ाद हुआ था। हालाँकि यह भारत के इतिहास का सबसे महत्वपूर्ण दिन है, लेकिन यह संविधान सभा की बैठक से जुड़ा हुआ नहीं है।",
    "{{exp3}}": "26 जनवरी 1950 को भारत का संविधान पूर्ण रूप से लागू हुआ और भारत एक संप्रभु लोकतांत्रिक गणराज्य बना। इसी कारण हर साल 26 जनवरी को गणतंत्र दिवस (Republic Day) के रूप में मनाया जाता है। संविधान को बनने में 2 साल, 11 महीने और 18 दिन लगे थे।"
}

for o, n in new_explanations.items():
    # Because previous script might have already replaced them, we'll replace the existing replacements
    pass # Wait, render script uses replace('{{exp0}}', '...'), so the original template variables must still be in the replace call!

# Let's just fix the render script completely for the replacements section
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

print("Applied fix for cut off options and detailed explanations.")
