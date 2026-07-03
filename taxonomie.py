"""
TAXONOMIE DE TYPES DÉRIVÉE DES DONNÉES (service — ADDITIF, lecture seule du lecteur).

But : remplacer les LISTES DE CATÉGORIES HUMAINES de resolution.py (l'ex-`_HOMONYME_KW`, 40 mots-clés
choisis à la main) par des MESURES sur les populations de clés réelles du corpus. Pensée machine :
on juge une relation par sa POPULATION MESURÉE, jamais par un mot de son nom.

Deux signaux, mesurés sur les tables (campagne _mesure_pivots_data*.py, 2026-07-02) :
  • FRACTION D'ÉCHANTILLON  frac_ech(rel, E)  : part d'un échantillon de clés de `rel` appartenant à
    l'ensemble de référence E — « la population de rel EST de type E » (capitale, monnaie -> pays ≈ 0.9).
  • DENSITÉ DE COUVERTURE   densite(rel, E)   : part des membres de E présents comme clés de `rel` —
    « rel couvre E SYSTÉMATIQUEMENT » (annee_creation_organisation couvre 55 % des pays = les pays SONT
    des organisations ; couleur_film n'en couvre que 6 % = collisions de noms accidentelles -> homonymes).

INVARIANT FAUX=0 : ces mesures ne servent qu'à AUTORISER/BLOQUER une réponse déjà vérifiée par
`cherche()` (un garde d'abstention). Un blocage de trop = perte de couverture (mesurée, acceptée) ;
un déblocage n'est admis que si la population le prouve (frac ≥ 0.5, densité ≥ 0.3 ou source lexicale).

Les ENSEMBLES de référence sont des objets de DONNÉES (clés/valeurs de tables ingérées), pas des listes
écrites à la main. Leur rôle de « pivot saillant » (pays/capitales/astres priment leurs homonymes) est
certifié par le corpus de pièges de valide_resolution (#98-#118) — la sélection a été faite par MESURE
d'erreurs réelles, pas par catégorie a priori. `hubs()` audite que ces registres ÉMERGENT des données.
"""
from __future__ import annotations

from itertools import islice

import lecteur
from base_faits import normalise

# Seuils mesurés (campagne 2026-07-02, cf. _archive des rapports mesure_pivots*) :
#  - FRAC 0.5   : population homogène (capitale/monnaie/diametre_planete ≥ 0.89 ; homonymes ≤ 0.08).
#  - DENS 0.3   : couverture systématique (annee_creation_organisation pays 0.55, altitude_localite
#                 capitales 0.65 ; collisions accidentelles ≤ 0.12 — marge ×2.5 de part et d'autre).
#                 0.5 perdait les années de fondation de capitales (Athènes=-507, vraies) ; 0.2 colle
#                 aux collisions max (0.12-0.17) sans marge -> 0.3.
#  - MIN_E 50   : la densité n'a de sens que sur un registre assez grand (astres |E|=8 : 1 clé = 12 % ;
#                 les dieux romains couvrent 6/8 noms de planètes -> la densité y validerait des homonymes).
SEUIL_FRAC = 0.5
SEUIL_DENS = 0.3
MIN_E_DENSITE = 50
_ECH = 300           # même taille d'échantillon que resolution._relations_du_type

# Marqueurs de source LEXICALE (lus dans la DONNÉE `source` du fait — mêmes marqueurs que
# resolution._MARQUEURS_LEXICAUX) : un dictionnaire parle du MOT ; tout nom propre est aussi un mot.
_MARQUEURS_LEXICAUX = ("wiktionnaire", "wiktionary", "kaikki", "grammatical", "lexi")

_ENSEMBLES = None
_FRAC_CACHE: dict = {}
_DENS_CACHE: dict = {}
_LEX_CACHE: dict = {}


def _keys_set(rel: str) -> set:
    t = lecteur.LECTEUR.tables.get(rel)
    return set(t.keys()) if t is not None else set()


def _values_set(rel: str) -> set:
    t = lecteur.LECTEUR.tables.get(rel)
    return {normalise(str(f.valeur)) for f in t.values()} if t is not None else set()


def ensembles() -> dict:
    """Ensembles de référence typés, lus des tables (DONNÉE, pas liste manuelle). Cachés une fois."""
    global _ENSEMBLES
    if _ENSEMBLES is None:
        _ENSEMBLES = {
            "pays": _keys_set("continent"),            # entités-pays = clés de `continent`
            "capitales": _values_set("capitale"),      # capitales = VALEURS de `capitale`
            "villes": _keys_set("pays_ville"),         # villes = clés de `pays_ville`
            "astres": _keys_set("type_planete"),       # astres = clés de `type_planete`
            "elements": _keys_set("numero_atomique"),  # éléments = clés de `numero_atomique`
        }
    return _ENSEMBLES


def types_de(ent: str) -> tuple:
    """Noms des ensembles de référence contenant `ent` (déjà normalisée). () si aucun."""
    return tuple(n for n, e in ensembles().items() if ent in e)


def frac_ech(rel: str, nom: str) -> float:
    """Fraction d'un échantillon de clés de `rel` appartenant à l'ensemble `nom` (cachée)."""
    k = (rel, nom)
    if k not in _FRAC_CACHE:
        t = lecteur.LECTEUR.tables.get(rel)
        ks = list(islice(t.keys(), _ECH)) if t is not None else []
        e = ensembles().get(nom, set())
        _FRAC_CACHE[k] = (sum(1 for c in ks if c in e) / len(ks)) if ks else 0.0
    return _FRAC_CACHE[k]


def densite(rel: str, nom: str) -> float:
    """Part des membres de l'ensemble `nom` présents comme clés de `rel` (cachée). |E| lookups (≤10k)."""
    k = (rel, nom)
    if k not in _DENS_CACHE:
        t = lecteur.LECTEUR.tables.get(rel)
        e = ensembles().get(nom, set())
        _DENS_CACHE[k] = (sum(1 for p in e if p in t) / len(e)) if (t is not None and e) else 0.0
    return _DENS_CACHE[k]


def source_lexicale_rel(rel: str) -> bool:
    """La relation est-elle à source LEXICALE (dictionnaire) ? Lu dans la source du 1er fait (donnée)."""
    if rel not in _LEX_CACHE:
        t = lecteur.LECTEUR.tables.get(rel)
        res = False
        if t is not None:
            for _k, f in islice(t.items(), 1):
                src = (getattr(f, "source", "") or "").lower()
                res = any(m in src for m in _MARQUEURS_LEXICAUX)
        _LEX_CACHE[rel] = res
    return _LEX_CACHE[rel]


def population_compatible(rel: str, noms_types) -> bool:
    """La population de `rel` est-elle compatible avec AU MOINS UN des types `noms_types` d'une entité ?
    Trois voies, toutes mesurées sur les données :
      1. population homogène du type (frac_ech ≥ SEUIL_FRAC) — ex. capitale/pays ;
      2. couverture systématique du registre (densite ≥ SEUIL_DENS, registre ≥ MIN_E_DENSITE) —
         ex. altitude_localite couvre 65 % des capitales (les capitales SONT des localités) ;
      3. source lexicale — un dictionnaire parle du MOT, tout nom d'entité est aussi un mot.
    Sinon : les clés communes sont des collisions de noms accidentelles -> INCOMPATIBLE (homonymes)."""
    if source_lexicale_rel(rel):
        return True
    ens = ensembles()
    for nom in noms_types:
        if frac_ech(rel, nom) >= SEUIL_FRAC:
            return True
        if len(ens.get(nom, ())) >= MIN_E_DENSITE and densite(rel, nom) >= SEUIL_DENS:
            return True
    return False


def hubs(min_taille: int = 5, max_taille: int = 20000, seuil: float = 0.7, min_score: int = 5) -> list:
    """AUDIT : registres de types qui ÉMERGENT des données — relations dont la population de clés sert
    de population de référence à ≥ `min_score` autres relations (échantillons ⊂ clés à ≥ `seuil`).
    Certifie que les ensembles de `ensembles()` sont des réalités du corpus, pas des choix arbitraires.
    Renvoie [(score, relation, taille)] trié décroissant. Coût ~quelques secondes (usage audit/validateur)."""
    L = lecteur.LECTEUR
    rels = sorted(L.tables.keys())
    ech = {}
    for r in rels:
        t = L.tables.get(r)
        ks = list(islice(t.keys(), 60)) if t is not None else []
        if ks:
            ech[r] = ks
    out = []
    for c in rels:
        n = len(L.tables[c]) if L.tables.get(c) is not None else 0
        if not (min_taille <= n <= max_taille):
            continue
        kc = _keys_set(c)
        sc = sum(1 for r, ks in ech.items() if r != c and sum(1 for k in ks if k in kc) >= seuil * len(ks))
        if sc >= min_score:
            out.append((sc, c, n))
    out.sort(key=lambda x: (-x[0], x[1]))
    return out
