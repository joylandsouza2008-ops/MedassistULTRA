"""Distance helpers (no internet / Google Maps needed for the demo)."""
import math

AVG_RURAL_SPEED_KMPH = 30   # rough average on village roads
ROAD_FACTOR = 1.3           # roads are longer than a straight line


def distance_km(lat1, lon1, lat2, lon2):
    """Straight-line distance using the haversine formula."""
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def road_km(lat1, lon1, lat2, lon2):
    return distance_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR


def eta_minutes(km):
    return round(km / AVG_RURAL_SPEED_KMPH * 60)


def sort_by_distance(places, lat, lon):
    """Return places sorted nearest first, each with 'km' and 'eta' added."""
    out = []
    for p in places:
        km = road_km(lat, lon, p["lat"], p["lon"])
        out.append({**p, "km": round(km, 1), "eta": eta_minutes(km)})
    return sorted(out, key=lambda x: x["km"])
