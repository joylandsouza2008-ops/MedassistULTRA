"""Emergency agent: understand the message -> find the right hospital ->
send alerts -> guide first aid (on screen and by voice)."""
import html

import pandas as pd
import streamlit as st

from core import ai, data, geo, live, state, ui, voice
from core.i18n import lang, t

# What each emergency needs, and words that point to it (English, Kannada, Hindi)
EMERGENCIES = {
    "snakebite": {"needs": "antivenom_vials",
                  "keywords": ["snake", "cobra", "viper", "krait", "haavu", "havu", "ಹಾವು",
                               "saanp", "saap", "sanp", "साँप", "सांप", "सांप"]},
    "dog_bite": {"needs": "anti_rabies_vaccine",
                 "keywords": ["dog", "naayi", "nayi", "ನಾಯಿ", "kutta", "कुत्ता", "कुत्ते",
                              "monkey", "ಮಂಗ", "बंदर", "animal bite"]},
    "chest_pain": {"needs": "cardiac_care",
                   "keywords": ["chest", "heart", "ede novu", "ಎದೆ", "ಹೃದಯ", "seene", "सीने", "सीना",
                                "दिल", "breathless", "help", "ಸಹಾಯ", "मदद"]},
}

# Screen + voice text for each emergency, in each language
EM_TEXT = {
    "snakebite": {
        "en": {"label": "Snakebite", "need": "antivenom",
               "do": ["Keep the person calm and lying still. Movement spreads venom faster.",
                      "Keep the bitten arm or leg still.",
                      "Remove rings, bangles, anklets and tight clothes near the bite.",
                      "Note the time of the bite and tell the doctor.",
                      "Go to the hospital shown here right away. Antivenom is the only real treatment."],
               "dont": ["Don't cut the wound or try to suck out the venom.",
                        "Don't tie a tight cloth or rope.",
                        "Don't put ice, herbs or any home remedy on the bite.",
                        "Don't waste time going to a traditional healer.",
                        "Don't try to catch or kill the snake."]},
        "kn": {"label": "ಹಾವು ಕಡಿತ", "need": "ಆಂಟಿವೆನಮ್ (ಹಾವಿನ ವಿಷದ ಔಷಧಿ)",
               "do": ["ವ್ಯಕ್ತಿಯನ್ನು ಶಾಂತವಾಗಿ, ಅಲುಗಾಡದಂತೆ ಮಲಗಿಸಿ. ಚಲನೆಯಿಂದ ವಿಷ ಬೇಗ ಹರಡುತ್ತದೆ.",
                      "ಕಚ್ಚಿದ ಕೈ ಅಥವಾ ಕಾಲನ್ನು ಅಲುಗಾಡಿಸದೆ ಇಡಿ.",
                      "ಕಚ್ಚಿದ ಜಾಗದ ಹತ್ತಿರದ ಉಂಗುರ, ಬಳೆ, ಕಾಲ್ಗೆಜ್ಜೆ, ಬಿಗಿ ಬಟ್ಟೆ ತೆಗೆಯಿರಿ.",
                      "ಕಚ್ಚಿದ ಸಮಯವನ್ನು ನೆನಪಿಟ್ಟು ವೈದ್ಯರಿಗೆ ತಿಳಿಸಿ.",
                      "ಇಲ್ಲಿ ತೋರಿಸಿದ ಆಸ್ಪತ್ರೆಗೆ ತಕ್ಷಣ ಹೋಗಿ. ಆಂಟಿವೆನಮ್ ಒಂದೇ ನಿಜವಾದ ಚಿಕಿತ್ಸೆ."],
               "dont": ["ಗಾಯವನ್ನು ಕೊಯ್ಯಬೇಡಿ, ವಿಷ ಹೀರಬೇಡಿ.",
                        "ಬಿಗಿಯಾಗಿ ಬಟ್ಟೆ ಅಥವಾ ಹಗ್ಗ ಕಟ್ಟಬೇಡಿ.",
                        "ಐಸ್, ಗಿಡಮೂಲಿಕೆ ಅಥವಾ ಮನೆಮದ್ದು ಹಚ್ಚಬೇಡಿ.",
                        "ನಾಟಿ ವೈದ್ಯರ ಬಳಿ ಹೋಗಿ ಸಮಯ ವ್ಯರ್ಥ ಮಾಡಬೇಡಿ.",
                        "ಹಾವನ್ನು ಹಿಡಿಯಲು ಅಥವಾ ಕೊಲ್ಲಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ."]},
        "hi": {"label": "साँप का काटना", "need": "एंटी-वेनम (साँप के ज़हर की दवा)",
               "do": ["व्यक्ति को शांत रखें और लिटाकर रखें। हिलने से ज़हर तेज़ी से फैलता है।",
                      "काटे गए हाथ या पैर को हिलने न दें।",
                      "काटे के पास की अंगूठी, चूड़ी, पायल और तंग कपड़े उतार दें।",
                      "काटने का समय याद रखें और डॉक्टर को बताएँ।",
                      "यहाँ दिखाए गए अस्पताल में तुरंत जाएँ। एंटी-वेनम ही असली इलाज है।"],
               "dont": ["घाव को काटें नहीं, ज़हर चूसने की कोशिश न करें।",
                        "कसकर कपड़ा या रस्सी न बाँधें।",
                        "बर्फ़, जड़ी-बूटी या घरेलू नुस्खा न लगाएँ।",
                        "झाड़-फूँक वाले के पास जाकर समय बर्बाद न करें।",
                        "साँप को पकड़ने या मारने की कोशिश न करें।"]},
    },
    "dog_bite": {
        "en": {"label": "Dog / animal bite", "need": "anti-rabies vaccine",
               "do": ["Wash the wound with soap and running water for 15 minutes.",
                      "Go to the hospital shown here today for the anti-rabies vaccine."],
               "dont": ["Don't apply chilli, turmeric, oil or mud on the wound.",
                        "Don't wait to see if the dog gets sick. Get the vaccine today."]},
        "kn": {"label": "ನಾಯಿ / ಪ್ರಾಣಿ ಕಡಿತ", "need": "ರೇಬೀಸ್ ಲಸಿಕೆ",
               "do": ["ಗಾಯವನ್ನು ಸೋಪು ಮತ್ತು ಹರಿಯುವ ನೀರಿನಿಂದ 15 ನಿಮಿಷ ತೊಳೆಯಿರಿ.",
                      "ರೇಬೀಸ್ ಲಸಿಕೆಗಾಗಿ ಇಂದೇ ಇಲ್ಲಿ ತೋರಿಸಿದ ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಿ."],
               "dont": ["ಗಾಯಕ್ಕೆ ಮೆಣಸು, ಅರಿಶಿನ, ಎಣ್ಣೆ ಅಥವಾ ಮಣ್ಣು ಹಚ್ಚಬೇಡಿ.",
                        "ನಾಯಿಗೆ ಕಾಯಿಲೆ ಬರುತ್ತದೆಯೇ ಎಂದು ಕಾಯಬೇಡಿ. ಇಂದೇ ಲಸಿಕೆ ಹಾಕಿಸಿ."]},
        "hi": {"label": "कुत्ते / जानवर का काटना", "need": "एंटी-रेबीज़ टीका",
               "do": ["घाव को साबुन और बहते पानी से 15 मिनट धोएँ।",
                      "एंटी-रेबीज़ टीके के लिए आज ही यहाँ दिखाए गए अस्पताल जाएँ।"],
               "dont": ["घाव पर मिर्च, हल्दी, तेल या मिट्टी न लगाएँ।",
                        "कुत्ते के बीमार होने का इंतज़ार न करें। आज ही टीका लगवाएँ।"]},
    },
    "chest_pain": {
        "en": {"label": "Chest pain / heart emergency", "need": "heart emergency care",
               "do": ["Call 108 for an ambulance.",
                      "Help the person sit down and rest. Loosen tight clothes.",
                      "Keep the medicine list ready to show the doctor."],
               "dont": ["Don't let the person walk, climb stairs or drive.",
                        "Don't give any medicine unless a doctor has told you to."]},
        "kn": {"label": "ಎದೆ ನೋವು / ಹೃದಯ ತುರ್ತು", "need": "ಹೃದಯ ತುರ್ತು ಚಿಕಿತ್ಸೆ",
               "do": ["ಆಂಬುಲೆನ್ಸ್‌ಗಾಗಿ 108ಕ್ಕೆ ಕರೆ ಮಾಡಿ.",
                      "ವ್ಯಕ್ತಿಯನ್ನು ಕೂರಿಸಿ ವಿಶ್ರಾಂತಿ ನೀಡಿ. ಬಿಗಿ ಬಟ್ಟೆ ಸಡಿಲಗೊಳಿಸಿ.",
                      "ಔಷಧಿ ಪಟ್ಟಿಯನ್ನು ವೈದ್ಯರಿಗೆ ತೋರಿಸಲು ಸಿದ್ಧವಾಗಿಡಿ."],
               "dont": ["ವ್ಯಕ್ತಿಯನ್ನು ನಡೆಯಲು, ಮೆಟ್ಟಿಲು ಹತ್ತಲು ಅಥವಾ ವಾಹನ ಓಡಿಸಲು ಬಿಡಬೇಡಿ.",
                        "ವೈದ್ಯರು ಹೇಳದ ಯಾವುದೇ ಔಷಧಿ ಕೊಡಬೇಡಿ."]},
        "hi": {"label": "सीने में दर्द / दिल की आपात स्थिति", "need": "दिल का आपातकालीन इलाज",
               "do": ["एम्बुलेंस के लिए 108 पर कॉल करें।",
                      "व्यक्ति को बैठाकर आराम कराएँ। तंग कपड़े ढीले करें।",
                      "दवाओं की सूची डॉक्टर को दिखाने के लिए तैयार रखें।"],
               "dont": ["व्यक्ति को चलने, सीढ़ियाँ चढ़ने या गाड़ी चलाने न दें।",
                        "डॉक्टर के कहे बिना कोई दवा न दें।"]},
    },
}


def text_for(etype):
    return EM_TEXT[etype].get(lang(), EM_TEXT[etype]["en"])


NEEDS = ["antivenom_vials", "anti_rabies_vaccine", "cardiac_care", "general"]
FAR_KM = 60  # beyond this, a partner hospital is too far to recommend


def keyword_detect(text):
    low = (text or "").lower()
    for etype, info in EMERGENCIES.items():
        if any(k in low for k in info["keywords"]):
            return etype
    return None


def detect(text):
    """Emergency type only (used by the API). AI if available, else keywords."""
    if not text or not text.strip():
        return None, ""
    if ai.available():
        try:
            result = ai.classify_emergency(text)
            if result and result.get("type") in EMERGENCIES:
                return result["type"], result.get("summary", "")
        except Exception:
            pass
    return keyword_detect(text), ""


def analyze(text, lang_code, place_name):
    """Understand ANYTHING the person said and build a tailored answer.
    With an AI key: the NVIDIA model answers their exact situation in their language.
    Without: keyword rules for snakebite / dog bite / chest pain, else 'call 108'."""
    if ai.available():
        try:
            r = ai.emergency_assistant(text, lang_code, place_name)
            if r:
                typ = r.get("type") if r.get("type") in EMERGENCIES else "other"
                needs = r.get("needs") if r.get("needs") in NEEDS else \
                    (EMERGENCIES[typ]["needs"] if typ in EMERGENCIES else "general")
                urgency = r.get("urgency") if r.get("urgency") in ("emergency", "urgent", "routine") else "urgent"
                return {"type": typ, "needs": needs, "urgency": urgency, "summary": r.get("summary", ""),
                        "reply": str(r["reply"]), "do": [str(x) for x in (r.get("do") or [])][:4],
                        "dont": [str(x) for x in (r.get("dont") or [])][:3], "source": "ai"}
        except Exception:
            pass
    typ = keyword_detect(text)
    if typ:
        tx = text_for(typ)
        return {"type": typ, "needs": EMERGENCIES[typ]["needs"], "urgency": "emergency", "summary": "",
                "reply": t("rules_reply", label=tx["label"]), "do": tx["do"], "dont": tx["dont"],
                "source": "rules"}
    return {"type": "other", "needs": "general", "urgency": "urgent", "summary": "",
            "reply": t("unknown_em"), "do": [], "dont": [], "source": "rules"}


def find_hospitals(need, lat, lon):
    """Nearest partner hospital overall vs nearest one that has what is needed."""
    ranked = geo.sort_by_distance(data.hospitals(), lat, lon)
    nearest_any = ranked[0]
    if need == "general":
        return nearest_any, nearest_any
    return nearest_any, next((h for h in ranked if h["stock"].get(need, 0) > 0), None)


def best_hospitals(etype, lat, lon):
    return find_hospitals(EMERGENCIES[etype]["needs"], lat, lon)


def render_result(res, loc, family_contact="Family member"):
    known = res["type"] in EM_TEXT
    label = text_for(res["type"])["label"] if known else t("general_label")
    need = res["needs"]
    need_label = t("need_" + need)
    kind = {"emergency": "danger", "urgent": "warn", "routine": "info"}[res["urgency"]]

    # 1. The answer to what they actually said
    ui.card(kind, f"{t('urg_' + res['urgency'])} · {label}", res["reply"])
    if res["urgency"] != "routine":
        st.link_button(t("call_108"), "tel:108", use_container_width=True, type="primary")
    if res["do"] or res["dont"]:
        c1, c2 = st.columns(2)
        with c1:
            if res["do"]:
                ui.list_card("ok", f"✅ {t('do')}", res["do"])
        with c2:
            if res["dont"]:
                ui.list_card("danger", f"❌ {t('dont')}", res["dont"])

    # 2. Where to go
    spoken = [res["reply"]]
    nearest_any, ok = find_hospitals(need, loc["lat"], loc["lon"])
    if ok is None or ok["km"] > FAR_KM:
        ui.card("warn", f"🏥 {t('m_hospital')}", t("far_away"))
        spoken.append(t("far_away"))
        ok = None
    else:
        if need != "general" and nearest_any["id"] != ok["id"]:
            warn = t("nearest_lacks", name=nearest_any["name"], km=nearest_any["km"], need=need_label)
            ui.card("warn", f"⚠️ {nearest_any['name']}", warn)
            spoken.append(warn)
        if need == "general":
            go = t("go_to_general", name=ok["name"], km=ok["km"], eta=ok["eta"])
        else:
            go = t("go_to", name=ok["name"], km=ok["km"], eta=ok["eta"], need=need_label, stock=t("in_stock"))
        ui.card("ok", f"🏥 {ok['name']}", go, extra_html=ui.pill(t("partner_label")))
        spoken.append(go)

        if res["urgency"] in ("emergency", "urgent"):
            key = f"{res['type']}-{loc['name']}-{ok['id']}"
            state.add_alert("Hospital alert", ok["name"],
                            f"Patient coming from {loc['name']} ({res['summary'] or label}), ETA {ok['eta']} min.",
                            key=key + "-h")
            state.add_alert("Ambulance (108)", "Ambulance control",
                            f"Pickup at {loc['name']}, drop at {ok['name']}.", key=key + "-a")
            state.add_alert("Family alert", family_contact,
                            f"Emergency at {loc['name']}. Going to {ok['name']}.", key=key + "-f")
            m1, m2, m3 = st.columns(3)
            m1.metric(t("m_hospital"), t("m_alerted"))
            m2.metric(t("m_ambulance"), t("m_requested"))
            m3.metric(t("m_family"), t("m_informed"))

    # 3. Map with real hospitals from OpenStreetMap
    try:
        real = live.hospitals_near(loc["lat"], loc["lon"])
    except Exception:
        real = []
    points = [{"lat": loc["lat"], "lon": loc["lon"], "color": "#C0392B", "size": 260}]
    if ok:
        points.append({"lat": ok["lat"], "lon": ok["lon"], "color": "#1F6F4A", "size": 420})
    points += [{"lat": h["lat"], "lon": h["lon"], "color": "#7F8C8D", "size": 160} for h in real]
    st.map(pd.DataFrame(points), latitude="lat", longitude="lon", color="color", size="size")
    st.caption(t("map_caption"))

    st.markdown(f"#### {t('real_title')}")
    if real:
        rows = []
        for h in real[:6]:
            phone = f'<a href="tel:{h["phone"]}">📞 {h["phone"]}</a>' if h.get("phone") else ""
            rows.append(f'<div class="sj-real"><span>🏥 {html.escape(h["name"])}</span>'
                        f'<span>{h["km"]} km · {phone}</span></div>')
        st.markdown("".join(rows), unsafe_allow_html=True)
        st.caption(t("real_note"))
    else:
        st.caption(t("real_none"))

    # 4. The pre-checked first aid, as a safety net under the AI answer
    if known and res["source"] == "ai":
        with st.expander(t("verified_fa")):
            tx = text_for(res["type"])
            for line in tx["do"]:
                st.markdown(f"- ✅ {line}")
            for line in tx["dont"]:
                st.markdown(f"- ❌ {line}")
    st.caption(t("fa_caption"))

    voice.say(" ".join(spoken))
    voice.listen_button(" ".join(spoken + res["do"] + res["dont"]), "em-result")
