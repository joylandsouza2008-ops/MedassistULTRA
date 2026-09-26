import io

import streamlit as st

from core import ai, voice
from core.i18n import t

st.markdown("""
<style>
.sj-hero{background:#0F3D2E;border-radius:20px;padding:2.4rem 2.2rem;margin-bottom:1.2rem}
.sj-kicker{color:#9FC2B1;text-transform:uppercase;letter-spacing:.08em;font-size:.85rem;margin-bottom:.4rem}
.sj-title{color:#FFFFFF;font-size:3.2rem;font-weight:800;line-height:1.1;margin-bottom:.6rem}
.sj-tag{color:#E8A33D;font-size:1.4rem;font-style:italic;margin-bottom:.7rem}
.sj-sub{color:#CFE3D8;font-size:1.1rem;max-width:760px}
.sj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:.4rem 0 1.4rem 0}
.sj-stat{background:#EEF5F0;border-radius:16px;padding:1.2rem 1.1rem}
.sj-num{color:#1F6F4A;font-size:2.4rem;font-weight:800;line-height:1.1}
.sj-lbl{color:#34463C;font-size:1rem;margin-top:.3rem}
</style>
""", unsafe_allow_html=True)

# ---------- hero ----------
st.markdown(f"""
<div class="sj-hero">
<div class="sj-kicker">Team Orbit · Agentic AI For Billions</div>
<div class="sj-title">🌿 Sanjeevani</div>
<div class="sj-tag">{t('home_tag')}</div>
<div class="sj-sub">{t('home_intro')}</div>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([1, 3])
with c1:
    st.page_link("pages/1_Emergency.py", label=t("hero_try"), icon="🚨")
with c2:
    voice.listen_button(f"{t('home_tag')} {t('home_intro')}", "home")

# ---------- impact numbers ----------
st.markdown(f"### {t('impact_title')}")
stats = [("~58,000", t("imp1")), ("13+ crore", t("imp2")), ("₹351", t("imp3")), ("3", t("imp4"))]
st.markdown('<div class="sj-grid">' + "".join(
    f'<div class="sj-stat"><div class="sj-num">{n}</div><div class="sj-lbl">{l}</div></div>' for n, l in stats
) + "</div>", unsafe_allow_html=True)

# ---------- what it does ----------
st.markdown(f"### {t('what_title')}")
cards = [
    ("🚨", "nav_em", "card_em", "pages/1_Emergency.py"),
    ("🏥", "nav_dis", "card_dis", "pages/2_After_Discharge.py"),
    ("👵", "nav_eld", "card_eld", "pages/3_Elderly_Care.py"),
    ("🌊", "nav_sar", "card_sar", "pages/5_Disaster_Mode.py"),
]
cols = st.columns(4)
for col, (icon, title, text, page) in zip(cols, cards):
    with col:
        with st.container(border=True):
            st.markdown(f"#### {icon} {t(title)}")
            st.write(t(text))
            st.page_link(page, label=t("open"), icon="➡️")

# ---------- live counter + QR ----------
left, right = st.columns([2, 1])
with left:
    st.info(t("live_actions", n=len(st.session_state.get("alerts", []))))
    if ai.available():
        st.success(t("ai_on"))
    else:
        st.caption(t("ai_off"))
    st.page_link("pages/4_Dashboard.py", label=t("see_dash"), icon="📋")


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
