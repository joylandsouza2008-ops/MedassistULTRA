"""One-press SOS: the moment the button is pressed, every emergency contact
gets an SMS + loud alarm with the person's live location and details.
On a phone, the dialer also opens to call the first contact.
(Automatic ringing of every contact happens too if Twilio is set up.)"""
import time

import streamlit as st

from core import location, notify, profile, state, ui
from core.i18n import t

try:
    from streamlit_js_eval import streamlit_js_eval
except Exception:
    streamlit_js_eval = None


def _is_phone():
    try:
        agent = st.context.headers.get("User-Agent", "")
        return any(w in agent for w in ("Mobi", "Android", "iPhone"))
    except Exception:
        return False


def trigger():
    """Send the SOS right now to everyone."""
    loc = location.current()
    maps = notify.maps_link(loc["lat"], loc["lon"])
    who = profile.get().get("name") or "A MedX user"
    msg = f"MEDX SOS: {who} pressed the SOS button and needs help NOW. Location: {maps} Please call immediately."
    spoken = (f"Emergency alert from MedX. {who} pressed the S O S button and needs help now. "
              f"Please call them immediately.")
    results = notify.send_sos(msg, spoken, call=True, click_url=maps) if notify.auto_ready() else []
    state.add_alert("SOS button", "All emergency contacts", msg)
    st.session_state.sos_panel = {"id": int(time.time()), "results": results, "maps": maps,
                                  "n": len(notify.contacts()), "dialed": False, "safe": False}


def render_panel():
    """Show what the SOS did, with call buttons and 'I'm safe'. Drawn at the top of every page."""
    panel = st.session_state.get("sos_panel")
    if not panel:
        return
    people = notify.contacts()
    with st.container(key="sos_panel"):
        if panel["safe"]:
            ui.card("ok", t("sos_safe_sent"))
        elif not people:
            ui.card("danger", "🆘 SOS", t("sos_none"))
        else:
            ui.card("danger", t("sos_sent_title", n=panel["n"]), t("sos_hint"))
            for name, kind, good, err in panel["results"]:
                if good:
                    st.success(t({"sms": "sos_sms_ok", "call": "sos_call_ok", "alarm": "sos_alarm_ok"}[kind], name=name))
                else:
                    st.warning(t("sos_fail", name=name, err=err))
            if not notify.auto_ready():
                st.caption("ℹ️ " + t("sos_auto_off"))
            # on a phone, open the dialer for the first contact straight away (once)
            if not panel["dialed"] and _is_phone() and streamlit_js_eval is not None:
                panel["dialed"] = True
                streamlit_js_eval(js_expressions=f"window.location.href='tel:{people[0]['phone']}'",
                                  key=f"sos_dial_{panel['id']}")
                st.info(t("sos_calling", name=people[0]["name"]))

        cols = st.columns(min(len(people), 3) + 1)
        cols[0].link_button(t("call_108"), "tel:108", type="primary", width="stretch")
        for col, c in zip(cols[1:], people[:3]):
            col.link_button(t("sos_call_btn", name=c["name"]), f"tel:{c['phone']}", width="stretch")

        a, b = st.columns(2)
        if not panel["safe"] and people and a.button(t("sos_safe"), width="stretch", key=f"sos_safe_{panel['id']}"):
            who = profile.get().get("name") or "The MedX user"
            if notify.auto_ready():
                notify.send_sos(f"MEDX: {who} is safe now. The SOS was a false alarm. Sorry for the worry.", "", call=False)
            state.add_alert("SOS cancelled", "All emergency contacts", f"{who} is safe")
            panel["safe"] = True
            st.rerun()
        if b.button("✖", width="stretch", key=f"sos_close_{panel['id']}"):
            st.session_state.pop("sos_panel", None)
            st.rerun()
