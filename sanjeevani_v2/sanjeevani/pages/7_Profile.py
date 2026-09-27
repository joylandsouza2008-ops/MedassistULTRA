import hashlib

import pandas as pd
import streamlit as st

from core import notify, profile, ui
from core.i18n import t

ui.header(t("prof_title"), t("prof_intro"), "prof")

p = profile.get()
BLOOD = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ---------- profile photo ----------
st.markdown(f"### 📷 {t('prof_photo')}")
pending = st.session_state.get("photo_pending")          # None = unchanged, "" = removed, "data:..." = new
shown = p.get("photo", "") if pending is None else pending
ph1, ph2 = st.columns([1, 3])
with ph1:
    st.markdown(profile.avatar_html(150, photo=shown, name=p.get("name")), unsafe_allow_html=True)
with ph2:
    if st.toggle(t("use_camera"), key="photo_cam"):
        pic = st.camera_input(t("prof_photo_camera"), key="photo_cam_input")
    else:
        pic = st.file_uploader(t("prof_photo_upload"), type=["jpg", "jpeg", "png", "webp"], key="photo_upload")
    if pic is not None:
        pic_id = hashlib.md5(pic.getvalue()).hexdigest()
        if st.session_state.get("photo_pic_id") != pic_id:          # only process a new picture once
            st.session_state.photo_pic_id = pic_id
            try:
                st.session_state.photo_pending = profile.process_photo(pic.getvalue())
                st.rerun()
            except Exception:
                st.warning(t("prof_photo_bad"))
    if st.session_state.get("photo_pending"):
        st.caption("👉 " + t("prof_photo_hint"))
    if shown and st.button(t("prof_photo_remove")):
        st.session_state.photo_pending = ""
        st.rerun()

# ---------- about you ----------
st.markdown(f"### {t('prof_about')}")
c1, c2, c3 = st.columns([3, 1, 2])
name = c1.text_input(t("prof_name"), value=p.get("name", ""))
age = c2.text_input(t("prof_age"), value=str(p.get("age", "")))
phone = c3.text_input(t("prof_phone"), value=p.get("phone", ""))
c4, c5 = st.columns([3, 1])
village = c4.text_input(t("prof_village"), value=p.get("village", ""))
blood = c5.selectbox(t("prof_blood"), BLOOD, index=BLOOD.index(p.get("blood", "")) if p.get("blood", "") in BLOOD else 0)
notes = st.text_area(t("prof_notes"), value=p.get("notes", ""), height=80)

# ---------- emergency contacts (no limit) ----------
st.markdown(f"### 🆘 {t('prof_contacts')}")
st.caption(t("prof_contacts_help"))
rows = p.get("contacts") or [{"name": "", "relation": "", "phone": ""}]
table = st.data_editor(
    pd.DataFrame(rows, columns=["name", "relation", "phone"]),
    num_rows="dynamic", width="stretch", key="contacts_editor",
    column_config={
        "name": st.column_config.TextColumn(t("prof_name")),
        "relation": st.column_config.TextColumn(t("col_relation")),
        "phone": st.column_config.TextColumn(t("col_phone")),
    },
)

# ---------- save ----------
if st.button(t("prof_save"), type="primary", width="stretch"):
    contacts, bad = [], []
    for r in table.to_dict("records"):
        r = {k: ("" if v is None or (isinstance(v, float) and v != v) else str(v).strip()) for k, v in r.items()}
        if not (r["name"] or r["phone"]):
            continue
        norm = notify.normalize(r["phone"])
        if len(norm.lstrip("+")) < 10:
            bad.append(r["phone"] or r["name"])
            continue
        contacts.append({"name": r["name"] or "Family", "relation": r["relation"], "phone": norm})
    photo = p.get("photo", "") if st.session_state.get("photo_pending") is None else st.session_state.photo_pending
    new = {"name": name.strip(), "age": age.strip(), "phone": notify.normalize(phone) if phone.strip() else "",
           "village": village.strip(), "blood": blood, "notes": notes.strip(), "photo": photo, "contacts": contacts}
    st.session_state.photo_pending = None
    kept = profile.save(new)
    st.success(t("prof_saved", n=len(contacts)))
    if not kept:
        st.caption(t("prof_session_only"))
    if bad:
        st.warning(t("prof_bad_phone", nums=", ".join(bad)))

# ---------- test SOS to everyone ----------
st.divider()
people = notify.contacts()
if st.button(t("prof_test"), width="stretch"):
    if not people:
        st.warning(t("prof_test_none"))
    elif not notify.auto_ready():
        st.caption("ℹ️ " + t("sos_auto_off"))
    else:
        results = notify.send_sos("MEDX TEST: this is only a test of the emergency alert. No action needed.",
                                  "", call=False)
        for who, kind, good, err in results:
            if good:
                st.success(t({"sms": "sos_sms_ok", "call": "sos_call_ok", "alarm": "sos_alarm_ok"}[kind], name=who))
            else:
                st.warning(t("sos_fail", name=who, err=err))

# one-tap buttons for every contact
for c in people:
    lk = notify.links(c["phone"], "Hello from MedX")
    b1, b2 = st.columns(2)
    b1.link_button(t("sos_call_btn", name=c["name"]), lk["call"], width="stretch")
    b2.link_button(f"🟢 WhatsApp {c['name']}", lk["whatsapp"], width="stretch")

st.caption("🔒 " + t("prof_note"))
