"""Shared look and feel: fonts, colours, page headers and result cards."""
import html

import streamlit as st

CSS = """
<style>
/* MedX design: hospital and road signage. Flat colour, nearly square corners, big clear type, no pills. */
@import url('https://fonts.googleapis.com/css2?family=Anek+Latin:wdth,wght@75..125,400..800&family=Anek+Kannada:wdth,wght@75..125,400..800&family=Anek+Devanagari:wdth,wght@75..125,400..800&display=swap');
:root {--r: 4px; --line: rgba(255,255,255,.14); --txt: #EEF3F1; --mut: #A3B8B1;}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp a,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp div {
  font-family: 'Anek Latin', 'Anek Kannada', 'Anek Devanagari', 'Noto Sans', system-ui, sans-serif;
}
.stApp p, .stApp li {line-height: 1.6;}
#MainMenu, footer, .stAppDeployButton {visibility: hidden;}

/* ---------- page header: a coloured sign square + a big condensed title ---------- */
.mx-head {display: flex; align-items: center; gap: 1.1rem; padding: .4rem 0 1.1rem; margin-bottom: 1rem;
  border-bottom: 1px solid var(--line);}
.mx-pict {width: 76px; height: 76px; flex-shrink: 0; border-radius: var(--r); background: var(--sj-a1, #2BB98A);
  display: flex; align-items: center; justify-content: center; font-size: 2.5rem; line-height: 1;}
.mx-title {color: #FFFFFF; font-size: 2.7rem; font-weight: 800; line-height: 1.05; font-variation-settings: "wdth" 82;
  margin: 0;}
.mx-sub {color: var(--mut); font-size: 1.12rem; margin-top: .35rem; line-height: 1.5; max-width: 760px;}
@media (max-width: 640px) {.mx-pict {width: 58px; height: 58px; font-size: 1.9rem} .mx-title {font-size: 2.05rem}}
.stApp h3, .stApp h4 {font-weight: 800; font-variation-settings: "wdth" 88; color: #FFFFFF; margin-top: 1.2rem;}
.st-key-home_link a {padding: 0 !important; background: none !important; border: none !important; min-height: 0 !important;}
.st-key-home_link a * {color: var(--mut) !important; font-weight: 600;}
.st-key-home_link a:hover * {color: #FFFFFF !important;}

/* ---------- result cards (status colours, flat) ---------- */
.sj-card {border: 1px solid; border-radius: var(--r); padding: 1rem 1.2rem; margin: .6rem 0;}
.sj-card-title {font-weight: 800; font-size: 1.3rem; margin-bottom: .35rem;}
.sj-card-body {color: #16241C !important; font-size: 1.1rem; line-height: 1.55;}
.sj-list, .sj-list li {color: #16241C !important; line-height: 1.6;}
.sj-list {margin: .2rem 0 0 1.1rem;}
.sj-pill {display: inline-block; border-radius: var(--r); padding: .15rem .6rem; font-weight: 700; font-size: .9rem;
  margin-top: .5rem; background: #0F6B50; color: #FFFFFF;}
.sj-real {display: flex; justify-content: space-between; gap: 1rem; padding: .6rem 0; border-bottom: 1px solid var(--line);
  color: var(--txt);}
.sj-real a {color: #5EE3B4; font-weight: 700; text-decoration: none;}

/* ---------- controls ---------- */
.stButton > button, .stLinkButton > a, .stDownloadButton > button {border-radius: var(--r) !important; font-weight: 700;
  min-height: 3rem;}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {
  background: var(--sj-a1, #0F6B50) !important; border: none !important; color: #fff !important;}
.stButton > button[kind="primary"] *, .stDownloadButton > button[kind="primary"] *, .stLinkButton > a[kind="primary"] * {
  color: #fff !important;}
.stButton > button[kind="secondary"], .stLinkButton > a[kind="secondary"], .stDownloadButton > button[kind="secondary"] {
  border: 1.5px solid var(--line) !important;}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {border-radius: var(--r) !important; font-size: 1.1rem;}
.stTabs [data-baseweb="tab-list"] {gap: 1.4rem; flex-wrap: wrap; border-bottom: 1px solid var(--line);}
.stTabs [data-baseweb="tab"] {background: none !important; border-top: 0 !important; border-left: 0 !important; border-right: 0 !important; padding: .55rem 0; font-weight: 700; color: var(--mut);
  border-bottom: 3px solid transparent; border-radius: 0;}
.stTabs [data-baseweb="tab"] * {color: inherit !important;}
.stTabs [aria-selected="true"] {color: #FFFFFF !important; border-bottom-color: var(--sj-a1, #2BB98A) !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}
div[data-testid="stMetric"] {background: rgba(255,255,255,.04); border-radius: var(--r); padding: .8rem 1rem;
  border: 1px solid var(--line); border-top: 4px solid var(--sj-a1, #2BB98A);}
div[data-testid="stChatMessage"] {border-radius: var(--r); padding: .9rem 1rem; background: rgba(255,255,255,.045);
  border: 1px solid var(--line);}
div[data-testid="stExpander"] details {border-radius: var(--r) !important;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: var(--r) !important;}
div[data-testid="stDataFrame"] {border-radius: var(--r); overflow: hidden;}

/* ---------- sidebar: plain and solid ---------- */
section[data-testid="stSidebar"] {background: #061C19 !important; border-right: 1px solid var(--line);}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"], section[data-testid="stSidebar"] summary {color: #E4EEEA !important;}
[data-testid="stSidebarNav"]::before {content: "MedX"; display: block; color: #FFFFFF; font-size: 1.9rem; font-weight: 800;
  font-variation-settings: "wdth" 80; padding: .2rem .9rem .8rem;}
[data-testid="stSidebarNav"] a {border-radius: var(--r); margin: 2px 6px; padding: .5rem .8rem; transition: background .12s;}
[data-testid="stSidebarNav"] a:hover {background: rgba(255,255,255,.07);}
[data-testid="stSidebarNav"] a[aria-current="page"] {background: rgba(255,255,255,.12);}
[data-testid="stSidebarNav"] a span {color: #FFFFFF !important; font-weight: 600;}
[data-testid="stSidebarNavSeparator"] {border-color: var(--line);}
.st-key-side_help button {background: #D7263D !important; border: none !important; min-height: 3.4rem;}
.st-key-side_help button p {color: #FFFFFF !important; font-size: 1.35rem !important; font-weight: 800 !important;}
@keyframes sjpulse {0% {box-shadow: 0 0 0 0 rgba(215,38,61,.55);} 70% {box-shadow: 0 0 0 14px rgba(215,38,61,0);}
  100% {box-shadow: 0 0 0 0 rgba(215,38,61,0);}}
.st-key-sb_settings {border-top: 1px solid var(--line); padding-top: .8rem;}
.sj-sb-title {color: var(--mut); font-weight: 700; font-size: .95rem;}
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-baseweb="input"], section[data-testid="stSidebar"] [data-baseweb="base-input"] {
  background: #FFFFFF !important; border-color: transparent !important;}
section[data-testid="stSidebar"] [data-baseweb="select"] *, section[data-testid="stSidebar"] input {
  color: #16241C !important; -webkit-text-fill-color: #16241C;}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {fill: #16241C !important;}
section[data-testid="stSidebar"] .stButton > button {background: rgba(255,255,255,.08); border: 1px solid var(--line);}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details {background: none; border-color: var(--line);}
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
    "em": ("#D7263D", "#D7263D", "🚨"),
    "dis": ("#0F8B6F", "#0F8B6F", "🏥"),
    "eld": ("#B8641A", "#B8641A", "👵"),
    "chat": ("#7B4FC9", "#7B4FC9", "💬"),
    "sar": ("#1F6FC5", "#1F6FC5", "🌊"),
    "dash": ("#4E6475", "#4E6475", "📋"),
    "prof": ("#C2416E", "#C2416E", "👤"),
    "about": ("#3E8E5E", "#3E8E5E", "ℹ️"),
    "home": ("#0F6B50", "#0F6B50", "🩺"),
}


def _strip_icon(title):
    """Titles in the translations start with an emoji; the sign square shows it instead."""
    first, _, rest = str(title).partition(" ")
    return rest if rest and not any(ch.isalnum() for ch in first) else str(title)


def header(title, subtitle="", theme="home"):
    """Page header: a coloured sign square with the page's icon, and a big title.
    Also sets the page's accent colour for buttons, tabs and headings."""
    a1, a2, icon = THEMES.get(theme, THEMES["home"])
    st.markdown(f"<style>:root{{--sj-a1:{a1};--sj-a2:{a2};}}</style>", unsafe_allow_html=True)
    if theme != "home":
        from core.i18n import t
        with st.container(key="home_link"):
            st.page_link("pages/home.py", label=t("nav_home"), icon=":material/arrow_back:")
    sub = f'<div class="mx-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="mx-head"><div class="mx-pict">{icon}</div><div>'
                f'<div class="mx-title">{html.escape(_strip_icon(title))}</div>{sub}</div></div>',
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
