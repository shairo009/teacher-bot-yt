import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY") or "sk-LsQ51RwzWpzDhqPoum8hHcZp4twSJrXL9pKOZeKHAEC1CNlUfLvvTacBJFKgqdng"
        self.base_url = base_url or os.environ.get("OPENCODE_BASE_URL") or "https://opencode.ai/zen"
        self.model_name = os.environ.get("OPENCODE_MODEL_NAME") or "minimax-m2.5-free"

    def explain_topic(self, raw_text, class_num=1):
        """Read raw textbook text and generate a teaching script."""
        if not self.api_key:
            print("⚠️ OPENCODE_API_KEY not found. Using fallback text directly.")
            return self._fallback_response(raw_text)

        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        level = "Basic" # Default
        if isinstance(raw_text, dict) and 'level' in raw_text:
            level = raw_text['level']
            raw_text = raw_text['topic']

        prompt = f"""
        Topic: {raw_text}
        Level: {level} (Class {class_num})
        
        Your task is to mathematically analyze the topic and formulate a real, mathematically precise key mathematical formula, relation, equation, or inequality representing the topic.
        Even for very fundamental/simple/NCERT concepts (like "Inside/Outside", "Big/Small", "Long/Short", "Counting", "Shapes"), you MUST formulate an elegant mathematical relation or equation.
        
        Format requirements:
        1. Extract the most fundamental formula/equation/inequality.
        2. Assign a neat math title for it.
        3. Classify it into one of the following 3D visualization math types:
           "sphere_3d", "cone_3d", "cylinder_3d", "torus_3d", "spiral_3d", "parametric_surface", "axes_3d"
        4. Break down this mathematical formula into exactly 3 progressive visual steps:
           - Step 1: The first mathematical component/variable (e.g., "x²" or "L₁" or "7").
           - Step 2: The second mathematical component/variable (e.g., "y²" or "L₂" or "5").
           - Step 3 (The Assembly): The complete mathematical relation (e.g., "x² + y² < r²" or "L₁ > L₂" or "7 + 5 = 12").
        5. Write an extremely engaging narrator script split into 5 parts, in Hinglish (Hindi written in English alphabets) explaining the mathematical concept of this formula.
           CRITICAL: The script MUST explain both the real mathematical logic of the formula AND explicitly guide the student through the step-by-step progressive assembly of the 3D rotating graph on the screen!
           - Keep each part short, highly pedagogical, and simple yet mathematically precise.

        Return the response strictly in valid JSON format:
        {{
            "formula_title": "A neat mathematical title",
            "formula_text": "A beautiful clean Unicode/text formula (e.g. x² + y² < r²)",
            "math_type": "one of: sphere_3d, cone_3d, cylinder_3d, torus_3d, spiral_3d, parametric_surface, axes_3d",
            "step1_symbol": "x²",
            "step1_desc": "X-Coordinate boundary limit",
            "step2_symbol": "y²",
            "step2_desc": "Y-Coordinate boundary limit",
            "step3_symbol": "x² + y² < r²",
            "step3_desc": "Spherical Inside inequality",
            "intro_script": "Engaging welcome introducing the formula title in Hinglish. e.g. Namaste pyaare dosto! Aaj hum seekhenge unit boundary circle equations ko 3D perspective se.",
            "step1_script": "Engaging explanation of Step 1 and its symbol in Hinglish. e.g. Sabse pehle Step 1 me screen par horizontal pink vector x-square ko dekhiye jo base boundary coordinates ko represent karta hai.",
            "step2_script": "Engaging explanation of Step 2 and its symbol in Hinglish. e.g. Ab Step 2 me screen par sunehra vertical vector y-square add kijiye jo perpendicular side ko represent karta hai.",
            "step3_script": "Engaging explanation of Step 3 and the final assembly in Hinglish. e.g. Aur ab aati hai magical assembly! Jab hum in dono parameters ko plus karte hain, toh ye merge hokar absolute rotating pink 3D Sphere me transform ho jaate hain!",
            "outro_script": "Engaging outro wrapping up in Hinglish. e.g. Aise hi visual ways se study karne ke liye, channel ko subscribe aur video ko like zaroor karein. Milenge agle lesson me, dhanyawad!"
        }}
        """
        
        system_prompt = "You are a professional, high-concept mathematics professor. Output strictly JSON."
        
        data = {
            "model": self.model_name,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": system_prompt
        }
        
        print(f"    🧠 Thinking (AI formulating 3D Math Equation with Split Scripts...)")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                content = ""
                for block in result.get("content", []):
                    if block.get("type") == "text":
                        content = block.get("text", "").strip()
                        break
                
                return self.parse_and_clean(content, raw_text)
            else:
                print(f"    ❌ AI Error: {response.status_code} - {response.text}")
                return self._fallback_response(raw_text)
        except Exception as e:
            print(f"    ❌ AI Exception: {e}")
            return self._fallback_response(raw_text)

    def _fallback_response(self, raw_text):
        """Fallback to raw text if AI fails. Cleans garbage metadata, indd tags, dates, and print specs."""
        import re
        
        # 1. Clean garbage metadata and NCERT layout specs
        clean_text = raw_text
        clean_text = re.sub(r'(?i)reprint\s+\d{4}-\d{2,4}', '', clean_text)
        clean_text = re.sub(r'(?i)class\s+\d+\s+math\s+hindi.*', '', clean_text)
        clean_text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}.*?(AM|PM)', '', clean_text)
        clean_text = re.sub(r'\d{1,2}\s+december\s+\d{4}.*?second', '', clean_text)
        clean_text = re.sub(r'\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}', '', clean_text)
        clean_text = re.sub(r'(?i)\w+\.indd\s+\d+', '', clean_text)
        clean_text = re.sub(r'\b[a-zA-Z\d_/\\\-]{5,}\.indd\b', '', clean_text)
        
        # Remove broken character sequences and numbers
        clean_text = re.sub(r'\b\d{4,}\b', '', clean_text)
        
        # Normalize broken spaces in Hindi text
        clean_text = clean_text.replace('सखं ्‍याओ ं', 'संख्याओं').replace('सयाथ', 'साथ')
        clean_text = clean_text.replace('िंतरे', 'संतरे')
        clean_text = clean_text.replace('सिब्बों', 'डिब्बों').replace('सिब्बे', 'डिब्बे')
        clean_text = clean_text.replace('प्रत्ेक', 'प्रत्येक').replace('गदें', 'गेंद')
        clean_text = clean_text.replace('ियाहर', 'बाहर').replace('िो्गें', 'बोलेंगे')
        clean_text = clean_text.replace('िच्च', 'बच्च').replace('्गयाआइए', 'लगाआइए')
        clean_text = clean_text.replace('िबड़्य', 'चिड़िया').replace('बनयाआइए', 'बनाइए')
        
        # Determine fallback formula and title based on content keywords
        title = "Math Coordinate Formula"
        formula = "x² + y² = r²"
        math_type = "sphere_3d"
        text_lower = clean_text.lower()
        
        step1_symbol = "x²"
        step1_desc = "First Boundary Variable"
        step2_symbol = "y²"
        step2_desc = "Second Boundary Variable"
        step3_symbol = "x² + y² = r²"
        step3_desc = "Total Boundary Assembled"
        
        is_chapter8 = any(x in text_lower for x in ["ahjm108", "ch 8.indd", "सयाथ खेल", "संतरे", "सिब्बों", "21 से 30", "31 से 50"])
        is_length = any(x in text_lower for x in ["lamba", "long", "lambai", "लंबा", "लंबाई", "लम्बा", "लम्बाई", "नाप", "माप", "नापने", "मापने", "भारी", "हल्की", "हलकी"])
        is_inside_outside = any(x in text_lower for x in ["inside", "outside", "andar", "bahar", "अंदर", "बाहर", "अदं र"])
        is_gol = any(x in text_lower for x in ["gol", "circle", "round", "गोल", "वृत्त", "गोला"])
        is_count = any(x in text_lower for x in ["number", "sankhya", "count", "tamatar", "gajar", "sankhy", "संख्या", "गिन", "गिनती", "जोड़", "जोध", "खेती", "सब्जी", "जोड़ने"])

        if is_chapter8:
            title = "Place Value Coordinate System"
            formula = "N = 10 * T + U"
            math_type = "spiral_3d"
            step1_symbol = "10 * T"
            step1_desc = "Tens Group (Dahai)"
            step2_symbol = "U"
            step2_desc = "Units (Ikai)"
            step3_symbol = "20 + 2 = 22"
            step3_desc = "Complete Number (22 Santare)"
            
            intro_script = "Namaste pyaare dosto! Aaj hum seekhenge Place Value coordinate system ko dynamic 3D spiral model se."
            step1_script = "Sabse pehle Step 1 me, screen par is vertical pink curve ten times T ko dekhiye jo dahai ke groups ko represent karta hai."
            step2_script = "Ab Step 2 me, isme hum bachi hui single quantity ikai 'U' ko add karte hain, screen par sunehre segment ko dekhiye."
            step3_script = "Aur ab aati hai final magic assembly! Jab hum in dono ko mathematically jodh dete hain, toh ye merge hokar is rotating purple 3D Spiral Helix me transform ho jaate hain!"
            outro_script = "Geometry ke sath counting ko samajhna hai na behad aasan! Aise hi seekhte rahiye, dhanyawad!"
        elif is_length:
            title = "Linear Dimension Relation"
            formula = "L₁ > L₂"
            math_type = "cylinder_3d"
            step1_symbol = "L₁"
            step1_desc = "Length Coordinate"
            step2_symbol = "L₂"
            step2_desc = "Radius Coordinate"
            step3_symbol = "L₁ > L₂"
            step3_desc = "Linear inequality relation"
            
            intro_script = "Namaste pyaare dosto! Aaj hum seekhenge length aur size ke concept ko dynamic 3D cylinder mesh ki madad se."
            step1_script = "Step 1 me screen par vertical pink line L-one parameter ko dekhiye jo linear length ko represent karti hai."
            step2_script = "Step 2 me, chaliye isme sunehra horizontal radius L-two component add karte hain jo width ko dikhata hai."
            step3_script = "Aur ab aati hai assembly! Jab hum in dono vectors ko compare karte hain, toh ye merge hokar is elegant rotating 3D Cylinder me transform ho jaate hain!"
            outro_script = "Dosto, visual geometry seekhte rahiye aur channel ko subscribe karna na bhoolein. Thank you!"
        elif is_inside_outside:
            title = "Boundary Circle Relation"
            formula = "x² + y² < r²"
            math_type = "sphere_3d"
            step1_symbol = "r"
            step1_desc = "Radius Boundary"
            step2_symbol = "d"
            step2_desc = "Point Distance"
            step3_symbol = "d < r"
            step3_desc = "Inside area inequality"
            
            intro_script = "Namaste dosto! Chaliye andar aur bahar ke boundary rule ko absolute step-by-step 3D geometry se samajhte hain."
            step1_script = "Step 1 me, screen par hum is radius limit r vector line ko plot kar rahe hain jo hamara geometric bounds hai."
            step2_script = "Step 2 me, is point distance d vector arrow line को dekhiye jo center se distance represent karta hai."
            step3_script = "Aur ab final assembly! Jab hum distance coordinate ko filter karte hain, toh screen par dynamic pink 3D Sphere emerge ho jata hai jo inside points coordinates ko prove karta hai!"
            outro_script = "Math presentation seekhne ke liye hamare sath bane rahiye. Dhanyawad!"
        elif is_gol:
            title = "Spherical Equation"
            formula = "x² + y² + z² = r²"
            math_type = "sphere_3d"
            step1_symbol = "x² + y²"
            step1_desc = "Planar coordinates"
            step2_symbol = "z²"
            step2_desc = "Depth coordinate"
            step3_symbol = "x² + y² + z² = r²"
            step3_desc = "Full Spherical boundary"
            
            intro_script = "Namaste dosto! Chaliye spherical space ko ekdam simple parts me break karke aur detail me samajhte hain."
            step1_script = "Sabse pehle Step 1 me screen par planar flat circle x-square plus y-square vector coordinate boundary ko dekhiye."
            step2_script = "Ab Step 2 me, vertical z-square depth coordinate height component ko dekhiye."
            step3_script = "Aur ab iski final assembly! Jab hum in dono components ko jodte hain, toh complete formula x-square plus y-square plus z-square equals r-square ke sath rotating 3D Sphere create ho jata hai!"
            outro_script = "Aise hi premium animations ke sath seekhne ke liye, subscribe zaroor karein. Thank you!"
        elif is_count:
            title = "Jod Ka Niyam (Addition Formula)"
            formula = "7 + 5 = 12"
            math_type = "cylinder_3d"
            step1_symbol = "7"
            step1_desc = "Pehla Group (7 Pink Ticks)"
            step2_symbol = "5"
            step2_desc = "Dusra Group (5 Gold Ticks)"
            step3_symbol = "7 + 5 = 12"
            step3_desc = "Dono ka Jod (Cylinder formed with 12)"
            
            intro_script = "Namaste pyaare dosto! Aaj hum addition yaani jod ke concept ko ekdum detailed aur visual tareeqe se samjhenge."
            step1_script = "Step 1 me screen par vertical pink line ko dekhiye. Ye line hamare pehle group yaani 7 items ko represent karti hai aur perfectly count hoti hai."
            step2_script = "Ab Step 2 me, chaliye isme sunehra base circle add karte hain jiska radius vector theek 5 units ka hai jo dusri quantity ko dikhata hai."
            step3_script = "Aur ab aati hai final magic assembly! Jaise hi hum mathematically 7 aur 5 ko add karte hain, toh ye vectors merge hokar is gorgeous rotating 3D Cylinder me transform ho jaate hain jiski height total sum 12 ko perfectly prove karti hai!"
            outro_script = "Dekha aapne math kitna visible aur aasan hai! Agle lesson me phir milenge, tab tak ke liye bye bye!"
        else:
            title = "Math Coordinate Formula"
            formula = "x² + y² = r²"
            math_type = "sphere_3d"
            
            intro_script = f"Namaste dosto! Chaliye is mathematical equation {formula} ko ekdum fundamental level se samajhte hain."
            step1_script = "Step 1 me, screen par hum is pink vector coordinate limit ko represent karte hain."
            step2_script = "Ab Step 2 me, sunehre vertical height vector coordinate ko scale coordinate axis par add karte hain."
            step3_script = "Aur ab dynamic assembly! In dono components ke coordination bounds se hamara elegant rotating pink 3D Sphere mesh ban jata hai!"
            outro_script = "Practice karte rahiye aur presentation model seekhte rahiye. Dhanyawad!"
            
        full_script = f"{intro_script} {step1_script} {step2_script} {step3_script} {outro_script}"
        
        return {
            "formula_title": title,
            "formula_text": formula,
            "math_type": math_type,
            "step1_symbol": step1_symbol,
            "step1_desc": step1_desc,
            "step2_symbol": step2_symbol,
            "step2_desc": step2_desc,
            "step3_symbol": step3_symbol,
            "step3_desc": step3_desc,
            "intro_script": intro_script,
            "step1_script": step1_script,
            "step2_script": step2_script,
            "step3_script": step3_script,
            "outro_script": outro_script,
            "screen_bullet_points": [title, formula],
            "narration_script": full_script
        }

    def parse_and_clean(self, content, raw_text):
        import re
        def clean_json_string(s):
            s = re.sub(r'<thinking>.*?</thinking>', '', s, flags=re.DOTALL)
            start = s.find('{')
            end = s.rfind('}')
            if start != -1 and end != -1:
                s = s[start:end+1]
            return s

        content = clean_json_string(content)
        try:
            data = json.loads(content)
            # Normalize and set fallbacks if some keys are missing
            if "formula_title" not in data:
                data["formula_title"] = "Mathematical Model"
            if "formula_text" not in data:
                data["formula_text"] = "y = f(x)"
            if "math_type" not in data:
                data["math_type"] = "axes_3d"
            if "step1_symbol" not in data:
                data["step1_symbol"] = "x"
            if "step1_desc" not in data:
                data["step1_desc"] = "Variable X"
            if "step2_symbol" not in data:
                data["step2_symbol"] = "y"
            if "step2_desc" not in data:
                data["step2_desc"] = "Variable Y"
            if "step3_symbol" not in data:
                data["step3_symbol"] = data["formula_text"]
            if "step3_desc" not in data:
                data["step3_desc"] = "Complete Equation Model"
            
            # Setup split scripts from single narration script if not explicitly returned
            if "intro_script" not in data or "step1_script" not in data:
                script = data.get("narration_script", "Welcome to the class! Here is our math model.")
                sentences = [s.strip() for s in script.split('.') if s.strip()]
                
                # Split sentences intelligently
                data["intro_script"] = sentences[0] + "." if len(sentences) > 0 else "Welcome."
                data["step1_script"] = sentences[1] + "." if len(sentences) > 1 else "Step one model."
                data["step2_script"] = sentences[2] + "." if len(sentences) > 2 else "Step two model."
                
                step3_sentences = sentences[3:-1] if len(sentences) > 4 else sentences[3:]
                data["step3_script"] = " ".join(step3_sentences) + "." if step3_sentences else "Step three model."
                
                data["outro_script"] = sentences[-1] + "." if len(sentences) > 4 else "Thank you!"
            
            # Ensure narration_script is populated
            if "narration_script" not in data:
                data["narration_script"] = f"{data['intro_script']} {data['step1_script']} {data['step2_script']} {data['step3_script']} {data['outro_script']}"
            
            # Keep bullet points compatible
            data["screen_bullet_points"] = [data["formula_title"], data["formula_text"]]
            return data
        except Exception as e:
            print(f"    ⚠️ Failed to parse AI JSON: {e}")
        
        return self._fallback_response(raw_text)
