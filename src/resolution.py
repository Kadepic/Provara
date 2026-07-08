"""
RÉSOLUTION FLOUE D'ENTITÉS (moteur — ADDITIF, ne modifie pas lecteur.py).

But : rendre l'IA tolérante aux FAUTES DE FRAPPE sur l'ENTITÉ d'une question (« protugal » -> « portugal »,
« arabie saoudit » -> « arabie saoudite ») AVANT le lookup, SANS jamais inventer.

INVARIANT FAUX=0 : on ne corrige QUE s'il existe UNE correspondance unique et PROCHE (distance d'édition ≤ seuil)
parmi les clés RÉELLES de la relation visée. Ambiguïté (≥2 candidats au même minimum) ou rien d'assez proche
-> AUCUNE correction (on reste HORS, honnête). On ne devine jamais entre deux possibilités. Heuristique de
sûreté : on n'essaie pas les entités très courtes (≤3) — trop de voisins, trop risqué.

ADDITIF & RÉUTILISABLE : lit `lecteur.LECTEUR` (tables, _GABARITS, cherche) ET `base_faits.FAITS` en LECTURE
SEULE. lecteur.py n'est pas touché -> les 1088 tests de T1 sont intacts. ia.py expose ce service via
`donnee_nl_floue`. Couvre les relations qui ont un gabarit NL (monnaie, langue, continent, code iso, …).
"""
from __future__ import annotations

import re
from itertools import islice

import base_faits
import lecteur
import taxonomie
from base_faits import VERIFIE, HORS, normalise


def _dist(a: str, b: str, maxd: int) -> int:
    """Distance de DAMERAU-Levenshtein (OSA) BORNÉE : insertion/suppression/substitution = 1, ET TRANSPOSITION
    de deux lettres adjacentes = 1 (les fautes de frappe les plus fréquentes : « numreo »->« numero »,
    « cpaitale »->« capitale », « protugal »->« portugal »). Coupe à maxd+1 dès qu'une ligne dépasse `maxd`."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > maxd:
        return maxd + 1
    prev2 = None
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        mini = i
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                v = min(v, prev2[j - 2] + 1)          # transposition adjacente
            cur[j] = v
            if v < mini:
                mini = v
        if mini > maxd:
            return maxd + 1
        prev2, prev = prev, cur
    return prev[lb]


def _seuil(mot: str) -> int:
    """Seuil de tolérance selon la longueur : court = strict (anti-ambiguïté), long = plus permissif."""
    n = len(mot)
    if n <= 3:
        return 0          # trop court -> pas de fuzzy
    if n <= 6:
        return 1
    return 2


def _cles_relation(relation: str):
    """Toutes les clés candidates d'une relation : table ingérée du lecteur + amorce base_faits (lecture seule)."""
    t = lecteur.LECTEUR.tables.get(relation)
    if t is not None:
        for cle in t.keys():
            yield cle
    for (rel, ent) in base_faits.FAITS:
        if rel == relation:
            yield ent


# Déterminants POSSESSIFS : « de MON chien », « de SA voiture » -> l'entité appartient à quelqu'un, c'est du
# LITTÉRAL. On n'y applique PAS le fuzzy. (Garde appliqué par les APPELANTS, qui voient la question entière.)
_POSSESSIFS_RE = re.compile(r"\b(?:mon|ma|mes|ton|ta|tes|son|sa|ses|notre|nos|votre|vos|leur|leurs)\s")

# GARDE LEXIQUE : on ne « corrige » JAMAIS une saisie qui est déjà un MOT de la langue (« chien », « lune »,
# « voiture »…). PRIORITÉ ABSOLUE À FAUX=0 : mieux vaut ne pas corriger un vrai mot (même si l'utilisateur visait
# un nom propre, ex. « frace ») que produire une réponse FAUSSE (« lune » -> une capitale). Le lexique kaikki est
# large : il attrape donc aussi quelques fautes — c'est le prix, assumé, de l'inviolabilité de FAUX=0.
# Tables à clé NUE (le mot entier EST un lemme : « chien », « mede », « acajou amer »).
_LEXIQUE_RELS = ("genre_grammatical", "definition_nom", "definition_verbe", "definition_adjectif")
# Tables LEXÈMES dont la clé est « lemme langue » (kaikki/Wikidata lexèmes, normalisée : « mère (français) » ->
# clé interne « mere francais »). Le LEMME = la clé sans son DERNIER token (= la langue). Ces tables, ingérées
# en masse (genre_grammatical_mot 480k, categorie_lexicale_mot 1,0M…), avaient ouvert un FAUX+ : « mère » n'étant
# pas une clé NUE, `_est_mot_connu` la croyait inconnue et le fuzzy la corrigeait en « mede » (clé nue, dist 1) ->
# réponse « nom » absurde. On reconnaît donc AUSSI les lemmes de ces tables comme des mots réels (jamais corrigés).
_LEXIQUE_RELS_LEMME_LANGUE = ("genre_grammatical_mot", "categorie_lexicale_mot", "concept_du_mot")


def _est_mot_connu(cle: str) -> bool:
    """Un mot RÉEL (jamais fuzzy-corrigé). LÉGER (pas de matérialisation des 2,3 M lemmes -> tenait ~1,5 Go RSS) :
    clés NUES + variante française « <lemme> francais » des tables lexèmes (contexte francophone). O(1)/table."""
    for rel in _LEXIQUE_RELS:
        t = lecteur.LECTEUR.tables.get(rel)
        if t is not None and cle in t:
            return True
    cle_fr = f"{cle} francais"               # clé interne des lexèmes = « lemme langue » normalisé (« mere francais »)
    for rel in _LEXIQUE_RELS_LEMME_LANGUE:
        t = lecteur.LECTEUR.tables.get(rel)
        if t is not None and cle_fr in t:
            return True
    return False


_CORRIGE_MEMO: dict = {}                     # (relation, cible) -> résultat ; borné (purgé à 4096)
_CORRIGE_MAX_CLES = 500_000                  # au-delà : PAS de fuzzy — scanner des MILLIONS de clés coûtait des
#                                              SECONDES PAR QUESTION (14 M d'itérations profilées, 2026-07-08)
#                                              pour des corrections à fort risque d'ambiguïté. Exact seulement.


def corrige(relation: str, saisie: str):
    """Meilleure correction UNIQUE de `saisie` parmi les clés de `relation`, ou None.
    Renvoie (cle_corrigee, distance) si une seule clé atteint le minimum (≤ seuil), sinon None (rien/ambigu).
    On exige la MÊME initiale (les fautes la préservent quasi toujours) : prune massif + précision accrue.
    GARDE FAUX=0 : jamais de correction d'un mot connu du lexique (« chien »≠« chine », « lune »≠une capitale)."""
    cible = lecteur.LECTEUR._cle(relation, saisie)
    if not cible:
        return None
    _t = lecteur.LECTEUR.tables.get(relation)
    if _t is not None and len(_t) > _CORRIGE_MAX_CLES:
        return None
    _cle_memo = (relation, cible)
    if _cle_memo in _CORRIGE_MEMO:
        return _CORRIGE_MEMO[_cle_memo]
    if len(_CORRIGE_MEMO) > 4096:
        _CORRIGE_MEMO.clear()
    _CORRIGE_MEMO[_cle_memo] = None          # posé d'avance : tout `return None` en aval reste cohérent
    if _est_mot_connu(cible) or _est_mot_connu(normalise(saisie)):
        return None
    seuil = _seuil(cible)
    if " " in cible:           # entité MULTI-MOTS (souvent une phrase littérale) : fuzzy strict (dist ≤1) pour
        seuil = min(seuil, 1)  # éviter « ile deserte » -> « ile desire ». Un mono-mot garde dist 2 (allemag->allemagne).
    if seuil == 0:
        return None
    c0 = cible[0]
    meilleure_d = seuil + 1
    gagnantes: set = set()
    for cle in _cles_relation(relation):
        if not cle or cle[0] != c0 or abs(len(cle) - len(cible)) > seuil:
            continue
        if cle == cible:                 # déjà exact -> ce n'est pas une « correction »
            return None
        d = _dist(cible, cle, seuil)
        if d > seuil:
            continue
        if d < meilleure_d:
            meilleure_d, gagnantes = d, {cle}
        elif d == meilleure_d:
            gagnantes.add(cle)
    if meilleure_d <= seuil and len(gagnantes) == 1:
        gagnante = next(iter(gagnantes))
        # GARDE MULTI-MOTS : une correction ne doit jamais CORROMPRE un mot connu en un mot INCONNU. « fondation FRANCE »
        # -> « fondation FRANCKE » : la clé introduit « francke » (INCONNU, absent du cible) à la place de « france »
        # (connu) -> l'utilisateur veut France, pas la Fondation Francke -> rejet (FAUX+ : fondation de la France->1695).
        # MAIS un typo-fix vers un mot CONNU est légitime (« etas »->« etats », « saodite »->« saoudite » : le nouveau
        # mot est connu) -> on n'examine QUE les mots NEUFS de la clé : si l'un est INCONNU, c'est une corruption.
        if " " in cible:
            mots_cible = set(cible.split())
            for w in gagnante.split():
                if len(w) >= 4 and w not in mots_cible and not _est_mot_connu(w):
                    return None
        _CORRIGE_MEMO[_cle_memo] = (gagnante, meilleure_d)
        return (gagnante, meilleure_d)
    return None                          # rien d'assez proche, OU ambigu (≥2 candidats au même minimum)


# ————————————————————————————————— RÉSOLVEUR NL GÉNÉRIQUE (toutes relations) —————————————————————————————————
# `lecteur.repond_nl` ne connaît qu'~14 gabarits ÉCRITS À LA MAIN (monnaie, langue, continent…). Or il y a ~298
# relations. Ici on COMPREND une question sur N'IMPORTE quelle relation, sans gabarit codé : on détecte la
# RELATION par un mot de son NOM présent dans la question (« capitale », « numero atomique », « masse molaire »…)
# et l'ENTITÉ par ce qui suit la dernière préposition (« … du JAPON »). Soundness : la réponse est TOUJOURS
# `cherche(relation, entité)` = un fait vérifié, sinon HORS. Double ancrage (mot de relation + entité = clé réelle)
# => on ne « devine » pas : si l'entité n'est pas une vraie clé de la relation, on n'invente rien.
_GENERIQUES = frozenset("pays code nom prenom type sorte categorie de du des la le les un une en au aux et est "
                        "quel quelle quels quelles quoi est-ce quel-est officiel officielle "
                        # QUALIFICATIFS DE TYPE (pas des attributs) : « œuvre ÉCRITE » est un type de chose, pas
                        # l'attribut demandé -> non-désignants. Sinon « qui a ÉCRIT X » accroche `illustrateur_oeuvre_
                        # ecrite` via « ecrite » et renvoie l'illustrateur (FAUX+ Les Misérables -> Émile Bayard).
                        "oeuvre oeuvres ecrit ecrite ecrits ecrites".split())
_PREP = r"(?:de la|de l|du|des|de|\bd|en|au|aux|pour|chez)"   # \bd : « d'Italie » -> « d italie » (sans matcher « gran-d »)
# BRUIT conversationnel : mots de remplissage qui ne portent AUCUNE information de lookup (« euh dis … stp »,
# « alors … voila »). Retirés en tête de `resout_nl_generique`. Choisis pour n'être JAMAIS une entité ni un attribut
# (pas « bon »/« mais »/« fait » = trop ambigus). L'exact-`cherche` garde FAUX=0 : retirer un filler ne peut que
# faire échouer un match (-> HORS), jamais inventer une réponse.
_FILLERS = frozenset("euh heu hein stp svp voila alors donc dis dites ben bah merci coucou salut bonjour bonsoir "
                     "hello please".split())
_FILLERS_LOCUTIONS = (r"\bau fait\b", r"\btout a fait\b", r"\bs il (?:te|vous) plait\b", r"\bs il te plait\b")
# Mots-outils retirés lors de l'extraction d'entité « par soustraction » (stratégie 2). Tout ce qui n'est ni un
# mot-outil ni un token du nom de relation est présumé faire partie de l'ENTITÉ.
_STOP_ENTITE = _GENERIQUES | frozenset(
    "pour chez sur dans a il elle on l d ce cet cette mon ma mes ton ta tes son sa ses notre nos votre vos "
    "leur leurs me te se y qui que quels combien comment ou est-ce sont c".split())

# ALIAS VERBE -> ATTRIBUT : « qui a ÉCRIT X » désigne l'AUTEUR, pas un token du nom de relation. On ajoute le
# token-attribut correspondant aux « demandes » -> la bonne relation (auteur_*) est détectée. SOUND : `cherche`
# reste exact (attribut absent dans la donnée -> HORS) ; un attribut inexistant comme token de relation est inoffensif.
# Compatible avec « ecrit/ecrite » rendus génériques (anti-FAUX+ illustrateur) : ici on RÉ-active vers « auteur ».
_ALIAS_VERBE = {
    "ecrit": "auteur", "ecrite": "auteur", "ecrivit": "auteur", "redige": "auteur", "redigee": "auteur",
    "compose": "compositeur", "composee": "compositeur", "composa": "compositeur",
    "peint": "peintre", "peinte": "peintre", "peignit": "peintre",
    "sculpte": "sculpteur", "sculptee": "sculpteur",
    "realise": "realisateur", "realisee": "realisateur", "realisa": "realisateur",
    "fonde": "fondateur", "fondee": "fondateur", "fonda": "fondateur",
    "invente": "inventeur", "inventee": "inventeur", "inventa": "inventeur",
    "construit": "constructeur", "construite": "constructeur",
    "produit": "producteur", "produite": "producteur",
}

# CLASSIFIEURS linguistiques : « le MOT table », « le VERBE manger », « l'ADJECTIF bleu ». Le token qui SUIT le
# classifieur est la vraie entité (tête du syntagme). On ne RETIRE pas « mot » de l'entité (il peut être lui-même
# l'entité : « pluriel de mot » -> « mots ») ; on AJOUTE seulement un candidat « tête après classifieur » en plus
# basse priorité. Aucun classifieur dans « le ciel est bleu » -> aucun candidat ajouté -> FAUX=0 préservé.
_CLASSIFIEURS = frozenset(
    "mot mots lettre lettres verbe verbes adjectif adjectifs adverbe adverbes terme termes expression expressions".split())
# Sous-ensemble DÉSIGNANT UN MOT DE LANGUE (pas « lettre »). Quand l'un de ces classifieurs est présent, l'entité
# est explicitement un mot du français -> en cas d'ambiguïté, seules les relations LEXICALES sont pertinentes.
_CLASSIF_LINGUISTIQUES = frozenset(
    "mot mots verbe verbes adjectif adjectifs adverbe adverbes terme termes expression expressions".split())
# Marqueurs (lus dans la SOURCE du fait, donc DONNÉE et non liste de relations codée en dur) d'une relation lexicale.
_MARQUEURS_LEXICAUX = ("wiktionnaire", "wiktionary", "kaikki", "grammatical", "lexi")
# Attributs lexicaux EXPLICITES : déclenchent le candidat « X (français) » (clé lexème). « mot » EXCLU (trop
# générique : « le mot magique » n'est pas une demande de genre).
_ATTRS_LEXICAUX = frozenset("genre grammatical categorie definition sens concept nature lexicale etymologie".split())


def _source_lexicale(fait) -> bool:
    """Le fait provient-il d'une relation LEXICALE (Wiktionnaire/kaikki/…) ? Lu dans la source = donnée, pas hard-codé."""
    src = (getattr(fait, "source", "") or "").lower()
    return any(m in src for m in _MARQUEURS_LEXICAUX)


def _classif_ling_present(qn: str) -> bool:
    """La question contient-elle un classifieur DÉSIGNANT UN MOT de langue (« le mot/verbe/adjectif X ») ?"""
    return bool(set(qn.split()) & _CLASSIF_LINGUISTIQUES)

_REGISTRE = None
_VOCAB_REL = None
_FAMILLES = None


def _registre():
    """Toutes les relations connues (tables ingérées + amorce base_faits). Lu une fois."""
    global _REGISTRE
    if _REGISTRE is None:
        rels = set(lecteur.LECTEUR.tables.keys())
        rels.update(rel for (rel, _ent) in base_faits.FAITS)
        _REGISTRE = sorted(rels)
    return _REGISTRE


def _familles():
    """Index attribut-tête (1er token) -> relations de la même famille (« pays » -> pays_chateau, pays_volcan…).
    Sert à la garde d'ambiguïté #79/#80 : une clé nue partagée par plusieurs types d'une même famille est ambiguë."""
    global _FAMILLES
    if _FAMILLES is None:
        d = {}
        for rel in _registre():
            d.setdefault(rel.split("_")[0], []).append(rel)
        _FAMILLES = d
    return _FAMILLES


_NEG_TOKENS_RE = re.compile(r"\bn(?:e)?\b[^?]*\b(?:pas|plus|jamais|aucune?|nulle?)\b")
_VERBES_OEUVRE = frozenset("ecrit ecrite compose composee chante chantee interprete interpretee realise realisee "
                           "peint peinte joue jouee dirige titre intitule appelle nomme".split())


def negation_fait_partie_entite(question: str) -> bool:
    """True si la « négation » d'une question fait en réalité partie d'une ENTITÉ réelle — un TITRE d'œuvre comme
    « On ne badine pas avec l'amour » (Musset), « Ne me quitte pas » (Brel) — et non une vraie négation LOGIQUE.
    SOUND (#88) : on n'autorise le lookup d'une question « négative » QUE si une CLÉ EXACTE contenant les tokens de
    négation existe dans une relation -> c'est un titre. Une vraie question négative (« quelle ville n'est pas la
    capitale ») n'a AUCUNE telle clé -> reste bloquée (FAUX=0 préservé : jamais de réponse positive à une négation)."""
    qn = normalise(question)
    cands = set()
    for m in re.finditer(rf"\b{_PREP}\s+", qn):           # le titre suit une préposition (« auteur DE on ne badine… »)
        cands.add(qn[m.end():].strip(" ?.!"))
    toks = qn.split()
    for i, tk in enumerate(toks):                        # … ou un verbe d'œuvre (« qui a ECRIT on ne badine… »)
        if tk in _VERBES_OEUVRE:
            cands.add(" ".join(toks[i + 1:]).strip(" ?.!"))
    for c in cands:
        if len(c) >= 5 and _NEG_TOKENS_RE.search(c):     # le candidat CONTIENT la négation -> titre potentiel
            for rel in _registre():
                if lecteur.LECTEUR.cherche(rel, c) is not None:
                    return True                          # clé EXACTE contenant la négation = TITRE, pas une négation
    return False


# ANTI-HOMONYME DATA-DÉRIVÉ (2026-07-02) : l'ex-liste `_HOMONYME_KW` (40 mots-clés de types choisis à la
# main — film/personne/equipe/navire…) est REMPLACÉE par la mesure de population de `taxonomie.py` :
# une relation ne répond pour un pivot que si sa POPULATION DE CLÉS est compatible avec un TYPE du pivot
# (fraction d'échantillon, densité de couverture, ou source lexicale). Mesuré (campagne _mesure_pivots_*) :
# la liste manuelle sur-bloquait 168 réponses VRAIES (pays_code_vehicule : « vehicule » décrit l'ATTRIBUT,
# pas l'entité) et laissait passer des FAUX+ (altitude_localite[soudan]=437 = le village de Loire-Atlantique,
# statut_patrimonial_structure[montserrat] = une structure homonyme). La mesure corrige les deux sens.


_ELEMENT_CACHE = None
_CAPITALE_CACHE = None


def _ensemble_capitale():
    """Référence des CAPITALES = VALEURS de la relation `capitale` (Paris, Londres, Madrid, Tokyo…). Sous-ensemble
    SAILLANT de villes pour la garde homonyme (#105) : une capitale prime quasi toujours son homonyme œuvre/personne,
    alors qu'une ville obscure (Carmen, Olympia) est dominée par l'œuvre éponyme -> on ne pivote QUE sur les capitales."""
    global _CAPITALE_CACHE
    if _CAPITALE_CACHE is None:
        t = lecteur.LECTEUR.tables.get("capitale")
        _CAPITALE_CACHE = ({normalise(str(t.get(k).valeur)) for k in t.keys() if t.get(k) is not None}
                           if t is not None else set())
    return _CAPITALE_CACHE


def _ensemble_element():
    """Référence des ÉLÉMENTS chimiques = clés de `numero_atomique` (fer, or, argent, mercure…). Pivot anti-homonyme :
    « Mercure/Mars » sont des éléments/astres saillants -> une relation NON-chimique/astro éponyme = homonyme."""
    global _ELEMENT_CACHE
    if _ELEMENT_CACHE is None:
        t = lecteur.LECTEUR.tables.get("numero_atomique")
        _ELEMENT_CACHE = set(t.keys()) if t is not None else set()
    return _ELEMENT_CACHE


def _pivot_homonyme_oeuvre(rel0, cle0):
    """True si l'entité résolue est un PIVOT SAILLANT (PAYS / CAPITALE / ASTRE) MAIS la POPULATION DE CLÉS de la
    relation gagnante est INCOMPATIBLE avec tous les types du pivot (mesure `taxonomie.population_compatible`) ->
    HOMONYME accidentel : l'utilisateur vise le pivot, pas l'entité éponyme. Ex. « couleur de l'Espagne »->couleur_film
    (densité pays 0.06 = collisions) ; « sexe de Paris »->sexe_personne (Pâris, densité capitales 0.05) (#100) ;
    « altitude du Soudan »->altitude_localite=437 (le VILLAGE de Loire-Atlantique : densité pays 0.09 -> bloqué,
    alors que densité capitales 0.65 -> « altitude de Paris » reste répondable) ; « auteur de Mercure »->Nothomb
    (#102). Abstenir. Sound : ne bloque QUE pivot + population-incompatible — les relations du pivot (capitale/
    monnaie frac pays 0.9 ; annee_creation_organisation densité pays 0.55 [les pays SONT des organisations] ;
    numero_atomique frac éléments 1.0 ; pluriel/définitions source lexicale) répondent ; une entité NON-pivot
    (Germinal, Inception) n'est pas bloquée.
    CLÉ CANONIQUE (fix 2026-07-02) : `cle0` arrive parfois BRUTE avec déterminant (« du soudan » — _PREP matchait
    le « de » interne d'« altitu-de ») ; `cherche` la canonise pour trouver le fait, mais le garde testait la forme
    brute -> « du soudan » ∉ pays -> gate jamais déclenché (trou pré-existant, aussi dans l'ex-garde à mots-clés).
    On canonise avec le MÊME `_cle` que le lecteur : le garde juge exactement la clé qui a répondu."""
    nc = lecteur.LECTEUR._cle(rel0, str(cle0)) or normalise(str(cle0))
    # PIVOTS SAILLANTS = PAYS + CAPITALES + ASTRES. VILLE restreinte aux CAPITALES (#105 : « compositeur de Carmen »
    # sinon bloqué, l'OPÉRA de Bizet primant la ville Carmen). ÉLÉMENT RETIRÉ #106 : les éléments mots-communs (or/fer/
    # argent/plomb) sont dominés par leurs homonymes-œuvres (« réalisateur de L'Argent » de Bresson) -> sur-block ; et
    # les vrais FAUX « élément » trouvés (Mercure) sont AUSSI des astres -> déjà couverts par l'ensemble astres.
    # Cette sélection des pivots saillants est CERTIFIÉE par le corpus de pièges (#98-#118) = des erreurs MESURÉES.
    if (nc not in _ensemble_pays() and nc not in _ensemble_capitale() and nc not in _ensemble_astre()):
        return False
    return not taxonomie.population_compatible(rel0, taxonomie.types_de(nc))


def _valeur_echo_attribut(rel0, valeur, qtoks):
    """True si la VALEUR n'est que l'ÉCHO du mot-ATTRIBUT demandé -> réponse TAUTOLOGIQUE dégénérée à écarter (#98).
    Ex. « quelle est la couleur de la France » : il existe un FILM « France » et `couleur_film[france]='couleur'`
    (le film est EN COULEUR) -> réponse « la couleur de la France est couleur » = absurde (homonyme film/pays + valeur
    = l'attribut). Sound : on n'abstient QUE si la valeur EST exactement le 1er token (attribut) de la relation ET que
    ce mot est dans la question — jamais une vraie réponse informative (« monnaie de X »=« euro »≠« monnaie »)."""
    nv = normalise(str(valeur))
    return bool(nv) and nv == rel0.split("_")[0] and nv in qtoks


def _entite_exacte_dans_famille(ent, rel):
    """True si `ent` (EXACT) est une clé dans une AUTRE relation de la même famille d'attribut -> `ent` est une vraie
    entité (pas une faute de frappe), donc on ne doit PAS la fuzzy-corriger (#113). Ex. « cap blanc » échoue dans
    `pays_cap` mais EXISTE dans `pays_plateau`=France / `pays_montagne`=Algérie… -> le corriger en « cap blanco »=USA
    (autre lieu réel) serait FAUX. Sound : si l'entité saisie est RÉELLE ailleurs, la correction floue est illégitime."""
    fam = rel.split("_")[0]
    for r in _familles().get(fam, ()):
        if r != rel and lecteur.LECTEUR.cherche(r, ent) is not None:
            return True
    return False


def _ambigu_famille(rel0, cle0, vval, qtoks):
    """True si une relation de la MÊME famille d'attribut (1er token) possède la MÊME clé exacte avec une valeur
    DIFFÉRENTE, et qu'AUCUN token DISCRIMINANT (du nom de rel0, hors attribut partagé ET hors tokens de l'entité) ne
    désigne rel0 -> question nue ambiguë -> abstention (#79/#80). Le conflictuel a souvent un score 0 (son token de
    TYPE n'est pas dans la question) -> on scanne la FAMILLE entière, pas seulement les candidats scorés. Appliqué AUX
    DEUX voies de sortie (gagnant solitaire ET consensus) : « annee de opération harpoon » = opération 2002 (consensus
    debut/fin) MAIS bataille 1942 (score 0, invisible) -> ambigu. Sound : valeurs identiques = consensus (ignoré)."""
    if not cle0:
        return False
    toks_ent = set(normalise(str(cle0)).split())
    vnoms = rel0.split("_")
    for rel in _familles().get(vnoms[0], ()):
        if rel == rel0:
            continue
        g = lecteur.LECTEUR.cherche(rel, cle0)
        if g is None or normalise(str(g.valeur)) == vval:
            continue                              # absente ailleurs, ou MÊME valeur (consensus) -> pas de conflit
        autres = set(rel.split("_"))
        if not [t for t in vnoms if t not in autres and t in qtoks and t not in toks_ent]:
            return True                           # conflit réel sans token discriminant -> ambigu
    return False


def _vocab_rel() -> set:
    """Vocabulaire des MOTS-ATTRIBUTS = tokens de noms de relation (≥4, non générique). Pour corriger une faute
    sur le mot-attribut lui-même (« cpaitale » -> « capitale »)."""
    global _VOCAB_REL
    if _VOCAB_REL is None:
        _VOCAB_REL = {t for rel in _registre() for t in rel.split("_") if len(t) >= 4 and t not in _GENERIQUES}
    return _VOCAB_REL


def _corrige_vers(mot: str, vocab: set):
    """Token de `vocab` le plus proche de `mot` (même initiale, distance ≤ seuil, UNIQUE), ou None."""
    if mot in vocab:
        return mot
    seuil = _seuil(mot)
    if seuil == 0:
        return None
    meilleure_d, gagnantes = seuil + 1, set()
    for cible in vocab:
        if cible[0] != mot[0] or abs(len(cible) - len(mot)) > seuil:
            continue
        d = _dist(mot, cible, seuil)
        if d > seuil:
            continue
        if d < meilleure_d:
            meilleure_d, gagnantes = d, {cible}
        elif d == meilleure_d:
            gagnantes.add(cible)
    return next(iter(gagnantes)) if (meilleure_d <= seuil and len(gagnantes) == 1) else None


def _extrait_entite(qn: str) -> str:
    """Entité = ce qui suit la DERNIÈRE préposition (« capitale du japon » -> « japon »). Repli : derniers mots."""
    ms = list(re.finditer(_PREP + r"\s+(.+)$", qn))
    if ms:
        return ms[-1].group(1).strip()
    # repli : retirer les mots interrogatifs/génériques de tête, garder la fin.
    toks = [t for t in qn.split() if t not in _GENERIQUES]
    return " ".join(toks[-3:]) if toks else ""


# SUPERLATIF : « la plus haute montagne de France », « le plus grand lac… ». Ce N'EST PAS un lookup `attribut(clé)`
# (le moteur ne range pas « la plus haute X de Y » comme un fait) -> le résolveur générique DOIT s'abstenir, sinon
# il accroche une clé par coïncidence (« france » = un sommet) et renvoie un faux à-côté (« France »). Garde de
# SÛRETÉ pur : on ne perd que des réponses-coïncidence (des FAUX+), jamais une vraie réponse. Le RAISONNEMENT
# superlatif réel (filtre + argmax sur les faits numériques) est tenté AVANT, par `resout_superlatif`.
_RE_SUPERLATIF = re.compile(
    r"\b(?:la|le|les|l|du|des|de|d)\s+(?:plus|moins)\b"          # « la plus … », « le moins … », « du plus … »
    r"|\b(?:plus|moins)\s+(?:haut|grand|long|petit|eleve|profond|peuple|vaste|riche|cher|"  # « plus haute … »
    r"lourd|leger|rapide|lent|ancien|vieux|jeune|chaud|froid|nombreux|important|celebre|peuplee)\w*"
)


def _est_superlatif(qn: str) -> bool:
    """La question est-elle une demande SUPERLATIVE (« la plus … », « le plus grand … ») ? (sur texte normalisé)."""
    return bool(_RE_SUPERLATIF.search(qn))


# ————————————————————————————————— RAISONNEMENT SUPERLATIF (SOUND, anti-incomplétude) —————————————————————————————————
# Un superlatif (« la plus haute montagne de France ») n'est PAS un lookup par clé. Le PIÈGE FAUX=0 = calculer un
# argmax sur une base INCOMPLÈTE : « altitude_montagne ⋈ pays=France » donne « mont blanc du tacul » (4248) car le
# mont Blanc (4808) est taggé Italie (frontière) -> faux maximum qui SEMBLE vérifié. Parade : privilégier une
# RELATION EXPLICITE de la source (déjà agrégée et exacte). v1 = `point_culminant` (P610, « plus haut sommet du
# pays », 194 pays). On NE fait AUCUN argmax tant que la complétude de l'ensemble n'est pas certifiée (FAUX=0 >
# couverture) -> tout autre superlatif reste HORS (garde de `resout_nl_generique`).
_SUP_HAUT = frozenset("haut haute hauts hautes eleve elevee eleves elevees culminant culminants".split())
_TYPES_SOMMET = frozenset("montagne montagnes sommet sommets mont monts pic pics cime cimes point points".split())
# « chaîne / massif / cordillère » = un ENSEMBLE de montagnes, PAS un sommet -> point_culminant ne répond pas
# (réponse = un pic). Pas de relation « plus haute chaîne par pays » -> on s'abstient (HORS), jamais un pic à tort.
_EXCLUS_SOMMET = frozenset("chaine chaines massif massifs cordillere cordilleres chaines".split())


def resout_superlatif(question: str):
    """RAISONNEMENT superlatif SOUND -> STRING (réponse) ou None (HORS). v1 : « le plus haut sommet/montagne/point
    de <pays> » -> `point_culminant` (relation EXPLICITE, exacte ; PAS d'argmax sur base incomplète). Le reste -> None."""
    qn = normalise(question)
    if not _est_superlatif(qn):
        return None
    toks = set(qn.split())
    # « plus HAUT(E) {montagne|sommet|mont|pic|point} de <pays> » -> point culminant du pays (réponse exacte source).
    if (toks & _SUP_HAUT) and (toks & _TYPES_SOMMET) and not (toks & _EXCLUS_SOMMET):
        pays = _extrait_entite(qn)                 # « … de france » -> « france »
        if pays and pays != "monde":
            f = lecteur.LECTEUR.cherche("point_culminant", pays)
            if f is not None:
                return f.valeur                    # « mont Blanc » — sommet réel, pas un argmax
    return None


# ————————————————————————————————— A2 COMPARAISON (2 faits numériques vérifiés) —————————————————————————————————
# « la France est-elle plus grande que l'Espagne ? ». SOUND : on compare DEUX faits réels (pas d'argmax, pas de
# complétude requise). Gardes FAUX=0 : si une entité manque dans la relation -> HORS ; si deux attributs candidats
# donnent des verdicts CONTRADICTOIRES -> HORS (ambigu). L'adjectif donne l'attribut + la direction ; « moins » inverse.
_CMP_ATTR = {
    "grand": (True, ("superficie", "population", "aire")), "grande": (True, ("superficie", "population", "aire")),
    "grands": (True, ("superficie", "population", "aire")), "grandes": (True, ("superficie", "population", "aire")),
    "vaste": (True, ("superficie", "aire")), "etendu": (True, ("superficie", "aire")),
    "haut": (True, ("altitude", "hauteur")), "haute": (True, ("altitude", "hauteur")),
    "eleve": (True, ("altitude", "hauteur")), "elevee": (True, ("altitude", "hauteur")),
    "long": (True, ("longueur",)), "longue": (True, ("longueur",)),
    "peuple": (True, ("population",)), "peuplee": (True, ("population",)),
    "lourd": (True, ("masse",)), "lourde": (True, ("masse",)),
    "profond": (True, ("profondeur",)), "profonde": (True, ("profondeur",)),
    "petit": (False, ("superficie", "population", "aire")), "petite": (False, ("superficie", "population", "aire")),
    "court": (False, ("longueur",)), "courte": (False, ("longueur",)),
    "bas": (False, ("altitude", "hauteur")), "basse": (False, ("altitude", "hauteur")),
    "leger": (False, ("masse",)), "legere": (False, ("masse",)),
}
_CMP_RE = re.compile(r"\b(plus|moins)\s+(\w+)\s+(?:que|qu)\s+(.+)$")


def _to_float(v):
    s = str(v)
    for ch in (" ", "\xa0", " "):
        s = s.replace(ch, "")
    s = s.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    try:
        return float(m.group(0)) if m else None
    except Exception:
        return None


def _nettoie_sujet(s: str) -> str:
    """Extrait l'entité-sujet d'un fragment (« la france est elle » -> « france »)."""
    s = re.sub(r"^(?:est[- ]ce que |qui |que |quel |quelle |dis moi si |sais tu si )", "", s).strip()
    s = _strip_det(s)
    s = re.sub(r"\b(?:est|es|sont|etait|etaient|elle|il|ils|elles|ce|t|a|y)\b", " ", s)
    return " ".join(s.split()).strip()


def resout_comparaison(question: str):
    """A2 : compare deux entités sur une dimension numérique -> STRING ou None. Voir bloc ci-dessus."""
    qn = normalise(question)
    m = _CMP_RE.search(qn)
    if not m:
        return None
    pm, adj, ypart = m.group(1), m.group(2), m.group(3)
    if adj not in _CMP_ATTR:
        return None
    sens_haut, attrs = _CMP_ATTR[adj]             # sens_haut=True si « plus <adj> » veut une valeur SUPÉRIEURE
    if pm == "moins":
        sens_haut = not sens_haut
    y = _strip_det(ypart.strip().strip(" ?.!"))
    x = _nettoie_sujet(qn[:m.start()])
    if len(x) < 2 or len(y) < 2:
        return None
    verdicts = []                                  # (rel, vx, vy)
    for attr in attrs:
        for rel in _registre():
            if not rel.split("_")[0] == attr:
                continue
            fx = lecteur.LECTEUR.cherche(rel, x)
            fy = lecteur.LECTEUR.cherche(rel, y)
            if fx is None or fy is None:
                continue
            vx, vy = _to_float(fx.valeur), _to_float(fy.valeur)
            if vx is None or vy is None or vx == vy:
                continue
            verdicts.append((rel, vx, vy))
    if not verdicts:
        return None                                # une des entités manque (ou égalité) -> HORS honnête
    directions = {(vx > vy) for (_r, vx, vy) in verdicts}
    if len(directions) != 1:
        return None                                # attributs CONTRADICTOIRES -> HORS (ambigu)
    rel, vx, vy = verdicts[0]
    x_gagne = (vx > vy)
    oui = (x_gagne == sens_haut)
    cx, cy = x.capitalize(), y.capitalize()
    comp = adj if oui else ("plus petit" if sens_haut else "plus grand")
    # Réponse honnête, orientée sur le verdict demandé
    plus_grand, v1, v2 = (cx, vx, vy) if x_gagne else (cy, vy, vx)
    return (f"{'Oui' if oui else 'Non'} — {cx} ({_fmt_nb(vx)}) vs {cy} ({_fmt_nb(vy)}) ; "
            f"{plus_grand} a la plus grande valeur ({_label_fiche(rel)}).")


def _fmt_nb(v: float) -> str:
    return str(int(v)) if v == int(v) else str(v)


# ————————————————————————————————— FICHE ENTITÉ (synthèse, longueur VARIABLE) —————————————————————————————————
# « parle-moi de la France » / « qu'est-ce que X » -> agréger TOUS les faits vérifiés où X est CLÉ en une synthèse.
# SOUND : uniquement des faits réels (`cherche` existe), jamais d'invention ; entité inconnue -> None (HORS).
# Longueur VARIABLE (directive Yohan) : « parle-moi de / décris / tout sur » = LONG (tout) ; « qu'est-ce que /
# c'est quoi / qui est » = COURT (faits-clés). Substrat du moteur invention : dire précisément CE QU'ON SAIT sur X.
_FICHE_LONG = ("parle moi de la", "parle moi de l", "parle moi du", "parle moi des", "parle moi de",
               "dis moi tout sur", "decris moi", "decris", "description de", "renseigne moi sur",
               "presente moi", "que sais tu sur", "que sais tu de", "informations sur", "infos sur", "info sur")
_FICHE_COURT = ("qu est ce que la", "qu est ce que le", "qu est ce que les", "qu est ce que l", "qu est ce que",
                "qu est ce qu", "c est quoi la", "c est quoi le", "c est quoi", "qui est", "qui etait")
# Relations à valeur peu lisible (codes/identifiants techniques) -> exclues de la fiche.
_FICHE_EXCLUS = ("code_", "mmsi", "imo_", "freebase", "glottolog", "babelnet", "iso_numerique", "aat_", "j9u",
                 "lccn", "ndl", "nkc", "gnd", "bnf", "linguasphere", "aiatsis", "endangered", "unesco")
# Premiers-tokens prioritaires (affichés en tête de fiche). Le reste suit, ordre alphabétique.
_FICHE_PRIO = {t: i for i, t in enumerate(
    "definition concept continent capitale pays monnaie langue population superficie point altitude hauteur "
    "longueur genre categorie numero masse taxon".split())}


def _strip_det(s: str) -> str:
    return re.sub(r"^(?:la |le |les |l |du |de la |de l |des |de |un |une |mon |ma |mes )", "", s).strip()


def _label_fiche(rel: str) -> str:
    return rel.replace("_", " ")


_REL_ELEM_CACHE = None


def _relations_du_type(ensemble_ref: set) -> list:
    """Relations dont les ENTITÉS (clés) appartiennent (≥80 %) à `ensemble_ref` — sert à n'agréger, dans une fiche,
    que des relations du MÊME type d'entité (pas de mélange d'homonymes : pays vs personne vs fleuve)."""
    out = []
    if not ensemble_ref:
        return out
    for rel in _registre():
        if any(x in rel for x in _FICHE_EXCLUS):
            continue
        t = lecteur.LECTEUR.tables.get(rel)
        ks = list(islice(t.keys(), 300)) if t is not None else []   # islice : NE matérialise pas 1M+ clés (perf)
        if ks and sum(1 for k in ks if k in ensemble_ref) >= 0.8 * len(ks):
            out.append(rel)
    return out


def _relations_element() -> list:
    global _REL_ELEM_CACHE
    if _REL_ELEM_CACHE is None:
        t = lecteur.LECTEUR.tables.get("numero_atomique")
        _REL_ELEM_CACHE = _relations_du_type(set(t.keys()) if t is not None else set())
    return _REL_ELEM_CACHE


_VILLE_CACHE = None
_REL_VILLE_CACHE = None
_ASTRE_CACHE = None
_REL_ASTRE_CACHE = None


def _ensemble_ville() -> set:
    """Référence de noms de VILLES = clés de `pays_ville` (entité=ville). Sert de pivot anti-homonyme :
    « Paris/Lyon » sont des villes -> fiche urbaine cohérente, jamais le homonyme lexical (« nom de famille »)."""
    global _VILLE_CACHE
    if _VILLE_CACHE is None:
        t = lecteur.LECTEUR.tables.get("pays_ville")
        _VILLE_CACHE = set(t.keys()) if t is not None else set()
    return _VILLE_CACHE


def _relations_ville() -> list:
    global _REL_VILLE_CACHE
    if _REL_VILLE_CACHE is None:
        _REL_VILLE_CACHE = _relations_du_type(_ensemble_ville())
    return _REL_VILLE_CACHE


def _ensemble_astre() -> set:
    """Référence de noms d'ASTRES/PLANÈTES = clés de `type_planete`. Pivot anti-homonyme : « Jupiter » est une
    planète -> fiche astronomique cohérente, jamais le homonyme lexical (« exoplanète similaire à jupiter »)."""
    global _ASTRE_CACHE
    if _ASTRE_CACHE is None:
        t = lecteur.LECTEUR.tables.get("type_planete")
        _ASTRE_CACHE = set(t.keys()) if t is not None else set()
    return _ASTRE_CACHE


def _relations_astre() -> list:
    global _REL_ASTRE_CACHE
    if _REL_ASTRE_CACHE is None:
        _REL_ASTRE_CACHE = _relations_du_type(_ensemble_astre())
    return _REL_ASTRE_CACHE


def _rels_fiche_pour(ent: str):
    """Relations à agréger pour la fiche de `ent`, selon son TYPE-PIVOT (cohérence anti-homonyme). None si l'entité
    n'est pas un pivot reconnu (pays / élément / ville / astre) -> pas de fiche riche (on évite de mélanger des
    homonymes ; voir aussi le verrou anti-fallback-lexical dans `resout_fiche`).
    PRIORITÉ DATA-DÉRIVÉE (2026-07-02) : l'ex-ordre codé en dur (pays > élément > astre > ville) est remplacé par
    la RICHESSE MESURÉE — le type retenu est celui dont le PLUS de relations connaissent `ent` (mesure M4 :
    mercure = 15 relations-éléments vs 9 relations-astres -> fiche élément ; jupiter = 10 astres vs 1 ville ->
    fiche astre ; luxembourg = ~24 pays vs ~3 villes -> fiche pays). Égalité -> le registre le plus PETIT
    (type le plus spécifique : astres 8 < éléments 118 < pays ~249 < villes ~10k)."""
    candidats = []                              # (richesse, taille_registre, relations_du_type)
    for ens, rels_type in ((_ensemble_pays(), _relations_pays),
                           (_ensemble_element(), _relations_element),
                           (_ensemble_astre(), _relations_astre),
                           (_ensemble_ville(), _relations_ville)):
        if ent in ens:
            rels = rels_type()
            richesse = sum(1 for rel in rels if lecteur.LECTEUR.cherche(rel, ent) is not None)
            candidats.append((richesse, len(ens), rels))
    if not candidats:
        return None
    candidats.sort(key=lambda c: (-c[0], c[1]))  # richesse max, puis registre le plus petit
    return candidats[0][2]


def resout_fiche(question: str):
    """Synthèse des faits vérifiés sur une entité (longueur variable) -> STRING ou None. SOUND anti-homonyme : fiche
    RICHE seulement pour un type-pivot cohérent (pays/élément) ; sinon fallback = la DÉFINITION seule (un fait, pas
    d'agrégation). Jamais de mélange d'entités homonymes (cf. bloc ci-dessus)."""
    qn = normalise(question).strip(" ?.!")
    ent, longue = None, None
    for marq in _FICHE_LONG:
        if qn.startswith(marq + " "):
            ent, longue = qn[len(marq):].strip(), True
            break
    if ent is None:
        for marq in _FICHE_COURT:
            if qn.startswith(marq + " "):
                ent, longue = qn[len(marq):].strip(), False
                break
    if not ent:
        return None
    ent = _strip_det(ent)
    if len(ent) < 2:
        return None
    rels = _rels_fiche_pour(ent)
    if rels is not None:                          # entité d'un TYPE-PIVOT cohérent -> fiche riche
        faits = []
        for rel in rels:
            if any(x in rel for x in _FICHE_EXCLUS):   # retire les codes/identifiants techniques (lisibilité)
                continue
            f = lecteur.LECTEUR.cherche(rel, ent)
            if f is not None:
                faits.append((rel, f.valeur))
        if faits:
            faits.sort(key=lambda rv: (_FICHE_PRIO.get(rv[0].split("_")[0], 99), rv[0]))
            if not longue:
                faits = faits[:4]
            parts = [f"{_label_fiche(rel)} : {val}" for rel, val in faits]
            return f"{ent.capitalize()} — " + " ; ".join(parts)
        # TYPE-PIVOT reconnu mais aucun fait exploitable -> HORS honnête. On NE retombe JAMAIS sur le fallback
        # lexical : « Paris » la ville ne doit pas devenir « nom de famille », « Jupiter » la planète pas un
        # homonyme. L'entité est typée (ville/astre/pays/élément) -> la définition lexicale serait un FAUX+.
        return None
    # FALLBACK SOUND (entité NON typée) : la DÉFINITION lexicale FR seule (un fait cohérent, aucun homonyme typé).
    for rel in ("definition_nom", "definition_verbe", "definition_adjectif"):
        f = lecteur.LECTEUR.cherche(rel, ent)
        if f is not None:
            return f"{ent.capitalize()} — {f.valeur}"
    return None                                  # rien de cohérent -> HORS honnête


def resout_nl_generique(question: str):
    """Comprend une question FORWARD sur n'importe quelle relation. Renvoie (VERIFIE, fait, correction) ou
    (HORS, None, None). `correction` = entité corrigée (str) si une faute a été rattrapée, sinon None."""
    qn = normalise(question)
    # ROBUSTESSE AU BRUIT : retire les locutions puis les mots de remplissage (« euh/stp/voila/au fait »…) avant tout
    # parsing. FILLERS retirés SEULEMENT EN DÉBUT/FIN (#115) — salutation/politesse — JAMAIS au MILIEU : un filler au
    # milieu fait souvent partie d'un TITRE (« langue de SALUT l'artiste » [film fr.] -> sans garde, « salut » strippé
    # -> « l artiste » = AUTRE film russe = FAUX). L'hypothèse « retirer un filler ne peut que faire HORS » est FAUSSE
    # quand le résidu est une autre entité valide -> on ne dérabotte qu'aux bords (le bruit conversationnel y est).
    for loc in _FILLERS_LOCUTIONS:
        qn = re.sub(loc, " ", qn)
    _ftoks = qn.split()
    while _ftoks and _ftoks[0] in _FILLERS:
        _ftoks.pop(0)
    while _ftoks and _ftoks[-1] in _FILLERS:
        _ftoks.pop()
    qn = " ".join(_ftoks)
    if _est_superlatif(qn):              # GARDE : un superlatif n'est jamais un lookup par clé -> HORS (cf. ci-dessus)
        return (HORS, None, None)
    # GARDE VÉRIFICATION-DE-NOMBRE (FAUX=0 vécu 2026-07-08) : « est-ce que 2024 est une année bissextile ? » ->
    # le résolveur ignorait le NOMBRE et servait l'année du FILM « Année bissextile » (2010). Une question
    # « est-ce que <nombre> est … » demande de VÉRIFIER une propriété du nombre — un lookup de valeur qui
    # écarte ce nombre répond à une AUTRE question -> HORS (les routes calcul, en aval, savent trancher).
    if re.search(r"\best[- ]ce\s+qu[e']\s*\d+([.,]\d+)?\s+(?:est|soit|sera|serait|c\s*est)\b", qn) \
            or re.search(r"^\s*\d+([.,]\d+)?\s+(?:est|sera|serait)[- ](?:il|elle|ce)\b", qn):
        return (HORS, None, None)
    # GARDE CADRE-FICHE : « parle-moi de X », « décris-moi X »… sont des frames de FICHE, jamais un lookup d'attribut.
    # Le verbe du cadre (« parle ») coïncide sinon avec un token de relation (`langue_parlee_personne`) et accroche
    # un homonyme-personne (« parle-moi de Lyon » -> « anglais » via P1412 = FAUX+). On laisse `resout_fiche` traiter.
    # NB : seuls les frames LONGS sont bloqués ; les courts (« c'est quoi la langue parlée au Mexique ») restent actifs.
    if any(qn.startswith(m + " ") for m in _FICHE_LONG):
        return (HORS, None, None)
    # GARDE REVERSE (#95/#96) : une requête INVERSE nomme la VALEUR et cherche l'ENTITÉ (« quel pays A POUR capitale
    # New York », « le pays DONT la capitale est New York », « New York EST LA capitale DE QUEL pays », « DE QUOI New
    # York est-elle la capitale »). Le forward résoudrait <attr>[New York]=Albany (capitale de l'ÉTAT de NY) -> FAUX
    # (Albany n'est ni un pays ni la réponse). On laisse l'inverse à `_liste_inverse` ; le forward s'abstient. Aucun
    # gabarit FORWARD n'emploie ces tournures (« quelle est la capitale du Japon » n'a ni « dont » ni « de quoi »…).
    if re.search(r"\ba pour\b|\ba comme\b|\bdont\b|\bde quoi\b|\bde qui\b"
                 r"|\best\s+(?:la|le|l|les)\s+\w+\s+de\s+(?:quel|quelle|quels|quelles|quoi|qui)\b", qn):
        return (HORS, None, None)
    qtoks = set(qn.split())
    demandes = set(qtoks)
    vocab = _vocab_rel()
    # La FUZZY d'attribut (« cpaitale »->« capitale ») ne s'applique qu'aux mots de la RÉGION-ATTRIBUT (avant la 1re
    # préposition) — JAMAIS à une ENTITÉ après « de » (#118 : « nom de PERSE » -> « perse » corrigé en « pere » ->
    # pere_divinite[perse]=Océan = FAUX). L'attribut est en tête ; l'entité (après « de ») n'est pas un mot-attribut.
    _mp = re.search(rf"\b{_PREP}\b", qn)
    _attr_toks = set((qn[:_mp.start()] if _mp else qn).split())
    for w in qtoks:
        if w.endswith(("s", "x")):
            demandes.add(w[:-1])
        demandes.add(w + "s")
        if len(w) >= 5 and w not in vocab and w in _attr_toks:   # FAUTE sur le mot-ATTRIBUT uniquement
            corr = _corrige_vers(w, vocab)
            if corr:
                demandes.add(corr)
    # ALIAS VERBE->ATTRIBUT général (« écrit »->« auteur »…) DÉSACTIVÉ : exposait 2 FAUX+ (fuzzy d'entité abusif ;
    # mauvaise relation « tour eiffel construite par »->France). À REPRENDRE avec garde anti-fuzzy + désambiguïsation.
    # ALIAS VERBE TEMPOREL testé (T3 #73) puis RETIRÉ : SOUND (le garde « temps requis » tuait le FAUX « qui a créé X »
    # ->année), MAIS sans BÉNÉFICE réel — le phrasing verbe (« l'OTAN a-t-elle été créée ») a l'entité EN TÊTE (pas
    # après préposition) -> l'extraction d'entité échoue -> HORS même pour une clé propre (otan=1999). Gap verbe-temporel
    # = multi-facteur (alias + extraction entité-en-tête + clés propres T8/T6), faible payoff. L'explicite « année de
    # création de X » marche déjà. Pas de code mort dans le résolveur cœur.
    entite_prep = _extrait_entite(qn)             # stratégie 1 : queue après préposition (« … du japon »)
    md = list(re.finditer(r"\b(?:le|la|les|l|un|une|des)\s+(.+)$", qn))   # stratégie : après le dernier déterminant
    entite_det = md[-1].group(1).strip() if md else ""                    # (« cause LE paludisme » -> « paludisme »)
    toks_q = qn.split()                           # stratégie : tête après un CLASSIFIEUR (« mot TABLE », « verbe MANGER »)
    entite_classif = ""
    classif_ling = False                          # le classifieur désigne-t-il un MOT de langue ? (désambiguïse vers lexical)
    for k in range(len(toks_q) - 1, -1, -1):
        if toks_q[k] in _CLASSIFIEURS:
            entite_classif = " ".join(toks_q[k + 1:]).strip()
            classif_ling = toks_q[k] in _CLASSIF_LINGUISTIQUES
            break
    # Le candidat lexème « X (français) » n'est légitime QUE si la question demande une PROPRIÉTÉ lexicale explicite
    # (« GENRE/CATÉGORIE/DÉFINITION du mot X »). Sinon « quel est le MOT magique » accrocherait « magique (français) »
    # -> un genre, alors que ce n'est pas une demande lexicale (FAUX+). « mot » seul ne suffit pas.
    attr_lex = bool(qtoks & _ATTRS_LEXICAUX)
    fuzzy_ok = not _POSSESSIFS_RE.search(qn)       # « de mon chien » -> littéral : pas de correction floue
    # relations candidates = un token de NOM (≥4, non générique) est demandé dans la question. Les plus
    # SPÉCIFIQUES d'abord (plus de tokens de nom reconnus = relation mieux désignée).
    candidats = []
    for rel in _registre():
        toks = [t for t in rel.split("_") if len(t) >= 3 and t not in _GENERIQUES]   # ≥3 : « cri », « lac », « ile »…
        score = sum(1 for t in toks if t in demandes)
        if not score:
            continue
        # GARDE anti-coïncidence TYPE-ENTITÉ : si l'ATTRIBUT (1er token) est GÉNÉRIQUE (« pays », « code », « nom »,
        # « type », « categorie »…), la relation n'est désignée QUE par son TYPE (« tour » de `pays_tour`) — or ce
        # type fait souvent partie de l'ENTITÉ (« la TOUR eiffel ») et non de l'attribut demandé. On n'accepte alors
        # la relation QUE si l'attribut générique est EXPLICITEMENT dans la question (« quel PAYS de … »). Sinon,
        # « qui a construit la tour eiffel » accrocherait `pays_tour` et répondrait le PAYS (« France ») = FAUX+.
        attr = rel.split("_")[0]
        if attr in _GENERIQUES and attr not in qtoks:
            continue
        # GARDE anti-coïncidence ENTITÉ-TYPE (attribut NON générique) : si l'attribut-tête réel de la relation n'est
        # PAS demandé, la relation n'est accrochée que par son token d'ENTITÉ-TYPE — souvent un mot que l'utilisateur
        # a répété (« la MONTAGNE de la MONTAGNE » -> `subdivision_montagne` -> Ontario) ou qui qualifie l'entité
        # (« capitale de l'OCÉAN Atlantique » -> `rang_ocean` -> « 2 »). On exige que l'attribut réel soit demandé ;
        # sinon c'est une coïncidence -> on écarte (FAUX=0 prime sur la couverture). Le cas attribut GÉNÉRIQUE est
        # déjà traité ci-dessus (il faut alors que le générique soit explicite).
        if attr not in _GENERIQUES and attr not in demandes:
            continue
        # GARDE QUANTITÉ vs DATE (FAUX vécu 2026-07-08) : « combien de secondes dans une année » accrochait
        # `annee_publication_oeuvre` (token « année ») et servait 1939 (une œuvre !). Une question « combien … »
        # attend une QUANTITÉ — jamais une relation d'année/date (qui répond une date, pas un compte). Les
        # relations de compte réel (population…) ne commencent pas par annee_/date_ et restent servies.
        if "combien" in qtoks and (rel.startswith("annee_") or rel.startswith("date_")):
            continue
        candidats.append((score, rel))
    candidats.sort(key=lambda sr: (-sr[0], sr[1]))

    def _resout(rel):
        """Tente de résoudre l'entité pour `rel` (plusieurs candidats + fuzzy). Renvoie (fait, correction) ou None."""
        rtoks = set(rel.split("_"))
        mots = [t for t in qn.split() if t not in rtoks and t not in _STOP_ENTITE]
        # Candidats d'ENTITÉ, du plus probable au plus restreint : queue-après-préposition, tout le reste, puis
        # les suffixes (2 derniers mots, dernier mot seul) — pour les phrases SANS préposition propre
        # (« agent cause le PALUDISME », « la lettre A »). Dédup en gardant l'ordre.
        # NOTE LOOP : « genre du mot TABLE » nécessiterait d'isoler « table » (tête du syntagme après préposition),
        # MAIS cela réintroduit un FAUX+ (« le ciel est bleu » -> arc-en-ciel). Candidat « tete_prep » RETIRÉ pour
        # préserver FAUX=0. À reprendre proprement (cf. REPRISE) : isoler la tête seulement si la relation est
        # vraiment désignée (token-attribut en position d'attribut), pas par coïncidence.
        cands, vus = [], set()
        # entite_classif (tête après « le mot/verbe/… X ») EN TÊTE : non-vide SEULEMENT s'il y a un classifieur,
        # et dans ce cas c'est l'entité exacte (« chien », « table ») -> match exact avant tout fuzzy, ce qui évite
        # un message de correction trompeur (« mot chien » fuzzy-corrigé en « mort chien »). Aucun effet sans classifieur.
        # CLÉ LEXÈME « lemme (langue) » : les tables ingérées (genre_grammatical_mot…) indexent « mère (français) »,
        # pas « mère » nu -> pour un classifieur LINGUISTIQUE on essaie aussi « X (français) » (MATCH EXACT, donc
        # sound : si la clé n'existe pas -> rien ; sur une relation non-lexicale -> aucune clé -> inoffensif).
        classif_fr = f"{entite_classif} (français)" if (classif_ling and entite_classif and attr_lex) else ""
        for c in (entite_classif, classif_fr, entite_prep, entite_det, " ".join(mots), " ".join(mots[-2:]) if mots else ""):
            # GARDE COÏNCIDENCE ENTITÉ=VOCAB-RELATION : un candidat-entité dont TOUS les tokens sont des tokens du
            # NOM de la relation n'est pas une vraie entité distincte — c'est le vocabulaire de la relation réutilisé
            # (« synonyme DE MAISON » : « maison » = clé-œuvre du relation `maison_edition_oeuvre_ecrite` -> éditeur
            # « Syros » = FAUX+). On l'écarte : la relation n'est légitime que désignée par une entité HORS de son nom.
            if c and c not in vus and not all(t in rtoks for t in c.split()):
                vus.add(c)
                cands.append(c)
        # NB #114 REVERTÉ : un pré-check EXACT sur la queue brute (« la lune », « mon chien ») matchait des clés
        # coïncidentes -> 8 pièges de soundness cassés. Le cas niche « a hmao » (langue « A-Hmao », ~2 clés « a X » par
        # relation) reste une CORRECTION DIVULGUÉE (« en comprenant hmar »), pas un FAUX silencieux -> acceptable.
        for ent in cands:
            if not ent:
                continue
            f = lecteur.LECTEUR.cherche(rel, ent)
            if f is not None:
                return (f, None, ent)             # 3e élément = CLÉ effectivement matchée (pour garde inter-palier)
            corr = corrige(rel, ent) if fuzzy_ok else None     # tolérance aux fautes (sauf entité possessive)
            if corr and _entite_exacte_dans_famille(ent, rel):
                corr = None                       # #113 : `ent` est un VRAI lieu ailleurs (« cap blanc »=France) -> ne PAS
                #                                   corriger en un voisin (« cap blanco »=USA) ; cette relation n'a rien.
            if corr:
                f = lecteur.LECTEUR.cherche(rel, corr[0])
                if f is not None:
                    return (f, corr[0], corr[0])
        return None

    # On traite les candidats par PALIER DE SCORE décroissant (mieux la question désigne la relation, mieux
    # c'est). GARDE ANTI-AMBIGUÏTÉ : si, au meilleur palier qui répond, DEUX relations distinctes répondent
    # (ex. « atomique du fer » -> numero_atomique ET masse_atomique), on NE CHOISIT PAS au hasard -> HORS.
    i, n = 0, len(candidats)
    while i < n:
        score = candidats[i][0]
        palier = []
        while i < n and candidats[i][0] == score:
            palier.append(candidats[i][1])
            i += 1
        repondants = []
        for rel in palier:
            r = _resout(rel)
            if r is not None:
                repondants.append((rel, r[0], r[1], r[2]))
        # DÉSAMBIGUÏSATION LEXICALE : « genre/définition du MOT X » désigne un mot de langue. On ne garde QUE les
        # répondants à SOURCE lexicale (Wiktionnaire/kaikki/…) — sinon « mère »->fuzzy « meru »->film passerait
        # quand genre_grammatical n'a pas répondu (accent). 0 lexical -> HORS honnête, JAMAIS un fait non-lexical.
        if classif_ling and entite_classif:
            repondants = [(rel, f, c, cl) for (rel, f, c, cl) in repondants if _source_lexicale(f)]
        distinctes = {rel for (rel, _f, _c, _cl) in repondants}
        if len(distinctes) == 1:
            # GARDE AMBIGUÏTÉ PAR FAMILLE D'ATTRIBUT (T3 #79/#80) : clé NUE partagée par plusieurs types d'une même
            # famille (« pays de château fort » château=Tunisie / volcan=France) -> abstenir sauf token discriminant.
            rel0, f, c, cle0 = repondants[0]
            if (_ambigu_famille(rel0, cle0, normalise(str(f.valeur)), qtoks) or _valeur_echo_attribut(rel0, f.valeur, qtoks)
                    or _pivot_homonyme_oeuvre(rel0, cle0)):
                return (HORS, None, None)
            # GARDE ATTRIBUT-PRIMAIRE (#116) : le gagnant solitaire a pu gagner via des mots de l'ENTITÉ coïncidant
            # avec son nom (« materiau de PHARE de l'ÎLE Machias » : `phare_sur_ile` gagne via « phare »+« ile » et
            # répond l'ÎLE, pas le matériau). Si un AUTRE candidat a son attribut-tête PLUS TÔT dans la question (= la
            # vraie POSITION-ATTRIBUT, juste après « quel est le ») et résout une valeur DIFFÉRENTE, c'est LUI que
            # l'utilisateur désigne -> ambigu -> HORS prudent. Sound : « capitale du Japon » n'a pas d'attribut plus tôt.
            qlist = qn.split()
            def _pos(r):
                h = r.split("_")[0]
                return qlist.index(h) if h in qlist else 10 ** 6
            pos0 = _pos(rel0)
            for _sc, rel in candidats:
                if rel != rel0 and _pos(rel) < pos0:
                    rr = _resout(rel)
                    if rr is not None and normalise(str(rr[0].valeur)) != normalise(str(f.valeur)):
                        return (HORS, None, None)
            return (VERIFIE, f, c)
        if len(distinctes) >= 2:
            # CONSENSUS : si TOUTES les relations répondantes donnent la MÊME valeur, ce n'est PAS une ambiguïté —
            # relations REDONDANTES (« longueur_cours_eau » et « longueur_fleuve » ont Volga=3530000) -> on renvoie la
            # valeur consensuelle. Sound (FAUX=0) : valeurs identiques = aucune incertitude sur la réponse, quel que
            # soit l'attribut visé. Débloque ~30 k cours d'eau (overlap cours_eau/fleuve) + tout doublon concordant.
            if len({normalise(str(f.valeur)) for (_rel, f, _c, _cl) in repondants}) == 1:
                rel0, f, c, cle0 = repondants[0]
                # même garde famille : le consensus du palier de tête peut masquer un frère de famille à SCORE 0 qui
                # donne une valeur différente (« annee de opération harpoon » : opération 2002 vs bataille 1942).
                if (_ambigu_famille(rel0, cle0, normalise(str(f.valeur)), qtoks) or _valeur_echo_attribut(rel0, f.valeur, qtoks)
                        or _pivot_homonyme_oeuvre(rel0, cle0)):
                    return (HORS, None, None)
                return (VERIFIE, f, c)
            # DÉPARTAGE par ATTRIBUT NOMMÉ : si EXACTEMENT une relation répondante a son attribut principal
            # (1er token, même générique : « pays », « numero »…) explicitement nommé dans la question, c'est CELLE
            # que l'utilisateur désigne (« quel PAYS de l'athlète X » -> pays_sportif_athlete, pas sport_athlete ;
            # « NUMERO atomique du fer » -> numero_atomique, pas masse_atomique). Sound : cherche() reste exact, on
            # ne fait que choisir la relation dont l'attribut EXACT est demandé. Sinon (0 ou ≥2) -> HORS prudent.
            prefere = [(rel, f, c, cl) for (rel, f, c, cl) in repondants if rel.split("_")[0] in qtoks]
            if len({rel for (rel, _f, _c, _cl) in prefere}) == 1:
                _rel, f, c, _cl = prefere[0]
                if _valeur_echo_attribut(_rel, f.valeur, qtoks) or _pivot_homonyme_oeuvre(_rel, _cl):
                    return (HORS, None, None)
                return (VERIFIE, f, c)
            return (HORS, None, None)         # ambigu : plusieurs relations également désignées répondent
        # 0 réponse à ce palier -> palier de score inférieur
    return (HORS, None, None)


# ————————————————————————————————— LISTAGE (value-ancré + list-all) —————————————————————————————————
_PAYS_CACHE = None
_REL_PAYS_CACHE = None
_REV_MEM: dict = {}
_INTENT_LISTE = frozenset("cite citez liste listez nomme nommez donne donnez enumere enumerez".split())
_TYPES_PAYS = frozenset("pays etat etats nation nations".split())


def _ensemble_pays() -> set:
    """Référence de noms de PAYS = clés de la relation `continent` (entité=pays). Sert à reconnaître les
    relations dont les entités SONT des pays (pour « quels pays de … »)."""
    global _PAYS_CACHE
    if _PAYS_CACHE is None:
        t = lecteur.LECTEUR.tables.get("continent")
        _PAYS_CACHE = set(t.keys()) if t is not None else set()
    return _PAYS_CACHE


def _relations_pays() -> list:
    """Relations dont les ENTITÉS sont (en grande majorité) des pays — déduit des données, pas codé en dur."""
    global _REL_PAYS_CACHE
    if _REL_PAYS_CACHE is None:
        pays, out = _ensemble_pays(), []
        if pays:
            for rel in _registre():
                t = lecteur.LECTEUR.tables.get(rel)
                ech = list(islice(t.keys(), 300)) if t is not None else []   # islice : pas de matérialisation 1M+ clés
                if ech and sum(1 for k in ech if k in pays) >= 0.8 * len(ech):
                    out.append(rel)
        _REL_PAYS_CACHE = out
    return _REL_PAYS_CACHE


def _reverse_mem(rel: str) -> dict:
    """Index inverse VALEUR -> (affichée, [entités]) d'une relation, en mémoire (depuis le lecteur), caché."""
    if rel in _REV_MEM:
        return _REV_MEM[rel]
    d: dict = {}
    t = lecteur.LECTEUR.tables.get(rel)
    if t is not None:
        for k, f in t.items():
            d.setdefault(normalise(f.valeur), [f.valeur, []])[1].append(k)
    _REV_MEM[rel] = {vn: (disp, sorted(set(ents))) for vn, (disp, ents) in d.items()}
    return _REV_MEM[rel]


_NB_DEMANDE = {"deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10}


def _nombre_demande(qn: str, qtoks: set):
    """Nombre d'exemples DEMANDÉ (« cite-moi TROIS pays… », « donne 5 fleuves ») ou None. Servir la liste
    entière quand on demande trois, c'est répondre à côté (vécu 2026-07-08 : 53 pays pour « trois »)."""
    for w, n in _NB_DEMANDE.items():
        if w in qtoks:
            return n
    m = re.search(r"\b([1-9]\d?)\b", qn)
    return int(m.group(1)) if m else None


def _format_liste(label: str, contexte: str, items: list, source: str, demande: int | None = None) -> str:
    if demande and 1 <= demande < len(items):
        montre = ", ".join(items[:demande])
        ctx = f" ({contexte})" if contexte else ""
        return f"{label}{ctx} : {montre} — en voici {demande} parmi {len(items)}."
    cap = 15
    montre = ", ".join(items[:cap])
    reste = f" … (échantillon ; {len(items) - cap} autres)" if len(items) > cap else ""
    ctx = f" ({contexte}, {len(items)})" if contexte else f" ({len(items)})"
    return f"{label}{ctx} : {montre}{reste}"     # `source` conservée en interne (FAUX=0), non affichée (préférence Yohan)


def resout_liste(question: str):
    """Requêtes de LISTAGE -> chaîne formatée, ou None. (A) « (les) pays de/en <valeur> » -> entités d'une
    relation à clés-pays pour cette valeur (« pays de l'europe »). (B) « cite/liste un <X> » -> valeurs
    distinctes d'une relation désignée par son nom (« cite un continent »). Sound : entités/valeurs réelles ou None."""
    qn = normalise(question)
    qtoks = set(qn.split())

    # (A) value-ancré : « quels PAYS de l'<valeur> ? ». GARDE : exiger une vraie INTENTION DE LISTE (pluriel/cite) —
    # « quel EST le pays de X » est une demande d'UN attribut (singulier), PAS un listage (sinon « est » est pris
    # comme valeur-ancre -> code Estonie -> FAUX+ « pays de l'athlète Usain Bolt » -> estonie).
    veut_liste = bool(qtoks & {"quels", "quelles", "combien"} or _INTENT_LISTE & qtoks
                      or "les pays" in qn or "des pays" in qn)
    if (_TYPES_PAYS & qtoks) and veut_liste:
        meilleur = None
        for rel in _relations_pays():
            for vn, (disp, ents) in _reverse_mem(rel).items():
                if len(vn) >= 4 and vn not in _GENERIQUES and re.search(r"\b" + re.escape(vn) + r"\b", qn):
                    if meilleur is None or len(vn) > len(meilleur[1]):
                        meilleur = (rel, vn, disp, ents)
        if meilleur and meilleur[3]:
            rel, _vn, disp, ents = meilleur
            return _format_liste("Pays", disp, ents, rel, demande=_nombre_demande(qn, qtoks))

    # (B) list-all : « cite/liste les <X> » -> valeurs distinctes de la relation désignée par son nom.
    if _INTENT_LISTE & qtoks or "quels sont" in qn or "quelles sont" in qn:
        for rel in _registre():
            for tk in rel.split("_"):
                if len(tk) >= 4 and tk not in _GENERIQUES and (tk in qtoks or tk + "s" in qtoks):
                    valeurs = sorted({disp for (disp, _e) in _reverse_mem(rel).values()})
                    if valeurs:
                        rep = _format_liste(tk.capitalize(), "", valeurs, rel, demande=_nombre_demande(qn, qtoks))
                        # QUALIFICATIF NON RÉSOLU (FAUX=0 vécu 2026-07-08) : « un exemple de mammifère MARIN »
                        # servait TOUS les ordres, chauves-souris comprises — le qualificatif était ignoré EN
                        # SILENCE. On ne sait pas le filtrer -> on le DIT (liste honnêtement non filtrée).
                        mq = re.search(r"\b" + re.escape(tk) + r"s?\b\s+([a-zà-ÿ-]{4,})", qn)
                        if mq and mq.group(1) not in _GENERIQUES and mq.group(1) not in rel.split("_") \
                                and mq.group(1) not in ("existants", "existantes", "connus", "connues",
                                                        "possibles", "differents", "differentes"):
                            rep += (" ⚠ Je ne sais pas filtrer « %s » — c'est la liste NON filtrée, à toi de "
                                    "trier." % mq.group(1))
                        return rep
    return None


def repond_floue(question: str):
    """Comme `lecteur.repond_nl`, mais TOLÉRANT à une faute sur l'entité. Renvoie (statut, fait, correction) :
    correction = la forme corrigée réellement utilisée (str) ou None. (HORS, None, None) si rien de sûr.
    On ne déclenche le fuzzy QUE sur un gabarit reconnu dont l'entité exacte a échoué."""
    L = lecteur.LECTEUR
    q = normalise(question)
    fuzzy_ok = not _POSSESSIFS_RE.search(q)        # « de mon chien » -> littéral : pas de correction floue
    # « genre du MOT mère » désigne un mot de langue : un gabarit non-lexical (genre_film) ne doit PAS répondre
    # (sinon « mère » fuzzy-corrigé en « meru » -> film = FAUX). On filtre par source ; sinon on laisse l'étage
    # générique (resout_nl_generique, qui désambiguïse vers le lexical) trancher.
    ling = _classif_ling_present(q)
    for rx, relation, gi in L._GABARITS:
        m = rx.search(q)
        if not m:
            continue
        entite = m.group(gi) if gi else ""
        f = L.cherche(relation, entite)
        if f is not None:
            if ling and not _source_lexicale(f):
                continue                                          # classifieur « mot » mais relation non-lexicale
            return (VERIFIE, f, None)                             # exact -> aucune correction
        corr = corrige(relation, entite) if fuzzy_ok else None
        if corr:
            f = L.cherche(relation, corr[0])
            if f is not None:
                if ling and not _source_lexicale(f):
                    continue                                      # idem : ne pas fuzzy vers un titre non-lexical
                return (VERIFIE, f, corr[0])
    return (HORS, None, None)
