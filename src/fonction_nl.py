"""
ROUTAGE NL → SOUS-SYSTÈMES FONCTION (module LÉGER — pas de lecteur).

Le lecteur DATA couvre les FAITS (capitale, masse atomique d'un élément…) mais PAS les fonctions CALCULÉES :
code morse, alphabet OTAN, masse molaire d'une formule, complément d'un brin d'ADN. Ce module ROUTE une question
en langage naturel vers le bon moteur fonction (`references` / `chimie` / `genetique`) par mots-clés, puis relaie
son verdict — qui est DÉJÀ sound (VÉRIFIÉ exact ou HORS).

INVARIANT FAUX=0 : on ne répond QUE si le moteur dit VÉRIFIÉ ; sinon HORS honnête. On exige un mot-clé fort
(« morse », « molaire », « complément »…), sinon on s'abstient (on ne route pas une question DATA/géo par erreur).
Pour les fonctions mono-caractère (morse, OTAN) appliquées à un MOT, on compose lettre par lettre : si UNE seule
lettre est hors-table, HORS global (jamais de réponse partielle). L'argument est extrait sur la question BRUTE
pour préserver la CASSE (les formules « H2O » et séquences « ATCG » en dépendent).

Ces modules (references/chimie/genetique) sont légers (aucun import lecteur) : ce module reste léger et testable
en <1 s, indépendamment du moteur DATA (resolution.py / lecteur.py).
"""
from __future__ import annotations

import math
import re

from base_faits import VERIFIE, HORS, normalise

_ARG_RE = re.compile(r"(?:\bde la\b|\bde l['’]|\bdu\b|\bdes\b|\bde\b|\bdans\b|\bpour\b|\ben\b|:|=)\s+(.+)$", re.IGNORECASE)

# ————————————————————————————————— PHYSIQUE NL (formules paramétriques, SI strict) —————————————————————————————————
# On extrait les nombres ÉTIQUETÉS PAR LEUR UNITÉ SI (« 2 kg » -> masse, « 10 m/s » -> vitesse). Anti-FAUX :
#   • SEULES les unités SI de BASE attendues par le moteur (kg, m, m/s, Hz, V, A, Ω, J, N…) — PAS km/cm/g
#     (sinon erreur d'échelle = nombre faux). Une mesure dans une unité dérivée -> non reconnue -> HORS.
#   • règle « EXACTEMENT UNE valeur par rôle » : 0 (manquant) ou ≥2 (ambigu) -> HORS, jamais d'assignation devinée.
#   • la grandeur est désignée par des mots-clés SPÉCIFIQUES (cinétique/photon/ohm…) ; on relaie le verdict de
#     `physique.calcule` (VÉRIFIÉ exact ou HORS). Le nombre rendu est donc soit juste pour CETTE grandeur, soit rien.
_NUM = r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?"
# (motif d'unité, rôle) — ordre LONGUEST-FIRST : « m/s² » avant « m/s » avant « m ».
_UNITES = [
    (r"m\s*/\s*s\s*[²2]", "acceleration"),
    (r"m\s*/\s*s", "vitesse"),
    (r"hz|hertz", "frequence"),
    (r"kg|kilogrammes?", "masse"),
    (r"ohms?|Ω", "resistance"),
    (r"newtons?|N", "force"),
    (r"volts?|V", "tension"),
    (r"amp[eè]res?|A", "courant"),
    (r"joules?|J", "energie"),
    (r"m[eè]tres?|m", "longueur"),
]
_PAIRE_MESURE = re.compile(rf"({_NUM})\s*(" + "|".join(u for u, _ in _UNITES) + r")\b", re.IGNORECASE)
# Routage grandeur : (nom, [ensembles de mots-clés — TOUS doivent intersecter], {param: rôle}). Ordre = spécifique
# d'abord (1er match gagne) : « potentielle » avant « gravité/surface » qui partagent masse+longueur.
_PHYS = [
    ("energie_cinetique", [{"cinetique"}], {"m": "masse", "v": "vitesse"}),
    ("energie_potentielle_pesanteur", [{"potentielle"}], {"m": "masse", "h": "longueur"}),
    ("energie_photon", [{"photon"}], {"frequence": "frequence"}),
    ("energie_repos", [{"repos"}], {"m": "masse"}),
    ("quantite_mouvement", [{"mouvement", "impulsion"}], {"m": "masse", "v": "vitesse"}),
    ("vitesse_onde", [{"onde"}, {"vitesse", "celerite"}], {"frequence": "frequence", "longueur_onde": "longueur"}),
    ("moment_force", [{"moment"}, {"force"}], {"force": "force", "bras_levier": "longueur"}),
    ("travail", [{"travail"}], {"force": "force", "deplacement": "longueur"}),
    ("puissance_electrique", [{"puissance"}, {"electrique"}], {"U": "tension", "I": "courant"}),
    ("loi_ohm_tension", [{"ohm", "tension"}], {"R": "resistance", "I": "courant"}),
    ("force_newton", [{"force", "newton"}, {"acceleration", "accelere"}], {"m": "masse", "a": "acceleration"}),
    ("force_poids", [{"poids"}], {"m": "masse"}),
    ("gravite_surface", [{"gravite", "surface"}], {"M": "masse", "r": "longueur"}),
]


def _mesures(question: str) -> dict:
    """Nombres ÉTIQUETÉS par rôle d'unité SI. Renvoie {rôle: [valeurs]}. « 2 kg et 10 m/s » -> {masse:[2], vitesse:[10]}."""
    par_role: dict = {}
    for m in _PAIRE_MESURE.finditer(question):
        val = float(m.group(1).replace(",", "."))
        unite = m.group(2)
        for motif, role in _UNITES:                 # même ordre longest-first -> rôle non ambigu
            if re.fullmatch(motif, unite, re.IGNORECASE):
                par_role.setdefault(role, []).append(val)
                break
    return par_role


def resout_physique(question: str):
    """Calcule une grandeur physique par formule (module `physique`, SI). (VERIFIE, texte, source) ou (HORS,...)."""
    try:
        import physique as _P
    except Exception:
        return (HORS, None, None)
    qtoks = set(normalise(question).split())
    par_role = _mesures(question)
    for grandeur, motscles, params in _PHYS:
        if not all(qtoks & grp for grp in motscles):
            continue
        valeurs = {}
        ok = True
        for nom_param, role in params.items():
            vals = par_role.get(role, [])
            if len(vals) != 1:                       # 0 = manquant, ≥2 = ambigu -> on n'assigne JAMAIS au hasard
                ok = False
                break
            valeurs[nom_param] = vals[0]
        if not ok:
            continue
        st, val, unite = _P.calcule(grandeur, valeurs)
        if st == VERIFIE and val is not None:
            lib = grandeur.replace("_", " ")
            return (VERIFIE, f"{val} {unite}", f"calcul physique — {lib} (formule + constantes SI/CODATA)")
        return (HORS, None, None)                    # grandeur désignée mais domaine invalide -> HORS (pas d'essai suivant)
    return (HORS, None, None)


def _extrait_arg_brut(question: str) -> str:
    """Argument d'une fonction (formule/lettre/séquence) en CASSE ORIGINALE — « masse molaire de H2O » -> « H2O »."""
    q = question.strip().rstrip("?.! ")
    m = _ARG_RE.search(q)
    arg = m.group(1) if m else (q.split()[-1] if q.split() else "")
    return arg.strip(" ?.!\"'«»").strip()


def _compose_par_lettre(mot: str, fn):
    """Applique une fonction MONO-CARACTÈRE (morse, nato) à chaque lettre/chiffre d'un mot. Sound : si UNE seule
    lettre échoue -> None (HORS global, pas de réponse partielle). Un espace -> séparateur « / »."""
    sorties = []
    for ch in mot:
        if ch.isspace():
            sorties.append("/")
            continue
        st, val = fn(ch)
        if st != VERIFIE or val is None:
            return None
        sorties.append(str(val))
    return " ".join(sorties) if sorties else None


def _dernier_token(question: str) -> str:
    """Dernier mot de la question, casse préservée — la formule/séquence est un token contigu (« … de H2O »->H2O)."""
    toks = question.strip().rstrip("?.! ").split()
    return toks[-1].strip(" ?.!\"'«».,") if toks else ""


def _essaie(fn, *cands):
    """Essaie une fonction (formule/séquence) sur plusieurs candidats d'argument, du plus probable au repli. Renvoie
    la valeur du PREMIER candidat VÉRIFIÉ, sinon None. Sound : tout candidat non vérifié est ignoré (jamais inventé)."""
    for c in cands:
        if not c:
            continue
        st, val = fn(c)
        if st == VERIFIE and val is not None:
            return val
    return None


# ————————————————————————————————— CONVERSION D'UNITÉS (table FERMÉE, facteurs EXACTS, même dimension) —————————————————————————————————
# FAUX=0 : on ne convertit QU'entre 2 unités d'une MÊME dimension (longueur/masse/temps), via une table FERMÉE de
# facteurs EXACTS (préfixes métriques décimaux ; conventions s/min/h/jour/semaine — toutes exactes par définition).
# Conversion INTER-dimension (km->kg) ou unité INCONNUE -> HORS (jamais de nombre faux). Résultat exact (entier si
# entier). On exclut les unités AMBIGUËS (livre/once : masse vs volume/livre-objet) pour rester FAUX=0.
_CONV_UNITS = {
    # longueur (base = mètre)
    "mm": ("L", 0.001), "millimetre": ("L", 0.001), "millimetres": ("L", 0.001),
    "cm": ("L", 0.01), "centimetre": ("L", 0.01), "centimetres": ("L", 0.01),
    "dm": ("L", 0.1), "decimetre": ("L", 0.1), "decimetres": ("L", 0.1),
    "m": ("L", 1.0), "metre": ("L", 1.0), "metres": ("L", 1.0),
    "km": ("L", 1000.0), "kilometre": ("L", 1000.0), "kilometres": ("L", 1000.0),
    # masse (base = gramme)
    "mg": ("M", 0.001), "milligramme": ("M", 0.001), "milligrammes": ("M", 0.001),
    "g": ("M", 1.0), "gramme": ("M", 1.0), "grammes": ("M", 1.0),
    "kg": ("M", 1000.0), "kilogramme": ("M", 1000.0), "kilogrammes": ("M", 1000.0),
    "tonne": ("M", 1_000_000.0), "tonnes": ("M", 1_000_000.0),
    # temps (base = seconde)
    "milliseconde": ("T", 0.001), "millisecondes": ("T", 0.001),
    "seconde": ("T", 1.0), "secondes": ("T", 1.0),
    "min": ("T", 60.0), "minute": ("T", 60.0), "minutes": ("T", 60.0),
    "heure": ("T", 3600.0), "heures": ("T", 3600.0),
    "jour": ("T", 86400.0), "jours": ("T", 86400.0), "journee": ("T", 86400.0), "journees": ("T", 86400.0),
    "semaine": ("T", 604800.0), "semaines": ("T", 604800.0),
    # volume (base = litre ; m³/cm³ par définition du litre = 1 dm³)
    "ml": ("V", 0.001), "millilitre": ("V", 0.001), "millilitres": ("V", 0.001),
    "cl": ("V", 0.01), "centilitre": ("V", 0.01), "centilitres": ("V", 0.01),
    "dl": ("V", 0.1), "decilitre": ("V", 0.1), "decilitres": ("V", 0.1),
    "l": ("V", 1.0), "litre": ("V", 1.0), "litres": ("V", 1.0),
    "hectolitre": ("V", 100.0), "hectolitres": ("V", 100.0),
    "m3": ("V", 1000.0), "metre cube": ("V", 1000.0), "metres cubes": ("V", 1000.0),
    "cm3": ("V", 0.001), "centimetre cube": ("V", 0.001), "centimetres cubes": ("V", 0.001),
    # aire (base = m² ; hectare/are = définitions exactes)
    "m2": ("A", 1.0), "metre carre": ("A", 1.0), "metres carres": ("A", 1.0),
    "cm2": ("A", 0.0001), "centimetre carre": ("A", 0.0001), "centimetres carres": ("A", 0.0001),
    "km2": ("A", 1_000_000.0), "kilometre carre": ("A", 1_000_000.0), "kilometres carres": ("A", 1_000_000.0),
    "hectare": ("A", 10000.0), "hectares": ("A", 10000.0), "ha": ("A", 10000.0),
    "are": ("A", 100.0), "ares": ("A", 100.0),
    # longueurs impériales (définitions légales exactes : 1 pied = 0,3048 m ; 1 pouce = 0,0254 m)
    "pied": ("L", 0.3048), "pieds": ("L", 0.3048), "pouce": ("L", 0.0254), "pouces": ("L", 0.0254),
    "yard": ("L", 0.9144), "yards": ("L", 0.9144), "mile": ("L", 1609.344), "miles": ("L", 1609.344),
    # données (préfixes SI DÉCIMAUX : 1 Go = 1000 Mo — les préfixes binaires Gio/Mio valent 1024, dit en source)
    "octet": ("D", 1.0), "octets": ("D", 1.0),
    "ko": ("D", 1000.0), "kilooctet": ("D", 1000.0), "kilooctets": ("D", 1000.0),
    "mo": ("D", 1_000_000.0), "megaoctet": ("D", 1_000_000.0), "megaoctets": ("D", 1_000_000.0),
    "go": ("D", 1_000_000_000.0), "gigaoctet": ("D", 1_000_000_000.0), "gigaoctets": ("D", 1_000_000_000.0),
    "to": ("D", 1_000_000_000_000.0), "teraoctet": ("D", 1_000_000_000_000.0), "teraoctets": ("D", 1_000_000_000_000.0),
    # vitesse (base = m/s ; km/h = 1000/3600 exact ; nœud = 1852 m/h, définition légale du mille marin).
    # Clés AVEC « / » (la normalisation locale le préserve) ET sans (formes parlées).
    "m/s": ("S", 1.0), "km/h": ("S", 1000.0 / 3600.0),
    "m s": ("S", 1.0), "metre par seconde": ("S", 1.0), "metres par seconde": ("S", 1.0),
    "km h": ("S", 1000.0 / 3600.0), "kmh": ("S", 1000.0 / 3600.0),
    "kilometre par heure": ("S", 1000.0 / 3600.0), "kilometres par heure": ("S", 1000.0 / 3600.0),
    "kilometre heure": ("S", 1000.0 / 3600.0), "kilometres heure": ("S", 1000.0 / 3600.0),
    "noeud": ("S", 1852.0 / 3600.0), "noeuds": ("S", 1852.0 / 3600.0),
}
# alternance longest-first : « kilometre » avant « metre » avant « m » ; « secondes » avant « s ».
_UNIT_ALT = "|".join(sorted((re.escape(u) for u in _CONV_UNITS), key=len, reverse=True))
_CONV_EN = re.compile(rf"({_NUM})\s*({_UNIT_ALT})\b\s+(?:en|vers)\s+({_UNIT_ALT})\b", re.IGNORECASE)
_CONV_DANS = re.compile(
    rf"combien\s+d(?:e|')\s*({_UNIT_ALT})\b\s+dans\s+(?:(?:un|une|le|la|l['’])\s+|({_NUM})\s*)?({_UNIT_ALT})\b",
    re.IGNORECASE)


def _fmt_nombre(val: float) -> str:
    """Entier sans décimale si entier, sinon arrondi propre (pas d'artefact flottant)."""
    if val == int(val):
        return str(int(val))
    return ("%.6f" % val).rstrip("0").rstrip(".")


def _norm_conv(s: str) -> str:
    """Normalisation LOCALE des conversions : accents/casse comme normalise(), mais PRÉSERVE « , . / » —
    normalise() les mange, ce qui tronquait « 1,5 heures » en « 5 heures » (300 min servi pour 90, FAUX vécu
    2026-07-08) et cassait « km/h »."""
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def compare_grandeurs(question: str):
    """COMPARAISON de deux grandeurs d'unités COMPARABLES : « 100 km/h ou 30 m/s, lequel est le plus rapide ? »,
    « 2 kg est-il plus lourd que 1500 g » -> les deux converties dans la même base (facteurs EXACTS) puis
    comparées ; l'équivalence du perdant est MONTRÉE dans l'unité du gagnant (re-vérifiable d'un coup d'œil).
    Dimensions différentes ou unité inconnue -> None. Devinette du kilo (plomb/plumes) : réponse exacte."""
    q = _norm_conv(question)
    madj = re.search(r"plus\s+(rapide|vite|lourde?s?|l[ée]g[eè]re?s?|longs?|longues?|courte?s?|grande?s?|petite?s?)\b", q)
    if madj:
        mcv = re.search(rf"({_NUM})\s*({_UNIT_ALT})\b\s+(?:ou|que)\s+(?:celui\s+de\s+)?({_NUM})\s*({_UNIT_ALT})\b", q) \
            or re.search(rf"({_NUM})\s*({_UNIT_ALT})\b[^0-9]{{0,35}}\b(?:ou|que)\b[^0-9]{{0,10}}({_NUM})\s*({_UNIT_ALT})\b", q)
        if mcv:
            n1, u1, n2, u2 = (float(mcv.group(1).replace(",", ".")), mcv.group(2).lower(),
                              float(mcv.group(3).replace(",", ".")), mcv.group(4).lower())
            d1, d2 = _CONV_UNITS.get(u1), _CONV_UNITS.get(u2)
            if d1 and d2 and d1[0] == d2[0]:
                b1, b2 = n1 * d1[1], n2 * d2[1]
                a1, a2 = "%s %s" % (_fmt_nombre(n1), u1), "%s %s" % (_fmt_nombre(n2), u2)
                if b1 == b2:
                    return "Ils sont égaux (%s = %s après conversion)." % (a1, a2)
                adj = {"vite": "rapide"}.get(madj.group(1), madj.group(1))
                inverse = bool(re.match(r"l[ée]g|court|petit", adj))     # « plus léger » = le plus PETIT gagne
                gagne_1 = (b1 > b2) != inverse
                gagnant, perdant = (a1, a2) if gagne_1 else (a2, a1)
                u_g, d_g = (u1, d1) if gagne_1 else (u2, d2)
                b_p = b2 if gagne_1 else b1
                return ("%s est plus %s que %s (%s = %s %s après conversion)."
                        % (gagnant, adj, perdant, perdant, _fmt_nombre(b_p / d_g[1]), u_g))
    # DEVINETTE CLASSIQUE, réponse exacte : un kilo est un kilo, quelle que soit la matière.
    if re.search(r"plus\s+lourd", q) and re.search(r"(?:kilo|kg)\s+de\s+\w+\s+ou\s+(?:un\s+)?(?:kilo|kg)\s+de\s+\w+", q):
        return ("Ils pèsent exactement pareil : un kilogramme est un kilogramme, la masse ne dépend "
                "pas de la matière.")
    return None


def resout_conversion(question: str):
    """Convertit entre 2 unités de MÊME dimension (table fermée, exacte). (VERIFIE, texte, source) ou (HORS,None,None).
    FAUX=0 : unité inconnue ou dimensions différentes -> HORS. Ne fire que sur un motif de conversion explicite."""
    q = _norm_conv(question)                         # accents/casse normalisés, décimales et « / » PRÉSERVÉS
    # « X <unité> et demie / et quart / et trois quarts » -> X.5 / X.25 / X.75 (« 2 heures et demie » valait
    # 2 heures : 7200 s servi pour 9000, FAUX vécu 2026-07-08). Réécriture AVANT le motif de conversion.
    q = re.sub(r"(\d+(?:[.,]\d+)?)\s+([a-z³²/ ]+?)\s+et\s+trois\s+quarts?\b",
               lambda m: "%s %s" % (float(m.group(1).replace(",", ".")) + 0.75, m.group(2)), q)
    q = re.sub(r"(\d+(?:[.,]\d+)?)\s+([a-z³²/ ]+?)\s+et\s+demie?s?\b",
               lambda m: "%s %s" % (float(m.group(1).replace(",", ".")) + 0.5, m.group(2)), q)
    q = re.sub(r"(\d+(?:[.,]\d+)?)\s+([a-z³²/ ]+?)\s+et\s+quarts?\b",
               lambda m: "%s %s" % (float(m.group(1).replace(",", ".")) + 0.25, m.group(2)), q)
    # SEMAINES DANS UNE ANNÉE : durée VARIABLE (365/366 j) -> réponse composée honnête, pas un facteur menteur.
    if re.search(r"semaines?\s+dans\s+(?:une?\s+|l['’]\s*)?annee", q):
        return (VERIFIE, "52 semaines et 1 jour (année de 365 jours) ; 52 semaines et 2 jours si bissextile (366).",
                "calendrier — 365 = 52×7 + 1")
    # COMPARAISON de deux grandeurs d'unités COMPARABLES (logique partagée avec _cap_comparaison de repond).
    cg = compare_grandeurs(question)
    if cg:
        return (VERIFIE, cg, "conversion + comparaison exactes")

    m = _CONV_EN.search(q)
    if m:
        num = float(m.group(1).replace(",", ".")); src = m.group(2).lower(); dst = m.group(3).lower()
    else:
        m = _CONV_DANS.search(q)
        if not m:
            return (HORS, None, None)
        dst = m.group(1).lower(); num = float((m.group(2) or "1").replace(",", ".")); src = m.group(3).lower()
    du = _CONV_UNITS.get(src); tu = _CONV_UNITS.get(dst)
    if not du or not tu or du[0] != tu[0]:           # unité inconnue OU dimensions différentes -> HORS (jamais faux)
        return (HORS, None, None)
    val = num * du[1] / tu[1]
    affiche = {"m s": "m/s", "km h": "km/h", "kmh": "km/h"}.get(dst, dst)   # normalise() a mangé le « / »
    src_lib = ("conversion de données (préfixes SI décimaux : 1 Go = 1000 Mo ; les préfixes binaires Gio/Mio "
               "valent 1024)") if du[0] == "D" else "conversion d'unités (facteurs exacts, même dimension)"
    return (VERIFIE, f"{_fmt_nombre(val)} {affiche}", src_lib)


# ————————————————————————————————— ARITHMÉTIQUE (entiers, résultat EXACT uniquement) —————————————————————————————————
# FAUX=0 : on ne répond QUE des résultats EXACTS sur des ENTIERS (+, −, ×, puissance ; division SEULEMENT si elle
# tombe juste ; racine carrée SEULEMENT d'un carré parfait). Tout résultat non exact (division non entière, racine
# non parfaite) -> HORS (jamais un arrondi présenté comme la réponse). Les nombres DÉCIMAUX -> HORS (hors périmètre,
# et évite un appariement partiel « 3.5 fois 2 »). Deux nombres adjacents + opérateur requis -> ne capte pas une
# question factuelle (« 2 plus grand pays » n'a pas 2 nombres). Parse la question BRUTE (garde +,*,/,^).
# Opérande = entier AUTONOME (jamais collé à une lettre/chiffre) : sinon « m3x1qu3 » (mexique leeté) matcherait
# « 3x1 » -> 3×1=3 (FAUX+ démasqué par le harnais d'invariance). Le « x »/«+»/… ne sont des opérateurs qu'entre
# nombres autonomes (« 3 x 4 » OK, « m3x1qu3 » rejeté).
_ARN = r"(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])"
# Les SYMBOLES (x * / ÷ + - ^) exigent des ESPACES autour (\s+…\s+) : sinon « D-1-8042-0175 » (ID) ou « 1/2/2020 »
# (date) seraient pris pour « 1-8042 »/« 1/2 » = soustraction/division (FAUX+ démasqué par le round-trip). Les
# opérateurs-MOTS (fois/plus/moins/divisé par) restent flexibles. « 5 - 3 » / « 7 fois 8 » marchent ; « 1-8042 » non.
_AR_BINAIRES = [
    # NB : la lettre « x » nue (« 4 x 100 », « 256 x 202 cm ») est RETIRÉE des opérateurs de multiplication — c'est un
    # séparateur omniprésent de DIMENSIONS/RELAIS/SCORES dans les vraies entités (relais olympiques « 4 x 100 m »,
    # tableaux « 256 x 202 cm », albums « 12 x 5 ») -> hijack FAUX (#82, 29 cas trouvés par chasseur). On garde les
    # opérateurs NON AMBIGUS : « fois », « multiplié par », « * », « × ». L'utilisateur voulant multiplier les écrit.
    (re.compile(rf"{_ARN}(?:\s*fois\s*|\s*multipli\w+\s+par\s*|\s+[*×]\s+){_ARN}"), "mul"),
    (re.compile(rf"{_ARN}(?:\s*puissance\s*|\s*exposant\s*|\s+(?:\^|\*\*)\s+){_ARN}"), "pow"),
    (re.compile(rf"{_ARN}(?:\s*divis\w+\s+par\s*|\s*sur\s*|\s+[/÷]\s+){_ARN}"), "div"),
    (re.compile(rf"{_ARN}(?:\s*plus\s*|\s+\+\s+){_ARN}"), "add"),
    (re.compile(rf"{_ARN}(?:\s*moins\s*|\s+-\s+){_ARN}"), "sub"),
]
_AR_RACINE = re.compile(rf"racine\s+(?:carr\w+\s+)?d['e]\s*{_ARN}")


def resout_arithmetique(question: str):
    """Calcul EXACT sur des entiers (+,−,×,puissance,division-juste,racine-de-carré-parfait). (VERIFIE, texte, source)
    ou (HORS, None, None). FAUX=0 : résultat non exact ou nombre décimal -> HORS (jamais d'arrondi)."""
    q = question.lower()
    if re.search(r"\d[.,]\d", q):                    # nombre décimal présent -> hors périmètre (et anti faux-match)
        return (HORS, None, None)
    m = _AR_RACINE.search(q)
    if m:
        # COUVERTURE TOTALE : l'opérande doit être le SEUL contenu numérique de la question — « racine de 16
        # plus 9 » évaluerait un FRAGMENT et servirait un résultat faux (passe adverse assistant_nl 2026-07-03).
        if re.findall(r"\d+", q) != [m.group(1)]:
            return (HORS, None, None)
        n = int(m.group(1)); r = math.isqrt(n)
        return (VERIFIE, str(r), "calcul — racine carrée exacte") if r * r == n else (HORS, None, None)
    for patron, op in _AR_BINAIRES:
        m = patron.search(q)
        if not m:
            continue
        # COUVERTURE TOTALE : les DEUX opérandes matchés doivent être TOUT le contenu numérique de la question.
        # « 2 + 2 fois 3 » matchait « 2 + 2 » -> « 4 » servi comme fait (vrai : 8) = FAUX+ réel corrigé.
        if re.findall(r"\d+", q) != [m.group(1), m.group(2)]:
            return (HORS, None, None)
        a, b = int(m.group(1)), int(m.group(2))
        if op == "mul":
            return (VERIFIE, str(a * b), "calcul arithmétique exact")
        if op == "add":
            return (VERIFIE, str(a + b), "calcul arithmétique exact")
        if op == "sub":
            return (VERIFIE, str(a - b), "calcul arithmétique exact")
        if op == "div":
            return (VERIFIE, str(a // b), "calcul arithmétique exact") if b and a % b == 0 else (HORS, None, None)
        if op == "pow":
            return (VERIFIE, str(a ** b), "calcul arithmétique exact") if b <= 64 and a <= 10 ** 6 else (HORS, None, None)
    return (HORS, None, None)


def _deux_entiers(question: str):
    """Les entiers positifs d'une question (« pgcd de 12 et 18 » -> [12, 18]). Descriptif, jamais une réponse."""
    return [int(x) for x in re.findall(r"\d+", question)]


# Nombre -> LETTRES françaises (orthographe TRADITIONNELLE : traits d'union sous 100 seulement ; « et un » à
# 21/31/41/51/61/71 ; « quatre-vingts »/« cents » avec s quand rien ne suit ; « mille » invariable). Convention
# orthographique fermée — ancres vérifiées à la main dans le banc (0, 21, 71, 80, 81, 91, 200, 201, 1984…).
_UNITES_FR_L = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
                "onze", "douze", "treize", "quatorze", "quinze", "seize"]
_DIZAINES_FR_L = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}


def _moins_de_cent(n: int) -> str:
    if n <= 16:
        return _UNITES_FR_L[n]
    if n < 20:
        return "dix-" + _UNITES_FR_L[n - 10]
    if n < 70:
        d, u = divmod(n, 10)
        if u == 0:
            return _DIZAINES_FR_L[d * 10]
        if u == 1:
            return _DIZAINES_FR_L[d * 10] + " et un"
        return _DIZAINES_FR_L[d * 10] + "-" + _UNITES_FR_L[u]
    if n < 80:                                        # 70-79 : soixante-dix… (71 = soixante et onze)
        return "soixante et onze" if n == 71 else "soixante-" + _moins_de_cent(n - 60)
    if n == 80:
        return "quatre-vingts"
    return "quatre-vingt-" + _moins_de_cent(n - 80)   # 81-99 (jamais « et » : quatre-vingt-un)


def _nombre_en_lettres(n: int) -> str:
    """0..999999 en toutes lettres (orthographe traditionnelle)."""
    if n < 100:
        return _moins_de_cent(n)
    if n < 1000:
        c, r = divmod(n, 100)
        tete = "cent" if c == 1 else _UNITES_FR_L[c] + " cent"
        if r == 0:
            return tete + ("s" if c > 1 else "")      # deux cents, mais deux cent un
        return tete + " " + _moins_de_cent(r)
    m, r = divmod(n, 1000)
    tete = "mille" if m == 1 else _nombre_en_lettres(m) + " mille"    # mille INVARIABLE
    if m > 1 and tete.endswith("quatre-vingts mille"):
        tete = tete.replace("quatre-vingts mille", "quatre-vingt mille")   # vingts perd son s devant mille
    if m > 1 and tete.endswith("cents mille"):
        tete = tete.replace("cents mille", "cent mille")
    return tete if r == 0 else tete + " " + _nombre_en_lettres(r)


# Numération romaine : PAIRES canoniques de la notation soustractive, construites sur les symboles VÉRIFIÉS du
# lecteur (chiffre_romain, CAT_CONVENTION). Round-trip complet 1..3999 épinglé au banc.
_ROMAIN_PAIRES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                  (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _en_romain(n: int) -> str:
    out = []
    for v, s in _ROMAIN_PAIRES:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def _depuis_romain(s: str):
    """Valeur d'un nombre romain CANONIQUE, sinon None (« IIII », « VX », ou un mot qui n'en est pas un —
    « CIVIL » a tous ses caractères dans l'alphabet romain). Validation par ROUND-TRIP : on reconvertit la
    valeur lue et on exige l'égalité stricte -> seule l'écriture canonique est acceptée (FAUX=0)."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, prec = 0, 0
    for c in reversed(s):
        v = vals.get(c)
        if v is None:
            return None
        total += v if v >= prec else -v
        prec = max(prec, v)
    return total if 1 <= total <= 3999 and _en_romain(total) == s else None


def _resout_geometrie(q: str):
    """GÉOMÉTRIE simple en NL sur la question NORMALISÉE — « aire d'un cercle de rayon 3 », « périmètre d'un
    carré de côté 4 », « aire d'un rectangle de 3 par 5 », « aire d'un triangle de base 6 et hauteur 4 »,
    « hypoténuse d'un triangle rectangle de côtés 3 et 4 », « volume d'un cube de côté 2 / d'une sphère de rayon 2 ».
    Briques : geometrie2d.Cercle/Polygone/Point, geometrie3d.cube ; la sphère est la seule formule directe
    (4/3·π·r³, mathématique sûre — pas de brique sphère). GARDE anti-faux-positif : exige le mot de MESURE
    (aire/périmètre/circonférence/volume/hypoténuse) + le mot de FIGURE + sa DIMENSION chiffrée — « aire
    urbaine », « périmètre de sécurité », « volume sonore » ne déclenchent rien. Renvoie un triplet ou None."""
    if not re.search(r"\b(aire|surface|perimetre|circonference|volume|hypotenuse)\b", q):
        return None
    try:
        from geometrie2d import Cercle, Polygone, Point
    except Exception:
        return None

    def dim(mot):
        m = re.search(mot + r"s?\s+(?:de\s+|d['’]\s*|:\s*)?(-?\d+(?:[.,]\d+)?)", q)
        return float(m.group(1).replace(",", ".")) if m else None

    aire = re.search(r"\b(aire|surface)\b", q) is not None
    perim = re.search(r"\b(perimetre|circonference)\b", q) is not None

    # CERCLE / DISQUE (rayon ou diamètre)
    if re.search(r"\b(cercle|disque)\b", q) and (aire or perim):
        r = dim("rayon")
        if r is None:
            d = dim("diametre")
            r = d / 2.0 if d is not None else None
        if r is not None and r >= 0:
            c = Cercle(Point(0.0, 0.0), r)
            if aire:
                return (VERIFIE, _fmt_nombre(round(c.aire(), 4)), "géométrie — aire du disque (π·r²)")
            return (VERIFIE, _fmt_nombre(round(c.perimetre(), 4)), "géométrie — circonférence (2·π·r)")

    # CARRÉ (côté)
    if "carre" in q and (aire or perim):
        c = dim("cote")
        if c is not None and c >= 0:
            p = Polygone([(0.0, 0.0), (c, 0.0), (c, c), (0.0, c)])
            if aire:
                return (VERIFIE, _fmt_nombre(p.aire()), "géométrie — aire du carré")
            return (VERIFIE, _fmt_nombre(p.perimetre()), "géométrie — périmètre du carré")

    # RECTANGLE (« longueur 5 et largeur 3 » ou « de 3 par 5 »)
    if "rectangle" in q and (aire or perim):
        L, l = dim("longueur"), dim("largeur")
        if L is None or l is None:
            m2 = re.search(r"(-?\d+(?:[.,]\d+)?)\s*(?:par|x|×|sur)\s*(-?\d+(?:[.,]\d+)?)", q)
            if m2:
                L, l = float(m2.group(1).replace(",", ".")), float(m2.group(2).replace(",", "."))
        if L is not None and l is not None and L >= 0 and l >= 0:
            p = Polygone([(0.0, 0.0), (L, 0.0), (L, l), (0.0, l)])
            if aire:
                return (VERIFIE, _fmt_nombre(p.aire()), "géométrie — aire du rectangle")
            return (VERIFIE, _fmt_nombre(p.perimetre()), "géométrie — périmètre du rectangle")

    # TRIANGLE : aire par base × hauteur (l'aire ne dépend pas de la position de l'apex — triangle rectangle posé)
    if "triangle" in q and aire:
        b, h = dim("base"), dim("hauteur")
        if b is not None and h is not None and b >= 0 and h >= 0:
            p = Polygone([(0.0, 0.0), (b, 0.0), (0.0, h)])
            return (VERIFIE, _fmt_nombre(p.aire()), "géométrie — aire du triangle (base×hauteur/2)")

    # TRIANGLE : périmètre par les 3 côtés — SEULEMENT si l'inégalité triangulaire tient (côtés 1, 1, 5 :
    # ce triangle n'existe pas -> abstention, pas une somme aveugle).
    if "triangle" in q and perim and "cote" in q:
        nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", q)]
        if len(nums) == 3 and all(n > 0 for n in nums):
            a, b, c = sorted(nums)
            if a + b > c:
                return (VERIFIE, _fmt_nombre(a + b + c), "géométrie — périmètre du triangle (somme des côtés)")
            return None                               # triangle impossible -> abstention honnête

    # LOSANGE : aire par les diagonales (sommets sur les axes -> brique Polygone, d1·d2/2)
    if "losange" in q and aire:
        md = re.search(r"diagonales?\s+(?:de\s+)?(\d+(?:[.,]\d+)?)\s+et\s+(?:de\s+)?(\d+(?:[.,]\d+)?)", q)
        if md:
            d1, d2 = float(md.group(1).replace(",", ".")), float(md.group(2).replace(",", "."))
            if d1 > 0 and d2 > 0:
                p = Polygone([(d1 / 2, 0.0), (0.0, d2 / 2), (-d1 / 2, 0.0), (0.0, -d2 / 2)])
                return (VERIFIE, _fmt_nombre(p.aire()), "géométrie — aire du losange (d₁·d₂/2)")

    # HYPOTÉNUSE d'un triangle rectangle (les deux côtés = les deux derniers nombres de la phrase)
    if "hypotenuse" in q:
        nums = [float(x.replace(",", ".")) for x in re.findall(r"-?\d+(?:[.,]\d+)?", q)]
        if len(nums) >= 2 and nums[-2] > 0 and nums[-1] > 0:
            d = Point(0.0, 0.0).distance(Point(nums[-2], nums[-1]))
            return (VERIFIE, _fmt_nombre(round(d, 4)), "géométrie — hypoténuse (Pythagore)")

    # VOLUMES : cube (brique geometrie3d.cube) et sphère (formule mathématique directe)
    if "volume" in q:
        if "cube" in q:
            c = dim("cote")
            if c is None:
                c = dim("arete")
            if c is not None and c >= 0:
                try:
                    from geometrie3d import cube as _cube
                    return (VERIFIE, _fmt_nombre(round(_cube(c).volume(), 4)), "géométrie — volume du cube")
                except Exception:
                    return None
        if "sphere" in q or "boule" in q:
            r = dim("rayon")
            if r is None:
                d = dim("diametre")
                r = d / 2.0 if d is not None else None
            if r is not None and r >= 0:
                import math as _math
                return (VERIFIE, _fmt_nombre(round(4.0 / 3.0 * _math.pi * r ** 3, 4)),
                        "géométrie — volume de la sphère (4/3·π·r³)")
    return None


def resout_math(question: str):
    """MATHS DISCRÈTES / ARITHMÉTIQUE / TRIGO en NL — capacités RÉELLES (arithmetique_modulaire, maths_discretes,
    trigonometrie) rendues atteignables par une phrase (mandat « tout câbler », 2026-07-08). Renvoie
    (VERIFIE, texte, source) ou (HORS, None, None). FAUX=0 : chaque route exige un mot-clé FORT + des opérandes
    valides ; le calcul vient d'un module vérifié ; hors périmètre -> HORS (le pipeline continue)."""
    q = normalise(question)
    qtoks = set(q.split())
    ent = _deux_entiers(question)
    try:
        import arithmetique_modulaire as _AM
        import maths_discretes as _MD
        import trigonometrie as _TG
    except Exception:
        return (HORS, None, None)

    # INTÉRÊTS (placement) : « combien rapportent 1000 euros à 5% pendant 3 ans » -> valeur acquise + gain.
    # Exige les TROIS composants (capital + taux + durée) pour ne pas confondre avec un simple pourcentage.
    mi = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)\s*(?:euros?|€|dollars?|\$)\b.*?(\d+(?:[.,]\d+)?)\s*(?:%|pour ?cent)"
                   r".*?(\d+(?:[.,]\d+)?)\s*(?:ans?|ann[ée]es?)", question, re.I)
    if mi:
        C = float(mi.group(1).replace(" ", "").replace(",", "."))
        t = float(mi.group(2).replace(",", ".")) / 100.0
        n = float(mi.group(3).replace(",", "."))
        try:
            import maths_financieres as _MF
            simple = "simple" in q or "lineaire" in q
            va = _MF.valeur_acquise_simple(C, t, n) if simple else _MF.interet_compose(C, t, n)
            gain = round(va - C, 2)
            mode = "intérêts simples" if simple else "intérêts composés"
            return (VERIFIE, "%s d'intérêts (%s) ; valeur acquise : %s" % (_fmt_nombre(gain), mode, _fmt_nombre(va)),
                    "mathématiques financières — %s" % mode)
        except Exception:
            return (HORS, None, None)

    # POURCENTAGES APPLIQUÉS (arithmétique exacte). ⚠ sur la question BRUTE : normalise() efface le « % ».
    # La réponse MONTRE le calcul (« 64 (80 − 20 % = 80 − 16) ») : lève l'ambiguïté remise/prix final.
    _PCT = r"(\d+(?:[.,]\d+)?)"
    _f = lambda g: float(g.replace(",", "."))
    mred = (re.search(rf"{_PCT}\s*(?:%|pour ?cents?)\s+de\s+(?:r[ée]duction|remise|rabais)\s+sur\s+{_PCT}",
                      question, re.I)
            or re.search(rf"(?:r[ée]duction|remise|rabais)\s+de\s+{_PCT}\s*(?:%|pour ?cents?)\s+sur\s+{_PCT}",
                         question, re.I))
    if mred:
        p, base = _f(mred.group(1)), _f(mred.group(2))
        return (VERIFIE, "%s (%s − %s %% = %s − %s)" % (_fmt_nombre(base * (1 - p / 100.0)), _fmt_nombre(base),
                                                        _fmt_nombre(p), _fmt_nombre(base), _fmt_nombre(base * p / 100.0)),
                "calcul — prix après réduction")
    maug = (re.search(rf"augmente[rz]?\s+{_PCT}\s+de\s+{_PCT}\s*(?:%|pour ?cents?)", question, re.I)
            or re.search(rf"{_PCT}\s+augment[ée]e?s?\s+de\s+{_PCT}\s*(?:%|pour ?cents?)", question, re.I))
    maug_inv = None if maug else re.search(
        rf"(?:hausse|augmentation)\s+de\s+{_PCT}\s*(?:%|pour ?cents?)\s+sur\s+{_PCT}", question, re.I)
    if maug or maug_inv:
        base, p = (_f(maug.group(1)), _f(maug.group(2))) if maug else (_f(maug_inv.group(2)), _f(maug_inv.group(1)))
        return (VERIFIE, "%s (%s + %s %% = %s + %s)" % (_fmt_nombre(base * (1 + p / 100.0)), _fmt_nombre(base),
                                                        _fmt_nombre(p), _fmt_nombre(base), _fmt_nombre(base * p / 100.0)),
                "calcul — valeur après augmentation")
    mpart = re.search(rf"{_PCT}\s+(?:est|repr[ée]sente|fait)\s+quel\s+pourcentage\s+de\s+{_PCT}", question, re.I)
    mpart_inv = None if mpart else re.search(
        rf"quel\s+pourcentage\s+de\s+{_PCT}\s+(?:repr[ée]sente|fait)\s+{_PCT}", question, re.I)
    if mpart or mpart_inv:
        part, tout = (_f(mpart.group(1)), _f(mpart.group(2))) if mpart else (_f(mpart_inv.group(2)), _f(mpart_inv.group(1)))
        if tout == 0:
            return (HORS, None, None)
        return (VERIFIE, _fmt_nombre(part / tout * 100.0) + " %",
                "calcul — part en pourcentage (%s sur %s)" % (_fmt_nombre(part), _fmt_nombre(tout)))

    # CHIFFRES ROMAINS (convention de numération, symboles = table lecteur._CHIFFRE_ROMAIN ; notation
    # soustractive canonique). EXACT dans les deux sens, round-trippé au banc sur 1..3999 ; hors plage ou
    # forme NON canonique (« IIII ») -> abstention.
    # NOMBRE EN TOUTES LETTRES : « écris 1984 en lettres » (convention orthographique traditionnelle, dite).
    mnl = re.search(r"(\d+)\s+en\s+(?:toutes\s+)?lettres", q)
    if mnl:
        n = int(mnl.group(1))
        if 0 <= n <= 999999:
            return (VERIFIE, "%s (orthographe traditionnelle)" % _nombre_en_lettres(n),
                    "numération française — nombre en toutes lettres")
        return (HORS, None, None)

    mrom = re.search(r"(\d+)\s+en\s+(?:chiffres?\s+)?romains?", q)
    if mrom:
        n = int(mrom.group(1))
        if 1 <= n <= 3999:
            return (VERIFIE, _en_romain(n), "numération romaine (convention, symboles du lecteur)")
        return (HORS, None, None)
    mrom2 = re.search(r"\b([ivxlcdm]+)\b\s+en\s+(?:chiffres?\s+)?(?:arabes?|d[ée]cimal)", q)
    if mrom2:
        n = _depuis_romain(mrom2.group(1).upper())
        if n is not None:
            return (VERIFIE, str(n), "numération romaine (convention, symboles du lecteur)")
        return (HORS, None, None)

    # POURCENTAGE : « 20% de 150 », « 20 pour cent de 150 » -> 30 (arithmétique exacte, sans module tiers).
    mp = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:%|pour ?cent(?:s)?|pourcent)\s+(?:de|du|des|d['’]|sur)\s+(\d+(?:[.,]\d+)?)",
                   question, re.I)
    if mp:
        p = float(mp.group(1).replace(",", ".")); base = float(mp.group(2).replace(",", "."))
        v = p / 100.0 * base
        return (VERIFIE, _fmt_nombre(v), "calcul — pourcentage")

    # VALEUR ABSOLUE : « valeur absolue de -5 » -> 5 (natif, exact).
    mabs = re.search(r"valeur\s+absolue\s+(?:de\s+|d['’])?(-?\d+(?:[.,]\d+)?)", question, re.I)
    if mabs:
        return (VERIFIE, _fmt_nombre(abs(float(mabs.group(1).replace(",", ".")))), "valeur absolue")

    # RACINE CUBIQUE : « racine cubique de 27 » -> 3 — cube PARFAIT seulement, sinon abstention (cohérent avec
    # la racine carrée exacte de resout_arithmetique : JAMAIS un arrondi servi comme exact).
    mrc = re.search(r"racine\s+cubique\s+(?:de\s+|d['’])?(-?\d+)\b", question, re.I)
    if mrc:
        n = int(mrc.group(1))
        r0 = round(abs(n) ** (1.0 / 3.0)) if n else 0
        r = next((k for k in (r0 - 1, r0, r0 + 1) if k >= 0 and k ** 3 == abs(n)), None)
        if r is None:
            return (HORS, None, None)
        return (VERIFIE, str(-r if n < 0 else r), "calcul — racine cubique exacte")

    # LOGARITHME en base EXPLICITE : « log de 100 en base 10 » -> 2 — exposant ENTIER exact seulement (base
    # non dite ou résultat non entier -> abstention : on ne devine pas ln/log10, on n'arrondit pas).
    mlg = re.search(r"log(?:arithme)?\s+(?:de\s+|d['’])?(\d+)\s+en\s+base\s+(\d+)", question, re.I)
    if mlg:
        n, b = int(mlg.group(1)), int(mlg.group(2))
        if n >= 1 and b >= 2:
            k, p = 0, 1
            while p < n:
                p *= b
                k += 1
            if p == n:
                return (VERIFIE, str(k), "calcul — logarithme exact (base %d)" % b)
        return (HORS, None, None)

    # ARRONDI / PARTIE ENTIÈRE / PLANCHER / PLAFOND : opérations EXACTES par définition sur le nombre donné.
    # Arrondi = demi-supérieur (convention française : 2,5 -> 3, jamais l'arrondi bancaire de round()).
    # Partie entière = définition MATHÉMATIQUE (plancher) : E(-2,3) = -3, étiquetée pour lever l'ambiguïté.
    mar = re.search(r"\b(arrondi[st]?|partie\s+entiere|plancher|plafond)\b", q)
    if mar:
        mnum = re.search(r"(-?\d+[.,]\d+)", question)    # exige un DÉCIMAL (« plafond de 3 mètres » ne matche pas)
        if mnum:
            from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
            x = Decimal(mnum.group(1).replace(",", "."))
            op = mar.group(1)
            if op.startswith("arrondi"):
                mdec = re.search(r"a\s+(\d+)\s+decimales?", q)
                if "superieur" in q:
                    return (VERIFIE, str(x.to_integral_value(rounding=ROUND_CEILING)), "calcul — arrondi supérieur")
                if "inferieur" in q:
                    return (VERIFIE, str(x.to_integral_value(rounding=ROUND_FLOOR)), "calcul — arrondi inférieur")
                if mdec:
                    quantum = Decimal(1).scaleb(-int(mdec.group(1)))
                    return (VERIFIE, str(x.quantize(quantum, rounding=ROUND_HALF_UP)),
                            "calcul — arrondi à %s décimale(s)" % mdec.group(1))
                return (VERIFIE, str(x.to_integral_value(rounding=ROUND_HALF_UP)), "calcul — arrondi (demi-supérieur)")
            if op == "plafond":
                return (VERIFIE, str(x.to_integral_value(rounding=ROUND_CEILING)), "calcul — plafond (entier supérieur)")
            return (VERIFIE, str(x.to_integral_value(rounding=ROUND_FLOOR)),
                    "calcul — partie entière (plancher : E(-2,3) = -3)")

    # CONVERSION DE BASE (binaire/octal/hexadécimal <-> décimal ; conversion MÉCANIQUE exacte, natif Python).
    # « convertis 42 en binaire », « 42 en hexadécimal », « 1010 binaire en décimal », « 2A hexadécimal en décimal ».
    _BASES = {"binaire": 2, "binaires": 2, "octal": 8, "octale": 8, "hexadecimal": 16, "hexadecimale": 16, "hexa": 16}
    m_dec = re.search(r"\b([0-9a-fA-F]+)\s+(binaires?|octale?|hexad[eé]cimale?|hexa)\s+en\s+d[eé]cimal", question, re.I)
    if m_dec:
        base = _BASES.get(normalise(m_dec.group(2)), None)
        try:
            return (VERIFIE, str(int(m_dec.group(1), base)), "conversion base %d -> décimal" % base)
        except (ValueError, TypeError):
            return (HORS, None, None)
    m_base = re.search(r"\b(\d+)\s+en\s+(binaire|octale?|hexad[eé]cimale?|hexa)\b", question, re.I)
    if m_base:
        base = _BASES.get(normalise(m_base.group(2)), None)
        n = int(m_base.group(1))
        out = {2: bin, 8: oct, 16: hex}[base](n)[2:].upper()
        return (VERIFIE, out, "conversion décimal -> base %d" % base)

    # INVERSE MODULAIRE : « inverse de 7 modulo 13 » -> 2 (arithmetique_modulaire, exact ; None si non inversible).
    minv = re.search(r"inverse\s+(?:de\s+|d['’])?(\d+)\s+modulo\s+(\d+)", question, re.I)
    if minv:
        try:
            return (VERIFIE, str(_AM.inverse_modulaire(int(minv.group(1)), int(minv.group(2)))),
                    "arithmétique modulaire — inverse")
        except Exception:
            return (HORS, None, None)                    # non inversible (pgcd≠1) -> abstention honnête

    # PGCD / PPCM : « pgcd de 12 et 18 », « ppcm de 4 et 6 » (2 entiers requis).
    if ("pgcd" in qtoks or "diviseur" in q and "commun" in q) and len(ent) >= 2:
        return (VERIFIE, str(_AM.pgcd(ent[0], ent[1])), "arithmétique — PGCD (Euclide)")
    if ("ppcm" in qtoks or "multiple" in q and "commun" in q) and len(ent) >= 2:
        g = _AM.pgcd(ent[0], ent[1])
        return (VERIFIE, str(ent[0] * ent[1] // g) if g else "0", "arithmétique — PPCM")

    # VÉRIFICATIONS NUMÉRIQUES exactes : pair/impair, divisible par, multiple de, carré parfait.
    # (La garde de resolution.py renvoie ces « est-ce que <nombre> est … » ici — on y répond VRAIMENT.)
    mvn = re.search(r"(\d+)\s+est(?:[- ](?:il|elle|ce))?\s+(?:un\s+nombre\s+)?(pair|impair)e?\b", q) \
        or (re.search(r"est[- ]ce\s+que\s+(\d+)\s+est\s+(?:un\s+nombre\s+)?(pair|impair)e?\b", q))
    if mvn:
        n, quoi = int(mvn.group(1)), mvn.group(2)
        est = (n % 2 == 0) if quoi == "pair" else (n % 2 == 1)
        return (VERIFIE, ("Oui, %d est %s." if est else "Non, %d n'est pas %s.") % (n, quoi),
                "arithmétique — parité")
    mdiv = re.search(r"(\d+)\s+(?:est(?:[- ](?:il|elle|ce))?\s+)?divisible\s+par\s+(\d+)", q)
    if mdiv:
        a, b = int(mdiv.group(1)), int(mdiv.group(2))
        if b == 0:
            return (VERIFIE, "La divisibilité par 0 n'est pas définie.", "arithmétique — divisibilité")
        est = a % b == 0
        return (VERIFIE, ("Oui, %d est divisible par %d (%d × %d)." % (a, b, b, a // b)) if est
                else "Non, %d n'est pas divisible par %d (reste %d)." % (a, b, a % b),
                "arithmétique — divisibilité")
    mmu = re.search(r"(\d+)\s+est(?:[- ](?:il|elle|ce))?\s+un\s+multiple\s+de\s+(\d+)", q)
    if mmu:
        a, b = int(mmu.group(1)), int(mmu.group(2))
        est = b != 0 and a % b == 0
        return (VERIFIE, ("Oui, %d est un multiple de %d (%d × %d)." % (a, b, b, a // b)) if est
                else "Non, %d n'est pas un multiple de %d." % (a, b), "arithmétique — multiples")
    mcp = re.search(r"(\d+)\s+est(?:[- ](?:il|elle|ce))?\s+un\s+carr[ée]\s+parfait", q)
    if mcp:
        n = int(mcp.group(1))
        r0 = math.isqrt(n)
        return (VERIFIE, ("Oui, %d est un carré parfait (%d²)." % (n, r0)) if r0 * r0 == n
                else "Non, %d n'est pas un carré parfait (%d² = %d, %d² = %d)."
                % (n, r0, r0 * r0, r0 + 1, (r0 + 1) ** 2), "arithmétique — carrés parfaits")

    # COMPARAISON DE FRACTIONS / ÉGALITÉ décimal-fraction : EXACTE via Fraction (jamais de flottant menteur).
    # ⚠ sur la question BRUTE : normalise() mange le « / » (« 2/3 » -> « 2 3 »).
    mfr = re.search(r"plus\s+grand\w*\s*:?\s*(\d+)\s*/\s*(\d+)\s+ou\s+(\d+)\s*/\s*(\d+)", question, re.I) \
        or re.search(r"(\d+)\s*/\s*(\d+)\s+ou\s+(\d+)\s*/\s*(\d+).*plus\s+grand", question, re.I)
    if mfr:
        from fractions import Fraction
        a = Fraction(int(mfr.group(1)), int(mfr.group(2)))
        b = Fraction(int(mfr.group(3)), int(mfr.group(4)))
        sa, sb = "%s/%s" % (mfr.group(1), mfr.group(2)), "%s/%s" % (mfr.group(3), mfr.group(4))
        if a == b:
            return (VERIFIE, "Ils sont égaux (%s = %s)." % (sa, sb), "arithmétique — fractions exactes")
        return (VERIFIE, "%s est plus grand (%s %s %s)." % (sa if a > b else sb, sa, ">" if a > b else "<", sb),
                "arithmétique — fractions exactes")
    meg = re.search(r"(\d+(?:[.,]\d+)?)\s+est(?:[- ](?:il|elle|ce))?\s+[ée]gale?\s+[àa]\s+(\d+)\s*/\s*(\d+)", question, re.I)
    if meg:
        from fractions import Fraction
        a = Fraction(meg.group(1).replace(",", "."))
        b = Fraction(int(meg.group(2)), int(meg.group(3)))
        return (VERIFIE, ("Oui, %s = %s/%s." % (meg.group(1), meg.group(2), meg.group(3))) if a == b
                else "Non, %s ≠ %s/%s." % (meg.group(1), meg.group(2), meg.group(3)),
                "arithmétique — fractions exactes")

    # PRODUIT / DIFFÉRENCE / QUOTIENT nommés : « le produit de 4 et 25 » -> 100 (exact ; quotient exact seul).
    mpr = re.search(r"\b(produit|difference|quotient)\s+(?:de\s+|d['’]\s*|entre\s+)(-?\d+)\s+et\s+(?:de\s+)?(-?\d+)", q)
    if mpr:
        op, a, b = mpr.group(1), int(mpr.group(2)), int(mpr.group(3))
        if op == "produit":
            return (VERIFIE, str(a * b), "arithmétique — produit")
        if op == "difference":
            return (VERIFIE, str(a - b), "arithmétique — différence")
        if b != 0 and a % b == 0:
            return (VERIFIE, str(a // b), "arithmétique — quotient exact")
        return (HORS, None, None)                        # quotient non entier -> abstention (cohérent division)

    # DIVISEURS d'un entier : énumération exacte (borne anti-DoS).
    mdv = re.search(r"(?:les\s+)?diviseurs\s+(?:de\s+|d['’]\s*)(\d+)", q)
    if mdv:
        n = int(mdv.group(1))
        if 1 <= n <= 10 ** 7:
            divs = [d for d in range(1, math.isqrt(n) + 1) if n % d == 0]
            tous = sorted(set(divs + [n // d for d in divs]))
            return (VERIFIE, "%d a %d diviseurs : %s." % (n, len(tous), ", ".join(map(str, tous))),
                    "arithmétique — diviseurs (énumération exacte)")
        return (HORS, None, None)

    # NOMBRE(S) PREMIER(S) DANS UN INTERVALLE : « un nombre premier entre 20 et 30 » -> 23, 29 (énumération
    # exacte, AVANT la primalité simple — sinon « Non, 20 n'est pas premier » répondait à côté, FAUX vécu).
    mpe = re.search(r"(?:nombres?\s+premiers?|premiers?)\s+entre\s+(\d+)\s+et\s+(\d+)", q)
    if mpe:
        a, b = int(mpe.group(1)), int(mpe.group(2))
        if a > b:
            a, b = b, a
        if b - a <= 10000 and b <= 10 ** 9:
            prems = [x for x in range(max(a, 2), b + 1) if _AM.est_premier(x)]
            if not prems:
                return (VERIFIE, "Aucun nombre premier entre %d et %d." % (a, b), "arithmétique — primalité")
            return (VERIFIE, "Entre %d et %d : %s." % (a, b, ", ".join(map(str, prems))),
                    "arithmétique — primalité (énumération exacte)")
        return (HORS, None, None)

    # NOMBRE PREMIER : « est-ce que 17 est (un nombre) premier ? », « 18 est-il un nombre premier ? ». GARDE
    # anti-faux-positif : « premier » est un ordinal courant (« premier président de 1958 ») -> on exige soit
    # « nombre premier », soit la forme « <n> est … premier » (le nombre ADJACENT au prédicat de primalité).
    if ent and (re.search(r"nombres?\s+premiers?", q)
                or re.search(r"\b\d+\b\s+(?:est(?:[- ]il|[- ]elle)?|es[- ]tu)?\s*(?:un\s+nombre\s+)?premier", q)
                or re.search(r"premier\s*\?*\s*$", q) and re.search(r"\b\d+\b\s+est", q)):
        prem = _AM.est_premier(ent[0])
        return (VERIFIE, ("Oui, %d est premier." if prem else "Non, %d n'est pas premier.") % ent[0],
                "arithmétique — primalité")

    # FACTORIELLE : « factorielle de 5 », « 5! »
    mf = re.search(r"(\d+)\s*!", question) or (re.search(r"\b(\d+)\b", question) if "factorielle" in qtoks else None)
    if mf and ("factorielle" in qtoks or "!" in question):
        return (VERIFIE, str(_MD.factorielle(int(mf.group(1)))), "combinatoire — factorielle")

    # COMBINAISONS / ARRANGEMENTS : « combien de façons d'ordonner 5 éléments » (=factorielle), « combinaisons de
    # 2 parmi 5 » (=binomial), « arrangements de 2 parmi 5 » (=binomial × k!).
    if ("ordonner" in qtoks or "permutations" in qtoks or ("facons" in qtoks and "ordonner" in q)) and ent:
        return (VERIFIE, str(_MD.factorielle(ent[0])), "combinatoire — permutations (n!)")
    if ("combinaisons" in qtoks or "combinaison" in qtoks) and "parmi" in qtoks and len(ent) >= 2:
        return (VERIFIE, str(_MD.binomial(ent[1], ent[0])), "combinatoire — combinaisons C(n,k)")
    if ("arrangements" in qtoks or "arrangement" in qtoks) and "parmi" in qtoks and len(ent) >= 2:
        k, n = ent[0], ent[1]
        return (VERIFIE, str(_MD.binomial(n, k) * _MD.factorielle(k)), "combinatoire — arrangements A(n,k)")

    # SUITES : « fibonacci de 10 », « 10e nombre de Fibonacci »
    if "fibonacci" in qtoks and ent:
        return (VERIFIE, str(_MD.fibonacci(ent[0])), "suite de Fibonacci")

    # NOMBRES COMPLEXES : « module de 3+4i », « conjugué de 2-3i », « argument de i » (module `nombres_complexes`,
    # format tuple (ré, im)). Exige un mot-clé + un « i »/« j » d'unité imaginaire. FAUX=0 : calcul vérifié.
    if ("complexe" in qtoks or "module" in qtoks or "conjugue" in qtoks or "argument" in qtoks) \
            and re.search(r"\d\s*[ij]\b|[+-]\s*[ij]\b|\b[ij]\b", question):
        s = question.replace(" ", "").replace(",", ".").lower()
        mi = re.search(r"([+-]?\d*(?:\.\d+)?)[ij]\b", s)      # terme imaginaire (coef vide -> 1, « - » -> -1)
        z = None
        if mi:
            coef = mi.group(1)
            im_part = 1.0 if coef in ("", "+") else -1.0 if coef == "-" else float(coef)
            mr = re.search(r"(-?\d+(?:\.\d+)?)$", s[:mi.start()])   # partie réelle = nombre juste avant le terme en i
            re_part = float(mr.group(1)) if mr else 0.0
            z = (re_part, im_part)
        if z is not None:
            try:
                import nombres_complexes as _NC
                if "module" in qtoks:
                    return (VERIFIE, _fmt_nombre(_NC.module(z)), "nombres complexes — module")
                if "argument" in qtoks:
                    return (VERIFIE, _fmt_nombre(_NC.argument(z)) + " rad", "nombres complexes — argument")
                if "conjugue" in qtoks:
                    c = _NC.conjugue(z)
                    im = c[1]
                    return (VERIFIE, "%s %s %si" % (_fmt_nombre(c[0]), "+" if im >= 0 else "-", _fmt_nombre(abs(im))),
                            "nombres complexes — conjugué")
            except Exception:
                return (HORS, None, None)

    # ANNÉE BISSEXTILE (règle grégorienne EXACTE — convention). FAUX=0 vécu : « est-ce que 2024 est une année
    # bissextile » servait « 2010 » (l'année du FILM « Année bissextile », lookup d'œuvre détourné).
    mbi = re.search(r"(\d{1,6})\s+est(?:[- ](?:elle|il|ce))?\s+(?:une\s+)?(?:annee\s+)?bissextile"
                    r"|annee\s+(\d{1,6})\s+est(?:[- ](?:elle|il))?\s+bissextile", q)
    if mbi or ("bissextile" in q and re.search(r"est[- ]ce\s+que\s+(\d{1,6})", q)):
        g = mbi.group(1) or mbi.group(2) if mbi else re.search(r"est[- ]ce\s+que\s+(\d{1,6})", q).group(1)
        n = int(g)
        biss = n % 4 == 0 and (n % 100 != 0 or n % 400 == 0)
        return (VERIFIE, ("Oui, %d est bissextile" if biss else "Non, %d n'est pas bissextile") % n
                + " (règle grégorienne : divisible par 4, sauf les siècles non divisibles par 400).",
                "calendrier grégorien — règle bissextile")
    mjan = re.search(r"(?:nombre|combien)\s+de\s+jours\s+(?:en|dans\s+l['’]?annee)\s+(\d{3,4})\b", q)
    if mjan:
        n = int(mjan.group(1))
        biss = n % 4 == 0 and (n % 100 != 0 or n % 400 == 0)
        return (VERIFIE, "%d jours (%d est %s)" % (366 if biss else 365, n,
                                                   "bissextile" if biss else "non bissextile"),
                "calendrier grégorien — règle bissextile")

    # SOMME DES ANGLES d'un polygone (convention euclidienne exacte : (n−2)·180°) et DEGRÉS d'un cercle.
    mang = re.search(r"somme\s+des\s+angles\s+(?:int[ée]rieurs\s+)?d['’]?\s*(?:un\s+|une\s+)?"
                     r"(triangle|quadrilatere|pentagone|hexagone|heptagone|octogone|nonagone|decagone"
                     r"|hendecagone|dodecagone)", q)
    if mang:
        _NCOTES = {"triangle": 3, "quadrilatere": 4, "pentagone": 5, "hexagone": 6, "heptagone": 7,
                   "octogone": 8, "nonagone": 9, "decagone": 10, "hendecagone": 11, "dodecagone": 12}
        n = _NCOTES[mang.group(1)]
        return (VERIFIE, "%d° ((n − 2) × 180° avec n = %d, géométrie euclidienne)" % ((n - 2) * 180, n),
                "géométrie — somme des angles intérieurs")
    if re.search(r"combien\s+de\s+degr[ée]s\s+dans\s+(?:un\s+)?demi[- ]cercle", q):
        return (VERIFIE, "180° (un demi-tour, convention)", "géométrie — mesure d'angle")
    if re.search(r"combien\s+de\s+degr[ée]s\s+dans\s+(?:un\s+)?(?:cercle|tour)(?:\s+complet)?\b", q):
        return (VERIFIE, "360° (tour complet, convention)", "géométrie — mesure d'angle")

    # RANGS ET SUCCESSIONS des cycles FERMÉS (mois de l'année, jours de la semaine, alphabet) — conventions.
    _MOIS_O = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
               "septembre", "octobre", "novembre", "décembre"]
    _JOURS_O = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mrg = re.search(r"le\s+(\d{1,2})\s*(?:e|eme|ème|er)\s+mois\s+de\s+l['’]?\s*annee", q)
    if mrg:
        n = int(mrg.group(1))
        if 1 <= n <= 12:
            return (VERIFIE, "%s (%de mois de l'année)" % (_MOIS_O[n - 1].capitalize(), n),
                    "calendrier — rang des mois")
        return (VERIFIE, "L'année n'a que 12 mois — il n'y a pas de %de mois." % n, "calendrier — rang des mois")
    mjs = re.search(r"quel\s+jour\s+vient\s+(apres|avant)\s+(?:le\s+)?(lundi|mardi|mercredi|jeudi|vendredi"
                    r"|samedi|dimanche)\b", q)
    if mjs:
        i = _JOURS_O.index(mjs.group(2))
        j = _JOURS_O[(i + (1 if mjs.group(1) == "apres" else -1)) % 7]
        return (VERIFIE, "%s%s" % (j.capitalize(), " (la semaine reboucle)" if (i, mjs.group(1)) in
                                   ((6, "apres"), (0, "avant")) else ""), "calendrier — ordre des jours")
    mls = re.search(r"quelle\s+lettre\s+vient\s+(apres|avant)\s+(?:le\s+|la\s+|l['’]\s*)?([a-z])\b", q)
    if mls:
        c, sens = mls.group(2), mls.group(1)
        if c == "z" and sens == "apres":
            return (VERIFIE, "Aucune — z est la dernière lettre de l'alphabet.", "alphabet latin")
        if c == "a" and sens == "avant":
            return (VERIFIE, "Aucune — a est la première lettre de l'alphabet.", "alphabet latin")
        return (VERIFIE, chr(ord(c) + (1 if sens == "apres" else -1)), "alphabet latin")

    # DIVISIONS DU TEMPS (conventions exactes du calendrier).
    mdt = re.search(r"combien\s+(?:de\s+|d['’]?\s*)(trimestres|semestres|mois|jours)\s+dans\s+(?:une?\s+)?"
                    r"(annee|semaine)\b", q)
    if mdt:
        val = {("trimestres", "annee"): "4", ("semestres", "annee"): "2", ("mois", "annee"): "12",
               ("jours", "semaine"): "7"}.get((mdt.group(1), mdt.group(2)))
        if val:
            return (VERIFIE, val, "calendrier — divisions de l'année")
    mds = re.search(r"combien\s+(?:de\s+|d['’]?\s*)(?:annees|ans)\s+dans\s+(?:un\s+|une\s+)?"
                    r"(siecle|millenaire|decennie)\b", q)
    if mds:
        return (VERIFIE, {"siecle": "100", "millenaire": "1000", "decennie": "10"}[mds.group(1)],
                "calendrier — divisions du temps")
    if re.search(r"combien\s+de\s+siecles\s+dans\s+(?:un\s+)?millenaire", q):
        return (VERIFIE, "10", "calendrier — divisions du temps")

    # GÉOMÉTRIE SIMPLE : aire/périmètre/volume de figures nommées (modules geometrie2d/geometrie3d vérifiés).
    geo = _resout_geometrie(q)
    if geo:
        return geo

    # OPÉRATIONS NOMMÉES sur UN nombre : « double de 21 » -> 42, « moitié de 42 » -> 21, « carré de 12 » -> 144,
    # « opposé de 7 » -> -7, « inverse de 4 » -> 0.25 (décimal FINI exigé : « inverse de 3 » -> abstention,
    # jamais 0.333 servi comme exact ; « tiers » pareil). GARDE : jamais quand un mot de MESURE est là
    # (« aire d'un carré de 4 » = géométrie, traitée au-dessus ; « périmètre d'un carré de 5 » ≠ 25).
    if not re.search(r"\b(aire|surface|perimetre|circonference|volume|cote|rayon|modulo)\b", q):
        mop = re.search(r"\b(double|triple|quadruple|moitie|tiers|quart|carre|cube|oppose|inverse)\s+"
                        r"(?:de\s+|du\s+|d['’]\s*)(-?\d+(?:[.,]\d+)?)(?!\s*[a-z])", q)
        if mop:
            op, x = mop.group(1), float(mop.group(2).replace(",", "."))
            from fractions import Fraction
            fx = Fraction(mop.group(2).replace(",", "."))
            simple = {"double": x * 2, "triple": x * 3, "quadruple": x * 4, "moitie": x / 2, "quart": x / 4,
                      "carre": x * x, "cube": x ** 3, "oppose": -x}
            if op in simple:
                return (VERIFIE, _fmt_nombre(simple[op]), "calcul — %s" % op.replace("moitie", "moitié"))
            frac = fx / 3 if op == "tiers" else (Fraction(1) / fx if fx != 0 else None)
            if frac is None:
                return (HORS, None, None)                      # inverse de 0 -> indéfini
            d = frac.denominator
            while d % 2 == 0:
                d //= 2
            while d % 5 == 0:
                d //= 5
            if d != 1:                                         # décimal infini -> abstention (jamais d'arrondi)
                return (HORS, None, None)
            return (VERIFIE, _fmt_nombre(float(frac)), "calcul — %s exact" % ("tiers" if op == "tiers" else "inverse"))

    # TRIGONOMÉTRIE : « sinus de 30 degrés », « cos de 60° », « tangente de 45 »
    mt = re.search(r"\b(sinus|sin|cosinus|cos|tangente|tan)\b.*?(-?\d+(?:[.,]\d+)?)", q)
    if mt:
        ang = float(mt.group(2).replace(",", "."))
        fn, nom = ((_TG.sin_deg, "sinus") if mt.group(1) in ("sinus", "sin")
                   else (_TG.cos_deg, "cosinus") if mt.group(1) in ("cosinus", "cos")
                   else (_TG.tan_deg, "tangente"))
        return (VERIFIE, _fmt_nombre(fn(ang)), "trigonométrie — %s (degrés)" % nom)

    return (HORS, None, None)


def resout_fonction(question: str):
    """Route vers un sous-système FONCTION (calcul borné). Renvoie (VERIFIE, texte, source) ou (HORS, None, None).
    Aucune invention : on relaie le verdict du moteur (déjà VÉRIFIÉ/HORS). Mot-clé exigé, sinon abstention."""
    conv = resout_conversion(question)               # conversion d'unités : motif explicite, sinon HORS -> on continue
    if conv[0] == VERIFIE:
        return conv
    arith = resout_arithmetique(question)            # calcul exact sur entiers ; sinon HORS -> on continue
    if arith[0] == VERIFIE:
        return arith
    mth = resout_math(question)                      # maths discrètes / arithmétique / trigo (câblage 2026-07-08)
    if mth[0] == VERIFIE:
        return mth
    qtoks = set(normalise(question).split())
    arg = _extrait_arg_brut(question)
    dernier = _dernier_token(question)              # repli robuste (« … de la séquence ATCG » -> « ATCG »)
    seq = dernier.upper()                           # séquences ADN/ARN : majuscules (l'ARN/ADN est en capitales)
    if not arg:
        return (HORS, None, None)
    try:
        import references as _R, chimie as _C, genetique as _G
    except Exception:
        return (HORS, None, None)

    # MORSE : encode (« code morse de SOS » -> ... --- ...) OU décode si des tokens de code (. -) sont présents
    # N'IMPORTE OÙ dans la question (« que signifie ... --- ... en morse » -> SOS — le mot-clé est en fin de phrase).
    if "morse" in qtoks:
        codes = [t for t in re.split(r"[\s/]+", question) if t and set(t) <= set(".-")]
        decode = bool(codes) and (any("-" in t for t in codes) or len(codes) >= 2)
        if decode:
            lettres = []
            for code in codes:
                st, val = _R.depuis_morse(code)
                if st != VERIFIE or val is None:
                    return (HORS, None, None)
                lettres.append(str(val))
            return (VERIFIE, "".join(lettres), "code morse international (table sourcée)")
        # GARDE HOMONYME (#83) : « morse » est AUSSI une ENTITÉ (l'animal, Odobenus rosmarus). Si l'ARGUMENT à traduire
        # EST « morse » lui-même (« c'est quoi un morse », « nom scientifique de morse »), ce n'est PAS une demande de
        # code Morse -> abstention (le lookup DATA répondra l'animal). On ne traduit que si l'arg est DISTINCT (« morse
        # de A », « code morse de SOS »). Idem OTAN ci-dessous. Sound : préserve l'intention, tue le hijack d'homonyme.
        if "morse" in normalise(arg).split():
            return (HORS, None, None)
        out = _compose_par_lettre(arg.upper(), _R.vers_morse)
        return (VERIFIE, out, "code morse international (table sourcée)") if out else (HORS, None, None)

    # ALPHABET OTAN / radio / aviation : « alphabet otan de B », « nato de R ».
    if "nato" in qtoks or "otan" in qtoks or ("alphabet" in qtoks and ("radio" in qtoks or "aviation" in qtoks)):
        # GARDE HOMONYME (#83) : « otan » est AUSSI l'ORGANISATION (sigle). Si l'arg EST « otan »/« nato » (« que
        # signifie le sigle otan »), ce n'est PAS une demande d'alphabet radio -> abstention (DATA répond l'organisation).
        if {"otan", "nato"} & set(normalise(arg).split()):
            return (HORS, None, None)
        out = _compose_par_lettre(arg.upper(), _R.nato)
        return (VERIFIE, out, "alphabet radio OTAN (table sourcée)") if out else (HORS, None, None)

    # CODE COULEUR DES RÉSISTANCES : « chiffre de la bande rouge », « code couleur résistance violet ». On exige un
    # mot-couleur VALIDE (sinon on n'intercepte pas — « résistance de 10 ohm » est de la physique, pas une couleur).
    if ("resistance" in qtoks or "bande" in qtoks or "anneau" in qtoks) and not _PAIRE_MESURE.search(question):
        for w in qtoks:
            st, val = _R.couleur_resistance(w)
            if st == VERIFIE and val is not None:
                return (VERIFIE, str(val), f"code couleur des résistances (bande « {w} » = chiffre)")
        # aucune couleur valide -> on laisse les routes suivantes tenter (pas de return)

    # FRÉQUENCE D'UNE NOTE : « fréquence de la note A4 » / « note La » (FR -> EN, octave 4 par défaut, A4 = 440 Hz).
    if "note" in qtoks and ("frequence" in qtoks or "hauteur" in qtoks or "hertz" in qtoks):
        n = normalise(_dernier_token(question))
        cands = [n.upper()]
        mfr = re.match(r"([a-z]+)(-?\d+)?$", n)
        _FR = {"do": "C", "re": "D", "mi": "E", "fa": "F", "sol": "G", "la": "A", "si": "B"}
        if mfr and mfr.group(1) in _FR:
            cands.append(_FR[mfr.group(1)] + (mfr.group(2) or "4"))   # octave fournie sinon 4 (référence A4=440)
        val = _essaie(_R.frequence_note, *cands)
        return (VERIFIE, f"{val} Hz", "gamme tempérée 12-TET (A4 = 440 Hz)") if val is not None else (HORS, None, None)

    # CHIMIE (casse préservée : H2O ≠ h2o). On essaie l'arg après-préposition PUIS le dernier token (repli).
    if "pourcentage" in qtoks and ("massique" in qtoks or "masse" in qtoks):
        # deux arguments : « pourcentage massique de O dans H2O » -> élément O, formule H2O.
        m = re.search(r"\bde\s+(\w+)\s+dans\s+(\S+)", question, re.IGNORECASE)
        if m:
            st, val = _C.pourcentage_massique(m.group(2).strip(" ?.!"), m.group(1))
            if st == VERIFIE:
                return (VERIFIE, f"{val} %", "calcul — pourcentage massique (IUPAC)")
        return (HORS, None, None)
    if "molaire" in qtoks or ("masse" in qtoks and "moleculaire" in qtoks):
        val = _essaie(_C.masse_molaire, arg, dernier)
        return (VERIFIE, f"{val} g/mol", "calcul — masses atomiques IUPAC") if val is not None else (HORS, None, None)
    if "atomes" in qtoks and ("nombre" in qtoks or "combien" in qtoks or "atomes" in qtoks):
        val = _essaie(_C.nb_atomes, arg, dernier)
        return (VERIFIE, f"{val} atomes", "calcul — formule chimique") if val is not None else (HORS, None, None)
    if "composition" in qtoks:
        val = _essaie(_C.composition, arg, dernier)
        if val is not None:
            txt = ", ".join(f"{n} {el}" for el, n in val.items())
            return (VERIFIE, txt, "calcul — composition atomique")
        return (HORS, None, None)

    # GÉNÉTIQUE : séquences ADN/ARN en MAJUSCULES (repli = dernier token, robuste à « la séquence ATCG »).
    if "complement" in qtoks or "complementaire" in qtoks:
        fn = _G.complement_inverse if ("inverse" in qtoks or "antiparallele" in qtoks) else _G.complement_adn
        val = _essaie(fn, arg.upper(), seq)
        return (VERIFIE, str(val), "appariement Watson-Crick (ADN)") if val is not None else (HORS, None, None)
    if "transcrit" in qtoks or "transcription" in qtoks or "transcris" in qtoks:
        val = _essaie(_G.transcrit, arg.upper(), seq)
        return (VERIFIE, str(val), "transcription ADN→ARN") if val is not None else (HORS, None, None)
    if "traduit" in qtoks or "traduction" in qtoks or "proteine" in qtoks or "traduis" in qtoks:
        val = _essaie(_G.traduit, arg.upper(), seq)
        return (VERIFIE, str(val), "traduction — code génétique standard (NCBI)") if val is not None else (HORS, None, None)
    if "codon" in qtoks or ("acide" in qtoks and "amine" in qtoks):
        val = _essaie(_G.codon_vers_aa, seq, arg.upper())
        return (VERIFIE, str(val), "code génétique standard (NCBI)") if val is not None else (HORS, None, None)

    # PHYSIQUE (formules paramétriques) — tenté en dernier (mots-clés + mesures étiquetées par unité SI).
    return resout_physique(question)
