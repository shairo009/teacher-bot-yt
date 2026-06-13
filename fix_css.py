with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('@keyframes spin { 100% { transform: rotate(360deg); } }', '@keyframes spin { 100% { transform: rotate(360deg); } }\n    @keyframes pulse { 0% { opacity: 0.5; transform: scale(0.98); } 100% { opacity: 1; transform: scale(1.02); } }')

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
