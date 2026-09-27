"""Daily companion: a caring AI that talks with the patient every day,
checks how they feel and whether they took their medicines, and alerts the
family (or triggers an emergency) when it hears danger signs."""
import re

from core import ai, data, meds
from core.ai import LANG_NAMES

DANGER_WORDS = [
    "chest pain", "can't breathe", "cannot breathe", "breathless", "not breathing", "fainted", "unconscious",
    "i fell", "fell down", "fall down", "bleeding", "stroke", "can't move", "snake", "dog bit",
    "ಎದೆ ನೋವು", "ಉಸಿರಾಡಲು", "ಉಸಿರು ಕಟ್ಟ", "ಬಿದ್ದೆ", "ಬಿದ್ದು", "ಪ್ರಜ್ಞೆ", "ರಕ್ತ", "ಹಾವು",
    "सीने में दर्द", "साँस नहीं", "सांस नहीं", "गिर गई", "गिर गया", "बेहोश", "खून", "सांप", "साँप",
]
CRISIS_WORDS = [
    "want to die", "kill myself", "end my life", "suicide", "no reason to live",
    "ಸಾಯಬೇಕು", "ಸಾಯಲು", "ಆತ್ಮಹತ್ಯೆ",
    "मरना चाहती", "मरना चाहता", "आत्महत्या", "जीना नहीं",
]
WORRY_WORDS = [
    "didn't take", "did not take", "forgot", "not eating", "can't sleep", "lonely", "very tired", "dizzy",
    "ಮರೆತೆ", "ತೆಗೆದುಕೊಂಡಿಲ್ಲ", "ತಲೆ ಸುತ್ತು", "ಒಂಟಿ",
    "भूल गई", "भूल गया", "नहीं ली", "चक्कर", "अकेला", "अकेली",
]
LEVELS = ["none", "family", "emergency", "crisis"]

SYSTEM = """You are Sanjeevani, a warm, patient daily companion for {name}, a {age}-year-old living in {village}, India.
Talk like a caring grandchild. Reply in {language}, in 1 to 3 short, simple sentences.
Their medicines: {medicines}.
Each day, gently check how they feel, their sleep, food and water, and whether they took their medicines.
Rules:
- Never diagnose. Never name new medicines or change doses. For medicine doubts, say to ask the pharmacist or doctor.
- If they mention chest pain, breathing trouble, fainting, a fall, confusion, weakness on one side, heavy bleeding,
  snakebite or high fever: tell them to press the HELP button or call 108 right now.
- If they talk about wanting to die or hurting themselves: respond with love, and give the free Tele-MANAS helpline 14416.
- If they sound lonely, listen kindly and ask about their family or something they enjoy.
At the very end, on its own line, write exactly one of:
ALERT: none
ALERT: family      (worrying but not urgent, like missed medicine, not eating, feeling very low)
ALERT: emergency   (a danger sign above)
ALERT: crisis      (talk of self-harm)"""


def patient():
    """The demo patient, personalised with the user's own profile when they've filled it in."""
    p = dict(data.load("elderly_profile"))
    try:
        from core import profile
        me = profile.get()
        if me.get("name"):
            p["name"] = me["name"]
            p["age"] = me.get("age") or p["age"]
            p["village"] = me.get("village") or p["village"]
    except Exception:
        pass
    return p


def system_prompt(lang_code):
    p = patient()
    plan = []
    for slot, items in meds.schedule(p["medicines"]).items():
        if items:
            plan.append(f"{slot}: " + ", ".join(m["brand"] for m in items))
    return SYSTEM.format(name=p["name"].split(" (")[0], age=p["age"], village=p["village"],
                         language=LANG_NAMES.get(lang_code, "English"), medicines="; ".join(plan))


def keyword_level(text):
    low = (text or "").lower()
    if any(w in low for w in CRISIS_WORDS):
        return "crisis"
    if any(w in low for w in DANGER_WORDS):
        return "emergency"
    if any(w in low for w in WORRY_WORDS):
        return "family"
    return "none"


def split_alert(reply):
    """Separate the 'ALERT: x' line from what we show the patient."""
    m = re.search(r"ALERT\s*:\s*(none|family|emergency|crisis)", reply or "", re.IGNORECASE)
    level = m.group(1).lower() if m else "none"
    clean = re.sub(r"\n?\s*ALERT\s*:\s*\w+\s*", "", reply or "").strip()
    return clean, level


def respond(history, user_text, lang_code, fallback_text):
    """history: list of {"role", "content"} shown so far. Returns (reply, level)."""
    kw = keyword_level(user_text)
    reply, ai_level = None, "none"
    if ai.available():
        try:
            msgs = [{"role": "system", "content": system_prompt(lang_code)}]
            msgs += history[-10:] + [{"role": "user", "content": user_text}]
            reply, ai_level = split_alert(ai.chat(msgs))
        except Exception:
            reply = None
    if not reply:
        reply = fallback_text
    # the more serious of the keyword check and the AI's judgement wins
    level = max(kw, ai_level, key=LEVELS.index)
    return reply, level
