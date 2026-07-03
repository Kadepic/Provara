"""
VALIDATION — MOTEUR DE RESTITUTION (routé, exact, ACT-R, consolidation, sound).
Prouve : routage parcimonieux (skip), rappel exact + contexte non-confondu, HORS honnête (zéro hallucination),
ordre ACT-R (fréquent+récent = plus chaud), consolidation par compression (fusion #1) sound, persistance disque.
"""
from __future__ import annotations
import os
import random
import tempfile

from garde_ressources import borne
borne(max_go=4.0, max_cpu_s=900)   # charge tout le lecteur (~10 M faits) : marge CPU pour le palier 10 M
import moteur_invention as MI
from base_faits import VERIFIE, HORS
from restitution import MoteurRestitution, _route

N = 0
def check(nom, cond):
    global N
    N += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    assert cond, nom


print("=" * 80)
print("VALIDATION MOTEUR DE RESTITUTION")
print("=" * 80)

# (1) ROUTAGE parcimonieux
check("routage relation->domaine (president->geo)", _route("president") == "geo")
check("routage calcul->calcul", _route("calcul") == "calcul")
check("routage inconnu->general", _route("relation_bizarre") == "general")

m = MoteurRestitution()
m.retient("president", "France", "Macron", "passe", "actualité", contexte="2026")
m.retient("president", "France", "Hollande", "passe", "actualité", contexte="2014")
st, f, dom = m.restitue("president", "France", "2026")
check("rappel exact (Macron 2026)", st == VERIFIE and f.valeur == "Macron")
st2, f2, _ = m.restitue("president", "France", "2014")
check("contexte non confondu (2014 != 2026)", f2.valeur == "Hollande")
check("routage parcimonieux : peu de shards consultés vs skippés", m.stats["shards_skippes"] > m.stats["shards_consultes"])

# (2) HORS honnête (zéro hallucination)
st3, f3, _ = m.restitue("president", "France", "1700")
check("HORS sur fait jamais appris (pas d'hallucination)", st3 == HORS and f3 is None)
st4, _, _ = m.restitue("capitale", "Atlantide")
check("HORS sur entité inexistante", st4 == HORS)

# (3) ACT-R : fréquent+récent = plus chaud qu'un ancien rarement vu
m2 = MoteurRestitution()
m2.retient("capitale", "France", "Paris", "convention", "geo")
m2.retient("capitale", "Japon", "Tokyo", "convention", "geo")
for _ in range(5):                                   # France consultée souvent et récemment
    m2.restitue("capitale", "France")
cle_fr = "capitale|france|"
cle_jp = "capitale|japon|"
check("ACT-R : clé fréquente+récente plus activée qu'une ancienne", m2.activation(cle_fr) > m2.activation(cle_jp))

# (4) CONSOLIDATION : compression de résultats mémorisés en règle (fusion #1), sound
m3 = MoteurRestitution()
rng = random.Random(3)
for _ in range(12):
    ab = [rng.randint(1, 12), rng.randint(1, 12)]
    m3.memorise_calcul(ab, ab[0] * ab[1])
rap = m3.consolide()
check("consolidation : faits rendus dérivables (compression)", rap["derivables"] >= 6)
check("consolidation : une règle reproduit les faits (sound)", bool(rap["par"]) and
      MI._reproduit(MI._callable(rap["par"][0], "f"), [( [3,4], 12)]))
check("consolidation : cache vidé après compression (mémoire rétrécit)", len(m3.cache_calc) == 0)
# rappel d'un calcul mémorisé AVANT consolidation
m4 = MoteurRestitution()
m4.memorise_calcul([6, 7], 42)
check("mémoïsation calcul : 6*7 rappelé = 42 (zéro recalcul)", m4.rappelle_calcul([6, 7]) == "42")
check("calcul jamais vu -> None (à calculer)", m4.rappelle_calcul([99, 99]) is None)

# (5) PERSISTANCE disque (reload = redémarrage)
d = tempfile.mkdtemp(prefix="valide_restit_")
mp = MoteurRestitution(racine=d)
mp.retient("capitale", "Espagne", "Madrid", "convention", "geo")
mp.sauve()
mp2 = MoteurRestitution(racine=d)
st5, f5, _ = mp2.restitue("capitale", "Espagne")
check("persistance disque : fait rechargé après reload", st5 == VERIFIE and f5.valeur == "Madrid")
# ménage
for fn in os.listdir(d):
    os.remove(os.path.join(d, fn))
os.rmdir(d)

# (6) RAISONNEMENT intégré : dérivation en repli + mémoïsation (tabling) + honnêteté
mr = MoteurRestitution()
mr.retient("parent", "a", "b", "passe", "arbre")
mr.retient("parent", "b", "c", "passe", "arbre")
mr.ajoute_regle(("grandparent", "X", "Z"), [("parent", "X", "Y"), ("parent", "Y", "Z")], "gp")
st6, f6, org6 = mr.restitue("grandparent", "a")
check("dérivation en repli : grandparent(a)=c (raisonné)", st6 == VERIFIE and f6.valeur == "c" and org6 == "deduit")
st7, f7, org7 = mr.restitue("grandparent", "a")
check("mémoïsation (tabling) : 2e appel direct (plus 'deduit')", st7 == VERIFIE and f7.valeur == "c" and org7 != "deduit")
check("honnêteté : grandparent(z) inconnu -> HORS", mr.restitue("grandparent", "z")[0] == HORS)

# (7) FUSION #2 — mémoïsation ADAPTATIVE : un calcul jamais vu répondu par la règle consolidée (sound)
mf = MoteurRestitution()
rf = random.Random(9)
for _ in range(10):
    ab = [rf.randint(1, 12), rf.randint(1, 12)]
    mf.memorise_calcul(ab, ab[0] * ab[1])
mf.consolide()
check("fusion#2 adaptatif : 11*7 jamais vu -> 77 par règle", mf.rappelle_calcul([11, 7]) == "77")

# (8) FUSION #5 — révision BITEMPORELLE : une ERREUR entrée puis corrigée ; courant = le bon, historique conservé.
# (Exemple factuel : Sydney est l'erreur classique pour la capitale de l'Australie ; la bonne réponse = Canberra.)
mb = MoteurRestitution()
mb.retient("capitale", "Australie", "Sydney", "convention", "saisie erronée")
mb.retient("capitale", "Australie", "Canberra", "convention", "correction sourcée")
check("fusion#5 révision : courant = valeur corrigée (Canberra)", mb.restitue("capitale", "Australie")[1].valeur == "Canberra")
hist = mb.shards["geo"].histoire_de("capitale", "Australie")
check("fusion#5 bitemporel : historique conservé (Sydney puis Canberra)", [h["valeur"] for h in hist] == ["Sydney", "Canberra"])

# (9) FUSION #4 — rappel associatif par indice partiel (sound, exact)
ma = MoteurRestitution()
ma.retient("capitale", "France", "Paris", "conv", "geo")
ma.retient("monnaie", "France", "Euro", "conv", "geo")
asso = {a[0].split("|")[0] for a in ma.rappel_associatif("France")}
check("fusion#4 associatif : tout sur France (capitale+monnaie)", {"capitale", "monnaie"} <= asso)

# (10) FUSION #3 — activation pondérée par provenance (fan-out) > activation seule pour un fait central
mp = MoteurRestitution()
mp.retient("parent", "a", "b", "passe", "arbre")
mp.retient("parent", "b", "c", "passe", "arbre")
mp.retient("parent", "x", "b", "passe", "arbre")
mp.ajoute_regle(("gp", "X", "Z"), [("parent", "X", "Y"), ("parent", "Y", "Z")], "gp")
mp.restitue("gp", "a"); mp.restitue("gp", "x")
check("fusion#3 provenance : fait central plus chaud (fan-out)",
      mp.activation_provenance("parent|b|") > mp.activation("parent|b|"))

# (11) INTÉGRATION LECTEUR DATA (#3) : le rappel atteint les tables ingérées du lecteur, HORS préservé.
ml = MoteurRestitution()
check("lecteur DATA atteignable : numero_atomique(fer)=26", ml.restitue("numero_atomique", "fer")[1].valeur == "26")
check("lecteur DATA atteignable : prefixe_si(kilo)=3", ml.restitue("prefixe_si", "kilo")[1].valeur == "3")
check("lecteur DATA atteignable : continent(japon)=Asie", ml.restitue("continent", "japon")[1].valeur == "Asie")
check("amorce base_faits toujours atteignable : capitale(France)=Paris",
      ml.restitue("capitale", "France")[1].valeur == "Paris")
check("HORS préservé sur entité DATA inconnue (numero_atomique vibranium)",
      ml.restitue("numero_atomique", "vibranium")[0] == HORS)
check("HORS préservé sur relation inconnue", ml.restitue("relation_inexistante", "x")[0] == HORS)

print("=" * 80)
print(f"RESTITUTION VALIDÉ — {N}/{N}.")
