import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path("C:/Users/1001s/teacher-bot-temp")
load_dotenv(PROJECT_ROOT / ".env", override=True)

api_key = os.environ.get('OPENAI_API_KEY', '')
base_url = os.environ.get('OPENAI_BASE_URL', 'https://opengateway.gitlawb.com/v1')
model = os.environ.get('OPENAI_MODEL', 'mimo-v2.5-free')

def call_llm(prompt):
    messages = [
        {"role": "system", "content": "You are a specialized content creator for GK education channels. Your task is to output clean, valid JSON only. Do not wrap it in markdown codeblocks."},
        {"role": "user", "content": prompt}
    ]
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 15000
        },
        timeout=300
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    
    # Strip markdown block formatting if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

def main():
    print("Generating Lucent GK Polity Questions...")
    prompt = """
Generate exactly 5 high-quality multiple choice questions based on 'Indian Polity & Constitution' section of Lucent's General Knowledge book.
The questions should cover chapters: 
1. Making of the Constitution (संविधान का निर्माण)
2. Preamble (प्रस्तावना)
3. Salient Features of the Constitution (संविधान की विशेषताएं)
4. Sources of the Constitution (संविधान के स्रोत)

For each question, output a JSON object with the following fields:
- id: unique integer starting from 1
- subject: "INDIAN POLITY (भारतीय राजव्यवस्था)"
- chapter: e.g. "CHAPTER 1: MAKING OF THE CONSTITUTION"
- topic: e.g. "CONSTITUENT ASSEMBLY (संविधान सभा)"
- question_hi: Question in Hindi
- question_en: Question in English
- opt0_hi: Option A in Hindi
- opt0_en: Option A in English
- opt1_hi: Option B in Hindi
- opt1_en: Option B in English
- opt2_hi: Option C in Hindi
- opt2_en: Option C in English
- opt3_hi: Option D in Hindi
- opt3_en: Option D in English
- correct_idx: index of correct option (0=A, 1=B, 2=C, 3=D)
- exp0: Explanation paragraph for Option A in Hindi (short, max 2 lines, informative)
- exp1: Explanation paragraph for Option B in Hindi (short, max 2 lines, informative)
- exp2: Explanation paragraph for Option C in Hindi (short, max 2 lines, informative)
- exp3: Explanation paragraph for Option D in Hindi (short, max 2 lines, informative)
- narration: A dictionary containing Hindi voiceover texts:
  - q_intro: "क्या आप जानते हैं"
  - q_question: e.g. "संविधान सभा की प्रथम बैठक कब हुई थी? आपके विकल्प हैं:" (always end with "आपके विकल्प हैं:")
  - opt0: e.g. "ए, 9 दिसंबर 1946,"
  - opt1: e.g. "बी, 11 दिसंबर 1946,"
  - opt2: e.g. "सी, 15 अगस्त 1947,"
  - opt3: e.g. "या डी, 26 जनवरी 1950।" (always start option D with "या डी,")
  - q_outro: "समय शुरू होता है अब!"
  - r_narration: e.g. "समय समाप्त! सही जवाब है विकल्प ए।"
  - e0_narration: Hindi voiceover for Option A explanation (very concise, 1 sentence, natural speech)
  - e1_narration: Hindi voiceover for Option B explanation (very concise, 1 sentence, natural speech)
  - e2_narration: Hindi voiceover for Option C explanation (very concise, 1 sentence, natural speech)
  - e3_narration: Hindi voiceover for Option D explanation (very concise, 1 sentence, natural speech)

Output a raw JSON array of these 5 objects. Ensure valid JSON without comments or extra text.
"""
    
    try:
        json_str = call_llm(prompt)
        # Verify JSON validity
        questions = json.loads(json_str)
        
        output_dir = PROJECT_ROOT / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "lucent_questions.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully generated {len(questions)} questions in {output_path}!")
    except Exception as e:
        print("Error generating database:", e)

if __name__ == "__main__":
    main()
