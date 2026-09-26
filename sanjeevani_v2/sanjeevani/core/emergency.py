"""Emergency agent: understand the message -> find the right hospital ->
send alerts -> guide first aid (on screen and by voice)."""
import pandas as pd
import streamlit as st

from core import ai, data, geo, state, voice
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


def detect(text):
    """Work out what kind of emergency this is.
    Uses AI if a key is set, otherwise keyword matching (works for Kannada/Hindi too)."""
    if not text or not text.strip():
        return None, ""
    if ai.available():
        try:
            result = ai.classify_emergency(text)
            if result and result.get("type") in EMERGENCIES:
                return result["type"], result.get("summary", "")
        except Exception:
            pass
    low = text.lower()
    for etype, info in EMERGENCIES.items():
        if any(k in low for k in info["keywords"]):
            return etype, ""
    return None, ""


def best_hospitals(etype, lat, lon):
    """Nearest hospital overall vs nearest one that can actually treat this."""
    need = EMERGENCIES[etype]["needs"]
    ranked = geo.sort_by_distance(data.hospitals(), lat, lon)
    nearest_any = ranked[0]
    nearest_ok = next((h for h in ranked if h["stock"].get(need, 0) > 0), None)
    return nearest_any, nearest_ok


def render(etype, village_name, family_contact="Family member"):
    tx = text_for(etype)
    en = EM_TEXT[etype]["en"]  # alert log stays in English for hospital staff
    need_key = EMERGENCIES[etype]["needs"]
    v = data.village(village_name)
    nearest_any, ok = best_hospitals(etype, v["lat"], v["lon"])

    st.subheader(t("em_near", label=tx["label"], village=village_name))

    if ok is None:
        msg = t("none_have", need=tx["need"])
        st.error(msg)
        voice.say(msg)
        return

    spoken = []
    if nearest_any["id"] != ok["id"]:
        warn = t("nearest_lacks", name=nearest_any["name"], km=nearest_any["km"], need=tx["need"])
        st.warning(warn)
        spoken.append(warn)

    stock = t("available") if need_key == "cardiac_care" else t("in_stock", n=ok["stock"][need_key])
    go = t("go_to", name=ok["name"], km=ok["km"], eta=ok["eta"], need=tx["need"], stock=stock)
    st.success(go)
    spoken.append(go)

    # The agent ACTS on its own: alerts go out automatically (once).
    key = f"{etype}-{village_name}-{ok['id']}"
    state.add_alert("Hospital alert", ok["name"],
                    f"{en['label']} patient coming from {village_name}, ETA {ok['eta']} min. Keep {en['need']} ready.",
                    key=key + "-h")
    state.add_alert("Ambulance (108)", "Ambulance control",
                    f"Pickup at {village_name} for {en['label'].lower()}, drop at {ok['name']}.", key=key + "-a")
    state.add_alert("Family alert", family_contact,
                    f"Emergency: {en['label'].lower()} at {village_name}. Going to {ok['name']}.", key=key + "-f")
    c1, c2, c3 = st.columns(3)
    c1.metric(t("m_hospital"), t("m_alerted"))
    c2.metric(t("m_ambulance"), t("m_requested"))
    c3.metric(t("m_family"), t("m_informed"))

    points = pd.DataFrame([
        {"lat": v["lat"], "lon": v["lon"], "color": "#C0392B", "size": 250},
        {"lat": ok["lat"], "lon": ok["lon"], "color": "#1F6F4A", "size": 400},
    ])
    st.map(points, latitude="lat", longitude="lon", color="color", size="size")
    st.caption(t("map_caption"))

    st.markdown(f"#### {t('first_aid')}")
    col_do, col_dont = st.columns(2)
    with col_do:
        st.markdown(f"**✅ {t('do')}**")
        for line in tx["do"]:
            st.markdown(f"- {line}")
    with col_dont:
        st.markdown(f"**❌ {t('dont')}**")
        for line in tx["dont"]:
            st.markdown(f"- {line}")
    st.caption(t("fa_caption"))

    # Speak the key instructions automatically, and offer a replay button
    full = " ".join(spoken + tx["do"] + tx["dont"])
    voice.say(" ".join(spoken + tx["do"][:2]))
    voice.listen_button(full, f"em-{etype}")
