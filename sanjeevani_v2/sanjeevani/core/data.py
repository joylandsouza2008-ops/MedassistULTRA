"""Loads the fake demo data from the data/ folder.
In a real product this would come from a database that hospitals
and pharmacies update themselves."""
import json
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def load(name):
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def hospitals():
    return load("hospitals")


def pharmacies():
    return load("pharmacies")


def villages():
    return load("villages")


def medicines():
    return load("medicines")


def village(name):
    for v in villages():
        if v["name"] == name:
            return v
    return villages()[0]


def find_medicine(brand):
    """Find a medicine in our list by its brand name (not case sensitive)."""
    if not brand:
        return None
    for m in medicines():
        if m["brand"].lower() == brand.lower().strip():
            return m
    return None


def generics_for(salt, strength=None):
    """All cheap generic versions of the same salt."""
    out = []
    for m in medicines():
        if m["generic"] and m["salt"].lower() == (salt or "").lower():
            if strength is None or m["strength"] == strength:
                out.append(m)
    return out
