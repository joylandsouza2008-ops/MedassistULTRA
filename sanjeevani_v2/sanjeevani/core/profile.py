"""The user's profile + emergency contacts, saved in the browser (localStorage)
on their own phone, so it survives refreshes and restarts and stays on their device."""
import json

import streamlit as st

try:
    from streamlit_js_eval import streamlit_js_eval
except Exception:
    streamlit_js_eval = None

STORAGE_KEY = "sanjeevani_profile_v1"
EMPTY = {"name": "", "age": "", "phone": "", "village": "", "blood": "", "notes": "", "photo": "", "contacts": []}


def _defaults():
    from core.notify import default_contacts   # from secrets, e.g. SOS_CONTACTS
    p = dict(EMPTY)
    p["contacts"] = [{"name": c["name"], "relation": "", "phone": c["phone"]} for c in default_contacts()]
    return p


def load_once():
    """Read the saved profile from the browser (call early, once per run, from app.py)."""
    if "profile" in st.session_state:
        return
    if streamlit_js_eval is None:
        st.session_state.profile = _defaults()
        return
    raw = streamlit_js_eval(js_expressions=f"localStorage.getItem('{STORAGE_KEY}') || 'EMPTY'",
                            key="profile_loader")
    if raw is None:          # the browser hasn't answered yet; it will on the next run
        return
    if raw == "EMPTY":
        st.session_state.profile = _defaults()
        return
    try:
        p = {**EMPTY, **json.loads(raw)}
    except Exception:
        p = _defaults()
    st.session_state.profile = p


def get():
    return st.session_state.get("profile") or _defaults()


def save(p):
    """Keep it for this session and write it to the browser's storage."""
    st.session_state.profile = p
    if streamlit_js_eval is None:
        return False
    n = st.session_state.get("profile_save_n", 0) + 1
    st.session_state.profile_save_n = n
    data = json.dumps(json.dumps(p, ensure_ascii=False), ensure_ascii=False)   # a safe JS string
    streamlit_js_eval(js_expressions=f"localStorage.setItem('{STORAGE_KEY}', {data}); 'ok'",
                      key=f"profile_saver_{n}")
    return True


def info_line():
    """Short identity line added to every SOS, e.g. 'Kamala, 74 yrs, Blood B+, Ph +91...'."""
    p = get()
    parts = [p.get("name"), f"{p['age']} yrs" if p.get("age") else "",
             f"Blood {p['blood']}" if p.get("blood") else "", f"Ph {p['phone']}" if p.get("phone") else ""]
    return ", ".join(x for x in parts if x)


def process_photo(file_bytes, size=256):
    """Any photo -> small square JPEG as a data URL (about 20 KB), so it fits in browser storage."""
    import base64
    import io

    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(file_bytes))).convert("RGB")
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((size, size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def photo_bytes():
    """The saved photo as raw bytes (for st.image / chat avatars), or None."""
    import base64
    photo = get().get("photo") or ""
    if not photo.startswith("data:image"):
        return None
    try:
        return base64.b64decode(photo.split(",", 1)[1])
    except Exception:
        return None


def avatar_html(size=56, photo=None, name=None):
    """Round profile picture, or coloured initials if there's no photo."""
    import html as _html
    p = get()
    photo = p.get("photo") if photo is None else photo
    name = (p.get("name") if name is None else name) or "?"
    style = (f"width:{size}px;height:{size}px;border-radius:50%;border:3px solid rgba(255,255,255,.9);"
             "box-shadow:0 4px 12px rgba(0,0,0,.2);flex-shrink:0;")
    if photo:
        return f'<img src="{photo}" style="{style}object-fit:cover" alt="">'
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
    return (f'<div style="{style}display:flex;align-items:center;justify-content:center;'
            f'background:linear-gradient(135deg,#943155,#E86A8A);color:#fff;font-weight:800;'
            f'font-size:{int(size * .38)}px">{_html.escape(initials)}</div>')
