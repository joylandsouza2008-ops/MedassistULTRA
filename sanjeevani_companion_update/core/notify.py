"""Family SOS. Three ways to reach the family, all optional:

1. FREE real SMS from your own Android phone's SIM (SMS Gateway for Android app):
       SMSGATE_USER = "..."      SMSGATE_PASS = "..."
2. FREE loud alarm on the family's phones (ntfy app, no account needed):
       NTFY_TOPIC = "sanjeevani-sos-some-secret-words"
3. Paid/trial automatic phone calls + SMS (Twilio):
       TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
Plus one-tap Call / SMS / WhatsApp buttons that always work with no setup.
    SOS_CONTACTS = "Suresh:+919876543210"   # optional default family contacts
"""
import base64
import json
import re
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

import streamlit as st

from core.ai import _secret


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
                                 headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
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


def ntfy_alarm(title, text, click_url=""):
    """Free loud push alarm to every phone subscribed to the topic in the ntfy app."""
    server = (_secret("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
    headers = {"Title": title, "Priority": "urgent", "Tags": "rotating_light,sos"}
    if click_url:
        headers["Click"] = click_url
    req = urllib.request.Request(f"{server}/{_secret('NTFY_TOPIC')}", data=text.encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


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
    """Family contacts entered in the sidebar (up to 2)."""
    out = []
    for i in (1, 2):
        name = (st.session_state.get(f"sos_name_{i}") or "").strip()
        phone = normalize(st.session_state.get(f"sos_phone_{i}"))
        if phone:
            out.append({"name": name or f"Family {i}", "phone": phone})
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
                                 headers={"Authorization": f"Basic {auth}"})
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


def send_sos(message, spoken, call=True, click_url=""):
    """Reach the family through every channel that is set up.
    Returns a list of (name, kind, ok, error) where kind is sms / call / alarm."""
    from core import state
    results = []
    people = contacts()

    def attempt(name, kind, fn, to):
        try:
            fn()
            results.append((name, kind, True, ""))
            state.add_alert("SOS " + kind.upper(), to, message)
        except Exception as e:
            results.append((name, kind, False, str(e)[:120]))

    # 1. Loud alarm on the family app (free, one message reaches everyone subscribed)
    if ntfy_ready():
        attempt("family app", "alarm", lambda: ntfy_alarm("SANJEEVANI SOS", message, click_url), "ntfy")

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
