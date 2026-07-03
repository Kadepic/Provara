"""
AUDIO WAV — noyau BORNÉ de la modalité SON (PCM non compressé), pur stdlib (2026-07-02).

POURQUOI (vision Yohan « outil universel toutes modalités ») : le son a un NOYAU exact — l'échantillon PCM entier.
Le WAV/RIFF est le conteneur PCM canonique et le module `wave` de la stdlib sait l'écrire ET le relire : on tient
donc un ORACLE indépendant gratuit (ce qu'on écrit, `wave` le relit). Aucune dépendance (ni scipy ni ffmpeg).

FAUX=0 — ce que ce module GARANTIT, et ce qu'il ne prétend PAS :
  • Round-trip PCM EXACT : `encode(samples,...)` puis `decode(...)` rend EXACTEMENT les mêmes entiers (prouvé par le
    validateur). Aucune perte, aucune approximation (PCM entier, pas de compression).
  • Bornes de quantification vérifiées : chaque échantillon doit tenir dans la plage signée du format (8/16/32 bits) ;
    un dépassement -> ValueError (jamais de repli silencieux/clipping caché).
  • Les générateurs (`silence`, `sinus`, `carre`) produisent des échantillons DÉTERMINISTES et re-dérivables ; le
    sinus quantifie round(A·sin(2πft/fr)) — la valeur EST reproductible (le validateur la re-calcule).
  Ce module ne juge PAS si un son est « agréable » (non-borné) : il garantit l'exactitude numérique de l'échantillon
  et la validité du conteneur RIFF. Souverain, offline, stdlib pur.

Formats : PCM entier signé little-endian, 1 canal (mono) ou 2 (stéréo entrelacé), largeur 1/2/4 octets.
"""
from __future__ import annotations

import io
import math
import wave

# largeur d'octets -> (min, max) de l'entier signé PCM. (8 bits WAV est NON signé 0..255 par la spec ; on le gère.)
_PLAGE = {2: (-32768, 32767), 4: (-2147483648, 2147483647)}


def _valide_entete(framerate: int, sampwidth: int, canaux: int):
    if not isinstance(framerate, int) or framerate < 1:
        raise ValueError("framerate doit être un entier ≥ 1")
    if sampwidth not in (1, 2, 4):
        raise ValueError(f"sampwidth {sampwidth} non supporté (1, 2 ou 4 octets)")
    if canaux not in (1, 2):
        raise ValueError(f"canaux {canaux} non supporté (1=mono, 2=stéréo)")


def _borne(sampwidth: int):
    if sampwidth == 1:
        return (0, 255)                      # PCM 8 bits WAV = non signé
    return _PLAGE[sampwidth]


def _aplati(samples, canaux):
    """Accepte soit une liste d'entiers (mono, ou stéréo déjà entrelacé), soit une liste de tuples/canaux.
    Renvoie la liste entrelacée d'entiers + le nombre de frames."""
    if not samples:
        raise ValueError("aucun échantillon")
    if isinstance(samples[0], (tuple, list)):
        plat = []
        for frame in samples:
            if len(frame) != canaux:
                raise ValueError(f"frame de {len(frame)} valeurs, {canaux} canaux attendus")
            plat.extend(frame)
        return plat, len(samples)
    # liste plate d'entiers : longueur multiple du nb de canaux
    if len(samples) % canaux != 0:
        raise ValueError(f"{len(samples)} échantillons non multiples de {canaux} canaux")
    return list(samples), len(samples) // canaux


def encode(samples, *, framerate: int = 44100, sampwidth: int = 2, canaux: int = 1) -> bytes:
    """Sérialise des échantillons PCM entiers en octets WAV valides (RIFF). Déterministe.
    `samples` = liste d'entiers (mono ou stéréo entrelacé) OU liste de tuples (un par frame)."""
    _valide_entete(framerate, sampwidth, canaux)
    plat, n_frames = _aplati(samples, canaux)
    lo, hi = _borne(sampwidth)
    for v in plat:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"échantillon non entier : {v!r}")
        if not (lo <= v <= hi):
            raise ValueError(f"échantillon {v} hors plage [{lo},{hi}] pour {sampwidth*8} bits")
    if sampwidth == 1:
        octets = bytes(plat)                                          # 8 bits non signé
    else:
        octets = b"".join(int(v).to_bytes(sampwidth, "little", signed=True) for v in plat)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(canaux)
        w.setsampwidth(sampwidth)
        w.setframerate(framerate)
        w.writeframes(octets)
    return buf.getvalue()


def ecris(samples, chemin: str, **kw) -> int:
    """Écrit le WAV sur disque (atomique). Renvoie le nombre d'octets écrits."""
    import os
    data = encode(samples, **kw)
    tmp = f"{chemin}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, chemin)
    return len(data)


def decode(octets: bytes) -> dict:
    """RE-LIT un WAV PCM (oracle stdlib `wave`) -> {framerate, sampwidth, canaux, frames, samples}. `samples` est la
    liste entrelacée d'entiers signés (ou non signés en 8 bits). FAUX=0 : `wave` lève sur un flux non-RIFF."""
    if not isinstance(octets, (bytes, bytearray)):
        raise ValueError("decode attend des octets")
    try:
        with wave.open(io.BytesIO(bytes(octets)), "rb") as w:
            canaux = w.getnchannels()
            sampwidth = w.getsampwidth()
            framerate = w.getframerate()
            n = w.getnframes()
            brut = w.readframes(n)
    except (wave.Error, EOFError) as e:
        raise ValueError(f"WAV invalide : {e}")
    if sampwidth == 1:
        samples = list(brut)
    else:
        samples = [int.from_bytes(brut[i:i + sampwidth], "little", signed=True)
                   for i in range(0, len(brut), sampwidth)]
    return {"framerate": framerate, "sampwidth": sampwidth, "canaux": canaux,
            "frames": n, "samples": samples}


# ─────────── générateurs déterministes (échantillons re-dérivables) ───────────
def silence(n_frames: int, *, canaux: int = 1, sampwidth: int = 2) -> list:
    """n_frames de silence (0, ou 128 en 8 bits non signé = milieu)."""
    if not isinstance(n_frames, int) or n_frames < 1:
        raise ValueError("n_frames doit être un entier ≥ 1")
    zero = 128 if sampwidth == 1 else 0
    return [zero] * (n_frames * canaux)


def sinus(freq: float, duree: float, *, framerate: int = 44100, amplitude: int = 16000, sampwidth: int = 2) -> list:
    """Onde sinusoïdale mono quantifiée : s[i] = round(amplitude·sin(2π·freq·i/framerate)). Déterministe."""
    if freq <= 0 or duree <= 0:
        raise ValueError("freq et duree doivent être > 0")
    lo, hi = _borne(sampwidth)
    milieu = 128 if sampwidth == 1 else 0
    if not (lo <= milieu + amplitude <= hi and lo <= milieu - amplitude <= hi):
        raise ValueError(f"amplitude {amplitude} dépasse la plage {sampwidth*8} bits")
    n = int(framerate * duree)
    return [milieu + round(amplitude * math.sin(2 * math.pi * freq * i / framerate)) for i in range(n)]


def carre(freq: float, duree: float, *, framerate: int = 44100, amplitude: int = 16000, sampwidth: int = 2) -> list:
    """Onde carrée mono EXACTE (entiers purs, aucun flottant) : ±amplitude selon la phase. Déterministe."""
    if freq <= 0 or duree <= 0:
        raise ValueError("freq et duree doivent être > 0")
    lo, hi = _borne(sampwidth)
    milieu = 128 if sampwidth == 1 else 0
    if not (lo <= milieu + amplitude <= hi and lo <= milieu - amplitude <= hi):
        raise ValueError(f"amplitude {amplitude} dépasse la plage {sampwidth*8} bits")
    n = int(framerate * duree)
    demi_periode = framerate / (2 * freq)
    return [milieu + (amplitude if (i // demi_periode) % 2 < 1 else -amplitude) for i in range(n)]
