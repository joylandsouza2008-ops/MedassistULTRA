import hashlib

import streamlit as st

from core import data, emergency, voice
from core.i18n import t

st.title(t("em_title"))
st.write(t("em_intro"))

SAMPLES = {
    "🐍 ಕನ್ನಡ": "ನನ್ನ ಅಪ್ಪನಿಗೆ ಹೊಲದಲ್ಲಿ ಹಾವು ಕಚ್ಚಿದೆ, ಬೇಗ ಸಹಾಯ ಮಾಡಿ",
    "🐍 हिन्दी": "मेरे पिताजी को खेत में सांप ने काट लिया है, जल्दी मदद करो",
    "🐕 English": "A stray dog bit my son on the leg near the school",
    "❤️ English": "My grandmother has chest pain and is sweating",
}

st.session_state.setdefault("em_text", "")
st.session_state.setdefault("em_place", data.villages()[0]["name"])


def use_sample(text):
    st.session_state.em_text = text
    st.session_state.em_go = True


place = st.selectbox(t("where"), [v["name"] for v in data.villages()], key="em_place")

# ---------- 1. Voice ----------
st.markdown(f"**{t('step_voice')}**")
audio = st.audio_input(t("record"))
if audio is not None:
    audio_id = hashlib.md5(audio.getvalue()).hexdigest()
    if st.session_state.get("last_audio") != audio_id:   # only transcribe a new recording
        st.session_state.last_audio = audio_id
        try:
            heard = voice.transcribe(audio)
        except Exception:
            heard = None
            st.caption(t("voice_offline"))
        if heard:
            st.session_state.em_text = heard          # set before the text box is drawn
            st.session_state.em_go = True
            st.session_state.heard = heard
        else:
            st.session_state.heard = None
            st.warning(t("not_heard"))
    if st.session_state.get("heard"):
        st.caption(t("heard", text=st.session_state.heard))

# ---------- 2. Text / examples ----------
st.markdown(f"**{t('step_text')}**")
cols = st.columns(len(SAMPLES))
for col, (label, text) in zip(cols, SAMPLES.items()):
    col.button(label, on_click=use_sample, args=(text,), use_container_width=True)
st.text_area(t("message"), key="em_text", height=80)

if st.button(t("get_help"), type="primary") or st.session_state.pop("em_go", False):
    etype, summary = emergency.detect(st.session_state.em_text)
    st.session_state.em_type = etype
    st.session_state.em_summary = summary

etype = st.session_state.get("em_type")
if etype:
    if st.session_state.get("em_summary"):
        st.caption(t("understood", s=st.session_state.em_summary))
    emergency.render(etype, place)
elif "em_type" in st.session_state:
    st.error(t("unknown_em"))
    voice.say(t("unknown_em"))
