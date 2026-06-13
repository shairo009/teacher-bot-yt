with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
html = html.replace('// Run autofit and randomize on load', '} // Run autofit and randomize on load')

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Brace added')
