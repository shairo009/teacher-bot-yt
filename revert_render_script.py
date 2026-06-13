with open('render_video_test.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

import re
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

print("Render script dummy data reverted!")
