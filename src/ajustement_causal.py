"""
AJUSTEMENT CAUSAL — ESTIMER l'effet causal depuis l'OBSERVATIONNEL, sous un DAG donné (PARTIE I, B-NEC).

POURQUOI (honnêteté capitale) : depuis des données observationnelles SEULES, l'effet causal N'EST PAS
identifiable. « Corrélation ≠ causalité » n'est pas un slogan mais un théorème : sans hypothèse structurelle
(un DAG), l'association mesurée peut être n'importe quel mélange d'effet direct, de confusion et de biais de
sélection. Ce module refuse donc de rendre un « effet » tant que le DAG ne PROUVE pas, via le CRITÈRE DE PORTE
DÉROBÉE de Pearl, que l'ensemble d'ajustement Z neutralise toute la confusion. Sinon -> abstention (ValueError).

RÉPARTITION DES RÔLES (ne PAS dupliquer, IMPORTER) :
  • `causalite.GrapheCausal` porte le DAG, le do-opérateur et les chemins (descendants/ancêtres). Non modifié.
  • `simpson` DÉTECTE le renversement d'une tendance agrégée vs stratifiée. Non modifié.
  • ICI : l'ESTIMATION quantitative EXACTE (aucun des deux autres ne l'estime).

MÉCANISME EXACT (théorèmes, pas corrélations) :
  • CRITÈRE DE PORTE DÉROBÉE (Pearl 1993/2009). Z est admissible pour (X→Y) ssi :
      (i)  aucun nœud de Z n'est un descendant de X (pas de collider/médiateur) ; ET
      (ii) Z bloque (d-séparation) tout chemin de porte dérobée X⇠Y, c.-à-d. tout chemin dont la PREMIÈRE
           arête entre DANS X.
    d-SÉPARATION exacte : un chemin est bloqué par Z ssi il possède (a) un nœud non-collider (chaîne
    i→m→j ou fourche i←m→j) avec m∈Z, ou (b) un collider i→m←j tel que ni m ni aucun descendant de m n'est
    dans Z. Le chemin est OUVERT (non bloqué) sinon ; Z d-sépare ssi TOUS les chemins concernés sont bloqués.
  • FORMULE D'AJUSTEMENT (back-door adjustment) :
        P(Y=y | do(X=x)) = Σ_z  P(Y=y | X=x, Z=z) · P(Z=z),
    calculée EXACTEMENT en `fractions.Fraction` depuis une table de contingence (comptes ENTIERS).
  • EFFET MOYEN : ATE = E[Y | do(X=1)] − E[Y | do(X=0)] (Y numérique entier), exact en Fraction.

GARANTIES (vérifiées en adverse par `valide_ajustement_causal.py`) :
  - DAG cyclique -> ValueError (identification impossible) ;
  - Z contenant un DESCENDANT de X (collider/médiateur) -> ValueError EXPLICITE (biais de sur-ajustement) ;
  - Z ne bloquant pas toutes les portes dérobées -> ValueError « l'association mesurée n'est pas l'effet causal » ;
  - strate d'effectif nul (P(X=x,Z=z)=0) -> ValueError (aucune extrapolation) ;
  - types invalides (bool refusé — True n'est pas 1 ; float refusé là où l'exactitude est requise ; str/NaN ;
    mauvaise arité ; |V|>10 pour l'énumération exhaustive) -> ValueError ;
  - déterministe, pur (stdlib : fractions) ; conservateur : faux négatif toléré, faux POSITIF INTERDIT.
"""
from __future__ import annotations

from fractions import Fraction

import causalite
import simpson

SOURCE = ("critère de porte dérobée + formule d'ajustement (Pearl, «Causality» 2009, ch. 3) ; "
          "cas d'école des calculs rénaux (Charig et al., BMJ 1986)")


# ── helpers : DAG (via causalite, sans le modifier) ──────────────────────────────────────────────────────────────
def _noeuds(dag) -> set:
    """Ensemble des nœuds du DAG. Lit les tables (non mutées). Objet non conforme -> ValueError."""
    try:
        noeuds = set()
        for c, es in dag._effets.items():
            noeuds.add(c)
            noeuds.update(es)
        for e, cs in dag._causes.items():
            noeuds.add(e)
            noeuds.update(cs)
        return noeuds
    except AttributeError:
        raise ValueError("dag invalide : un GrapheCausal (causalite) est attendu")


def _verifie_dag(dag) -> None:
    """Refuse tout objet non-DAG et tout DAG CYCLIQUE (identification impossible)."""
    for m in ("effets_directs", "causes_directes", "descendants"):
        if not callable(getattr(dag, m, None)):
            raise ValueError("dag invalide : un GrapheCausal (causalite) est attendu")
    for n in _noeuds(dag):
        if n in dag.descendants(n):
            raise ValueError("DAG cyclique : l'effet causal n'est pas identifiable")


def _arete(dag, a, b) -> bool:
    """True ssi l'arête ORIENTÉE a→b existe."""
    return b in dag.effets_directs(a)


def _voisins(dag, n) -> set:
    """Voisins dans le squelette NON orienté (causes ∪ effets directs)."""
    return set(dag.effets_directs(n)) | set(dag.causes_directes(n))


def _chemins_simples(dag, source, cible) -> list:
    """Tous les chemins SIMPLES source⇢cible dans le squelette non orienté (déterministe, trié)."""
    chemins: list = []

    def dfs(n, chemin, vus):
        if n == cible:
            chemins.append(list(chemin))
            return
        for w in sorted(_voisins(dag, n), key=repr):
            if w not in vus:
                vus.add(w)
                chemin.append(w)
                dfs(w, chemin, vus)
                chemin.pop()
                vus.discard(w)

    if source == cible:
        return []
    dfs(source, [source], {source})
    return chemins


def _chemin_bloque(dag, chemin, Z) -> bool:
    """d-séparation d'UN chemin par Z (règles chaîne/fourche/collider exactes)."""
    for i in range(1, len(chemin) - 1):
        prev, m, nxt = chemin[i - 1], chemin[i], chemin[i + 1]
        collider = _arete(dag, prev, m) and _arete(dag, nxt, m)   # prev→m ET nxt→m
        if collider:
            # collider FERMÉ (bloque) ssi ni m ni un descendant de m n'est conditionné
            if not (m in Z or (dag.descendants(m) & Z)):
                return True
        else:
            # chaîne/fourche : bloqué ssi le nœud médiateur est conditionné
            if m in Z:
                return True
    return False


# ── helpers : entrées ────────────────────────────────────────────────────────────────────────────────────────────
def _normalise_Z(ensemble_Z) -> frozenset:
    if isinstance(ensemble_Z, str):
        raise ValueError("ensemble_Z : une chaîne n'est pas un ensemble de variables")
    if not isinstance(ensemble_Z, (set, frozenset, list, tuple)):
        raise ValueError("ensemble_Z : set/frozenset/list/tuple de noms de variables attendu")
    for v in ensemble_Z:
        if isinstance(v, bool):
            raise ValueError("ensemble_Z : nom de variable booléen refusé")
    return frozenset(ensemble_Z)


def _valeur_licite(v) -> None:
    """Valeur de donnée : bool REFUSÉ (True n'est pas 1), float REFUSÉ (exactitude), NaN implicite exclu."""
    if isinstance(v, bool):
        raise ValueError("valeur booléenne refusée (True n'est pas 1)")
    if isinstance(v, float):
        raise ValueError("valeur flottante refusée : exactitude requise (Fraction/entier/catégorie)")


def _verifie_donnees(donnees, cles) -> None:
    if not isinstance(donnees, (list, tuple)) or len(donnees) == 0:
        raise ValueError("donnees : liste NON VIDE de lignes (dict) attendue")
    for r in donnees:
        if not isinstance(r, dict):
            raise ValueError("donnees : chaque ligne doit être un dict variable->valeur")
        for c in cles:
            if c not in r:
                raise ValueError(f"variable {c!r} absente d'une ligne de donnees")
            _valeur_licite(r[c])


def _cle_strate(ligne, zvars) -> tuple:
    """Clé de strate = valeurs de Z triées par nom de variable (déterministe)."""
    return tuple(ligne[v] for v in zvars)


# ── (a) CRITÈRE DE PORTE DÉROBÉE ─────────────────────────────────────────────────────────────────────────────────
def critere_backdoor(dag, traitement, resultat, ensemble_Z) -> bool:
    """True ssi Z satisfait le critère de porte dérobée de Pearl pour (traitement→resultat).

    (i) aucun nœud de Z n'est descendant de X ; (ii) Z bloque (d-séparation) toute porte dérobée X⇠Y."""
    _verifie_dag(dag)
    Z = _normalise_Z(ensemble_Z)
    if traitement == resultat:
        raise ValueError("traitement et resultat doivent être distincts")
    noeuds = _noeuds(dag)
    if traitement not in noeuds or resultat not in noeuds:
        raise ValueError("traitement/resultat absents du DAG")
    if not Z <= noeuds:
        raise ValueError("ensemble_Z contient des nœuds hors du DAG")
    if traitement in Z or resultat in Z:
        return False
    # (i) pas de descendant de X dans Z
    if Z & dag.descendants(traitement):
        return False
    # (ii) toute porte dérobée (1re arête entrant DANS X) doit être bloquée par Z
    for chemin in _chemins_simples(dag, traitement, resultat):
        premier_voisin = chemin[1]
        entre_dans_X = _arete(dag, premier_voisin, traitement)   # voisin → X ?
        if not entre_dans_X:
            continue                                             # chemin de porte de devant : ignoré
        if not _chemin_bloque(dag, chemin, Z):
            return False
    return True


# ── (b) ÉNUMÉRATION DES ENSEMBLES D'AJUSTEMENT ───────────────────────────────────────────────────────────────────
def ensembles_ajustement(dag, traitement, resultat) -> list:
    """Tous les Z ⊆ V\\{X,Y,desc(X)} satisfaisant le critère de porte dérobée (recherche exhaustive bornée).

    Renvoie une liste (déterministe, du plus petit au plus grand) de frozenset. |V| > 10 -> ValueError."""
    _verifie_dag(dag)
    if traitement == resultat:
        raise ValueError("traitement et resultat doivent être distincts")
    noeuds = _noeuds(dag)
    if traitement not in noeuds or resultat not in noeuds:
        raise ValueError("traitement/resultat absents du DAG")
    if len(noeuds) > 10:
        raise ValueError("|V| > 10 : énumération exhaustive refusée (borne de sûreté)")
    interdits = {traitement, resultat} | dag.descendants(traitement)
    candidats = sorted((noeuds - interdits), key=repr)
    valides: list = []
    for masque in range(1 << len(candidats)):
        Z = frozenset(candidats[i] for i in range(len(candidats)) if masque & (1 << i))
        if critere_backdoor(dag, traitement, resultat, Z):
            valides.append(Z)
    valides.sort(key=lambda z: (len(z), sorted(map(repr, z))))
    return valides


# ── comptes exacts (table de contingence) ────────────────────────────────────────────────────────────────────────
def _compte(donnees, contraintes) -> int:
    """Nombre de lignes satisfaisant TOUTES les contraintes {variable: valeur}."""
    n = 0
    for r in donnees:
        if all(r[k] == v for k, v in contraintes.items()):
            n += 1
    return n


def _strates_Z(donnees, zvars) -> list:
    """Valeurs de strate distinctes observées, triées (déterministe)."""
    vues = {_cle_strate(r, zvars) for r in donnees}
    return sorted(vues, key=repr)


# ── (c) EFFET CAUSAL PAR PORTE DÉROBÉE : P(Y=y | do(X=x)) ─────────────────────────────────────────────────────────
def effet_causal_backdoor(dag, donnees, traitement, resultat, ensemble_Z,
                          valeur_traitement, valeur_resultat) -> Fraction:
    """P(Y=y | do(X=x)) = Σ_z P(Y=y|X=x,Z=z)·P(Z=z), EXACT en Fraction (table de contingence).

    ABSTENTION : Z non admissible -> ValueError ; strate d'effectif nul -> ValueError."""
    _verifie_dag(dag)
    Z = _normalise_Z(ensemble_Z)
    _valeur_licite(valeur_traitement)
    _valeur_licite(valeur_resultat)
    zvars = sorted(Z, key=repr)
    _verifie_donnees(donnees, [traitement, resultat] + zvars)
    # HONNÊTETÉ : sans admissibilité, l'association N'EST PAS l'effet causal.
    if Z & dag.descendants(traitement):
        raise ValueError("Z contient un descendant du traitement (collider/médiateur) : ajustement invalide")
    if not critere_backdoor(dag, traitement, resultat, Z):
        raise ValueError("Z ne bloque pas toutes les portes dérobées : "
                         "l'association mesurée n'est pas l'effet causal")
    N = len(donnees)
    total = Fraction(0)
    for zval in _strates_Z(donnees, zvars):
        contr_z = dict(zip(zvars, zval))
        n_z = _compte(donnees, contr_z)                                   # #(Z=z)
        contr_xz = dict(contr_z, **{traitement: valeur_traitement})
        n_xz = _compte(donnees, contr_xz)                                 # #(X=x, Z=z)
        if n_xz == 0:
            raise ValueError(f"strate d'effectif nul pour X={valeur_traitement!r}, Z={zval!r} : "
                             "effet non identifiable (aucune extrapolation)")
        n_xyz = _compte(donnees, dict(contr_xz, **{resultat: valeur_resultat}))   # #(X=x,Y=y,Z=z)
        p_y_sachant_xz = Fraction(n_xyz, n_xz)
        p_z = Fraction(n_z, N)
        total += p_y_sachant_xz * p_z
    return total


# ── espérance interventionnelle E[Y | do(X=x)] (Y numérique entier) ──────────────────────────────────────────────
def esperance_do(dag, donnees, traitement, resultat, ensemble_Z, valeur_traitement) -> Fraction:
    """E[Y | do(X=x)] = Σ_z E[Y|X=x,Z=z]·P(Z=z), Y ENTIER, exact en Fraction."""
    _verifie_dag(dag)
    Z = _normalise_Z(ensemble_Z)
    _valeur_licite(valeur_traitement)
    zvars = sorted(Z, key=repr)
    _verifie_donnees(donnees, [traitement, resultat] + zvars)
    for r in donnees:
        y = r[resultat]
        if not isinstance(y, int) or isinstance(y, bool):
            raise ValueError("esperance_do : le résultat Y doit être un entier (espérance numérique)")
    if Z & dag.descendants(traitement):
        raise ValueError("Z contient un descendant du traitement (collider/médiateur) : ajustement invalide")
    if not critere_backdoor(dag, traitement, resultat, Z):
        raise ValueError("Z ne bloque pas toutes les portes dérobées : "
                         "l'association mesurée n'est pas l'effet causal")
    N = len(donnees)
    total = Fraction(0)
    for zval in _strates_Z(donnees, zvars):
        contr_z = dict(zip(zvars, zval))
        n_z = _compte(donnees, contr_z)
        contr_xz = dict(contr_z, **{traitement: valeur_traitement})
        n_xz = _compte(donnees, contr_xz)
        if n_xz == 0:
            raise ValueError(f"strate d'effectif nul pour X={valeur_traitement!r}, Z={zval!r}")
        somme_y = sum(r[resultat] for r in donnees
                      if all(r[k] == v for k, v in contr_xz.items()))
        e_y_xz = Fraction(somme_y, n_xz)
        total += e_y_xz * Fraction(n_z, N)
    return total


# ── (d) EFFET MOYEN DU TRAITEMENT (ATE) ──────────────────────────────────────────────────────────────────────────
def effet_moyen_traitement(dag, donnees, traitement, resultat, ensemble_Z,
                           valeur_traite, valeur_controle) -> Fraction:
    """ATE = E[Y | do(X=traité)] − E[Y | do(X=contrôle)], exact en Fraction."""
    if valeur_traite == valeur_controle:
        raise ValueError("valeur_traite et valeur_controle doivent être distinctes")
    e1 = esperance_do(dag, donnees, traitement, resultat, ensemble_Z, valeur_traite)
    e0 = esperance_do(dag, donnees, traitement, resultat, ensemble_Z, valeur_controle)
    return e1 - e0


# ── (f) SIMPSON + AJUSTEMENT : montre le renversement, puis l'effet CAUSAL (si le DAG le justifie) ────────────────
def simpson_et_ajustement(dag, donnees, traitement, resultat, ensemble_Z,
                          valeur_a, valeur_b, valeur_succes) -> dict:
    """Détecte le renversement de Simpson (via `simpson`) PUIS rend l'effet ajusté, et nomme le CAUSAL.

    Z doit être UNE variable de stratification (le paradoxe de Simpson porte sur un unique confondeur).
    L'effet ajusté n'est déclaré CAUSAL que si le DAG rend Z admissible (sinon effet_causal_backdoor abstient)."""
    _verifie_dag(dag)
    Z = _normalise_Z(ensemble_Z)
    if len(Z) != 1:
        raise ValueError("simpson_et_ajustement : exactement UNE variable de stratification attendue")
    if valeur_a == valeur_b:
        raise ValueError("valeur_a et valeur_b doivent être distinctes")
    _valeur_licite(valeur_succes)
    (zvar,) = tuple(Z)
    _verifie_donnees(donnees, [traitement, resultat, zvar])
    # 1) Table stratifiée pour simpson : {trt: {strate: (succès, total)}}
    strates = sorted({r[zvar] for r in donnees}, key=repr)
    table: dict = {valeur_a: {}, valeur_b: {}}
    for trt in (valeur_a, valeur_b):
        for s in strates:
            total = _compte(donnees, {traitement: trt, zvar: s})
            succ = _compte(donnees, {traitement: trt, zvar: s, resultat: valeur_succes})
            table[trt][s] = (succ, total)
    diag = simpson.analyse(table, valeur_a, valeur_b)
    # 2) Effet ajusté (lève si Z non admissible -> pas de prétention causale)
    adj_a = effet_causal_backdoor(dag, donnees, traitement, resultat, Z, valeur_a, valeur_succes)
    adj_b = effet_causal_backdoor(dag, donnees, traitement, resultat, Z, valeur_b, valeur_succes)
    brut_a = Fraction(_compte(donnees, {traitement: valeur_a, resultat: valeur_succes}),
                      _compte(donnees, {traitement: valeur_a}))
    brut_b = Fraction(_compte(donnees, {traitement: valeur_b, resultat: valeur_succes}),
                      _compte(donnees, {traitement: valeur_b}))
    gagnant_brut = valeur_a if brut_a > brut_b else (valeur_b if brut_b > brut_a else None)
    gagnant_ajuste = valeur_a if adj_a > adj_b else (valeur_b if adj_b > adj_a else None)
    return {
        "simpson": diag[0],                     # simpson.SIMPSON / COHERENT / ABSTENTION
        "renversement": diag[0] == simpson.SIMPSON,
        "brut": {valeur_a: brut_a, valeur_b: brut_b},
        "ajuste": {valeur_a: adj_a, valeur_b: adj_b},
        "gagnant_brut": gagnant_brut,
        "gagnant_ajuste": gagnant_ajuste,
        "causal": gagnant_ajuste,               # ajusté = causal car Z admissible (vérifié par backdoor)
        "message": (f"L'agrégat favorise {gagnant_brut!r}, mais après ajustement sur {zvar!r} "
                    f"(confondeur admissible selon le DAG) l'effet CAUSAL favorise {gagnant_ajuste!r}."),
    }
