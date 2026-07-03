"""
VALIDATION — MÉMOIRE DE BRIQUES PERSISTANTE (apprend / retient / réutilise, sound).
Prouve : (1) rétention+réutilisation (INVENTION -> EXISTE_DEJA), (2) PERSISTANCE disque (reload = nouveau
process), (3) ACCÉLÉRATION mesurée (réutilisation << re-dérivation), (4) SOUNDNESS (une brique apprise ne
matche JAMAIS une cible qu'elle ne reproduit pas ; jamais un faux).
"""
from __future__ import annotations
import os
import time
import tempfile

from garde_ressources import borne
borne(max_cpu_s=400)
import moteur_invention as MI
from memoire_briques import MemoireBriques

N = 0
def check(nom, cond):
    global N
    N += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    assert cond, nom


# cibles à apprendre (déterminées, vérifiées par held)
CIBLES = {
    "amplitude": ([([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)], [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)]),
    "somme_carres": ([([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
    # DÉTERMINANT (nuit 2026-06-24) : 2 exemples avec ÉGALITÉ d'absolus ([-3,3] et [4,-4]) qui fixent le tie-break =
    # ORDRE D'ORIGINE (tri stable). Sans eux, la composition profonde propose aussi `sorted(sorted(x,reverse=True),
    # key=abs)` (ties par valeur décroissante) -> AMBIGU honnête. Le moteur plus discriminant veut un spec déterminé.
    "tri_par_abs": ([([-3, 1, -2], [1, -2, -3]), ([5, -1], [-1, 5]), ([-3, 3, 1], [1, -3, 3]), ([4, -4, 1], [1, 4, -4])],
                    [([-4, 2, -1], [-1, 2, -4]), ([0, -7], [0, -7])]),
}

tmp = os.path.join(tempfile.gettempdir(), "valide_memoire_briques.json")
if os.path.exists(tmp):
    os.remove(tmp)

print("=" * 80)
print("VALIDATION MÉMOIRE DE BRIQUES")
print("=" * 80)

# (1) RÉTENTION + RÉUTILISATION
mem = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
faux = 0
appris_ok = True
for nom, (ex, held) in CIBLES.items():
    v1 = MI.examine_cible(nom, "x", ex, held, existant=mem.existant())
    if v1.statut == MI.INVENTION:
        if not (v1.par and MI._reproduit(MI._callable(v1.par, "f"), ex + held)):
            faux += 1
        mem.retient(v1.par)
    elif v1.statut == MI.EXISTE_DEJA:
        pass  # déjà dans la base (ok)
    else:
        appris_ok = False
mem.sauve()
check("3 cibles traitées sans abstention parasite", appris_ok)
check("au moins 2 briques apprises et retenues", len(mem) >= 2)
check("aucune invention fausse à l'apprentissage (FAUX=0)", faux == 0)

# réutilisation : re-juger les mêmes cibles -> EXISTE_DEJA (reconnues depuis la mémoire)
reuse = 0
for nom, (ex, held) in CIBLES.items():
    v = MI.examine_cible(nom + "_bis", "x", ex, held, existant=mem.existant())
    if v.statut == MI.EXISTE_DEJA and MI._reproduit(MI._callable(v.par, "f"), ex + held):
        reuse += 1
check("cibles ré-encontrées -> EXISTE_DEJA (réutilisées, reproduisent)", reuse == len(CIBLES))

# (2) PERSISTANCE : un NOUVEAU MemoireBriques relit le disque (= simulate redémarrage process)
mem2 = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("persistance disque : briques rechargées", len(mem2) == len(mem) and len(mem2) >= 2)
nom0, (ex0, held0) = next(iter(CIBLES.items()))
v_reload = MI.examine_cible(nom0 + "_reload", "x", ex0, held0, existant=mem2.existant())
check("après reload : cible apprise reconnue EXISTE_DEJA", v_reload.statut == MI.EXISTE_DEJA)

# (3) ACCÉLÉRATION : réutilisation (EXISTE_DEJA early) << re-dérivation générative
exsc, hsc = CIBLES["somme_carres"]
mem_vide = MemoireBriques(base=MI.EXISTANT)
t0 = time.time(); MI.examine_cible("sc_froid", "x", exsc, hsc, existant=mem_vide.existant()); t_froid = time.time() - t0
t0 = time.time(); MI.examine_cible("sc_chaud", "x", exsc, hsc, existant=mem2.existant()); t_chaud = time.time() - t0
print(f"      (froid={t_froid*1000:.0f} ms  chaud={t_chaud*1000:.0f} ms)")
check("réutilisation plus rapide que re-dérivation", t_chaud <= t_froid)

# (4) SOUNDNESS : une brique apprise ne crée JAMAIS de faux EXISTE_DEJA sur une cible DIFFÉRENTE.
#     On apprend amplitude (max-min) puis on juge une cible que max-min NE reproduit PAS -> doit rester correct.
mem3 = MemoireBriques(base=MI.EXISTANT)
va = MI.examine_cible("amplitude", "x", *[CIBLES["amplitude"][0], CIBLES["amplitude"][1]], existant=mem3.existant())
if va.statut == MI.INVENTION:
    mem3.retient(va.par)
# cible "longueur" : max-min ne la reproduit pas ; doit être EXISTE_DEJA via 'len' (base) ou correct, JAMAIS via amplitude
exL = [([3, 1, 5], 3), ([2, 2], 2), ([9], 1)]
helL = [([0, 0, 0, 0], 4), ([7, 7], 2)]
vL = MI.examine_cible("longueur", "x", exL, helL, existant=mem3.existant())
ok_sound = vL.par is None or MI._reproduit(MI._callable(vL.par, "f"), exL + helL)
check("soundness : la brique apprise ne produit pas de faux (par reproduit ou abstention)", ok_sound)
# et le verdict ne ment pas : si EXISTE_DEJA, le par reproduit vraiment
check("verdict honnête sur cible différente", vL.statut != MI.EXISTE_DEJA or MI._reproduit(MI._callable(vL.par, "f"), exL + helL))

if os.path.exists(tmp):
    os.remove(tmp)
print("=" * 80)
print(f"MÉMOIRE DE BRIQUES VALIDÉ — {N}/{N}.")
