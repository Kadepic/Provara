"""
AUTO-APPRENTISSAGE AUTONOME (2026-06-22, phase « l'IA crée ce qui lui manque, jugée par la réalité » — vision Yohan).

Étend le moteur d'auto-invention OUVERTE (auto_invention_ouverte.MoteurOuvert, l'éveil DreamCoder) avec ce que le TEST
AVEUGLE a révélé manquant :
  1) VOCABULAIRE PLUS PROFOND — un COMBINATEUR BINAIRE `op(f(x), g(x))` (op ∈ +,−,*) + l'identité `x`. Cela rend
     inventables des cibles hors de compose/map seuls : `max−min` = combine(−, max, min) ; `cube` = combine(*, x, x*x) ;
     etc. Toujours réalité-jugé (déterministe, total, NOUVEAU comportement, généralise sur held-out).
  2) RÉSOLUTION CONFIANTE / APPRENTISSAGE ACTIF — au lieu de rendre le 1ᵉʳ candidat qui passe (risque de COÏNCIDENCE,
     cf. `min(x)+1` capté pour « 2ᵉ élément »), on RASSEMBLE TOUS les candidats qui passent les exemples, on les
     exécute sur des sondes variées, et :
        - tous d'accord  -> solution CONFIANTE (généralisation robuste, jugée par la réalité) ;
        - désaccord      -> tâche SOUS-DÉTERMINÉE : on renvoie l'entrée DISCRIMINANTE (la « question » la plus
          informative) au lieu de commettre un faux. C'est l'IA qui SAIT qu'elle ne sait pas et demande la bonne
          épreuve à la réalité (active learning) — la voie SÛRE et autonome (pas d'aide humaine ad hoc).

Sûr avant rapide : on n'ACCEPTE que ce que la réalité valide ; un désaccord => abstention informative, jamais un faux.
NB : ne modifie pas MoteurOuvert (sa validation 5/5 reste intacte) — sous-classe additive.
"""
from __future__ import annotations

import itertools

from auto_invention_ouverte import (INT_H, INT_P, LIST_H, LIST_P, MoteurOuvert,
                                    _empreinte, _fn)

# Identité (int->int) en plus des primitives de base : permet cube = x*(x*x), etc.
PRIMITIVES_PLUS = list(MoteurOuvert().atomes) + [("x", "int", "int")]
_OPS = (("+", "{a} + {b}"), ("-", "{a} - {b}"), ("*", "{a} * {b}"))


class MoteurAutonome(MoteurOuvert):
    """MoteurOuvert + combinateur binaire op(f(x),g(x)) + résolution confiante (active learning)."""

    def __init__(self, seed: int = 0):
        super().__init__(primitives=PRIMITIVES_PLUS, seed=seed)

    def _combine(self, f, g):
        """op(f(x), g(x)) pour f,g de MÊME type d'entrée et sortie int -> sortie int. Génère 3 variantes (+,−,*)."""
        ef, tif, tof = f
        eg, tig, tog = g
        if tif != tig or tof != "int" or tog != "int":
            return []
        out = []
        for _, modele in _OPS:
            out.append((f"({modele.format(a=ef, b=eg)})", tif, "int"))
        return out

    def explore_combine(self, budget: int = 3000, cap: int = 6000):
        """Éveil étendu. ORDRE CLÉ : on COMBINE d'abord sur la PETITE base de primitives (génère cube = x*(x*x),
        max−min, etc. à coût borné), PUIS explore_basis propage par compose/map (map(cube), sum∘map(cube)=somme_cubes…).
        Faire l'inverse noyait le budget : combine sur 800 atomes = O(800²), épuisé avant d'atteindre la paire utile."""
        # 1) combinaisons binaires op(f(x),g(x)) sur les PRIMITIVES seulement (base petite -> cube, max−min, …)
        base = [a for a in self.atomes]              # à ce stade = primitives uniquement (graine)
        for f in base:
            for g in base:
                for c in self._combine(f, g):
                    self._ajoute(*c, invente=True)
        # 2) profondeur compose/map sur le répertoire enrichi (propage cube, max−min via map/compose)
        self.explore_basis(budget=budget, cap=cap)
        return self.inventes

    # --- Sondes adverses AUTO-FORGÉES (l'IA fabrique sa réalité de test dure, sans entrées fournies à la main) -------
    @staticmethod
    def sondes_auto(exemples):
        """Dérive des entrées de STRESS depuis la STRUCTURE des exemples : permutations/rotations/décalages qui BRISENT
        les régularités accidentelles (ordre trié, etc.) → font diverger les coïncidences (min+1) du vrai solveur (x[1]).
        Pas de sortie inventée : ce sont seulement des ENTRÉES pour détecter le désaccord entre candidats. Autonome."""
        out = []
        # DOMAINE OBSERVÉ : si TOUTES les entrées entières sont ≥ 0, le domaine-cible est les naturels. Forger une
        # sonde NÉGATIVE (-x) sortirait de ce domaine et créerait une FAUSSE under-détermination (ex. factorielle :
        # math.factorial erreure sur négatif, la version reduce rend 1 → « divergence » hors-domaine alors que les
        # deux réalisations sont IDENTIQUES sur les naturels). On stresse DANS le domaine observé (sound : on ne juge
        # l'unicité que là où les exemples vivent). Si un négatif est déjà présent, le signe compte → on garde -x.
        _ints = [ex[0] for ex in exemples if isinstance(ex[0], int) and not isinstance(ex[0], bool)]
        _signe_compte = any(v < 0 for v in _ints)
        for ex in exemples:
            x = ex[0]                      # exemples = [(entrée, sortie), …] ; l'entrée EST l'argument (tâches mono-arg)
            if isinstance(x, (list, tuple)) and len(x) >= 2:
                xs = list(x)
                k = len(xs) // 2
                # type-safe : les sondes arithmétiques (+1, *2) n'ont de sens que sur des éléments NUMÉRIQUES.
                # Sur une matrice (liste de listes) ou une liste de chaînes, `e + 1` lèverait → on les saute
                # (cf. sonde cross-domaines 2026-06-23). Pour une liste tout-numérique, ensemble et ordre des
                # sondes restent IDENTIQUES à l'historique → zéro régression sur le domaine entiers.
                numerique = all(isinstance(e, (int, float)) and not isinstance(e, bool) for e in xs)
                variantes = [xs[::-1]]
                try:                                   # tri : éléments comparables homogènes seulement
                    variantes += [sorted(xs), sorted(xs, reverse=True)]
                except TypeError:
                    pass
                variantes += [xs[1:] + xs[:1], xs[k:] + xs[:k]]
                if numerique:
                    variantes += [[e + 1 for e in xs], [e * 2 for e in xs]]
                # SONDE EN DOMAINE : on garde le TYPE des exemples (liste), pas un tuple. Sinon une réalisation
                # identité `x` rend un tuple sur une sonde-tuple tandis que `list(x)` rend une liste -> fausse
                # divergence de repr -> fausse AMBIGU (cas liste__identite). Une liste est le bon domaine ici.
                for v in variantes:
                    out.append(list(v))
            elif isinstance(x, str) and len(x) >= 2:
                xs = x
                for v in (xs[::-1], xs.upper(), xs.lower(), xs[1:] + xs[:1], xs + xs, "  " + xs + " "):
                    out.append((v,))
            elif isinstance(x, int):
                out.append((x + 1,)); out.append((x * 2,)); out.append((x + 2,))
                if _signe_compte:
                    out.append((-x,))
        # dédup ordre-préservant ROBUSTE aux entrées non-hashables (sondes matricielles = tuple de listes) :
        # `dict.fromkeys` exigerait des clés hashables. Pour des tuples d'entiers/chaînes -> résultat identique.
        seen, res = set(), []
        for t in out:
            cle = repr(t)
            if cle not in seen:
                seen.add(cle)
                res.append(t)
        return res

    # --- Auto-EXTENSION du vocabulaire sur GAP découvert -------------------------------------------
    # Schémas CHAÎNES (domaine SANS primitives seed dans le moteur ouvert : l'IA les acquiert par schéma sur un gap str).
    _STR = [
        "x[::-1]", "x.upper()", "x.lower()", "x.strip()", "x[1:]", "x[:-1]", "x[0]", "x[-1]",
        "x + x", "''.join(sorted(x))", "''.join(dict.fromkeys(x))", "x.replace(' ', '')",
        "len(x)", "x.count(' ')", "sum(_c.isupper() for _c in x)", "x.title()", "' '.join(x.split()[::-1])",
        "''.join(sorted(x.replace(' ', '')))",                       # anagramme trié (lettres triées, sans espaces)
        "''.join(_w[0] for _w in x.split())",                       # initiales
    ]
    # Schémas de FOLD/réduction (reduce passe le juge en une expr, cf. test 2026-06-22) + conditions/comptages.
    _FOLDS = [
        "__import__('functools').reduce(lambda a, b: a * b, x)",      # produit
        "__import__('functools').reduce(lambda a, b: a if a > b else b, x)",  # max (fold)
        "__import__('functools').reduce(lambda a, b: a if a < b else b, x)",  # min (fold)
        "sum(1 for _e in x if _e > 0)",                              # comptage positifs
        "sum(1 for _e in x if _e % 2 == 0)",                         # comptage pairs
        "sum(_e for _e in x if _e % 2 == 0)",                        # somme des pairs (agrégat FILTRÉ)
        "sum(_e for _e in x if _e % 2 == 1)",                        # somme des impairs
        "sum(_e for _e in x if _e > 0)",                             # somme des positifs
        "all(_e > 0 for _e in x)",                                   # tous positifs
        "any(_e < 0 for _e in x)",                                   # un négatif ?
        "len(x) != len(set(x))",                                     # a des doublons ?
        "len(set(x)) == 1",                                          # tous égaux ?
        # — MONOTONIE (famille générale : l'ordre des voisins) — est trié croissant/décroissant/strict —
        "all(x[_i] <= x[_i + 1] for _i in range(len(x) - 1))",       # trié croissant ?
        "all(x[_i] >= x[_i + 1] for _i in range(len(x) - 1))",       # trié décroissant ?
        "all(x[_i] < x[_i + 1] for _i in range(len(x) - 1))",        # strictement croissant ?
        # — APPARTENANCE / agrégat entier dérivé —
        "0 in x",                                                    # contient zéro ?
        "sum(x) // len(x)",                                          # moyenne entière (quotient)
        "sum(x) % len(x)",                                           # reste de la moyenne
    ]
    # DÉCOUPE en sous-listes : paires glissantes, chunks (relations de voisinage -> liste de listes).
    _DECOUPE = [
        "[[x[_i], x[_i + 1]] for _i in range(len(x) - 1)]",          # paires glissantes
        "[x[_i:_i + 2] for _i in range(0, len(x), 2)]",             # chunks de 2
    ]
    # CONTRÔLE DE FLUX (arrêt anticipé) — itérer JUSQU'À une condition, exprimé fonctionnellement (takewhile/next).
    # La frontière de contrôle, bornée par des conditions NATURELLES (cf. sonde « arret_anticipe »). Sound : ce qui
    # ne reproduit pas le held-out est écarté ; validation contextuelle (lambdas/itertools OK dans le juge).
    _CONTROLE = [
        "sum(__import__('itertools').takewhile(lambda _e: _e >= 0, x))",        # somme jusqu'au 1er négatif
        "sum(__import__('itertools').takewhile(lambda _e: _e > 0, x))",         # somme jusqu'au 1er <= 0
        "list(__import__('itertools').takewhile(lambda _e: _e > 0, x))",        # préfixe positif
        "len(list(__import__('itertools').takewhile(lambda _e: _e > 0, x)))",   # longueur du préfixe positif
        "next((_e for _e in x if _e < 0), 0)",                                  # premier négatif (0 si aucun)
        "next((_e for _e in x if _e > 0), 0)",                                  # premier positif
        "next((_i for _i in range(len(x)) if x[_i] < 0), -1)",                  # index du premier négatif
    ]
    # PRIMITIVES DE BASE (briques élémentaires pour le mécanisme génératif : sorted∘f, len∘unique…). Standalone.
    _BASE = [
        "sorted(x)",                                                # tri croissant
        "sorted(x, reverse=True)",                                  # tri décroissant
        "x[::-1]",                                                  # renverse
        "list(dict.fromkeys(x))",                                   # uniques en ordre
    ]
    # Schémas FENÊTRE (paires consécutives) -> liste, et FILTRE-LISTE (garder par prédicat naturel) -> liste.
    # Familles « relations de voisinage » et « sélection » (sonde de familles 2026-06-23). Prédicats naturels
    # seulement (pas de seuil magique). Validation contextuelle dans etend_vocabulaire.
    _FENETRE = [
        "[x[_i + 1] + x[_i] for _i in range(len(x) - 1)]",          # somme par paires consécutives
        "[x[_i + 1] * x[_i] for _i in range(len(x) - 1)]",          # produit par paires consécutives
    ]
    _FILTRE_LISTE = [
        "[_e for _e in x if _e > 0]",                               # positifs seulement
        "[_e for _e in x if _e < 0]",                               # négatifs seulement
        "[_e for _e in x if _e % 2 == 0]",                          # pairs seulement
        "[_e for _e in x if _e != 0]",                              # non nuls
        "[_e for _e in x if _e % 2 == 1]",                          # impairs seulement
    ]
    # Schémas INDICE — raisonnement POSITIONNEL (utilise _i, pas seulement l'élément) : sélection d'indices,
    # dict indexé par position, pondération par l'indice. Famille distincte (sonde cross-domaine 2026-06-23).
    _INDEX = [
        "[_i for _i in range(len(x)) if x[_i] > 0]",                # indices des positifs
        "[_i for _i in range(len(x)) if x[_i] % 2 == 0]",           # indices des pairs
        "{_i: x[_i] for _i in range(len(x))}",                      # dict indexé par position (dict(enumerate))
        "sum(_i * x[_i] for _i in range(len(x)))",                  # somme pondérée par l'indice
        "sum(x[_i] for _i in range(0, len(x), 2))",                 # somme des positions PAIRES (stride 2)
        "sum(x[_i] for _i in range(1, len(x), 2))",                 # somme des positions IMPAIRES
        # — POSITIONNEL/ARGUMENT (famille générale : où est l'extrême ?) — argmax/argmin + tous les indices d'un extrême.
        "x.index(max(x))",                                          # argmax (position du 1er max)
        "x.index(min(x))",                                          # argmin (position du 1er min)
        "[_i for _i in range(len(x)) if x[_i] == max(x)]",          # indices du max (tous)
        "[_i for _i in range(len(x)) if x[_i] == min(x)]",          # indices du min (tous)
    ]
    # FAMILLES RÉELLES (corpus réel 2026-06-23) — tâches utiles d'un vrai assistant. Validation contextuelle.
    # ÉLÉMENT vs AGRÉGAT : chaque élément combiné à un agrégat global de x (normalisation, %, distance).
    _ELEM_AGG = [
        "[_e - min(x) for _e in x]",                                # normaliser par le min (décalage)
        "[max(x) - _e for _e in x]",                                # distance au max
        "[100 * _e // sum(x) for _e in x]",                         # pourcentage du total
    ]
    # TRI INDEXÉ (médiane/top-N/n-ième) : sélectionner dans un tri. ACTIVÉ 2026-06-23 (choix Yohan : déplacer le
    # benchmark de frontière vers `mode`). `mediane` devient donc une CAPACITÉ (plus une frontière).
    _SORT_INDEX = [
        "sorted(x)[len(x) // 2]",                                   # médiane (élément du milieu)
        "sorted(x)[-2]",                                            # 2e plus grand
        "sorted(x, reverse=True)[:2]",                              # top 2
        "sorted(x)[:2]",                                            # bottom 2
        # — sur les valeurs DISTINCTES (dédup avant sélection) : 2e/3e distinct, plus petit/grand distinct —
        "sorted(set(x))[-2]",                                       # 2e plus grand DISTINCT
        "sorted(set(x))[1]",                                        # 2e plus petit DISTINCT
        "sorted(set(x))[0]",                                        # plus petit distinct (= min)
        "sorted(set(x))[-1]",                                       # plus grand distinct (= max)
        # — TRI PAR CLÉ DÉRIVÉE (famille générale : ordonner selon une fonction de l'élément) —
        "sorted(x, key=abs)",                                       # tri par valeur absolue
        "sorted(x, key=lambda _e: -_e)",                            # tri décroissant via clé
    ]
    # MAP CONDITIONNEL (transformer chaque élément, éventuellement selon une condition) ; SCAN (running) ;
    # DÉDUP-ORDRE + FENÊTRE-COMPTAGE (relations de voisinage). Familles réelles (sonde familles 2, 2026-06-23).
    _MAP_COND = [
        "[abs(_e) for _e in x]",                                   # valeur absolue de chaque
        "[_e if _e > 0 else 0 for _e in x]",                       # ReLU (garder positif, sinon 0)
        "[-_e for _e in x]",                                       # négation de chaque
        "[_e // 2 for _e in x]",                                   # moitié (division entière) de chaque
        "[_e % 2 == 0 for _e in x]",                               # est-pair (map booléen)
    ]
    _SCAN = [
        "list(__import__('itertools').accumulate(x, max))",        # running max
        "list(__import__('itertools').accumulate(x, min))",        # running min
        "list(__import__('itertools').accumulate(x))",             # sommes cumulées (préfixes)
        "list(__import__('itertools').accumulate(x, lambda _a, _b: _a * _b))",  # produit cumulatif
    ]
    _DEDUP_WINDOW = [
        "list(dict.fromkeys(x))",                                  # uniques en ordre d'apparition
        "sum(1 for _i in range(len(x) - 1) if x[_i + 1] > x[_i])", # nombre de montées
        "sum(1 for _i in range(len(x) - 1) if x[_i + 1] < x[_i])", # nombre de descentes
    ]
    # MULTISET / THÉORIE DES NOMBRES sur LISTE (élargissement nuit 2026-06-24 : fréquences + arithmétique).
    _NOMBRES_LISTE = [
        "max(set(x), key=lambda _e: (x.count(_e), -_e))",         # mode (plus fréquent ; tie-break déterministe)
        "sum(1 for _e in set(x) if x.count(_e) > 1)",             # nb d'éléments en doublon
        "sum(1 for _e in set(x) if x.count(_e) == 1)",           # nb d'éléments UNIQUES (hapax) — complète la famille fréquence
        "max(x.count(_e) for _e in set(x))",                     # fréquence du mode (compte max) — complète la famille fréquence
        "__import__('functools').reduce(__import__('math').gcd, [abs(_e) for _e in x], 0)",  # pgcd de la liste
        # — STRUCTURE LOCALE (vague 6) : pics, plus longue série de valeurs égales consécutives —
        "sum(1 for _i in range(1, len(x) - 1) if x[_i - 1] < x[_i] > x[_i + 1])",            # nb de pics
        "sum(1 for _i in range(1, len(x) - 1) if x[_i - 1] > x[_i] < x[_i + 1])",            # nb de vallées
        "max(sum(1 for _ in _g) for _k, _g in __import__('itertools').groupby(x))",          # plus longue série
    ]
    # GROUPBY / RUN-LENGTH (vague 20, capstone nuit 2026-06-24) : FRANCHIT la frontière `rle` — regroupement de
    # valeurs consécutives en structure imbriquée [[valeur, compte], …]. Sorties distinctives (liste de paires) ->
    # ne matchent que de vraies cibles rle, jamais une cible plate par coïncidence. La frontière se DÉPLACE vers
    # rle-DECODE (cf. valide_invention_gap). « Le plafond monte, le benchmark de frontière se déplace. »
    _GROUPBY = [
        "[[_k, sum(1 for _ in _g)] for _k, _g in __import__('itertools').groupby(x)]",       # rle (encode)
        "[_k for _k, _g in __import__('itertools').groupby(x)]",                              # valeurs sans répétition consécutive
        "[sum(1 for _ in _g) for _k, _g in __import__('itertools').groupby(x)]",             # longueurs des séries
    ]
    # EXPANSION / RUN-LENGTH DECODE (2026-06-24, après-nuit) : FRANCHIT la frontière `rle-decode` — l'INVERSE de rle :
    # une structure imbriquée [[valeur, compte], …] -> liste PLATE par DOUBLE expansion (boucle externe sur les paires,
    # boucle interne range(compte)). Entrée distinctive (liste de paires) : sur une liste plate, _p[1] crashe ->
    # ignoré par la validation contextuelle -> ne matche JAMAIS une cible plate par coïncidence (soundness préservée).
    # La frontière se DÉPLACE vers le FLATTEN RÉCURSIF profondeur arbitraire (récursion vraie, hors vocab borné).
    _EXPANSION = [
        "[_p[0] for _p in x for _ in range(_p[1])]",                                          # rle-decode ([[v,c],…] -> plat)
        "[_p[1] for _p in x for _ in range(_p[0])]",                                          # decode si l'ordre est [compte, valeur]
        # RÉCURSION par AUTO-APPLICATION (combinateur, dans l'esprit des formes lambda réf-unique de la nuit) : flatten
        # PROFONDEUR ARBITRAIRE d'une liste imbriquée -> liste plate. C'est le 1er atome RÉCURSIF du vocabulaire (les
        # autres sont des compréhensions à profondeur fixe). SOUNDNESS : sélectionné seulement s'il reproduit le held-out
        # (confirmé au juge) -> au pire AMBIGU, jamais de FAUX. La frontière se DÉPLACE vers une cible exigeant une
        # RECHERCHE (subset-sum : NP, hors recombinaison = « un solveur, pas un atome » cf. note AlphaZero/GPU).
        "(lambda _g: _g(_g, x))(lambda _g, _l: [_v for _e in _l for _v in (_g(_g, _e) if isinstance(_e, list) else [_e])])",
    ]
    # ARBRES (imbrication profonde) — frontière MESURÉE (sonde palier structurel 2026-07-12) : l'atome flatten
    # RÉCURSIF ci-dessus existait mais RIEN ne composait par-dessus (somme_arbre/max_arbre/nb_feuilles =
    # brique_manquante) ; la profondeur est un 2e catamorphisme (fold d'arbre distinct, cf. recursion schemes).
    # SCOPÉ à l'aplatie récursive SEULE (même design prouvé que _MAT_APLATIE) : AGG∘flatten_rec + profondeur,
    # PAS une famille récursive générale — sémantique exacte, zéro aimant à coïncidences. Sur liste PLATE,
    # AGG∘flatten_rec ≡ AGG(x) (même signature comportementale -> jamais une fausse AMBIGU) ; sur arbre, AGG(x)
    # crashe (validation contextuelle) -> seuls les vrais candidats arbre survivent.
    _FLAT_REC = ("(lambda _g: _g(_g, x))(lambda _g, _l: [_v for _e in _l for _v in "
                 "(_g(_g, _e) if isinstance(_e, list) else [_e])])")
    _ARBRE = [
        "sum(" + _FLAT_REC + ")",                  # somme de l'arbre (profondeur arbitraire)
        "max(" + _FLAT_REC + ")",                  # max de l'arbre
        "min(" + _FLAT_REC + ")",                  # min de l'arbre
        "len(" + _FLAT_REC + ")",                  # nombre de feuilles
        # profondeur d'imbrication (catamorphisme distinct : 1 + max des profondeurs des sous-listes)
        "(lambda _g: _g(_g, x))(lambda _g, _l: 1 + max((_g(_g, _e) for _e in _l if isinstance(_e, list)), default=0))",
    ]
    # SORTIES STRUCTURÉES (palier structurel, atome 2) — frontière MESURÉE (sonde 2026-07-12) : partition par
    # prédicat, groupby par clé CALCULÉE et pivot liste-de-paires -> dict restaient brique_manquante
    # (paquets_de_2, lui, était déjà couvert). Ce sont les opérateurs de PREMIÈRE CLASSE de la littérature
    # table-manipulation (GroupBy/Pivot/Partition — synthèse SQL par exemples, migration hiérarchique->relationnel),
    # pas de la recombinaison libre. Famille dirigée BORNÉE, sémantique exacte ; sorties DISTINCTIVES
    # (liste-de-2-listes, dict-de-listes, dict) -> ne matchent jamais une cible plate par coïncidence ;
    # groupby = sémantique clés OBSERVÉES (celles présentes dans les données, le canon du groupby).
    _SORTIE_STRUCTUREE = [
        # partition par prédicat -> [[ceux qui satisfont], [les autres]] (les 2 ordres : le spec tranche)
        "[[_e for _e in x if _e % 2 == 0], [_e for _e in x if _e % 2 == 1]]",
        "[[_e for _e in x if _e % 2 == 1], [_e for _e in x if _e % 2 == 0]]",
        "[[_e for _e in x if _e >= 0], [_e for _e in x if _e < 0]]",
        "[[_e for _e in x if _e < 0], [_e for _e in x if _e >= 0]]",
        # groupby par clé calculée -> {clé observée: [éléments]}
        "{_k: [_e for _e in x if _e % 2 == _k] for _k in sorted({_v % 2 for _v in x})}",
        "{_k: [_e for _e in x if _e % 3 == _k] for _k in sorted({_v % 3 for _v in x})}",
        "{_k: [_e for _e in x if len(_e) == _k] for _k in sorted({len(_v) for _v in x})}",   # par longueur (mots)
        # pivot liste-de-paires -> dict (direct et inversé ; une paire ASYMÉTRIQUE les discrimine)
        "{_p[0]: _p[1] for _p in x}",
        "{_p[1]: _p[0] for _p in x}",
        # GROUPBY GÉNÉRALISÉ (atome 7, frontière mesurée après l'atome 2) : clé = f(élément) au-delà des
        # modulos — premier élément/lettre (mots ET listes), signe. Même sémantique clés OBSERVÉES.
        "{_k: [_e for _e in x if _e[0] == _k] for _k in sorted({_v[0] for _v in x})}",
        "{_k: [_e for _e in x if (_e > 0) - (_e < 0) == _k] for _k in sorted({(_v > 0) - (_v < 0) for _v in x})}",
        # PIVOT 2 NIVEAUX (canon pandas pivot_table : split sur une grille 2D) : liste de triplets
        # [a, b, c] -> {a: {b: c}} — sortie dict-de-dicts, distinctive, jamais coïncidente.
        "{_a: {_p[1]: _p[2] for _p in x if _p[0] == _a} for _a in sorted({_q[0] for _q in x})}",
        # DÉGROUPAGE (atome 8, frontière mesurée) : l'INVERSE du groupby — dict-de-listes -> liste de paires
        # [clé, valeur], clés triées (déterminisme). Referme l'aller-retour groupby/dégroupage (même patron
        # que rle encode/decode : « la frontière se déplace vers l'inverse »).
        "[[_k, _v] for _k in sorted(x) for _v in x[_k]]",
    ]
    # DICT PROFOND (atome 15, frontière mesurée) : dict-de-dicts — agrégats des valeurs PROFONDES,
    # aplatissement, et DÉPIVOT = l'inverse du pivot 2 niveaux (referme l'aller-retour pivot/dépivot,
    # comme groupby/dégroupage). Validation contextuelle : sur un dict PLAT, _sd.values() crashe -> filtré.
    _DICT_PROFOND = [
        "sum(_v for _sd in x.values() for _v in _sd.values())",             # somme des valeurs profondes
        "max(_v for _sd in x.values() for _v in _sd.values())",
        "min(_v for _sd in x.values() for _v in _sd.values())",
        "sum(len(_sd) for _sd in x.values())",                              # nb d'entrées profondes
        "{_k2: _v for _sd in x.values() for _k2, _v in _sd.items()}",       # aplatissement (fusion des sous-dicts)
        "[[_k, _k2, _v] for _k in sorted(x) for _k2, _v in sorted(x[_k].items())]",   # dépivot -> triplets triés
        "{_k: sum(_sd.values()) for _k, _sd in sorted(x.items())}",         # agrégat par groupe (somme des sous-dicts)
    ]
    # CHIFFRES d'un entier ; PRÉDICAT palindrome ; ARITHMÉTIQUE à 2 champs ([fait, total] -> %).
    _DIVERS_REEL = [
        "sum(int(_d) for _d in str(x))",                           # somme des chiffres
        "len(str(x))",                                             # nombre de chiffres
        "x == x[::-1]",                                            # palindrome (chaîne/liste)
        "x[0] * 100 // x[1]",                                      # progression % ([fait, total])
    ]
    # Schémas MATRICES (liste de listes) — domaine SANS primitives seed : l'IA les acquiert par schéma sur un gap
    # matriciel (cf. _STR pour les chaînes). Primitives matrice→liste + agrégats AGG(primitive)→scalaire.
    _MAT_PRIMS = [
        "[list(_c) for _c in zip(*x)]",          # transposée
        "[sum(_r) for _r in x]",                 # somme par ligne
        "[sum(_c) for _c in zip(*x)]",           # somme par colonne
        "[max(_r) for _r in x]",                 # max par ligne
        "[min(_r) for _r in x]",                 # min par ligne
        "[max(_r) - min(_r) for _r in x]",       # amplitude par ligne
        "[x[_i][_i] for _i in range(len(x))]",   # diagonale
        "[x[_i][-1 - _i] for _i in range(len(x))]",  # anti-diagonale
        "[_v for _r in x for _v in _r]",         # aplatie
    ]
    _MAT_AGG = ["sum({P})", "max({P})", "min({P})", "__import__('math').prod({P})"]   # trace=sum∘diagonale, produit_diagonale=prod∘diagonale…
    # LISTE-OP ∘ APLATIE -> LISTE : trier/renverser/dédoublonner l'aplatie de la matrice. Ferme les cibles dont
    # la sortie est une LISTE réordonnée de l'aplatie (aplati_trie = sorted∘aplatie, aplati_unique = sorted∘set…).
    # SCOPÉ à l'aplatie SEULE (pas à toutes les primitives) : c'est LA frontière mesurée ; l'appliquer partout
    # ne créerait que des candidats coïncidents sur specs faibles (ambiguïtés spurieuses), pas de vraie capacité.
    _MAT_APLATIE = "[_v for _r in x for _v in _r]"
    _MAT_LISTE_OP = ["sorted({P})", "sorted({P}, reverse=True)", "list(dict.fromkeys({P}))", "sorted(set({P}))"]
    # Schémas DICT (mapping) — domaine SANS seed : acquis par schéma sur un gap dict. Listes-de-valeurs/clés à
    # agréger + argmax/argmin (clé du max/min). Validation contextuelle : x.values() erreur sur liste/matrice -> skip.
    _DICT_LIST = ["list(x.values())", "list(x.keys())", "sorted(x.values())", "sorted(x.keys())"]  # supports d'agrégat
    _DICT_DIRECT = [
        "max(x, key=x.get)", "min(x, key=x.get)",                 # argmax/argmin (clé du max/min)
        "{_v: _k for _k, _v in x.items()}",                       # dict inversé (valeur -> clé)
        "{_k: _v for _k, _v in sorted(x.items())}",               # dict trié par clé
        "len(x)",                                                  # nombre d'entrées
    ]
    _DICT_AGG = ["sum({P})", "max({P})", "min({P})"]   # somme_valeurs=sum∘values, max_valeur=max∘values…
    # Schémas CHAÎNES-COMPOSITIONS — au-delà des primitives _STR simples : compositions sur MOTS/CARACTÈRES.
    # Domaine SANS seed -> acquis par schéma sur un gap chaîne (cf. _MAT/_DICT). Validation contextuelle :
    # x.split() erreur sur liste/int/matrice -> ignoré (ne matche que de vraies chaînes).
    _STR_COMPOS = [
        "''.join(_m[0] for _m in x.split())",        # initiales (acronyme)
        "''.join(_m[-1] for _m in x.split())",       # dernières lettres de chaque mot
        "max(x.split(), key=len)",                    # mot le plus long
        "min(x.split(), key=len)",                    # mot le plus court
        "' '.join(_m[::-1] for _m in x.split())",     # inverse chaque mot
        "' '.join(sorted(x.split()))",                # mots triés alpha
        "' '.join(x.split()[::-1])",                  # mots en ordre inverse
        "sum(_c in 'aeiou' for _c in x.lower())",     # compte voyelles
        "len(x.split())",                             # nombre de mots
        "max(len(_m) for _m in x.split())",           # longueur du plus long mot
        "sum(len(_m) for _m in x.split())",           # longueur totale des mots
        "[len(_m) for _m in x.split()]",              # liste des longueurs de mots
        "{_m: x.split().count(_m) for _m in set(x.split())}",   # fréquence des mots (string->dict)
        "x.swapcase()",                               # inverse la casse
    ]

    def etend_vocabulaire(self, exemples):
        """L'IA COMBLE un gap auto-découvert en INSTANCIANT des schémas de primitives qu'elle n'avait pas — SANS qu'on
        les lui donne : INDEXATION/TRANCHAGE paramétrés (x[k], x[:k]…) + FOLDS/réductions (produit, comptages, prédicats).
        Validation CONTEXTUELLE (réalité) : on ne garde que ce qui TOURNE sans crash sur les entrées des exemples
        (x[1] est partiel — interdit en primitive globale TOTALE — mais valide dans le contexte de la tâche). SÛR : un
        atome inapplicable ailleurs échoue au juge -> ignoré ; aucun faux. C'est « créer ce qui manque », jugé par la réalité."""
        schemas = ([f"x[{k}]" for k in (1, 2, 3, -2, -3)]
                   + [f"x[:{k}]" for k in (2, 3)] + [f"x[{k}:]" for k in (2, 3)] + ["x[1:-1]"]
                   + self._FOLDS + self._FENETRE + self._FILTRE_LISTE + self._INDEX
                   + self._ELEM_AGG + self._SORT_INDEX + self._MAP_COND + self._SCAN + self._DEDUP_WINDOW
                   + self._NOMBRES_LISTE + self._GROUPBY + self._EXPANSION + self._ARBRE + self._SORTIE_STRUCTUREE
                   + self._DICT_PROFOND
                   + self._DECOUPE + self._CONTROLE + self._BASE + self._DIVERS_REEL + self._STR)
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in schemas:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]                  # tourne sur TOUTES les entrées d'exemple ?
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, str) for o in outs):
                to = "str"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            elif all(isinstance(o, dict) for o in outs):
                to = "dict"
            else:
                continue
            self.atomes.append((expr, "list", to))
            ajoutes += 1
        return ajoutes

    def etend_composition(self, exemples):
        """Schéma COMPOSITIONNEL DIRIGÉ (recherche dirigée vs BFS large) : AGG(f(_e) for _e in x) pour AGG ∈
        {sum, produit, max, min} et f parcourant les TRANSFORMATIONS int→int COMPACTES du répertoire (incl. inventées :
        cube, etc.). Construit DIRECTEMENT sum∘map(cube)=somme_cubes, prod∘map(f), etc. — la chaîne 3-profonde que le BFS
        enterrait. Validation CONTEXTUELLE (réalité, sur les entrées). SÛR : inapplicable ailleurs -> échoue au juge."""
        import re as _re
        sub = _re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])")
        transfos = [e for e, ti, to in self.atomes if ti == "int" and to == "int" and len(e) <= 16]
        AGG = ["sum({F} for _e in x)",
               "__import__('functools').reduce(lambda a, b: a * b, [{F} for _e in x])",
               "max({F} for _e in x)", "min({F} for _e in x)"]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for fe in transfos:
            F = sub.sub("_e", fe)
            for tmpl in AGG:
                expr = tmpl.format(F=F)
                if expr in existants:
                    continue
                try:
                    f = _fn(expr)
                    outs = [f(x) for x, _ in exemples]
                except Exception:
                    continue
                if all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                    self.atomes.append((expr, "list", "int"))
                    existants.add(expr)
                    ajoutes += 1
        return ajoutes

    # MÉCANISME GÉNÉRATIF — vocabulaire CURÉ de composition : transforms liste→liste (l'inner f) × consumers
    # liste→* (l'outer g). DIRIGÉ et borné (≈ |T|×|G|), pas l'explosion des 345 atomes bruts d'explore_combine.
    _GEN_TRANSFORMS = [
        "sorted(x)", "sorted(x, reverse=True)", "sorted(x, key=abs)", "x[::-1]", "list(dict.fromkeys(x))",
        "[abs(_e) for _e in x]", "[_e * _e for _e in x]", "[-_e for _e in x]",
        "[_e * 2 for _e in x]", "[_e + 1 for _e in x]",
        "[_e for _e in x if _e > 0]", "[_e for _e in x if _e % 2 == 0]", "[_e for _e in x if _e != 0]",
        # `differences` en LAMBDA à RÉFÉRENCE UNIQUE de la base : composable à toute profondeur sans explosion de
        # longueur (la forme x[_i+1]-x[_i]…len(x) référence x 3× -> differences∘differences explose le cap).
        "(lambda _y: [_y[_i + 1] - _y[_i] for _i in range(len(_y) - 1)])(x)",
        "list(__import__('itertools').accumulate(x))",              # sommes cumulées (préfixes) — composable
        "[(_e > 0) - (_e < 0) for _e in x]",                        # signe de chaque élément (-1/0/1)
        "[max(_e, 0) for _e in x]",                                 # relu (max avec 0)
    ]
    _GEN_CONSUMERS = [
        "sum(x)", "max(x)", "min(x)", "len(x)", "x[0]", "x[-1]", "len(set(x))",
        "sorted(x)", "x[::-1]", "__import__('math').prod(x)", "list(dict.fromkeys(x))",
        "(lambda _y: max(_y) - min(_y))(x)",                        # amplitude en LAMBDA réf-unique (ne duplique pas l'inner)
    ]

    def etend_composition_generale(self, exemples, profondeur=2):
        """MÉCANISME GÉNÉRATIF (2026-06-23, choix Yohan ; APPROFONDI nuit 2026-06-24, mandat « plus long/complexe »
        pour la réflexion+synthèse) — compose g(f_k(…f_1(x))) sur un vocabulaire CURÉ : `profondeur` transforms
        liste→liste chaînés (l'inner) puis un consumer liste→* (l'outer). Les inners sont DÉDUPLIQUÉS PAR
        COMPORTEMENT sur les exemples (abs∘abs=abs, sorted∘sorted=sorted, neg∘neg=id…) -> la profondeur N'EXPLOSE
        PAS (collapse fort) ; garde-fou dur sur le nombre d'inners. SOUND PAR CONSTRUCTION : n'ajoute que des
        CANDIDATS ; les gardes d'examine_cible (held-out + unicité + nouveauté) tranchent -> jamais de faux.
        (Composer les ATOMES bruts était trop indirigé : 345 atomes liste→liste -> explosion.)"""
        import re as _re
        sub = _re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])")
        xs = [x for x, _ in exemples]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0

        # Un inner est valable s'il produit une LISTE d'entiers sur TOUTES les entrées d'exemple (sinon : mauvais
        # domaine -> ignoré, aucun faux). Dédup SYNTAXIQUE (par chaîne) : on NE collapse PAS par comportement
        # sur-exemples (qui perdrait carres∘uniques≡carres quand les exemples n'ont pas de doublon) -> coverage =
        # SUR-ENSEMBLE garanti de l'ancien g(f(x)). Le cap dur borne l'explosion.
        def _liste_ok(expr):
            try:
                outs = [_fn(expr)(x) for x in xs]
            except Exception:
                return False
            return all(isinstance(o, list)
                       and all(isinstance(e, int) and not isinstance(e, bool) for e in o) for o in outs)

        # NIVEAU 1 : tous les transforms simples (compat totale avec l'ancien g(f(x))).
        inners = []
        seen_expr = set()
        frontier = []
        for fe in self._GEN_TRANSFORMS:
            if not _liste_ok(fe):
                continue
            inners.append(fe)
            seen_expr.add(fe)
            frontier.append(fe)

        # NIVEAUX 2..profondeur : chaîner f∘base (chaînes de raisonnement plus LONGUES), dédup syntaxique + cap.
        for _ in range(max(0, profondeur - 1)):
            nouveau = []
            for base in frontier:
                base_in = "(" + base + ")"
                for fe in self._GEN_TRANSFORMS:
                    expr = sub.sub(base_in, fe)           # fe avec x := base  (chaîne f∘base)
                    # cap 240 (pas 120) : `differences` référence x 3× et `amplitude` (consumer) 2× -> les chaînes
                    # légitimes avec ces primitives dépassent 120 ; le cap de COMPTE (240 inners) borne l'explosion.
                    if len(expr) > 240 or expr in seen_expr or not _liste_ok(expr):
                        continue
                    seen_expr.add(expr)
                    inners.append(expr)
                    nouveau.append(expr)
            frontier = nouveau
            if len(inners) > 240:                         # garde-fou dur anti-explosion
                break

        # 1bis) chaque inner CHAÎNÉ (niveau >= 2) est aussi un candidat LISTE en soi (consumer = identité) : couvre
        #       les cibles dont la sortie EST la chaîne (ex. sorted(double(x), key=abs)) sans agrégat outer.
        for inexpr in inners:
            if inexpr in self._GEN_TRANSFORMS or inexpr in existants:
                continue
            self.atomes.append((inexpr, "list", "list"))
            existants.add(inexpr)
            ajoutes += 1

        # 2) g(inner) pour chaque consumer (l'outer).
        for inexpr in inners:
            inner = "(" + inexpr + ")"
            for ge in self._GEN_CONSUMERS:
                expr = sub.sub(inner, ge)                 # g avec x := inner
                if expr in existants or len(expr) > 240:
                    continue
                try:
                    fn = _fn(expr)
                    outs = [fn(x) for x in xs]
                except Exception:
                    continue
                if all(isinstance(o, bool) for o in outs):
                    to = "bool"
                elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                    to = "int"
                elif all(isinstance(o, list) for o in outs):
                    to = "list"
                else:
                    continue
                self.atomes.append((expr, "list", to))
                existants.add(expr)
                ajoutes += 1
        return ajoutes

    def etend_synthese(self, exemples):
        """AUTO-SYNTHÈSE DE PRIMITIVES (2026-06-23, le cap de l'auto-évolution) — face à un gap, l'engine
        SYNTHÉTISE des primitives PARAMÉTRIQUES en CHERCHANT les constantes DANS LES DONNÉES (seuils, pas/stride,
        puissances) au lieu d'attendre des schémas à constantes fixes codés à la main. Mint ce qui tourne sur les
        exemples ; la SOUNDNESS reste garantie par examine_cible (held-out + unicité + nouveauté) -> un candidat
        sur-ajusté qui rate le held-out, ou ambigu, ne devient jamais une fausse invention. Bornée (constantes
        DÉRIVÉES des données + petits entiers, templates capés)."""
        vals = []
        for x, _ in exemples:
            if isinstance(x, list):
                vals += [v for v in x if isinstance(v, int) and not isinstance(v, bool)]
            elif isinstance(x, int) and not isinstance(x, bool):
                vals.append(x)
        vals = sorted(set(vals))
        seuils = set(vals)
        for i in range(len(vals) - 1):
            seuils.add((vals[i] + vals[i + 1]) // 2)
        seuils = sorted(seuils)[:24]                       # cap anti-explosion
        templates = []
        for k in range(1, 6):                              # PAS (stride) cherché
            templates.append(f"sum(x[_i] for _i in range(0, len(x), {k}))")
            templates.append(f"sum(x[_i] for _i in range({k % 2}, len(x), {k}))")
        for c in seuils:                                   # SEUIL cherché (filtre / comptage / agrégat / map affine)
            for cmp in (">", ">=", "<", "<="):
                templates.append(f"sum(_e for _e in x if _e {cmp} {c})")
                templates.append(f"len([_e for _e in x if _e {cmp} {c}])")
                templates.append(f"[_e for _e in x if _e {cmp} {c}]")
        for c in sorted(set(seuils) | set(range(1, 11))):  # offsets/facteurs : seuils + petites constantes communes
            for op in ("+", "-", "*", "//"):
                if op == "//" and c == 0:
                    continue
                templates.append(f"[_e {op} {c} for _e in x]")
        for p in (2, 3):                                   # PUISSANCE cherchée
            templates.append(f"sum(_e ** {p} for _e in x)")
            templates.append(f"[_e ** {p} for _e in x]")
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in templates:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]
            except Exception:
                continue
            # ANTI-COÏNCIDENCE : un FILTRE à seuil qui ne retire RIEN sur AUCUN exemple (output == input partout)
            # est l'IDENTITÉ déguisée (seuil = extrême observé, ex. `>= min`). Il ne capture pas une vraie sélection
            # et crée une fausse AMBIGU vs l'identité (que l'apprentissage actif ne peut lever car la synthèse
            # régénère un seuil = nouvel extrême à chaque tour). On ne l'émet pas (bruit, jamais une vraie brique).
            if " if " in expr and all(isinstance(o, list) and o == list(xx) for o, (xx, _) in zip(outs, exemples)):
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            else:
                continue
            self.atomes.append((expr, "list", to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    def etend_composition_filtree(self, exemples):
        """Composition FILTRÉE dirigée : AGG(F for _e in x if COND) et [F for _e in x if COND] — filtrer PUIS
        transformer PUIS agréger (3 étapes). Étend etend_composition d'une clause conditionnelle BORNÉE (prédicats
        naturels). Ferme somme_carres_pairs, produit_impairs, carres_pairs. Recherche dirigée bornée (transfos ×
        conds × agg), validation CONTEXTUELLE. SÛR : inapplicable -> échoue au juge."""
        import re as _re
        sub = _re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])")
        transfos = [e for e, ti, to in self.atomes if ti == "int" and to == "int" and len(e) <= 16]
        CONDS = ["_e % 2 == 0", "_e % 2 == 1", "_e > 0", "_e < 0"]
        FORMES = ["sum({F} for _e in x if {C})",
                  "__import__('math').prod([{F} for _e in x if {C}])",
                  "max(({F} for _e in x if {C}), default=0)",
                  "[{F} for _e in x if {C}]"]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for fe in transfos:
            F = sub.sub("_e", fe)
            for C in CONDS:
                for tmpl in FORMES:
                    expr = tmpl.format(F=F, C=C)
                    if expr in existants:
                        continue
                    try:
                        f = _fn(expr)
                        outs = [f(x) for x, _ in exemples]
                    except Exception:
                        continue
                    if all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                        to = "int"
                    elif all(isinstance(o, list) for o in outs):
                        to = "list"
                    else:
                        continue
                    self.atomes.append((expr, "list", to))
                    existants.add(expr)
                    ajoutes += 1
        return ajoutes

    def etend_indexe(self, exemples):
        """Compositions INDEXÉES : AGG(G for _i, _e in enumerate(x) [if COND]) où la transformation G ET la
        condition COND peuvent référencer l'INDICE `_i`, pas seulement la valeur `_e`. C'est le mécanisme
        qu'AUCUNE famille ne couvrait (compte des points fixes x[i]==i, somme des positions paires, somme
        pondérée _e*_i, indice-dépendances). Recherche dirigée bornée (transfos × conds × agg = 6×6×4),
        validation CONTEXTUELLE (tourne sur les entrées). SÛR : les gardes d'examine_cible (held-out +
        unicité + nouveauté) tranchent -> jamais de faux ; un atome inapplicable échoue au juge."""
        TRANSF = ["_e", "_i", "_e * _i", "_e + _i", "_e - _i", "1"]
        CONDS = ["", " if _e == _i", " if _e > _i", " if _e < _i", " if _i % 2 == 0", " if _i % 2 == 1"]
        FORMES = ["sum({G} for _i, _e in enumerate(x){C})",
                  "max(({G} for _i, _e in enumerate(x){C}), default=0)",
                  "min(({G} for _i, _e in enumerate(x){C}), default=0)",
                  "[{G} for _i, _e in enumerate(x){C}]"]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for G in TRANSF:
            for C in CONDS:
                for tmpl in FORMES:
                    expr = tmpl.format(G=G, C=C)
                    if expr in existants:
                        continue
                    try:
                        f = _fn(expr)
                        outs = [f(x) for x, _ in exemples]
                    except Exception:
                        continue
                    if all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                        to = "int"
                    elif all(isinstance(o, list) for o in outs):
                        to = "list"
                    else:
                        continue
                    self.atomes.append((expr, "list", to))
                    existants.add(expr)
                    ajoutes += 1
        return ajoutes

    def etend_paires(self, exemples):
        """Compositions TOUTES-PAIRES O(n²) : AGG sur les couples ordonnés (i<j) de la liste. Le mécanisme des
        relations ENTRE éléments distants qu'aucune famille LOCALE (fenêtre glissante, fold) ne couvrait :
        nb d'inversions (x[i]>x[j]), nb de paires égales, somme des produits/écarts de couples… Recherche
        dirigée BORNÉE (une poignée de formes canoniques), validation CONTEXTUELLE. SÛR : les gardes
        d'examine_cible (held-out + unicité + nouveauté) tranchent -> jamais de faux."""
        P = "for _i in range(len(x)) for _j in range(_i + 1, len(x))"
        FORMES = [
            f"sum(1 {P} if x[_i] > x[_j])",              # nb d'inversions
            f"sum(1 {P} if x[_i] < x[_j])",              # nb de couples croissants
            f"sum(1 {P} if x[_i] == x[_j])",             # nb de paires égales
            f"sum(x[_i] * x[_j] {P})",                   # somme des produits de couples
            f"sum(abs(x[_i] - x[_j]) {P})",              # somme des écarts absolus (dispersion pairwise)
        ]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in FORMES:
            if expr in existants:
                continue
            try:
                f = _fn(expr)
                outs = [f(x) for x, _ in exemples]
            except Exception:
                continue
            if all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                self.atomes.append((expr, "list", "int"))
                existants.add(expr)
                ajoutes += 1
        return ajoutes

    def etend_sous_tableaux(self, exemples):
        """Compositions SOUS-TABLEAUX CONTIGUS : AGG sur les sommes des tranches x[i:j] (i<j). Le mécanisme
        du meilleur segment contigu (Kadane = max des sommes de sous-tableaux, min des sommes…) qu'aucune
        famille ne couvrait — distinct de etend_paires (couples d'ÉLÉMENTS) et de accumulate (préfixes seuls).
        Formes canoniques bornées, validation CONTEXTUELLE. SÛR : gardes d'examine_cible -> jamais de faux."""
        S = "for _i in range(len(x)) for _j in range(_i + 1, len(x) + 1)"
        FORMES = [f"max(sum(x[_i:_j]) {S})",              # Kadane : meilleur sous-tableau contigu
                  f"min(sum(x[_i:_j]) {S})"]              # pire sous-tableau contigu
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in FORMES:
            if expr in existants:
                continue
            try:
                f = _fn(expr)
                outs = [f(x) for x, _ in exemples]
            except Exception:
                continue
            if all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                self.atomes.append((expr, "list", "int"))
                existants.add(expr)
                ajoutes += 1
        return ajoutes

    def etend_composition_liste(self, exemples):
        """Compositions LISTE-OP∘map -> LISTE : trier/renverser un map(f) (carres_tries = sorted∘map(carré),
        carres_renverses = map(carré)[::-1]). Complète etend_composition (qui ne fait que AGG∘map -> scalaire) :
        la même chaîne 3-profonde mais à sortie LISTE. Abstractions de 2e niveau « transformer puis réordonner »,
        comblées de façon ADDITIVE et sûre (pas de feedback risqué dans le vocabulaire). Validation CONTEXTUELLE."""
        import re as _re
        sub = _re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])")
        transfos = [e for e, ti, to in self.atomes if ti == "int" and to == "int" and len(e) <= 16]
        LISTOPS = ["sorted([{F} for _e in x])", "sorted([{F} for _e in x], reverse=True)", "[{F} for _e in x][::-1]"]
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for fe in transfos:
            F = sub.sub("_e", fe)
            for tmpl in LISTOPS:
                expr = tmpl.format(F=F)
                if expr in existants:
                    continue
                try:
                    f = _fn(expr)
                    outs = [f(x) for x, _ in exemples]
                except Exception:
                    continue
                if all(isinstance(o, list) for o in outs):
                    self.atomes.append((expr, "list", "list"))
                    existants.add(expr)
                    ajoutes += 1
        return ajoutes

    def etend_matrice(self, exemples):
        """Vocabulaire MATRICIEL auto-instancié sur un gap matriciel : primitives (transposée, réductions
        ligne/colonne, diagonale, aplatie) + agrégats AGG(primitive) -> scalaire (trace = sum∘diagonale,
        grand_total = sum∘aplatie, max_global = max∘aplatie). Validation CONTEXTUELLE (réalité) : ce qui
        ERREUR sur les entrées (= pas une matrice : zip(*scalaire), x[i][i] sur un int) est ignoré -> aucun
        faux. Câblé comme etend_vocabulaire/etend_composition (recherche dirigée, pas BFS large)."""
        existants = {e for e, _, _ in self.atomes}
        cand = (list(self._MAT_PRIMS)
                + [agg.format(P=p) for p in self._MAT_PRIMS for agg in self._MAT_AGG]
                + [op.format(P=self._MAT_APLATIE) for op in self._MAT_LISTE_OP])
        ajoutes = 0
        for expr in cand:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]                 # tourne sur TOUTES les entrées ? (sinon : pas matriciel)
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            elif all(isinstance(o, dict) for o in outs):
                to = "dict"
            else:
                continue
            self.atomes.append((expr, "list", to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    def etend_dict(self, exemples):
        """Vocabulaire DICT auto-instancié sur un gap dict (mapping) : agrégats AGG(valeurs/clés) -> scalaire
        (somme_valeurs = sum∘values, max_valeur = max∘values) + argmax/argmin (clé du max/min via key=x.get).
        Validation CONTEXTUELLE (réalité) : ce qui ERREUR sur les entrées (= pas un dict : .values() sur une
        liste) est ignoré -> aucun faux. Câblé comme etend_vocabulaire/etend_matrice (recherche dirigée)."""
        existants = {e for e, _, _ in self.atomes}
        cand = list(self._DICT_DIRECT) + [agg.format(P=p) for p in self._DICT_LIST for agg in self._DICT_AGG]
        ajoutes = 0
        for expr in cand:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]                 # tourne sur TOUTES les entrées ? (sinon : pas un dict)
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, str) for o in outs):
                to = "str"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            elif all(isinstance(o, dict) for o in outs):
                to = "dict"
            else:
                continue
            self.atomes.append((expr, "list", to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    def etend_chaines(self, exemples):
        """Vocabulaire CHAÎNES-COMPOSITIONS auto-instancié sur un gap chaîne : compositions sur mots/caractères
        (initiales = join∘first∘split, mot_le_plus_long = argmax-len∘split, inverse_par_mot, compte_voyelles…).
        Validation CONTEXTUELLE (réalité) : ce qui ERREUR sur les entrées (= pas une chaîne) est ignoré -> aucun
        faux. Câblé comme etend_vocabulaire/etend_matrice/etend_dict (recherche dirigée)."""
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in self._STR_COMPOS:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]                 # tourne sur TOUTES les entrées ? (sinon : pas une chaîne)
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, str) for o in outs):
                to = "str"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            elif all(isinstance(o, dict) for o in outs):
                to = "dict"
            else:
                continue
            self.atomes.append((expr, "list", to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    # Schémas ENTIER (entrée = un seul entier n) — domaine SANS primitives seed côté listes : les schémas
    # listes erreurent sur un int -> il faut un vocabulaire DÉDIÉ. Familles générales : formules fermées
    # (somme 1..n, carrés…), récurrences exprimées fonctionnellement (factorielle/fibonacci via reduce :
    # la frontière « récursif/état » franchie sans boucle impérative), puissances, chiffres, parité, plages.
    _ENTIER = [
        "x * (x + 1) // 2",                                            # somme 1..n (formule fermée de Gauss)
        "sum(range(1, x + 1))",                                        # somme 1..n (itérative)
        "sum(range(x))",                                               # somme 0..n-1
        "__import__('math').factorial(x)",                            # factorielle
        "__import__('functools').reduce(lambda _a, _b: _a * _b, range(1, x + 1), 1)",   # factorielle (fold)
        "__import__('functools').reduce(lambda _a, _b: (_a[1], _a[0] + _a[1]), range(x), (0, 1))[0]",  # n-ième Fibonacci (fold d'état)
        "x ** 2", "x ** 3", "x * x", "x + x", "x * 2", "2 ** x",      # puissances / multiples
        "x // 2", "x % 2", "x % 2 == 0", "-x", "abs(x)",              # parité / division / signe
        "sum(int(_d) for _d in str(abs(x)))",                         # somme des chiffres
        "len(str(abs(x)))",                                           # nombre de chiffres
        "int(str(x)[::-1]) if x >= 0 else -int(str(-x)[::-1])",       # entier renversé
        "list(range(x))", "list(range(1, x + 1))",                    # plages
        "[_i * _i for _i in range(1, x + 1)]",                        # carrés 1..n
        # — élargissement nuit 2026-06-24 : bits / théorie des nombres (entrée mono-int) —
        "bin(x).count('1')",                                          # popcount (nb de bits à 1)
        "x > 0 and (x & (x - 1)) == 0",                               # est une puissance de 2 ?
        "sum(1 for _d in range(1, x + 1) if x % _d == 0)",            # nombre de diviseurs
        "sum(_d for _d in range(1, x + 1) if x % _d == 0)",          # somme des diviseurs
        "x > 1 and all(x % _d for _d in range(2, x))",               # est premier ?
        # collatz (longueur) en EXPRESSION pure : récursion par auto-application (pas de boucle impérative)
        "(lambda _g: _g(_g, x, 0))(lambda _s, _n, _c: _c if _n <= 1 else _s(_s, _n // 2 if _n % 2 == 0 else 3 * _n + 1, _c + 1))",
        # — décomposition d'un entier (vague 6) : racine entière, chiffres, binaire —
        "__import__('math').isqrt(x)",                               # racine carrée entière
        "[int(_d) for _d in str(abs(x))]",                          # liste des chiffres
        "[int(_b) for _b in bin(abs(x))[2:]]",                      # représentation binaire (liste de bits)
        "str(x) == str(x)[::-1]",                                   # entier palindrome ?
    ]

    def etend_entier(self, exemples):
        """Vocabulaire ENTIER (entrée mono-int) auto-instancié sur un gap entier : formules fermées,
        récurrences (factorielle/fibonacci) exprimées en fold fonctionnel, puissances, chiffres, plages.
        Validation CONTEXTUELLE (réalité) : ce qui ERREUR sur les entrées (= pas un int : str(x)[::-1] sur
        une liste, range(x) sur une liste) est ignoré -> ne matche que de vrais entiers, aucun faux. Câblé
        comme etend_matrice/etend_dict (recherche dirigée). Franchit la frontière récursif/état SANS boucle
        impérative (reduce d'état) -> l'IA acquiert la famille, pas un cas isolé."""
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in self._ENTIER:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]                    # tourne sur TOUTES les entrées ? (sinon : pas un int)
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, str) for o in outs):
                to = "str"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            else:
                continue
            self.atomes.append((expr, "int", to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    # ───────── FUSIONS DE DOMAINES (structures COMPOSITES — mandat « multi-domaine » Yohan) ─────────
    def _instancie(self, cand, exemples, ti="list"):
        """Motif commun d'auto-extension : instancie une liste de schémas, ne garde que ceux qui TOURNENT sur
        TOUTES les entrées d'exemple (validation contextuelle = la réalité), type de sortie inféré. SÛR : ce qui
        erreure sur la structure (= mauvais domaine) est ignoré -> aucun faux. `ti` = type d'entrée (pour la compo)."""
        existants = {e for e, _, _ in self.atomes}
        ajoutes = 0
        for expr in cand:
            if expr in existants:
                continue
            f = _fn(expr)
            try:
                outs = [f(x) for x, _ in exemples]
            except Exception:
                continue
            if all(isinstance(o, bool) for o in outs):
                to = "bool"
            elif all(isinstance(o, int) and not isinstance(o, bool) for o in outs):
                to = "int"
            elif all(isinstance(o, str) for o in outs):
                to = "str"
            elif all(isinstance(o, list) for o in outs):
                to = "list"
            elif all(isinstance(o, dict) for o in outs):
                to = "dict"
            else:
                continue
            self.atomes.append((expr, ti, to))
            existants.add(expr)
            ajoutes += 1
        return ajoutes

    _LSTR = [   # liste de CHAÎNES (fusion str × list)
        "[_w.upper() for _w in x]", "[_w.lower() for _w in x]", "[len(_w) for _w in x]",
        "sum(len(_w) for _w in x)", "max(x, key=len)", "min(x, key=len)", "''.join(x)", "' '.join(x)",
        "sorted(x)", "sorted(x, key=len)", "len(x)", "[_w[0] for _w in x]", "''.join(_w[0] for _w in x)",
        "[_w[::-1] for _w in x]", "max(len(_w) for _w in x)", "min(len(_w) for _w in x)",
        "[_w for _w in x if len(_w) > 1]",
    ]
    _DLST = [   # dict de LISTES (fusion dict × list)
        "{_k: sum(_v) for _k, _v in x.items()}", "{_k: max(_v) for _k, _v in x.items()}",
        "{_k: min(_v) for _k, _v in x.items()}", "{_k: len(_v) for _k, _v in x.items()}",
        "{_k: sorted(_v) for _k, _v in x.items()}", "sum(sum(_v) for _v in x.values())",
        "max(max(_v) for _v in x.values())", "[sum(_v) for _v in x.values()]",
        "sum(len(_v) for _v in x.values())",
    ]
    _LPAIR = [  # liste de PAIRES [a, b]
        "[_a + _b for _a, _b in x]", "[_a * _b for _a, _b in x]", "[_a - _b for _a, _b in x]",
        "[abs(_a - _b) for _a, _b in x]", "[_a for _a, _b in x]", "[_b for _a, _b in x]",
        "[max(_a, _b) for _a, _b in x]", "[min(_a, _b) for _a, _b in x]",
        "sum(_a + _b for _a, _b in x)", "sum(_a * _b for _a, _b in x)",
    ]

    def etend_liste_chaines_fusion(self, exemples):
        """Vocabulaire LISTE-DE-CHAÎNES (map/agg sur mots : longueurs, plus_long, total_lettres, concatène…)."""
        return self._instancie(self._LSTR, exemples, ti="list")

    def etend_dict_listes(self, exemples):
        """Vocabulaire DICT-DE-LISTES (agg par clé : somme/max/len par clé, total global…)."""
        return self._instancie(self._DLST, exemples, ti="dict")

    def etend_liste_paires(self, exemples):
        """Vocabulaire LISTE-DE-PAIRES (combiner les 2 champs : somme/produit/max par paire, projections…)."""
        return self._instancie(self._LPAIR, exemples, ti="list")

    _PAIRE_LISTES = [   # DEUX listes [A, B] (raisonnement INTER-séquences : zip des deux)
        "[_a + _b for _a, _b in zip(x[0], x[1])]", "[_a - _b for _a, _b in zip(x[0], x[1])]",
        "[_a * _b for _a, _b in zip(x[0], x[1])]", "[max(_a, _b) for _a, _b in zip(x[0], x[1])]",
        "[min(_a, _b) for _a, _b in zip(x[0], x[1])]", "sum(_a * _b for _a, _b in zip(x[0], x[1]))",
        "sum(_a + _b for _a, _b in zip(x[0], x[1]))", "x[0] + x[1]", "x[1] + x[0]",
        "[abs(_a - _b) for _a, _b in zip(x[0], x[1])]",
    ]

    def etend_paire_listes(self, exemples):
        """Vocabulaire DEUX-LISTES (zip de A et B : somme/diff/produit élément-par-élément, produit scalaire,
        concaténation). N'opère que sur des entrées [A, B] (sinon zip(int,int) erreure -> ignoré, aucun faux)."""
        return self._instancie(self._PAIRE_LISTES, exemples, ti="list")

    def etend_liste_dicts(self, exemples):
        """Vocabulaire LISTE-D'ENREGISTREMENTS (liste de dicts) : agg/projection par CHAMP. Les champs sont
        DÉCOUVERTS (intersection des clés de tous les dicts) -> général (pas de nom de champ codé en dur)."""
        champs = None
        for x, _ in exemples:
            if not (isinstance(x, list) and x and all(isinstance(d, dict) for d in x)):
                return 0
            ks = set.intersection(*[set(d.keys()) for d in x])
            champs = ks if champs is None else (champs & ks)
        if not champs:
            return 0
        cand = []
        for f in sorted(map(repr, champs)):
            cand += [f"sum(_d[{f}] for _d in x)", f"[_d[{f}] for _d in x]", f"max(_d[{f}] for _d in x)",
                     f"min(_d[{f}] for _d in x)", f"sorted(_d[{f}] for _d in x)"]
        return self._instancie(cand, exemples, ti="list")

    def resoudre_autonome(self, faire_tache, exemples, oracle, max_pas=8):
        """BOUCLE AUTONOME COMPLÈTE (zéro aide) : résoudre ; si AMBIGU -> demander l'entrée discriminante à la RÉALITÉ
        (oracle) et réapprendre ; si HORS -> ÉTENDRE le vocabulaire (combler le gap) et réessayer. L'IA invente,
        s'interroge, se corrige — bornée par la réalité. `faire_tache(exemples)->Tache`."""
        ex = list(exemples)
        etendu = False
        r = {"etat": "hors"}
        for _ in range(max_pas):
            r = self.resoudre_confiant(faire_tache(ex), ex)
            if r["etat"] == "ambigu":
                q = r["question"]
                ex.append((list(q), oracle(list(q))))             # la réalité répond à la question CHOISIE par l'IA
                continue
            if r["etat"] == "hors" and not etendu:
                self.etend_vocabulaire(ex)                         # comble le gap : indexation/tranchage/folds
                self.etend_composition(ex)                         # + schémas compositionnels dirigés (AGG∘map(f))
                etendu = True
                continue
            break
        return r

    # --- Résolution CONFIANTE / active learning ------------------------------------------------
    def _candidats_passants(self, tache):
        """Tous les atomes dont le code passe les exemples VISIBLES (sans encore exiger le held-out)."""
        from juge import juge
        from auto_invention_ouverte import LIM
        out = []
        for expr, ti, to in self.atomes:
            code = f"def {tache.point_entree}(x):\n    return {expr}\n"
            if juge(code, tache.tests, LIM).passe:
                out.append((expr, ti, to))
        return out

    def resoudre_confiant(self, tache, exemples, sondes=None):
        """Renvoie un dict :
          - {'etat':'confiant', 'expr':..., 'n':k}  : k candidats passent ET S'ACCORDENT sur toutes les sondes.
          - {'etat':'ambigu', 'question':entree, 'sorties':{expr:val}} : désaccord -> entrée discriminante à trancher.
          - {'etat':'hors'} : aucun candidat ne passe les exemples.
        `sondes` = entrées de stress ; si None, l'IA les AUTO-FORGE depuis `exemples` (sondes_auto) — zéro aide."""
        if sondes is None:
            sondes = self.sondes_auto(exemples)
        cands = self._candidats_passants(tache)
        if not cands:
            return {"etat": "hors"}
        # comportement de chaque candidat sur les sondes
        comport = {}
        for expr, ti, to in cands:
            f = _fn(expr)
            sig = []
            for s in sondes:
                try:
                    sig.append(repr(f(s)))
                except Exception:
                    sig.append("ERR")
            comport[expr] = sig
        # désaccord sur une sonde ?
        for j, s in enumerate(sondes):
            vals = {comport[e][j] for e in comport}
            if len(vals) > 1:
                return {"etat": "ambigu", "question": s,
                        "sorties": {e: comport[e][j] for e in comport}}
        # aucun désaccord sur les sondes. La dédup comportementale du moteur fait qu'un seul comportement survit en
        # général -> 1 candidat = HYPOTHÈSE non confirmée (peut être une coïncidence, cf. min+1) ; ≥2 d'accord sur
        # TOUTES les sondes = consensus robuste. On rend le plus court (Occam) avec le bon niveau de confiance.
        meilleur = min(cands, key=lambda c: len(c[0]))
        if len(cands) >= 2:
            return {"etat": "confiant", "expr": meilleur[0], "n": len(cands)}
        return {"etat": "tentatif", "expr": meilleur[0], "n": 1}   # hypothèse : demande plus d'exemples pour confirmer


if __name__ == "__main__":
    from garde_ressources import borne
    from taches import Tache
    from demande import _asserts
    borne()

    def T(pe, vis, held):
        return Tache(id=pe, point_entree=pe, prompt=f"def {pe}(x):\n  pass",
                     tests=_asserts(pe, [((a,), o) for a, o in vis]),
                     tests_held_out=_asserts(pe, [((a,), o) for a, o in held]))

    m = MoteurAutonome()
    g = len(m.atomes)
    m.explore_combine(budget=3000)
    print(f"AUTONOME : graine {g} -> {len(m.atomes)} atomes (compose+map+combine), coût={m._cout}\n")

    # TEST AVEUGLE — tâches inconnues, AUCUNE aide : les sondes sont AUTO-FORGÉES par l'IA depuis les exemples.
    TESTS = [
        ("somme_cubes",   [([1, 2], 9), ([2, 3], 35)], [([1, 1, 1], 3), ([3], 27)]),
        ("max_moins_min", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9)]),
        ("deuxieme_elt",  [([9, 8, 7], 8), ([1, 2, 3], 2)], [([3, 9, 1], 9)]),
        ("somme_doubles", [([1, 2, 3], 12), ([5], 10)], [([0, 4], 8)]),
    ]
    # ORACLES de réalité (la VÉRITÉ de chaque tâche — c'est la réalité, PAS une aide : l'IA choisit la question,
    # la réalité répond). Sert à fermer la boucle d'apprentissage actif quand l'IA demande une entrée discriminante.
    ORACLE = {
        "somme_cubes": lambda x: sum(e ** 3 for e in x),
        "max_moins_min": lambda x: max(x) - min(x),
        "deuxieme_elt": lambda x: x[1],
        "somme_doubles": lambda x: sum(2 * e for e in x),
    }
    print("FACE À L'INCONNU (résolution confiante / active learning, zéro aide ; boucle jusqu'à 3 questions) :")
    for pe, vis, held in TESTS:
        vis = list(vis)
        for tour in range(4):
            r = m.resoudre_confiant(T(pe, vis, held), vis)   # sondes AUTO-forgées depuis les exemples
            if r["etat"] == "ambigu":
                q = r["question"]                       # l'IA CHOISIT l'entrée la plus informative
                rep = ORACLE[pe](list(q))               # la RÉALITÉ répond (oracle), pas moi
                vis.append((list(q), rep))              # l'IA APPREND l'épreuve dure et recommence
                continue
            break
        if r["etat"] == "confiant":
            print(f"  ✅ {pe:16s} CONFIANT ({r['n']} candidats) -> {r['expr']}  [après {tour} question(s) à la réalité]")
        elif r["etat"] == "tentatif":
            print(f"  ◽ {pe:16s} TENTATIF (1 candidat, non confirmé) -> {r['expr']}  [demande plus d'exemples]")
        elif r["etat"] == "ambigu":
            print(f"  ❓ {pe:16s} ENCORE AMBIGU après questions (divergent: {set(r['sorties'].values())})")
        else:
            print(f"  ⛔ {pe:16s} HORS — gap découvert : aucune brique ne généralise (il faut inventer + de vocabulaire)")
