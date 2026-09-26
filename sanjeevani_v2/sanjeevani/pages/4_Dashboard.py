import pandas as pd
import streamlit as st

from core import ui, data, state
from core.i18n import t

ui.header(t("dash_title"), t("dash_intro"))

st.markdown(f"### {t('actions')}")
if st.session_state.alerts:
    st.dataframe(pd.DataFrame(st.session_state.alerts), hide_index=True, width="stretch")
    if st.button(t("clear")):
        st.session_state.alerts = []
        st.session_state.sent_keys = set()
        st.rerun()
else:
    st.info(t("no_actions"))

st.markdown(f"### {t('h_stock')}")
st.dataframe(pd.DataFrame([{"Hospital": h["name"],
                            t("need_antivenom_vials"): ui.stock_status(h["stock"]["antivenom_vials"]),
                            t("need_anti_rabies_vaccine"): ui.stock_status(h["stock"]["anti_rabies_vaccine"]),
                            t("need_cardiac_care"): ui.stock_status(h["stock"]["cardiac_care"])}
                           for h in data.hospitals()]), hide_index=True, width="stretch")

st.markdown(f"### {t('p_stock')}")
st.dataframe(pd.DataFrame([{"Pharmacy": ph["name"], **{k.title(): ui.stock_status(v) for k, v in ph["stock"].items()}}
                           for ph in data.pharmacies()]), hide_index=True, width="stretch")
