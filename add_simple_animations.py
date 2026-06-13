with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

animations_css = """
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
    @keyframes slideAnim { 0% { background-position: 0 0; } 100% { background-position: 100px 100px; } }
"""
if "@keyframes spin" not in html:
    html = html.replace('</style>', animations_css + '\n  </style>')

# hud_corners animation
# geometric_bars animation
html = html.replace('<rect x="80" y="80" width="2000" height="3680" stroke="" stroke-width="40" fill="none" />', '<rect x="80" y="80" width="2000" height="3680" stroke="" stroke-width="40" fill="none" stroke-dasharray="100 200" style="animation: borderDash 15s linear infinite;" />')
# minimalist_dots animation
html = html.replace('background: radial-gradient(circle at center, transparent 30%, 22 100%);', 'background: radial-gradient(circle at center, transparent 30%, 22 100%); animation: slideAnim 10s linear infinite;')

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated borders with simple animations.")
