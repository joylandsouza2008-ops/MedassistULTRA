"""Home: one giant SOS button, then a plain list of everything else MedX does."""
import html
from datetime import datetime

import streamlit as st

from core import fx, profile, sos, voice
from core.i18n import t
from core.reminders import IST

ROWS = [  # key, page, icon, title key, description key, sign colour
    ("em", "pages/1_Emergency.py", "🚨", "nav_em", "tile_em", "#D7263D"),
    ("dis", "pages/2_After_Discharge.py", "🏥", "nav_dis", "tile_dis", "#0F8B6F"),
    ("eld", "pages/3_Elderly_Care.py", "👵", "nav_eld", "tile_eld", "#B8641A"),
    ("chat", "pages/6_Companion.py", "💬", "nav_chat", "tile_chat", "#7B4FC9"),
    ("sar", "pages/5_Disaster_Mode.py", "🌊", "nav_sar", "tile_sar", "#1F6FC5"),
    ("prof", "pages/7_Profile.py", "👤", "nav_profile", "tile_prof", "#C2416E"),
    ("dash", "pages/4_Dashboard.py", "📋", "nav_dash", "tile_dash", "#4E6475"),
    ("about", "pages/8_About.py", "ℹ️", "nav_about", "tile_about", "#3E8E5E"),
]

row_css = "".join(
    f'.st-key-row_{k} [data-testid="stPageLink"] a::before{{content:"{icon}";background:{colour}}}'
    for k, _, icon, _, _, colour in ROWS)

st.markdown("""
<style>
:root{--sj-a1:#0F6B50}
/* greeting */
.mx-hello{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;
  padding-bottom:.6rem;border-bottom:1px solid rgba(255,255,255,.14)}
.mx-hello-greet{color:#FFFFFF;font-size:1.6rem;font-weight:700;font-variation-settings:"wdth" 90}
.mx-hello-loc{color:#A3B8B1;font-size:1.05rem}

/* the giant SOS button: an emergency-stop button. The whole circle is the button. */
.st-key-big_sos{display:flex;flex-direction:column;align-items:center;padding:2.2rem 0 .4rem}
.st-key-big_sos .stButton,.st-key-big_sos [data-testid="stButton"]{display:flex;justify-content:center;width:100%}
.st-key-big_sos button{width:min(76vw,360px)!important;height:min(76vw,360px)!important;min-height:0!important;
  border-radius:50%!important;padding:0!important;cursor:pointer;
  background:radial-gradient(circle at 38% 32%,#F2546A 0%,#D7263D 45%,#A3142A 100%)!important;
  border:16px solid #F2C230!important;
  box-shadow:0 0 0 5px #141414,0 22px 50px rgba(0,0,0,.55),0 0 0 0 rgba(215,38,61,.55)!important;
  animation:mxSos 2s ease-out infinite!important;transition:transform .12s ease!important}
.st-key-big_sos button:hover{transform:scale(1.025)}
.st-key-big_sos button:active{transform:scale(.96)}
.st-key-big_sos button::before{display:none!important}
.st-key-big_sos button p{color:#FFFFFF!important;font-size:min(22vw,7.2rem)!important;font-weight:800!important;
  letter-spacing:.03em;font-variation-settings:"wdth" 85;line-height:1!important;text-shadow:0 3px 0 rgba(0,0,0,.25)}
@keyframes mxSos{0%{box-shadow:0 0 0 5px #141414,0 22px 50px rgba(0,0,0,.55),0 0 0 0 rgba(215,38,61,.55)}
  100%{box-shadow:0 0 0 5px #141414,0 22px 50px rgba(0,0,0,.55),0 0 0 46px rgba(215,38,61,0)}}
.mx-sos-hint{text-align:center;color:#C9D8D3;font-size:1.15rem;max-width:460px;margin:.6rem auto 0;line-height:1.5}

/* "choose what you need": a signage list. Each whole row is one link. */
.mx-list-title{color:#FFFFFF;font-size:1.5rem;font-weight:800;font-variation-settings:"wdth" 88;
  margin:2.4rem 0 .3rem;padding-bottom:.5rem;border-bottom:1px solid rgba(255,255,255,.14)}
div[class*="st-key-row_"] [data-testid="stPageLink"] a{display:flex!important;box-sizing:border-box;align-items:center;gap:1.1rem;
  width:100%;max-width:none;padding:.85rem .4rem!important;margin:0!important;min-height:0!important;
  background:none!important;border:none!important;border-bottom:1px solid rgba(255,255,255,.14)!important;
  border-radius:0!important;box-shadow:none!important;text-decoration:none!important;transform:none!important;
  transition:background .15s ease!important}
div[class*="st-key-row_"] [data-testid="stPageLink"] a:hover{background:rgba(255,255,255,.05)!important}
.stApp div[class*="st-key-row_"] [data-testid="stPageLink"] a::before{position:static;transform:none;width:58px;height:58px;
  aspect-ratio:auto;border-radius:4px;z-index:auto;flex-shrink:0;display:flex;align-items:center;justify-content:center;
  font-size:1.9rem;line-height:1;transition:none}
div[class*="st-key-row_"] [data-testid="stPageLink"] a::after{content:"→";margin-left:auto;padding-left:1rem;
  color:#A3B8B1;font-size:1.6rem;font-weight:700;transition:transform .15s ease,color .15s ease}
div[class*="st-key-row_"] [data-testid="stPageLink"] a:hover::after{transform:translateX(5px);color:#FFFFFF}
div[class*="st-key-row_"] [data-testid="stPageLink"] a p,div[class*="st-key-row_"] [data-testid="stPageLink"] a span{
  color:#C9D8D3!important;font-size:1.05rem!important;font-weight:400!important;line-height:1.45!important;
  white-space:normal!important;text-align:left}
div[class*="st-key-row_"] [data-testid="stPageLink"] a strong{display:block;color:#FFFFFF!important;font-size:1.35rem;
  font-weight:800;font-variation-settings:"wdth" 90;margin-bottom:.1rem}
div[class*="st-key-row_"]{animation:mxRise .45s ease both}
""" + row_css + "\n</style>", unsafe_allow_html=True)
st.markdown(fx.HERO_CSS, unsafe_allow_html=True)

# ---------- greeting ----------
hour = datetime.now(IST).hour
greet = t("greet_morning") if hour < 12 else t("greet_afternoon") if hour < 17 else t("greet_evening")
me = profile.get()
greet_line = f"{greet}, {me['name'].split()[0]}" if me.get("name") else greet
gps = st.session_state.get("gps")
loc = f'<span class="mx-hello-loc">📍 {html.escape(gps["name"])}</span>' if gps else ""
st.markdown(f'<div class="mx-hello"><span class="mx-hello-greet">{fx.words(greet_line, .05)}</span>{loc}</div>',
            unsafe_allow_html=True)

# ---------- the giant SOS button ----------
with st.container(key="big_sos"):
    if st.button(t("sos_big"), key="big_sos_btn"):
        sos.trigger()
        st.rerun()
    st.markdown(f'<div class="mx-sos-hint">{html.escape(t("sos_big_hint"))}</div>', unsafe_allow_html=True)

# ---------- everything else, as a plain list ----------
st.markdown(f'<div class="mx-list-title">{html.escape(t("choose_need"))}</div>', unsafe_allow_html=True)
for k, page, _icon, title_key, desc_key, _colour in ROWS:
    with st.container(key=f"row_{k}"):
        st.page_link(page, label=f"**{t(title_key)}** {t(desc_key)}")

voice.listen_button(" ".join([greet_line, t("sos_big_hint"), t("choose_need")]
                             + [t(r[3]) for r in ROWS]), "home")

# ---------- the village at night ----------
st.markdown(f'<div class="mx-horizon">{fx.hero_scene()}</div>', unsafe_allow_html=True)
st.caption(t("disclaimer"))
