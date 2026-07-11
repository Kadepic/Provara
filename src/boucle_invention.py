"""
CAPSTONE — LA BOUCLE D'INVENTION COMPLÈTE : besoin -> assemblage -> gap -> corroboration -> atome -> writeback.

Enchaîne les briques déjà validées en UN geste, en ABSTENANT au premier maillon manquant (pas de fabrication) :

  1. OBJECTIF (`besoin.decompose`) : repart du BUT réel (rafraîchir = évacuer les W du corps, pas l'air) ->
     canaux physiques + principes JUGÉS. Besoin non modélisé -> HORS (étape 'objectif').
  2. ASSEMBLAGE (`transfert.transfere`) : compose des candidats-stacks (principe viable × canal), SUPPOSITIONS
     GÉNÉRATIVES classées par plausibilité de composition (jamais des faits). Rien de composable -> HORS.
  3. GAP (`transfert.manque`) : « voir ce qui manque » — canaux/puits/effets non exploités (diagnostic).
  4. CORROBORATION+WRITEBACK (`veille_corroboration.corrobore_valeur`) : les FAITS FACTUELS sur lesquels repose
     l'invention (ex. « le matériau M a l'effet élastocalorique », « la source S est à T °C ») sont confrontés à
     des sources INDÉPENDANTES + un JUGE réel ; ceux qui SURVIVENT sont PERSISTÉS (fait NON-éphémère, provenance
     tracée, écriture conflit-refusée). Les autres restent supposition / sont réfutés — jamais servis comme faits.

DISTINCTION FAUX=0 essentielle : le CANDIDAT d'invention est une SUPPOSITION GÉNÉRATIVE (n'existe pas encore) —
il n'est JAMAIS promu en fait ici. Seuls les FAITS FACTUELS de grounding (des affirmations sur le réel existant)
peuvent être corroborés et persistés. « Une invention est une supposition qui a survécu à la réalité » : la boucle
rend explicite ce qui est SUPPOSÉ (le dispositif) et ce qui est VÉRIFIÉ (les faits qui le fondent).

Souverain/offline : les `faits_a_verifier` (avec leurs observations issues de sources STRUCTURÉES) et la
persistance sont fournis/injectés par l'appelant — la boucle orchestre, elle n'invente pas de données.
"""
from __future__ import annotations

import besoin as _B
import transfert as _T
import veille_corroboration as _VC

HORS = "hors"
PROPOSE = "propose"


def _serialise_candidat(c) -> dict:
    """Vue lisible d'un Candidat (SUPPOSITION générative) — jamais présenté comme un fait."""
    return {
        "titre": c.titre,
        "statut_atome": c.atome.statut,              # 'supposition' (régime génératif) — vérifié par le contrat
        "confiance": round(c.atome.confiance, 3),
        "puits": c.puits,
        "canal": c.livraison,
        "inspiration": c.inspiration_nature,
        "composants": list(c.composants),
    }


def invente_composite(besoin: str) -> dict:
    """LES 3 AXES ASSEMBLÉS (Phase 2) : un besoin COMPOSITE est routé vers ses domaines (axe ③ compose),
    chaque domaine émet ses principes JUGÉS en atomes (axe ① contrat), tous postés sur UN blackboard partagé
    (axe ② substrat commun) — d'où toute capacité aval relit SOUS le contrat : suppositions() = la matière à
    travailler ; faits() = RIEN tant qu'aucun juge réel n'a promu (asymétrie préservée de bout en bout).
    Besoin non composite -> HORS (la boucle mono-domaine reste boucle()). Ne lève pas."""
    import blackboard as _BB
    comp = _B.compose(besoin)
    if comp.get("statut") != "compose":
        return {"statut": HORS, "etape": "composition", "besoin": besoin,
                "raison": "besoin composite non déclaré — abstention plutôt que fabriquer une composition"}
    bb = _BB.Blackboard()
    refutes = 0
    for sous in comp["sous"]:
        sb = sous["besoin"]
        p = _B.principes(sb)
        if p.get("statut") != "principes":
            continue                                   # domaine sans catalogue : déjà visible via comp['manques']
        for e in p["liste"]:
            bb.poste_atome(f"{comp['nom']}/{sb}", e["atome"], source=f"besoin.principes({sb})")
            refutes += e["atome"].statut == "refute"
    sujets = sorted(bb.sujets())
    return {
        "statut": PROPOSE,
        "etape": "complet",
        "besoin": besoin,
        "nom": comp["nom"],
        "blackboard": bb,
        "sujets": sujets,
        "lois": comp["lois"],
        "manques": comp["manques"],
        "n_suppositions": sum(len(bb.suppositions(s)) for s in sujets),
        "n_refutes": refutes,
        "note": "chaque principe est une SUPPOSITION jugée (ou un RÉFUTÉ) posté au tableau ; faits() reste vide "
                "tant qu'aucun juge réel n'a promu — l'asymétrie du contrat tient de bout en bout.",
    }


def boucle(besoin: str, faits_a_verifier=(), *, minimum: int = 2, juge=None, persiste=None, lecteur=None) -> dict:
    """Exécute la boucle d'invention pour `besoin`. `faits_a_verifier` = itérable de dicts
    {relation, entite, valeur, observations, [categorie], [source]} = les affirmations FACTUELLES de grounding à
    corroborer (leurs `observations` = veille_corroboration.Observation issues de sources structurées). Abstient au
    1er maillon manquant. Renvoie un dict :
      {statut: PROPOSE|HORS, etape, objectif, candidats:[...], meilleur:{...}|None, trous:[...],
       faits: {persistes:[...], supposes:[...], refuses:[...], conflits:[...]}}.
    Ne lève pas. `juge`/`persiste`/`lecteur` transmis à la corroboration (défauts sound de veille_corroboration)."""
    # 1) OBJECTIF
    decomp = _B.decompose(besoin)
    if decomp.get("statut") != "decompose":
        return {"statut": HORS, "etape": "objectif", "besoin": besoin,
                "raison": "besoin non modélisé (couche objectif à étendre) — abstention plutôt que fabriquer"}

    # 2) ASSEMBLAGE
    assemble = _T.transfere(besoin)
    if assemble.get("statut") != "candidats" or not assemble.get("candidats"):
        return {"statut": HORS, "etape": "assemblage", "besoin": besoin,
                "objectif": decomp.get("objectif_reel"),
                "raison": "aucun candidat composable (principes viables/canaux insuffisants)"}
    candidats = assemble["candidats"]

    # 3) GAP
    trous = _T.manque(besoin)

    # 4) CORROBORATION + WRITEBACK des faits de grounding (chacun jugé + persisté si survit ; sinon supposition)
    persistes, supposes, refuses, conflits = [], [], [], []
    for f in faits_a_verifier:
        try:
            rel, ent, val = f["relation"], f["entite"], f["valeur"]
            obs = f.get("observations", ())
        except (TypeError, KeyError):
            continue                                  # entrée malformée ignorée (jamais devinée)
        res = _VC.corrobore_valeur(
            rel, ent, val, obs,
            categorie=f.get("categorie", "convention"),
            source=f.get("source", f"grounding invention « {besoin} »"),
            minimum=minimum, juge=juge, persiste=persiste, lecteur=lecteur)
        cle = {"relation": rel, "entite": ent, "valeur": res["valeur"],
               "n_independantes": res["n_independantes"], "raison": res["raison"]}
        {_VC.PERSISTE: persistes, _VC.SUPPOSE: supposes,
         _VC.REFUTE: refuses, _VC.CONFLIT: conflits}[res["statut"]].append(cle)

    return {
        "statut": PROPOSE,
        "etape": "complet",
        "besoin": besoin,
        "objectif": decomp.get("objectif_reel"),
        "candidats": [_serialise_candidat(c) for c in candidats],
        "meilleur": _serialise_candidat(candidats[0]),
        "trous": trous,
        "faits": {"persistes": persistes, "supposes": supposes, "refuses": refuses, "conflits": conflits},
        "note": "le CANDIDAT est une SUPPOSITION générative (à éprouver) ; seuls les FAITS 'persistes' ont "
                "survécu à la corroboration + juge réel et sont désormais des faits du store (non-éphémères).",
    }
