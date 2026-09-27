import html
import io
from datetime import datetime

import streamlit as st

from core import ai, profile, sos, voice
from core.i18n import t
from core.reminders import IST

# ---------- look and feel ----------
st.markdown("""
<style>
.sj-hero{background:linear-gradient(135deg,#0F3D2E 0%,#1F6F4A 100%);border-radius:24px;padding:2rem 2.2rem;
  margin-bottom:1.2rem;position:relative;overflow:hidden}
.sj-hero:after{content:"🩺";position:absolute;right:-10px;bottom:-40px;font-size:11rem;opacity:.12}
.sj-greet{color:#E8A33D;font-size:1.25rem;font-weight:700}
.sj-title{color:#fff;font-size:2.9rem;font-weight:800;line-height:1.1;margin:.25rem 0 .5rem}
.sj-tag{color:#CFE3D8;font-size:1.15rem;max-width:720px}
.sj-chip{display:inline-block;margin-top:.9rem;background:rgba(255,255,255,.14);color:#fff;border-radius:999px;
  padding:.3rem .9rem;font-weight:600;font-size:.95rem}

/* big clickable tiles: the whole card is one button */
div[class*="st-key-tile_"]{position:relative;border-radius:24px;padding:1.3rem 1.4rem 1.1rem;min-height:185px;
  overflow:hidden;box-shadow:0 8px 22px rgba(15,61,46,.16);transition:transform .15s ease, box-shadow .15s ease}
div[class*="st-key-tile_"]:hover{transform:translateY(-5px);box-shadow:0 16px 32px rgba(15,61,46,.24)}
div[class*="st-key-tile_"] .stButton button{background:rgba(255,255,255,.2)!important;color:#fff!important;
  border:1.5px solid rgba(255,255,255,.55)!important;border-radius:14px!important;font-weight:800!important;
  font-size:1.08rem!important;min-height:3rem;margin-top:.5rem;position:relative;z-index:2}
div[class*="st-key-tile_"] .stButton button:hover{background:rgba(255,255,255,.34)!important}
div[class*="st-key-tile_"] .stButton button p{color:#fff!important;font-weight:800!important}
div[class*="st-key-tile_"] [data-testid="stButton"] button{background:rgba(255,255,255,.2)!important;
  border:1.5px solid rgba(255,255,255,.55)!important;border-radius:14px!important;min-height:3rem}
div[class*="st-key-tile_"] [data-testid="stButton"] button p{color:#fff!important;font-weight:800!important}
.st-key-tile_em .stButton button, .st-key-tile_em [data-testid="stButton"] button{background:#fff!important;
  border:none!important;min-height:3.6rem;box-shadow:0 6px 16px rgba(0,0,0,.18)}
.st-key-tile_em .stButton button p, .st-key-tile_em [data-testid="stButton"] button p{color:#C0392B!important;
  font-size:1.35rem!important}
/* decorations never block clicks */
.sj-t-bg,.sj-t-go,.sj-t-icon,.sj-hero:after{pointer-events:none}
/* the link button inside each tile */
div[class*="st-key-tile_"] [data-testid="stPageLink"],div[class*="st-key-tile_"] .stPageLink{position:relative;z-index:3}
div[class*="st-key-tile_"] a[data-testid="stPageLink-NavLink"],div[class*="st-key-tile_"] [data-testid="stPageLink"] a{
  display:flex!important;justify-content:center;align-items:center;width:100%;min-height:3.1rem;margin-top:.6rem;
  background:rgba(255,255,255,.22)!important;border:2px solid rgba(255,255,255,.6);border-radius:14px!important;
  text-decoration:none!important}
div[class*="st-key-tile_"] [data-testid="stPageLink"] a:hover{background:rgba(255,255,255,.36)!important}
div[class*="st-key-tile_"] [data-testid="stPageLink"] a *{color:#fff!important;font-weight:800!important;font-size:1.1rem!important}
.st-key-tile_em [data-testid="stPageLink"] a{background:#fff!important;border:none;min-height:3.5rem}
.st-key-tile_em [data-testid="stPageLink"] a *{color:#C0392B!important;font-size:1.3rem!important}
/* giant instant SOS button */
.st-key-home_sos button{background:linear-gradient(135deg,#E74C3C,#922B21)!important;border:none!important;
  border-radius:22px!important;min-height:4.4rem;box-shadow:0 10px 24px rgba(192,57,43,.35);animation:sjpulse 2.2s infinite}
.st-key-home_sos button p{color:#fff!important;font-size:1.6rem!important;font-weight:800!important}
.sj-t-bg{position:absolute;right:-8px;bottom:-26px;font-size:7.5rem;opacity:.18;line-height:1}
.sj-t-icon{width:62px;height:62px;border-radius:18px;background:rgba(255,255,255,.2);display:flex;align-items:center;
  justify-content:center;font-size:2.1rem;margin-bottom:.7rem}
.sj-t-title{color:#fff;font-size:1.45rem;font-weight:800;line-height:1.2}
.sj-t-sub{color:rgba(255,255,255,.9);font-size:1rem;margin-top:.35rem;line-height:1.45;max-width:92%}
.sj-t-go{position:absolute;right:1.1rem;top:1rem;color:#fff;font-size:1.6rem;font-weight:800;opacity:.85}

.st-key-tile_em{background:linear-gradient(135deg,#A93226,#E74C3C);min-height:160px!important;
  animation:sjpulse 2.2s infinite}
.st-key-tile_em .sj-t-title{font-size:2.1rem}
.st-key-tile_dis{background:linear-gradient(135deg,#117864,#1ABC9C)}
.st-key-tile_eld{background:linear-gradient(135deg,#BA4A00,#F39C12)}
.st-key-tile_chat{background:linear-gradient(135deg,#5B2C6F,#A569BD)}
.st-key-tile_sar{background:linear-gradient(135deg,#1A5276,#3498DB)}
.st-key-tile_prof{background:linear-gradient(135deg,#943155,#E86A8A)}
.st-key-tile_dash{background:linear-gradient(135deg,#283747,#5D6D7E)}
@keyframes sjpulse{0%{box-shadow:0 0 0 0 rgba(231,76,60,.55)}70%{box-shadow:0 0 0 18px rgba(231,76,60,0)}
  100%{box-shadow:0 0 0 0 rgba(231,76,60,0)}}

.sj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:.4rem 0 1.2rem}
.sj-stat{background:#EEF5F0;border-radius:18px;padding:1.1rem}
.sj-num{color:#1F6F4A;font-size:2.2rem;font-weight:800;line-height:1.1}
.sj-lbl{color:#34463C;font-size:.98rem;margin-top:.3rem}
</style>
""", unsafe_allow_html=True)

# ---------- greeting ----------
hour = datetime.now(IST).hour
greet = t("greet_morning") if hour < 12 else t("greet_afternoon") if hour < 17 else t("greet_evening")
gps = st.session_state.get("gps")
me = profile.get()
greet_line = f"{greet}, {me['name'].split()[0]}" if me.get("name") else greet
avatar = profile.avatar_html(64) if (me.get("photo") or me.get("name")) else ""
chip = f'<div class="sj-chip">📍 {html.escape(gps["name"])}</div>' if gps else ""
st.markdown(f"""
<div class="sj-hero">
<div style="display:flex;align-items:center;gap:1rem">{avatar}<div class="sj-greet">{html.escape(greet_line)} 🙏</div></div>
<div class="sj-title">MedX</div>
<div class="sj-tag">{html.escape(t('how_help'))}</div>
{chip}
</div>""", unsafe_allow_html=True)


def tile(key, icon, title, sub, page, arrow=True, button_label=None):
    """A big colourful card with one big link button (page links always work)."""
    button_label = button_label or f"{t('open')} ➜"
    with st.container(key=f"tile_{key}"):
        st.markdown(
            f'<div class="sj-t-bg">{icon}</div><div class="sj-t-icon">{icon}</div>'
            f'<div class="sj-t-title">{html.escape(title)}</div><div class="sj-t-sub">{html.escape(sub)}</div>'
            + ('<div class="sj-t-go">→</div>' if arrow else ""),
            unsafe_allow_html=True)
        st.page_link(page, label=button_label)


# ---------- instant SOS ----------
with st.container(key="home_sos"):
    if st.button(t("sos_home_btn"), key="home_sos_btn", width="stretch"):
        sos.trigger()
        st.rerun()

# ---------- the tiles ----------
tile("em", "🆘", t("tile_em_title"), t("tile_em"), "pages/1_Emergency.py", button_label=f"🆘 {t('get_help')}")

row1 = st.columns(3)
with row1[0]:
    tile("dis", "🏥", t("nav_dis"), t("tile_dis"), "pages/2_After_Discharge.py")
with row1[1]:
    tile("eld", "👵", t("nav_eld"), t("tile_eld"), "pages/3_Elderly_Care.py")
with row1[2]:
    tile("chat", "💬", t("nav_chat"), t("tile_chat"), "pages/6_Companion.py")

row2 = st.columns(3)
with row2[2]:
    tile("prof", "👤", t("nav_profile"), t("tile_prof"), "pages/7_Profile.py", button_label=f"{t('open')} ➜")
with row2[0]:
    tile("sar", "🌊", t("nav_sar"), t("tile_sar"), "pages/5_Disaster_Mode.py")
with row2[1]:
    tile("dash", "📋", t("nav_dash"), t("tile_dash"), "pages/4_Dashboard.py")

voice.listen_button(" ".join([greet, t("how_help"), t("tile_em_title"), t("nav_dis"), t("nav_eld"),
                              t("nav_chat"), t("nav_sar")]), "home")

# ---------- why it matters ----------
st.markdown(f"### {t('impact_title')}")
stats = [("~58,000", t("imp1")), ("13+ crore", t("imp2")), ("₹351", t("imp3")), ("3", t("imp4"))]
st.markdown('<div class="sj-grid">' + "".join(
    f'<div class="sj-stat"><div class="sj-num">{n}</div><div class="sj-lbl">{html.escape(l)}</div></div>'
    for n, l in stats) + "</div>", unsafe_allow_html=True)

# ---------- live counter + QR ----------
left, right = st.columns([2, 1])
with left:
    st.info(t("live_actions", n=len(st.session_state.get("alerts", []))))
    if ai.available():
        st.success(t("ai_on"))
    else:
        st.caption(t("ai_off"))


def app_url():
    """The public link: from secrets, or detected automatically on the live site."""
    try:
        if "APP_URL" in st.secrets:
            return st.secrets["APP_URL"]
    except Exception:
        pass
    try:
        host = st.context.headers.get("Host", "")
        if host and "localhost" not in host and "127.0.0.1" not in host:
            return f"https://{host}"
    except Exception:
        pass
    return None


with right:
    st.markdown(f"#### 📱 {t('qr_title')}")
    url = app_url()
    if url:
        try:
            import qrcode
            buf = io.BytesIO()
            qrcode.make(url, box_size=8, border=2).save(buf, format="PNG")
            st.image(buf.getvalue(), width=200)
            st.caption(f"{t('qr_text')}  \n{url}")
        except Exception:
            st.caption(url)
    else:
        st.caption(t("qr_missing"))

st.divider()
st.caption(t("disclaimer"))
