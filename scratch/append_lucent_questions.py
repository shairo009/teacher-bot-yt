import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

api_key = os.environ.get('OPENAI_API_KEY', '')
base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

def call_llm(prompt):
    messages = [
        {"role": "system", "content": "You are a specialized GK content creator. Output clean, valid JSON only. Do not wrap in markdown codeblocks."},
        {"role": "user", "content": prompt}
    ]
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
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

def append_questions(num_questions=10, chapter_topic_info=None):
    questions_path = PROJECT_ROOT / "data/lucent_questions.json"
    
    # Load existing questions
    existing_questions = []
    if questions_path.exists():
        with open(questions_path, 'r', encoding='utf-8') as f:
            try:
                existing_questions = json.load(f)
            except:
                pass
                
    start_id = len(existing_questions) + 1
    print(f"Current database has {len(existing_questions)} questions. Starting new batch from ID: {start_id}")
    
    if not chapter_topic_info:
        # Default next chapters for Polity
        chapter_topic_info = (
            "Indian Polity & Constitution. Focus on subsequent chapters like:\n"
            "- Amendment of the Constitution (संविधान का संशोधन)\n"
            "- Fundamental Rights & Duties (Additional advanced details)\n"
            "- President & Vice President of India (राष्ट्रपति और उपराष्ट्रपति)\n"
            "- Prime Minister & Council of Ministers (प्रधानमंत्री और मंत्रिपरिषद)\n"
            "- Parliament of India (भारतीय संसद - लोकसभा और राज्यसभा)"
        )
        
    prompt = f"""
Generate exactly {num_questions} high-quality multiple choice questions based on the Lucent's General Knowledge book.
Focus area: {chapter_topic_info}

Start numbering the IDs from {start_id}.

For each question, output a JSON object with the following fields:
- id: unique integer starting from {start_id} and incrementing by 1
- subject: e.g., "INDIAN POLITY (भारतीय राजव्यवस्था)"
- chapter: e.g., "CHAPTER 10: AMENDMENT OF THE CONSTITUTION (संविधान का संशोधन)"
- topic: e.g., "AMENDMENT PROCEDURE (संशोधन प्रक्रिया)"
- question_hi: Question in Hindi (clear, high quality)
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

Output a raw JSON array of these {num_questions} objects. Ensure valid JSON without comments or extra text.
"""
    
    try:
        print("Calling LLM to generate questions...")
        json_str = call_llm(prompt)
        new_questions = json.loads(json_str)
        
        # Verify IDs are sequential
        for idx, q in enumerate(new_questions):
            q["id"] = start_id + idx
            
        combined_questions = existing_questions + new_questions
        
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump(combined_questions, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully generated and appended {len(new_questions)} questions! New database size: {len(combined_questions)}")
        return True
    except Exception as e:
        print("Error appending questions:", e)
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=10, help="Number of questions to generate")
    parser.add_argument("--focus", type=str, default=None, help="Focus chapters/topics description")
    args = parser.parse_args()
    
    append_questions(args.num, args.focus)
