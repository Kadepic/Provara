"""
VALIDATION — FORMES CHAÎNES en multi-arg (invention_multi) : palier structurel, atome 12.

Deux frontières MESURÉES et comblées d'un même geste (les chaînes en arité 2) :
- CHAÎNE×CHAÎNE (_CC_REGISTRE/_CC_OPS/sondes) — la classe FlashFill/BlinkFill des paires de chaînes :
  préfixe/suffixe communs (canoniques : l'edit distance les saute en linéaire), concat à séparateur,
  Hamming, retrait, mots communs. Registre = primitives du langage (concat, in, count, find).
- SÉQUENCE×ENTIER — _forme_liste_scalaire GÉNÉRALISÉE (liste OU chaîne) : les tranches/rotations/paquets
  valent verbatim pour str (n_premiers_car, rotation_chaine = brique_manquante avant) ; les ops
  inapplicables (comparaisons _e > k, sum) crashent à la validation contextuelle -> filtrées, jamais un faux.
  Sondes fidèles au TYPE (renversé/trié/doublon en str pour une entrée str).

Prouve : (1) FRONTIÈRES FERMÉES — prefixe_commun, concat_espace, hamming, mots_communs, retrait,
n_premiers_car, rotation_chaine deviennent INVENTION ; (2) NOUVEAUTÉ CONTRE REGISTRE — contient (b in a)
et compte_sous_chaine restent EXISTE_DEJA ; (3) FAÇADE COHÉRENTE — pas de fausse nouveauté via
ia.forge_brique_multi (atome 6 étendu aux nouvelles formes) ; (4) ASYMÉTRIE — le préfixe commun est
symétrique mais retrait ne l'est pas (SWAP) ; (5) CORRECT hors moteur ; (6) DÉTERMINISME ;
(7) NON-RÉGRESSION — liste×entier et int×int intacts.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=500)
import invention_multi as IM

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn2(expr):
    ns: dict = {}
    exec(f"def _f(a, b):\n    return {expr}\n", ns)
    return ns["_f"]


def _prefixe(a, b):
    return a[:max(i for i in range(min(len(a), len(b)) + 1) if a[:i] == b[:i])]


SS = [(("banane", "bandeau"),), (("chat", "chien"),), (("porte", "portail"),)]
SSH = [(("mer", "mercredi"),)]
SSF = [(("montagne", "monture"),)]
C = [(("le chat dort", "chat"),), (("aa baa", "aa"),), (("xyz", "k"),)]
CH = [(("un chien vient", "chien"),)]
CF = [(("bord de mer", "de"),)]
M = [(("le chat dort la", "chat le muse"),), (("un deux trois", "trois cinq un"),), (("a b", "b c"),)]
MH = [(("gauche droite haut", "haut bas gauche"),)]
MF = [(("nord sud", "sud ouest"),)]
SI = [(("banane", 3),), (("chat", 1),), (("portail", 4),)]
SIH = [(("mercredi", 2),)]
SIF = [(("voiture", 3),)]

CIBLES = [
    ("prefixe_commun", _prefixe, SS, SSH, SSF),
    ("concat_espace", lambda a, b: a + " " + b, SS, SSH, SSF),
    ("hamming_zip", lambda a, b: sum(1 for x, y in zip(a, b) if x != y), SS, SSH, SSF),
    ("mots_communs", lambda a, b: " ".join(sorted(set(a.split()) & set(b.split()))), M, MH, MF),
    ("retrait", lambda a, b: a.replace(b, ""), C, CH, CF),
    ("n_premiers_car", lambda a, b: a[:b], SI, SIH, SIF),
    ("rotation_chaine", lambda a, b: a[b:] + a[:b], SI, SIH, SIF),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((a, b), ref(a, b)) for (a, b), in spec_in],
                               [((a, b), ref(a, b)) for (a, b), in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(a, b) == ref(a, b) for (a, b), in spec_in + held_in + frais))
    realisations[nom] = v.par

# NOUVEAUTÉ CONTRE REGISTRE : les primitives chaîne×chaîne restent EXISTE_DEJA.
v = IM.examine_cible_multi("contient", [((a, b), b in a) for (a, b), in C], [((a, b), b in a) for (a, b), in CH])
check("contient (b in a) : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("compte_sous_chaine",
                           [((a, b), a.count(b)) for (a, b), in C], [((a, b), a.count(b)) for (a, b), in CH])
check("compte_sous_chaine : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)

# FAÇADE COHÉRENTE (atome 6 étendu) : pas de fausse nouveauté via ia.forge_brique_multi.
import os
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
import ia
r = ia.forge_brique_multi("contient_forge", [((a, b), b in a) for (a, b), in C], [((a, b), b in a) for (a, b), in CH])
check("façade : contient reste EXISTE_DEJA via ia.forge_brique_multi (pas de fausse nouveauté)",
      r["statut"] == IM.EXISTE_DEJA and r["code"] == "b in a")

# ASYMÉTRIE : retrait n'est pas symétrique (SWAP discrimine) ; préfixe commun l'est.
check("retrait asymétrique (retire b DE a)",
      _fn2(realisations["retrait"])("le chat dort", "chat") == "le  dort"
      and _fn2(realisations["retrait"])("chat", "le chat dort") == "chat")
check("préfixe commun symétrique et correct",
      _fn2(realisations["prefixe_commun"])("banane", "bandeau") == "ban"
      and _fn2(realisations["prefixe_commun"])("bandeau", "banane") == "ban")

# DÉTERMINISME.
v2 = IM.examine_cible_multi("prefixe_commun",
                            [((a, b), _prefixe(a, b)) for (a, b), in SS],
                            [((a, b), _prefixe(a, b)) for (a, b), in SSH])
check("déterminisme (prefixe_commun : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["prefixe_commun"])

# NON-RÉGRESSION : liste×entier et int×int intacts.
v = IM.examine_cible_multi("n_premiers",
                           [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])],
                           [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])])
check("liste×entier : n_premiers reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_chaines_multi : {ok}/{total}")
assert ok == total
