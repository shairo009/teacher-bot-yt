import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove old hardcoded decorations
html = re.sub(r'<!-- Corner triangles -->.*?(?=<!-- QUIZ PAGE -->)', '<div id="decorations"></div>\n\n  ', html, flags=re.DOTALL)

# 2. Add randomizeTheme script
script_injection = """
    function randomizeTheme() {
        const mainColor = "#00FFFF"; // Cyan color, static, no color change
        window.themeColor = mainColor;
        
        // Remove old backgrounds
        document.getElementById('chapter-text') && (document.getElementById('chapter-text').style.color = mainColor);
        document.getElementById('chapter-text-exp') && (document.getElementById('chapter-text-exp').style.color = mainColor);

        const decContainer = document.getElementById('decorations');
        if(!decContainer) return;
        
        decContainer.innerHTML = ''; 
        
        const frameLayouts = [
            // 0: Cyberpunk Frame with animated dash
            \<svg width="2160" height="3840" style="position:absolute;top:0;left:0;"><rect x="60" y="60" width="2040" height="3720" stroke="\" stroke-width="30" fill="none" stroke-dasharray="80 160" style="animation: borderDash 10s linear infinite;"/></svg>\,
            
            // 1: HUD Corners
            \<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <path d="M 60 400 L 60 60 L 400 60" stroke="\" stroke-width="40" fill="none"/>
              <path d="M 1760 60 L 2100 60 L 2100 400" stroke="\" stroke-width="40" fill="none"/>
              <path d="M 60 3440 L 60 3780 L 400 3780" stroke="\" stroke-width="40" fill="none"/>
              <path d="M 1760 3780 L 2100 3780 L 2100 3440" stroke="\" stroke-width="40" fill="none"/>
            </svg>\,
            
            // 2: Neon Pillars
            \<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <line x1="80" y1="0" x2="80" y2="3840" stroke="\" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite;" />
              <line x1="2080" y1="0" x2="2080" y2="3840" stroke="\" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite reverse;" />
            </svg>\,
            
            // 3: Thick Cinematic
            \<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <rect x="0" y="0" width="2160" height="120" fill="\" />
              <rect x="0" y="3720" width="2160" height="120" fill="\" />
            </svg>\,
            
            // 4: Minimalist Dots
            \<div style="position:absolute;top:0;left:0;width:100%;height:100%;background: radial-gradient(circle at center, transparent 40%, \22 100%); animation: slideAnim 15s linear infinite;"></div>
             <svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <circle cx="100" cy="100" r="30" fill="\"/>
              <circle cx="2060" cy="100" r="30" fill="\"/>
              <circle cx="100" cy="3740" r="30" fill="\"/>
              <circle cx="2060" cy="3740" r="30" fill="\"/>
            </svg>\,
            
            // 5: Double Rectangles
            \<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
              <rect x="40" y="40" width="2080" height="3760" stroke="\" stroke-width="10" fill="none"/>
              <rect x="80" y="80" width="2000" height="3680" stroke="\" stroke-width="20" fill="none" opacity="0.6"/>
            </svg>\
        ];
        
        let styleIdx = Math.floor(Math.random() * frameLayouts.length);
        styleIdx = 0; // Force layout 0 for demonstration
        decContainer.innerHTML = frameLayouts[styleIdx];
    }
"""
html = html.replace('const correctIdx = {{correct_idx}};', script_injection + '\n    const correctIdx = {{correct_idx}};')

# 3. Add clock style update logic inside setQuizState if needed
# Actually, the original clock is already fine!

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Rebuilt template successfully")
