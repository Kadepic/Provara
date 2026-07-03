"""
VALIDE cycles_economiques.py — held-out ADVERSE.

Ancres CONNUES (structure consensuelle du cycle + classification Conference Board, NON circulaires) :
  • 4 phases ordonnées : expansion(1) -> sommet/pic(2) -> recession(3) -> creux/depression(4) -> expansion.
  • après le PIC vient la RÉCESSION ; après le creux vient l'expansion (le cycle boucle).
  • récession technique = 2 trimestres CONSÉCUTIFS de baisse du PIB (CAS de la spéc).
  • indicateurs avancés (permis de construire, bourse, courbe des taux) / coïncidents (PIB, production
    industrielle, emploi salarié) / retardés (taux de chômage, inflation, taux préférentiel).
SOUNDNESS (jamais un faux -> ValueError) : phase inconnue, indicateur hors catalogue, libellé ambigu
  (« taux d'intérêt » seul), non-str, vide, séquence vide / non numérique / non finie.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import cycles_economiques as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) LES 4 PHASES, ordonnées (CAS « 4 phases ») ──
ph = M.phases()
check(len(ph) == 4, "le cycle a exactement 4 phases")
check(ph == ("expansion", "sommet/pic", "recession", "creux/depression"), "ordre canonique des 4 phases")
check(len(set(ph)) == 4, "les 4 phases sont distinctes")

# ── 2) phase_cycle : description + ordre ──
check(M.phase_cycle("expansion")["ordre"] == 1, "expansion = ordre 1")
check(M.phase_cycle("sommet/pic")["ordre"] == 2, "sommet/pic = ordre 2")
check(M.phase_cycle("recession")["ordre"] == 3, "recession = ordre 3")
check(M.phase_cycle("creux/depression")["ordre"] == 4, "creux/depression = ordre 4")
check(M.phase_cycle("pic")["nom"] == "sommet/pic", "synonyme 'pic' -> sommet/pic")
check(M.phase_cycle("récession")["nom"] == "recession", "accent : 'récession' -> recession")
check(M.phase_cycle("dépression")["nom"] == "creux/depression", "synonyme 'dépression' -> creux/depression")
check(M.phase_cycle("PEAK")["nom"] == "sommet/pic", "casse + EN : 'PEAK' -> sommet/pic")
check(M.phase_cycle("contraction")["nom"] == "recession", "synonyme 'contraction' -> recession")
check(isinstance(M.phase_cycle("expansion")["description"], str) and
      len(M.phase_cycle("expansion")["description"]) > 10, "description présente et non vide")
# ordre cohérent avec la position dans phases()
check(all(M.phase_cycle(p)["ordre"] == i + 1 for i, p in enumerate(ph)), "ordre == position dans phases()")

# ── 3) phase_suivante — le cycle et « après pic vient récession » ──
check(M.phase_suivante("sommet/pic") == "recession", "après le PIC vient la RÉCESSION (CAS spéc)")
check(M.phase_suivante("pic") == "recession", "synonyme : après 'pic' -> recession")
check(M.phase_suivante("expansion") == "sommet/pic", "expansion -> sommet/pic")
check(M.phase_suivante("recession") == "creux/depression", "recession -> creux/depression")
check(M.phase_suivante("creux/depression") == "expansion", "creux -> expansion (le cycle boucle)")
# tour complet : 4 transitions ramènent au départ
cur = "expansion"
for _ in range(4):
    cur = M.phase_suivante(cur)
check(cur == "expansion", "4 transitions ramènent à l'expansion (cycle fermé)")
# l'ordre avance de 1 modulo 4 à chaque transition
check(all(M.phase_cycle(M.phase_suivante(p))["ordre"] == (M.phase_cycle(p)["ordre"] % 4) + 1 for p in ph),
      "ordre(suivante) = ordre%4 + 1 pour chaque phase")

# ── 4) definition_recession — règle technique (CAS « 2 trimestres ») ──
dr = M.definition_recession()
check(dr["nombre_trimestres"] == 2, "récession technique = 2 trimestres")
check(dr["consecutifs"] is True, "trimestres CONSÉCUTIFS")
check("PIB" in dr["regle"] or "PIB" in dr["critere"], "critère = baisse du PIB")
check("consécuti" in dr["regle"].lower(), "règle mentionne 'consécutifs'")

# ── 5) est_recession_technique — application de la règle ──
check(M.est_recession_technique([-0.1, -0.2]) is True, "2 trimestres de baisse consécutifs -> récession")
check(M.est_recession_technique([-0.5]) is False, "1 seul trimestre de baisse -> PAS récession technique")
check(M.est_recession_technique([-0.1, 0.2, -0.3]) is False, "baisses NON consécutives -> PAS récession")
check(M.est_recession_technique([0.3, -0.1, -0.2, 0.5]) is True, "2 baisses consécutives au milieu -> récession")
check(M.est_recession_technique([0.3, 0.4, 0.5]) is False, "croissance continue -> pas de récession")
check(M.est_recession_technique([0.0, 0.0]) is False, "stagnation (0) n'est pas une baisse -> pas de récession")
check(M.est_recession_technique([-0.0, -0.1, -0.2, -0.3]) is True, "3 baisses consécutives -> récession")

# ── 6) type_indicateur — classification consensuelle ──
check(M.type_indicateur("permis de construire") == "avance", "permis de construire = avancé")
check(M.type_indicateur("cours des actions") == "avance", "cours des actions = avancé")
check(M.type_indicateur("courbe des taux") == "avance", "courbe des taux = avancé")
check(M.type_indicateur("nouvelles commandes") == "avance", "nouvelles commandes = avancé")
check(M.type_indicateur("PIB") == "coincident", "PIB = coïncident")
check(M.type_indicateur("production industrielle") == "coincident", "production industrielle = coïncident")
check(M.type_indicateur("emploi salarié") == "coincident", "emploi salarié = coïncident")
check(M.type_indicateur("taux de chômage") == "retarde", "taux de chômage = retardé")
check(M.type_indicateur("inflation") == "retarde", "inflation = retardé")
check(M.type_indicateur("taux préférentiel") == "retarde", "taux préférentiel = retardé")
check(M.type_indicateur("Taux de Chômage") == "retarde", "casse/accents normalisés")

# ── 7) definition_indicateur + indicateurs ──
check("avant" in M.definition_indicateur("avance").lower(), "avancé = se retourne AVANT")
check("après" in M.definition_indicateur("retarde").lower(), "retardé = se retourne APRÈS")
check("même temps" in M.definition_indicateur("coincident").lower(), "coïncident = en MÊME TEMPS")
check("permis de construire" in M.indicateurs("avance"), "liste avancés contient permis de construire")
check("taux de chomage" in M.indicateurs("retarde"), "liste retardés contient taux de chômage")
# cohérence croisée : chaque libellé listé se reclasse dans son type
check(all(M.type_indicateur(n) == "avance" for n in M.indicateurs("avance")), "indicateurs('avance') cohérents")
check(all(M.type_indicateur(n) == "coincident" for n in M.indicateurs("coincident")),
      "indicateurs('coincident') cohérents")
check(all(M.type_indicateur(n) == "retarde" for n in M.indicateurs("retarde")), "indicateurs('retarde') cohérents")

# ── 8) SOUNDNESS — phases inconnues / non-str / vide ──
check(_leve_v(M.phase_cycle, "croissance forte"), "phase inconnue -> ValueError")
check(_leve_v(M.phase_cycle, "ralentissement"), "ralentissement (≠ récession) -> ValueError")
check(_leve_v(M.phase_cycle, ""), "phase vide -> ValueError")
check(_leve_v(M.phase_cycle, 123), "phase non-str -> ValueError")
check(_leve_v(M.phase_cycle, None), "phase None -> ValueError")
check(_leve_v(M.phase_suivante, "inconnu"), "phase_suivante inconnue -> ValueError")

# ── 9) SOUNDNESS — indicateurs hors catalogue / ambigus ──
check(_leve_v(M.type_indicateur, "taux d'intérêt"), "« taux d'intérêt » seul (ambigu) -> ValueError")
check(_leve_v(M.type_indicateur, "emploi"), "« emploi » seul (ambigu) -> ValueError")
check(_leve_v(M.type_indicateur, "indicateur mystère"), "indicateur inconnu -> ValueError")
check(_leve_v(M.type_indicateur, 42), "indicateur non-str -> ValueError")
check(_leve_v(M.type_indicateur, ""), "indicateur vide -> ValueError")
check(_leve_v(M.definition_indicateur, "inconnu"), "type d'indicateur inconnu -> ValueError")
check(_leve_v(M.indicateurs, "leading"), "indicateurs(type EN inconnu) -> ValueError")

# ── 10) SOUNDNESS — est_recession_technique : données invalides ──
check(_leve_v(M.est_recession_technique, []), "séquence vide -> ValueError")
check(_leve_v(M.est_recession_technique, "abc"), "chaîne (non-liste) -> ValueError")
check(_leve_v(M.est_recession_technique, [0.1, "x"]), "élément non numérique -> ValueError")
check(_leve_v(M.est_recession_technique, [0.1, True]), "booléen refusé -> ValueError")
check(_leve_v(M.est_recession_technique, [float("nan"), -0.2]), "valeur NaN -> ValueError")
check(_leve_v(M.est_recession_technique, [float("inf"), -0.2]), "valeur inf -> ValueError")
check(_leve_v(M.est_recession_technique, {"q1": -0.1}), "dict refusé -> ValueError")

# ── 11) DÉTERMINISME ──
check(M.phase_suivante("expansion") == M.phase_suivante("expansion"), "phase_suivante déterministe")
check(M.phase_cycle("pic") == M.phase_cycle("pic"), "phase_cycle déterministe")
check(M.type_indicateur("PIB") == M.type_indicateur("PIB"), "type_indicateur déterministe")
check(M.est_recession_technique([-0.1, -0.2]) == M.est_recession_technique([-0.1, -0.2]),
      "est_recession_technique déterministe")
check(M.phases() == M.phases(), "phases() déterministe")

print(f"\n=== valide_cycles_economiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
