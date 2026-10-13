"""About: why MedX exists, how it works, a QR code to open it on a phone, and credits."""
import html
import io

import streamlit as st

from core import ai, fx, ui
from core.i18n import t

ui.header(t("about_title"), t("about_intro"), theme="about")

st.markdown("""
<style>
.mx-sec{color:#FFFFFF;font-size:1.4rem;font-weight:800;font-variation-settings:"wdth" 88;
  margin:2rem 0 .2rem;padding-bottom:.45rem;border-bottom:1px solid rgba(255,255,255,.14)}
.mx-fact{display:flex;align-items:baseline;gap:1.4rem;padding:.9rem .2rem;border-bottom:1px solid rgba(255,255,255,.1)}
.mx-fact-n{flex:0 0 9.5rem;color:#FFFFFF;font-size:2rem;font-weight:800;font-variation-settings:"wdth" 85;line-height:1}
.mx-fact-l{color:#C9D8D3;font-size:1.05rem;line-height:1.45}
.mx-step{display:flex;gap:1.1rem;align-items:flex-start;padding:.85rem .2rem;border-bottom:1px solid rgba(255,255,255,.1)}
.mx-step-n{flex:0 0 2.4rem;height:2.4rem;border-radius:4px;background:#3E8E5E;color:#fff;font-weight:800;
  display:flex;align-items:center;justify-content:center;font-size:1.2rem}
.mx-step-t{color:#E9F6F2;font-size:1.1rem;line-height:1.5;padding-top:.3rem}
@media (max-width:640px){.mx-fact{flex-direction:column;gap:.3rem}.mx-fact-n{flex:none}}
</style>
""", unsafe_allow_html=True)

# ---------- why it matters ----------
st.markdown(f'<div class="mx-sec">{html.escape(t("impact_title"))}</div>', unsafe_allow_html=True)
facts = [(fx.count("~58,000", 58000, "~"), t("imp1")), (fx.count("13+ crore", 13, "", "+ crore"), t("imp2")),
         (fx.count("₹351", 351, "₹"), t("imp3")), (fx.count("3", 3), t("imp4"))]
st.markdown("".join(f'<div class="mx-fact"><div class="mx-fact-n">{n}</div>'
                    f'<div class="mx-fact-l">{html.escape(l)}</div></div>' for n, l in facts),
            unsafe_allow_html=True)

# ---------- how it works ----------
st.markdown(f'<div class="mx-sec">{html.escape(t("how_title"))}</div>', unsafe_allow_html=True)
st.markdown("".join(f'<div class="mx-step"><div class="mx-step-n">{i}</div>'
                    f'<div class="mx-step-t">{html.escape(t(f"how{i}"))}</div></div>' for i in range(1, 5)),
            unsafe_allow_html=True)

# ---------- this session + phone ----------
st.markdown(f'<div class="mx-sec">{html.escape(t("qr_title"))}</div>', unsafe_allow_html=True)


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


left, right = st.columns([2, 1])
with left:
    st.write(t("live_actions", n=len(st.session_state.get("alerts", []))))
    st.write(t("ai_on") if ai.available() else t("ai_off"))
with right:
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

# ---------- credits ----------
st.markdown('<div class="mx-sec">&nbsp;</div>', unsafe_allow_html=True)
st.write(t("footer"))
st.markdown(f"[{t('footer_code')}](https://github.com/joylandsouza2008-ops/MedassistULTRA)")
st.caption(t("disclaimer"))
