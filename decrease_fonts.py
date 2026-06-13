import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacements = {
    # Main Header
    '<span style="font-size:120px;font-weight:900;color:#FF6B00': '<span style="font-size:80px;font-weight:900;color:#FF6B00',
    '<span style="font-size:100px;font-weight:600;color:#aaa': '<span style="font-size:70px;font-weight:600;color:#aaa',
    '<span style="font-size:100px;font-weight:800;color:#39FF14;" id="chapter-text"': '<span style="font-size:70px;font-weight:800;color:#39FF14;" id="chapter-text"',
    '<span style="font-size:100px;font-weight:600;color:#777;"': '<span style="font-size:70px;font-weight:600;color:#777;"',

    # Timer
    '<span style="font-size:30px;font-weight:700;color:#888': '<span style="font-size:24px;font-weight:700;color:#888',
    '<span id="timer-num" style="position:relative; font-size:110px; font-weight:900;': '<span id="timer-num" style="position:relative; font-size:80px; font-weight:900;',

    # Subscribe
    '<span style="font-size:80px;font-weight:900;color:white;letter-spacing:4px;">SUBSCRIBE</span>': '<span style="font-size:60px;font-weight:900;color:white;letter-spacing:4px;">SUBSCRIBE</span>',
    '<span style="font-size:90px;">🔔</span>': '<span style="font-size:70px;">🔔</span>',

    # Explain Page Header
    '<div id="chapter-text-exp" style="font-size:100px;font-weight:800;color:#39FF14;margin-top:16px;">': '<div id="chapter-text-exp" style="font-size:70px;font-weight:800;color:#39FF14;margin-top:16px;">',
    '<div style="font-size:100px;font-weight:700;color:#aaa;margin-top:10px;">': '<div style="font-size:70px;font-weight:700;color:#aaa;margin-top:10px;">',

    # Explain Page Details
    '<p style="font-size:90px;font-weight:500;color:#999': '<p style="font-size:65px;font-weight:500;color:#999'
}

for old_str, new_str in replacements.items():
    html = html.replace(old_str, new_str)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
