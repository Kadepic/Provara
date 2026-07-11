#!/usr/bin/env python3
"""VALIDE le MÉCANISME d'audit de cohérence ORDRE (audit_coherence.py) — FAUX=0 sur le diagnostic lui-même.

On ne teste PAS que le store est 100 % cohérent (il ne l'est pas : ~3300 contradictions naissance/décès réelles) :
on teste que l'OUTIL est SOUND. Cœur = une FIXTURE SYNTHÉTIQUE en tmpdir avec des cas connus (violation posée
détectée, égalité tolérée, valeur non-int ignorée, entité non partagée ignorée, appariage auto correct). Puis un
passage non-régressif sur l'échantillon committé (structure du rapport, pas de crash). LÉGER : pas de base complète.
"""
import json
import os
import sys
import tempfile

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

NONREG_SCAN_SOURCES = True   # gate-SCANNER (parcourt datasets/ par chemin) : le cache de _nonreg la relance toujours

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def _ecris(dossier, relation, paires):
    """Écrit datasets/<relation>.jsonl self-describing depuis [(entite, valeur), …]."""
    with open(os.path.join(dossier, relation + ".jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"_relation": relation, "_categorie": "passe", "_source": "fixture"}) + "\n")
        for e, v in paires:
            fh.write(json.dumps({"entite": e, "valeur": v}) + "\n")


# ─────────────────────────── 1) SOUNDNESS sur fixture synthétique ───────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    # Couple AUTO début/fin : débuts et fins de « test ».
    _ecris(tmp, "annee_debut_test", [
        ("A", "1990"),      # A : 1990 <= 1995  -> COHÉRENT
        ("B", "2000"),      # B : 2000 >  1980  -> VIOLATION posée
        ("C", "1850"),      # C : 1850 == 1850  -> égalité, COHÉRENT (pas une violation)
        ("D", "1700"),      # D : valeur fin non-int -> IGNORÉ
        ("E", "1600"),      # E : absent côté fin -> IGNORÉ
        ("G", "-50"),       # G : -50 <= -10    -> COHÉRENT (années négatives ordonnées)
        ("H", "-10"),       # H : -10 >  -99    -> VIOLATION posée (négatifs)
    ])
    _ecris(tmp, "annee_fin_test", [
        ("A", "1995"),
        ("B", "1980"),
        ("C", "1850"),
        ("D", "vers 1720"),   # non parsable -> le couple D est IGNORÉ (soundness : jamais compté violation)
        ("F", "1500"),        # absent côté début -> IGNORÉ
        ("G", "-10"),
        ("H", "-99"),
    ])
    # Couple SÉMANTIQUE naissance/décès (déclaré) : une violation dure.
    _ecris(tmp, "annee_naissance_personne", [("Zoé", "1970"), ("Yann", "2005")])
    _ecris(tmp, "annee_deces_personne", [("Zoé", "1990"), ("Yann", "1405")])   # Yann : né après sa mort -> viol.

    os.environ["LECTEUR_DATASETS_DIR"] = tmp
    # Import APRÈS avoir posé l'env (le module fige _LECT à l'import).
    import importlib
    import audit_coherence as AC
    importlib.reload(AC)

    # -- audit de la paire auto isolée --
    r = AC.audite_paire("annee_debut_test", "annee_fin_test")
    check(r["communs"] == 6, f"communs = A,B,C,D,G,H partagés = 6 (obtenu {r['communs']})")
    check(r["comparables"] == 5, f"comparables (int des deux côtés) = A,B,C,G,H (D non-int exclu) = 5 (obtenu {r['comparables']})")
    check(r["violations"] == 2, f"violations = B et H = 2 (obtenu {r['violations']})")
    ents_viol = {e for e, _, _ in r["exemples"]}
    check(ents_viol == {"B", "H"}, f"les violations sont exactement B et H (obtenu {ents_viol})")
    check("C" not in ents_viol, "égalité (C : 1850==1850) N'EST PAS une violation")
    check("D" not in ents_viol, "valeur non-int (D) IGNORÉE, jamais violation (soundness)")
    check("E" not in ents_viol and "F" not in ents_viol, "entités non partagées (E, F) ignorées")

    # -- appariage : la paire auto ET la paire sémantique sont découvertes --
    paires = {(a, b) for a, b, _ in AC.paires_disponibles()}
    check(("annee_debut_test", "annee_fin_test") in paires, "paire AUTO début/fin découverte par le nom")
    check(("annee_naissance_personne", "annee_deces_personne") in paires, "paire SÉMANTIQUE déclarée découverte")

    # -- audit global : agrégation exacte --
    g = AC.audit(details=True)
    check(g["paires"] == 2, f"2 paires disponibles (obtenu {g['paires']})")
    check(g["violations"] == 3, f"3 violations totales (B, H, Yann) (obtenu {g['violations']})")
    check(g["paires_en_conflit"] == 2, "les 2 paires sont en conflit")
    check(g["top"][0][3] >= g["top"][1][3], "top trié par nombre de violations décroissant")
    somme = sum(t[3] for t in g["top"])
    check(somme == g["violations"], "somme des violations par paire == total (aucune perdue/doublée)")

    # -- FRUGALITÉ : le sens de comparaison est correct quel que soit le fichier chargé (petit/grand) --
    # naissance (2) plus petit que décès (2) : égalité de taille, on force l'autre sens en vérifiant le résultat.
    rn = AC.audite_paire("annee_naissance_personne", "annee_deces_personne")
    check(rn["violations"] == 1 and rn["exemples"][0][0] == "Yann",
          "sens min/max correct : Yann (2005>1405) détecté, Zoé (1970<1990) non")

# ─────────────────────────── 2) NON-RÉGRESSION sur l'échantillon committé ───────────────────────────
_ECHANT = os.path.join(os.path.dirname(_ICI), "datasets", "lecteur")
if os.path.isdir(_ECHANT):
    os.environ["LECTEUR_DATASETS_DIR"] = _ECHANT
    importlib.reload(AC)
    e = AC.audit()
    check(e["paires"] >= 5, f"échantillon : au moins 5 paires ORDRE appariées (obtenu {e['paires']})")
    check(e["comparables"] > 0, "échantillon : des couples comparables existent")
    check(0 <= e["violations"] <= e["comparables"], "violations dans [0, comparables]")
    check(e["paires_en_conflit"] <= e["paires"], "paires en conflit ≤ paires totales")
    check(all(e["top"][i][3] >= e["top"][i + 1][3] for i in range(len(e["top"]) - 1)),
          "top de l'échantillon trié décroissant")
else:
    print("  (échantillon committé absent : partie 2 sautée)")

print(f"\n=== valide_audit_coherence : {ok} OK, {ko} KO ===")
sys.exit(1 if ko else 0)
