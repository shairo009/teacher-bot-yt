import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the randomizeTheme function entirely with the awesome SVG ones
new_randomize_theme = '''
    window.randomizeTheme = function() {
        const colors = ["#39FF14", "#FF00FF", "#00FFFF", "#FFEA00", "#FF007F", "#00FF00", "#7DF9FF", "#FF4500", "#B366FF", "#FF355E", "#FFAA00", "#00FA9A"];
        const mainColor = colors[Math.floor(Math.random() * colors.length)];
        window.themeColor = mainColor;
        
        // Ensure text elements use the main color
        const chapterText = document.getElementById('chapter-text');
        if(chapterText) chapterText.style.color = mainColor;
        const chapterExp = document.getElementById('chapter-text-exp');
        if(chapterExp) chapterExp.style.color = mainColor;
        
        const decContainer = document.getElementById('decorations');
        if(!decContainer) return;
        
        decContainer.innerHTML = ''; 
        
        const frameLayouts = [
            // 0: Cyberpunk Frame with animated dash
            <svg width="2160" height="3840" style="position:absolute;top:0;left:0;"><rect x="60" y="60" width="2040" height="3720" stroke="" stroke-width="30" fill="none" stroke-dasharray="80 160" style="animation: borderDash 10s linear infinite;"/></svg>,
            // 1: Neon Pillars
            <svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <line x1="80" y1="0" x2="80" y2="3840" stroke="" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite;" />
              <line x1="2080" y1="0" x2="2080" y2="3840" stroke="" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite reverse;" />
            </svg>,
            // 2: Minimalist Dots
            <div style="position:absolute;top:0;left:0;width:100%;height:100%;background: radial-gradient(circle at center, transparent 40%, 22 100%); animation: slideAnim 15s linear infinite;"></div>
             <svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <circle cx="100" cy="100" r="30" fill=""/>
              <circle cx="2060" cy="100" r="30" fill=""/>
              <circle cx="100" cy="3740" r="30" fill=""/>
              <circle cx="2060" cy="3740" r="30" fill=""/>
            </svg>
        ];
        
        let styleIdx = Math.floor(Math.random() * frameLayouts.length);
        decContainer.innerHTML = frameLayouts[styleIdx];
    }
'''

html = re.sub(r'window\.randomizeTheme = function\(\) \{.*?(?=const correctIdx)', new_randomize_theme + '\n    ', html, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
