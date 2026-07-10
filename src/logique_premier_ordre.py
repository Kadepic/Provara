"""
LOGIQUE DU PREMIER ORDRE — conséquence sur DOMAINE FINI (fragment DÉCIDABLE, model checking exhaustif).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est la sémantique de TARSKI sur structures FINIES :
      – `satisfait` évalue récursivement une formule dans UNE structure donnée (M, affectation ⊨ φ) ;
        sur un domaine fini, cette évaluation est EXACTE et TERMINANTE (les quantificateurs deviennent
        des conjonctions/disjonctions finies) — c'est le fragment décidable exploité ici.
      – `consequence` teste l'implication DANS CE MODÈLE uniquement : M ⊨ prémisses ⇒ M ⊨ conclusion.
      – `cherche_contre_modele` énumère EXHAUSTIVEMENT toutes les structures de domaine de taille 1..N
        (toutes les extensions possibles de chaque prédicat) et cherche un modèle des prémisses qui
        réfute la conclusion.
  • HONNÊTETÉ CAPITALE : la logique du premier ordre est INDÉCIDABLE en général (Church–Turing 1936).
    L'absence de contre-modèle jusqu'à la taille N ne prouve PAS la validité ; le résultat dit donc
    « non réfuté jusqu'à N » et JAMAIS « valide ». Seul un contre-modèle TROUVÉ est une preuve
    (preuve de NON-conséquence, exhibée explicitement).

Formules = tuples imbriqués :
    ('pred', nom, args)        atome — args : variables (str, liées ou affectées) ou éléments du domaine
    ('non', f)                 négation
    ('et', f, g) | ('ou', f, g) | ('implique', f, g)
    ('tous', var, f) | ('existe', var, f)
Structure = {'domaine': tuple non vide, 'predicats': {nom: set de tuples d'éléments du domaine}}.
Un atome absent de l'extension est FAUX dans CE modèle (sémantique de Tarski, pas une devinette).

GARANTIES (vérifiées en adverse par `valide_logique_premier_ordre.py`) :
  - domaine vide -> ValueError (la sémantique du premier ordre exige un domaine non vide) ;
  - prédicat inconnu de la structure -> ValueError ;
  - variable libre non affectée (ou argument hors domaine) -> ValueError ;
  - arité incohérente (entre extension et usage, entre deux usages, ou dans l'extension) -> ValueError ;
  - ambiguïté nom de variable / élément du domaine -> ValueError (jamais une résolution silencieuse) ;
  - types invalides (bool partout où un bool n'est pas une valeur de vérité D'ENTRÉE, str à la place
    d'un entier, formule mal formée, opérateur inconnu, mauvaise arité de tuple) -> ValueError ;
  - recherche de contre-modèle : taille_max hors 1..6 -> ValueError ; espace > 2^20 interprétations
    pour une taille de domaine -> ValueError (abstention : on refuse de rendre un « non réfuté »
    qu'on n'aurait pas réellement vérifié) ;
  - le dict retourné par cherche_contre_modele dit « non réfuté jusqu'à N », jamais « valide » ;
  - fonctions pures et déterministes ; énumération en ordre fixe (contre-modèle reproductible).

Le module n'importe que `itertools` (stdlib). Aucun flottant : tout est exact (booléens, ensembles finis).
"""
from __future__ import annotations

import itertools

SOURCE = ("sémantique de Tarski (1933) sur structures finies : le model checking du premier ordre sur "
          "domaine fini est décidable et exact ; le cas général est indécidable (Church-Turing 1936), "
          "d'où l'abstention structurelle : « non réfuté jusqu'à N » n'est JAMAIS présenté comme « valide »")

_OPERATEURS_BINAIRES = ('et', 'ou', 'implique')
_QUANTIFICATEURS = ('tous', 'existe')
_NOMS_ELEMENTS = ('a', 'b', 'c', 'd', 'e', 'f')   # éléments des domaines énumérés (ordre fixe)
_TAILLE_MAX_ABSOLUE = 6                            # au-delà, l'énumération n'est plus raisonnable
_BUDGET_EXPOSANT = 20                              # ≤ 2^20 interprétations par taille de domaine


# ── VALIDATION DE LA STRUCTURE ─────────────────────────────────────────────────────────────────────────────────
def _valide_structure(structure):
    """Valide {'domaine': tuple, 'predicats': dict} ; renvoie (domaine, predicats, arites).

    arites[nom] = arité déduite de l'extension, ou None si l'extension est vide (arité alors fixée
    par le premier usage dans la formule, et exigée cohérente ensuite)."""
    if not isinstance(structure, dict) or set(structure.keys()) != {'domaine', 'predicats'}:
        raise ValueError("structure invalide : dict {'domaine': tuple, 'predicats': dict} exactement requis")
    domaine = structure['domaine']
    if not isinstance(domaine, tuple):
        raise ValueError("domaine invalide : un tuple est requis")
    if len(domaine) == 0:
        raise ValueError("domaine vide : la sémantique du premier ordre exige un domaine NON VIDE")
    for e in domaine:
        if isinstance(e, bool):
            raise ValueError("domaine invalide : bool refusé comme élément (True n'est pas 1)")
        try:
            hash(e)
        except TypeError:
            raise ValueError("domaine invalide : éléments hashables requis")
    if len(set(domaine)) != len(domaine):
        raise ValueError("domaine invalide : éléments dupliqués")
    predicats = structure['predicats']
    if not isinstance(predicats, dict):
        raise ValueError("predicats invalide : un dict {nom: set de tuples} est requis")
    arites = {}
    for nom, extension in predicats.items():
        if not isinstance(nom, str) or not nom:
            raise ValueError("nom de prédicat invalide : str non vide requis")
        if not isinstance(extension, (set, frozenset)):
            raise ValueError(f"extension de {nom!r} invalide : un set/frozenset de tuples est requis")
        arite = None
        for t in extension:
            if not isinstance(t, tuple):
                raise ValueError(f"extension de {nom!r} invalide : chaque élément doit être un tuple")
            if arite is None:
                arite = len(t)
            elif len(t) != arite:
                raise ValueError(f"arité incohérente dans l'extension du prédicat {nom!r}")
            for e in t:
                if isinstance(e, bool) or e not in domaine:
                    raise ValueError(f"extension de {nom!r} : élément hors du domaine")
        arites[nom] = arite
    return domaine, predicats, arites


# ── VALIDATION DES FORMULES (statique, AVANT évaluation : rien n'échappe au court-circuit) ─────────────────────
def _valide_formule(formule, bornees, domaine, predicats, arites):
    """Valide la formule contre la structure. `bornees` = variables liées par un quantificateur englobant
    OU affectées ; `arites` (mutable) impose la cohérence d'arité à travers TOUTE la formule."""
    if not isinstance(formule, tuple) or len(formule) == 0 or not isinstance(formule[0], str):
        raise ValueError("formule invalide : un tuple ('op', ...) est requis")
    op = formule[0]
    if op == 'pred':
        if len(formule) != 3:
            raise ValueError("atome invalide : ('pred', nom, args) — exactement 3 composants")
        nom, args = formule[1], formule[2]
        if not isinstance(nom, str) or nom not in predicats:
            raise ValueError(f"prédicat inconnu de la structure : {nom!r}")
        if not isinstance(args, tuple):
            raise ValueError(f"arguments de {nom!r} invalides : un tuple est requis")
        if arites.get(nom) is None:
            arites[nom] = len(args)
        elif arites[nom] != len(args):
            raise ValueError(f"arité incohérente pour {nom!r} : {len(args)} vs {arites[nom]}")
        for a in args:
            if isinstance(a, bool):
                raise ValueError("argument bool refusé (True n'est pas un élément du domaine)")
            est_variable = isinstance(a, str) and a in bornees
            est_element = a in domaine
            if est_variable and est_element:
                raise ValueError(f"ambiguïté : {a!r} est à la fois une variable et un élément du domaine")
            if not est_variable and not est_element:
                raise ValueError(f"variable libre non affectée (ou constante hors domaine) : {a!r}")
        return
    if op == 'non':
        if len(formule) != 2:
            raise ValueError("négation invalide : ('non', f) — exactement 2 composants")
        _valide_formule(formule[1], bornees, domaine, predicats, arites)
        return
    if op in _OPERATEURS_BINAIRES:
        if len(formule) != 3:
            raise ValueError(f"connecteur {op!r} invalide : ({op!r}, f, g) — exactement 3 composants")
        _valide_formule(formule[1], bornees, domaine, predicats, arites)
        _valide_formule(formule[2], bornees, domaine, predicats, arites)
        return
    if op in _QUANTIFICATEURS:
        if len(formule) != 3:
            raise ValueError(f"quantificateur {op!r} invalide : ({op!r}, var, f) — exactement 3 composants")
        var = formule[1]
        if not isinstance(var, str) or not var:
            raise ValueError("variable de quantificateur invalide : str non vide requis")
        if var in domaine:
            raise ValueError(f"ambiguïté : la variable {var!r} est aussi un élément du domaine")
        _valide_formule(formule[2], bornees | {var}, domaine, predicats, arites)
        return
    raise ValueError(f"opérateur inconnu : {op!r} (attendu : pred/non/et/ou/implique/tous/existe)")


# ── ÉVALUATION (sémantique de Tarski — exacte et terminante sur domaine fini) ──────────────────────────────────
def _eval(domaine, predicats, formule, env):
    """Évalue une formule DÉJÀ VALIDÉE. env : variable -> élément du domaine."""
    op = formule[0]
    if op == 'pred':
        nom, args = formule[1], formule[2]
        valeurs = tuple(env[a] if (isinstance(a, str) and a in env) else a for a in args)
        return valeurs in predicats[nom]
    if op == 'non':
        return not _eval(domaine, predicats, formule[1], env)
    if op == 'et':
        return _eval(domaine, predicats, formule[1], env) and _eval(domaine, predicats, formule[2], env)
    if op == 'ou':
        return _eval(domaine, predicats, formule[1], env) or _eval(domaine, predicats, formule[2], env)
    if op == 'implique':
        return (not _eval(domaine, predicats, formule[1], env)) or _eval(domaine, predicats, formule[2], env)
    var, corps = formule[1], formule[2]
    if op == 'tous':
        for element in domaine:
            env_local = dict(env)
            env_local[var] = element
            if not _eval(domaine, predicats, corps, env_local):
                return False
        return True
    # op == 'existe' (garanti par la validation)
    for element in domaine:
        env_local = dict(env)
        env_local[var] = element
        if _eval(domaine, predicats, corps, env_local):
            return True
    return False


# ── API : SATISFACTION DANS UNE STRUCTURE ──────────────────────────────────────────────────────────────────────
def satisfait(structure, formule, affectation=None) -> bool:
    """M, affectation ⊨ formule ? — évaluation EXACTE dans CETTE structure finie.

    affectation : dict variable(str) -> élément du domaine (None = vide ; les formules closes n'en ont
    pas besoin). Variable libre non affectée / prédicat inconnu / domaine vide / arité incohérente /
    ambiguïté variable-élément -> ValueError."""
    domaine, predicats, arites = _valide_structure(structure)
    if affectation is None:
        affectation = {}
    if not isinstance(affectation, dict):
        raise ValueError("affectation invalide : un dict {variable: élément du domaine} est requis")
    for cle, valeur in affectation.items():
        if not isinstance(cle, str) or not cle:
            raise ValueError("affectation invalide : les variables sont des str non vides")
        if cle in domaine:
            raise ValueError(f"ambiguïté : la variable affectée {cle!r} est aussi un élément du domaine")
        if isinstance(valeur, bool) or valeur not in domaine:
            raise ValueError(f"affectation invalide : {cle!r} -> valeur hors du domaine")
    arites_locales = dict(arites)
    _valide_formule(formule, frozenset(affectation), domaine, predicats, arites_locales)
    return bool(_eval(domaine, predicats, formule, dict(affectation)))


# ── API : CONSÉQUENCE DANS UN MODÈLE DONNÉ ─────────────────────────────────────────────────────────────────────
def consequence(structure, premisses, conclusion) -> bool:
    """Conséquence DANS CE MODÈLE uniquement : (M ⊨ chaque prémisse) ⇒ (M ⊨ conclusion).

    Vrai si une prémisse est fausse dans M (implication vacuement vraie) ou si la conclusion y est
    vraie ; faux ssi toutes les prémisses sont vraies dans M et la conclusion fausse. Ce N'EST PAS la
    validité logique (⊨ universel) : voir cherche_contre_modele pour la réfutation multi-modèles.
    Les formules doivent être closes (variable libre -> ValueError)."""
    domaine, predicats, arites = _valide_structure(structure)
    if not isinstance(premisses, (list, tuple)):
        raise ValueError("premisses invalide : une liste/tuple de formules est requise")
    arites_locales = dict(arites)
    for p in premisses:
        _valide_formule(p, frozenset(), domaine, predicats, arites_locales)
    _valide_formule(conclusion, frozenset(), domaine, predicats, arites_locales)
    for p in premisses:
        if not _eval(domaine, predicats, p, {}):
            return True   # prémisse fausse dans M : implication vacuement vraie DANS CE MODÈLE
    return bool(_eval(domaine, predicats, conclusion, {}))


# ── COLLECTE DES PRÉDICATS (formules closes, variables liées uniquement) ───────────────────────────────────────
def _collecte_predicats(formule, bornees, arites):
    """Pour cherche_contre_modele : formule CLOSE dont tous les arguments sont des variables LIÉES
    (aucune constante : le domaine n'existe pas encore). Remplit arites[nom] et impose la cohérence."""
    if not isinstance(formule, tuple) or len(formule) == 0 or not isinstance(formule[0], str):
        raise ValueError("formule invalide : un tuple ('op', ...) est requis")
    op = formule[0]
    if op == 'pred':
        if len(formule) != 3:
            raise ValueError("atome invalide : ('pred', nom, args) — exactement 3 composants")
        nom, args = formule[1], formule[2]
        if not isinstance(nom, str) or not nom:
            raise ValueError("nom de prédicat invalide : str non vide requis")
        if not isinstance(args, tuple):
            raise ValueError(f"arguments de {nom!r} invalides : un tuple est requis")
        if nom in arites and arites[nom] != len(args):
            raise ValueError(f"arité incohérente pour {nom!r} : {len(args)} vs {arites[nom]}")
        arites[nom] = len(args)
        for a in args:
            if not isinstance(a, str) or a not in bornees:
                raise ValueError(f"variable libre non affectée (formule non close) : {a!r}")
        return
    if op == 'non':
        if len(formule) != 2:
            raise ValueError("négation invalide : ('non', f) — exactement 2 composants")
        _collecte_predicats(formule[1], bornees, arites)
        return
    if op in _OPERATEURS_BINAIRES:
        if len(formule) != 3:
            raise ValueError(f"connecteur {op!r} invalide : ({op!r}, f, g) — exactement 3 composants")
        _collecte_predicats(formule[1], bornees, arites)
        _collecte_predicats(formule[2], bornees, arites)
        return
    if op in _QUANTIFICATEURS:
        if len(formule) != 3:
            raise ValueError(f"quantificateur {op!r} invalide : ({op!r}, var, f) — exactement 3 composants")
        var = formule[1]
        if not isinstance(var, str) or not var:
            raise ValueError("variable de quantificateur invalide : str non vide requis")
        _collecte_predicats(formule[2], bornees | {var}, arites)
        return
    raise ValueError(f"opérateur inconnu : {op!r} (attendu : pred/non/et/ou/implique/tous/existe)")


# ── API : RECHERCHE EXHAUSTIVE DE CONTRE-MODÈLE ────────────────────────────────────────────────────────────────
def cherche_contre_modele(premisses, conclusion, taille_max) -> dict:
    """Énumère TOUTES les structures de domaine de taille 1..taille_max (toutes les extensions possibles
    de chaque prédicat, ordre fixe) et cherche M ⊨ prémisses avec M ⊭ conclusion.

    Renvoie {'refute': bool, 'contre_modele': structure|None, 'portee': 'domaines de taille <= N',
             'statut': ...}.
    HONNÊTETÉ : refute=False signifie « non réfuté jusqu'à N », JAMAIS « valide » (la logique du premier
    ordre est indécidable en général — Church-Turing 1936). Seul refute=True est une preuve (de
    non-conséquence), le contre-modèle explicite étant exhibé.
    Abstentions : taille_max hors 1..6 -> ValueError ; formules non closes -> ValueError ; espace de
    recherche > 2^20 interprétations pour une taille -> ValueError (on refuse un « non réfuté » non
    réellement vérifié)."""
    if isinstance(taille_max, bool) or not isinstance(taille_max, int):
        raise ValueError("taille_max invalide : un entier (non bool) est requis")
    if not (1 <= taille_max <= _TAILLE_MAX_ABSOLUE):
        raise ValueError(f"taille_max hors domaine : entier dans 1..{_TAILLE_MAX_ABSOLUE} requis")
    if not isinstance(premisses, (list, tuple)):
        raise ValueError("premisses invalide : une liste/tuple de formules est requise")
    arites = {}
    for p in premisses:
        _collecte_predicats(p, frozenset(), arites)
    _collecte_predicats(conclusion, frozenset(), arites)
    for n in range(1, taille_max + 1):
        exposant = sum(n ** r for r in arites.values())
        if exposant > _BUDGET_EXPOSANT:
            raise ValueError(
                f"recherche trop coûteuse (2^{exposant} interprétations pour un domaine de taille {n}, "
                f"budget 2^{_BUDGET_EXPOSANT}) : abstention — réduire taille_max ou les arités")
    portee = f"domaines de taille <= {taille_max}"
    noms = sorted(arites)
    for n in range(1, taille_max + 1):
        domaine = _NOMS_ELEMENTS[:n]
        tuples_par_pred = [tuple(itertools.product(domaine, repeat=arites[nom])) for nom in noms]
        for masques in itertools.product(*(range(1 << len(tp)) for tp in tuples_par_pred)):
            predicats = {}
            for nom, tp, masque in zip(noms, tuples_par_pred, masques):
                predicats[nom] = {tp[i] for i in range(len(tp)) if (masque >> i) & 1}
            if all(_eval(domaine, predicats, p, {}) for p in premisses) \
                    and not _eval(domaine, predicats, conclusion, {}):
                return {'refute': True,
                        'contre_modele': {'domaine': domaine, 'predicats': predicats},
                        'portee': portee,
                        'statut': f"réfuté : contre-modèle explicite de taille {n}"}
    return {'refute': False,
            'contre_modele': None,
            'portee': portee,
            'statut': (f"non réfuté sur les {portee} — ceci N'EST PAS une preuve de validité "
                       f"(le premier ordre est indécidable en général)")}
