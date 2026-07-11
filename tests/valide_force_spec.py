"""
VALIDATION — FORCE DU SPEC (mutation testing, force_spec.py, chantier FORGE atome 4).

Prouve : (1) énumération EXHAUSTIVE des mutants (constantes ±1/0, opérateurs binaires ET comparaisons —
le bug qui ratait Mult est mort) ; (2) un spec FORT tue tous les mutants non équivalents (score 1.0) ;
(3) un spec FAIBLE laisse des survivants et rend un DISCRIMINANT ; (4) BOUCLE CEGIS : ajouter le
discriminant TUE le survivant (score remonte) ; (5) le problème du MUTANT ÉQUIVALENT est géré (un mutant
sémantiquement identique est exclu, jamais compté comme faiblesse) ; (6) SONDES ASYMÉTRIQUES : elles
démasquent des survivants que les sondes symétriques cachaient, SANS créer de fausse faiblesse sur un spec
fort ; (7) TYPE-SAFE : sondes jamais hors du domaine observé (négatifs, non numérique) ; (8) garde
d'entrée (l'expr de référence doit reproduire son spec).
"""
from __future__ import annotations

from garde_ressources import borne
import moteur_invention as MI
import force_spec as F

borne()
ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# (1) ÉNUMÉRATION EXHAUSTIVE — le mutant Mult (x[0]*x[1]) doit être présent (bug de _nb_graines corrigé).
muts = F.mutants("x[0] + x[1]")
check("mutants inclut l'échange d'opérateur Add->Mult (énumération non tronquée)", "x[0] * x[1]" in muts)
check("mutants inclut Add->Sub et les décalages d'index", "x[0] - x[1]" in muts and "x[1] + x[1]" in muts)
check("mutants dé-dupliqués (l'original n'y est pas)", "x[0] + x[1]" not in muts)
# comparaisons : les 3 voisins d'un < sont tous énumérés (le bug comptait 1 seul)
mc = F.mutants("all(_e > 0 for _e in x)")
check("comparaison : >= , < et != sont tous énumérés", all(m in " ".join(mc) for m in (">=", "<", "!=")))

# (2) SPEC FORT -> score 1.0, aucun survivant.
fort = F.force_du_spec("max(x) - min(x)", [([3, 1, 5], 4), ([2, 2], 0), ([5, 0, 9], 9)],
                       [([0, 9, 4], 9), ([7], 0), ([4, 4], 0)])
check("spec fort (amplitude) : score 1.0", fort["score"] == 1.0 and fort["survivants"] == 0)
check("spec fort : discriminant None (rien à renforcer)", fort["discriminant"] is None)

# (3) SPEC FAIBLE -> survivants + discriminant.
faible = F.force_du_spec("x[0] + x[1]", [([2, 2], 4)], [])
check("spec faible (1 paire symétrique) : des survivants non équivalents", faible["survivants"] >= 1)
check("spec faible : score < 1 (faiblesse mesurée)", faible["score"] < 1.0)
check("spec faible : un discriminant (entrée, sortie attendue) est rendu", faible["discriminant"] is not None)

# (4) BOUCLE CEGIS — le discriminant TUE le survivant : l'ajouter au spec fait remonter le score.
d = faible["discriminant"]
surv = MI._callable(faible["survivant_exemple"], "f")
vrai = MI._callable("x[0] + x[1]", "f")
check("le survivant DIVERGE de l'original sur le discriminant (c'est bien une faiblesse réelle)",
      surv(d[0]) != vrai(d[0]))
check("la sortie attendue du discriminant est celle de l'original (vérité par construction)", d[1] == vrai(d[0]))
renforce = F.force_du_spec("x[0] + x[1]", [([2, 2], 4), d], [])
check("CEGIS : spec + discriminant -> score 1.0 (survivant tué)",
      renforce["score"] == 1.0 and renforce["survivants"] == 0)

# (5) MUTANT ÉQUIVALENT — géré au niveau du détecteur ET du rapport (jamais une fausse faiblesse).
check("détecteur : deux réalisations identiques -> pas de divergence (équivalent)",
      F._diverge(lambda x: x[0] + x[0], lambda x: x[0] * 2, [[1], [2], [5]]) is None)
check("détecteur : deux réalisations distinctes -> divergence trouvée",
      F._diverge(lambda x: x[0] + x[1], lambda x: x[1] + x[1], [[1, 2]]) == [1, 2])
eq = F.force_du_spec("x[0] * 2", [([3], 6)], [])
check("rapport : un mutant équivalent (x[-1]*2 sur liste à 1 élément) est ÉCARTÉ, pas compté faiblesse",
      eq["equivalents"] >= 1 and eq["survivants"] == 0 and eq["score"] == 1.0)

# (6) SONDES ASYMÉTRIQUES — l'optimisation chirurgicale : elles démasquent une faiblesse que les sondes
#     symétriques (celles générées par sondes_auto : [2,2]->[3,3]) cachaient. x[1]+x[1] coïncide avec
#     x[0]+x[1] sur toute entrée à éléments ÉGAUX, mais diverge sur une entrée à valeurs distinctes.
f0 = MI._callable("x[0] + x[1]", "f")
g0 = MI._callable("x[1] + x[1]", "f")
check("symétrique SEUL : x[1]+x[1] passe pour équivalent (divergence non vue)",
      F._diverge(f0, g0, [[2, 2], [3, 3], [4, 4]]) is None)
asym = F._sondes_asymetriques([([2, 2], 4)])
check("_sondes_asymetriques forge une entrée à valeurs distinctes et sa renversée", [1, 2] in asym and [2, 1] in asym)
check("asymétrique : la divergence est DÉMASQUÉE (x[1]+x[1] est bien une faiblesse)",
      F._diverge(f0, g0, asym) is not None)
check("sondes asymétriques : ZÉRO fausse faiblesse sur un spec fort", fort["survivants"] == 0)

# (7) TYPE-SAFE / DOMAINE — sur un domaine négatif, aucune sonde hors-domaine ne crée de faux survivant.
neg = F.force_du_spec("max(x) - min(x)", [([-3, -1], 2), ([2, 2], 0)], [([0, -9], 9), ([5, 5], 0)])
check("domaine négatif : spec fort reste 1.0 (pas de sonde hors-domaine)", neg["score"] == 1.0)
# sur une liste de chaînes, les sondes asymétriques numériques ne s'appliquent pas (pas d'erreur)
check("séquence non numérique : pas de sonde asymétrique forgée (type-safe)",
      F._sondes_asymetriques([(["a", "b"], "ab")]) == [])

# (8) GARDE D'ENTRÉE — une expr qui ne reproduit pas son propre spec est refusée (rien à mesurer).
try:
    F.force_du_spec("x[0] - x[1]", [([2, 2], 4)], [])
    check("garde d'entrée : expr non conforme au spec -> ValueError", False)
except ValueError:
    check("garde d'entrée : expr non conforme au spec -> ValueError", True)

print(f"\nFORCE_SPEC VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
