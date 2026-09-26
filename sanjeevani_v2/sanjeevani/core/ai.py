"""All AI calls live here, using NVIDIA NIM (build.nvidia.com).
NVIDIA's API is OpenAI-compatible, so we just send HTTP requests to it.
If no key is set, the pages use sample data or keyword rules instead,
so the demo never breaks on stage.

Secrets (in .streamlit/secrets.toml or Streamlit Cloud -> Settings -> Secrets):
    NVIDIA_API_KEY = "nvapi-..."
    NVIDIA_TEXT_MODEL = "sarvamai/sarvam-m"                              # optional
    NVIDIA_VISION_MODEL = "meta/llama-4-maverick-17b-128e-instruct"      # optional
"""
import base64
import json
import os
import re
import urllib.request

import streamlit as st

API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# Text (understanding what people say, replying in Kannada/Hindi/English)
# and vision (reading prescriptions and medicine strips) can use different models.
DEFAULT_VISION_MODEL = "meta/llama-4-maverick-17b-128e-instruct"
DEFAULT_TEXT_MODEL = DEFAULT_VISION_MODEL


def _secret(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name)


def available():
    return bool(_secret("NVIDIA_API_KEY"))


def _model(has_image):
    if has_image:
        return _secret("NVIDIA_VISION_MODEL") or _secret("NVIDIA_MODEL") or DEFAULT_VISION_MODEL
    return _secret("NVIDIA_TEXT_MODEL") or _secret("NVIDIA_MODEL") or DEFAULT_TEXT_MODEL


def _ask(content, max_tokens=1000):
    """Send one message (text, or text + image) to NVIDIA and return the reply text."""
    has_image = any(part.get("type") == "image_url" for part in content)
    body = {
        "model": _model(has_image),
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_secret('NVIDIA_API_KEY')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"] or ""


def _to_json(text):
    """Pull the JSON out of the model's reply, even if it added extra words around it."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if start == -1 or end == -1:
            return None
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None


def _image_block(file):
    """Turn an uploaded photo into the format NVIDIA's vision models accept."""
    data = base64.standard_b64encode(file.getvalue()).decode("utf-8")
    media_type = file.type if file.type in ("image/jpeg", "image/png", "image/webp") else "image/jpeg"
    return {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}}


PRESCRIPTION_PROMPT = """You are reading a prescription or hospital discharge summary from India.
Extract ONLY the medicines that are written. Do not add, remove or change any medicine.
Return ONLY JSON, no other text, in this format:
{"medicines": [{"brand": "...", "salt": "... or null", "strength": "... or null",
  "pattern": "morning-afternoon-night like 1-0-1", "days": number or null}],
 "follow_up_days": number or null}
If something is unclear, use null instead of guessing."""

STRIP_PROMPT = """This is a photo of a medicine strip or box. Read the printed text.
Return ONLY JSON, no other text:
{"readable": true/false, "brand": "... or null", "salt": "... or null",
 "strength": "... or null", "expiry": "MM/YYYY or null"}
If the name is not clearly visible (for example a loose tablet), set readable to false.
Never guess a medicine name."""

EMERGENCY_PROMPT = """A villager in Karnataka, India sent this emergency message
(it may be in Kannada, Tulu, Hindi or English): "{text}"
Classify it. Return ONLY JSON:
{{"type": "snakebite" | "dog_bite" | "chest_pain" | "other",
  "summary": "one short English sentence"}}"""


def read_prescription(file):
    result = _to_json(_ask([_image_block(file), {"type": "text", "text": PRESCRIPTION_PROMPT}]))
    return result if isinstance(result, dict) else None


def read_strip(file):
    result = _to_json(_ask([_image_block(file), {"type": "text", "text": STRIP_PROMPT}], max_tokens=300))
    return result if isinstance(result, dict) else None


def classify_emergency(text):
    result = _to_json(_ask([{"type": "text", "text": EMERGENCY_PROMPT.format(text=text)}], max_tokens=200))
    return result if isinstance(result, dict) else None


SAR_PROMPT = """This is a flood/landslide emergency report from Karnataka, India
(it may be in Kannada, Hindi or English): "{text}"
Pick which of these apply: unconscious, trapped, snakebite, injured, landslide,
water_rising, vulnerable (elderly, child, pregnant, disabled), medicine, food.
Return ONLY JSON: {{"flags": [..], "people": number of people mentioned or 1}}"""


def classify_sar_report(text):
    result = _to_json(_ask([{"type": "text", "text": SAR_PROMPT.format(text=text)}], max_tokens=200))
    return result if isinstance(result, dict) else None


LANG_NAMES = {"en": "English", "kn": "Kannada (in Kannada script)", "hi": "Hindi (in Devanagari script)"}

ASSIST_PROMPT = """You are Sanjeevani, a voice-first emergency helper for rural families in Karnataka, India.
A person near "{place}" said (maybe in Kannada, Tulu, Hindi or English): "{text}"

Rules you must follow:
- Never diagnose a disease. Never name medicines or doses.
- Give only standard, widely accepted first aid.
- If it could be serious, tell them to call 108 and go to a hospital now. If in doubt, treat it as serious.
- Snakebite needs antivenom at a hospital. Animal bites need the anti-rabies vaccine. Chest pain, stroke signs
  or breathing trouble need emergency hospital care.
- If it is clearly not an emergency, give short safe advice and suggest seeing a doctor.
- Write "reply", "do" and "dont" in {language}, in very simple words an elderly villager understands.

Return ONLY JSON, no other text:
{{"type": "snakebite" or "dog_bite" or "chest_pain" or "other",
  "needs": "antivenom_vials" or "anti_rabies_vaccine" or "cardiac_care" or "general",
  "urgency": "emergency" or "urgent" or "routine",
  "summary": "one short English sentence describing the situation",
  "reply": "2 or 3 short sentences to speak aloud to them",
  "do": ["up to 4 short steps"],
  "dont": ["up to 3 short warnings"]}}"""


def emergency_assistant(text, lang, place):
    prompt = ASSIST_PROMPT.format(place=place, text=text, language=LANG_NAMES.get(lang, "English"))
    result = _to_json(_ask([{"type": "text", "text": prompt}], max_tokens=900))
    return result if isinstance(result, dict) and result.get("reply") else None
