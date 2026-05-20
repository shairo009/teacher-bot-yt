import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = "sk-LsQ51RwzWpzDhqPoum8hHcZp4twSJrXL9pKOZeKHAEC1CNlUfLvvTacBJFKgqdng"
        self.base_url = "https://opencode.ai/zen"
        self.model_name = "minimax-m2.5-free"

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
        
        Your task is to EXPLAIN this math concept in Hinglish (Hindi in English script).
        Since this is a {level} level video, keep the tone appropriate.
        - If Basic: Use very simple examples, slow pace.
        - If Advanced: Use professional terms but explain them simply.
        
        Return the response in valid JSON format:
        {{
            "screen_bullet_points": [
                "Point 1 (max 5 words)",
                "Point 2 (max 5 words)",
                "Point 3 (max 5 words)"
            ],
            "narration_script": "Engaging Hinglish script for a YouTube Short. Start with a hook, explain the concept, and end with a call to action."
        }}
        
        Maximum 6 bullet points. Narration script should be around 40-60 seconds when spoken (approx 100-120 words).
        """
        
        system_prompt = "You are a friendly, engaging primary school teacher. Output strictly JSON."
        
        data = {
            "model": self.model_name,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": system_prompt
        }
        
        print(f"    🧠 Thinking (AI reading the book...)")
        
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
        """Fallback to raw text if AI fails."""
        words = raw_text.split()
        lines = []
        current = []
        for w in words[:30]:
            current.append(w)
            if len(current) >= 5:
                lines.append(" ".join(current))
                current = []
        if current: lines.append(" ".join(current))
        
        return {
            "screen_bullet_points": lines[:5],
            "narration_script": raw_text[:500]
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
            if "screen_bullet_points" in data and "narration_script" in data:
                return data
        except Exception as e:
            print(f"    ⚠️ Failed to parse AI JSON: {e}")
        
        return self._fallback_response(raw_text)
