import hashlib

import pandas as pd
import streamlit as st

from core import ui, ai, sar, state, voice
from core.i18n import t

ui.header(t("sar_title"), t("sar_intro"), "sar")

event, demo_reports = sar.load_demo()
places = event["places"]
st.session_state.setdefault("sar_reports", demo_reports)
st.session_state.setdefault("sar_text", "")
reports = st.session_state.sar_reports
zones = sar.build_zones(reports, places)

st.caption(f"📍 {event['event']}")

# ---------- headline numbers ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("m_reports"), len(reports))
c2.metric(t("m_zones"), len(zones))
c3.metric(t("m_people"), sum(z["people"] for z in zones))
c4.metric(t("m_critical"), sum(1 for z in zones if z["level"] == "critical"))

# ---------- map ----------
dots = pd.DataFrame([{"lat": r["lat"], "lon": r["lon"], "color": sar.LEVEL_COLORS[r["level"]],
                      "size": 120 + r["score"] * 25} for r in reports])
st.map(dots, latitude="lat", longitude="lon", color="color", size="size")
st.caption(t("sar_map_caption"))

# ---------- priority list ----------
st.markdown(f"### {t('sar_priority')}")
if zones:
    top = zones[0]
    voice.say(t("sar_top_say", place=top["place"],
                needs=", ".join(t("flag_" + f) for f in top["flags"][:3]),
                teams=", ".join(t(x) for x in top["teams"])))

badge = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
for rank, z in enumerate(zones, 1):
    with st.container(border=True):
        head, btn = st.columns([4, 1])
        with head:
            st.markdown(f"#### {rank}. {badge[z['level']]} {z['place']} · {t('lvl_' + z['level'])}")
            st.caption(t("zone_stats", n=len(z["reports"]), people=z["people"]))
            st.write(f"**{t('zone_needs')}:** " + ", ".join(t("flag_" + f) for f in z["flags"]))
            if z["teams"]:
                st.write(f"**{t('zone_send')}:** " + ", ".join(t(x) for x in z["teams"]))
            st.caption(t("zone_hospital", name=z["hospital"]["name"], km=z["hospital"]["km"]))
            if z["antivenom"]:
                st.caption("🐍 " + t("zone_antivenom", name=z["antivenom"]["name"], km=z["antivenom"]["km"]))
        with btn:
            key = f"sar-{z['place']}-{'-'.join(z['report_ids'])}"
            if key in st.session_state.sent_keys:
                st.success("✅")
            elif st.button(t("dispatch"), key=key, type="primary" if z["level"] == "critical" else "secondary",
                           width="stretch"):
                state.add_alert("Rescue dispatch", "District control room",
                                f"Send {', '.join(t(x) for x in z['teams']) or 'survey team'} to {z['place']} "
                                f"({len(z['reports'])} reports, ~{z['people']} people).", key=key)
                if z["antivenom"]:
                    state.add_alert("Hospital alert", z["antivenom"]["name"],
                                    f"Snakebite case expected from {z['place']} (flood zone). Keep antivenom ready.")
                st.toast(t("dispatched", place=z["place"]))
                st.rerun()
        with st.expander(t("zone_reports")):
            for r in z["reports"]:
                st.markdown(f"- `{r['time']}` {badge[r['level']]} ({t('src_' + r['source'])}) {r['text']}")
st.caption(t("sar_safe"))

# ---------- add a new report ----------
st.markdown(f"### {t('sar_add')}")
audio = st.audio_input(t("record_sar"))
if audio is not None:
    audio_id = hashlib.md5(audio.getvalue()).hexdigest()
    if st.session_state.get("sar_last_audio") != audio_id:
        st.session_state.sar_last_audio = audio_id
        try:
            heard = voice.transcribe(audio)
        except Exception:
            heard = None
        if heard:
            st.session_state.sar_text = heard
        else:
            st.warning(t("not_heard"))

a, b = st.columns(2)
place_name = a.selectbox(t("sar_where"), [p["name"] for p in places])
source = b.selectbox(t("sar_source"), ["call", "whatsapp", "sms"], format_func=lambda s: t("src_" + s))
text = st.text_area(t("sar_text"), key="sar_text", height=80)

if st.button(t("sar_add_btn"), type="primary") and text.strip():
    flags = people = None
    if ai.available():
        try:
            res = ai.classify_sar_report(text)
            if res:
                flags, people = res.get("flags"), res.get("people")
        except Exception:
            pass
    p = next(x for x in places if x["name"] == place_name)
    n = len(reports) + 1
    # small offset so the new dot doesn't sit exactly on top of another
    new = {"id": f"R{n}", "source": source, "time": "now", "text": text,
           "lat": p["lat"] + 0.0004 * (n % 5), "lon": p["lon"] - 0.0004 * (n % 3),
           **sar.analyze(text, flags, people)}
    st.session_state.sar_reports = reports + [new]
    msg = t("sar_added", level=t("lvl_" + new["level"]))
    st.toast(msg)
    voice.say(msg)
    st.rerun()

with st.expander(t("all_reports")):
    st.dataframe(pd.DataFrame([{"ID": r["id"], "⏱": r["time"], "📡": t("src_" + r["source"]),
                                "📝": r["text"], "⚠️": t("lvl_" + r["level"]), "🔢": r["score"]}
                               for r in reports]), hide_index=True, width="stretch")
