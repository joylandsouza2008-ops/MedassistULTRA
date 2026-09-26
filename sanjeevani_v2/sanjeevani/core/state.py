"""Shared memory for the demo (alerts, doses taken, reservations).
Streamlit keeps this while the browser tab is open."""
from datetime import datetime

import streamlit as st


def init():
    ss = st.session_state
    ss.setdefault("alerts", [])          # every action the agent takes
    ss.setdefault("taken_today", {})     # brand+slot -> True
    ss.setdefault("sent_keys", set())    # to avoid sending the same alert twice


def add_alert(kind, to, message, key=None):
    """Record an action the agent took. In the real product this would
    send a WhatsApp message / SMS / phone call instead."""
    init()
    if key and key in st.session_state.sent_keys:
        return False
    if key:
        st.session_state.sent_keys.add(key)
    st.session_state.alerts.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "type": kind,
        "to": to,
        "message": message,
    })
    return True
