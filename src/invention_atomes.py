"""
PONT MOTEUR D'INVENTION → CONTRAT D'ATOME (2026-07-02).

POURQUOI (vision Yohan) : « une invention est une supposition qui a survécu à la réalité ». Le moteur d'invention
produit des candidats ; le contrat d'atome (`atome.py`) leur donne leur STATUT ÉPISTÉMIQUE exact, pour qu'aucun ne
soit jamais servi comme un fait certain qu'il n'est pas. Ce module TRADUIT les sorties du moteur en `Atome` typés,
en respectant la distinction VITALE :
  • `substrat_reel` (composite DÉRIVABLE) : un attribut déjà vrai dans le corpus, juste non stocké.
      - la GÉNÉRALISATION -> `SUPPOSITION` régime DÉRIVABLE, confiance = COUVERTURE (fraction de la population) ;
      - le TÉMOIN d'une instance re-vérifié -> `FAIT` par instance (juge = graphe_monde.verifie_chemin -> Verdict).
  • `substrat_physique` (chaîne de transduction NOUVELLE) : une invention GÉNÉRATIVE, pas encore réelle.
      - -> `SUPPOSITION` régime GÉNÉRATIF, confiance = PLAUSIBILITÉ STRUCTURELLE (bornée, basse), portée = domaine
        physique ; « efficacité/magnitudes non jugées » = supposition cadrée, à confronter (promeut via un vrai juge).
FAUX=0 : le contrat d'atome garantit qu'une supposition n'est jamais servable comme fait ; un dérivable-systématique
n'est un FAIT que par INSTANCE re-vérifiée. Additif, souverain ; ne modifie pas les moteurs (mirroir).
"""
from __future__ import annotations

import atome as A


def atome_derivable(composite) -> A.Atome | None:
    """Composite INVENTION -> SUPPOSITION régime DÉRIVABLE (confiance = couverture). Autre statut -> None."""
    import substrat_reel as SR
    if composite is None or composite.statut != SR.INVENTION:
        return None
    s, mi, v = (tuple(composite.temoin) + ("", "", ""))[:3]
    contenu = f"{composite.type_source} → {composite.cible}({composite.pont}(x)) [attribut composite dérivable]"
    conf = max(0.01, min(0.99, float(composite.couverture)))          # borné ]0,1[ (une supposition n'est jamais certaine)
    return A.suppose(
        contenu, A.DERIVABLE,
        A.Portee(A.EPISTEMIQUE, f"dérivable pour ~{composite.couverture:.0%} du type {composite.type_source}"),
        conf,
        base=f"pont {composite.pont} ∘ {composite.cible} ; témoin re-vérifié {s}→{mi}→{v} ; couverture {composite.couverture:.0%}")


def atome_temoin(composite) -> A.Atome | None:
    """Le TÉMOIN d'un composite INVENTION -> FAIT par instance (Verdict = graphe_monde.verifie_chemin). Sinon None."""
    import substrat_reel as SR
    if composite is None or composite.statut != SR.INVENTION or len(composite.temoin) < 3:
        return None
    s, mi, v = composite.temoin[:3]
    verdict = A.Verdict("graphe_monde.verifie_chemin", True,
                        f"chemin {s} -[{composite.pont}]-> {mi} -[{composite.cible}]-> {v} re-vérifié arête par arête")
    contenu = f"pour {s} : {composite.cible}({composite.pont}({s})) = {v}"
    return A.atteste(contenu, A.Portee(A.REFERENTIEL, f"l'entité {s} via {composite.pont}∘{composite.cible}"), verdict)


def atome_generatif(concept) -> A.Atome | None:
    """Concept INVENTION (substrat_physique) -> SUPPOSITION régime GÉNÉRATIF (plausibilité structurelle). Sinon None."""
    import substrat_physique as SP
    if concept is None or concept.statut != SP.INVENTION:
        return None
    n = max(1, len(concept.chaine))
    plausibilite = 1.0 / (1.0 + n)                                    # borné ]0,1[ : + la chaîne est longue, - plausible
    fleche = " → ".join(concept.grandeurs) if concept.grandeurs else f"{concept.entree} → {concept.sortie}"
    contenu = f"dispositif {concept.entree} → {concept.sortie} par [{' + '.join(concept.chaine)}]"
    return A.suppose(
        contenu, A.GENERATIF,
        A.Portee(A.DOMAINE, "transduction physique cohérente ; efficacité/magnitudes non jugées"),
        plausibilite,
        base=f"chaîne cohérente {fleche} ; principes à combiner : {', '.join(concept.chaine)}")


# ─────────── PONT moteur_invention (capacités) → atomes (Phase 2 axe ① : contrat d'atome universel) ───────────
def atome_capacite(verdict, exemples, exemples_held) -> tuple:
    """MI.Verdict (capacités, jugé par l'exécuteur) -> (supposition_générale, fait_borné), l'un ou l'autre None.

    La distinction VITALE, même patron que (dérivable, témoin) :
      • INVENTION : la revendication GÉNÉRALE (« S est la capacité voulue au-delà du spec ») reste une SUPPOSITION
        GÉNÉRATIVE — le spec est fini, le comportement général n'est pas jugé. Confiance = règle de succession de
        Laplace (n+1)/(n+2) sur les n paires vérifiées (bornée ]0,1[, croît avec l'évidence, jamais 1).
        La revendication BORNÉE (« S reproduit les n paires exemples+held ») est un FAIT : jugée par EXÉCUTION
        réelle (_reproduit en process + juge sandbox sur le held-out) -> Verdict tracé.
      • EXISTE_DEJA : rien de nouveau à supposer (pas de supposition) ; le fait borné (« la capacité existante
        reproduit le spec ») est attesté (vérifié par exécution).
      • AMBIGU / BRIQUE_MANQUANTE / INCOHERENT : (None, None) — ABSTENTION (≥2 réalisations distinctes, ou rien
        de vérifié : committer un atome serait un faux). La sonde discriminante reste dans le verdict.
    """
    import moteur_invention as MI
    if verdict is None or verdict.statut not in (MI.INVENTION, MI.EXISTE_DEJA):
        return None, None
    n = len(list(exemples)) + len(list(exemples_held or []))
    if n == 0:
        return None, None                                  # aucun spec vérifié -> rien d'attestable
    portee_spec = A.Portee(A.EPISTEMIQUE, f"les {n} paires vérifiées du spec de {verdict.cible}")
    if verdict.statut == MI.EXISTE_DEJA:
        v = A.Verdict("moteur_invention(exécution réelle sur exemples+held)", True,
                      f"la capacité existante « {verdict.proche_de} » ({verdict.par}) reproduit les {n} paires")
        fait = A.atteste(f"{verdict.cible} = capacité existante « {verdict.proche_de} » sur son spec ({n} paires)",
                         portee_spec, v)
        return None, fait
    # INVENTION : vérifiée (unique sous le spec + held-out + nouveauté) — cf. soundness de examine_cible.
    conf = (n + 1.0) / (n + 2.0)                           # règle de succession (n succès observés, jamais 1)
    sup = A.suppose(
        f"invention {verdict.cible} : {verdict.par} (comportement général au-delà du spec)",
        A.GENERATIF,
        A.Portee(A.DOMAINE, f"candidat capacité {verdict.cible} ; comportement hors spec non jugé"),
        conf,
        base=f"unique sous le spec ({n} paires), held-out confirmé par le juge, comportement nouveau ; {verdict.justification}")
    v = A.Verdict("moteur_invention(_reproduit + juge held-out)", True,
                  f"{verdict.par} reproduit les {n} paires du spec (exemples en process, held-out en sandbox)")
    fait = A.atteste(f"la réalisation {verdict.par} reproduit les {n} paires du spec de {verdict.cible}",
                     portee_spec, v)
    return sup, fait


def invente_capacite(nom: str, signature: str, exemples, exemples_held, *, budget: int = 2000, existant=None):
    """Surface haut niveau : tranche une cible-capacité ET rend ses atomes. -> (verdict, supposition, fait_borné).
    Le verdict complet reste disponible (statuts AMBIGU/BRIQUE_MANQUANTE/INCOHERENT + sonde) ; les atomes ne sont
    émis QUE pour INVENTION / EXISTE_DEJA (sinon (None, None) — abstention)."""
    import moteur_invention as MI
    verdict = MI.examine_cible(nom, signature, exemples, exemples_held, budget=budget, existant=existant)
    sup, fait = atome_capacite(verdict, exemples, exemples_held)
    return verdict, sup, fait


# ─────────── surface haut niveau : le moteur rend directement des atomes ───────────
def invente_attribut(type_source: str, relation_cible: str, *, budget: int = 300):
    """(supposition_dérivable, fait_témoin) pour un attribut composite du réel — ou (None, None). La supposition
    porte la confiance = couverture ; le témoin est un fait par instance re-vérifié."""
    import substrat_reel as SR
    c = SR.derive_attribut(type_source, relation_cible, budget=budget)
    return atome_derivable(c), atome_temoin(c)


def invente_dispositif(entree: str, sortie: str, *, max_len: int = 4):
    """Supposition GÉNÉRATIVE d'un dispositif physique (chaîne de transduction nouvelle) — ou None si connu/impossible."""
    import substrat_physique as SP
    return atome_generatif(SP.examine(entree, sortie, max_len=max_len))
