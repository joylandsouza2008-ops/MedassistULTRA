"""Sanjeevani: one voice-first AI agent from emergency to recovery to everyday care.
Run with:  python -m streamlit run app.py"""
import streamlit as st

from core import i18n, notify, state, ui

st.set_page_config(page_title="Sanjeevani", page_icon="🌿", layout="wide")
state.init()

# Settings in the sidebar, shared by every page
with st.sidebar:
    st.selectbox("🌐 Language / ಭಾಷೆ / भाषा", list(i18n.LANGS),
                 format_func=lambda k: i18n.LANGS[k], key="lang")
    st.toggle(i18n.t("voice_on"), value=True, key="voice_on")
    st.toggle(i18n.t("big_text"), value=True, key="big_text")
    with st.expander(i18n.t("sos_contacts")):
        defaults = notify.default_contacts()
        for i in (1, 2):
            d = defaults[i - 1] if len(defaults) >= i else {"name": "", "phone": ""}
            c1, c2 = st.columns([2, 3])
            c1.text_input(i18n.t("sos_name"), value=d["name"], key=f"sos_name_{i}")
            c2.text_input(i18n.t("sos_phone"), value=d["phone"], key=f"sos_phone_{i}")

ui.css()
i18n.big_text_css()

pages = [
    st.Page("pages/home.py", title=i18n.t("nav_home"), icon="🌿", default=True),
    st.Page("pages/1_Emergency.py", title=i18n.t("nav_em"), icon="🚨"),
    st.Page("pages/2_After_Discharge.py", title=i18n.t("nav_dis"), icon="🏥"),
    st.Page("pages/3_Elderly_Care.py", title=i18n.t("nav_eld"), icon="👵"),
    st.Page("pages/5_Disaster_Mode.py", title=i18n.t("nav_sar"), icon="🌊"),
    st.Page("pages/4_Dashboard.py", title=i18n.t("nav_dash"), icon="📋"),
]
st.navigation(pages).run()
