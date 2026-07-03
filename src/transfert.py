"""
TRANSFERT INTER-DOMAINES — l'ASSEMBLEUR (machine-inventeur) : composer les leviers HONNÊTES d'un besoin en
combinaisons inédites, comme l'humain a inventé la voiture en transférant des pièces d'un domaine à l'autre
(demande Yohan 2026-07-02 : « donne-lui tout ce qui lui sera nécessaire »).

IDÉE. La percée (voiture, avion, voiture autonome) n'a jamais violé une loi : elle a ASSEMBLÉ des briques
existantes dans une combinaison que personne n'avait osée. Cette brique fait ça sur un besoin : elle prend les
leviers validés par `besoin.py` (canaux du corps, principes jugés, stratégies naturelles) et les COMPOSE en
candidats-stacks, chacun servi comme SUPPOSITION (atome génératif) — jamais comme fait.

GARDE PHYSIQUE INTÉGRÉE (FAUX=0, réutilise l'arbitrage) :
  • un candidat contenant un principe RÉFUTÉ (coherence_physique) est EXCLU ;
  • un candidat SANS PUITS de chaleur nommé est EXCLU (pas de froid gratuit — 2nd principe) ;
  • un candidat cohérent RESTE une SUPPOSITION : on ne prétend JAMAIS qu'il « marche » (efficacité non jugée) ;
  • besoin inconnu / aucune brique -> HORS (le manque devient VISIBLE — « voir ce qui manque »).

Le substrat de mécanismes est CURATÉ (principes + canaux + stratégies naturelles de `besoin.py`, chaînes de
`substrat_physique`). Il GRANDIT en ajoutant des effets/stratégies : c'est ainsi qu'on « voit ce qui manque ».
"""
from __future__ import annotations

from collections import namedtuple

import atome as A
import besoin as B

HORS = "hors"

# Réductions d'apports (le levier « empêcher la chaleur d'entrer » — n'a besoin d'AUCUN puits).
_REDUCTIONS = [
    ("ombrage extérieur (volet/BSO/screen)", "bloque 90–98 % du rayonnement solaire avant le vitrage"),
    ("réduction des charges internes (LED, débrancher les veilles)", "supprime 50–400 W dissipés en continu"),
]

Candidat = namedtuple("Candidat", ["titre", "atome", "score", "silencieux", "solide", "puits",
                                    "livraison", "inspiration_nature", "composants"])


def _canaux_livraison(decomp):
    """Canaux d'échange du corps utilisables pour LIVRER le froid : silencieux d'abord, PUIS ceux qui ciblent
    directement le corps (rayonnement/conduction), puis alphabétique. Corrige le tie-break qui écartait le
    rayonnement (le meilleur canal radiant)."""
    cx = list(decomp["canaux"])
    cx.sort(key=lambda c: (not c.silencieux, c.canal not in ("rayonnement", "conduction"), c.canal))
    return cx


def _puits_reel(principe: dict) -> bool:
    """Un candidat n'est physiquement viable que si son principe nomme un PUITS de chaleur (hors « aucun »)."""
    p = (principe.get("puits") or "").lower()
    return bool(p) and "aucun" not in p


def _inspiration(livraison_canal: str) -> str:
    """Rattache la stratégie naturelle la plus parlante (biomimétisme) au canal de livraison."""
    nat = B.strategies_naturelles()
    if livraison_canal in ("rayonnement", "conduction"):
        for s in nat:
            if "grotte" in s["exemple"]:
                return s["exemple"] + " → " + s["lecon"]
    for s in nat:
        if "forêt" in s["exemple"]:
            return s["exemple"] + " → " + s["lecon"]
    return nat[0]["exemple"] if nat else ""


def _score(principe: dict, canal, avec_reduction: bool) -> tuple[int, str]:
    """Score TRANSPARENT (favorise silencieux + puits sûr + solide + cible le corps + simple/abordable)."""
    s, notes = 0, []
    if principe["silencieux"]:
        s += 2; notes.append("silencieux")
    else:
        notes.append("bruyant")
    if principe["solide_sans_gaz"]:
        s += 1; notes.append("sans gaz/compresseur")
    if _puits_reel(principe):
        s += 2; notes.append("puits réel")
    if canal.silencieux:
        s += 1
    if canal.canal in ("rayonnement", "conduction"):
        s += 2; notes.append("cible le corps (~100 W, pas l'air)")
    if avec_reduction:
        s += 1; notes.append("apports réduits")
    mat = (principe.get("maturite") or "").lower()
    if any(k in mat for k in ("simple", "mature")):
        s += 1; notes.append("abordable/disponible")
    p = (principe.get("puits") or "").lower()
    if "humide" in p:                                      # évaporatif en pièce fermée -> humidité
        s -= 2; notes.append("humidifie (problématique en pièce fermée)")
    return s, ", ".join(notes)


def _viables(besoin: str, exiger_silence: bool):
    """Principes VIABLES : cohérents (SUPPOSITION, pas RÉFUTÉ) ET puits réel ET (silencieux si exigé). Le SILENCE
    est ici une EXIGENCE (pas un bonus mou) : un principe bruyant est EXCLU, comme un sans-puits."""
    return [p for p in B.principes(besoin)["liste"]
            if p["atome"].statut == A.SUPPOSITION and _puits_reel(p) and (p["silencieux"] or not exiger_silence)]


def transfere(besoin: str = "rafraichir une piece", k: int = 5, *, exiger_silence: bool = True) -> dict:
    """Compose des candidats-stacks pour `besoin` : principe VIABLE × canal de livraison (corps d'abord) + réduction
    d'apports + inspiration naturelle. EXCLUT réfutés, sans-puits, et bruyants (silence exigé par défaut). Rend des
    SUPPOSITIONS classées par PLAUSIBILITÉ DE COMPOSITION (silence/puits/cible-corps/apports) — PAS par efficacité/
    COP (non jugée ici). Inconnu -> HORS."""
    decomp = B.decompose(besoin)
    if decomp["statut"] != "decompose":
        return {"statut": HORS, "besoin": besoin, "raison": "besoin non décomposable — brique d'objectif à ajouter"}
    viables = _viables(besoin, exiger_silence)
    canaux = _canaux_livraison(decomp)
    livraison = canaux[:2]                                # 2 meilleurs : silencieux + ciblant le corps
    reduction_titres = [t for t, _ in _REDUCTIONS]

    candidats = []
    for p in viables:
        for c in livraison:
            sc, notes = _score(p, c, avec_reduction=True)
            titre = f"{p['nom']} → livré par {c.canal} (surface/contact frais)"
            composants = reduction_titres + [f"principe : {p['nom']}", f"puits : {p['puits']}",
                                             f"livraison : {c.levier}"]
            insp = _inspiration(c.canal)
            base = (f"stack : {' + '.join(reduction_titres)} + {p['nom']} (puits {p['puits']}) + livraison "
                    f"{c.canal} ; inspiration nature : {insp} ; propriétés : {notes}")
            conf = max(0.05, min(0.95, sc / 12.0))        # borné ]0,1[ : score -> plausibilité de composition
            at = A.suppose(f"dispositif : {titre}", A.GENERATIF,
                           A.Portee(A.DOMAINE, "candidat composé pour " + besoin + " ; efficacité/COP non jugés"),
                           conf, base)
            candidats.append(Candidat(titre, at, sc, p["silencieux"], p["solide_sans_gaz"], p["puits"],
                                      c.canal, insp, composants))
    candidats.sort(key=lambda x: (-x.score, x.titre))
    return {
        "statut": "candidats",
        "besoin": besoin,
        "objectif_reel": decomp["objectif_reel"],
        "candidats": candidats[:k],
        "note": "classement = PLAUSIBILITÉ DE COMPOSITION (silence, puits réel, cible le corps, apports réduits), "
                "PAS un ordre d'efficacité/COP — l'efficacité reste à juger séparément (bancs d'essai/mesure).",
        "manque": manque(besoin),
    }


def manque(besoin: str = "rafraichir une piece") -> list[str]:
    """« Voir ce qui manque » : diagnostique les trous — canaux silencieux non exploités en livraison, absence
    d'option abordable+solide+silencieuse+puits-sûr, puits gratuit non catalogué. Auto-suffisant."""
    decomp = B.decompose(besoin)
    if decomp["statut"] != "decompose":
        return ["besoin non modélisé : ajouter sa décomposition (couche objectif)"]
    viables = _viables(besoin, exiger_silence=True)
    trous = []
    # canaux SILENCIEUX du besoin non exploités par la livraison composée (livraison = 2 meilleurs canaux).
    utilises = {c.canal for c in _canaux_livraison(decomp)[:2]}
    non_couverts = [c.canal for c in decomp["canaux"] if c.silencieux and c.canal not in utilises]
    if non_couverts:
        trous.append("canaux silencieux non exploités en livraison : " + ", ".join(non_couverts)
                     + " (leviers additionnels possibles)")
    # option idéale = silencieuse + solide + puits sûr + abordable
    ideale = [p for p in viables if p["solide_sans_gaz"]
              and any(k in (p.get("maturite") or "").lower() for k in ("simple", "mature", "éprouvé"))]
    if not ideale:
        trous.append("aucune option à la fois silencieuse, solide (sans gaz) ET abordable/mature : "
                     "les effets caloriques (magnéto/élasto/électro) restent au stade recherche → coût à faire baisser")
    # un puits périodique gratuit (nuit/sol) doit être représenté comme principe
    puits = {(p.get("puits") or "").lower() for p in viables}
    if not any("nuit" in x or "sol" in x or "terre" in x for x in puits):
        trous.append("puits périodique gratuit (air nocturne/sol) non représenté comme principe : "
                     "à ajouter au catalogue (stratégie de la maison en pierre)")
    if not trous:
        trous.append("couverture correcte ; prochain gain = abaisser le coût des effets caloriques solides")
    return trous


if __name__ == "__main__":
    r = transfere("rafraichir une piece")
    print("OBJECTIF :", r["objectif_reel"][:90], "...\n")
    print("CANDIDATS COMPOSÉS (classés) :")
    for c in r["candidats"]:
        print(f"  [{c.score:2d}] {c.atome.statut.upper()} {c.titre}")
        print(f"        puits={c.puits} | nature: {c.inspiration_nature[:70]}")
    print("\nCE QUI MANQUE :")
    for m in r["manque"]:
        print("  -", m)
    print("\nBESOIN INCONNU :", transfere("faire du pain")["statut"])
