from datetime import date

import pandas as pd
import streamlit as st

from core import notify, ui, ai, data, meds, state, voice
from core.i18n import slot, t

p = data.load("elderly_profile")
first_name = p["name"].split(" (")[0]
family = p["family_contact"]["name"]
v = data.village(p["village"])
med_list = p["medicines"]

profile = t("eld_profile", name=p["name"], age=p["age"], village=p["village"], family=family,
            n=len(med_list), d=len({m["doctor"] for m in med_list}))
ui.header(t("eld_title"), profile)

# ---------- HELP button ----------
if st.button(t("help_btn"), type="primary", width="stretch"):
    st.session_state.em_text = "Elderly person pressed HELP: chest pain"
    st.session_state.em_place = st.session_state.gps["name"] if "gps" in st.session_state else p["village"]
    st.session_state.em_go = True
    st.switch_page("pages/1_Emergency.py")
st.caption(t("help_caption"))

tab_today, tab_photo, tab_missed, tab_dup, tab_stock = st.tabs(
    [t("tab_today"), t("tab_photo"), t("tab_missed"), t("tab_dup"), t("tab_stock")])

# ---------- 1. Daily voice check-in ----------
with tab_today:
    st.write(t("today_intro"))
    for slot_name, items in meds.schedule(med_list).items():
        st.markdown(f"**{slot(slot_name)}**")
        for m in items:
            key = f"{m['brand']}|{slot_name}"
            done = st.session_state.taken_today.get(key)
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"{'✅' if done else '⏳'} {m['brand']} ({m['salt']} {m['strength']})")
            with c2:
                voice.listen_button(t("call_script", name=first_name, med=m["brand"]), key)
            if not done:
                if c3.button(t("yes_taken"), key="y" + key):
                    st.session_state.taken_today[key] = True
                    st.rerun()
                if c4.button(t("not_yet"), key="n" + key):
                    state.add_alert("Family alert", family,
                                    f"{p['name']} said she has not taken {m['brand']} ({slot_name}).")
                    st.toast(t("fam_informed", family=family))

# ---------- 2. Photo check before taking ----------
with tab_photo:
    st.write(t("photo_intro"))
    options = [(m["brand"], s) for s, items in meds.schedule(med_list).items() for m in items]
    exp_brand, exp_slot = st.selectbox(t("which_due"), options,
                                       format_func=lambda o: f"{o[0]}  ·  {slot(o[1])}")
    expected = next(m for m in med_list if m["brand"] == exp_brand)

    if st.toggle(t("use_camera"), value=False):
        photo = st.camera_input(t("show_strip"))
    else:
        photo = st.file_uploader(t("upload_strip"), type=["jpg", "jpeg", "png", "webp"], key="strip_up")

    seen = None
    if photo is not None and ai.available():
        with st.spinner(t("reading")):
            try:
                seen = ai.read_strip(photo)
            except Exception:
                st.error(t("ai_err"))
    if seen is None:
        st.caption(t("demo_choose"))
        loose = t("loose")
        demo_pick = st.selectbox(t("strip_is"), [m["brand"] for m in med_list] + [loose])
        expired = st.checkbox(t("expired_cb"))
        if demo_pick == loose:
            seen = {"readable": False}
        else:
            k = next(m for m in med_list if m["brand"] == demo_pick)
            seen = {"readable": True, "brand": k["brand"], "salt": k["salt"],
                    "expiry": "01/2024" if expired else "12/2027"}

    if st.button(t("check_btn"), type="primary"):
        slot_key = f"{expected['brand']}|{exp_slot}"
        seen_salt = (seen.get("salt") or (data.find_medicine(seen.get("brand")) or {}).get("salt") or "").lower()
        seen_brand = (seen.get("brand") or "").lower()

        expiry_passed = False
        if seen.get("expiry"):
            try:
                mm, yyyy = seen["expiry"].split("/")
                expiry_passed = (int(yyyy), int(mm)) < (date.today().year, date.today().month)
            except ValueError:
                pass

        if not seen.get("readable"):
            msg, kind = t("r_unread"), "warning"
        elif expiry_passed:
            msg, kind = t("r_expired", d=seen["expiry"]), "error"
            state.add_alert("Family alert", family, f"Expired {seen.get('brand')} strip found. Please replace it.")
        elif st.session_state.taken_today.get(slot_key):
            msg, kind = t("r_already", med=expected["brand"]), "error"
        elif seen_brand == expected["brand"].lower():
            msg, kind = t("r_ok", med=expected["brand"]), "success"
            st.session_state.taken_today[slot_key] = True
        elif seen_salt == expected["salt"].lower():
            msg, kind = t("r_same_salt", seen=seen.get("brand"), med=expected["brand"]), "warning"
        else:
            msg, kind = t("r_wrong", seen=seen.get("brand"), med=expected["brand"]), "error"
            state.add_alert("Family alert", family,
                            f"{p['name']} almost took {seen.get('brand')} instead of {expected['brand']}.")
        getattr(st, kind)(msg)
        voice.play(msg)   # always read the result aloud, even if she checks the same thing twice

# ---------- 3. Missed doses ----------
with tab_missed:
    log = p["dose_log"]
    st.dataframe(pd.DataFrame(log).rename(columns={"when": t("col_when"), "brand": t("col_brand"),
                                                    "taken": t("col_taken")}),
                 hide_index=True, width="stretch")
    streak = 0
    for entry in reversed(log):
        if entry["taken"]:
            break
        streak += 1
    if streak >= 2:
        st.error(t("missed_streak", n=streak, med=log[-1]["brand"]))
        state.add_alert("Family alert", family,
                        f"{p['name']} has missed {streak} doses of {log[-1]['brand']} in a row. Please call her.",
                        key="missed-streak")
        if notify.auto_ready() and "missed-sms" not in st.session_state.sent_keys:
            st.session_state.sent_keys.add("missed-sms")
            notify.send_sos(f"Sanjeevani: {p['name']} has missed {streak} doses of {log[-1]['brand']} in a row. "
                            f"Please call her.", "", call=False)
        st.success(t("missed_sent", family=family))
    else:
        st.success(t("no_gaps"))

# ---------- 4. Duplicate medicines ----------
with tab_dup:
    st.write(t("dup_intro"))
    st.dataframe(pd.DataFrame(med_list)[["brand", "salt", "strength", "pattern", "doctor"]].rename(columns={
        "brand": t("col_brand"), "salt": t("col_salt"), "strength": t("col_strength"),
        "pattern": t("col_pattern"), "doctor": t("col_doctor")}),
        hide_index=True, width="stretch")
    dups = meds.duplicates(med_list)
    if not dups:
        st.success(t("no_dup"))
    for salt, items in dups.items():
        who = "; ".join(t("from_doc", brand=i["brand"], doctor=i["doctor"]) for i in items)
        msg = t("dup_warn", salt=salt.title(), who=who)
        st.error(msg)
        voice.listen_button(msg, f"dup-{salt}")
        state.add_alert("Pharmacist review", "Local pharmacist",
                        f"Possible duplicate {salt.title()} for {p['name']}. Please confirm with doctor.",
                        key=f"dup-{salt}")
        st.info(t("dup_sent"))

# ---------- 5. Running out ----------
with tab_stock:
    st.dataframe(pd.DataFrame([{t("col_brand"): m["brand"], t("col_left"): m["tablets_left"],
                                t("col_perday"): meds.per_day(m["pattern"]),
                                t("col_daysleft"): meds.days_left(m)} for m in med_list]),
                 hide_index=True, width="stretch")
    for m in med_list:
        left = meds.days_left(m)
        if left is not None and left <= 5:
            msg = t("runs_out", med=m["brand"], n=left)
            st.warning(msg)
            voice.listen_button(msg, f"out-{m['brand']}")
            shop = meds.pharmacy_with([m["salt"]], v["lat"], v["lon"])
            if shop:
                st.write(t("nearest_shop", name=shop["name"], km=shop["km"]))
                if st.button(t("reserve_med", med=m["brand"]), key="res" + m["brand"]):
                    state.add_alert("Pharmacy reservation", shop["name"],
                                    f"Reserve {m['brand']} ({m['salt']}) for {p['name']}.")
                    state.add_alert("Family alert", family,
                                    f"{m['brand']} reserved at {shop['name']}. Please pick it up.")
                    st.success(t("reserved_fam"))
