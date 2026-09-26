"""Medicine helpers: schedules, duplicates, generics, run-out prediction."""
from core import data, geo

SLOTS = ["Morning (8 AM)", "Afternoon (2 PM)", "Night (9 PM)"]


def parse_pattern(pattern):
    """'1-0-1' -> [1, 0, 1]  (morning, afternoon, night)."""
    try:
        parts = [int(float(x)) for x in str(pattern).replace(" ", "").split("-")]
        return (parts + [0, 0, 0])[:3]
    except (ValueError, AttributeError):
        return [0, 0, 0]


def per_day(pattern):
    return sum(parse_pattern(pattern))


def schedule(meds):
    """Group medicines by time of day."""
    out = {slot: [] for slot in SLOTS}
    for m in meds:
        for i, count in enumerate(parse_pattern(m.get("pattern"))):
            if count:
                out[SLOTS[i]].append({**m, "count": count})
    return out


def fill_salt(med):
    """If the salt is missing, look it up from our medicine list."""
    if not med.get("salt"):
        known = data.find_medicine(med.get("brand"))
        if known:
            med = {**med, "salt": known["salt"], "strength": med.get("strength") or known["strength"]}
    return med


def duplicates(meds):
    """Find different brands that contain the same salt (same medicine)."""
    groups = {}
    for m in meds:
        m = fill_salt(m)
        salt = (m.get("salt") or "").lower()
        if salt:
            groups.setdefault(salt, []).append(m)
    return {salt: items for salt, items in groups.items()
            if len({i["brand"].lower() for i in items}) > 1}


def generic_savings(meds):
    """For each medicine, show the cheapest generic and how much you save."""
    rows = []
    for m in meds:
        m = fill_salt(m)
        branded = data.find_medicine(m.get("brand"))
        options = data.generics_for(m.get("salt"), m.get("strength")) or data.generics_for(m.get("salt"))
        if not branded or not options:
            rows.append({"Prescribed": m.get("brand"), "Generic option": "Not found in demo list",
                         "Brand price / tab": None, "Generic price / tab": None, "You save for course": None})
            continue
        g = min(options, key=lambda x: x["price_per_strip"] / x["tabs_per_strip"])
        b_tab = branded["price_per_strip"] / branded["tabs_per_strip"]
        g_tab = g["price_per_strip"] / g["tabs_per_strip"]
        tabs = per_day(m.get("pattern")) * (m.get("days") or 30)
        rows.append({
            "Prescribed": m["brand"],
            "Generic option": g["brand"],
            "Brand price / tab": round(b_tab, 2),
            "Generic price / tab": round(g_tab, 2),
            "You save for course": round((b_tab - g_tab) * tabs),
        })
    return rows


def days_left(med):
    daily = per_day(med.get("pattern"))
    return None if daily == 0 else med.get("tablets_left", 0) // daily


def pharmacy_with(salts, lat, lon):
    """Nearest pharmacy that has ALL these salts in stock."""
    salts = [s.lower() for s in salts if s]
    for p in geo.sort_by_distance(data.pharmacies(), lat, lon):
        if all(p["stock"].get(s, 0) > 0 for s in salts):
            return p
    return None


def clean(row):
    """Table rows can contain NaN (empty cells). Turn those into None."""
    out = {}
    for k, v in row.items():
        if isinstance(v, float) and v != v:  # NaN check
            v = None
        if isinstance(v, str) and not v.strip():
            v = None
        out[k] = v
    return out
