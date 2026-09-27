import hashlib

import streamlit as st

from core import ai, data, emergency, live, ui, voice
from core.i18n import lang, t

ui.header(t("em_title"), t("em_intro"), "em")

EXAMPLES = {
    "🐍 ಕನ್ನಡ": "ನನ್ನ ಅಪ್ಪನಿಗೆ ಹೊಲದಲ್ಲಿ ಹಾವು ಕಚ್ಚಿದೆ, ಬೇಗ ಸಹಾಯ ಮಾಡಿ",
    "🔥 हिन्दी": "मेरी माँ का हाथ चूल्हे पर बुरी तरह जल गया है",
    "🐕 English": "A stray dog bit my son on the leg near the school",
    "❤️ English": "My grandmother has chest pain and is sweating",
}

st.session_state.setdefault("em_text", "")
st.session_state.setdefault("em_place", data.villages()[0]["name"])


def use_example(text):
    st.session_state.em_text = text
    st.session_state.em_go = True


def resolve_place(name):
    """Live GPS first, then demo villages, then find the typed place on the real map."""
    name = (name or "").strip()
    gps = st.session_state.get("gps")
    if gps and name == gps["name"]:
        return gps, None
    for v in data.villages():
        if v["name"].lower() == name.lower():
            return {**v, "full": v["name"]}, None
    if name:
        try:
            found = live.geocode(name)
            if found:
                return found, None
        except Exception:
            pass
    fallback = data.villages()[0]
    return {**fallback, "full": fallback["name"]}, t("loc_not_found", place=fallback["name"])


if st.session_state.get("gps") and st.session_state.get("em_place") == st.session_state.gps["name"]:
    g = st.session_state.gps
    st.success(t("gps_ok", place=g["name"], acc=g["acc"] or "?"))

st.text_input(t("loc_label"), key="em_place")

# ---------- speak ----------
st.markdown(f"**{t('what_happened')}**")
audio = st.audio_input(t("record"))
if audio is not None:
    audio_id = hashlib.md5(audio.getvalue()).hexdigest()
    if st.session_state.get("last_audio") != audio_id:
        st.session_state.last_audio = audio_id
        try:
            heard = voice.transcribe(audio)
        except Exception:
            heard = None
        if heard:
            st.session_state.em_text = heard
            st.session_state.em_go = True
        else:
            st.warning(t("not_heard"))

st.text_area(t("message"), key="em_text", height=90)

with st.expander(t("ex_title")):
    cols = st.columns(len(EXAMPLES))
    for col, (label, text) in zip(cols, EXAMPLES.items()):
        col.button(label, on_click=use_example, args=(text,), width="stretch")

go = st.button(t("get_help"), type="primary", width="stretch")
if (go or st.session_state.pop("em_go", False)) and st.session_state.em_text.strip():
    loc, note = resolve_place(st.session_state.em_place)
    with st.spinner(t("thinking")):
        st.session_state.em_result = emergency.analyze(st.session_state.em_text, lang(), loc["full"])
    st.session_state.em_loc = loc
    st.session_state.em_note = note

if not ai.available():
    st.caption("ℹ️ " + t("ai_needed"))

if st.session_state.get("em_result"):
    if st.session_state.get("em_note"):
        st.caption(st.session_state.em_note)
    loc = st.session_state.em_loc
    st.caption(f"📍 {loc['full']}")
    emergency.render_result(st.session_state.em_result, loc)
