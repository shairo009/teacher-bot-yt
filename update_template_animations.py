import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add CSS animations to the <style> block
animations_css = """
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @keyframes pulseGlow { 0%, 100% { opacity: 0.5; filter: drop-shadow(0 0 10px currentColor); } 50% { opacity: 1; filter: drop-shadow(0 0 40px currentColor); } }
    @keyframes slideAnim { 0% { background-position: 0 0; } 100% { background-position: 100px 100px; } }
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
"""
if "@keyframes spin" not in html:
    html = html.replace('</style>', animations_css + '\n  </style>')

# 2. Modify border layouts to include animation classes
html = html.replace('stroke="" stroke-width="20" fill="none" opacity="0.6"', 'stroke="" stroke-width="20" fill="none" opacity="0.6" style="animation: pulseGlow 3s infinite;"')
html = html.replace('<rect x="80" y="80" width="2000" height="3680" stroke="" stroke-width="40"', '<rect x="80" y="80" width="2000" height="3680" stroke="" stroke-width="40" stroke-dasharray="100 200" style="animation: borderDash 10s linear infinite;"')
html = html.replace('background: radial-gradient(circle at center, transparent 30%, 22 100%);', 'background: radial-gradient(circle at center, transparent 30%, 22 100%); animation: pulseGlow 4s infinite;')

# 3. Dynamic Timers
# Instead of replacing HTML, let's inject a container with 4 timers and show one.
timer_html = """
      <!-- Dynamic Timers -->
      <div id="dynamic-timers" style="width:340px; height:340px; position:relative; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
        <!-- Timer 0: Default Circle -->
        <div id="timer-style-0" class="clock-outer" style="width:340px; height:340px; border-radius:50%; background:#0a0a0a; border:12px solid #1a1a1a; box-shadow:0 0 60px rgba(124,58,237,0.5); position:absolute; display:flex; align-items:center; justify-content:center;">
          <svg style="position:absolute; top:-12px; left:-12px; width:340px; height:340px; overflow:visible;">
            <circle id="clock-ring-0" cx="170" cy="170" r="164" stroke="#A855F7" stroke-width="16" stroke-dasharray="1030.5" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" transform="rotate(-90 170 170)"/>
          </svg>
        </div>
        <!-- Timer 1: Pulsing Circle -->
        <div id="timer-style-1" style="width:340px; height:340px; border-radius:50%; background:transparent; border:20px dashed #1a1a1a; position:absolute; display:flex; align-items:center; justify-content:center; animation: spin 10s linear infinite;">
          <svg style="position:absolute; top:-20px; left:-20px; width:340px; height:340px; overflow:visible;">
            <circle id="clock-ring-1" cx="170" cy="170" r="164" stroke="#A855F7" stroke-width="20" stroke-dasharray="400 630" stroke-dashoffset="0" stroke-linecap="round" fill="transparent" transform="rotate(-90 170 170)"/>
          </svg>
        </div>
        <!-- Timer 2: Horizontal Top Bar -->
        <div id="timer-style-2" style="position:fixed; top:0; left:0; width:100%; height:40px; background:#111; z-index:999; display:none;">
          <div id="clock-ring-2" style="width:100%; height:100%; background:#A855F7;"></div>
        </div>
        <!-- Timer 3: Square Diamond -->
        <div id="timer-style-3" style="width:280px; height:280px; background:#0a0a0a; border:12px solid #1a1a1a; position:absolute; display:flex; align-items:center; justify-content:center; transform: rotate(45deg);">
          <div id="clock-ring-3" style="position:absolute; bottom:0; left:0; width:100%; height:100%; background:#A855F7; opacity:0.5;"></div>
        </div>

        <span style="font-size:30px;font-weight:700;color:#888;letter-spacing:4px;position:relative;z-index:2;margin-bottom:-10px; margin-top:-140px; display:none;">TIME</span>
        <span id="timer-num" style="position:absolute; font-size:110px; font-weight:900; color:#A855F7; font-family:monospace!important; z-index:2; line-height:1;">00:05</span>
      </div>
"""

# Replace the old timer
old_timer_regex = re.compile(r'<!-- Restored Clock Timer -->.*?</div>\s*</div>', re.DOTALL)
html = old_timer_regex.sub(timer_html, html)

# 4. In randomizeTheme, pick clockStyle
randomize_theme_patch = """
        window.clockThemeColor = clockColor;
        window.clockStyle = Math.floor(Math.random() * 4);
        
        // Hide all timers
        for(let i=0; i<4; i++) {
           let el = document.getElementById("timer-style-" + i);
           if(el) el.style.display = "none";
        }
        // Show selected timer
        let sel = document.getElementById("timer-style-" + window.clockStyle);
        if(sel) {
           sel.style.display = (window.clockStyle === 2) ? "block" : "flex";
        }
        if (window.clockStyle === 3) {
           document.getElementById("timer-num").style.color = "white"; // contrast
        } else {
           document.getElementById("timer-num").style.color = clockColor;
        }
        
        // Update clock colors
        for(let i=0; i<4; i++) {
            let cr = document.getElementById("clock-ring-" + i);
            if(cr) {
                if(i===0 || i===1) cr.style.stroke = clockColor;
                if(i===2 || i===3) cr.style.background = clockColor;
            }
        }
"""
html = html.replace("window.clockThemeColor = clockColor;", randomize_theme_patch)

# 5. Fix setQuizState to handle dynamic clock rings
set_quiz_state_patch = """
          // Handle dynamic clocks
          let offset = 0;
          if (phase === 'question') {
             timerNum.innerText = "00:05";
             progress = 0;
          } else if (phase === 'countdown') {
             const secs = Math.max(0, 5 - Math.floor(progress * 5));
             timerNum.innerText = "00:0" + secs;
             if (progress > 0.7) {
                timerNum.style.color = "#FF4444";
                for(let i=0; i<4; i++){
                    let cr = document.getElementById("clock-ring-"+i);
                    if(cr) {
                        if(i===0 || i===1) cr.style.stroke = "#FF4444";
                        if(i===2 || i===3) cr.style.background = "#FF4444";
                    }
                }
             } else {
                timerNum.style.color = (window.clockStyle===3) ? "white" : window.clockThemeColor;
                for(let i=0; i<4; i++){
                    let cr = document.getElementById("clock-ring-"+i);
                    if(cr) {
                        if(i===0 || i===1) cr.style.stroke = window.clockThemeColor;
                        if(i===2 || i===3) cr.style.background = window.clockThemeColor;
                    }
                }
             }
          } else if (phase === 'reveal' || phase === 'explanation') {
             timerNum.innerText = "00:00";
             progress = 1.0;
             for(let i=0; i<4; i++){
                 let cr = document.getElementById("clock-ring-"+i);
                 if(cr) {
                     if(i===0 || i===1) cr.style.stroke = "#FF4444";
                     if(i===2 || i===3) cr.style.background = "#FF4444";
                 }
             }
          }
          
          // Apply progress to clock
          const cr0 = document.getElementById("clock-ring-0");
          if(cr0) cr0.style.strokeDashoffset = progress * 1030.5;
          const cr1 = document.getElementById("clock-ring-1");
          if(cr1) cr1.style.strokeDashoffset = progress * 1030.5;
          const cr2 = document.getElementById("clock-ring-2");
          if(cr2) cr2.style.width = (100 - (progress*100)) + "%";
          const cr3 = document.getElementById("clock-ring-3");
          if(cr3) cr3.style.height = (100 - (progress*100)) + "%";
"""

old_clock_logic = re.compile(r'if \(phase === \'question\'\) \{.*?if \(clockRing\) \{ clockRing\.style\.strokeDashoffset = CIRC; clockRing\.style\.stroke = "#FF4444"; \}\s*\}', re.DOTALL)
html = old_clock_logic.sub(set_quiz_state_patch, html)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated successfully")
