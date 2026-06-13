import re

with open('templates/quiz_shorts_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Inject @keyframes for animations
keyframes = '''
    @keyframes borderDash { to { stroke-dashoffset: 1000; } }
    @keyframes pulseGlow { 0% { opacity: 0.5; box-shadow: 0 0 20px currentColor; } 50% { opacity: 1; box-shadow: 0 0 80px currentColor; } 100% { opacity: 0.5; box-shadow: 0 0 20px currentColor; } }
    @keyframes rotateHue { to { filter: hue-rotate(360deg); } }
'''
if '@keyframes borderDash' not in html:
    html = html.replace('</style>', keyframes + '\n  </style>')

# 2. Replace the old static decorations with fully ANIMATED ones
old_dec_logic = r'// Pick an advanced frame layout.*?decContainer\.innerHTML = frameHTML;'

new_dec_logic = '''
      // Pick an advanced ANIMATED frame layout
      const frameLayouts = [
          // 1: Animated Dashed Border (Cyberpunk)
          `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
            <rect x="60" y="60" width="2040" height="3720" stroke="${mainColor}" stroke-width="30" fill="none" stroke-dasharray="80 160" style="animation: borderDash 10s linear infinite;"/>
          </svg>`,
          
          // 2: Animated Moving Pillars (Neon)
          `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
            <line x1="80" y1="0" x2="80" y2="3840" stroke="${mainColor}" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite;" />
            <line x1="2080" y1="0" x2="2080" y2="3840" stroke="${mainColor}" stroke-width="40" stroke-dasharray="200 100" style="animation: borderDash 8s linear infinite reverse;" />
          </svg>`,
          
          // 3: Pulsing Glowing Frame (HUD)
          `<div style="position:absolute;top:60px;left:60px;right:60px;bottom:60px;border:12px solid ${mainColor}; color:${mainColor}; animation: pulseGlow 3s ease-in-out infinite;"></div>`,
          
          // 4: Color Shifting Borders
          `<div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:16px solid ${mainColor}; filter: hue-rotate(0deg); animation: rotateHue 8s linear infinite; box-shadow: inset 0 0 50px ${mainColor}, 0 0 50px ${mainColor};"></div>`,

          // 5: Minimalist Moving Dots
          `<svg width="2160" height="3840" style="position:absolute;top:0;left:0;">
            <rect x="50" y="50" width="2060" height="3740" stroke="${mainColor}" stroke-width="20" stroke-dasharray="20 40" fill="none" style="animation: borderDash 20s linear infinite;" />
          </svg>`
      ];
      
      const frameHTML = frameLayouts[Math.floor(Math.random() * frameLayouts.length)];
      decContainer.innerHTML = frameHTML;
'''

html = re.sub(old_dec_logic, new_dec_logic, html, flags=re.DOTALL)

with open('templates/quiz_shorts_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
