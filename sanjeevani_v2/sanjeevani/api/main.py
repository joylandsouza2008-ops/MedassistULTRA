"""MedX API: the same agent brain, usable by other systems.

WhatsApp bots, hospital software, IVR phone systems or a mobile app can all
call these endpoints instead of using the website.

Run (from the project folder):
    python -m uvicorn api.main:app --reload
Then open http://127.0.0.1:8000/docs to try every endpoint in the browser.
"""
import sys
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Form, HTTPException  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from pydantic import BaseModel  # noqa: E402

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
    message: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    village: Optional[str] = None
    lang: str = "en"


class StockIn(BaseModel):
    item: str
    in_stock: bool


class MedicineIn(BaseModel):
    brand: str
    salt: Optional[str] = None
    strength: Optional[str] = None
    pattern: str = "1-0-0"
    days: Optional[int] = None


class MedicinesIn(BaseModel):
    medicines: List[MedicineIn]


class ReportIn(BaseModel):
    text: str
    lat: float
    lon: float
    source: str = "whatsapp"


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


@app.patch("/hospitals/{hospital_id}/stock", tags=["hospitals"])
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


@app.post("/sar/reports", tags=["disaster rescue"])
def add_report(body: ReportIn):
    """Add a flood/landslide report (from a call, WhatsApp or SMS) and get its priority."""
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
def whatsapp_webhook(Body: str = Form(""), Latitude: Optional[float] = Form(None),
                     Longitude: Optional[float] = Form(None)):
    """Ready for a Twilio WhatsApp number: a voice note's text or a message comes in,
    MedX replies with the hospital to go to and the first two first-aid steps."""
    etype, _ = emergency.detect(Body)
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
