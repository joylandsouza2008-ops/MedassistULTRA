"""MedX API: the same agent brain, usable by other systems.

WhatsApp bots, hospital software, IVR phone systems or a mobile app can all
call these endpoints instead of using the website.

Run (from the project folder):
    python -m uvicorn api.main:app --reload
Then open http://127.0.0.1:8000/docs to try every endpoint in the browser.

Security:
- Reading is open. Changing data (hospital stock, disaster reports) needs the header
  X-API-Key with the value of the MEDX_API_KEY environment variable. With no key set, changes are switched off.
- Every client is limited to 60 requests a minute.
- If TWILIO_AUTH_TOKEN is set, the WhatsApp webhook only accepts requests signed by Twilio.
"""
import base64
import collections
import hashlib
import hmac
import os
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from core import data, emergency, geo, meds, sar  # noqa: E402

app = FastAPI(
    title="MedX API",
    version="0.1.0",
    description="Voice-first medicine agent: emergencies, medicine checks and disaster rescue. "
                "All data is demo data.",
)

STOCK_ITEMS = ["antivenom_vials", "anti_rabies_vaccine", "cardiac_care"]
EVENT, REPORTS = sar.load_demo()           # disaster reports kept in memory for the demo
REPORTS = list(REPORTS)


# ---------- security ----------
RATE_MAX, RATE_WINDOW = 60, 60            # requests per client per minute
_hits = collections.defaultdict(collections.deque)
_hits_lock = threading.Lock()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    who = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()
    now = time.time()
    with _hits_lock:
        q = _hits[who]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_MAX:
            return JSONResponse({"detail": "Too many requests. Try again in a minute."}, status_code=429,
                                headers={"Retry-After": str(RATE_WINDOW)})
        q.append(now)
        if len(_hits) > 10_000:           # don't let the table grow forever
            _hits.clear()
    return await call_next(request)


def require_key(x_api_key: Optional[str] = Header(None)):
    """Only trusted systems (hospitals, the control room) may change data."""
    expected = os.getenv("MEDX_API_KEY")
    if not expected:
        raise HTTPException(503, "Changing data is switched off: set MEDX_API_KEY on the server.")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Missing or wrong X-API-Key header.")


def twilio_signed(request: Request, form: dict):
    """True if the request really came from Twilio (or no Twilio token is set)."""
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not token:
        return True
    url = os.getenv("PUBLIC_WEBHOOK_URL") or str(request.url)
    payload = url + "".join(k + str(form[k]) for k in sorted(form))
    expected = base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(expected, request.headers.get("X-Twilio-Signature", ""))


# ---------- helpers ----------
def where(lat, lon, village):
    if lat is not None and lon is not None:
        return lat, lon
    if village:
        for v in data.villages():
            if v["name"].lower() == village.lower():
                return v["lat"], v["lon"]
        raise HTTPException(404, f"Unknown village '{village}'")
    raise HTTPException(400, "Give either lat and lon, or a village name")


def first_aid(etype, lang):
    tx = emergency.EM_TEXT[etype].get(lang) or emergency.EM_TEXT[etype]["en"]
    return {"label": tx["label"], "needs": tx["need"], "do": tx["do"], "dont": tx["dont"]}


def stock_view(stock):
    return {item: ("in stock" if qty > 0 else "out of stock") for item, qty in stock.items()}


def hospital_out(h):
    out = {"id": h["id"], "name": h["name"], "phone": h["phone"], "stock": stock_view(h["stock"])}
    if "km" in h:
        out.update({"km": h["km"], "eta_min": h["eta"]})
    return out


# ---------- models (what the requests look like) ----------
class EmergencyIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    village: Optional[str] = Field(None, max_length=100)
    lang: str = Field("en", pattern="^(en|kn|hi)$")


class StockIn(BaseModel):
    item: str = Field(..., max_length=40)
    in_stock: bool


class MedicineIn(BaseModel):
    brand: str = Field(..., max_length=80)
    salt: Optional[str] = Field(None, max_length=80)
    strength: Optional[str] = Field(None, max_length=30)
    pattern: str = Field("1-0-0", pattern=r"^\d(\.\d)?-\d(\.\d)?-\d(\.\d)?$")
    days: Optional[int] = Field(None, ge=1, le=365)


class MedicinesIn(BaseModel):
    medicines: List[MedicineIn] = Field(..., max_length=30)


class ReportIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    source: str = Field("whatsapp", pattern="^(call|whatsapp|sms)$")


# ---------- endpoints ----------
@app.get("/", tags=["info"])
def root():
    return {"name": "MedX API", "docs": "/docs", "status": "ok"}


@app.post("/emergency", tags=["emergency"])
def handle_emergency(body: EmergencyIn):
    """Understand an emergency message and find the nearest hospital that can actually treat it."""
    etype, summary = emergency.detect(body.message)
    if not etype:
        return {"type": None, "advice": "Could not tell the emergency type. Call 108 now."}
    lat, lon = where(body.lat, body.lon, body.village)
    nearest_any, ok = emergency.best_hospitals(etype, lat, lon)
    return {
        "type": etype,
        "summary": summary,
        "nearest_hospital": hospital_out(nearest_any),
        "nearest_has_treatment": ok is not None and nearest_any["id"] == ok["id"],
        "go_to": hospital_out(ok) if ok else None,
        "first_aid": first_aid(etype, body.lang),
        "advice": "Go now and call 108." if ok else "No hospital with this treatment found. Call 108 now.",
    }


@app.get("/hospitals", tags=["hospitals"])
def list_hospitals(need: Optional[str] = None, lat: Optional[float] = None,
                   lon: Optional[float] = None, village: Optional[str] = None):
    """Hospitals nearest first. Use need=antivenom_vials to only show hospitals that have it."""
    hs = data.hospitals()
    if lat is not None or village:
        la, lo = where(lat, lon, village)
        hs = geo.sort_by_distance(hs, la, lo)
    if need:
        if need not in STOCK_ITEMS:
            raise HTTPException(400, f"need must be one of {STOCK_ITEMS}")
        hs = [h for h in hs if h["stock"].get(need, 0) > 0]
    return [hospital_out(h) for h in hs]


@app.patch("/hospitals/{hospital_id}/stock", tags=["hospitals"], dependencies=[Depends(require_key)])
def update_stock(hospital_id: str, body: StockIn):
    """How hospitals keep their stock up to date (for example after using antivenom vials)."""
    if body.item not in STOCK_ITEMS:
        raise HTTPException(400, f"item must be one of {STOCK_ITEMS}")
    for h in data.hospitals():
        if h["id"] == hospital_id:
            h["stock"][body.item] = 1 if body.in_stock else 0
            return {"updated": hospital_out(h)}
    raise HTTPException(404, "Hospital not found")


@app.post("/medicines/check", tags=["medicines"])
def check_medicines(body: MedicinesIn):
    """Timetable, same-medicine-twice warnings and generic savings for a list of medicines."""
    med_list = [meds.fill_salt(dict(m)) for m in body.medicines]
    dups = meds.duplicates(med_list)
    return {
        "timetable": {slot: [f"{m['brand']} x{m['count']}" for m in items]
                      for slot, items in meds.schedule(med_list).items()},
        "duplicates": [{"salt": s.title(), "brands": [i["brand"] for i in items]} for s, items in dups.items()],
        "generic_savings": meds.generic_savings(med_list),
        "note": "Duplicates and generic switches must be confirmed by a pharmacist or doctor.",
    }


@app.post("/sar/reports", tags=["disaster rescue"], dependencies=[Depends(require_key)])
def add_report(body: ReportIn):
    """Add a flood/landslide report (from a call, WhatsApp or SMS) and get its priority."""
    if len(REPORTS) >= 2000:
        raise HTTPException(507, "Report list is full for this demo server.")
    report = {"id": f"R{len(REPORTS) + 1}", "source": body.source, "time": "now",
              "text": body.text, "lat": body.lat, "lon": body.lon, **sar.analyze(body.text)}
    REPORTS.append(report)
    return report


@app.get("/sar/zones", tags=["disaster rescue"])
def rescue_zones():
    """Rescue zones, most urgent first, with the teams to send."""
    zones = sar.build_zones(REPORTS, EVENT["places"])
    for z in zones:
        z.pop("reports", None)
    return {"event": EVENT["event"], "zones": zones}


@app.post("/webhook/whatsapp", tags=["channels"])
async def whatsapp_webhook(request: Request, Body: str = Form("", max_length=1000),
                           Latitude: Optional[float] = Form(None), Longitude: Optional[float] = Form(None)):
    """Ready for a Twilio WhatsApp number: a voice note's text or a message comes in,
    MedX replies with the hospital to go to and the first two first-aid steps."""
    form = {k: v for k, v in (await request.form()).items()}
    if not twilio_signed(request, form):
        raise HTTPException(403, "Request was not signed by Twilio.")
    etype, _ = await run_in_threadpool(emergency.detect, Body)
    if not etype:
        reply = "MedX: please tell us what happened (snakebite, dog bite, chest pain) and share your location. In danger? Call 108."
    elif Latitude is None or Longitude is None:
        reply = "MedX: we understood the emergency. Please share your location so we can find the right hospital. Call 108 now."
    else:
        _, ok = emergency.best_hospitals(etype, Latitude, Longitude)
        fa = first_aid(etype, "en")
        if ok:
            reply = (f"MedX: go to {ok['name']} ({ok['km']} km, ~{ok['eta']} min), {fa['needs']} in stock. "
                     f"Call 108. {fa['do'][0]} {fa['dont'][0]}")
        else:
            reply = "MedX: no hospital with this treatment found nearby. Call 108 now."
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(reply)}</Message></Response>'
    return Response(content=xml, media_type="application/xml")
