import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
_memories = {}


def get_llm():
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        if r.status_code != 200:
            return None
        from langchain_community.llms import Ollama
        return Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.7)
    except Exception:
        return None


def get_memory(session_id: str):
    if session_id not in _memories:
        from langchain.memory import ConversationBufferWindowMemory
        _memories[session_id] = ConversationBufferWindowMemory(k=10)
    return _memories[session_id]


OFFLINE_TIPS = {
    "tcs": "TCS NQT: Focus on verbal, quantitative (time-speed-distance, percentages), and basic coding in Python/C++.",
    "infosys": "Infosys: Strong focus on logical reasoning and puzzles. Practice seating arrangements and blood relations.",
    "wipro": "Wipro NLTH: Verbal + quantitative + coding. Practice sentence completion and data interpretation.",
    "zoho": "Zoho: Heaviest coding round. Master arrays, strings, sorting, and searching algorithms.",
    "accenture": "Accenture: Cognitive + technical + coding. Focus on communication and English grammar.",
    "cognizant": "Cognizant CTS: Focus on quantitative aptitude and basic programming concepts.",
    "hcl": "HCL TechBee: Aptitude, reasoning, and basic coding. Similar pattern to TCS NQT.",
    "percentage": "Percentage formula: x% of y = y × x/100. Increase then decrease = net negative change.",
    "profit": "Profit% = (SP-CP)/CP × 100. SP = CP × (1 + P%). Loss% = (CP-SP)/CP × 100.",
    "speed": "Speed = Distance / Time. Relative speed same direction: |v1-v2|. Opposite: v1+v2.",
    "interest": "SI = PRT/100. CI = P[(1+r)^n - 1]. CI is always greater than SI for same P, R, T.",
    "fibonacci": "Fibonacci: f(n) = f(n-1) + f(n-2). Use DP or memoization. Time O(n), Space O(n).",
    "binary": "Binary Search: arr must be sorted. Compare mid element. O(log n) time complexity.",
    "sorting": "Bubble Sort O(n²), Merge Sort O(n log n), Quick Sort O(n log n) average case.",
    "array": "Arrays: indexing O(1), search O(n), insertion/deletion O(n). Use hash map for O(1) lookup.",
}


def smart_fallback(message: str) -> str:
    msg = message.lower()
    for key, tip in OFFLINE_TIPS.items():
        if key in msg:
            return f"💡 {tip}\n\n*(Start Ollama for detailed AI answers: `ollama serve`)*"

    if any(w in msg for w in ["aptitude", "quant", "logical", "reasoning", "formula"]):
        return ("📚 **Aptitude Tips:**\n"
                "• Practice 20 questions daily\n"
                "• Key topics: percentages, profit-loss, time-work, ratios, averages\n"
                "• TCS/Infosys heavily test logical reasoning\n"
                "• Aim for 90 seconds per question\n\n"
                "*(Start Ollama for step-by-step solutions)*")

    if any(w in msg for w in ["coding", "program", "code", "python", "java", "array", "string", "algorithm"]):
        return ("💻 **Coding Tips:**\n"
                "• Master: arrays, strings, recursion, sorting\n"
                "• Practice on the Coding page with real test cases\n"
                "• Know time complexity: O(1), O(n), O(log n), O(n²)\n"
                "• Most companies test basic DSA, not advanced topics\n\n"
                "*(Start Ollama for code explanations)*")

    if any(w in msg for w in ["communication", "speak", "voice", "hr", "interview", "filler", "wpm"]):
        return ("🎤 **Communication Tips:**\n"
                "• Target 120-150 words per minute\n"
                "• Avoid filler words: 'um', 'uh', 'like', 'basically'\n"
                "• Use STAR method for behavioral questions\n"
                "• Practice on the Communication page daily!\n\n"
                "*(Start Ollama for personalized feedback)*")

    return ("👋 I'm PlacePro AI! Currently in **offline mode**.\n\n"
            "I can still help with tips on:\n"
            "• 📚 Aptitude — ask any formula or topic\n"
            "• 💻 Coding — ask any DSA concept\n"
            "• 🎤 Communication — interview tips\n"
            "• 🏢 Company prep — ask about TCS, Infosys, Wipro, etc.\n\n"
            "**Enable full AI:** Run `ollama serve` in your terminal.")


async def chat_with_assistant(message: str, session_id: str) -> str:
    llm = get_llm()
    if not llm:
        return smart_fallback(message)
    try:
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        SYSTEM = """You are PlacePro AI, a smart placement training assistant for Indian engineering students.
Help them prepare for TCS, Infosys, Wipro, Zoho, Accenture, Cognizant, HCL campus placements.
Expertise: Aptitude (quant, logical), DSA, coding (Python/Java/C++), communication, HR interviews.
Show step-by-step solutions for aptitude. Give clean commented code for coding questions.
Be encouraging, concise, and practical.
History: {history}
Student: {input}
PlacePro AI:"""
        prompt = PromptTemplate(input_variables=["history", "input"], template=SYSTEM)
        chain = LLMChain(llm=llm, prompt=prompt, memory=get_memory(session_id))
        return chain.predict(input=message).strip()
    except Exception:
        return smart_fallback(message)


async def generate_test_feedback(test_type, score, max_score, percentage, time_taken, wrong_answers) -> str:
    llm = get_llm()
    if not llm:
        if percentage >= 80:
            return f"⭐⭐⭐ Excellent! {percentage:.0f}% — You're placement ready!"
        elif percentage >= 60:
            return f"⭐⭐ Good effort! {percentage:.0f}% — Review your weak areas and retry."
        else:
            return f"⭐ Keep going! {percentage:.0f}% — Focus on topics you missed. Practice daily!"
    try:
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        PROMPT = """Placement expert. Give brief motivating feedback.
Test: {test_type} | Score: {score}/{max_score} ({percentage}%) | Time: {time_taken}s
Wrong answers (sample): {wrong_answers}
Format: 1-line summary, 2 improvement areas, 1 study tip, 1 encouraging line. Max 80 words."""
        chain = LLMChain(llm=llm, prompt=PromptTemplate(
            input_variables=["test_type", "score", "max_score", "percentage", "time_taken", "wrong_answers"],
            template=PROMPT))
        return chain.predict(test_type=test_type, score=score, max_score=max_score,
                             percentage=percentage, time_taken=time_taken,
                             wrong_answers=str(wrong_answers[:3])).strip()
    except Exception:
        return f"Score: {percentage:.0f}%. Keep practicing!"


async def analyze_communication(topic, transcript, wpm, filler_words, duration) -> dict:
    word_count = len(transcript.split()) if transcript else 0
    fluency_score = min(10, max(0, 10 - abs(wpm - 140) / 20)) if wpm > 0 else 3
    fluency_score = max(0, fluency_score - min(4, len(filler_words) * 0.5))
    vocab_score = min(10, word_count / 25)
    overall = round((fluency_score + vocab_score) / 2, 2)

    llm = get_llm()
    if not llm:
        feedback = (f"WPM: {wpm:.0f} (ideal 120-150). "
                    f"Filler words: {len(filler_words)}. "
                    f"{'Good pace! ' if 120 <= wpm <= 150 else 'Adjust your speaking pace. '}"
                    f"{'Reduce fillers for confident delivery.' if len(filler_words) > 3 else 'Great job avoiding fillers!'}")
        return {"fluency_score": round(fluency_score, 2), "vocabulary_score": round(vocab_score, 2), "overall_score": overall, "feedback": feedback}

    try:
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        PROMPT = """Analyze speech for placement interview. Max 100 words.
Topic: {topic} | WPM: {wpm} (ideal 120-150) | Fillers: {filler_words} | Duration: {duration}s
Transcript: {transcript}
Feedback: 1) Pace 2) Content 3) Two improvements 4) Score/10"""
        chain = LLMChain(llm=llm, prompt=PromptTemplate(
            input_variables=["topic", "transcript", "wpm", "filler_words", "duration"],
            template=PROMPT))
        feedback = chain.predict(topic=topic, transcript=transcript[:500], wpm=wpm,
                                 filler_words=", ".join(filler_words[:10]) or "none",
                                 duration=duration).strip()
        return {"fluency_score": round(fluency_score, 2), "vocabulary_score": round(vocab_score, 2), "overall_score": overall, "feedback": feedback}
    except Exception:
        return {"fluency_score": round(fluency_score, 2), "vocabulary_score": round(vocab_score, 2), "overall_score": overall,
                "feedback": f"WPM: {wpm:.0f}. Fillers: {len(filler_words)}. Keep practicing!"}
