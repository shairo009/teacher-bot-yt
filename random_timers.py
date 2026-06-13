import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update randomizeTheme to fix colors and inject dynamic timer logic
# The user wants clockColor to MATCH mainColor always.
old_color_logic = '''const mainColor = colors[Math.floor(Math.random() * colors.length)];
      let clockColor = colors[Math.floor(Math.random() * colors.length)];
      while(clockColor === mainColor) clockColor = colors[Math.floor(Math.random() * colors.length)];
      
      window.themeColor = mainColor;'''

new_color_logic = '''const mainColor = colors[Math.floor(Math.random() * colors.length)];
      let clockColor = mainColor; // Same as border color
      
      window.themeColor = mainColor;
      window.clockThemeColor = mainColor; // Fix undefined error and sync'''

html = html.replace(old_color_logic, new_color_logic)

# 2. Inject dynamic timers into randomizeTheme
# I will find where it says "// Apply Clock" and replace the static DOM updates with a dynamic innerHTML update.

old_apply_clock = '''// Apply Clock
      const clockRing = document.getElementById('clock-ring');
      if (clockRing) clockRing.style.stroke = clockColor;
      document.getElementById('timer-num').style.color = clockColor;
      const ticks = document.querySelectorAll('#clock-ticks line');
      ticks.forEach(line => line.style.stroke = clockColor);
      
      const clockInner = document.querySelector('.clock-inner');
      const clockOuter = document.querySelector('.clock-outer');
      if (clockInner) clockInner.style.borderColor = clockColor;
      if (clockOuter) {
        clockOuter.style.boxShadow = `0 0 60px ${clockColor}80`;
        const innerBorderStyles = ["solid", "dashed"];
        clockOuter.style.borderStyle = innerBorderStyles[Math.floor(Math.random() * innerBorderStyles.length)];
      }'''

dynamic_timer_logic = '''// Dynamic Timers
      const timerContainer = document.getElementById("dynamic-timer-container");
      if(timerContainer) {
          const tStyles = ["classic", "diamond", "thick", "dotted"];
          const tStyle = tStyles[Math.floor(Math.random() * tStyles.length)];
          let tHTML = "";
          
          if(tStyle === "classic") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; background:#0a0a0a; border:12px solid #1a1a1a; box-shadow:0 0 60px ${mainColor}80; position:relative; display:flex; align-items:center; justify-content:center;">
                <svg style="position:absolute; top:-12px; left:-12px; width:340px; height:340px; overflow:visible;">
                  <circle id="clock-ring" cx="170" cy="170" r="164" stroke="${mainColor}" stroke-width="16" stroke-dasharray="1030.5" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" transform="rotate(-90 170 170)"/>
                </svg>
                <div style="width:260px; height:260px; border-radius:50%; border:6px solid ${mainColor}40; display:flex; align-items:center; justify-content:center; flex-direction:column;">
                  <span style="font-size:24px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:80px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "diamond") {
              tHTML = `
              <div style="width:340px; height:340px; background:#0a0a0a; box-shadow:0 0 60px ${mainColor}80; position:relative; display:flex; align-items:center; justify-content:center; transform: rotate(45deg); border-radius:30px;">
                <svg style="position:absolute; top:-12px; left:-12px; width:340px; height:340px; overflow:visible;">
                  <circle id="clock-ring" cx="170" cy="170" r="164" stroke="${mainColor}" stroke-width="16" stroke-dasharray="1030.5" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" />
                </svg>
                <div style="transform: rotate(-45deg); display:flex; flex-direction:column; align-items:center; justify-content:center;">
                  <span style="font-size:24px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:80px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "thick") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; position:relative; display:flex; align-items:center; justify-content:center; background:#111; box-shadow: inset 0 0 30px ${mainColor}80;">
                <svg style="position:absolute; top:-12px; left:-12px; width:340px; height:340px; overflow:visible;">
                  <circle id="clock-ring" cx="170" cy="170" r="164" stroke="${mainColor}" stroke-width="40" stroke-dasharray="1030.5" stroke-dashoffset="0" fill="transparent" transform="rotate(-90 170 170)"/>
                </svg>
                <div style="position:relative; z-index:10; display:flex; flex-direction:column; align-items:center;">
                  <span style="font-size:24px;font-weight:700;color:#fff;letter-spacing:4px;margin-bottom:-10px; text-shadow: 0 0 10px #000;">TIME</span>
                  <span id="timer-num" style="font-size:80px; font-weight:900; color:#fff; font-family:monospace!important; line-height:1; text-shadow: 0 0 10px #000;">00:05</span>
                </div>
              </div>`;
          } else if (tStyle === "dotted") {
              tHTML = `
              <div style="width:340px; height:340px; border-radius:50%; position:relative; display:flex; align-items:center; justify-content:center; box-shadow: 0 0 40px ${mainColor}60;">
                <svg style="position:absolute; top:-12px; left:-12px; width:340px; height:340px; overflow:visible; animation: rotateHue 20s linear infinite;">
                  <circle id="clock-ring" cx="170" cy="170" r="164" stroke="${mainColor}" stroke-width="12" stroke-dasharray="1030.5" stroke-dashoffset="0" fill="transparent"/>
                </svg>
                <div style="width:280px; height:280px; border-radius:50%; background:#111; display:flex; flex-direction:column; align-items:center; justify-content:center; position:relative; z-index:2; border: 4px dashed ${mainColor};">
                  <span style="font-size:24px;font-weight:700;color:#888;letter-spacing:4px;margin-bottom:-10px;">TIME</span>
                  <span id="timer-num" style="font-size:80px; font-weight:900; color:${mainColor}; font-family:monospace!important; line-height:1;">00:05</span>
                </div>
              </div>`;
          }
          timerContainer.innerHTML = tHTML;
      }'''

html = html.replace(old_apply_clock, dynamic_timer_logic)

# 3. Replace the static timer HTML block with the dynamic container
# We must capture exactly from <div class="clock-outer"... down to its closing </div>
# In the pristine template, this block is 43 lines long. 
# Using a regex DOTALL replacement is safest.

timer_placeholder = '''<!-- Restored Clock Timer -->
      <div id="dynamic-timer-container" style="width:340px; height:340px; position:relative; flex-shrink:0;">
      </div>'''

html = re.sub(r'<!-- Restored Clock Timer -->\s*<div class="clock-outer".*?</div>\s*</div>', timer_placeholder, html, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
