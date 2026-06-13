import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the static clock-outer HTML with a dynamic container
timer_html = '''<div id="dynamic-timer-container" style="display:flex; justify-content:center; align-items:center; position:relative; flex-shrink:0;"></div>'''
html = re.sub(r'<div class="clock-outer".*?</div>\s*</div>\s*</div>', timer_html, html, flags=re.DOTALL)

# Inject dynamic timer creation into randomizeTheme
timer_js = '''
        decContainer.innerHTML = frameLayouts[styleIdx];
        
        window.clockThemeColor = mainColor; // ensure this is set
        const timerContainer = document.getElementById("dynamic-timer-container");
        if(timerContainer) {
            const tStyles = ["circular_classic", "horizontal_bar", "square_outline", "liquid_drain"];
            const tStyle = tStyles[Math.floor(Math.random() * tStyles.length)];
            
            let tHTML = "";
            if(tStyle === "circular_classic") {
                tHTML = 
                <div class="clock-outer" style="width:340px; height:340px; border-radius:50%; background:#0a0a0a; border:12px solid #1a1a1a; box-shadow:0 0 60px 80; position:relative; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                  <svg style="position:absolute; width:340px; height:340px; transform:rotate(0deg);">
                    <circle id="clock-ring" cx="170" cy="170" r="164" stroke="" stroke-width="16" stroke-dasharray="1030.5" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" transform="rotate(-90 170 170)"/>
                  </svg>
                  <div class="clock-inner" style="width:260px; height:260px; border-radius:50%; border:6px solid 40; display:flex; align-items:center; justify-content:center; flex-direction:column; position:relative;">
                    <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;position:relative;z-index:2;margin-bottom:-10px;">TIME</span>
                    <span id="timer-num" style="position:relative; font-size:110px; font-weight:900; color:; font-family:monospace!important; z-index:2; line-height:1;">00:05</span>
                  </div>
                </div>;
            } else if (tStyle === "horizontal_bar") {
                tHTML = 
                <div style="display:flex; flex-direction:column; align-items:center; gap: 20px; width: 400px; padding: 20px; background:#111; border-radius:40px; border:4px solid 40; box-shadow:0 0 40px 40;">
                   <span id="timer-num" style="font-size:120px;font-weight:900;color:;font-family:monospace!important;letter-spacing:10px; line-height:1; text-shadow: 0 0 30px 80;">00:05</span>
                   <div style="width:100%; height:40px; background:#000; border-radius:20px; overflow:hidden; position:relative; box-shadow: inset 0 0 20px rgba(0,0,0,0.8);">
                       <div id="clock-bar" style="width:100%; height:100%; background:; box-shadow: 0 0 20px ;"></div>
                   </div>
                </div>;
            } else if (tStyle === "square_outline") {
                tHTML = 
                <div style="position:relative; width:340px; height:340px; display:flex; align-items:center; justify-content:center; transform: rotate(45deg); background:#0a0a0a; border-radius: 40px; box-shadow:0 0 60px 40;">
                    <svg width="340" height="340" style="position:absolute; top:0; left:0; filter: drop-shadow(0 0 20px );">
                       <rect id="clock-ring" x="20" y="20" width="300" height="300" rx="30" stroke="" stroke-width="16" fill="none" stroke-dasharray="1200" stroke-dashoffset="0" />
                    </svg>
                    <div style="transform: rotate(-45deg); text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                        <span id="timer-num" style="font-size:110px;font-weight:900;color:; line-height:1; font-family:monospace!important;">00:05</span>
                    </div>
                </div>;
            } else if (tStyle === "liquid_drain") {
                tHTML = 
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <div style="width:80px; height:20px; background:80; border-radius:20px 20px 0 0; box-shadow: 0 -10px 20px 40;"></div>
                    <div style="width: 200px; height: 320px; border: 12px solid #222; border-radius: 40px; position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; background:#000; box-shadow: 0 0 50px 40;">
                        <div id="clock-fill" style="position:absolute; bottom:0; left:0; width:100%; height:100%; background:; box-shadow: 0 0 40px ;"></div>
                        <span id="timer-num" style="font-size:80px;font-weight:900;color:#fff; z-index:2; text-shadow: 0 4px 10px rgba(0,0,0,0.8); font-family:monospace!important;">00:05</span>
                    </div>
                </div>;
            }
            timerContainer.innerHTML = tHTML;
        }
'''
html = html.replace('decContainer.innerHTML = frameLayouts[styleIdx];', timer_js)

# Remove the old static JS setup for clock properties
html = re.sub(r'// Apply Clock.*?\}\s*\}', '', html, flags=re.DOTALL)

# Now update the countdown logic in setQuizState
# Replace standard clockRing offset update
html = re.sub(r'const offset = progress \* CIRC;\s*if \(clockRing\) clockRing\.style\.strokeDashoffset = offset;', 
'''
          if (clockRing) {
              const totalLen = parseFloat(clockRing.getAttribute("stroke-dasharray") || CIRC);
              clockRing.style.strokeDashoffset = progress * totalLen;
          }
          const clockBar = document.getElementById("clock-bar");
          if(clockBar) {
              clockBar.style.width = (100 - (progress * 100)) + "%";
          }
          const clockFill = document.getElementById("clock-fill");
          if(clockFill) {
              clockFill.style.height = (100 - (progress * 100)) + "%";
          }
''', html)

# Question state reset
html = re.sub(r'if \(clockRing\) \{ clockRing\.style\.strokeDashoffset = "0"; clockRing\.style\.stroke = window\.clockThemeColor; \}',
'''
            if (clockRing) { clockRing.style.strokeDashoffset = "0"; clockRing.style.stroke = window.clockThemeColor; }
            const clockBar = document.getElementById("clock-bar");
            if(clockBar) { clockBar.style.width = "100%"; clockBar.style.background = window.clockThemeColor; }
            const clockFill = document.getElementById("clock-fill");
            if(clockFill) { clockFill.style.height = "100%"; clockFill.style.background = window.clockThemeColor; }
''', html)

# Red state
html = re.sub(r'if \(clockRing\) clockRing\.style\.stroke = "#FF4444";',
'''
              if (clockRing) clockRing.style.stroke = "#FF4444";
              const clockBar = document.getElementById("clock-bar");
              if(clockBar) clockBar.style.background = "#FF4444";
              const clockFill = document.getElementById("clock-fill");
              if(clockFill) clockFill.style.background = "#FF4444";
''', html)

# Normal state (after restoring from red, or just else branch)
html = re.sub(r'if \(clockRing\) clockRing\.style\.stroke = window\.clockThemeColor;',
'''
              if (clockRing) clockRing.style.stroke = window.clockThemeColor;
              const clockBar = document.getElementById("clock-bar");
              if(clockBar) clockBar.style.background = window.clockThemeColor;
              const clockFill = document.getElementById("clock-fill");
              if(clockFill) clockFill.style.background = window.clockThemeColor;
''', html)

# End state reveal
html = re.sub(r'if \(clockRing\) \{ clockRing\.style\.strokeDashoffset = CIRC; clockRing\.style\.stroke = "#FF4444"; \}',
'''
            if (clockRing) { 
                const totalLen = parseFloat(clockRing.getAttribute("stroke-dasharray") || CIRC);
                clockRing.style.strokeDashoffset = totalLen; 
                clockRing.style.stroke = "#FF4444"; 
            }
            const clockBar = document.getElementById("clock-bar");
            if(clockBar) { clockBar.style.width = "0%"; clockBar.style.background = "#FF4444"; }
            const clockFill = document.getElementById("clock-fill");
            if(clockFill) { clockFill.style.height = "0%"; clockFill.style.background = "#FF4444"; }
''', html)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Timer injected!")
