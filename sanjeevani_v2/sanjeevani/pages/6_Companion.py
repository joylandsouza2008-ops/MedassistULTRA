import hashlib

import streamlit as st

from core import ai, companion, location, notify, state, ui, voice
from core.i18n import lang, t

p = companion.patient()
first = p["name"].split(" (")[0]
family = p["family_contact"]["name"]

ui.header(t("chat_title"), t("chat_intro", name=first))
if not ai.available():
    st.caption("ℹ️ " + t("chat_no_ai"))

# start (or restart) the conversation with a greeting in the chosen language
if st.button(t("chat_clear")) or "chat" not in st.session_state or st.session_state.get("chat_lang") != lang():
    st.session_state.chat = [{"role": "assistant", "content": t("chat_greeting", name=first), "level": "none"}]
    st.session_state.chat_lang = lang()


def act_on(level, user_text, msg_id):
    """Alert the family / trigger SOS when the companion hears something worrying."""
    if level == "none":
        return
    loc = location.current(p["village"])
    maps = notify.maps_link(loc["lat"], loc["lon"])
    if level == "emergency":
        text = f"SANJEEVANI SOS: {p['name']} said: \"{user_text[:100]}\". Location: {maps} Please call now."
        spoken = f"Emergency alert from Sanjeevani. {first} may need urgent help. Please call her now."
        call = True
    elif level == "crisis":
        text = f"Sanjeevani: {p['name']} may need emotional support right now. Please call her. Location: {maps}"
        spoken, call = "", False
    else:
        text = f"Sanjeevani daily check-in: {p['name']} said: \"{user_text[:100]}\". Please give her a call today."
        spoken, call = "", False
    state.add_alert(f"Companion: {level}", family, text, key=f"comp-{msg_id}")
    if notify.auto_ready() and f"comp-sos-{msg_id}" not in st.session_state.sent_keys:
        st.session_state.sent_keys.add(f"comp-sos-{msg_id}")
        notify.send_sos(text, spoken, call=call, click_url=maps)


def handle(user_text):
    msg_id = hashlib.md5(f"{len(st.session_state.chat)}-{user_text}".encode()).hexdigest()[:10]
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat]
    with st.spinner(t("thinking")):
        reply, level = companion.respond(history, user_text, lang(), t("chat_fallback"))
    st.session_state.chat.append({"role": "user", "content": user_text, "level": "none"})
    st.session_state.chat.append({"role": "assistant", "content": reply, "level": level})
    act_on(level, user_text, msg_id)


# ---------- the conversation ----------
for i, m in enumerate(st.session_state.chat):
    with st.chat_message(m["role"], avatar="🌿" if m["role"] == "assistant" else "👵"):
        st.write(m["content"])
        if m["level"] == "emergency":
            ui.card("danger", t("chat_danger"))
            st.link_button(t("call_108"), "tel:108", type="primary")
        elif m["level"] == "crisis":
            ui.card("warn", t("chat_crisis"))
            st.link_button(t("chat_call_helpline"), "tel:14416", type="primary")
        elif m["level"] == "family":
            st.caption(t("chat_family"))

# read the newest reply aloud, and offer a replay button
last = st.session_state.chat[-1]
if last["role"] == "assistant":
    voice.say(last["content"])
    voice.listen_button(last["content"], f"chat-{len(st.session_state.chat)}")

# ---------- speak ----------
audio = st.audio_input(t("chat_speak"))
if audio is not None:
    audio_id = hashlib.md5(audio.getvalue()).hexdigest()
    if st.session_state.get("chat_last_audio") != audio_id:
        st.session_state.chat_last_audio = audio_id
        try:
            heard = voice.transcribe(audio)
        except Exception:
            heard = None
        if heard:
            handle(heard)
            st.rerun()
        else:
            st.warning(t("not_heard"))

# ---------- type ----------
typed = st.chat_input(t("chat_placeholder"))
if typed:
    handle(typed)
    st.rerun()
