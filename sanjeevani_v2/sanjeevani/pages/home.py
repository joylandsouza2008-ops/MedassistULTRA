import streamlit as st

from core import ai, voice
from core.i18n import t

st.title("🌿 Sanjeevani")
st.markdown(f"### {t('home_tag')}")
st.write(t("home_intro"))
voice.listen_button(f"{t('home_tag')} {t('home_intro')}", "home")

if ai.available():
    st.success(t("ai_on"))
else:
    st.info(t("ai_off"))

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"#### 🚨 {t('nav_em')}")
    st.write(t("card_em"))
    st.page_link("pages/1_Emergency.py", label=t("open"), icon="🚨")
with c2:
    st.markdown(f"#### 🏥 {t('nav_dis')}")
    st.write(t("card_dis"))
    st.page_link("pages/2_After_Discharge.py", label=t("open"), icon="🏥")
with c3:
    st.markdown(f"#### 👵 {t('nav_eld')}")
    st.write(t("card_eld"))
    st.page_link("pages/3_Elderly_Care.py", label=t("open"), icon="👵")

st.divider()
st.page_link("pages/4_Dashboard.py", label=t("see_dash"), icon="📋")
st.caption(t("disclaimer"))
