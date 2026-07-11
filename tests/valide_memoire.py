"""
VALIDATION — MÉMOIRE DE BRIQUES PERSISTANTE v2 (apprend / retient / réutilise, CONFIANCE ZÉRO AU DISQUE).
Prouve : (1) rétention+réutilisation (INVENTION -> EXISTE_DEJA), (2) PERSISTANCE disque (reload = nouveau
process), (3) ACCÉLÉRATION mesurée (réutilisation << re-dérivation), (4) SOUNDNESS (une brique apprise ne
matche JAMAIS une cible qu'elle ne reproduit pas ; jamais un faux), (5) LE DISQUE N'EST JAMAIS CRU SUR
PAROLE : expr altérée -> quarantaine (jamais servie) ; JSON corrompu -> préservé en .corrompu, rien
d'injecté ; format v1 sans spec -> quarantaine (re-dérivable, jamais injecté) ; spec à TUPLES survit à
l'aller-retour disque (repr/literal_eval — JSON aurait menti) ; admission GARDÉE dans retient() (refus
compté) ; noms PARLANTS + provenance servable ; collision -> suffixe, rien d'écrasé ; zéro résidu .tmp.
"""
from __future__ import annotations
import json
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
for suffixe in ("", ".quarantaine", ".corrompu", ".tmp"):
    if os.path.exists(tmp + suffixe):
        os.remove(tmp + suffixe)

print("=" * 80)
print("VALIDATION MÉMOIRE DE BRIQUES v2")
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
        mem.retient(v1.par, origine=nom, exemples=ex, held=held)
    elif v1.statut == MI.EXISTE_DEJA:
        pass  # déjà dans la base (ok)
    else:
        appris_ok = False
mem.sauve()
check("3 cibles traitées sans abstention parasite", appris_ok)
check("au moins 2 briques apprises et retenues", len(mem) >= 2)
check("aucune invention fausse à l'apprentissage (FAUX=0)", faux == 0)
check("zéro refus d'admission sur des inventions vérifiées", mem.refus_admission == 0)

# réutilisation : re-juger les mêmes cibles -> EXISTE_DEJA (reconnues depuis la mémoire)
reuse = 0
for nom, (ex, held) in CIBLES.items():
    v = MI.examine_cible(nom + "_bis", "x", ex, held, existant=mem.existant())
    if v.statut == MI.EXISTE_DEJA and MI._reproduit(MI._callable(v.par, "f"), ex + held):
        reuse += 1
check("cibles ré-encontrées -> EXISTE_DEJA (réutilisées, reproduisent)", reuse == len(CIBLES))

# (2) PERSISTANCE : un NOUVEAU MemoireBriques relit le disque (= simulate redémarrage process)
mem2 = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("persistance disque : briques rechargées (et RE-JUGÉES) au reload",
      len(mem2) == len(mem) and len(mem2) >= 2 and not mem2.quarantaine)
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
mem3 = MemoireBriques(base=MI.EXISTANT)
va = MI.examine_cible("amplitude", "x", *[CIBLES["amplitude"][0], CIBLES["amplitude"][1]], existant=mem3.existant())
if va.statut == MI.INVENTION:
    mem3.retient(va.par, origine="amplitude", exemples=CIBLES["amplitude"][0], held=CIBLES["amplitude"][1])
exL = [([3, 1, 5], 3), ([2, 2], 2), ([9], 1)]
helL = [([0, 0, 0, 0], 4), ([7, 7], 2)]
vL = MI.examine_cible("longueur", "x", exL, helL, existant=mem3.existant())
ok_sound = vL.par is None or MI._reproduit(MI._callable(vL.par, "f"), exL + helL)
check("soundness : la brique apprise ne produit pas de faux (par reproduit ou abstention)", ok_sound)
check("verdict honnête sur cible différente", vL.statut != MI.EXISTE_DEJA or MI._reproduit(MI._callable(vL.par, "f"), exL + helL))

# (5) CONFIANCE ZÉRO AU DISQUE — chaque mode d'échec, un par un.
# (5a) EXPR ALTÉRÉE : le fichier est falsifié -> la brique ne reproduit plus SON spec -> quarantaine,
#      jamais injectée, jamais exécutable via existant(). L'attaque du cache qui « servait D -> None ».
with open(tmp, encoding="utf-8") as f:
    contenu = json.load(f)
nom_sab = sorted(contenu["briques"])[0]
expr_saine = contenu["briques"][nom_sab]["expr"]
contenu["briques"][nom_sab]["expr"] = "sum(x) * 0 + 999999"        # exécutable, mais FAUSSE pour le spec
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(contenu, f, ensure_ascii=False)
mem_sab = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("expr altérée -> brique en QUARANTAINE (re-jugement au chargement)",
      any(q["nom"] == nom_sab and "ne reproduit plus" in q["raison"] for q in mem_sab.quarantaine))
check("expr altérée -> JAMAIS injectée dans existant()", "999999" not in " ".join(mem_sab.existant().values()))
check("la quarantaine est TRACÉE sur disque (append-only)", os.path.exists(tmp + ".quarantaine"))
autres = len(contenu["briques"]) - 1
check("les briques SAINES du même fichier restent servies", len(mem_sab) == autres)
# restaurer et re-sauver proprement pour la suite
contenu["briques"][nom_sab]["expr"] = expr_saine
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(contenu, f, ensure_ascii=False)

# (5b) JSON CORROMPU : préservé en .corrompu (l'évidence jamais détruite), chargement vide, compté.
with open(tmp, "w", encoding="utf-8") as f:
    f.write('{"version": 2, "briques": {  TRONQUÉ')
mem_cor = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("JSON corrompu -> chargement VIDE (rien de deviné)", len(mem_cor) == 0)
check("JSON corrompu -> pièce préservée en .corrompu", os.path.exists(tmp + ".corrompu"))
check("JSON corrompu -> refus dit et compté", any("illisible" in q["raison"] for q in mem_cor.quarantaine))

# (5c) FORMAT v1 (nom -> expr, sans spec) : non re-jugeable -> quarantaine, rien d'injecté.
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"appris_0": "max(x) - min(x)", "appris_1": "sum(_e * _e for _e in x)"}, f)
mem_v1 = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("format v1 -> AUCUNE brique injectée (pas de spec = pas de preuve)", len(mem_v1) == 0)
check("format v1 -> les 2 entrées en quarantaine avec la raison dite",
      sum(1 for q in mem_v1.quarantaine if "sans spec" in q["raison"]) == 2)

# (5d) SPEC À TUPLES : survit à l'aller-retour disque (JSON nu aurait rendu des listes -> faux re-jugement).
os.remove(tmp)
mem_t = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
ex_t = [((1, 2), 3), ((5, 7), 12)]
held_t = [((0, 4), 4)]
check("retient : brique à spec TUPLES admise (reproduit vérifié)",
      mem_t.retient("x[0] + x[1]", origine="somme_paire", exemples=ex_t, held=held_t))
mem_t.sauve()
mem_t2 = MemoireBriques(chemin=tmp, base=MI.EXISTANT)
check("spec à tuples RECHARGÉ et RE-JUGÉ avec succès (tuples préservés)",
      len(mem_t2) == 1 and not mem_t2.quarantaine)

# (5e) ADMISSION GARDÉE : une expr qui ne reproduit PAS son spec est refusée ET comptée ; spec vide refusé.
refus_avant = mem_t2.refus_admission
check("retient REFUSE une expr qui ne reproduit pas son spec",
      not mem_t2.retient("x[0] * x[1]", origine="somme_paire", exemples=ex_t, held=held_t))
check("retient REFUSE un spec vide (rien ne prouve rien)",
      not mem_t2.retient("x[0] - x[1] + 42", origine="vide", exemples=[], held=[]))
check("chaque refus d'admission est COMPTÉ", mem_t2.refus_admission == refus_avant + 2)
# dé-dup : la même expr n'est ni réapprise ni comptée comme refus
refus_avant = mem_t2.refus_admission
check("dé-dup : expr déjà connue -> False sans refus compté",
      not mem_t2.retient("x[0] + x[1]", origine="somme_paire", exemples=ex_t, held=held_t)
      and mem_t2.refus_admission == refus_avant)

# (5f) NOM PARLANT + PROVENANCE + COLLISION : rien d'opaque, rien d'écrasé.
prov = mem_t2.provenance("somme_paire")
check("provenance servable : origine, quand, spec, held, n_verifie présents",
      prov is not None and all(k in prov for k in ("expr", "origine", "quand", "spec", "held", "n_verifie"))
      and prov["n_verifie"] == 3)
ex_c = [((2, 3), 6), ((4, 5), 20)]
check("collision de nom -> suffixe, la brique prouvée n'est JAMAIS écrasée",
      mem_t2.retient("x[0] * x[1]", origine="somme_paire", exemples=ex_c, held=[((1, 9), 9)])
      and mem_t2.provenance("somme_paire")["expr"] == "x[0] + x[1]"
      and mem_t2.provenance("somme_paire_2")["expr"] == "x[0] * x[1]")

# (5g) ZÉRO RÉSIDU : sauve() ne laisse jamais traîner de .tmp (leçon de la fuite du cache).
mem_t2.sauve()
check("aucun résidu .tmp après sauve()", not os.path.exists(tmp + ".tmp"))

for suffixe in ("", ".quarantaine", ".corrompu"):
    if os.path.exists(tmp + suffixe):
        os.remove(tmp + suffixe)
print("=" * 80)
print(f"MÉMOIRE DE BRIQUES v2 VALIDÉE — {N}/{N}.")
