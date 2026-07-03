"""
ZONE-ROUTING — activation parcimonieuse « façon cerveau » (2026-06-17, vision Yohan).

Le moteur unique a ~35 étages (zones). L'escalade canonique les essaie tous, du moins cher au plus cher, et paie
l'échec de toutes les zones AMONT avant la bonne (mesuré : oracle de routage = plafond −98 % d'appels juge).

`RouteurZone` apprend, depuis le PASSÉ (les succès de la montée), une carte `clé(tâche) -> votes d'étages`, où
`clé = (arité, type_entrée, type_sortie)` est LISIBLE avant de résoudre (signature + littéraux des tests). Sur une
nouvelle tâche, il PRÉDIT les zones probables (par fréquence de vote) ; `resoudre_route` les essaie D'ABORD, puis
RETOMBE sur l'escalade complète des zones restantes -> **couverture STRICTEMENT identique à l'escalade** (jamais de
perte : règle « réordonner, jamais filtrer »). Gain = sauter les zones qu'on n'essaie plus quand la prédiction tient.

PRINCIPE (régime) : à froid (aucun vote) -> predit() rend [] -> resoudre_route == escalade canonique (zéro risque).
Le routeur se RÉCHAUFFE avec le store (le passé nourrit le présent) ; le gain croît avec l'expérience. Le signal
GÉNÉRALISE : toute tâche de même clé hérite des étages déjà vus pour cette clé (pas seulement les tâches répétées).
"""

from __future__ import annotations

import ast
import re

from juge import juge


def _classe(v):
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, dict):
        return "dict"
    if isinstance(v, tuple):
        return "tuple"
    if isinstance(v, list):
        if v and all(isinstance(e, list) for e in v):
            return "list[list]"
        if v and all(isinstance(e, tuple) for e in v):
            return "list[tuple]"
        return "list"
    return "?"


def _type_noeud(node):
    try:
        return _classe(ast.literal_eval(node))
    except Exception:
        return "?"


def _exemples(tache):
    """[(entrée0, sortie)] lus dans les asserts `c(entrée0, ...) == sortie` (visible + held), littéraux seulement."""
    ex = []
    for src in (getattr(tache, "tests", None), getattr(tache, "tests_held_out", None)):
        if not src:
            continue
        try:
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Compare) and isinstance(node.left, ast.Call) \
                        and isinstance(node.left.func, ast.Name) and node.left.func.id == "c" and node.left.args:
                    try:
                        ex.append((ast.literal_eval(node.left.args[0]), ast.literal_eval(node.comparators[0])))
                    except Exception:
                        pass
        except Exception:
            pass
    return ex


def _features_sortie(ex):
    """Signaux CHEAP sur le rapport entrée/sortie observé (sélectionnés par mesure_signal_v3 : ils cassent en partie
    l'ambiguïté (1,list,int)). Booléens, agnostiques au type (False inoffensif hors list->int). Pas un prior de
    correction : juste de quoi RANGER plus finement les zones (le fallback garde la couverture)."""
    def _ent(x): return isinstance(x, int) and not isinstance(x, bool)
    L = [(a, o) for a, o in ex if isinstance(a, list) and a]                        # entrée = liste non vide
    Lnum = [(a, o) for a, o in L if _ent(o) and all(_ent(e) for e in a)]            # liste plate d'entiers -> sortie int
    f_borne = bool(Lnum) and all(o <= len(a) for a, o in Lnum)                      # comptage / longueur
    f_elem = bool(L) and all(o in a for a, o in L)                                  # sélection d'un élément
    f_agrege = any(o > max(a) for a, o in Lnum)                                     # échelle d'agrégation (somme…)
    f_neg = any(_ent(o) and o < 0 for _, o in ex)                                   # différence / signé
    # NB : une feature de MAGNITUDE int->int (sortie croît ?) a été testée (2026-06-20) puis RÉVERTÉE : elle aide
    # integer_break (203->131) mais désaligne les frères (hamming 10->327, perfect_squares 167->1073) -> net négatif
    # sur la généralisation. Les features de magnitude ne désambiguïsent PAS robustement int->int / 2-args-int.
    return (f_borne, f_elem, f_agrege, f_neg)


def cle_tache(tache) -> tuple:
    """Clé de routage LISIBLE sans résoudre : (arité, type_entrée, type_sortie) + signaux cheap sur les exemples
    (borne_len, élément, agrégat, signé). arité <- signature ; types+signaux <- littéraux des asserts du test.
    Les signaux désambiguent la famille scalaire (1,list,int) (mesuré : 14 étages -> sous-clés ~3,5)."""
    arity = 0
    m = re.search(r"def\s+\w+\s*\(([^)]*)\)", tache.prompt or "")
    if m and m.group(1).strip():
        arity = len([p for p in m.group(1).split(",") if p.strip()])
    in_t = out_t = "?"
    try:
        for node in ast.walk(ast.parse(tache.tests)):
            if isinstance(node, ast.Compare) and isinstance(node.left, ast.Call) \
                    and isinstance(node.left.func, ast.Name) and node.left.func.id == "c":
                if node.left.args:
                    in_t = _type_noeud(node.left.args[0])
                out_t = _type_noeud(node.comparators[0])
                break
    except Exception:
        pass
    return (arity, in_t, out_t) + _features_sortie(_exemples(tache))


class RouteurZone:
    """Carte apprise `clé -> {étage: nb de succès}`. Ne jette RIEN, ne filtre RIEN : il ORDONNE les zones.

    GATE DE CONFIANCE (v2, exigence « sûr avant rapide ») : on ne PRÉDIT que si la clé est DISCRIMINANTE — au
    plus `seuil` étages distincts l'ont résolue. Sinon (clé ambiguë, ex. (1,list,int) -> 14 étages) on rend []
    -> escalade canonique pure -> AUCUN réordonnancement -> impossible de faire pire que l'escalade. Mesuré : sans
    ce gate, router une tâche cheap-précoce par une clé ambiguë la traînait à travers des étages profonds (compte_pairs
    12 -> 1638 appels). Le gate supprime ce risque ; les clés pures/peu ambiguës (la majorité) gardent tout le gain."""

    def __init__(self, seuil: int = 8):
        self._votes: dict[tuple, dict[str, int]] = {}
        self._seuil = seuil

    def apprendre(self, tache, etage: str) -> None:
        if not etage:
            return
        c = cle_tache(tache)
        self._votes.setdefault(c, {})
        self._votes[c][etage] = self._votes[c].get(etage, 0) + 1

    def predit(self, tache) -> list[str]:
        """Étages probables si la clé est CONFIANTE (<= seuil étages) ; [] sinon -> escalade pure (sûr).

        NB (2026-06-22) : un ROUTAGE PAR CLÉ VOISINE (k-NN/Hamming, emprunt des votes de la clé la plus proche quand
        la clé exacte manque) a été essayé puis RÉVERTÉ : dans les familles ambiguës (ex. (1,list,int)), il route vers
        l'étage générique puissant (tableaux) du voisin et MASQUE les briques spécifiques (single_number_ii ->
        tableaux au lieu de premier-unique : valide_vague28 cassé). Bénéfice marginal, masquage réel -> « sûr avant
        rapide ». La généralisation aux clés neuves passe par des étages dédiés + frères de prior, pas par l'emprunt."""
        votes = self._votes.get(cle_tache(tache), {})
        if not votes or len(votes) > self._seuil:
            return []
        return [e for e, _ in sorted(votes.items(), key=lambda kv: -kv[1])]

    def votes_confiants(self, tache) -> dict:
        """Votes {étage: n} de la clé si elle est CONFIANTE (même gate que `predit`) ; {} sinon. Sert aux
        stratégies pondérées (Smith / SUNNY) : elles ont besoin des POIDS, pas seulement de l'ordre. Sound :
        même gate -> mêmes clés servies ; un poids n'influence que l'ORDRE de traversée, jamais la couverture."""
        votes = self._votes.get(cle_tache(tache), {})
        if not votes or len(votes) > self._seuil:
            return {}
        return dict(votes)

    def etat(self) -> dict:
        return {c: dict(v) for c, v in self._votes.items()}

    def fusionne(self, votes: dict) -> None:
        """Injecte des votes (PRIOR appris hors-ligne) -> le routeur est CHAUD dès le 1ᵉʳ appel sur les clés connues.
        Additif : ne remplace rien, cumule. Sound : le gate de confiance + le fallback escalade restent en place
        (un prior bruité ne fait jamais PIRE que l'escalade)."""
        for c, vs in votes.items():
            c = tuple(c)
            self._votes.setdefault(c, {})
            for e, n in vs.items():
                self._votes[c][e] = self._votes[c].get(e, 0) + n

    def sauve(self, chemin) -> None:
        import json
        from pathlib import Path
        data = [[list(c), v] for c, v in self._votes.items()]
        Path(chemin).write_text(json.dumps(data))

    def charge(self, chemin) -> bool:
        """Charge un prior depuis le disque (clés tuples re-sérialisées). Rend True si chargé. Tolérant : absent -> False."""
        import json
        from pathlib import Path
        p = Path(chemin)
        if not p.exists():
            return False
        try:
            for c, v in json.loads(p.read_text()):
                self.fusionne({tuple(c): v})
        except Exception:
            return False
        return True


def resoudre_route(orchestre, tache, routeur: RouteurZone, limites=None, k: int = 400):
    """Comme `compounding.resoudre` mais on tente d'ABORD les zones prédites, PUIS le reste (FALLBACK -> couverture
    identique). Les zones prédites ET le fallback sont parcourus en ORDRE CANONIQUE (cheap-first préservé) -> on ne
    front-load jamais un étage cher -> sur un hit, routé <= escalade (on saute les zones non prédites d'avant le
    solveur) ; sur un mis-gate, surcoût borné aux zones prédites situées après le solveur. Renvoie (etage, appels,
    code, verdict). N'APPREND PAS (apprentissage explicite via routeur.apprendre, fait par la montée sur succès)."""
    etages = orchestre.etages(tache.prompt, k)             # [(nom, candidats)] en ordre canonique
    par_nom = {nom: cands for nom, cands in etages}
    predits = {e for e in routeur.predit(tache) if e in par_nom}
    noms = [nom for nom, _ in etages]                                   # ordre canonique
    ordre = [n for n in noms if n in predits] + [n for n in noms if n not in predits]   # prédits (canon) puis reste (canon)
    appels = 0
    for nom in ordre:
        for code in par_nom[nom]:
            appels += 1
            v = juge(code, tache.tests, limites)
            if not v.passe:
                continue
            if tache.tests_held_out and not juge(code, tache.tests_held_out, limites).passe:
                continue
            return nom, appels, code, v
    return None, appels, None, None


def resoudre_route_rr(orchestre, tache, routeur: RouteurZone, limites=None, k: int = 400):
    """ROUTING + ROUND-ROBIN (2026-06-17, vérité cachée du test exotique : le round-robin = −84 % en COLD, 0 masquage
    sur la batterie durcie). Étages PRÉDITS essayés À FOND, en ordre (gain CHAUD : un succès routé en ~1 appel) ; PUIS
    le fallback parcouru en ROUND-ROBIN (largeur d'abord : 1ᵉʳ candidat de chaque étage, puis le 2ᵉ…) -> en COLD/non
    prédit, on atteint vite un solveur dont le candidat gagnant est tôt-dans-son-étage, SANS épuiser les étages amont.
    Couverture identique (solveur unique). Le meilleur des deux : chaud routé, froid round-robin."""
    etages = orchestre.etages(tache.prompt, k)
    par_nom = {nom: cands for nom, cands in etages}
    predits = [e for e in routeur.predit(tache) if e in par_nom]
    reste = [nom for nom, _ in etages if nom not in predits]
    appels = 0

    def _gagne(code):
        return juge(code, tache.tests, limites).passe and \
            (not tache.tests_held_out or juge(code, tache.tests_held_out, limites).passe)

    for nom in predits:                                   # 1. prédits À FOND (gain chaud)
        for code in par_nom[nom]:
            appels += 1
            if _gagne(code):
                return nom, appels, code, juge(code, tache.tests, limites)
    i, encore = 0, True                                   # 2. fallback ROUND-ROBIN (gain cold)
    while encore:
        encore = False
        for nom in reste:
            cands = par_nom[nom]
            if i < len(cands):
                encore = True
                appels += 1
                if _gagne(cands[i]):
                    return nom, appels, cands[i], juge(cands[i], tache.tests, limites)
        i += 1
    return None, appels, None, None


def auto_configure(orchestre, taches, seuils=(4, 8, 12, 16), ks=(200, 400, 800), limites=None):
    """AUTO-CONFIGURATION OFFLINE (AutoFolio-lite, 2026-07-02) des 2 constantes du routage jusqu'ici fixées À LA
    MAIN (seuil de confiance=8, k candidats/étage=400). Protocole hindsight, borné et SOUND :
      1. résout la batterie à FROID (escalade pure) au k MAX -> apprend clé->étage gagnant + fixe la COUVERTURE
         DE RÉFÉRENCE (le meilleur k testé : k plus petit ne peut que perdre des candidats, jamais en gagner) ;
      2. pour chaque (seuil, k) : routeur réchauffé de ces votes, coût total mesuré via resoudre_route_rr2 ;
      3. ÉLIMINE toute config dont la couverture n'est pas ≥ la référence (k n'est PAS un pur réordonnancement :
         il borne le pool de candidats -> un k trop bas peut perdre une tâche = interdit) ; coût minimal ensuite.
    Renvoie (meilleure_config | None, mesures). Persistance : `sauve_config` / `charge_config` (routeur_config.json,
    chargé opt-in par AssistantIA(config="DEFAUT") — les défauts codés restent inchangés sans opt-in)."""
    kmax = max(ks)
    succes = {}
    for t in taches:
        etage, _a, code, _v = resoudre_route(orchestre, t, RouteurZone(), limites, kmax)   # escalade froide pure
        if code is not None:
            succes[t.id] = (t, etage)
    couverture_ref = set(succes)
    mesures = []
    for s in seuils:
        for k in ks:
            rz = RouteurZone(seuil=s)
            for t, etage in succes.values():
                rz.apprendre(t, etage)
            total, couverts = 0, set()
            for t in taches:
                _e, appels, code, _v = resoudre_route_rr2(orchestre, t, rz, limites, k)
                total += appels
                if code is not None:
                    couverts.add(t.id)
            mesures.append({"seuil": s, "k": k, "appels": total, "couverture": len(couverts),
                            "couverture_ok": couverts >= couverture_ref})
    valides = [m for m in mesures if m["couverture_ok"]]
    best = min(valides, key=lambda m: (m["appels"], m["seuil"], m["k"])) if valides else None
    return best, mesures


def sauve_config(config: dict, chemin) -> None:
    """Persiste la config auto-mesurée (seuil, k, mesures) — atomique (tmp + replace)."""
    import json
    import os
    from pathlib import Path
    p = Path(chemin)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, ensure_ascii=False, indent=1))
    os.replace(tmp, p)


def charge_config(chemin) -> dict | None:
    """Charge une config persistée ; None si absente/illisible (les défauts codés s'appliquent alors)."""
    import json
    from pathlib import Path
    p = Path(chemin)
    if not p.exists():
        return None
    try:
        cfg = json.loads(p.read_text())
        return cfg if isinstance(cfg, dict) and "seuil" in cfg and "k" in cfg else None
    except Exception:
        return None


def resoudre_route_rr2(orchestre, tache, routeur: RouteurZone, limites=None, k: int = 400):
    """HYBRIDE PER-TÂCHE (2026-06-19, idée Yohan « impose v3a là où il gagne, v3b là où il gagne »). `rr` essaie les
    étages PRÉDITS À FOND en ordre canonique (PROFONDEUR : optimal quand le gagnant est profond-dans-son-étage, mais
    lent quand le bon étage est TARD en canonique alors que son gagnant est TÔT). Ici on parcourt l'ensemble prédit en
    ROUND-ROBIN (LARGEUR : 1ᵉʳ candidat de chaque étage prédit, puis le 2ᵉ…). Propriété clé :
      - clé UNIQUE (1 étage prédit)  -> round-robin == à-fond -> le gain CHAUD est INTACT.
      - clé AMBIGUË (n étages prédits) -> la largeur atteint vite un gagnant tôt-dans-un-étage-tardif SANS épuiser
        d'abord un étage profond -> capte le MEILLEUR de v3a (profond) ET de v3b (largeur) selon la tâche, sans rien
        choisir à la main : la structure du round-robin réalise la sélection per-tâche que Yohan décrit.
    Puis fallback round-robin sur le reste -> COUVERTURE STRICTEMENT IDENTIQUE (solveur unique). Renvoie (etage, appels,
    code, verdict). N'apprend pas (apprentissage explicite via routeur.apprendre)."""
    etages = orchestre.etages(tache.prompt, k)
    par_nom = {nom: cands for nom, cands in etages}
    predits = [e for e in routeur.predit(tache) if e in par_nom]
    reste = [nom for nom, _ in etages if nom not in predits]
    appels = 0

    def _gagne(code):
        return juge(code, tache.tests, limites).passe and \
            (not tache.tests_held_out or juge(code, tache.tests_held_out, limites).passe)

    def _rr(noms):                                         # round-robin (largeur) sur une liste d'étages
        nonlocal appels
        i, encore = 0, True
        while encore:
            encore = False
            for nom in noms:
                cands = par_nom[nom]
                if i < len(cands):
                    encore = True
                    appels += 1
                    if _gagne(cands[i]):
                        return nom, cands[i]
            i += 1
        return None, None

    nom, code = _rr(predits)                               # 1. prédits en LARGEUR (hybride per-tâche)
    if code is None:
        nom, code = _rr(reste)                             # 2. fallback round-robin (couverture identique)
    if code is None:
        return None, appels, None, None
    return nom, appels, code, juge(code, tache.tests, limites)
