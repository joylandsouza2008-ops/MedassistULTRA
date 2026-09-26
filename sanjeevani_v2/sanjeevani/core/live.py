"""Real, live data from OpenStreetMap (free, no key needed):
- geocode(): turns any place name into a location
- hospitals_near(): real hospitals and clinics around a location
Needs internet. If it fails, the app keeps working with the demo data."""
import json
import urllib.parse
import urllib.request

import streamlit as st

from core import geo

HEADERS = {"User-Agent": "Sanjeevani-hackathon/0.1 (Team Orbit, St Joseph Engineering College)"}


def _get_json(url, data=None, timeout=15):
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


@st.cache_data(ttl=86400, show_spinner=False)
def geocode(place):
    query = urllib.parse.urlencode({"q": f"{place}, India", "format": "json", "limit": 1})
    res = _get_json(f"https://nominatim.openstreetmap.org/search?{query}")
    if not res:
        return None
    r = res[0]
    return {"name": place.strip().title(), "full": r["display_name"],
            "lat": float(r["lat"]), "lon": float(r["lon"])}


@st.cache_data(ttl=3600, show_spinner=False)
def hospitals_near(lat, lon, radius_m=15000, limit=8):
    q = (f'[out:json][timeout:20];('
         f'node["amenity"="hospital"](around:{radius_m},{lat},{lon});'
         f'way["amenity"="hospital"](around:{radius_m},{lat},{lon});'
         f'node["amenity"="clinic"](around:{radius_m},{lat},{lon}););out center tags;')
    res = _get_json("https://overpass-api.de/api/interpreter",
                    data=urllib.parse.urlencode({"data": q}).encode())
    found = []
    for el in res.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        la = el.get("lat") or el.get("center", {}).get("lat")
        lo = el.get("lon") or el.get("center", {}).get("lon")
        if not name or la is None or lo is None:
            continue
        km = geo.road_km(lat, lon, la, lo)
        found.append({"name": name, "lat": la, "lon": lo, "km": round(km, 1), "eta": geo.eta_minutes(km),
                      "phone": tags.get("phone") or tags.get("contact:phone"),
                      "kind": tags.get("amenity", "hospital")})
    seen, unique = set(), []
    for h in sorted(found, key=lambda x: x["km"]):
        if h["name"].lower() not in seen:
            seen.add(h["name"].lower())
            unique.append(h)
    return unique[:limit]
