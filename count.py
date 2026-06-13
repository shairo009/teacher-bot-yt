with open('temp_script.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'//.*', '', text)
text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
text = re.sub(r'`[^`]*`', '``', text, flags=re.DOTALL)
text = re.sub(r'\"[^\"]*\"', '\"\"', text, flags=re.DOTALL)
text = re.sub(r'\'[^\']*\'', '\'\'', text, flags=re.DOTALL)

open_braces = text.count('{')
close_braces = text.count('}')
print(f'{{ : {open_braces}, }} : {close_braces}')
