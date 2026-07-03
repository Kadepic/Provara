"""
INDUCTION DE RÈGLES DE HORN (ILP borné) — produire des règles VALIDÉES pour deduction.py (2026-07-02).

POURQUOI : `deduction.py` (Datalog) est vivant mais AFFAMÉ — il CONSOMME des règles écrites à la main, rien ne les
PRODUIT. Ce module propose des règles structurelles candidates (transitivité, symétrie, réflexivité, inverse) sur
une relation binaire, puis les VALIDE contre des exemples AVANT toute adoption.

FAUX=0 — la ligne rouge de l'induction :
  • Une règle n'est JAMAIS déclarée « vraie ». Au mieux CONSISTANTE avec les exemples fournis : elle couvre ≥1
    exemple POSITIF (support réel) ET ne dérive AUCUN exemple NÉGATIF (0 violation) — vérifié AU POINT FIXE
    (toutes profondeurs), la sémantique réelle d'un Datalog qui matérialise. Un seul négatif dérivé -> REJET.
  • Sans exemples NÉGATIFS on ne peut pas réfuter une règle (monde ouvert : absence ≠ fausseté) -> on NE VALIDE PAS
    (statut « non_refutable »), on ne l'adopte pas comme certaine. Jamais de CWA implicite.
  • Les faits qu'une règle consistante IMPLIQUE au-delà des exemples (`nouveaux`) sont marqués INCERTAINS (une
    généralisation, pas un fait FAUX=0) — à confirmer par ailleurs, jamais injectés comme certains.
Stdlib pur, déterministe, souverain. Relations binaires = ensembles de couples (x, y).
"""
from __future__ import annotations

TRANSITIVITE = "transitivite"     # R(x,z) :- R(x,y), R(y,z)
SYMETRIE = "symetrie"             # R(y,x) :- R(x,y)
REFLEXIVITE = "reflexivite"       # R(x,x) :- R(x,_) ou R(_,x)
CANDIDATES = (TRANSITIVITE, SYMETRIE, REFLEXIVITE)


def derive(type_regle: str, faits) -> set:
    """Faits dérivés en appliquant UNE fois la règle structurelle à l'ensemble `faits` (couples). Déterministe."""
    f = set(faits)
    if type_regle == TRANSITIVITE:
        succ = {}
        for (x, y) in f:
            succ.setdefault(y, set()).add(x)     # x -> y : pour composer, on cherche y == y' de (y', z)
        out = set()
        for (y2, z) in f:
            for x in succ.get(y2, ()):           # (x, y2) ∈ f et (y2, z) ∈ f -> (x, z)
                out.add((x, z))
        return out
    if type_regle == SYMETRIE:
        return {(y, x) for (x, y) in f}
    if type_regle == REFLEXIVITE:
        elems = {x for (x, _y) in f} | {y for (_x, y) in f}
        return {(e, e) for e in elems}
    raise ValueError(f"règle inconnue : {type_regle}")


def _couples(exemples, etiquette: str) -> set:
    """Force la forme « ensemble de couples (x, y) ». Un couple NU (`('a','b')` au lieu de `{('a','b')}`) ou une
    chaîne deviendraient des éléments SCALAIRES qui ne matchent jamais un couple dérivé : la réfutation serait
    silencieusement désarmée ET le garde monde-ouvert contourné (attaque exécutée 2026-07-02). Malformé -> ValueError."""
    s = set(exemples)
    for c in s:
        if not (isinstance(c, tuple) and len(c) == 2):
            raise ValueError(f"{etiquette} : exemple malformé {c!r} (attendu un ENSEMBLE de couples (x, y))")
    return s


def cloture_derives(type_regle: str, faits) -> set:
    """TOUT ce que la règle peut dériver de `faits` au POINT FIXE (union des applications jusqu'à stabilité).
    C'est la sémantique RÉELLE d'un moteur Datalog qui matérialise : valider sur UNE application laissait une
    règle « consistante » dériver un négatif déclaré à profondeur ≥ 2 (attaque exécutée 2026-07-02).
    Termine : domaine fini (couples sur les éléments présents). Déterministe."""
    f = set(faits)
    derives = set()
    while True:
        d = derive(type_regle, f)
        derives |= d
        nouveaux = d - f
        if not nouveaux:
            return derives
        f |= nouveaux


def evalue(type_regle: str, positifs, negatifs) -> dict:
    """Évalue une règle candidate contre des exemples. Renvoie :
      {support: nb positifs re-dérivés, viole: {négatifs dérivés}, nouveaux: {dérivés hors exemples}, consistante: bool}.
    Deux sémantiques VOLONTAIREMENT distinctes :
      • support = UNE application (preuve réelle : un positif expliqué par les AUTRES). Au point fixe, symétrie/
        transitivité re-dérivent chaque positif via un aller-retour x→y→x : un « support » vide de preuve.
      • viole / nouveaux = POINT FIXE (sémantique de déploiement Datalog) : aucun négatif atteignable à AUCUNE
        profondeur, et `nouveaux` = l'inventaire COMPLET des généralisations au moment de l'évaluation.
    consistante = (viole == ∅)."""
    pos, neg = _couples(positifs, "positifs"), _couples(negatifs, "negatifs")
    d = cloture_derives(type_regle, pos)
    viole = d & neg
    support = derive(type_regle, pos) & pos
    nouveaux = d - pos - neg
    return {"support": len(support), "viole": viole, "nouveaux": nouveaux, "consistante": not viole}


def induit(positifs, negatifs, candidates=CANDIDATES) -> dict:
    """Induit les règles structurelles à partir d'exemples. Renvoie :
      {validees: [(type, support, nouveaux)], rejetees: [(type, exemple_négatif_dérivé)], non_refutables: [type]}.
    - validee   = consistante (0 négatif dérivé) ET support > 0 ET négatifs FOURNIS (donc réfutable et non réfutée).
    - rejetee   = dérive au moins un négatif connu (FAUX=0 : la règle produit un fait faux).
    - non_refutable = aucun négatif fourni -> impossible de valider en monde ouvert -> NON adoptée (abstention).
    Déterministe (ordre des candidates préservé)."""
    pos = _couples(positifs, "positifs")     # matérialisé UNE fois (un générateur ne serait consommé que par le
    neg = set(negatifs)                      # 1er candidat -> règles suivantes silencieusement perdues)
    if pos & _couples(neg, "negatifs"):
        raise ValueError(f"exemples contradictoires : {sorted(pos & neg)[:3]} à la fois positifs ET négatifs")
    validees, rejetees, non_refutables = [], [], []
    for t in candidates:
        ev = evalue(t, pos, neg)
        if not neg:
            non_refutables.append(t)                          # rien pour réfuter -> on n'adopte pas
        elif not ev["consistante"]:
            rejetees.append((t, sorted(ev["viole"])[0]))      # un négatif dérivé -> REJET (FAUX=0)
        elif ev["support"] > 0:
            validees.append((t, ev["support"], sorted(ev["nouveaux"])))
        # consistante mais support 0 (n'explique aucun positif) -> ni validée ni rejetée (inutile), ignorée
    return {"validees": validees, "rejetees": rejetees, "non_refutables": non_refutables}
