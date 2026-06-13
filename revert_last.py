import re

# 1. Read pristine HTML
with open('pristine.html', 'r', encoding='utf-8') as f:
    pristine = f.read()

# Extract pristine page-explain
pristine_explain_match = re.search(r'(<div id="page-explain".*?</div>\s*</div>\s*</div>)', pristine, flags=re.DOTALL)
pristine_explain = pristine_explain_match.group(1)

# Apply decrease_fonts.py logic to pristine_explain
replacements = {
    '<div id="chapter-text-exp" style="font-size:100px;font-weight:800;color:#39FF14;margin-top:16px;">': '<div id="chapter-text-exp" style="font-size:70px;font-weight:800;color:#39FF14;margin-top:16px;">',
    '<div style="font-size:100px;font-weight:700;color:#aaa;margin-top:10px;">': '<div style="font-size:70px;font-weight:700;color:#aaa;margin-top:10px;">',
    '<p style="font-size:90px;font-weight:500;color:#999': '<p style="font-size:65px;font-weight:500;color:#999'
}
for o, n in replacements.items():
    pristine_explain = pristine_explain.replace(o, n)

# Extract pristine JS logic for expQEl
pristine_js_match = re.search(r'(let expQEl = document\.getElementById\(\'question-text-exp\'\);.*?\n\s*\})', pristine, flags=re.DOTALL)
pristine_js = pristine_js_match.group(1)


# 2. Read current HTML
with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    current = f.read()

# Replace current page-explain with pristine
current = re.sub(r'<div id="page-explain".*?</div>\s*</div>\s*</div>', pristine_explain, current, flags=re.DOTALL)

# Re-inject the JS logic
# It should go right after "pgExp.style.display = "flex";"
# We removed it entirely before, so we just need to find pgExp.style.display = "flex"; and insert it after.
current = re.sub(r'(pgExp\.style\.display = "flex";)', r'\1\n\n        ' + pristine_js, current)

# Write back
with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(current)

# 3. Restore render_video_test.py dummy data
with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

# Replace the giant new replacements block with the old short ones
replace_block_regex = r"html = html\.replace\('\{\{subject_hi\}\}', 'भारतीय राजव्यवस्था'\).*?html = html\.replace\('\{\{exp3\}\}', '.*?'\)"
old_replace_block = """html = html.replace('{{subject_hi}}', 'भारतीय राजव्यवस्था')
    html = html.replace('{{chapter_hi}}', 'अध्याय 1: संविधान का निर्माण')
    html = html.replace('{{topic_hi}}', 'संविधान सभा')
    html = html.replace('{{question_hi}}', 'संविधान सभा की प्रथम बैठक कब हुई थी?')
    html = html.replace('{{opt0_hi}}', '9 दिसंबर 1946')
    html = html.replace('{{opt1_hi}}', '11 दिसंबर 1946')
    html = html.replace('{{opt2_hi}}', '15 अगस्त 1947')
    html = html.replace('{{opt3_hi}}', '26 जनवरी 1950')
    html = html.replace('{{correct_idx}}', '0')
    html = html.replace('{{exp0}}', 'संविधान सभा की प्रथम बैठक 9 दिसंबर 1946 को हुई थी।')
    html = html.replace('{{exp1}}', 'यह दिन संविधान सभा के गठन के बाद का है, लेकिन प्रथम बैठक नहीं।')
    html = html.replace('{{exp2}}', '15 अगस्त 1947 को भारत को स्वतंत्रता मिली।')
    html = html.replace('{{exp3}}', '26 जनवरी 1950 को संविधान लागू हुआ।')"""

py_code = re.sub(replace_block_regex, old_replace_block, py_code, flags=re.DOTALL)

with open('render_video_test.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print("Reverted to previous layout!")
