"""
AUDIT DE COHÉRENCE INTER-RELATIONS — le store contient-il deux faits qui NE PEUVENT PAS être vrais ensemble ?

Le write path (`lecteur.ingere_table`) refuse déjà les conflits INTRA-relation (même clé -> valeur divergente lève).
Il ne voit RIEN entre deux relations distinctes. Or certains couples de relations portent une contrainte d'ordre
DURE, indépendante de la source : l'année de début d'un mandat ne peut pas être postérieure à son année de fin ;
une personne ne peut pas décéder avant de naître. Ce module DIAGNOSTIQUE ces contradictions sur le store existant.

TYPE DE RÈGLE (atome 1) : ORDRE — pour un couple (rel_min, rel_max) partageant l'espace d'entités, on exige
`int(rel_min[e]) <= int(rel_max[e])` pour toute entité `e` présente des deux côtés. Une violation (vmin > vmax
STRICT) est une contradiction dure : aucune valeur d'incertitude/arrondi ne la rend simultanément vraie.

SOUNDNESS (FAUX=0 sur le diagnostic lui-même) :
  - On ne juge QUE ce qui est comparable : entité présente des DEUX côtés ET les deux valeurs parsables en `int`.
    Tout le reste est IGNORÉ (jamais compté comme violation) -> zéro faux « incohérent ».
  - L'égalité (début == fin, même année) est COHÉRENTE, pas une violation.
  - Le store est mono-valué par entité (garanti par ingere_table), donc pas d'ambiguïté « quelle valeur comparer ».

APPARIAGE :
  - AUTO (patron générique par le nom) : tout couple `annee_debut_X` / `annee_fin_X` (même suffixe -> même type
    d'objet, même espace de clés -> appariage SOUND).
  - SÉMANTIQUE (déclaré) : les couples à nom non symétrique (naissance/décès), listés explicitement ci-dessous.

FRUGAL : les paires sont traitées SÉQUENTIELLEMENT ; pour chacune on charge en mémoire le PLUS PETIT des deux
fichiers puis on STREAME l'autre. Pic RAM = plus gros « petit côté » d'une seule paire. Read-only, stdlib pur,
souverain (aucun réseau). Usage : `python3 audit_coherence.py` (rapport) ; importable : `audit() -> dict`.
"""
from __future__ import annotations

import json
import os

_ICI = (os.environ.get("VERAX_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LECT = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(_ICI, "datasets", "lecteur")

# Couples à nom NON symétrique : (relation « min », relation « max », étiquette lisible). L'auto-appariage
# début/fin les manquerait (les préfixes diffèrent) -> on les déclare. Ajouter ici tout couple ordonné dur.
PAIRES_SEMANTIQUES = [
    ("annee_naissance_personne", "annee_deces_personne", "naissance ≤ décès"),
]

_PREFIXE_DEBUT = "annee_debut_"
_PREFIXE_FIN = "annee_fin_"

# Nombre d'exemples de violation retenus PAR PAIRE pour le rapport (borne mémoire du rapport).
_MAX_EXEMPLES = 12


def _relations_presentes() -> set:
    if not os.path.isdir(_LECT):
        return set()
    return {f[:-6] for f in os.listdir(_LECT) if f.endswith(".jsonl")}


def _auto_paires(relations: set) -> list:
    """Couples (annee_debut_X, annee_fin_X, étiquette) dont les DEUX fichiers existent. Suffixe commun ->
    même type d'objet -> appariage sound."""
    out = []
    for r in sorted(relations):
        if r.startswith(_PREFIXE_DEBUT):
            suffixe = r[len(_PREFIXE_DEBUT):]
            fin = _PREFIXE_FIN + suffixe
            if fin in relations:
                out.append((r, fin, f"début ≤ fin ({suffixe})"))
    return out


def paires_disponibles() -> list:
    """Toutes les paires ORDRE dont les deux relations sont présentes dans le store (auto + sémantiques),
    dé-doublonnées par (rel_min, rel_max)."""
    presentes = _relations_presentes()
    paires = _auto_paires(presentes)
    for rmin, rmax, etiq in PAIRES_SEMANTIQUES:
        if rmin in presentes and rmax in presentes:
            paires.append((rmin, rmax, etiq))
    vues, uniques = set(), []
    for rmin, rmax, etiq in paires:
        cle = (rmin, rmax)
        if cle not in vues:
            vues.add(cle)
            uniques.append((rmin, rmax, etiq))
    return uniques


def _nb_lignes(chemin: str) -> int:
    """Comptage rapide par blocs (newlines), sans parser le JSON. -1 pour l'en-tête self-describing."""
    n = 0
    try:
        with open(chemin, "rb") as fh:
            while True:
                bloc = fh.read(1 << 20)
                if not bloc:
                    break
                n += bloc.count(b"\n")
    except OSError:
        return 0
    return max(0, n - 1)


def _charge_dico(chemin: str) -> dict:
    """{entite: valeur} d'un .jsonl self-describing (en-tête `_relation` sauté). Dernière écriture gagne, mais
    le store est mono-valué par entité (ingere_table) donc sans effet ici."""
    d = {}
    try:
        with open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                obj = json.loads(ligne)
                if "_relation" in obj:
                    continue
                d[obj["entite"]] = obj["valeur"]
    except OSError:
        return {}
    return d


def _entier(v):
    """int(v) tolérant (strip), ou None si non parsable -> la valeur est alors IGNORÉE (soundness)."""
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def audite_paire(rmin: str, rmax: str) -> dict:
    """Compare une paire ORDRE. Charge le PLUS PETIT fichier en dict, streame l'autre. Renvoie
    {communs, comparables, violations, exemples:[(entite, vmin, vmax), …]}. Une violation = vmin > vmax."""
    fmin = os.path.join(_LECT, rmin + ".jsonl")
    fmax = os.path.join(_LECT, rmax + ".jsonl")
    # Charger le plus petit des deux ; streamer l'autre.
    charge_min = _nb_lignes(fmin) <= _nb_lignes(fmax)
    if charge_min:
        table, stream = _charge_dico(fmin), fmax          # table = valeurs « min », stream = valeurs « max »
    else:
        table, stream = _charge_dico(fmax), fmin          # table = valeurs « max », stream = valeurs « min »
    communs = comparables = violations = 0
    exemples = []
    try:
        with open(stream, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                obj = json.loads(ligne)
                if "_relation" in obj:
                    continue
                e = obj["entite"]
                if e not in table:
                    continue
                communs += 1
                if charge_min:
                    vmin, vmax = _entier(table[e]), _entier(obj["valeur"])
                else:
                    vmin, vmax = _entier(obj["valeur"]), _entier(table[e])
                if vmin is None or vmax is None:
                    continue
                comparables += 1
                if vmin > vmax:
                    violations += 1
                    if len(exemples) < _MAX_EXEMPLES:
                        exemples.append((e, vmin, vmax))
    except OSError:
        pass
    return {"communs": communs, "comparables": comparables, "violations": violations, "exemples": exemples}


def audit(details: bool = False) -> dict:
    """Rapport de cohérence ORDRE sur tout le store. Renvoie {paires, paires_en_conflit, communs, comparables,
    violations, top:[(rmin, rmax, étiquette, n_violations), …]}. `details=True` ajoute `par_paire` (exemples)."""
    paires = paires_disponibles()
    total_c = total_cmp = total_v = 0
    top = []
    par_paire = {}
    for rmin, rmax, etiq in paires:
        r = audite_paire(rmin, rmax)
        total_c += r["communs"]
        total_cmp += r["comparables"]
        total_v += r["violations"]
        top.append((rmin, rmax, etiq, r["violations"]))
        if details:
            par_paire[(rmin, rmax)] = r
    top.sort(key=lambda t: -t[3])
    out = {
        "paires": len(paires),
        "paires_en_conflit": sum(1 for t in top if t[3] > 0),
        "communs": total_c,
        "comparables": total_cmp,
        "violations": total_v,
        "top": top,
    }
    if details:
        out["par_paire"] = par_paire
    return out


if __name__ == "__main__":
    r = audit(details=True)
    print(f"=== AUDIT DE COHÉRENCE ORDRE ({r['paires']} paires, {r['comparables']:,} couples comparables) ===")
    print(f"  paires en conflit : {r['paires_en_conflit']}/{r['paires']}")
    print(f"  VIOLATIONS (min > max, contradiction dure) : {r['violations']:,}\n")
    for rmin, rmax, etiq, n in r["top"]:
        if n == 0:
            continue
        print(f"  {n:>6,}  {etiq}")
        for e, vmin, vmax in r["par_paire"][(rmin, rmax)]["exemples"][:4]:
            print(f"            {e!r} : {vmin} > {vmax}")
