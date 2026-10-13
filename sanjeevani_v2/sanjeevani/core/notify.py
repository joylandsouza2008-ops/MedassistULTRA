"""Family SOS. Three ways to reach the family, all optional:

1. FREE real SMS from your own Android phone's SIM (SMS Gateway for Android app):
       SMSGATE_USER = "..."      SMSGATE_PASS = "..."
2. FREE loud alarm on the family's phones (ntfy app, no account needed):
       NTFY_TOPIC = "medx-sos-some-secret-words"
3. Paid/trial automatic phone calls + SMS (Twilio):
       TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
Plus one-tap Call / SMS / WhatsApp buttons that always work with no setup.
    SOS_CONTACTS = "Suresh:+919876543210"   # optional default family contacts
"""
import base64
import collections
import json
import re
import time
import threading
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

import streamlit as st

from core.ai import _secret

USER_AGENT = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/128.0 Mobile Safari/537.36 MedX/1.0")


def twilio_ready():
    return all(_secret(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"))


def gateway_ready():
    return bool(_secret("SMSGATE_USER") and _secret("SMSGATE_PASS"))


def ntfy_ready():
    return bool(_secret("NTFY_TOPIC"))


def auto_ready():
    """True if at least one automatic channel is set up."""
    return gateway_ready() or ntfy_ready() or twilio_ready()


def _post_json(url, payload, user, password, timeout=15):
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def gateway_sms(phones, text):
    """Real SMS sent by YOUR Android phone (free with your SIM plan)."""
    base = (_secret("SMSGATE_URL") or "https://api.sms-gate.app/3rdparty/v1").rstrip("/")
    payload = {"textMessage": {"text": text}, "phoneNumbers": phones}
    user, pw = _secret("SMSGATE_USER"), _secret("SMSGATE_PASS")
    last = ""
    for path in ("/messages", "/message"):   # newer and older app versions
        try:
            return _post_json(base + path, payload, user, pw)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode()[:120]
            except Exception:
                detail = ""
            last = f"SMS gateway error {e.code} {detail}".strip()
            if e.code not in (403, 404, 405):
                break
    raise RuntimeError(last)


def ntfy_send(title, text, priority="urgent", tags="rotating_light,sos", at=None, click_url="", topic=None):
    """Push a notification to every phone subscribed to the topic in the ntfy app.
    at = unix timestamp to deliver it later (ntfy holds it, up to 3 days ahead)."""
    server = (_secret("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
    headers = {"Title": title, "Priority": priority, "Tags": tags, "User-Agent": USER_AGENT}
    if at:
        headers["At"] = str(int(at))
    if click_url:
        headers["Click"] = click_url
    topic = topic or _secret("NTFY_TOPIC")
    req = urllib.request.Request(f"{server}/{topic}", data=text.encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def ntfy_alarm(title, text, click_url=""):
    """Free loud emergency alarm on the family's phones."""
    return ntfy_send(title, text, "urgent", "rotating_light,sos", click_url=click_url)


def reminder_topic():
    """Reminders can go to the patient's own topic; falls back to the family topic."""
    return _secret("NTFY_REMINDER_TOPIC") or _secret("NTFY_TOPIC")


def normalize(phone):
    """'98765 43210' -> '+919876543210'."""
    digits = re.sub(r"[^\d+]", "", phone or "")
    if not digits:
        return ""
    if digits.startswith("+"):
        return digits
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    return "+" + digits


def default_contacts():
    """Contacts from secrets, like SOS_CONTACTS = "Suresh:+9198...,Priya:+9197..."."""
    raw = _secret("SOS_CONTACTS") or ""
    out = []
    for part in str(raw).split(","):
        if ":" in part:
            name, phone = part.split(":", 1)
            out.append({"name": name.strip(), "phone": normalize(phone)})
    return out


def contacts():
    """Every emergency contact from the user's profile (no limit)."""
    from core import profile
    out, seen = [], set()
    for c in profile.get().get("contacts", []):
        phone = normalize(c.get("phone"))
        if phone and phone not in seen:
            seen.add(phone)
            out.append({"name": (c.get("name") or "").strip() or "Family", "phone": phone})
    return out


def maps_link(lat, lon):
    return f"https://maps.google.com/?q={lat:.5f},{lon:.5f}"


def links(phone, message):
    digits = phone.lstrip("+")
    return {
        "call": f"tel:{phone}",
        "sms": f"sms:{phone}?body={urllib.parse.quote(message)}",
        "whatsapp": f"https://wa.me/{digits}?text={urllib.parse.quote(message)}",
    }


def _twilio(resource, params):
    sid, token = _secret("TWILIO_ACCOUNT_SID"), _secret("TWILIO_AUTH_TOKEN")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/{resource}.json"
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                 headers={"Authorization": f"Basic {auth}", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode()).get("message", str(e))
        except Exception:
            msg = str(e)
        raise RuntimeError(msg) from None


def send_sms(to, body):
    return _twilio("Messages", {"To": to, "From": _secret("TWILIO_FROM_NUMBER"), "Body": body})


def place_call(to, spoken):
    """A real phone call that reads the emergency message aloud (twice)."""
    say = f'<Say voice="Polly.Raveena">{escape(spoken)}</Say>'
    twiml = f'<Response>{say}<Pause length="1"/>{say}</Response>'
    return _twilio("Calls", {"To": to, "From": _secret("TWILIO_FROM_NUMBER"), "Twiml": twiml})


# ---------- rate limits ----------
# Per browser: one SOS every 30 seconds. For the whole app: at most 20 alert rounds in 10 minutes.
# Without this, someone pressing SOS again and again could use up the SIM's daily SMS limit,
# and a real emergency would then fail to send.
SESSION_GAP = 30
GLOBAL_MAX, GLOBAL_WINDOW = 20, 600
_global_sends = collections.deque()
_global_lock = threading.Lock()


def _rate_check(limit):
    """Returns how many seconds to wait, or 0 if sending is allowed now."""
    now = time.time()
    if limit:
        last = st.session_state.get("_last_sos", 0)
        if now - last < SESSION_GAP:
            return int(SESSION_GAP - (now - last)) + 1
    with _global_lock:
        while _global_sends and now - _global_sends[0] > GLOBAL_WINDOW:
            _global_sends.popleft()
        if len(_global_sends) >= GLOBAL_MAX:
            return int(GLOBAL_WINDOW - (now - _global_sends[0])) + 1
        _global_sends.append(now)
    if limit:
        st.session_state["_last_sos"] = now
    return 0


def send_sos(message, spoken, call=True, click_url="", limit=True):
    """Reach the family through every channel that is set up.
    Returns a list of (name, kind, ok, error) where kind is sms / call / alarm.
    limit=False is only for the "I'm safe" message, which must always get through."""
    from core import profile, state
    from core.i18n import t
    wait = _rate_check(limit)
    if wait:
        state.add_alert("SOS held back", "Rate limit", f"Too many alerts. Next one allowed in {wait}s.")
        return [("MedX", "sms", False, t("sos_wait", s=wait))]
    results = []
    people = contacts()
    who = profile.info_line()
    if who and who not in message:
        message = f"{message} [{who}]"

    def attempt(name, kind, fn, to):
        try:
            fn()
            results.append((name, kind, True, ""))
            state.add_alert("SOS " + kind.upper(), to, message)
        except Exception as e:
            results.append((name, kind, False, str(e)[:120]))

    # 1. Loud alarm on the family app (free, one message reaches everyone subscribed)
    if ntfy_ready():
        attempt("family app", "alarm", lambda: ntfy_alarm("MEDX SOS", message, click_url), "ntfy")

    for c in people:
        # 2. SMS: free phone gateway first, Twilio if that isn't set up
        if gateway_ready():
            attempt(c["name"], "sms", lambda c=c: gateway_sms([c["phone"]], message), c["phone"])
        elif twilio_ready():
            attempt(c["name"], "sms", lambda c=c: send_sms(c["phone"], message), c["phone"])
        # 3. Automatic phone call (Twilio only)
        if call and twilio_ready():
            attempt(c["name"], "call", lambda c=c: place_call(c["phone"], spoken), c["phone"])
    return results
