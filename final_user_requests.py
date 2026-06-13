import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Do not hide the other 3 answers during reveal
# In the `reveal` phase block:
old_reveal_hide = '''            } else {
              card.style.opacity = "0.35";
            }'''
new_reveal_hide = '''            } else {
              card.style.opacity = "1"; /* User requested not to hide */
            }'''
html = html.replace(old_reveal_hide, new_reveal_hide)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Fix the render script so it calls 'explain3' instead of 'explanation' to show all options
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

old_render_explain = '''await page.evaluate("window.setQuizState('explanation', 1, 0)")'''
new_render_explain = '''await page.evaluate("window.setQuizState('explain3', 1, 0)")'''
py_code = py_code.replace(old_render_explain, new_render_explain)

with open('render_video_test.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print("Applied fixes!")
