# -*- coding: utf-8 -*-
"""MÉTÉO EN DIRECT — source STRUCTURÉE Open-Meteo (open-meteo.com : API publique, sans clé, JSON).

Exigence Yohan (2026-07-06) : « si Internet est activé, Provara peut très bien aller vérifier » — refuser la
météo web ON était incohérent. FAUX=0 : on ne rapporte QUE la réponse STRUCTURÉE de la source (température,
code temps WMO, vent), TOUJOURS attribuée (« source : open-meteo.com, relevé HH:MM ») — un relevé rapporté,
jamais une invention. Échec réseau/ville inconnue -> None (l'appelant s'abstient honnêtement).
Stdlib pure (urllib + json)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

_UA = "Provara (github.com/Provara-IA/Provara)"
_GEO = "https://geocoding-api.open-meteo.com/v1/search?"
_FCT = "https://api.open-meteo.com/v1/forecast?"

# Codes temps WMO -> libellé FR (table FERMÉE, doc open-meteo).
_WMO = {0: "ciel dégagé", 1: "plutôt dégagé", 2: "partiellement nuageux", 3: "couvert",
        45: "brouillard", 48: "brouillard givrant", 51: "bruine légère", 53: "bruine", 55: "bruine dense",
        56: "bruine verglaçante", 57: "bruine verglaçante dense", 61: "pluie légère", 63: "pluie",
        65: "pluie forte", 66: "pluie verglaçante", 67: "pluie verglaçante forte", 71: "neige légère",
        73: "neige", 75: "neige forte", 77: "grains de neige", 80: "averses légères", 81: "averses",
        82: "averses violentes", 85: "averses de neige", 86: "averses de neige fortes", 95: "orage",
        96: "orage avec grêle", 99: "orage avec forte grêle"}


def _get(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(ville: str):
    """(latitude, longitude, nom_affiché, pays) de la ville, ou None (inconnue). 1er résultat du géocodeur."""
    try:
        d = _get(_GEO + urllib.parse.urlencode({"name": ville, "count": 1, "language": "fr", "format": "json"}))
        res = (d.get("results") or [None])[0]
        if not res:
            return None
        return res["latitude"], res["longitude"], res.get("name") or ville, res.get("country") or ""
    except Exception:
        return None


def pluie_aujourdhui(ville: str):
    """Probabilité de PRÉCIPITATION max du JOUR pour `ville` : dict(nom, pays, proba_pluie [0-100]) ou None.
    Vient du champ STRUCTURÉ daily.precipitation_probability_max de la source — rapporté, jamais complété.
    Sert la décision quotidienne sous incertitude (« dois-je prendre un parapluie ? », decision.py)."""
    geo = geocode(ville)
    if not geo:
        return None
    lat, lon, nom, pays = geo
    try:
        d = _get(_FCT + urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "daily": "precipitation_probability_max", "forecast_days": 1}))
        probas = (d.get("daily") or {}).get("precipitation_probability_max") or []
        if not probas or probas[0] is None:
            return None
        return {"nom": nom, "pays": pays, "proba_pluie": int(probas[0])}
    except Exception:
        return None


def actuelle(ville: str):
    """Relevé ACTUEL pour `ville` : dict(nom, pays, temperature, ressenti, libelle, vent_kmh, heure) ou None.
    Tout vient de la réponse structurée de la source — rien n'est complété ni deviné."""
    geo = geocode(ville)
    if not geo:
        return None
    lat, lon, nom, pays = geo
    try:
        d = _get(_FCT + urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m"}))
        cur = d.get("current") or {}
        t = cur.get("temperature_2m")
        if t is None:
            return None
        code = cur.get("weather_code")
        heure = str(cur.get("time") or "")
        return {"nom": nom, "pays": pays, "temperature": float(t),
                "ressenti": cur.get("apparent_temperature"),
                "libelle": _WMO.get(int(code)) if code is not None else None,
                "vent_kmh": cur.get("wind_speed_10m"),
                "heure": heure[-5:] if "T" in heure else heure}
    except Exception:
        return None
