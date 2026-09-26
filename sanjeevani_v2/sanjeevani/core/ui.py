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


def header(title, subtitle=""):
    sub = f'<div class="sj-head-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="sj-head"><div class="sj-head-title">{html.escape(title)}</div>{sub}</div>',
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
