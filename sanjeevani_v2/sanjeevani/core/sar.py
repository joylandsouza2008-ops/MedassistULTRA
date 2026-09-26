"""Disaster mode (search and rescue).
Reads many emergency reports (calls, WhatsApp, SMS), scores who is in the most danger,
groups nearby reports into rescue zones, and suggests which teams to send first.
Works with simple keyword rules (English, Kannada, Hindi). AI can improve it when a key is set."""
import re

from core import data, geo

# flag: (danger points, words that point to it)
RULES = {
    "unconscious": (6, ["unconscious", "not breathing", "fainted", "ಪ್ರಜ್ಞೆ", "बेहोश"]),
    "trapped": (5, ["trapped", "stuck", "roof", "terrace", "surrounded", "ಸಿಕ್ಕಿ", "ಮಾಳಿಗೆ", "फँसे", "फंसे", "छत"]),
    "snakebite": (5, ["snake", "ಹಾವು", "सांप", "साँप"]),
    "injured": (4, ["injured", "bleeding", "fracture", "hurt", "ಗಾಯ", "घायल", "खून"]),
    "landslide": (4, ["landslide", "collapsed", "mudslide", "ಭೂಕುಸಿತ", "ಕುಸಿ", "भूस्खलन", "ढह"]),
    "water_rising": (3, ["water is rising", "water rising", "rising fast", "neck deep", "chest deep",
                         "ನೀರು ಏರು", "ನೀರು ಹೆಚ್ಚ", "पानी बढ़", "पानी भर"]),
    "vulnerable": (3, ["grandmother", "grandfather", "elderly", "old man", "old woman", "cannot walk", "bedridden",
                       "child", "children", "baby", "pregnant", "wheelchair",
                       "ಅಜ್ಜ", "ಅಜ್ಜಿ", "ಮಗು", "ಮಕ್ಕಳು", "ಗರ್ಭಿಣಿ",
                       "बुज़ुर्ग", "बुजुर्ग", "बच्चा", "बच्चे", "गर्भवती", "दादी", "दादा", "बिस्तर"]),
    "medicine": (2, ["insulin", "dialysis", "oxygen", "medicine", "tablets", "ಔಷಧಿ", "दवा"]),
    "food": (1, ["food", "drinking water", "hungry", "ಆಹಾರ", "ಊಟ", "ಕುಡಿಯುವ ನೀರು", "खाना", "पीने का पानी"]),
}

# which teams each situation needs
TEAMS = {
    "trapped": "team_boat", "water_rising": "team_boat",
    "landslide": "team_ndrf",
    "injured": "team_medical", "unconscious": "team_medical",
    "snakebite": "team_antivenom",
    "medicine": "team_medicine",
    "food": "team_food",
}
TEAM_ORDER = ["team_boat", "team_ndrf", "team_medical", "team_antivenom", "team_medicine", "team_food"]
LEVEL_COLORS = {"critical": "#C0392B", "high": "#E67E22", "medium": "#F1C40F", "low": "#2E86C1"}

PEOPLE_RE = re.compile(r"(\d+)\s*(people|persons|ppl|members|of us|ಜನ|लोग)", re.IGNORECASE)


def level_for(score):
    if score >= 13:
        return "critical"
    if score >= 8:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def analyze(text, flags=None, people=None):
    """Score one report. You can pass flags/people from the AI; otherwise keywords are used."""
    low = (text or "").lower()
    if flags is None:
        flags = [f for f, (_, words) in RULES.items() if any(w in low for w in words)]
    flags = [f for f in flags if f in RULES]
    if people is None:
        m = PEOPLE_RE.search(text or "")
        people = int(m.group(1)) if m else 1
    score = sum(RULES[f][0] for f in flags) + min(int(people), 20) * 0.5
    return {"flags": flags, "people": int(people), "score": round(score, 1), "level": level_for(score)}


def nearest_place(lat, lon, places):
    return min(places, key=lambda p: geo.distance_km(lat, lon, p["lat"], p["lon"]))["name"]


def build_zones(reports, places, radius_km=1.0):
    """Group reports that are within radius_km of each other into zones, most urgent first."""
    zones = []
    for r in reports:
        for z in zones:
            if geo.distance_km(r["lat"], r["lon"], z["lat"], z["lon"]) <= radius_km:
                z["reports"].append(r)
                z["lat"] = sum(x["lat"] for x in z["reports"]) / len(z["reports"])
                z["lon"] = sum(x["lon"] for x in z["reports"]) / len(z["reports"])
                break
        else:
            zones.append({"reports": [r], "lat": r["lat"], "lon": r["lon"]})

    out = []
    for i, z in enumerate(zones, 1):
        rs = z["reports"]
        flags = sorted({f for r in rs for f in r["flags"]}, key=lambda f: -RULES[f][0])
        # the worst report counts fully; every extra report confirming it adds 1 point
        score = max(r["score"] for r in rs) + (len(rs) - 1)
        teams = [t for t in TEAM_ORDER if any(TEAMS.get(f) == t for f in flags)]
        hospital = geo.sort_by_distance(data.hospitals(), z["lat"], z["lon"])[0]
        antivenom = None
        if "snakebite" in flags:
            ranked = geo.sort_by_distance(data.hospitals(), z["lat"], z["lon"])
            antivenom = next((h for h in ranked if h["stock"].get("antivenom_vials", 0) > 0), None)
        out.append({
            "id": f"Z{i}",
            "place": nearest_place(z["lat"], z["lon"], places),
            "lat": round(z["lat"], 5), "lon": round(z["lon"], 5),
            "report_ids": [r["id"] for r in rs],
            "reports": rs,
            # reports from the same spot usually describe the same people, so take the largest count
            "people": max(r["people"] for r in rs),
            "flags": flags,
            "teams": teams,
            "score": round(score, 1),
            "level": level_for(max(r["score"] for r in rs)),
            "hospital": {"name": hospital["name"], "km": hospital["km"]},
            "antivenom": {"name": antivenom["name"], "km": antivenom["km"]} if antivenom else None,
        })
    return sorted(out, key=lambda z: -z["score"])


def load_demo():
    d = data.load("disaster_reports")
    reports = [{**r, **analyze(r["text"])} for r in d["reports"]]
    return d, reports
