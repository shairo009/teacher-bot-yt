import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove "classic" from tStyles to guarantee the user sees a different timer
html = html.replace('const tStyles = ["classic", "diamond", "thick", "dotted"];', 'const tStyles = ["diamond", "thick", "dotted"];')

# 2. Fix the "Color Shifting Borders" to be a "Double Pulse Glow" border that NEVER changes color
old_shifting_border = '`<div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:16px solid ${mainColor}; filter: hue-rotate(0deg); animation: rotateHue 8s linear infinite; box-shadow: inset 0 0 50px ${mainColor}, 0 0 50px ${mainColor};"></div>`'

new_double_pulse = '`<div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:16px solid ${mainColor}; color:${mainColor}; animation: pulseGlow 4s ease-in-out infinite; box-shadow: inset 0 0 50px ${mainColor}, 0 0 50px ${mainColor};"></div>`'

html = html.replace(old_shifting_border, new_double_pulse)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
