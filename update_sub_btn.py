import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

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

html = html.replace(old_btn, new_btn)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Subscribe button updated!")
