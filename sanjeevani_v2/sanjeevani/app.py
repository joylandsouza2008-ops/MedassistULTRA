"""Sanjeevani: one voice-first AI agent from emergency to recovery to everyday care.
Run with:  python -m streamlit run app.py"""
import streamlit as st

from core import i18n, state

st.set_page_config(page_title="Sanjeevani", page_icon="🌿", layout="wide")
state.init()

# Settings in the sidebar, shared by every page
with st.sidebar:
    st.selectbox("🌐 Language / ಭಾಷೆ / भाषा", list(i18n.LANGS),
                 format_func=lambda k: i18n.LANGS[k], key="lang")
    st.toggle(i18n.t("voice_on"), value=True, key="voice_on")
    st.toggle(i18n.t("big_text"), value=True, key="big_text")

i18n.big_text_css()

pages = [
    st.Page("pages/home.py", title=i18n.t("nav_home"), icon="🌿", default=True),
    st.Page("pages/1_Emergency.py", title=i18n.t("nav_em"), icon="🚨"),
    st.Page("pages/2_After_Discharge.py", title=i18n.t("nav_dis"), icon="🏥"),
    st.Page("pages/3_Elderly_Care.py", title=i18n.t("nav_eld"), icon="👵"),
    st.Page("pages/4_Dashboard.py", title=i18n.t("nav_dash"), icon="📋"),
]
st.navigation(pages).run()
