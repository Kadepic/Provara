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
    "seconde": ("T", 1.0), "secondes": ("T", 1.0),
    "min": ("T", 60.0), "minute": ("T", 60.0), "minutes": ("T", 60.0),
    "heure": ("T", 3600.0), "heures": ("T", 3600.0),
    "jour": ("T", 86400.0), "jours": ("T", 86400.0),
    "semaine": ("T", 604800.0), "semaines": ("T", 604800.0),
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


def resout_conversion(question: str):
    """Convertit entre 2 unités de MÊME dimension (table fermée, exacte). (VERIFIE, texte, source) ou (HORS,None,None).
    FAUX=0 : unité inconnue ou dimensions différentes -> HORS. Ne fire que sur un motif de conversion explicite."""
    q = normalise(question)                          # accents/casse -> clés de table normalisées
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
    return (VERIFIE, f"{_fmt_nombre(val)} {dst}", "conversion d'unités (facteurs exacts, même dimension)")


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

    # POURCENTAGE : « 20% de 150 », « 20 pour cent de 150 » -> 30 (arithmétique exacte, sans module tiers).
    mp = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:%|pour ?cent(?:s)?|pourcent)\s+(?:de|du|des|d['’]|sur)\s+(\d+(?:[.,]\d+)?)",
                   question, re.I)
    if mp:
        p = float(mp.group(1).replace(",", ".")); base = float(mp.group(2).replace(",", "."))
        v = p / 100.0 * base
        return (VERIFIE, _fmt_nombre(v), "calcul — pourcentage")

    # PGCD / PPCM : « pgcd de 12 et 18 », « ppcm de 4 et 6 » (2 entiers requis).
    if ("pgcd" in qtoks or "diviseur" in q and "commun" in q) and len(ent) >= 2:
        return (VERIFIE, str(_AM.pgcd(ent[0], ent[1])), "arithmétique — PGCD (Euclide)")
    if ("ppcm" in qtoks or "multiple" in q and "commun" in q) and len(ent) >= 2:
        g = _AM.pgcd(ent[0], ent[1])
        return (VERIFIE, str(ent[0] * ent[1] // g) if g else "0", "arithmétique — PPCM")

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
