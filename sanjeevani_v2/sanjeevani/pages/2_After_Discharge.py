from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import ui, ai, data, meds, state, voice
from core.i18n import slot, t

ui.header(t("dis_title"), t("dis_intro"))

sample = data.load("sample_discharge")

# ---------- 1. Read the prescription ----------
st.markdown(f"### {t('s1')}")
c1, c2 = st.columns([2, 1])
with c1:
    photo = st.file_uploader(t("upload_rx"), type=["jpg", "jpeg", "png", "webp"])
    if photo and st.button(t("read_ai"), type="primary"):
        if not ai.available():
            st.warning(t("no_key"))
        else:
            with st.spinner(t("reading")):
                try:
                    result = ai.read_prescription(photo)
                except Exception:
                    result = None
                    st.error(t("ai_err"))
            if result and result.get("medicines"):
                st.session_state.discharge_meds = result["medicines"]
                st.session_state.follow_up_days = result.get("follow_up_days") or 7
            elif result is not None:
                st.error(t("rx_unclear"))
with c2:
    if st.button(t("use_sample"), width="stretch"):
        st.session_state.discharge_meds = sample["medicines"]
        st.session_state.follow_up_days = sample["follow_up_days"]
    st.caption(f"{sample['patient']}: {sample['reason']}")

if "discharge_meds" not in st.session_state:
    st.info(t("upload_first"))
    st.stop()

st.markdown(f"**{t('check_list')}**")
df = pd.DataFrame(st.session_state.discharge_meds)
for col in ["brand", "salt", "strength", "pattern", "days"]:
    if col not in df.columns:
        df[col] = None
edited = st.data_editor(
    df[["brand", "salt", "strength", "pattern", "days"]],
    num_rows="dynamic", width="stretch", key="med_editor",
    column_config={
        "brand": st.column_config.TextColumn(t("col_brand")),
        "salt": st.column_config.TextColumn(t("col_salt")),
        "strength": st.column_config.TextColumn(t("col_strength")),
        "pattern": st.column_config.TextColumn(t("col_pattern")),
        "days": st.column_config.NumberColumn(t("col_days")),
    },
)
med_list = [meds.fill_salt(meds.clean(r)) for r in edited.to_dict("records")]
med_list = [m for m in med_list if m.get("brand")]

# ---------- 2. Timetable ----------
st.markdown(f"### {t('s2')}")
plan = meds.schedule(med_list)
spoken = []
cols = st.columns(3)
for col, (slot_name, items) in zip(cols, plan.items()):
    with col:
        st.markdown(f"**{slot(slot_name)}**")
        if not items:
            st.caption(t("nothing"))
        for m in items:
            days = f", {t('n_days', n=int(m['days']))}" if m.get("days") else ""
            st.markdown(f"- {m['brand']} × {m['count']}{days}")
        if items:
            spoken.append(f"{slot(slot_name)}: {', '.join(m['brand'] for m in items)}.")
voice.listen_button(" ".join(spoken), "timetable")

for salt, items in meds.duplicates(med_list).items():
    st.warning(t("dup_found", salt=salt.title(), brands=", ".join(i["brand"] for i in items)))

# ---------- 3. Generics ----------
st.markdown(f"### {t('s3')}")
rows = meds.generic_savings(med_list)
table = pd.DataFrame(rows).rename(columns={
    "Prescribed": t("col_prescribed"), "Generic option": t("col_generic"),
    "Brand price / tab": t("col_bprice"), "Generic price / tab": t("col_gprice"),
    "You save for course": t("col_save")})
table[t("col_generic")] = table[t("col_generic")].replace("Not found in demo list", t("not_in_list"))
st.dataframe(table, width="stretch", hide_index=True)
total = sum(r["You save for course"] or 0 for r in rows)
if total:
    msg = t("savings", n=total)
    st.success(msg)
    voice.listen_button(msg, "savings")

# ---------- 4. Pharmacy ----------
st.markdown(f"### {t('s4')}")
village = st.selectbox(t("village"), [v["name"] for v in data.villages()], key="dis_village")
v = data.village(village)
shop = meds.pharmacy_with([m.get("salt") for m in med_list], v["lat"], v["lon"])
if shop:
    st.write(t("shop_has", name=shop["name"], km=shop["km"]))
    if st.button(t("reserve")):
        state.add_alert("Pharmacy reservation", shop["name"],
                        f"Keep ready for pickup: {', '.join(m['brand'] for m in med_list)}.")
        msg = t("reserved", name=shop["name"])
        st.success(msg)
        voice.say(msg)
else:
    st.warning(t("no_shop"))

# ---------- 5. Follow-up ----------
st.markdown(f"### {t('s5')}")
default_day = date.today() + timedelta(days=int(st.session_state.get("follow_up_days") or 7))
fu = st.date_input(t("fu_date"), value=default_day)
if st.button(t("book_fu")):
    state.add_alert("Follow-up booked", "Hospital OPD + family",
                    f"Follow-up visit on {fu.strftime('%d %b %Y')}. Reminder 1 day before.")
    msg = t("fu_booked", d=fu.strftime("%d-%m-%Y"))
    st.success(msg)
    voice.say(msg)
