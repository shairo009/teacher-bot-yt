import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Hide Top Row and Question from the Explanation Page
old_explain_top = '''    <!-- TOP ROW -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:50px;">
      <div>
        <span style="font-size:80px;font-weight:900;color:#FF6B00;letter-spacing:6px;">LUCENT GK</span>
        <div id="chapter-text-exp" style="font-size:70px;font-weight:800;color:#39FF14;margin-top:16px;">CHAPTER 1: MAKING OF THE CONSTITUTION (संविधान का निर्माण)</div>
        <div style="font-size:70px;font-weight:700;color:#aaa;margin-top:10px;">✅ सही उत्तर और व्याख्या</div>
      </div>
    </div>

    <!-- Repeated question -->
    <div style="height:650px; display:flex; align-items:center; justify-content:center; text-align:center; margin-bottom:100px;">
      <h3 id="question-text-exp" style="font-weight:900;color:white;line-height:1.2;margin:0;max-height:100%;overflow:hidden;display:flex;align-items:center;">संविधान सभा की प्रथम बैठक कब हुई थी?</h3>
    </div>'''

new_explain_top = '''    <!-- TOP ROW (HIDDEN PER USER REQUEST) -->
    <div style="display:none;align-items:flex-start;justify-content:space-between;margin-bottom:50px;">
      <div>
        <span style="font-size:80px;font-weight:900;color:#FF6B00;letter-spacing:6px;">LUCENT GK</span>
        <div id="chapter-text-exp" style="font-size:70px;font-weight:800;color:#39FF14;margin-top:16px;">CHAPTER 1: MAKING OF THE CONSTITUTION (संविधान का निर्माण)</div>
        <div style="font-size:70px;font-weight:700;color:#aaa;margin-top:10px;">✅ सही उत्तर और व्याख्या</div>
      </div>
    </div>

    <!-- Repeated question (HIDDEN PER USER REQUEST) -->
    <div style="display:none; height:650px; align-items:center; justify-content:center; text-align:center; margin-bottom:100px;">
      <h3 id="question-text-exp" style="font-weight:900;color:white;line-height:1.2;margin:0;max-height:100%;overflow:hidden;align-items:center;">संविधान सभा की प्रथम बैठक कब हुई थी?</h3>
    </div>'''
html = html.replace(old_explain_top, new_explain_top)

# Update Explanation Cards container to fill screen and space out
old_exp_cards_container = '<div style="display:flex;flex-direction:column;gap:30px;width:100%;">'
new_exp_cards_container = '<div style="display:flex;flex-direction:column;gap:80px;width:100%;height:100%;justify-content:center;padding:100px 0;">'
html = html.replace(old_exp_cards_container, new_exp_cards_container)

# Update each explanation card to use more space
for i in range(4):
    old_card = f'<div id="exp-card-{i}" class="option-card" style="padding:40px 60px;flex-direction:column;align-items:center;text-align:center;gap:16px;opacity:0;">'
    new_card = f'<div id="exp-card-{i}" class="option-card" style="padding:80px 100px;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:40px;opacity:0;min-height:700px;flex-grow:1;">'
    html = html.replace(old_card, new_card)
    
    # Increase explanation paragraph text size for better readability on huge cards
    old_p = f'<p style="font-size:65px;font-weight:500;color:#999;line-height:1.4;margin:0;">'
    new_p = f'<p style="font-size:75px;font-weight:600;color:#bbb;line-height:1.5;margin:0;">'
    html = html.replace(old_p, new_p)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)


# Now update the render script to have detailed dummy data
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

replacements_py = {
    "html = html.replace('{{exp0}}', 'संविधान 26 जनवरी 1950 को पूर्ण रूप से लागू हुआ।')": "html = html.replace('{{exp0}}', '9 दिसंबर 1946 को संविधान सभा की पहली बैठक नई दिल्ली के संसद भवन (अब सेंट्रल हॉल) में हुई थी, जिसमें डॉ. सच्चिदानंद सिन्हा को अस्थायी अध्यक्ष चुना गया था।')",
    "html = html.replace('{{exp1}}', '')": "html = html.replace('{{exp1}}', '11 दिसंबर 1946 को संविधान सभा की दूसरी बैठक हुई, जिसमें डॉ. राजेंद्र प्रसाद को स्थायी अध्यक्ष और एच.सी. मुखर्जी को उपाध्यक्ष चुना गया था।')",
    "html = html.replace('{{exp2}}', '')": "html = html.replace('{{exp2}}', '15 अगस्त 1947 भारत की आज़ादी का दिन है। इस दिन हमारा देश ब्रिटिश शासन से आज़ाद हुआ था। यह संविधान की बैठक का दिन नहीं है।')",
    "html = html.replace('{{exp3}}', '')": "html = html.replace('{{exp3}}', '26 जनवरी 1950 को भारत का संविधान पूर्ण रूप से लागू हुआ और भारत एक गणतंत्र देश बना, इसलिए इसे गणतंत्र दिवस कहते हैं।')"
}

for o, n in replacements_py.items():
    py_code = py_code.replace(o, n)

with open('render_video_test.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print("Applied full screen explanation fixes!")
