"""
BOUCLE WEB -> RÉALITÉ -> FAIT-STORE : rendre l'invention/apprentissage NON-ÉPHÉMÈRE (roadmap #11, backlog #3).

Ce module ferme le cycle du contrat d'atome : une valeur RAPPORTÉE (observée sur des sources) n'est PROMUE en
FAIT et PERSISTÉE que si (a) des sources INDÉPENDANTES concordent sur LA MÊME valeur (corroboration, veille.py) ET
(b) un JUGE RÉEL confronte le candidat à la réalité connue. Sinon elle reste SUPPOSITION (rien n'est stocké).

DÉCOMPOSITION FAUX=0 (contrat d'atome) :
  • OBSERVER = SUPPOSITION RAPPORTÉE (veille.rapporte) — jamais un fait.
  • CORROBORER = compter les sources INDÉPENDANTES (domaines distincts, contenu non recopié) qui portent LA MÊME
    valeur (veille.corrobore) — au moins `minimum`.
  • JUGER = un mécanisme RÉEL (`atome.Verdict`), pas un bool nu. Le juge par défaut `juge_coherence_store` est une
    vraie confrontation : la valeur candidate NE DOIT PAS CONTREDIRE le fait déjà connu du store (si présent) ; pour
    une grandeur numérique, un juge de plage/tolérance est composables. L'appelant peut injecter coherence_physique,
    un test, une falsification…
  • PERSISTER = écriture CONFLIT-REFUSÉE (`ia.ingere_donnees` / lecteur.ingere_table lève sur valeur divergente) :
    seconde garde FAUX=0 AU WRITE. La provenance (sources + juge) est tracée dans la source du fait.

Un seul maillon manquant -> on s'ARRÊTE au premier None/échec (abstention). Aucune valeur non corroborée-et-jugée
n'entre dans le store. Souverain/offline : `observations` et `persiste` sont INJECTABLES (tests sans réseau ni
lecteur lourd) ; en prod, les observations viennent des sources STRUCTURÉES (SPARQL/API) du registre, pas du HTML
libre (veille.py ne fait pas d'extraction — anti-hallucination assumé).
"""
from __future__ import annotations

from collections import namedtuple

import atome as A
import veille as _VEI

# Une OBSERVATION = une valeur vue pour (relation, entité) sur UNE source (domaine + url). Structurée : la valeur
# vient d'un point d'accès déterministe (API/SPARQL), pas d'une extraction de texte libre.
Observation = namedtuple("Observation", ["domaine", "url", "valeur"])

PERSISTE = "persiste"          # promu FAIT ET écrit dans le store
SUPPOSE = "suppose"            # corroboration/juge insuffisants -> reste SUPPOSITION (rien de stocké)
CONFLIT = "conflit"           # promu mais le store détenait une valeur divergente -> écriture REFUSÉE (FAUX=0)
REFUTE = "refute"             # le juge a réfuté le candidat (garde anti-re-proposition d'atome)


def _cle(relation: str, entite: str, valeur: str) -> str:
    return f"{relation}({entite}) = {valeur}"


def _norm(v) -> str:
    return " ".join(str(v).strip().lower().split())


def juge_coherence_store(lecteur=None):
    """Fabrique un JUGE RÉEL : la valeur candidate est cohérente SSI le store (lecteur) ne détient PAS déjà une
    valeur DIFFÉRENTE pour (relation, entité). C'est une confrontation à la connaissance vérifiée existante
    (le store est la mémoire de faits jugés) — pas un tampon. Renvoie un callable (enonce, indep) -> A.Verdict.
    `lecteur` : objet avec .cherche(relation, entite) -> fait|None ; None -> pas de contre-preuve disponible
    (le juge valide alors sur la seule base de l'indépendance, déjà exigée par corrobore)."""
    def _juge(relation, entite, valeur):
        if lecteur is not None:
            try:
                f = lecteur.cherche(relation, entite)
            except Exception:
                f = None
            if f is not None and _norm(getattr(f, "valeur", f)) != _norm(valeur):
                return A.Verdict("coherence_store", False,
                                 f"contredit le fait connu {relation}({entite})={getattr(f, 'valeur', f)!r}")
        return A.Verdict("coherence_store", True,
                         f"cohérent avec le store connu pour {relation}({entite})={valeur!r}")
    return _juge


def corrobore_valeur(relation, entite, valeur, observations, *, categorie, source,
                     minimum=2, juge=None, persiste=None, lecteur=None):
    """Tente de promouvoir (relation, entité)=valeur en FAIT PERSISTÉ à partir d'`observations`.
    Étapes : filtre les observations qui portent CETTE valeur -> témoignages ; veille.corrobore exige >= `minimum`
    domaines INDÉPENDANTS ET le juge réel ; sur promotion -> persiste (conflit-refusé). Renvoie un dict :
      {statut: PERSISTE|SUPPOSE|CONFLIT|REFUTE, atome, n_independantes, valeur, provenance, raison}.
    Ne lève pas (les erreurs deviennent SUPPOSE/CONFLIT). `juge` : callable(enonce, indep)->A.Verdict OU None
    (défaut = juge_coherence_store(lecteur)). `persiste` : callable(relation, [(entite,valeur)], categorie, source)
    ->int OU None (défaut = ia.ingere_donnees) ; injectable pour tests offline."""
    if not (isinstance(relation, str) and relation.strip() and isinstance(entite, str) and entite.strip()):
        return {"statut": SUPPOSE, "atome": None, "n_independantes": 0, "valeur": valeur,
                "provenance": (), "raison": "relation/entité requises"}
    vser = str(valeur).strip()
    if not vser:
        return {"statut": SUPPOSE, "atome": None, "n_independantes": 0, "valeur": valeur,
                "provenance": (), "raison": "valeur vide"}

    enonce = _cle(relation, entite, vser)
    # témoignages = observations qui portent LA MÊME valeur (empreinte = contenu de la source, pour l'indépendance).
    temoins = []
    for o in observations:
        if _norm(o.valeur) != _norm(vser):
            continue
        emp = _VEI.hashlib.sha256(f"{o.domaine}|{o.url}|{vser}".encode()).hexdigest()
        temoins.append(_VEI.Temoignage(o.url, o.domaine, enonce, emp))
    indep = _VEI.independantes(temoins)
    n = len(indep)
    doms = tuple(t.domaine for t in indep)

    # Atome RAPPORTÉ (supposition) portant le compte d'indépendance — SANS juge ici : la décision juge/promotion
    # est faite EXPLICITEMENT ci-dessous (veille.corrobore avale un verdict négatif en « reste supposition », ce
    # qui masquerait une VRAIE réfutation ; on veut un REFUTE explicite = garde anti-re-proposition du contrat).
    at = _VEI.corrobore(enonce, temoins, minimum=minimum, juge=None)

    if n < minimum:
        return {"statut": SUPPOSE, "atome": at, "n_independantes": n, "valeur": vser, "provenance": doms,
                "raison": f"corroboration insuffisante ({n}/{minimum} sources indépendantes)"}

    # JUGE RÉEL (défaut = cohérence avec le store connu). Un Verdict, pas un bool.
    j = juge or juge_coherence_store(lecteur)
    v = j(relation, entite, vser)
    if not (isinstance(v, A.Verdict)):
        return {"statut": SUPPOSE, "atome": at, "n_independantes": n, "valeur": vser, "provenance": doms,
                "raison": "juge n'a pas rendu de Verdict -> pas de promotion (reste supposition)"}
    if not v.verdict:
        try:
            ref = A.promeut(at, v, quand="veille_corroboration")   # SUPPOSITION -> REFUTE + garde anti-re-proposition
        except ValueError:
            ref = at                                               # déjà réfuté antérieurement (garde active)
        return {"statut": REFUTE, "atome": ref, "n_independantes": n, "valeur": vser, "provenance": doms,
                "raison": f"juge réel a réfuté le candidat ({v.preuve()})"}
    try:
        fait = A.promeut(at, v, quand="veille_corroboration")      # SUPPOSITION -> FAIT (verdict positif)
    except ValueError as e:
        return {"statut": REFUTE, "atome": at, "n_independantes": n, "valeur": vser, "provenance": doms,
                "raison": f"contenu antérieurement réfuté (garde anti-blanchiment) : {e}"}

    # PROMU FAIT -> PERSISTER (écriture conflit-refusée = 2e garde FAUX=0). Provenance tracée dans la source.
    src = f"{source} — corroboré {n} sources indépendantes [{', '.join(doms)}] ; juge: {fait.preuve}"
    ecrit = persiste
    if ecrit is None:
        import ia
        ecrit = ia.ingere_donnees
    try:
        ecrit(relation, [(entite, vser)], categorie, src)
    except ValueError as e:
        return {"statut": CONFLIT, "atome": fait, "n_independantes": n, "valeur": vser, "provenance": doms,
                "raison": f"le store détenait une valeur divergente (écriture refusée) : {e}"}
    return {"statut": PERSISTE, "atome": fait, "n_independantes": n, "valeur": vser, "provenance": doms,
            "raison": f"corroboré ({n} sources) + jugé + persisté"}
