import os
import io

def recover_template():
    # Attempt to read as utf-16 first
    try:
        with open('templates_quiz_shorts_template_copy.html', 'r', encoding='utf-16') as f:
            content = f.read()
    except Exception:
        with open('templates_quiz_shorts_template_copy.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
    with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
recover_template()
print("Recovered template from copy!")
