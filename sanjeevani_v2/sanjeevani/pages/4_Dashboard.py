import pandas as pd
import streamlit as st

from core import data, state
from core.i18n import t

st.title(t("dash_title"))
st.write(t("dash_intro"))

st.markdown(f"### {t('actions')}")
if st.session_state.alerts:
    st.dataframe(pd.DataFrame(st.session_state.alerts), hide_index=True, use_container_width=True)
    if st.button(t("clear")):
        st.session_state.alerts = []
        st.session_state.sent_keys = set()
        st.rerun()
else:
    st.info(t("no_actions"))

st.markdown(f"### {t('h_stock')}")
st.dataframe(pd.DataFrame([{"Hospital": h["name"], "Antivenom vials": h["stock"]["antivenom_vials"],
                            "Anti-rabies vaccine": h["stock"]["anti_rabies_vaccine"],
                            "Heart care": "Yes" if h["stock"]["cardiac_care"] else "No"}
                           for h in data.hospitals()]), hide_index=True, use_container_width=True)

st.markdown(f"### {t('p_stock')}")
st.dataframe(pd.DataFrame([{"Pharmacy": ph["name"], **{k.title(): v for k, v in ph["stock"].items()}}
                           for ph in data.pharmacies()]), hide_index=True, use_container_width=True)
