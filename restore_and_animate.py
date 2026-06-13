import re

with open('templates/quiz_shorts.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace hardcoded text with variables
replacements = {
    'INDIAN POLITY (भारतीय राजव्यवस्था)': '{{subject_hi}}',
    'CHAPTER 1: MAKING OF THE CONSTITUTION (संविधान का निर्माण)': '{{chapter_hi}}',
    'CONSTITUENT ASSEMBLY (संविधान सभा)': '{{topic_hi}}',
    'संविधान सभा की प्रथम बैठक कब हुई थी?': '{{question_hi}}',
    '9 दिसंबर 1946': '{{opt0_hi}}',
    '11 दिसंबर 1946': '{{opt1_hi}}',
    '13 दिसंबर 1946': '{{opt2_hi}}',
    '26 जनवरी 1950': '{{opt3_hi}}',
    'const correctIdx = 0;': 'const correctIdx = {{correct_idx}};'
}

# In explain phase:
html = html.replace('संविधान सभा की प्रथम बैठक 9 दिसंबर 1946 को हुई थी।', '{{exp0}}')
html = html.replace('यह दिन संविधान सभा के गठन के बाद का है, लेकिन प्रथम बैठक नहीं।', '{{exp1}}')
html = html.replace('26 जनवरी 1950 को संविधान लागू हुआ।', '{{exp2}}')
html = html.replace('13 दिसंबर 1946 को उद्देश्य प्रस्ताव पेश किया गया।', '{{exp3}}')

for k, v in replacements.items():
    html = html.replace(k, v)

# 2. Add Animations
animations = """
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
    @keyframes slideAnim { 0% { background-position: 0 0; } 100% { background-position: 100px 100px; } }
"""
html = html.replace("</style>", animations + "\n  </style>")

# 3. Modify randomizeTheme to NOT change color constantly and just add animation classes
# In quiz_shorts.html, randomizeTheme creates HTML chunks. We just replace those chunks.
html = html.replace('stroke="\" stroke-width="20" fill="none" opacity="0.6"', 'stroke="\" stroke-width="20" fill="none" opacity="0.6"')
html = html.replace('stroke="\" stroke-width="40" fill="none"', 'stroke="\" stroke-width="40" fill="none"')

# Wait, instead of regex, let me inject the animations directly into the SVG HTML blocks of randomizeTheme.
html = html.replace('stroke-dasharray="100 200"', 'stroke-dasharray="100 200" style="animation: borderDash 10s linear infinite;"')
html = html.replace('stroke-dasharray="200 100"', 'stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite;"')
html = html.replace('background: radial-gradient(circle at center, transparent 30%, \22 100%);', 'background: radial-gradient(circle at center, transparent 30%, \22 100%); animation: slideAnim 15s linear infinite;')

# Disable color cycling:
html = html.replace('let clockColor = colors[Math.floor(Math.random() * colors.length)];', 'let clockColor = mainColor;')
html = html.replace('while(clockColor === mainColor) clockColor = colors[Math.floor(Math.random() * colors.length)];', '')

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Template restored perfectly from quiz_shorts.html with animations!")
