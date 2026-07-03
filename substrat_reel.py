"""
SUBSTRAT-RÉEL — découverte d'inventions par TRANSDUCTION RELATIONNELLE sur les 71 M faits (OBJECTIF FINAL, 2026-07-02).

POURQUOI (cf. [[project-ia-objectif-final-inventions]]) : `substrat_physique.py` invente en chaînant des PRINCIPES
physiques sur un petit graphe curé de ~48 transducteurs. Ce module GÉNÉRALISE le même algorithme au graphe RÉEL du
corpus : un TYPE d'entité (pays, ville, élément…) joue le rôle d'une grandeur, une RELATION typée (capitale : pays→ville)
joue le rôle d'un transducteur, et une CHAÎNE de relations réalise une transduction type→type. Une chaîne NOUVELLE
(non stockée comme relation directe) = un ATTRIBUT COMPOSITE dérivable = un candidat d'invention (« il manque la
relation r1∘r2, voici les éléments : composer ces relations existantes »).

FAUX=0 — le risque (proposer une invention qui existe déjà, ou dériver du faux) est neutralisé par TROIS gardes
CUMULÉES, dans l'esprit de `substrat_physique.examine` mais durci pour le réel bruité :
  1. TYPAGE MESURÉ ≠ CERTAIN : `schema_relations.profil` mesure les types domaine/codomaine (frac ≥ 0.5, COMPATIBLE,
     PAS une preuve). On ne dérive JAMAIS une invention du seul typage. Il sert uniquement à PROPOSER des chaînes.
  2. TÉMOIN RÉEL OBLIGATOIRE : une chaîne n'est retenue que s'il existe ≥1 entité concrète du type de départ dont le
     suivi des relations, arête par arête, aboutit à une entité du type d'arrivée — et ce chemin est RE-VÉRIFIÉ par
     `graphe_monde.verifie_chemin` (chaque fait re-lookupé). C'est le « lookup par instance » sound qui transforme un
     typage COMPATIBLE en faits RÉELS. Sans témoin re-vérifié -> pas d'invention (BRIQUE_MANQUANTE).
  3. ANTI-FAUSSE-NOUVEAUTÉ : si une relation directe (ou un inverse compatible) réalise déjà type→type, c'est
     EXISTE_DEJA, jamais une invention. Dans le doute -> marquer connu (faux négatif toléré, faux positif interdit).
Comme `substrat_physique`, on NE JUGE PAS l'utilité/faisabilité de l'attribut composite : « concept à évaluer ». On
laisse `substrat_physique` et `moteur_invention` INTACTS (mirroir séparé, aucune contamination du substrat curé).
Souverain, offline. NB : coûteux (charge le lecteur) -> API bornée (budgets, échantillons), déterministe.

LIMITE ASSUMÉE (honnêteté FAUX=0) : le moteur garantit que chaque composite émis est un FAIT VRAI, re-vérifié et
SYSTÉMATIQUE ; il ne garantit PAS sa SALIENCE SÉMANTIQUE. Les entités étant identifiées par chaîne normalisée, un
pivot POLYSÉMIQUE traverse des composites vrais-mais-peu-utiles (« genre grammatical du mot qui nomme le pays du
film ») ou des homonymes SYSTÉMATIQUES (« pays de la localité homonyme du pays du film ») que la garde de couverture
(anti-coïncidence) ne filtre pas. Ces sorties restent VRAIES (pas de FAUX=0), pas forcément UTILES — le classement
par utilité / la résolution d'entité fine sont le prochain levier. Les composites clairement utiles émergent aussi
(code ISO/devise du pays, année de naissance/nationalité de l'auteur), avec témoin re-vérifié.
"""
from __future__ import annotations

import dataclasses

from base_faits import normalise

EXISTE_DEJA = "existe_deja"
INVENTION = "invention"
BRIQUE_MANQUANTE = "brique_manquante"


def _lecteur():
    import lecteur
    return lecteur.LECTEUR


# Types-ANCRES supplémentaires : chaque type = la POPULATION-clé d'une relation d'appartenance. Représenté par la
# TABLE elle-même (membership `x in table` en O(1), échantillon par islice) -> ZÉRO matérialisation, n'importe quelle
# relation propre devient un type. Choix data-driven : relations fonctionnelles à grande population homogène qui
# ouvrent des composites utiles (personne/œuvre/film/taxon/relief/étoile). Isolé de taxonomie (aucun autre module touché).
_ANCRES_TYPE = {
    "localites": "population_ville",            # ~M — population de villes COMPLÈTE (type « ville » dense, ≠ villes/9998
                                                #      trop petit) : rend la garde de jointure discriminante sur les reliefs/localités
    "personnes": "annee_naissance_personne",   # 3,2M — riches en attributs (naissance/nationalité/occupation…)
    "oeuvres_ecrites": "auteur_oeuvre_ecrite",  # 149k — œuvre -> auteur (personne)
    "films": "pays_film",                       # 77k
    "albums": "interprete_album",               # 159k — album -> interprète (personne)
    "taxons": "taxon_rang",                     # 3,8M
    "montagnes": "pays_montagne",               # 325k
    "rivieres": "pays_riviere",                 # 295k
    "lacs": "pays_lac",                         # 179k
    "etoiles": "type_etoile",                   # 1,28M
}

_TYPES_ENS = None


def types_reels() -> dict:
    """Univers de TYPES = ensembles de référence MESURÉS (taxonomie : pays/villes/astres/éléments) ÉTENDUS par des
    types-ancres (population-clé d'une relation d'appartenance : personnes/œuvres/films/taxons/reliefs/étoiles).
    name -> objet set-like (frozenset ou table dict) supportant `in` et l'itération. Émergent du corpus, pas arbitraire."""
    global _TYPES_ENS
    if _TYPES_ENS is None:
        import taxonomie
        ens = dict(taxonomie.ensembles())
        L = _lecteur()
        for nom, rel in _ANCRES_TYPE.items():
            t = L.tables.get(rel)
            if t and nom not in ens:
                ens[nom] = t                    # la table sert de set (clés = membres ; `x in t` O(1))
        _TYPES_ENS = ens
    return _TYPES_ENS


def _profil(rel):
    import schema_relations
    return schema_relations.profil(rel)


def transducteurs_reels(min_taille: int = 50, relations=None) -> list:
    """T0 — dérive les TRANSDUCTEURS = [(relation, type_domaine, type_codomaine)] pour chaque relation dont les CLÉS
    matchent un type mesuré ET les VALEURS un type mesuré (schema_relations.profil). LECTURE SEULE, aucun verdict :
    ne fait que refléter le typage déjà mesuré, avec provenance. Déterministe (tri)."""
    L = _lecteur()
    rels = sorted(relations) if relations is not None else sorted(L.relations())
    out = []
    for rel in rels:
        p = _profil(rel)
        if p is None or p.taille < min_taille:
            continue
        for a in p.types_domaine:
            for b in p.types_codomaine:
                if a != b:                          # une transduction change de type (arête non triviale)
                    out.append((rel, a, b))
    out.sort()
    return out


def _graphe(transducteurs) -> dict:
    """type -> [(type_suivant, relation)]."""
    g: dict = {}
    for rel, a, b in transducteurs:
        g.setdefault(a, []).append((b, rel))
    return g


def _directs(transducteurs) -> dict:
    """(type_domaine, type_codomaine) -> {relations directes}. Base de « CE QUI EXISTE DÉJÀ » (arête à un maillon)."""
    d: dict = {}
    for rel, a, b in transducteurs:
        d.setdefault((a, b), set()).add(rel)
    return d


def connus_reel(transducteurs) -> set:
    """T1 — ensemble des couples (type_domaine, type_codomaine) DÉJÀ réalisés par une relation directe. Sur-inclure
    ici ne produit QUE des inventions manquées (faux négatif), jamais une fausse invention (biais conservateur)."""
    return set(_directs(transducteurs).keys())


def chaines_types(transducteurs, a: str, b: str, max_len: int = 3) -> list:
    """Toutes les chaînes SIMPLES de types (sans répéter un type) reliant a->b, longueur <= max_len relations.
    Chaque chaîne = (relations, types). Purement structurel (candidat, PAS encore de témoin)."""
    g = _graphe(transducteurs)
    res = []

    def dfs(courant, vus, rels_acc):
        if len(rels_acc) > max_len:
            return
        if courant == b and rels_acc:
            res.append((tuple(rels_acc), tuple(vus)))
            return
        for (suiv, rel) in g.get(courant, []):
            if suiv in vus:
                continue
            dfs(suiv, vus + [suiv], rels_acc + [rel])

    if a in {t for t in g} or any(a == x for x in {t2 for _, _, t2 in transducteurs}):
        dfs(a, [a], [])
    res.sort(key=lambda c: len(c[0]))
    return res


def _table(rel):
    return _lecteur().tables.get(rel)


def _suit_chaine(depart: str, rels: tuple):
    """Suit une chaîne de relations depuis l'entité `depart` : depart --r1--> v1 --r2--> ... Renvoie (final, pas)
    où `pas` = [(rel, noeud)] à passer à graphe_monde.verifie_chemin, ou (None, None) si une arête manque."""
    cur = normalise(depart)
    pas = []
    for rel in rels:
        t = _table(rel)
        if t is None:
            return None, None
        f = t.get(cur)
        if f is None:
            return None, None
        v = normalise(str(f.valeur))
        pas.append((rel, v))
        cur = v
    return cur, pas


def _temoin(a: str, rels: tuple, type_b, ens, budget: int = 400):
    """Cherche une entité de type `a` dont le suivi de `rels` aboutit dans le type `b`, chemin RE-VÉRIFIÉ.
    Renvoie (entite, final, pas) ou None. Borné (`budget` entités échantillonnées). C'est la garde FAUX=0 #2."""
    import graphe_monde
    ens_a = ens.get(a)
    ens_b = ens.get(type_b)
    if not ens_a or not ens_b:
        return None
    for i, e0 in enumerate(ens_a):
        if i >= budget:
            break
        final, pas = _suit_chaine(e0, rels)
        if final is not None and final in ens_b and graphe_monde.verifie_chemin(e0, pas):
            return (e0, final, tuple(pas))
    return None


@dataclasses.dataclass(frozen=True)
class ConceptReel:
    statut: str
    type_entree: str
    type_sortie: str
    relations: tuple = ()          # les relations à composer (les « éléments à construire »)
    temoin: tuple = ()             # (entité_départ, entité_arrivée) — la preuve d'existence re-vérifiée
    justification: str = ""

    def __str__(self) -> str:
        chaine = " ∘ ".join(self.relations) if self.relations else "—"
        if self.statut == INVENTION:
            e0, ef = (self.temoin + ("", ""))[:2]
            return (f"[INVENTION] attribut composite {self.type_entree} → {self.type_sortie}\n"
                    f"      relations à composer : {chaine}\n"
                    f"      témoin re-vérifié : {e0} → {ef}\n      ({self.justification})")
        if self.statut == EXISTE_DEJA:
            return f"[EXISTE DÉJÀ] {self.type_entree} → {self.type_sortie} (relation directe : {chaine})"
        return f"[BRIQUE MANQUANTE] {self.type_entree} → {self.type_sortie} — {self.justification}"


def examine_reel(a: str, b: str, transducteurs=None, *, max_len: int = 3, budget: int = 400) -> ConceptReel:
    """T3 — tranche la cible (type a -> type b) : EXISTE_DEJA / INVENTION / BRIQUE_MANQUANTE. Gardes FAUX=0 cumulées :
    relation directe -> EXISTE_DEJA ; sinon la chaîne composée NOUVELLE la plus courte AVEC témoin re-vérifié ->
    INVENTION ; sinon BRIQUE_MANQUANTE. Jamais d'invention sans preuve d'instance re-lookupée."""
    if transducteurs is None:
        transducteurs = transducteurs_reels()
    directs = _directs(transducteurs)
    ens = types_reels()
    # Garde #3 : une relation directe réalise déjà a->b -> EXISTE_DEJA (pas une invention).
    if (a, b) in directs:
        return ConceptReel(EXISTE_DEJA, a, b, relations=tuple(sorted(directs[(a, b)])),
                           justification="relation directe stockée")
    connus = connus_reel(transducteurs)
    cs = chaines_types(transducteurs, a, b, max_len)
    if not cs:
        return ConceptReel(BRIQUE_MANQUANTE, a, b,
                           justification="aucune chaîne de relations typées ne relie ces types")
    # chaînes composées nouvelles (≥2 maillons), plus simple d'abord, exigeant un TÉMOIN re-vérifié (garde #2).
    for rels, types in cs:
        if len(rels) < 2:
            continue
        # sous-chaîne déjà connue en direct ? (a->b réalisable en 1 maillon est déjà écarté au-dessus)
        t = _temoin(a, rels, b, ens, budget=budget)
        if t is not None:
            e0, ef, _pas = t
            return ConceptReel(INVENTION, a, b, relations=rels, temoin=(e0, ef),
                               justification="attribut composite dérivable, témoin re-vérifié (efficacité/valeur non jugées)")
    return ConceptReel(BRIQUE_MANQUANTE, a, b,
                       justification="chaînes typées possibles mais aucun témoin réel re-vérifié -> pas de dérivation sound")


# ─────────────────────────────────────────────────────────────────────────────
# ATTRIBUT COMPOSITE DÉRIVABLE — la surface UTILE de l'objectif : « quel attribut d'une entité n'est pas stocké
# directement mais est DÉRIVABLE en composant des relations existantes ? » (ex. population de la capitale d'un pays).
# C'est une invention BORNÉE et FAUX=0 : chaque composite proposé est prouvé par ≥1 témoin re-vérifié, et n'est
# retenu QUE si aucune relation directe de l'entité ne fournit déjà la même valeur (anti-fausse-nouveauté par instance).
# ─────────────────────────────────────────────────────────────────────────────
import itertools


def _echantillon_type(nom_type: str, budget: int) -> list:
    ens = types_reels().get(nom_type)
    if not ens:
        raise ValueError(f"type inconnu : {nom_type!r}")
    return list(itertools.islice(ens, budget))


def relations_pont(entites: list, seuil: float = 0.5, min_taille: int = 50) -> list:
    """Relations dont les CLÉS couvrent (≥ seuil) `entites` = les « attributs directs » d'une population. Déterministe."""
    L = _lecteur()
    out = []
    n = len(entites)
    if not n:
        return []
    for rel in sorted(L.relations()):
        t = L.tables.get(rel)
        if t is None or len(t) < min_taille:
            continue
        couv = sum(1 for e in entites if normalise(e) in t)
        if couv >= seuil * n:
            out.append(rel)
    return out


@dataclasses.dataclass(frozen=True)
class Composite:
    statut: str
    type_source: str
    pont: str                      # relation-pont : source -> entité intermédiaire
    cible: str                     # relation-cible : entité intermédiaire -> valeur
    temoin: tuple = ()             # (source, intermédiaire, valeur) re-vérifié
    justification: str = ""
    couverture: float = 0.0        # fraction de la population où le composite tient (= confiance dérivable)

    def __str__(self) -> str:
        if self.statut == INVENTION:
            s, mi, v = (self.temoin + ("", "", ""))[:3]
            return (f"[INVENTION] attribut composite : {self.type_source} → ({self.pont} ∘ {self.cible})\n"
                    f"      dérivable = {self.cible}( {self.pont}(x) )\n"
                    f"      témoin re-vérifié : {s} → {mi} → {v}\n      ({self.justification})")
        if self.statut == EXISTE_DEJA:
            return f"[EXISTE DÉJÀ] {self.type_source} a déjà l'attribut {self.cible} (ou le compose trivialement)"
        return f"[BRIQUE MANQUANTE] {self.type_source} → {self.cible} — {self.justification}"


def _valeurs_directes(e0: str) -> set:
    """Toutes les valeurs normalisées atteignables depuis e0 par UNE relation directe (pour juger la nouveauté)."""
    import graphe_monde
    return {v for _rel, v, _aff in graphe_monde.sortants(e0)}


import itertools as _it

_TYPAGE_CACHE: dict = {}


def _types_relation(rel: str, cote: str, *, seuil: float = 0.5, ech: int = 200) -> tuple:
    """Typage LOCAL MESURÉ d'une relation contre l'univers de types enrichi (indépendant de schema_relations, isolé).
    `cote`='D' (domaine : sur les CLÉS) ou 'C' (codomaine : sur les VALEURS). Renvoie les types couvrant ≥ seuil de
    l'échantillon. Caché. FAUX=0 : ne reflète que ce qui est mesuré ; sert à PROPOSER, jamais à affirmer un fait."""
    clef = (rel, cote, seuil, ech)
    if clef in _TYPAGE_CACHE:
        return _TYPAGE_CACHE[clef]
    t = _table(rel)
    types = types_reels()
    res = ()
    if t is not None and len(t):
        if cote == "D":
            ech_vals = [normalise(k) for k in _it.islice(t.keys(), ech)]
        else:
            ech_vals = [normalise(str(f.valeur)) for f in _it.islice(t.values(), ech)]
        n = len(ech_vals)
        # Garde ENTITÉ vs SCALAIRE/CATÉGORIEL : un codomaine d'ENTITÉ a des valeurs majoritairement DISTINCTES.
        # Une relation booléenne/catégorielle (sans_littoral -> oui/non ; genre -> H/F) a peu de valeurs distinctes ;
        # sa valeur unique peut coïncider avec une clé d'un type énorme -> faux typage entité. On l'exclut du codomaine.
        if cote == "C" and (len(set(ech_vals)) < 10 or len(set(ech_vals)) < 0.5 * n):
            res = ()
        else:
            res = tuple(nom for nom, ens in types.items()
                        if sum(1 for x in ech_vals if x in ens) >= seuil * n)
    _TYPAGE_CACHE[clef] = res
    return res


def _pont_valide(rel: str, type_source: str) -> bool:
    """GARDES anti-faux-composite (risque FAUX=0 #5, homonymes) sur une relation-PONT, via typage LOCAL enrichi :
      (a) CODOMAINE = type d'entité mesuré (non vide) -> l'intermédiaire est une entité d'une population reconnue, pas
          un scalaire/code/booléen dont la forme-chaîne coïncide par hasard (ex. pays→'non'→auteur, pays→1965→…) ;
      (b) DOMAINE inclut `type_source` -> le pont est employé dans son sens mesuré pour ce type (écarte les homonymes
          de rôle). Sans typage mesuré -> refus (conservateur, FAUX=0)."""
    return bool(_types_relation(rel, "C") and type_source in _types_relation(rel, "D"))


def derive_attribut(type_source: str, relation_cible: str, *, budget: int = 400,
                    seuil_pont: float = 0.5, seuil_couverture: float = 0.3) -> Composite:
    """Le composite (pont ∘ relation_cible) est-il une INVENTION dérivable pour `type_source` ? Gardes FAUX=0 :
      • EXISTE_DEJA si les entités du type ONT déjà `relation_cible` en direct ;
      • sinon on retient la relation-PONT dont le composite est SYSTÉMATIQUE = re-vérifié pour une FRACTION ≥
        `seuil_couverture` de la population (pas un simple témoin isolé). Cette couverture est le garde anti-homonyme
        DÉCISIF : « population de la capitale » tient pour ~tous les pays (systématique) ; un homonyme du pivot
        (« victoria » capitale ≠ subdivision) ne tient que pour une poignée (couverture faible) -> BRIQUE_MANQUANTE.
      Chaque maillon reste re-vérifié (`verifie_chemin`), le composite exclut identité et redondance directe."""
    import collections
    import graphe_monde
    L = _lecteur()
    if relation_cible not in set(L.relations()):
        raise ValueError(f"relation cible inconnue : {relation_cible!r}")
    ech = _echantillon_type(type_source, budget)
    tcible = L.tables.get(relation_cible)
    types_cible_dom = set(_types_relation(relation_cible, "D"))  # types du DOMAINE de la cible (le pivot attendu)
    directe = sum(1 for e in ech if normalise(e) in tcible)
    if ech and directe >= seuil_pont * len(ech):
        return Composite(EXISTE_DEJA, type_source, "", relation_cible,
                         justification="les entités du type possèdent déjà cette relation en direct")
    couverture = collections.Counter()                          # pont -> nb d'entités source à chaîne re-vérifiée
    temoin = {}
    for e0 in ech:
        e0n = normalise(e0)
        directes_e0 = _valeurs_directes(e0n)
        for rel, v, _aff in graphe_monde.sortants(e0n):
            if rel == relation_cible or not _pont_valide(rel, type_source):
                continue
            # Garde COHÉRENCE DE TYPE à la jointure : le type du codomaine du pont (l'intermédiaire) doit recouper le
            # type du domaine de la cible. Sinon la cible interprète le pivot dans un AUTRE type (ex. « japon » pays
            # via pays_film, mais genre_grammatical le lit comme un MOT -> jointure de types incohérente, écartée).
            if types_cible_dom and not (set(_types_relation(rel, "C")) & types_cible_dom):
                continue
            f2 = tcible.get(v)
            if f2 is None:
                continue
            val = normalise(str(f2.valeur))
            if val == e0n or val == v or val in directes_e0:    # dégénéré / redondant
                continue
            if not graphe_monde.verifie_chemin(e0n, [(rel, v), (relation_cible, val)]):
                continue
            couverture[rel] += 1
            temoin.setdefault(rel, (e0n, v, val))
    if not couverture:
        return Composite(BRIQUE_MANQUANTE, type_source, "", relation_cible,
                         justification="aucun pont réel re-vérifié vers cette cible depuis ce type")
    pont, n = couverture.most_common(1)[0]
    frac = n / len(ech) if ech else 0.0
    if frac >= seuil_couverture:
        return Composite(INVENTION, type_source, pont, relation_cible, temoin=temoin[pont],
                         justification=f"attribut composite SYSTÉMATIQUE (dérivé pour {n}/{len(ech)}={frac:.0%} du type, "
                                       f"chaînes re-vérifiées ; valeur/utilité non jugées)", couverture=frac)
    return Composite(BRIQUE_MANQUANTE, type_source, "", relation_cible,
                     justification=f"seulement {n}/{len(ech)} chaînes ({frac:.0%}) < seuil {seuil_couverture:.0%} "
                                   f"-> vraisemblablement coïncidence d'homonymes, pas une dérivation systématique")


def composites_utiles(type_source: str, *, budget: int = 200, max_cibles: int = 40, k: int = 12) -> list:
    """Énumère des INVENTIONS d'attributs composites pour `type_source` : pour chaque relation-cible candidate
    (keyée par des entités intermédiaires atteignables), teste `derive_attribut`. Renvoie ≤ k composites INVENTION
    distincts (pont, cible). BORNÉ (budget entités, max_cibles relations). Déterministe."""
    L = _lecteur()
    ech = _echantillon_type(type_source, budget)
    import graphe_monde
    # cibles candidates = relations keyées par les entités intermédiaires (valeurs des ponts sortants du type)
    cibles = {}
    for e0 in ech:
        for rel, v, _aff in graphe_monde.sortants(normalise(e0)):
            if not _pont_valide(rel, type_source):              # ne compter que via des ponts entité-typés, bon sens
                continue
            for rc, _v2, _a2 in graphe_monde.sortants(v):
                if rc != rel:
                    cibles[rc] = cibles.get(rc, 0) + 1
    ordonnees = [rc for rc, _ in sorted(cibles.items(), key=lambda kv: (-kv[1], kv[0]))][:max_cibles]
    trouves, vus = [], set()
    for rc in ordonnees:
        c = derive_attribut(type_source, rc, budget=budget)
        if c.statut == INVENTION and (c.pont, c.cible) not in vus:
            vus.add((c.pont, c.cible))
            trouves.append(c)
            if len(trouves) >= k:
                break
    return trouves
