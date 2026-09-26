"""All AI calls live here. If no API key is set, the app still works
using demo/fallback logic, so your demo never breaks on stage."""
import base64
import json
import os

import streamlit as st

DEFAULT_MODEL = "claude-sonnet-5"


def _secret(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name)


def available():
    return bool(_secret("ANTHROPIC_API_KEY"))


def _ask(content, max_tokens=1000):
    import anthropic  # imported here so the app runs even without the package

    client = anthropic.Anthropic(api_key=_secret("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=_secret("ANTHROPIC_MODEL") or DEFAULT_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _to_json(text):
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
    data = base64.standard_b64encode(file.getvalue()).decode("utf-8")
    media_type = file.type if file.type in ("image/jpeg", "image/png", "image/webp", "image/gif") else "image/jpeg"
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


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
