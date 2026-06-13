import re

# Read pristine template
with open('templates/quiz_shorts.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. FIX THE TIMER HTML LOCATION (Keep it 340x340 in Top Right)
timer_placeholder = '''
      <!-- Restored Clock Timer -->
      <div id="dynamic-timer-container" style="width:340px; height:340px; position:relative; flex-shrink:0;">
      </div>
'''
# Replace the original clock div
html = re.sub(r'<div class="clock-outer".*?</div>\s*</div>\s*</div>', timer_placeholder, html, flags=re.DOTALL)

# 2. Inject CSS animations into the <style> block
animations = '''
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
    @keyframes slideAnim { 0% { background-position: 0 0; } 100% { background-position: 100% 100%; } }
'''
html = html.replace('</style>', animations + '\n  </style>')

# 3. Update JS randomizeTheme
# First, find randomizeTheme and rewrite its inner body completely.
js_new_randomize = '''
    function randomizeTheme() {
      const colors = ["#39FF14", "#FF00FF", "#00FFFF", "#FFEA00", "#FF007F", "#00FF00", "#7DF9FF", "#FF4500", "#B366FF", "#FF355E", "#FFAA00", "#00FA9A"];
      const mainColor = colors[Math.floor(Math.random() * colors.length)];
      
      // USER REQUEST: Timer color MUST match border color
      window.themeColor = mainColor;
      window.clockThemeColor = mainColor; 

      // Apply to Text
      const ct = document.getElementById('chapter-text');
      if(ct) ct.style.color = mainColor;
      const cte = document.getElementById('chapter-text-exp');
      if(cte) cte.style.color = mainColor;

      // ----------------------------------------
      // USER REQUEST: Animated Video Borders
      // ----------------------------------------
      const decContainer = document.getElementById('decorations');
      if(decContainer) {
          const frameLayouts = [
              // 0: Cyberpunk Frame with animated dash
              `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;"><rect x="60" y="60" width="2040" height="3720" stroke="${mainColor}" stroke-width="30" fill="none" stroke-dasharray="80 160" style="animation: borderDash 10s linear infinite;"/></svg>`,
              // 1: Neon Pillars
              `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
                <line x1="80" y1="0" x2="80" y2="3840" stroke="${mainColor}" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite;" />
                <line x1="2080" y1="0" x2="2080" y2="3840" stroke="${mainColor}" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite reverse;" />
              </svg>`,
              // 2: Dotted minimalist
              `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
                <rect x="50" y="50" width="2060" height="3740" stroke="${mainColor}" stroke-width="20" stroke-dasharray="20 40" fill="none" style="animation: borderDash 20s linear infinite;" />
              </svg>`
          ];
          decContainer.innerHTML = frameLayouts[Math.floor(Math.random() * frameLayouts.length)];
      }

      // ----------------------------------------
      // USER REQUEST: Timers exactly in their place, 340x340
      // ----------------------------------------
      const timerContainer = document.getElementById("dynamic-timer-container");
      if(timerContainer) {
          const tStyles = ["classic", "diamond", "thick", "dotted"];
          const tStyle = tStyles[Math.floor(Math.random() * tStyles.length)];
          let tHTML = "";
          
          if(tStyle === "classic") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; background:#0a0a0a; border:12px solid #1a1a1a; box-shadow:0 0 60px ${mainColor}80; position:relative; display:flex; align-items:center; justify-content:center;">
                <svg style="position:absolute; width:340px; height:340px;">
                  <circle id="clock-ring" cx="170" cy="170" r="164" stroke="${mainColor}" stroke-width="16" stroke-dasharray="1030.5" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" transform="rotate(-90 170 170)"/>
                </svg>
                <div style="width:260px; height:260px; border-radius:50%; border:6px solid ${mainColor}40; display:flex; align-items:center; justify-content:center; flex-direction:column;">
                  <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:110px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "diamond") {
              tHTML = `
              <div style="width:340px; height:340px; background:#0a0a0a; box-shadow:0 0 60px ${mainColor}80; position:relative; display:flex; align-items:center; justify-content:center; transform: rotate(45deg); border-radius:30px;">
                <svg style="position:absolute; width:340px; height:340px;">
                  <rect id="clock-ring" x="15" y="15" width="310" height="310" rx="30" stroke="${mainColor}" stroke-width="16" stroke-dasharray="1240" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" />
                </svg>
                <div style="transform: rotate(-45deg); display:flex; flex-direction:column; align-items:center; justify-content:center;">
                  <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:110px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "thick") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; position:relative; display:flex; align-items:center; justify-content:center; background:#111; box-shadow: inset 0 0 30px ${mainColor}80;">
                <svg style="position:absolute; width:340px; height:340px;">
                  <circle id="clock-ring" cx="170" cy="170" r="140" stroke="${mainColor}" stroke-width="40" stroke-dasharray="880" stroke-dashoffset="0" fill="transparent" transform="rotate(-90 170 170)"/>
                </svg>
                <div style="position:relative; z-index:10; display:flex; flex-direction:column; align-items:center;">
                  <span style="font-size:30px;font-weight:700;color:#fff;letter-spacing:4px;margin-bottom:-10px; text-shadow: 0 0 10px #000;">TIME</span>
                  <span id="timer-num" style="font-size:110px; font-weight:900; color:#fff; font-family:monospace!important; line-height:1; text-shadow: 0 0 10px #000;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "dotted") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; position:relative; display:flex; align-items:center; justify-content:center; box-shadow: 0 0 40px ${mainColor}60;">
                <svg style="position:absolute; width:340px; height:340px; animation: spin 20s linear infinite;">
                  <circle id="clock-ring" cx="170" cy="170" r="160" stroke="${mainColor}" stroke-width="12" stroke-dasharray="20 30" stroke-dashoffset="0" fill="transparent"/>
                </svg>
                <div style="width:280px; height:280px; border-radius:50%; background:#111; display:flex; flex-direction:column; align-items:center; justify-content:center; position:relative; z-index:2; border: 4px solid ${mainColor};">
                  <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:110px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          }
          timerContainer.innerHTML = tHTML;
      }

      // Box borders generator
      const borderStyles = ["solid", "dashed", "dotted"];
      window.dynamicBorderStyle = {
        style: borderStyles[Math.floor(Math.random() * borderStyles.length)],
        width: 10,
        shadow: `0 0 30px ${mainColor}`,
        selector: "all"
      };
    }
'''

# We need to replace the ENTIRE existing function randomizeTheme() { ... } with js_new_randomize
html = re.sub(r'function randomizeTheme\(\) \{.*?(?=// Run autofit and randomize on load)', js_new_randomize + '\n    ', html, flags=re.DOTALL)

# 4. Update the logic inside setQuizState
# Specifically, we need to handle the fact that strokeDashoffset totalLen is dynamically read from stroke-dasharray

update_js = '''
          if (clockRing) {
              const totalLen = parseFloat(clockRing.getAttribute("stroke-dasharray") || CIRC);
              clockRing.style.strokeDashoffset = progress * totalLen;
          }
'''
html = re.sub(r'const offset = progress \* CIRC;\s*if \(clockRing\) clockRing\.style\.strokeDashoffset = offset;', update_js, html)

reset_js = '''
            if (clockRing) { clockRing.style.strokeDashoffset = "0"; clockRing.style.stroke = window.clockThemeColor; }
'''
html = re.sub(r'if \(clockRing\) \{ clockRing\.style\.strokeDashoffset = "0"; clockRing\.style\.stroke = window\.clockThemeColor; \}', reset_js, html)

# Red end state
end_js = '''
            if (clockRing) { 
                const totalLen = parseFloat(clockRing.getAttribute("stroke-dasharray") || CIRC);
                clockRing.style.strokeDashoffset = totalLen; 
                clockRing.style.stroke = "#FF4444"; 
            }
'''
html = re.sub(r'if \(clockRing\) \{ clockRing\.style\.strokeDashoffset = CIRC; clockRing\.style\.stroke = "#FF4444"; \}', end_js, html)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Template reset successfully')
