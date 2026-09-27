"""The user's profile + emergency contacts, saved in the browser (localStorage)
on their own phone, so it survives refreshes and restarts and stays on their device."""
import json

import streamlit as st

try:
    from streamlit_js_eval import streamlit_js_eval
except Exception:
    streamlit_js_eval = None

STORAGE_KEY = "sanjeevani_profile_v1"
EMPTY = {"name": "", "age": "", "phone": "", "village": "", "blood": "", "notes": "", "contacts": []}


def _defaults():
    from core.notify import default_contacts   # from secrets, e.g. SOS_CONTACTS
    p = dict(EMPTY)
    p["contacts"] = [{"name": c["name"], "relation": "", "phone": c["phone"]} for c in default_contacts()]
    return p


def load_once():
    """Read the saved profile from the browser (call early, once per run, from app.py)."""
    if "profile" in st.session_state:
        return
    if streamlit_js_eval is None:
        st.session_state.profile = _defaults()
        return
    raw = streamlit_js_eval(js_expressions=f"localStorage.getItem('{STORAGE_KEY}') || 'EMPTY'",
                            key="profile_loader")
    if raw is None:          # the browser hasn't answered yet; it will on the next run
        return
    if raw == "EMPTY":
        st.session_state.profile = _defaults()
        return
    try:
        p = {**EMPTY, **json.loads(raw)}
    except Exception:
        p = _defaults()
    st.session_state.profile = p


def get():
    return st.session_state.get("profile") or _defaults()


def save(p):
    """Keep it for this session and write it to the browser's storage."""
    st.session_state.profile = p
    if streamlit_js_eval is None:
        return False
    n = st.session_state.get("profile_save_n", 0) + 1
    st.session_state.profile_save_n = n
    data = json.dumps(json.dumps(p, ensure_ascii=False), ensure_ascii=False)   # a safe JS string
    streamlit_js_eval(js_expressions=f"localStorage.setItem('{STORAGE_KEY}', {data}); 'ok'",
                      key=f"profile_saver_{n}")
    return True


def info_line():
    """Short identity line added to every SOS, e.g. 'Kamala, 74 yrs, Blood B+, Ph +91...'."""
    p = get()
    parts = [p.get("name"), f"{p['age']} yrs" if p.get("age") else "",
             f"Blood {p['blood']}" if p.get("blood") else "", f"Ph {p['phone']}" if p.get("phone") else ""]
    return ", ".join(x for x in parts if x)
