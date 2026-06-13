
    const correctIdx = 0;
    const CIRC = 1030.5; // Calculated for r=164

    function runAutoFit() {
      // 1) Find the best size for question
      let qEl = document.getElementById('question-text');
      let sz = 110; // default size
      qEl.style.fontSize = sz + "px";
      while (qEl.scrollHeight > 800 && sz > 60) {
        sz -= 4;
        qEl.style.fontSize = sz + "px";
      }

      // 2) Find the best size for options
      let optSz = sz;
      for (let i = 0; i < 4; i++) {
        let optEl = document.getElementById(`opt-text-${i}`);
        if(optEl) {
          optEl.style.fontSize = optSz + "px";
          while (optEl.scrollHeight > 220 && optSz > 60) {
            optSz -= 4;
            optEl.style.fontSize = optSz + "px";
          }
        }
      }

      // 3) Apply the SMALLEST size to ALL (Question + Options) so they share the SAME font size
      let finalSz = Math.min(sz, optSz);
      qEl.style.fontSize = finalSz + "px";
      for (let i = 0; i < 4; i++) {
        let optEl = document.getElementById(`opt-text-${i}`);
        if(optEl) optEl.style.fontSize = finalSz + "px";
      }
      
      // Do the same for Explain page
      const pgQuiz = document.getElementById("page-quiz");
      const pgExp = document.getElementById("page-explain");
      const oldQuizD = pgQuiz.style.display;
      const oldExpD = pgExp.style.display;
      pgQuiz.style.display = "none";
      pgExp.style.display = "flex";

      let expQEl = document.getElementById('question-text-exp');
      let expSz = 100;
      expQEl.style.fontSize = expSz + "px";
      while (expQEl.scrollHeight > 600 && expSz > 60) {
        expSz -= 4;
        expQEl.style.fontSize = expSz + "px";
      }
      // Apply to explain question and options
      expQEl.style.fontSize = expSz + "px";
      for (let i = 0; i < 4; i++) {
        let expOptEl = document.getElementById(`exp-text-${i}`);
        if(expOptEl) expOptEl.style.fontSize = expSz + "px";
      }
      
      pgQuiz.style.display = oldQuizD;
      pgExp.style.display = oldExpD;
    }

    // Randomize visual theme
    function randomizeTheme() {
      const colors = ["#39FF14", "#FF00FF", "#00FFFF", "#FFEA00", "#FF007F", "#00FF00", "#7DF9FF", "#FF4500", "#B366FF", "#FF355E", "#FFAA00", "#00FA9A"];
      const mainColor = colors[Math.floor(Math.random() * colors.length)];
      let clockColor = colors[Math.floor(Math.random() * colors.length)];
      while(clockColor === mainColor) clockColor = colors[Math.floor(Math.random() * colors.length)];
      
      window.themeColor = mainColor;
      // Remove old backgrounds
      document.getElementById('chapter-text').style.color = mainColor;
      document.getElementById('chapter-text-exp').style.color = mainColor;

      // 200+ VIDEO FRAME / BORDER DECORATIONS
      const decContainer = document.getElementById('decorations');
      decContainer.innerHTML = ''; // clear

      // Pick an advanced frame layout
      const frameLayouts = [
          "hud_corners", 
          "neon_pillars", 
          "cyberpunk_frame", 
          "minimalist_dots", 
          "thick_cinematic", 
          "geometric_bars"
      ];
      const layout = frameLayouts[Math.floor(Math.random() * frameLayouts.length)];
      
      let frameHTML = '';
      
      if (layout === "hud_corners") {
         // High-tech HUD style corner brackets
         const s = `position:absolute;width:150px;height:150px;`;
         const stroke = `8px solid ${mainColor}`;
         frameHTML = `
           <div style="${s}top:80px;left:80px;border-top:${stroke};border-left:${stroke};box-shadow:inset 20px 20px 40px -20px ${mainColor};">
               <div style="position:absolute;top:10px;left:10px;width:30px;height:30px;background:${mainColor};"></div>
           </div>
           <div style="${s}top:80px;right:80px;border-top:${stroke};border-right:${stroke};box-shadow:inset -20px 20px 40px -20px ${mainColor};">
               <div style="position:absolute;top:10px;right:10px;width:30px;height:30px;background:${mainColor};"></div>
           </div>
           <div style="${s}bottom:80px;left:80px;border-bottom:${stroke};border-left:${stroke};box-shadow:inset 20px -20px 40px -20px ${mainColor};">
               <div style="position:absolute;bottom:10px;left:10px;width:30px;height:30px;background:${mainColor};"></div>
           </div>
           <div style="${s}bottom:80px;right:80px;border-bottom:${stroke};border-right:${stroke};box-shadow:inset -20px -20px 40px -20px ${mainColor};">
               <div style="position:absolute;bottom:10px;right:10px;width:30px;height:30px;background:${mainColor};"></div>
           </div>
         `;
      } else if (layout === "neon_pillars") {
         // Glowing pillars on left and right
         const glow = `box-shadow: 0 0 50px ${mainColor}, 0 0 100px ${mainColor};`;
         frameHTML = `
           <div style="position:absolute;top:0;left:0;width:30px;height:100%;background:${mainColor};${glow}"></div>
           <div style="position:absolute;top:0;right:0;width:30px;height:100%;background:${mainColor};${glow}"></div>
           <div style="position:absolute;top:20%;left:50px;width:4px;height:60%;background:${mainColor};opacity:0.5;"></div>
           <div style="position:absolute;top:20%;right:50px;width:4px;height:60%;background:${mainColor};opacity:0.5;"></div>
         `;
      } else if (layout === "cyberpunk_frame") {
         // Complex frame with angles (using clip-path)
         const cpColor = mainColor;
         frameHTML = `
           <div style="position:absolute;top:30px;left:30px;right:30px;bottom:30px;border:10px solid ${cpColor};opacity:0.3;"></div>
           <div style="position:absolute;top:0;left:10%;width:80%;height:40px;background:${cpColor};clip-path:polygon(5% 0, 95% 0, 100% 100%, 0% 100%);"></div>
           <div style="position:absolute;bottom:0;left:10%;width:80%;height:40px;background:${cpColor};clip-path:polygon(0% 0, 100% 0, 95% 100%, 5% 100%);"></div>
           <div style="position:absolute;top:40%;left:0;width:20px;height:20%;background:${cpColor};"></div>
           <div style="position:absolute;top:40%;right:0;width:20px;height:20%;background:${cpColor};"></div>
         `;
      } else if (layout === "minimalist_dots") {
         // Premium dotted grid along the edges
         const dotPattern = `radial-gradient(${mainColor} 4px, transparent 4px)`;
         frameHTML = `
           <div style="position:absolute;top:40px;left:40px;right:40px;height:60px;background-image:${dotPattern};background-size:20px 20px;"></div>
           <div style="position:absolute;bottom:40px;left:40px;right:40px;height:60px;background-image:${dotPattern};background-size:20px 20px;"></div>
           <div style="position:absolute;top:100px;bottom:100px;left:40px;width:60px;background-image:${dotPattern};background-size:20px 20px;"></div>
           <div style="position:absolute;top:100px;bottom:100px;right:40px;width:60px;background-image:${dotPattern};background-size:20px 20px;"></div>
         `;
      } else if (layout === "thick_cinematic") {
         // Top/Bottom cinematic bars with glowing inner line
         frameHTML = `
           <div style="position:absolute;top:0;left:0;right:0;height:80px;background:#111;border-bottom:8px solid ${mainColor};box-shadow:0 10px 40px ${mainColor};"></div>
           <div style="position:absolute;bottom:0;left:0;right:0;height:80px;background:#111;border-top:8px solid ${mainColor};box-shadow:0 -10px 40px ${mainColor};"></div>
         `;
      } else if (layout === "geometric_bars") {
         // Repeating diagonal stripes on the edges
         const stripe = `repeating-linear-gradient(45deg, transparent, transparent 20px, ${mainColor} 20px, ${mainColor} 40px)`;
         frameHTML = `
           <div style="position:absolute;top:40px;left:40px;width:40px;bottom:40px;background-image:${stripe};opacity:0.6;border-radius:20px;"></div>
           <div style="position:absolute;top:40px;right:40px;width:40px;bottom:40px;background-image:${stripe};opacity:0.6;border-radius:20px;"></div>
           <div style="position:absolute;top:50%;left:0;width:120px;height:10px;background:${mainColor};box-shadow:0 0 20px ${mainColor};"></div>
           <div style="position:absolute;top:50%;right:0;width:120px;height:10px;background:${mainColor};box-shadow:0 0 20px ${mainColor};"></div>
         `;
      }
      
      decContainer.innerHTML = frameHTML;

      // 200+ Combinations Generator for Borders (Style x Width x BoxShadow x Side Selector)
      const borderStyles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"];
      const bStyle = borderStyles[Math.floor(Math.random() * borderStyles.length)];
      const bWidth = Math.floor(Math.random() * 16) + 6; // 6px to 21px
      
      const shadows = [
        `0 0 50px ${mainColor}, inset 0 0 50px ${mainColor}`, // Super Glow
        `0 0 30px ${mainColor}`, // Outer Glow
        `inset 0 0 40px ${mainColor}`, // Inner Glow
        `10px 10px 0px ${mainColor}`, // Retro offset shadow
        `-10px 10px 0px ${mainColor}, 10px -10px 0px ${mainColor}`, // Dual offset
        `none` // No shadow
      ];
      const bShadow = shadows[Math.floor(Math.random() * shadows.length)];
      
      const selectors = [
        "all", "leftRight", "topBottom", "leftThick", "bottomThick"
      ];
      const selector = selectors[Math.floor(Math.random() * selectors.length)];
      
      window.dynamicBorderStyle = {
        style: bStyle,
        width: bWidth,
        shadow: bShadow,
        selector: selector
      };

      

    } // Run autofit and randomize on load
    window.addEventListener('load', () => {
      randomizeTheme();
      runAutoFit();
    });

    window.setQuizState = function(phase, progress, timings) {
      const timerNum = document.getElementById("timer-num");
      const clockRing = document.getElementById("clock-ring");

      if (phase === 'question' || phase === 'countdown' || phase === 'reveal') {
        document.getElementById("page-quiz").style.display = "flex";
        document.getElementById("page-explain").style.display = "none";

        for (let i = 0; i < 4; i++) {
          const card = document.getElementById(`opt-${i}`);
          card.classList.remove("correct", "wrong");
          card.style.opacity = "1";
          card.style.border = "8px solid transparent";
          card.style.background = "transparent";
          card.style.boxShadow = "none";
        }

        if (phase === 'question') {
          timerNum.innerText = "00:05";
          
            if (clockRing) { clockRing.style.strokeDashoffset = "0"; clockRing.style.stroke = window.clockThemeColor; }
            const clockBar = document.getElementById("clock-bar");
            if(clockBar) { clockBar.style.width = "100%"; clockBar.style.background = window.clockThemeColor; }
            const clockFill = document.getElementById("clock-fill");
            if(clockFill) { clockFill.style.height = "100%"; clockFill.style.background = window.clockThemeColor; }

        }
        else if (phase === 'countdown') {
          
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

          const secs = Math.max(0, 5 - Math.floor(progress * 5));
          timerNum.innerText = "00:0" + secs;
          if (progress > 0.7) {
            timerNum.style.color = "#FF4444";
            
              if (clockRing) clockRing.style.stroke = "#FF4444";
              const clockBar = document.getElementById("clock-bar");
              if(clockBar) clockBar.style.background = "#FF4444";
              const clockFill = document.getElementById("clock-fill");
              if(clockFill) clockFill.style.background = "#FF4444";

          } else {
            timerNum.style.color = window.clockThemeColor;
            
              if (clockRing) clockRing.style.stroke = window.clockThemeColor;
              const clockBar = document.getElementById("clock-bar");
              if(clockBar) clockBar.style.background = window.clockThemeColor;
              const clockFill = document.getElementById("clock-fill");
              if(clockFill) clockFill.style.background = window.clockThemeColor;

          }
        }
        else if (phase === 'reveal') {
          for (let i = 0; i < 4; i++) {
            const card = document.getElementById(`opt-${i}`);
            if (i === correctIdx) {
              card.style.background = "transparent";
              card.style.border = "8px solid transparent";
              
              const d = window.dynamicBorderStyle;
              card.style.boxShadow = d.shadow;
              
              if(d.selector === "all") {
                  card.style.border = `${d.width}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "leftRight") {
                  card.style.borderLeft = `${d.width * 2}px ${d.style} ${window.themeColor}`;
                  card.style.borderRight = `${d.width * 2}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "topBottom") {
                  card.style.borderTop = `${d.width * 1.5}px ${d.style} ${window.themeColor}`;
                  card.style.borderBottom = `${d.width * 1.5}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "leftThick") {
                  card.style.borderLeft = `${d.width * 3}px solid ${window.themeColor}`;
              } else if (d.selector === "bottomThick") {
                  card.style.borderBottom = `${d.width * 2}px solid ${window.themeColor}`;
              }

            } else {
              card.style.opacity = "0.35";
            }
          }
          timerNum.innerText = "00:00";
          
            if (clockRing) { 
                const totalLen = parseFloat(clockRing.getAttribute("stroke-dasharray") || CIRC);
                clockRing.style.strokeDashoffset = totalLen; 
                clockRing.style.stroke = "#FF4444"; 
            }
            const clockBar = document.getElementById("clock-bar");
            if(clockBar) { clockBar.style.width = "0%"; clockBar.style.background = "#FF4444"; }
            const clockFill = document.getElementById("clock-fill");
            if(clockFill) { clockFill.style.height = "0%"; clockFill.style.background = "#FF4444"; }

        }
      }
      else if (phase.startsWith('explain')) {
        document.getElementById("page-quiz").style.display = "none";
        document.getElementById("page-explain").style.display = "flex";
        let activeIdx = parseInt(phase.replace('explain', ''));
        for (let i = 0; i < 4; i++) {
          const card = document.getElementById(`exp-card-${i}`);
          if (i <= activeIdx) {
            card.style.opacity = "1";
            if (i === correctIdx) {
              card.style.background = "transparent";
              card.style.border = "8px solid transparent";
              
              const d = window.dynamicBorderStyle;
              card.style.boxShadow = d.shadow;
              
              if(d.selector === "all") {
                  card.style.border = `${d.width}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "leftRight") {
                  card.style.borderLeft = `${d.width * 2}px ${d.style} ${window.themeColor}`;
                  card.style.borderRight = `${d.width * 2}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "topBottom") {
                  card.style.borderTop = `${d.width * 1.5}px ${d.style} ${window.themeColor}`;
                  card.style.borderBottom = `${d.width * 1.5}px ${d.style} ${window.themeColor}`;
              } else if (d.selector === "leftThick") {
                  card.style.borderLeft = `${d.width * 3}px solid ${window.themeColor}`;
              } else if (d.selector === "bottomThick") {
                  card.style.borderBottom = `${d.width * 2}px solid ${window.themeColor}`;
              }
            } else if (i < activeIdx) {
              card.style.opacity = "0.4";
            }
          } else {
            card.style.opacity = "0";
          }
        }
      }
    };

    window.setQuizState('question', 0, null);
  