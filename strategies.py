"""
STRATÉGIES DE TRAVERSÉE + ROUTAGE DE STRATÉGIE PAR CLÉ (2026-06-19, idée Yohan « occam là où il gagne, rr2 là où il
perd » — validée par mesure_routage_strategie : per-clé LOO honnête = −24 %, hindsight = −32 %, oracle = −38 %).

PRINCIPE. Toutes les stratégies parcourent le MÊME ensemble de candidats (étages prédits PUIS fallback) -> COUVERTURE
STRICTEMENT IDENTIQUE quelle que soit la stratégie. Elles ne diffèrent QUE par l'ORDRE -> le choix de stratégie est
NEUTRE EN CORRECTION : router vers une mauvaise stratégie coûte plus d'appels, JAMAIS un faux résultat. C'est pourquoi
apprendre par clé la stratégie la moins chère est SÛR PAR CONSTRUCTION (≠ un prior de correction).

Registre (toutes : prédits puis fallback ; round-robin = largeur ; voir mesure_structure*) :
  - rr2          : round-robin largeur stride 1 (référence câblée, near-oracle global).
  - costw        : round-robin, étages triés par nb de candidats CROISSANT (bon-marché d'abord). +1.2 % global sûr.
  - rr_occam     : round-robin, candidats triés par LONGUEUR à l'intérieur de chaque étage (simplicité locale).
  - costw_occam  : costw + simplicité intra-étage.
(rr_occam/costw_occam PERDENT en global moyen mais GAGNENT gros sur certaines clés -> d'où le routage par clé.)

RouteurStrategie : clé(tâche) -> coût moyen observé par stratégie ; predit() rend la moins chère vue, sinon "rr2"
(défaut SÛR à froid). On le réchauffe soit par l'usage, soit par un warm-up amorti (apprendre_toutes).
"""

from __future__ import annotations

from juge import juge
from prefiltre import faire_gagne_prefiltre
from routeur import cle_tache
from typage import reordonne_par_type, type_attendu


# --- traverseurs élémentaires (appels = 1 par candidat testé, comme routeur.resoudre_route_rr2) ---

def _rr(par_nom, noms, gagne, stride=1):
    appels, i, encore = 0, 0, True
    while encore:
        encore = False
        for nom in noms:
            cands = par_nom[nom]
            for s in range(stride):
                idx = i + s
                if idx < len(cands):
                    encore = True
                    appels += 1
                    if gagne(cands[idx]):
                        return nom, cands[idx], appels
        i += stride
    return None, None, appels


def _trier_intra(par_nom):
    return {nom: sorted(cands, key=len) for nom, cands in par_nom.items()}


def _phases(par_nom, predits, reste, gagne, runner):
    n, c, a1 = runner(par_nom, predits, gagne)
    if c is not None:
        return n, c, a1
    n, c, a2 = runner(par_nom, reste, gagne)
    return n, c, a1 + a2


def st_rr2(par_nom, predits, reste, gagne, votes=None):
    return _phases(par_nom, predits, reste, gagne, lambda p, n, g: _rr(p, n, g, 1))


def st_costw(par_nom, predits, reste, gagne, votes=None):
    p = sorted(predits, key=lambda nom: len(par_nom[nom]))
    rs = sorted(reste, key=lambda nom: len(par_nom[nom]))
    n, c, a1 = _rr(par_nom, p, gagne, 1)
    if c is not None:
        return n, c, a1
    n, c, a2 = _rr(par_nom, rs, gagne, 1)
    return n, c, a1 + a2


def st_rr_occam(par_nom, predits, reste, gagne, votes=None):
    pn = _trier_intra(par_nom)
    return _phases(pn, predits, reste, gagne, lambda p, n, g: _rr(p, n, g, 1))


def st_costw_occam(par_nom, predits, reste, gagne, votes=None):
    pn = _trier_intra(par_nom)
    p = sorted(predits, key=lambda nom: len(pn[nom]))
    rs = sorted(reste, key=lambda nom: len(pn[nom]))
    n, c, a1 = _rr(pn, p, gagne, 1)
    if c is not None:
        return n, c, a1
    n, c, a2 = _rr(pn, rs, gagne, 1)
    return n, c, a1 + a2


# --- STRATÉGIES SOTA DES PORTFOLIOS (2026-07-02, recherche web §4ter ETAT_REEL) ------------------------------
# Les solveurs-portfolios (SATzilla / SUNNY / littérature scheduling) prouvent que « lancer le moins cher qui
# marche, juger par le vérificateur » se raffine par 3 ordonnancements classiques. Tous passent par le REGISTRE
# per-clé -> adoption UNIQUEMENT là où la mesure les donne moins chers ; couverture identique par construction
# (mêmes candidats, autre ordre) ; le juge reste l'arbitre. `votes` (poids appris, cf. RouteurZone.votes_confiants)
# est optionnel : sans votes, chaque stratégie dégrade proprement vers son ordre sans poids.

def st_smith(par_nom, predits, reste, gagne, votes=None):
    """SMITH'S RULE (WSPT, 1956) : ordonnancer par ratio poids/coût décroissant minimise l'attente pondérée.
    Ici : étages prédits triés par votes/nb_candidats décroissant (probabilité de succès par unité de coût),
    chacun À FOND (le ratio a déjà arbitré profondeur vs largeur) ; puis fallback round-robin standard."""
    v = votes or {}
    p = sorted(predits, key=lambda nom: -(v.get(nom, 1) / max(1, len(par_nom[nom]))))
    appels = 0
    for nom in p:
        for code in par_nom[nom]:
            appels += 1
            if gagne(code):
                return nom, code, appels
    n, c, a2 = _rr(par_nom, reste, gagne, 1)
    return n, c, appels + a2


def st_sunny(par_nom, predits, reste, gagne, votes=None):
    """SUNNY (Amadini et al. 2014) : allouer le budget aux solveurs PROPORTIONNELLEMENT à leurs succès observés.
    Ici : round-robin PONDÉRÉ sur les étages prédits — à chaque tour, l'étage e consomme ~votes(e) candidats
    (≥1, plafonné à 4 pour ne pas dégénérer en à-fond) ; puis fallback round-robin standard."""
    v = votes or {}
    appels = 0
    if predits:
        stride = {nom: max(1, min(4, v.get(nom, 1))) for nom in predits}
        pos = {nom: 0 for nom in predits}
        encore = True
        while encore:
            encore = False
            for nom in predits:
                cands = par_nom[nom]
                for _ in range(stride[nom]):
                    if pos[nom] < len(cands):
                        encore = True
                        code = cands[pos[nom]]
                        pos[nom] += 1
                        appels += 1
                        if gagne(code):
                            return nom, code, appels
    n, c, a2 = _rr(par_nom, reste, gagne, 1)
    return n, c, appels + a2


PRESOLVE_ETAGES = 5   # nb d'étages canoniques de tête balayés en profondeur 1 avant tout routage


def st_presolve(par_nom, predits, reste, gagne, votes=None):
    """PRESOLVE cheap-first (SATzilla) : phase 0 = le 1ᵉʳ candidat de chacun des PRESOLVE_ETAGES étages
    canoniques de tête (attrape les tâches TRIVIALES en ≤5 appels, même quand la prédiction se trompe vers un
    étage profond) ; puis rr2 prédits→reste en SAUTANT les candidats déjà testés (cache `seen`, zéro re-test).
    L'ordre canonique de tête = les étages les moins chers de l'escalade (dict `par_nom` = ordre d'insertion)."""
    seen = set()
    appels = 0
    for nom in list(par_nom)[:PRESOLVE_ETAGES]:            # phase 0 : profondeur 1, étages de tête
        cands = par_nom[nom]
        if cands:
            code = cands[0]
            seen.add(code)
            appels += 1
            if gagne(code):
                return nom, code, appels

    def _rr_seen(noms):
        nonlocal appels
        i, encore = 0, True
        while encore:
            encore = False
            for nom in noms:
                cands = par_nom[nom]
                if i < len(cands):
                    encore = True
                    code = cands[i]
                    if code in seen:
                        continue
                    seen.add(code)
                    appels += 1
                    if gagne(code):
                        return nom, code
            i += 1
        return None, None

    nom, code = _rr_seen(predits)
    if code is None:
        nom, code = _rr_seen(reste)
    return nom, code, appels


STRATEGIES = {"rr2": st_rr2, "costw": st_costw, "rr_occam": st_rr_occam, "costw_occam": st_costw_occam,
              "smith": st_smith, "sunny": st_sunny, "presolve": st_presolve}
DEFAUT = "rr2"   # défaut SÛR à froid (near-oracle global, jamais catastrophique)


def _ctx(orchestre, tache, routeur_zone, k):
    """(par_nom, predits, reste) — identique à routeur.resoudre_route_rr2 (ordre canonique, prédits confiants).

    TRI PAR TYPE DE SORTIE sur les étages PRÉDITS (2026-06-22, cf. typage.py) : le solveur du bon type remonte ->
    jugé tôt -> compteur d'appels plus bas. SOUND (réordonnancement intra-étage, rien retiré -> couverture intacte ;
    étage gagnant inchangé -> épinglages intacts). Restreint aux PRÉDITS : ne perturbe pas le round-robin du reste
    (un tri GLOBAL gonflait les tâches int, type majoritaire ; cf. mesure 2026-06-22)."""
    etages = orchestre.etages(tache.prompt, k)
    par_nom = {nom: cands for nom, cands in etages}
    predits = [e for e in routeur_zone.predit(tache) if e in par_nom]
    reste = [nom for nom, _ in etages if nom not in predits]
    if predits:
        att = type_attendu(cle_tache(tache)[2])
        if att:
            for n in predits:
                par_nom[n] = reordonne_par_type(par_nom[n], att)
    return par_nom, predits, reste


def _faire_gagne(tache, limites):
    def gagne(code):
        if not juge(code, tache.tests, limites).passe:
            return False
        if tache.tests_held_out and not juge(code, tache.tests_held_out, limites).passe:
            return False
        return True
    return gagne


class RouteurStrategie:
    """Carte apprise clé -> coût moyen par stratégie. predit() rend la moins chère VUE pour la clé, sinon DEFAUT (rr2).

    SÛR : comme toutes les stratégies ont la MÊME couverture, un mauvais routage ne coûte que des appels, jamais un faux.
    À froid (clé jamais vue) -> DEFAUT -> comportement == rr2 actuel (zéro régression). Le gain se réveille quand une
    clé se réchauffe (l'IA s'améliore à l'usage), exactement comme le RouteurZone des étages."""

    def __init__(self):
        self._stats: dict[tuple, dict[str, list]] = {}   # cle -> {strat: [somme_cout, n]}

    def apprendre(self, tache, strategie: str, cout: int) -> None:
        if strategie not in STRATEGIES:
            return
        c = cle_tache(tache)
        d = self._stats.setdefault(c, {})
        s = d.setdefault(strategie, [0, 0])
        s[0] += cout
        s[1] += 1

    def predit(self, tache) -> str:
        d = self._stats.get(cle_tache(tache))
        if not d:
            return DEFAUT
        return min(d, key=lambda s: d[s][0] / d[s][1])      # stratégie de coût moyen minimal

    def etat(self) -> dict:
        return {c: {s: round(v[0] / v[1], 1) for s, v in d.items()} for c, d in self._stats.items()}


def resoudre_route_strategie(orchestre, tache, routeur_zone, routeur_strat: RouteurStrategie, limites=None,
                             k: int = 400, prefiltre: bool = True):
    """Comme resoudre_route_rr2 mais la STRATÉGIE de traversée est choisie par clé (routeur_strat.predit). À froid ->
    rr2 (DEFAUT). Renvoie (etage, appels, code, verdict) ; couverture identique à rr2 quelle que soit la stratégie.

    `prefiltre=True` (défaut) : chaque candidat est testé EN-PROCESS d'abord (quasi-gratuit) et n'atteint le sous-process
    juge que s'il est prometteur/incertain -> mesuré −96 % de sous-process sandbox sur 59 familles, couverture IDENTIQUE
    (le juge reste l'arbitre final). `appels` = nb de candidats testés (inchangé par le pré-filtre) ; le gain est sur
    le coût RÉEL (sous-process + temps mur). prefiltre=False = ancien comportement (sandbox à chaque candidat)."""
    par_nom, predits, reste = _ctx(orchestre, tache, routeur_zone, k)
    gagne = faire_gagne_prefiltre(tache, limites) if prefiltre else _faire_gagne(tache, limites)
    strat = routeur_strat.predit(tache)
    votes = routeur_zone.votes_confiants(tache)
    nom, code, appels = STRATEGIES[strat](par_nom, predits, reste, gagne, votes=votes)
    if code is None:
        return None, appels, None, None
    return nom, appels, code, juge(code, tache.tests, limites)


# --- SWITCH ADAPTATIF (idée Yohan 2026-06-19, « basculer de routage selon les appels, comme le cerveau ») ---
# Chaque stratégie expose son ORDRE de candidats (liste à plat) ; un cache de verdicts par tâche (l'ensemble `seen`)
# garantit qu'aucun candidat n'est re-testé en basculant -> le switch ne paie QUE les candidats neufs. SOUND.

def _ordre_rr(par_nom, noms, stride=1):
    out, i, encore = [], 0, True
    while encore:
        encore = False
        for nom in noms:
            cands = par_nom[nom]
            for s in range(stride):
                idx = i + s
                if idx < len(cands):
                    encore = True
                    out.append((nom, cands[idx]))
        i += stride
    return out


def ordre_rr2(par_nom, predits, reste):
    return _ordre_rr(par_nom, predits) + _ordre_rr(par_nom, reste)


def ordre_costw(par_nom, predits, reste):
    p = sorted(predits, key=lambda nom: len(par_nom[nom]))
    rs = sorted(reste, key=lambda nom: len(par_nom[nom]))
    return _ordre_rr(par_nom, p) + _ordre_rr(par_nom, rs)


def ordre_rr_occam(par_nom, predits, reste):
    pn = _trier_intra(par_nom)
    return _ordre_rr(pn, predits) + _ordre_rr(pn, reste)


def ordre_costw_occam(par_nom, predits, reste):
    pn = _trier_intra(par_nom)
    p = sorted(predits, key=lambda nom: len(pn[nom]))
    rs = sorted(reste, key=lambda nom: len(pn[nom]))
    return _ordre_rr(pn, p) + _ordre_rr(pn, rs)


ORDRES = {"rr2": ordre_rr2, "costw": ordre_costw, "rr_occam": ordre_rr_occam, "costw_occam": ordre_costw_occam}


def resoudre_switch(par_nom, predits, reste, gagne, plan):
    """SWITCH ADAPTATIF : `plan` = [(stratégie, budget|None), …]. On suit l'ordre de la 1ʳᵉ stratégie pour `budget`
    candidats NEUFS ; si non résolu on bascule sur la suivante en SAUTANT les candidats déjà testés (cache `seen`)
    -> zéro re-test. budget=None = jusqu'à épuisement. La dernière phase devrait épuiser un ordre complet pour
    GARANTIR LA COUVERTURE (un ordre couvre tous les candidats). Renvoie (nom_étage, code, appels)."""
    seen = set()
    appels = 0
    for strat, budget in plan:
        ordre = ORDRES[strat](par_nom, predits, reste)
        spent = 0
        for nom, code in ordre:
            if code in seen:
                continue
            seen.add(code)
            appels += 1
            spent += 1
            if gagne(code):
                return nom, code, appels
            if budget is not None and spent >= budget:
                break
    return None, None, appels


def apprendre_toutes(orchestre, tache, routeur_zone, routeur_strat: RouteurStrategie, limites=None, k: int = 400):
    """WARM-UP AMORTI (one-shot, hors chemin chaud) : exécute TOUTES les stratégies sur `tache`, enregistre le coût de
    chacune pour la clé -> le routeur saura ensuite router toute tâche de même clé vers la moins chère. Renvoie les coûts
    {strat: appels}. Sound : ne change RIEN au résultat (mesure pure de coût). À utiliser sur une batterie d'amorçage,
    PAS sur chaque demande de production (là, l'apprentissage se fait par l'usage via apprendre())."""
    par_nom, predits, reste = _ctx(orchestre, tache, routeur_zone, k)
    gagne = _faire_gagne(tache, limites)
    votes = routeur_zone.votes_confiants(tache)
    couts = {}
    for nom_s, fn in STRATEGIES.items():
        _, code, appels = fn(par_nom, predits, reste, gagne, votes=votes)
        couts[nom_s] = appels
        if code is not None:
            routeur_strat.apprendre(tache, nom_s, appels)
    return couts
