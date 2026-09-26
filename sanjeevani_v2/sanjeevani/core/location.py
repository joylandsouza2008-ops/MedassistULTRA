"""Automatic location: asks the browser for GPS as soon as the app opens.
The person taps Allow once; after that, every page knows where they are.
Shows a clear status in the sidebar so problems are easy to spot."""
import streamlit as st

from core import data, live
from core.i18n import t

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None


def _reset():
    for k in ("gps", "gps_denied", "gps_reason"):
        st.session_state.pop(k, None)
    st.session_state.gps_attempt = st.session_state.get("gps_attempt", 0) + 1


def auto_detect():
    """Call once per run from app.py (inside the sidebar)."""
    if "gps" in st.session_state:
        g = st.session_state.gps
        st.caption(t("gps_sidebar", place=g["name"]) + (f" (±{g['acc']} m)" if g.get("acc") else ""))
        if st.button(t("gps_refresh"), key="gps_refresh_btn"):
            _reset()
            st.rerun()
        return

    if get_geolocation is None:
        st.caption(t("gps_missing"))
        return

    if st.session_state.get("gps_denied"):
        st.caption(t("gps_denied", reason=st.session_state.get("gps_reason", "?")))
        if st.button(t("gps_retry"), key="gps_retry_btn"):
            _reset()
            st.rerun()
        return

    # a new key on every retry makes the browser ask again
    result = get_geolocation(f"gps_auto_{st.session_state.get('gps_attempt', 0)}")
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
        err = result["error"]
        reason = err.get("message") if isinstance(err, dict) else str(err)
        st.session_state.gps_denied = True
        st.session_state.gps_reason = (reason or "blocked")[:60]
        st.rerun()
    else:
        st.caption(t("gps_asking"))
        if st.button(t("gps_retry"), key="gps_retry_wait"):
            _reset()
            st.rerun()


def current(default_village=None):
    """Where the person is: live GPS if we have it, else a village from the demo data."""
    if "gps" in st.session_state:
        return st.session_state.gps
    v = data.village(default_village) if default_village else data.villages()[0]
    return {**v, "full": v["name"]}
