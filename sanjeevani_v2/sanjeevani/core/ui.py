"""Shared look and feel: fonts, colours, page headers and result cards."""
import html

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;800&family=Noto+Sans+Kannada:wght@400;700&family=Noto+Sans+Devanagari:wght@400;700&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: 'Noto Sans', 'Noto Sans Kannada', 'Noto Sans Devanagari', system-ui, sans-serif;
}
#MainMenu, footer, .stAppDeployButton {visibility: hidden;}
.stButton > button, .stLinkButton > a {border-radius: 12px; font-weight: 700; min-height: 3rem;}
.stTextInput input, .stTextArea textarea {border-radius: 12px;}
div[data-testid="stMetric"] {background: #EEF5F0; border-radius: 14px; padding: .8rem 1rem;}
div[data-testid="stExpander"] details {border-radius: 14px;}
.sj-head {background: linear-gradient(135deg, #0F3D2E, #1F6F4A); border-radius: 18px;
  padding: 1.4rem 1.6rem; margin-bottom: 1rem;}
.sj-head-title {color: #FFFFFF; font-size: 2rem; font-weight: 800; line-height: 1.2;}
.sj-head-sub {color: #CFE3D8; font-size: 1.05rem; margin-top: .4rem; line-height: 1.5;}
.sj-card {border: 1px solid; border-radius: 16px; padding: 1rem 1.2rem; margin: .6rem 0;}
.sj-card-title {font-weight: 800; font-size: 1.25rem; margin-bottom: .35rem;}
.sj-card-body {color: #16241C; font-size: 1.08rem; line-height: 1.55;}
.sj-list {margin: .2rem 0 0 1.1rem; color: #16241C; line-height: 1.6;}
.sj-pill {display: inline-block; border-radius: 999px; padding: .15rem .75rem; font-weight: 700;
  font-size: .9rem; margin-top: .5rem; background: #1F6F4A; color: #FFFFFF;}
.sj-real {display: flex; justify-content: space-between; gap: 1rem; padding: .55rem .2rem;
  border-bottom: 1px solid #E3EDE7; color: #16241C;}
.sj-real a {color: #1F6F4A; font-weight: 700; text-decoration: none;}

/* ---------- shared page style (colour comes from the page header) ---------- */
.sj-head {position: relative; overflow: hidden; border-radius: 24px; padding: 1.6rem 1.8rem;
  background: linear-gradient(135deg, var(--sj-a2, #0F3D2E), var(--sj-a1, #1F6F4A));
  box-shadow: 0 10px 26px rgba(0,0,0,.14);}
.sj-head-icon {position: absolute; right: -6px; bottom: -34px; font-size: 8.5rem; opacity: .16; line-height: 1;}
.stApp h3, .stApp h4 {border-left: 6px solid var(--sj-a1, #1F6F4A); padding-left: .65rem;}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {
  background: linear-gradient(135deg, var(--sj-a2, #0F3D2E), var(--sj-a1, #1F6F4A)) !important;
  border: none !important; color: #fff !important; box-shadow: 0 6px 16px rgba(0,0,0,.14);}
.stButton > button, .stDownloadButton > button, .stLinkButton > a {transition: transform .12s ease, box-shadow .12s ease;}
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0,0,0,.14);}
.stButton > button[kind="secondary"], .stLinkButton > a[kind="secondary"] {border: 2px solid var(--sj-a1, #1F6F4A);}
.stTabs [data-baseweb="tab-list"] {gap: .4rem; flex-wrap: wrap;}
.stTabs [data-baseweb="tab"] {border-radius: 999px; padding: .45rem 1rem; background: #F2F5F3; font-weight: 700;}
.stTabs [aria-selected="true"] {background: var(--sj-a1, #1F6F4A) !important; color: #fff !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 20px;}
div[data-testid="stMetric"] {border-top: 5px solid var(--sj-a1, #1F6F4A);}
div[data-testid="stChatMessage"] {border-radius: 20px; padding: .8rem 1rem; background: #F7F9F8;}
div[data-testid="stExpander"] details {border-radius: 16px; border-color: #E3EDE7;}
div[data-testid="stDataFrame"] {border-radius: 14px; overflow: hidden;}
.stTextInput input, .stTextArea textarea {border-radius: 14px; font-size: 1.1rem;}
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #EEF5F0, #FFFFFF);}
.st-key-home_link a {border-radius: 999px; background: #F2F5F3; font-weight: 700; padding: .25rem .9rem;}
</style>
"""

KINDS = {
    "ok": ("#E8F5EE", "#1F6F4A"),
    "warn": ("#FFF4E0", "#9A5B00"),
    "danger": ("#FDECEA", "#A93226"),
    "info": ("#EEF3FB", "#1F4E79"),
}


def css():
    st.markdown(CSS, unsafe_allow_html=True)


THEMES = {
    "em": ("#E74C3C", "#A93226", "🚨"),
    "dis": ("#1ABC9C", "#117864", "🏥"),
    "eld": ("#F39C12", "#BA4A00", "👵"),
    "chat": ("#A569BD", "#5B2C6F", "💬"),
    "sar": ("#3498DB", "#1A5276", "🌊"),
    "dash": ("#5D6D7E", "#283747", "📋"),
    "home": ("#1F6F4A", "#0F3D2E", "🌿"),
}


def header(title, subtitle="", theme="home"):
    """Coloured page banner. Also sets the page's accent colour for buttons, tabs and headings."""
    a1, a2, icon = THEMES.get(theme, THEMES["home"])
    st.markdown(f"<style>:root{{--sj-a1:{a1};--sj-a2:{a2};}}</style>", unsafe_allow_html=True)
    if theme != "home":
        from core.i18n import t
        with st.container(key="home_link"):
            st.page_link("pages/home.py", label=t("nav_home"), icon="🏠")
    sub = f'<div class="sj-head-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="sj-head"><div class="sj-head-icon">{icon}</div>'
                f'<div class="sj-head-title">{html.escape(title)}</div>{sub}</div>',
                unsafe_allow_html=True)


def card(kind, title, body="", extra_html=""):
    bg, fg = KINDS[kind]
    st.markdown(
        f'<div class="sj-card" style="background:{bg};border-color:{fg}40">'
        f'<div class="sj-card-title" style="color:{fg}">{html.escape(title)}</div>'
        f'<div class="sj-card-body">{html.escape(body)}</div>{extra_html}</div>',
        unsafe_allow_html=True)


def list_card(kind, title, items):
    bg, fg = KINDS[kind]
    lis = "".join(f"<li>{html.escape(str(i))}</li>" for i in items)
    st.markdown(
        f'<div class="sj-card" style="background:{bg};border-color:{fg}40">'
        f'<div class="sj-card-title" style="color:{fg}">{html.escape(title)}</div>'
        f'<ul class="sj-list">{lis}</ul></div>',
        unsafe_allow_html=True)


def pill(text):
    return f'<span class="sj-pill">{html.escape(text)}</span>'


def stock_status(qty):
    from core.i18n import t
    return f"✅ {t('in_stock')}" if qty and qty > 0 else f"❌ {t('out_stock')}"
