"""
VALIDATION du CHOIX SOCIAL (choix_social.py). Vérifie la détection du gagnant de Condorcet (et qu'il bat tous les
autres), le PARADOXE de Condorcet (cycle → aucun gagnant), le DÉMASQUE (la pluralité élit un candidat battu par tous
en face-à-face ; les méthodes divergent → sur-affirmer est sur-confiant), l'effet SPOILER (retirer un perdant change
le vainqueur = violation d'IIA), le verdict CLAIR/AMBIGU, et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

from garde_ressources import borne
import choix_social as S
from choix_social import ABSTENTION, CLAIR, AMBIGU

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


C = ["A", "B", "C"]

# ─── 1. Gagnant de Condorcet net + bat tous + verdict CLAIR ───
print("=== Gagnant de Condorcet net ===")
clair = [("A", "B", "C")] * 6 + [("A", "C", "B")] * 3 + [("B", "C", "A")] * 2
M = S.matrice_majorite(clair, C)
check("matrice : M[a][b]+M[b][a] = n (pas d'égalité dans les rangs)", all(M[a][b] + M[b][a] == 11 for a in C for b in C if a != b))
gc = S.gagnant_condorcet(clair, C)
check("A est gagnant de Condorcet (majorité le classe 1er)", gc == "A")
check("le gagnant de Condorcet bat tous les autres en face-à-face", all(S.bat(M, "A", b) for b in C if b != "A"))
st_c, _ = S.analyse(clair, C)
check("verdict CLAIR quand les 3 méthodes s'accordent", st_c == CLAIR)

# ─── 2. Paradoxe de Condorcet : cycle → aucun gagnant ───
print("=== Paradoxe de Condorcet (cycle) ===")
cyc = [("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B")]
check("cycle de majorité détecté", S.cycle_condorcet(cyc, C))
check("AUCUN gagnant de Condorcet (cycle)", S.gagnant_condorcet(cyc, C) is None)
st_cy, info_cy = S.analyse(cyc, C)
check("verdict AMBIGU sur un cycle", st_cy == AMBIGU and info_cy["cycle"])

# ─── 3. DÉMASQUE : la pluralité élit un candidat battu par tous ───
print("=== Mode d'échec : la pluralité sur-confiante ===")
prof = [("A", "B", "C")] * 5 + [("B", "C", "A")] * 4 + [("C", "B", "A")] * 2
M2 = S.matrice_majorite(prof, C)
plur = S.gagnant_pluralite(prof, C)
cond = S.gagnant_condorcet(prof, C)
print(f"   pluralité={plur} ; Condorcet={cond} ; Borda={S.gagnant_borda(prof, C)}")
check("la pluralité élit A", plur == "A")
check("mais A est BATTU par B et par C en face-à-face (pluralité sur-confiante)", S.bat(M2, "B", "A") and S.bat(M2, "C", "A"))
check("Condorcet/Borda désignent B (≠ pluralité) → méthodes divergent", cond == "B" and S.gagnant_borda(prof, C) == "B")
st_p, _ = S.analyse(prof, C)
check("verdict AMBIGU quand les méthodes divergent", st_p == AMBIGU)

# ─── 4. Effet SPOILER (violation d'IIA) : retirer un perdant change le vainqueur ───
print("=== Effet spoiler / violation d'IIA ===")
sp = [("A", "C", "B")] * 4 + [("B", "C", "A")] * 3 + [("C", "B", "A")] * 2
g_avant = S.gagnant_pluralite(sp, C)
sans_C = [tuple(c for c in rang if c != "C") for rang in sp]
g_apres = S.gagnant_pluralite(sans_C, ["A", "B"])
print(f"   pluralité avec C={g_avant} ; sans C (perdant retiré)={g_apres}")
check("retirer le perdant C CHANGE le vainqueur de pluralité (spoiler/IIA)", g_avant == "A" and g_apres == "B")

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = S.analyse([], C)
st2, _ = S.analyse([("A",)], ["A"])
check("profil vide → ABSTENTION", st1 == ABSTENTION)
check("< 2 candidats → ABSTENTION", st2 == ABSTENTION)
st3, _ = S.analyse(clair, C)
check("cas valide → CLAIR ou AMBIGU", st3 in (CLAIR, AMBIGU))

print(f"\nRÉSULTAT choix_social : {ok}/{total}")
assert ok == total
