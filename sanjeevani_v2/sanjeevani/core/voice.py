"""Voice: text-to-speech (read aloud) and speech-to-text (understand voice notes).
Both use free Google voice services, so they need internet.
Kannada, Hindi and English are supported."""
import io

import streamlit as st

from core import i18n

TTS_LANG = {"en": "en", "kn": "kn", "hi": "hi"}
STT_LANG = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}


@st.cache_data(show_spinner=False)
def _mp3(text, lang):
    from gtts import gTTS

    buf = io.BytesIO()
    gTTS(text=text, lang=TTS_LANG.get(lang, "en"), tld="co.in").write_to_fp(buf)
    return buf.getvalue()


def play(text):
    """Read text aloud right now, in the chosen language."""
    try:
        st.audio(_mp3(text, i18n.lang()), format="audio/mp3", autoplay=True)
    except Exception:
        st.caption(i18n.t("voice_offline"))


def say(text):
    """Speak an important result automatically (only once, only if voice is on)."""
    if not st.session_state.get("voice_on", True):
        return
    spoken = st.session_state.setdefault("spoken", set())
    key = (i18n.lang(), text)
    if key in spoken:
        return
    spoken.add(key)
    play(text)


def listen_button(text, key):
    """A 🔊 button that reads the given text aloud when pressed."""
    if st.button(i18n.t("listen"), key=f"listen-{key}"):
        play(text)


def transcribe(audio_file):
    """Turn a recorded voice note into text in the chosen language.
    Returns the text, or None if it couldn't understand."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_file.getvalue())) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language=STT_LANG.get(i18n.lang(), "en-IN"))
    except (sr.UnknownValueError, sr.RequestError):
        return None
