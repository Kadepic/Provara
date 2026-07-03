"""
MUTATION DES COMPARAISONS → PRÉDICATS INVENTÉS, dans la boucle vivante (le mur d'avant le contrôle).

L'invention savait muter slice / chaîne de produits / constante / opérateur BINAIRE (M1-M4), mais PAS les
opérateurs de COMPARAISON : elle ne pouvait pas faire émerger un prédicat inverse. On ajoute **M5 — échanger
l'opérateur de comparaison** (`x > 0` -> `x < 0`). Couplé à l'AUTO-ROUTAGE déjà là (`route` : unaire booléen sur
scalaire -> 'predicat', `verse_predicat` câblé) et à l'inclusion des PRÉDICATS dans la matière à muter, le moteur
peut désormais, EN UNE SEULE SESSION : inventer `est_negatif` (en mutant `est_positif`), le ROUTER lui-même en
prédicat, et l'étage BRANCHEMENT composer dessus — résoudre `signe`, qui a besoin des DEUX prédicats.

L'A/B isole EXACTEMENT M5 (`comparaisons` on/off) ; tout le reste (routage, inclusion des prédicats) est commun :
    CONTRÔLE   (comparaisons=False) : l'invention ne peut PAS flipper `>` en `<` -> `est_negatif` HORS-PORTÉE
                                      -> `signe` HORS-PORTÉE (il manque la branche x<0).
    TRAITEMENT (comparaisons=True)  : `est_negatif` INVENTÉ -> routé en prédicat -> `signe` RÉSOLU à branchement.

Critères de MORT (si l'un tombe, la brique est réfutée) :
  1. MUR (unité)     : sans M5, muter `est_positif` ne minte PAS `est_negatif` (x<0).
  2. INVENTION (unité): avec M5, `est_negatif` est minté ET GÉNÉRALISE (held-out) — vrai prédicat, pas un fluke.
  3. ROUTAGE         : `est_negatif` est rangé en 'predicat' par la signature (unaire booléen sur scalaire).
  4. CONTRÔLE        : montée sans M5 -> `est_negatif` ET `signe` HORS-PORTÉE.
  5. SESSION AUTONOME: montée avec M5 -> `est_negatif` inventé+routé, `signe` RÉSOLU à `branchement`, UNE session.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee, route
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurInvention, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, sig, tests, held, ref_corps, diff):
    prompt = f'def {fn}({sig}):\n    """..."""'
    ref = f"def {fn}(*args, **kwargs):\n{ref_corps}\n"
    return Tache(id=f"mc/{fn}", point_entree=fn, prompt=prompt, tests=tests,
                 tests_held_out=held, solution_ref=ref, difficulte=diff)


# --- Curriculum gradué : inventer un PRÉDICAT, puis composer un BRANCHEMENT dessus ---------------
TACHES = [
    _t("est_negatif", "x",
       "def check(c):\n    assert c(-3) is True\n    assert c(2) is False\n    assert c(0) is False\ncheck(est_negatif)",
       "def check(c):\n    assert c(-1) is True\n    assert c(5) is False\n    assert c(-100) is True\ncheck(est_negatif)",
       "    return args[0] < 0", 1),
    _t("signe", "x",
       "def check(c):\n    assert c(5) == 1\n    assert c(-3) == -1\n    assert c(0) == 0\ncheck(signe)",
       "def check(c):\n    assert c(2) == 1\n    assert c(-7) == -1\n    assert c(0) == 0\ncheck(signe)",
       "    return 1 if args[0] > 0 else (-1 if args[0] < 0 else 0)", 2),
]
CIBLE = "signe"

# Seed : le SEUL prédicat donné est `est_positif`. `est_negatif` n'est PAS donné — il sera INVENTÉ (mutation M5).
EST_POSITIF = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")


def _etage_de(journal, point_entree):
    for p in journal:
        if p.point_entree == point_entree and p.confirme:
            return p.etage
    return None


def _montee(d, suffixe, comparaisons):
    """Une montée FRAÎCHE (orchestrateur + store isolés), inventer=True, auto-routage ON.
    Seul `comparaisons` (M5) change entre les deux bras."""
    store = Store(Path(d) / f"s_{suffixe}.jsonl")
    pred = Predicteur(store, types=TYPES_RICHES)
    orch = GenerateurOrchestre(store, predicats=[EST_POSITIF], predicteur=pred,
                               inventer=True, comparaisons=comparaisons)
    curateur = CurateurGradue(TACHES, seuil=0.7, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=True, routage=True)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []
    T_NEG = TACHES[0]

    # 1. MUR (unité) : sans M5, muter est_positif ne minte PAS est_negatif.
    sans_m5 = GenerateurInvention([EST_POSITIF], comparaisons=False)
    resultats.append(_check(
        "MUR : sans M5, l'invention ne minte PAS `est_negatif` (ne peut pas flipper `>` en `<`)",
        _resout(sans_m5, T_NEG) is None))

    # 2. INVENTION (unité) : avec M5, est_negatif minté ET généralise (held-out).
    avec_m5 = GenerateurInvention([EST_POSITIF], comparaisons=True)
    g_neg = _resout(avec_m5, T_NEG)
    if g_neg:
        print(f"    minté -> {g_neg.strip().splitlines()[-1].strip()}")
    generalise = g_neg is not None and juge(g_neg, T_NEG.tests_held_out, LIM).passe
    resultats.append(_check(
        "INVENTION : avec M5, `est_negatif` (x<0) minté et passe le HELD-OUT (vrai prédicat, pas un fluke)",
        generalise))

    # 3. ROUTAGE : est_negatif rangé en 'predicat' par sa signature.
    r = route("def est_negatif(*args, **kwargs):\n    return args[0] < 0\n", "est_negatif", LIM)
    print(f"    routage : est_negatif -> {r}")
    resultats.append(_check("ROUTAGE : `est_negatif` rangé en 'predicat' (unaire booléen sur scalaire)",
                            r == "predicat"))

    # 4+5. A/B en SESSION vivante : seul M5 change.
    with tempfile.TemporaryDirectory() as d:
        print("\n  CONTRÔLE — montée SANS M5 (comparaisons=False) :")
        j_sans = _montee(d, "sans", comparaisons=False)
        for p in j_sans:
            print(p.resume())
        f_sans = franchies(j_sans)

        print("\n  TRAITEMENT — montée AVEC M5 (comparaisons=True) :")
        j_avec = _montee(d, "avec", comparaisons=True)
        for p in j_avec:
            print(p.resume())
        f_avec = franchies(j_avec)
        etage_cible = _etage_de(j_avec, CIBLE)
        etage_neg = _etage_de(j_avec, "est_negatif")

    print()
    # 4. CONTRÔLE : sans M5, est_negatif ET signe hors-portée.
    resultats.append(_check(
        f"CONTRÔLE : sans M5 -> `est_negatif` ET `{CIBLE}` HORS-PORTÉE (la branche x<0 manque)",
        "est_negatif" not in f_sans and CIBLE not in f_sans))

    # 5. SESSION AUTONOME : avec M5, est_negatif inventé+routé, signe résolu à branchement, une session.
    resultats.append(_check(
        f"SESSION AUTONOME : avec M5 -> `est_negatif` inventé (étage `{etage_neg}`) + routé, puis `{CIBLE}` "
        f"RÉSOLU à l'étage `{etage_cible}` en UNE session",
        "est_negatif" in f_avec and CIBLE in f_avec and etage_cible == "branchement"))

    print()
    if all(resultats):
        print(f"MUTATION DES COMPARAISONS VALIDÉE — {len(resultats)}/{len(resultats)}. M5 ouvre à l'invention le "
              f"dernier registre qui lui échappait : les PRÉDICATS. Le moteur invente `est_negatif` en mutant "
              f"`est_positif`, le ROUTE lui-même en prédicat (signature), et BRANCHEMENT compose dessus pour "
              f"résoudre `signe` — dans UNE session, jugé held-out, sans main. La boucle "
              f"invention→registre→mécanisme couvre maintenant op, primitive ET prédicat. (Caveat base-froide : "
              f"l'A/B isole le mécanisme ; le régime se déplacera avec l'apprentissage.)")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La mutation des comparaisons ne ferme pas (encore) la "
          f"boucle prédicat : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
