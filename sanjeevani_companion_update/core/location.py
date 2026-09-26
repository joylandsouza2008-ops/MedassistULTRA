"""Automatic location: asks the browser for GPS as soon as the app opens.
The person taps Allow once; after that, every page knows where they are."""
import streamlit as st

from core import data, live
from core.i18n import t

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None


def auto_detect():
    """Call once per run from app.py (inside the sidebar)."""
    if "gps" in st.session_state:
        st.caption(t("gps_sidebar", place=st.session_state.gps["name"]))
        return
    if get_geolocation is None or st.session_state.get("gps_denied"):
        return
    result = get_geolocation("gps_auto")
    coords = result.get("coords") if isinstance(result, dict) else None
    if coords and coords.get("latitude") is not None:
        lat, lon = float(coords["latitude"]), float(coords["longitude"])
        try:
            place = live.reverse_geocode(round(lat, 4), round(lon, 4))
        except Exception:
            place = {"name": "My location", "full": ""}
        st.session_state.gps = {"name": place["name"], "lat": lat, "lon": lon,
                                "full": place["full"] or f"{lat:.5f}, {lon:.5f}",
                                "acc": int(coords.get("accuracy") or 0)}
        st.session_state.em_place = place["name"]   # pre-fill the Emergency page
        st.rerun()
    elif isinstance(result, dict) and result.get("error"):
        st.session_state.gps_denied = True
    else:
        st.caption(t("gps_asking"))


def current(default_village=None):
    """Where the person is: live GPS if we have it, else a village from the demo data."""
    if "gps" in st.session_state:
        return st.session_state.gps
    v = data.village(default_village) if default_village else data.villages()[0]
    return {**v, "full": v["name"]}
