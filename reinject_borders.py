with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add randomizeTheme logic and CSS animations
animations = """
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
    @keyframes slideAnim { 0% { background-position: 0 0; } 100% { background-position: 100px 100px; } }
"""
html = html.replace("</style>", animations + "\n  </style>")

script_injection = """
    function randomizeTheme() {
        // Hardcode a single color for this test so it doesn't change, OR pick a random one
        // User wants ONE color, ONE border.
        const colors = ["#39FF14", "#FF00FF", "#00FFFF", "#FFEA00", "#FF007F", "#00FF00", "#7DF9FF", "#FF4500", "#B366FF", "#FF355E", "#FFAA00", "#00FA9A"];
        // For the single video, let's just pick one color
        const mainColor = colors[Math.floor(Math.random() * colors.length)];
        let clockColor = mainColor; // Keep clock same or different
        
        window.themeColor = mainColor;
        window.clockThemeColor = clockColor;
        
        document.getElementById('chapter-text').style.color = mainColor;
        document.getElementById('chapter-text-exp').style.color = mainColor;

        const decContainer = document.getElementById('decorations');
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
        
        // Pick one layout randomly for this video
        let styleIdx = Math.floor(Math.random() * frameLayouts.length);
        // Force the first style (Cyberpunk Dash) for this test to show the animation
        styleIdx = 0; 
        
        decContainer.innerHTML = frameLayouts[styleIdx];
        
        // Update clock
        const timerNum = document.getElementById("timer-num");
        const clockRing = document.getElementById("clock-ring");
        if(timerNum) timerNum.style.color = clockColor;
        if(clockRing) clockRing.style.stroke = clockColor;
        
        const ticks = document.querySelectorAll('#clock-ticks line');
        ticks.forEach(line => line.style.stroke = clockColor);
    }
"""

# Replace the runAutoFit function area to inject randomizeTheme
import re
html = re.sub(r'function runAutoFit\(\) \{', script_injection + r'\n    function runAutoFit() {', html)

# Modify setQuizState to ensure it updates clockRing color properly
# Wait, the current template has no clockRing logic for colors in setQuizState?
# It does, we reverted to the original. Let's make sure clockRing exists.

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Injected animations and borders successfully!")
