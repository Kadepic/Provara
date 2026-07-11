"""
MOTEUR D'INVENTION MULTI-ARGUMENT (chantier FORGE — cap multi-arg, 2026-07-12) : franchit le palier mono→binaire.

`moteur_invention.examine_cible` tranche des cibles MONO-argument f(x). Toute une classe d'inventions vit à
PLUSIEURS arguments : f(a, b) = combinaison de deux entrées (arithmétique, distance, moyenne, sommes de carrés,
théorie des nombres…). Ce module ajoute `examine_cible_multi` — chemin SÉPARÉ (zéro impact sur le mono-arg, la
non-régression du moteur mono reste intacte) avec les MÊMES gardes de soundness que le mono-arg (cohérence,
EXISTE_DEJA, unicité comportementale sur sondes, juge held-out en subprocess, nouveauté) → FAUX=0 préservé.

SYMÉTRIE (commutativité, le piège du multi-arg — cf. littérature synthèse) : a+b ≡ b+a sont IDENTIQUES sur
toute sonde → jamais une fausse ambiguïté ; mais a−b ≠ b−a divergent sur une sonde ASYMÉTRIQUE (a≠b). Les
sondes incluent donc le SWAP (b, a) et des paires asymétriques → l'ordre des arguments est discriminé, sound.

Premier RUNG : l'arité 2 (binaire). Le vocabulaire de recombinaison est binaire ; une cible d'arité ≠ 2 non
couverte par le registre tombe honnêtement en BRIQUE_MANQUANTE (l'arité 3+ est le rung suivant, patron identique).
"""
from __future__ import annotations

from auto_invention_ouverte import LIM
from juge import juge
from moteur_invention import (AMBIGU, BRIQUE_MANQUANTE, EXISTE_DEJA, INCOHERENT, INVENTION, Verdict)

# Registre BINAIRE : capacités connues à deux arguments entiers (la nouveauté se mesure CONTRE lui).
EXISTANT_BINAIRE: dict[str, str] = {
    "somme": "a + b",
    "difference": "a - b",
    "produit": "a * b",
    "maximum": "max(a, b)",
    "minimum": "min(a, b)",
    "distance": "abs(a - b)",
    "quotient": "a // b",
    "reste": "a % b",
    "puissance": "a ** b",
    "pgcd": "__import__('math').gcd(a, b)",
    "moyenne_basse": "(a + b) // 2",
}

# Vocabulaire de recombinaison binaire : combineurs sur transformations unaires de chaque argument. Curé et
# BORNÉ (unaires × unaires × combineurs) — assez pour les fonctions binaires canoniques, sans les aimants à
# coïncidences (pas d'affine a+k·b généralisé). La soundness vient des gardes, pas de la petitesse du vocab.
_UNAIRE = ["{v}", "abs({v})", "-{v}"]
_COMBINE = ["{pa} + {pb}", "{pa} - {pb}", "{pa} * {pb}", "max({pa}, {pb})", "min({pa}, {pb})",
            "abs({pa} - {pb})", "{pa} // {pb}", "{pa} % {pb}", "{pa} ** {pb}"]
_BASE_SUPPL = ["b - a", "b // a", "b % a", "b ** a", "a * a + b * b", "a * a - b * b",
               "a * b + a + b", "__import__('math').gcd(a, b)"]


def _params(arite: int) -> list[str]:
    return ["a", "b", "c", "d", "e"][:arite]


def _callable_multi(expr: str, nom: str, params: list[str]):
    src = (expr if expr.lstrip().startswith("def ")
           else f"def {nom}({', '.join(params)}):\n    return {expr}\n")
    ns: dict = {}
    try:
        exec(src, ns)
        return ns.get(nom)
    except Exception:
        return None


def _reproduit_multi(f, paires) -> bool:
    if f is None:
        return False
    for args, o in paires:
        try:
            r = f(*args)
            # égalité TYPE-EXACTE sur bool (même règle que le mono-arg : 1 n'est pas True).
            if r != o or isinstance(r, bool) != isinstance(o, bool):
                return False
        except Exception:
            return False
    return True


def _sig_multi(f, sondes) -> list[str]:
    out = []
    for s in sondes:
        try:
            out.append(repr(f(*s)))
        except Exception:
            out.append("ERR")
    return out


def _candidats_binaires(exemples) -> list[str]:
    """Expressions binaires qui REPRODUISENT les exemples (validation contextuelle). Bornée, dédupliquée."""
    cands: set[str] = set(EXISTANT_BINAIRE.values()) | set(_BASE_SUPPL)
    for ta in _UNAIRE:
        pa = ta.format(v="a")
        for tb in _UNAIRE:
            pb = tb.format(v="b")
            for c in _COMBINE:
                cands.add(c.format(pa=pa, pb=pb))
    ok = []
    for e in cands:
        if _reproduit_multi(_callable_multi(e, "f", ["a", "b"]), exemples):
            ok.append(e)
    return ok


def _sondes_binaires(exemples) -> list[tuple]:
    """Sondes de stress dérivées des exemples : SWAP (discrimine le non-commutatif) + perturbations DANS le
    domaine observé (signe gardé comme en mono-arg). Pas de sortie inventée : seulement des entrées."""
    ints = [v for args, _ in exemples for v in args if isinstance(v, int) and not isinstance(v, bool)]
    signe = any(v < 0 for v in ints)
    out = []
    for args, _ in exemples:
        if len(args) != 2:
            continue
        a, b = args
        out.append((a, b))
        out.append((b, a))                          # SWAP : a−b vs b−a divergent ici
        if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) and not isinstance(b, bool):
            out.append((a + 1, b))
            out.append((a, b + 1))
            out.append((a + 1, b + 2))              # paire asymétrique
            if signe:
                out.append((-a, b))
    seen, res = set(), []
    for s in out:
        k = repr(s)
        if k not in seen:
            seen.add(k)
            res.append(s)
    return res


def _asserts_multi(nom: str, paires) -> str:
    from demande import _asserts
    return _asserts(nom, [(tuple(args), o) for args, o in paires])


def examine_cible_multi(nom: str, exemples, exemples_held, existant: dict | None = None) -> Verdict:
    """Tranche une cible MULTI-ARGUMENT en EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT.
    `exemples`/`exemples_held` = listes de (args, sortie) où args est un tuple/liste d'arguments. Mêmes garanties
    de soundness que le mono-arg. `existant` = registre binaire (défaut EXISTANT_BINAIRE)."""
    existant = EXISTANT_BINAIRE if existant is None else existant
    exemples = [(tuple(a), o) for a, o in exemples]
    held = [(tuple(a), o) for a, o in (exemples_held or [])]
    toutes = exemples + held
    if not toutes:
        return Verdict(INCOHERENT, nom, justification="aucun exemple")

    arites = {len(a) for a, _ in toutes}
    if len(arites) != 1:
        return Verdict(INCOHERENT, nom, justification="arité incohérente entre les exemples")
    arite = arites.pop()
    params = _params(arite)

    # 0) COHÉRENCE : même entrée -> deux sorties = contradiction.
    vus: dict = {}
    for a, o in toutes:
        k = repr(a)
        if k in vus and vus[k] != o:
            return Verdict(INCOHERENT, nom, justification="deux sorties différentes pour la même entrée")
        vus[k] = o

    sondes = _sondes_binaires(toutes)

    # 1) EXISTE DÉJÀ : une capacité binaire connue reproduit la cible ?
    for capa, expr in existant.items():
        if _reproduit_multi(_callable_multi(expr, nom, params), toutes):
            return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                           justification="déjà couvert par l'inventaire binaire existant")

    # 2) RÉALISABLE par recombinaison binaire ? (rung actuel : arité 2)
    candidats = _candidats_binaires(toutes) if arite == 2 else []
    if candidats:
        sigs = {e: _sig_multi(_callable_multi(e, nom, params), sondes) for e in candidats}
        for j, s in enumerate(sondes):
            if len({sigs[e][j] for e in candidats}) > 1:
                return Verdict(AMBIGU, nom, sonde=s,
                               justification="plusieurs réalisations binaires distinctes satisfont le spec")
        S = min(candidats, key=len)                 # Occam
        code = f"def {nom}({', '.join(params)}):\n    return {S}\n"
        if held and not juge(code, _asserts_multi(nom, held), LIM).passe:
            return Verdict(BRIQUE_MANQUANTE, nom, justification="réalisation non confirmée par le juge sur le held-out")
        sig_S = _sig_multi(_callable_multi(S, nom, params), sondes)
        for capa, expr in existant.items():
            g = _callable_multi(expr, nom, params)
            if g is not None and _sig_multi(g, sondes) == sig_S and _reproduit_multi(g, toutes):
                return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                               justification="réalisable mais équivalent à une capacité binaire existante (non nouveau)")
        return Verdict(INVENTION, nom, par=S,
                       justification="recombinaison binaire unique sous le spec, vérifiée (held-out), comportement nouveau")

    # 3) Aucune recombinaison binaire connue -> FRONTIÈRE.
    return Verdict(BRIQUE_MANQUANTE, nom,
                   justification="cohérente mais non réalisable par recombinaison binaire connue : un principe neuf est requis")
