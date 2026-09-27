"""Sanjeevani: one voice-first AI agent from emergency to recovery to everyday care.
Run with:  python -m streamlit run app.py"""
import streamlit as st

from core import i18n, location, notify, profile, state, ui

st.set_page_config(page_title="Sanjeevani", page_icon="🌿", layout="wide")
state.init()

# Settings in the sidebar, shared by every page
with st.sidebar:
    with st.container(key="side_help"):
        if st.button(i18n.t("help_btn"), key="side_help_btn", width="stretch"):
            st.session_state.goto_help = True
    with st.container(key="sb_settings"):
        st.markdown(f'<div class="sj-sb-title">⚙️ {i18n.t("settings")}</div>', unsafe_allow_html=True)
        st.selectbox("🌐 Language / ಭಾಷೆ / भाषा", list(i18n.LANGS),
                     format_func=lambda k: i18n.LANGS[k], key="lang")
        st.toggle(i18n.t("voice_on"), value=True, key="voice_on")
        st.toggle(i18n.t("big_text"), value=True, key="big_text")
        location.auto_detect()
    profile.load_once()

ui.css()
i18n.big_text_css()

pages = [
    st.Page("pages/home.py", title=i18n.t("nav_home"), icon="🌿", default=True),
    st.Page("pages/1_Emergency.py", title=i18n.t("nav_em"), icon="🚨"),
    st.Page("pages/7_Profile.py", title=i18n.t("nav_profile"), icon="👤"),
    st.Page("pages/2_After_Discharge.py", title=i18n.t("nav_dis"), icon="🏥"),
    st.Page("pages/3_Elderly_Care.py", title=i18n.t("nav_eld"), icon="👵"),
    st.Page("pages/6_Companion.py", title=i18n.t("nav_chat"), icon="💬"),
    st.Page("pages/5_Disaster_Mode.py", title=i18n.t("nav_sar"), icon="🌊"),
    st.Page("pages/4_Dashboard.py", title=i18n.t("nav_dash"), icon="📋"),
]
pg = st.navigation(pages)
with st.sidebar:
    with st.container(key="sb_profile"):
        me = profile.get()
        n = len(notify.contacts())
        if me.get("name") or n:
            st.caption(i18n.t("prof_sidebar", name=me.get("name") or "—", n=n))
        st.page_link("pages/7_Profile.py", label=i18n.t("prof_setup") if not n else i18n.t("nav_profile"), icon="👤")

if st.session_state.pop("goto_help", False):
    st.switch_page("pages/1_Emergency.py")
pg.run()
