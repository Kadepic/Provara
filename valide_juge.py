"""
Validation de la BRIQUE 1 (le juge).

Critère de la brique (cf. plan) : sur un problème EXISTANT (HumanEval/0),
  - la bonne solution      -> PASS
  - une solution fausse     -> FAIL
  - une boucle infinie      -> TIMEOUT  (la sandbox coupe)
  - une bombe mémoire       -> KILLED   (la limite mémoire coupe)
  - un code invalide        -> ERROR

Si ces 5 cas tombent juste, le juge est incorruptible côté ressources et
correct côté verdict. On peut bâtir la brique suivante dessus.
"""

from __future__ import annotations

from juge import Limites, juge
from taches import HUMANEVAL_0


def _attendu(nom: str, verdict, statut_attendu: str) -> bool:
    ok = verdict.statut == statut_attendu
    marque = "OK " if ok else "RATÉ"
    print(f"  [{marque}] {nom:<28} -> {verdict.statut:<8} ({verdict.duree_s:.2f}s)"
          f"{'' if ok else f'  ATTENDU={statut_attendu}'}")
    return ok


def main() -> int:
    t = HUMANEVAL_0
    print(f"Validation du juge sur {t.id} :\n")
    resultats = []

    # 1. La solution canonique connue DOIT passer.
    resultats.append(_attendu(
        "bonne solution", juge(t.solution_ref, t.tests), "pass"))

    # 2. Une solution fausse (renvoie toujours False) DOIT échouer.
    fausse = t.prompt + "\n    return False\n"
    resultats.append(_attendu(
        "solution fausse", juge(fausse, t.tests), "fail"))

    # 3. Une boucle infinie DOIT être coupée par le timeout/CPU.
    boucle = t.prompt + "\n    while True:\n        pass\n"
    resultats.append(_attendu(
        "boucle infinie", juge(boucle, t.tests, Limites(temps_s=3, cpu_s=2)), "timeout"))

    # 4. Une bombe mémoire DOIT être tuée par la limite mémoire.
    bombe = t.prompt + "\n    x = [0] * (10**9)\n    return bool(x)\n"
    resultats.append(_attendu(
        "bombe mémoire", juge(bombe, t.tests, Limites(memoire_mo=128)), "killed"))

    # 5. Un code syntaxiquement invalide DOIT être une erreur (pas un pass).
    casse = t.prompt + "\n    return ???\n"
    resultats.append(_attendu(
        "code invalide", juge(casse, t.tests), "error"))

    # 6. SENTINELLE : une sortie prématurée (exit 0 avant les tests) NE DOIT PAS
    #    passer. Sans la sentinelle, le juge dirait 'pass' (faille trouvée via B5).
    exploit = "import sys\n" + t.prompt + "\n    return False\nsys.exit(0)\n"
    resultats.append(_attendu(
        "exploit sortie prématurée", juge(exploit, t.tests), "sabotage"))

    print()
    if all(resultats):
        print(f"BRIQUE 1 VALIDÉE — {len(resultats)}/{len(resultats)} cas justes. Le juge tranche le réel.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)} cas justes. À corriger avant de continuer.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
