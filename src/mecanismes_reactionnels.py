"""
MÉCANISMES RÉACTIONNELS — classification des substitutions/éliminations nucléophiles (SN1/SN2/E1/E2)
par RÈGLES de chimie organique ÉTABLIES (manuels Clayden / Klein / Vollhardt).

Même posture FAUX=0 que `chimie` / `analyse_chimique` (la réalité juge, jamais un faux) :
  • Le MÉCANISME (corrélations structure/conditions -> chemin réactionnel) est un FAIT ÉTABLI et déterministe.
  • ABSTENTION STRUCTURELLE : on ne classe QUE les régimes où TOUS les facteurs textbook concordent sans
    ambiguïté. Tout cas borderline (substrat secondaire, facteurs en conflit, vocabulaire inconnu) -> ValueError.
    Faux négatif (abstention) toléré ; faux POSITIF interdit.

PRINCIPES ÉTABLIS UTILISÉS (certains, non controversés) :
  ── Molécularité / cinétique ──
    SN1, E1  : étape limitante UNImoléculaire (ionisation -> carbocation)  =>  cinétique d'ORDRE 1, rate = k·[substrat]
    SN2, E2  : étape limitante BImoléculaire (concertée)                    =>  cinétique d'ORDRE 2, rate = k·[substrat]·[Nu/base]
  ── Substrat (encombrement / stabilité du carbocation) ──
    méthyle / primaire : SN2 (jamais SN1 — carbocation trop instable) ; pas d'E1.
    tertiaire          : SN1 / E1 (carbocation stabilisé) ; SN2 DÉFAVORISÉ (encombrement bloque l'attaque dorsale).
    secondaire         : borderline -> ABSTENTION.
    méthyle            : aucun carbone β -> élimination IMPOSSIBLE.
  ── Nucléophile / base ──
    fort  -> voie bimoléculaire (SN2 / E2)   ;   faible -> voie unimoléculaire (SN1 / E1).
  ── Solvant ──
    polaire protique  -> favorise SN1 / E1 (stabilise carbocation et groupe partant par liaison H).
    polaire aprotique -> favorise SN2 / E2 (nucléophile « nu », très réactif).
  ── Stéréochimie ──
    SN2 : inversion de Walden ; SN1 : racémisation ; E2 : anti-périplanaire ; E1 : non stéréospécifique.

RÈGLE DE DÉCISION (FAUX=0) : un mécanisme n'est renvoyé que si substrat + force + solvant pointent UNANIMEMENT
vers ce mécanisme, dans un régime où le manuel est catégorique. Sinon ValueError.
"""
from __future__ import annotations

# ── Vocabulaire canonique (closed-set) ──────────────────────────────────────────────────────────────────────────
_SUBSTRATS = ("methyle", "primaire", "secondaire", "tertiaire")
_FORCES = ("fort", "faible")
_SOLVANTS = ("polaire_protique", "polaire_aprotique")
_MECANISMES = ("SN1", "SN2", "E1", "E2")

# Alias non ambigus tolérés (chaque alias -> un seul token canonique).
_ALIAS_SUBSTRAT = {
    "méthyle": "methyle", "methyl": "methyle",
    "1aire": "primaire", "2aire": "secondaire", "3aire": "tertiaire",
}
_ALIAS_FORCE = {
    "forte": "fort", "faibles": "faible",
}
_ALIAS_SOLVANT = {
    "protique": "polaire_protique", "polaire protique": "polaire_protique",
    "aprotique": "polaire_aprotique", "polaire aprotique": "polaire_aprotique",
}


def _token(x, valides, alias) -> str:
    """Normalise x en un token canonique de `valides`, sinon ValueError (vocabulaire inconnu)."""
    if isinstance(x, bool) or not isinstance(x, str):
        raise ValueError(f"paramètre non textuel : {x!r}")
    t = x.strip().lower()
    t = alias.get(t, t)
    if t not in valides:
        raise ValueError(f"valeur inconnue : {x!r} (attendu l'un de {valides})")
    return t


def _mecanisme(x) -> str:
    """Normalise un nom de mécanisme en SN1/SN2/E1/E2, sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, str):
        raise ValueError(f"mécanisme non textuel : {x!r}")
    t = x.strip().upper().replace(" ", "")
    if t not in _MECANISMES:
        raise ValueError(f"mécanisme inconnu : {x!r} (attendu SN1/SN2/E1/E2)")
    return t


# ── SUBSTITUTION NUCLÉOPHILE : SN1 vs SN2 ────────────────────────────────────────────────────────────────────────

def type_substitution(classe_substrat, nucleophile_force, solvant) -> str:
    """Classe la substitution nucléophile en 'SN1' ou 'SN2' UNIQUEMENT si les trois facteurs concordent.

    SN1  <=  substrat tertiaire  ET  nucléophile faible  ET  solvant polaire protique.
    SN2  <=  substrat méthyle/primaire  ET  nucléophile fort  ET  solvant polaire aprotique.
    Sinon (secondaire, facteurs en conflit, vocabulaire inconnu) -> ValueError (abstention).
    """
    s = _token(classe_substrat, _SUBSTRATS, _ALIAS_SUBSTRAT)
    nu = _token(nucleophile_force, _FORCES, _ALIAS_FORCE)
    sv = _token(solvant, _SOLVANTS, _ALIAS_SOLVANT)

    if s == "tertiaire" and nu == "faible" and sv == "polaire_protique":
        return "SN1"
    if s in ("methyle", "primaire") and nu == "fort" and sv == "polaire_aprotique":
        return "SN2"
    raise ValueError(
        f"régime non déterminant pour la substitution (substrat={s}, nucléophile={nu}, solvant={sv}) : abstention")


def sn2_defavorise_par_encombrement(classe_substrat) -> bool:
    """True si l'encombrement stérique DÉFAVORISE la SN2 (attaque dorsale bloquée) : vrai pour le substrat tertiaire.

    méthyle/primaire : non encombré -> SN2 favorisée (False). secondaire : possible mais ralentie -> False
    (non « défavorisée » au sens bloqué). tertiaire : SN2 essentiellement bloquée -> True.
    """
    s = _token(classe_substrat, _SUBSTRATS, _ALIAS_SUBSTRAT)
    return s == "tertiaire"


# ── ÉLIMINATION : E1 vs E2 ───────────────────────────────────────────────────────────────────────────────────────

def type_elimination(classe_substrat, base_force, solvant) -> str:
    """Classe l'élimination en 'E1' ou 'E2' UNIQUEMENT si les facteurs concordent.

    Substrat méthyle -> pas de carbone β -> élimination IMPOSSIBLE -> ValueError.
    E1  <=  substrat tertiaire  ET  base faible  ET  solvant polaire protique.
    E2  <=  substrat primaire/secondaire/tertiaire  ET  base forte  ET  solvant polaire aprotique.
    Sinon -> ValueError (abstention).
    """
    s = _token(classe_substrat, _SUBSTRATS, _ALIAS_SUBSTRAT)
    b = _token(base_force, _FORCES, _ALIAS_FORCE)
    sv = _token(solvant, _SOLVANTS, _ALIAS_SOLVANT)

    if s == "methyle":
        raise ValueError("substrat méthyle : aucun carbone β, élimination impossible")
    if s == "tertiaire" and b == "faible" and sv == "polaire_protique":
        return "E1"
    if s in ("primaire", "secondaire", "tertiaire") and b == "fort" and sv == "polaire_aprotique":
        return "E2"
    raise ValueError(
        f"régime non déterminant pour l'élimination (substrat={s}, base={b}, solvant={sv}) : abstention")


# ── CINÉTIQUE / MÉCANISME — faits exacts encodés par la molécularité ─────────────────────────────────────────────

def ordre_cinetique(mecanisme) -> int:
    """Ordre global de la cinétique : SN1/E1 -> 1 (unimoléculaire) ; SN2/E2 -> 2 (bimoléculaire)."""
    m = _mecanisme(mecanisme)
    return 1 if m in ("SN1", "E1") else 2


def concerte(mecanisme) -> bool:
    """True si le mécanisme est concerté (une seule étape) : SN2/E2 ; False si par étapes : SN1/E1."""
    m = _mecanisme(mecanisme)
    return m in ("SN2", "E2")


def passe_par_carbocation(mecanisme) -> bool:
    """True si le mécanisme passe par un intermédiaire carbocation : SN1/E1 ; False pour SN2/E2 (concertés)."""
    m = _mecanisme(mecanisme)
    return m in ("SN1", "E1")


def nombre_etapes(mecanisme) -> int:
    """Nombre d'étapes élémentaires : SN2/E2 -> 1 (concerté) ; SN1/E1 -> 2 (ionisation puis capture/déprotonation)."""
    m = _mecanisme(mecanisme)
    return 1 if m in ("SN2", "E2") else 2


def stereochimie(mecanisme) -> str:
    """Conséquence stéréochimique établie :
    SN2 -> 'inversion' (Walden) ; SN1 -> 'racemisation' ; E2 -> 'anti-periplanaire' ; E1 -> 'non-stereospecifique'.
    """
    m = _mecanisme(mecanisme)
    return {
        "SN2": "inversion",
        "SN1": "racemisation",
        "E2": "anti-periplanaire",
        "E1": "non-stereospecifique",
    }[m]
