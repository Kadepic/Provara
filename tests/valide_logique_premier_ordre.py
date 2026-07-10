"""
VALIDE logique_premier_ordre.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (faits logiques CLASSIQUES, valeurs attendues écrites EN DUR — jamais
recalculées par la fonction testée) :
  • ∀x P(x) ⊨ ∃x P(x) sur domaine non vide (loi classique) : aucun contre-modèle jusqu'à la taille 4.
  • ∃x P(x) ⊭ ∀x P(x) : le contre-modèle classique domaine {a,b}, P={a} DOIT être trouvé (écrit en dur).
  • ∀x∀y R(x,y) ⊨ ∀y∀x R(x,y) (permutation de quantificateurs identiques) : aucun contre-modèle.
  • ∃x∀y R(x,y) ⊨ ∀y∃x R(x,y) : aucun contre-modèle ; la RÉCIPROQUE est FAUSSE (piège classique) —
    le contre-modèle domaine {a,b}, R={(a,a),(b,b)} est écrit EN DUR et vérifié directement.
  • De Morgan quantifié ¬∀x P(x) ≡ ∃x ¬P(x) : vérifié sur TOUS les modèles de taille <= 3, énumérés
    À LA MAIN dans la gate (itertools, SECOND chemin indépendant de cherche_contre_modele).
  • Syllogisme (Socrate) : ∀x(H(x)→M(x)), H(socrate) ⊨ M(socrate) — vérité de table calculée à la main.
  • Table de vérité de l'implication (4 cas) et satisfactions calculées à la main sur une structure fixe.

SOUNDNESS : domaine vide, prédicat inconnu, variable libre, arité incohérente, bool/str/float/formule
mal formée, taille_max hors 1..6, budget dépassé -> ValueError.
HONNÊTETÉ : refute=False dit « non réfuté », jamais « valide ».
"""
import itertools

import logique_premier_ordre as L

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# Structure fixe de référence — vérités calculées À LA MAIN dans les commentaires.
S1 = {'domaine': (1, 2, 3),
      'predicats': {'P': {(1,), (2,)},           # P vrai de 1 et 2, faux de 3
                    'R': {(1, 2), (2, 3)}}}      # R vrai de (1,2) et (2,3) seulement

P1 = ('pred', 'P', (1,))
P2 = ('pred', 'P', (2,))
P3 = ('pred', 'P', (3,))
TOUS_P = ('tous', 'x', ('pred', 'P', ('x',)))
EXISTE_P = ('existe', 'x', ('pred', 'P', ('x',)))

# ── 1) SATISFACTION : atomes et connecteurs (vérités à la main sur S1) ──
check(L.satisfait(S1, P1) is True, "P(1) vrai (1 est dans l'extension)")
check(L.satisfait(S1, P3) is False, "P(3) faux (3 hors extension)")
check(L.satisfait(S1, ('non', P3)) is True, "¬P(3) vrai")
check(L.satisfait(S1, ('et', P1, P2)) is True, "P(1)∧P(2) vrai")
check(L.satisfait(S1, ('et', P1, P3)) is False, "P(1)∧P(3) faux")
check(L.satisfait(S1, ('ou', P3, P1)) is True, "P(3)∨P(1) vrai")
check(L.satisfait(S1, ('ou', P3, ('non', P1))) is False, "P(3)∨¬P(1) faux")
# Table de vérité de l'implication (ancre : sémantique classique, 4 cas)
check(L.satisfait(S1, ('implique', P1, P2)) is True, "V→V = V")
check(L.satisfait(S1, ('implique', P1, P3)) is False, "V→F = F")
check(L.satisfait(S1, ('implique', P3, P1)) is True, "F→V = V")
check(L.satisfait(S1, ('implique', P3, P3)) is True, "F→F = V")

# ── 2) SATISFACTION : quantificateurs et affectations (à la main sur S1) ──
check(L.satisfait(S1, EXISTE_P) is True, "∃x P(x) vrai dans S1")
check(L.satisfait(S1, TOUS_P) is False, "∀x P(x) faux dans S1 (3 ∉ P)")
check(L.satisfait(S1, ('tous', 'x', ('existe', 'y', ('pred', 'R', ('x', 'y'))))) is False,
      "∀x∃y R(x,y) faux dans S1 (x=3 n'a pas de successeur)")
check(L.satisfait(S1, ('existe', 'y', ('pred', 'R', (1, 'y')))) is True,
      "∃y R(1,y) vrai dans S1 ((1,2) ∈ R)")
check(L.satisfait(S1, ('existe', 'x', ('tous', 'y', ('pred', 'R', ('x', 'y'))))) is False,
      "∃x∀y R(x,y) faux dans S1 (aucune ligne pleine)")
check(L.satisfait(S1, ('pred', 'P', ('x',)), {'x': 1}) is True, "P(x)[x:=1] vrai")
check(L.satisfait(S1, ('pred', 'P', ('x',)), {'x': 3}) is False, "P(x)[x:=3] faux")
check(L.satisfait(S1, ('pred', 'R', ('x', 'y')), {'x': 1, 'y': 2}) is True, "R(x,y)[1,2] vrai")
check(L.satisfait(S1, ('pred', 'R', ('x', 'y')), {'x': 2, 'y': 1}) is False, "R(x,y)[2,1] faux")
check(isinstance(L.satisfait(S1, P1), bool), "satisfait renvoie un vrai bool")

# ── 3) CONSÉQUENCE DANS CE MODÈLE ──
check(L.consequence(S1, [], P1) is True, "sans prémisse : conclusion vraie -> True")
check(L.consequence(S1, [], P3) is False, "sans prémisse : conclusion fausse -> False")
check(L.consequence(S1, [EXISTE_P], TOUS_P) is False,
      "∃xP vrai mais ∀xP faux dans S1 -> pas conséquence ICI")
check(L.consequence(S1, [TOUS_P], EXISTE_P) is True,
      "prémisse ∀xP fausse dans S1 -> implication vacuement vraie")
# Syllogisme de Socrate : ∀x(H(x)→M(x)), H(1) ⊨ M(1) — table à la main (1,2 humains+mortels, 3 mortel)
S2 = {'domaine': (1, 2, 3),
      'predicats': {'H': {(1,), (2,)}, 'M': {(1,), (2,), (3,)}}}
TOUS_HM = ('tous', 'x', ('implique', ('pred', 'H', ('x',)), ('pred', 'M', ('x',))))
check(L.satisfait(S2, TOUS_HM) is True, "∀x(H→M) vrai dans S2 (vérifié à la main)")
check(L.consequence(S2, [TOUS_HM, ('pred', 'H', (1,))], ('pred', 'M', (1,))) is True,
      "syllogisme : Socrate humain, humains mortels -> Socrate mortel")

# ── 4) ANCRE 1 : ∀x P(x) ⊨ ∃x P(x) — aucun contre-modèle jusqu'à la taille 4 ──
r1 = L.cherche_contre_modele([TOUS_P], EXISTE_P, 4)
check(r1['refute'] is False, "∀xP ⊨ ∃xP : non réfuté (loi classique, domaine non vide)")
check(r1['contre_modele'] is None, "∀xP ⊨ ∃xP : contre_modele None")
check(r1['portee'] == "domaines de taille <= 4", "portée exacte 'domaines de taille <= 4'")
check("non réfuté" in r1['statut'], "HONNÊTETÉ : le statut dit 'non réfuté'")
check("valide" not in r1['statut'].lower().replace("validité", ""),
      "HONNÊTETÉ : le statut ne prétend jamais 'valide'")

# ── 5) ANCRE 2 : ∃x P(x) ⊭ ∀x P(x) — contre-modèle CLASSIQUE {a,b}, P={a} écrit EN DUR ──
r2 = L.cherche_contre_modele([EXISTE_P], TOUS_P, 4)
check(r2['refute'] is True, "∃xP ⊭ ∀xP : réfuté")
check(r2['contre_modele'] == {'domaine': ('a', 'b'), 'predicats': {'P': {('a',)}}},
      "contre-modèle attendu EN DUR : domaine (a,b), P={a}")
check(L.satisfait(r2['contre_modele'], EXISTE_P) is True, "contre-modèle : prémisse ∃xP satisfaite")
check(L.satisfait(r2['contre_modele'], TOUS_P) is False, "contre-modèle : conclusion ∀xP réfutée")
check("taille 2" in r2['statut'], "trouvé à la taille 2 (aucun à la taille 1 : à la main)")

# ── 6) ANCRE 3 : ∀x∀y R(x,y) ⊨ ∀y∀x R(x,y) — aucun contre-modèle ──
RXY = ('pred', 'R', ('x', 'y'))
TT = ('tous', 'x', ('tous', 'y', RXY))
TT_INV = ('tous', 'y', ('tous', 'x', RXY))
r3 = L.cherche_contre_modele([TT], TT_INV, 3)
check(r3['refute'] is False, "∀x∀yR ⊨ ∀y∀xR : non réfuté (permutation licite)")
check(r3['contre_modele'] is None, "∀x∀yR ⊨ ∀y∀xR : contre_modele None")

# ── 7) ANCRE 4 : ∃x∀y R ⊨ ∀y∃x R, mais la RÉCIPROQUE est FAUSSE ──
ET_R = ('existe', 'x', ('tous', 'y', RXY))
TE_R = ('tous', 'y', ('existe', 'x', RXY))
r4 = L.cherche_contre_modele([ET_R], TE_R, 3)
check(r4['refute'] is False, "∃x∀yR ⊨ ∀y∃xR : non réfuté (sens licite)")
r4b = L.cherche_contre_modele([TE_R], ET_R, 3)
check(r4b['refute'] is True, "∀y∃xR ⊭ ∃x∀yR : réfuté (piège classique)")
check(len(r4b['contre_modele']['domaine']) == 2, "réciproque : contre-modèle de taille 2")
check(L.satisfait(r4b['contre_modele'], TE_R) is True, "contre-modèle trouvé : prémisse satisfaite")
check(L.satisfait(r4b['contre_modele'], ET_R) is False, "contre-modèle trouvé : conclusion réfutée")
# Contre-modèle CLASSIQUE imposé, écrit EN DUR, vérifié DIRECTEMENT par satisfait :
SR = {'domaine': ('a', 'b'), 'predicats': {'R': {('a', 'a'), ('b', 'b')}}}   # R = identité
check(L.satisfait(SR, TE_R) is True, "ancre en dur {a,b}, R={(a,a),(b,b)} : ∀y∃xR vrai")
check(L.satisfait(SR, ET_R) is False, "ancre en dur {a,b}, R={(a,a),(b,b)} : ∃x∀yR faux")

# ── 8) ANCRE 5 : De Morgan quantifié ¬∀xP ≡ ∃x¬P sur TOUS les modèles de taille <= 3 ──
NON_TOUS = ('non', TOUS_P)
EXISTE_NON = ('existe', 'x', ('non', ('pred', 'P', ('x',))))
# Second chemin INDÉPENDANT : énumération manuelle des modèles dans la gate (pas cherche_contre_modele)
modeles_vus = 0
equivalence_partout = True
for n in (1, 2, 3):
    domaine = ('a', 'b', 'c')[:n]
    for k in range(len(domaine) + 1):
        for sous_ensemble in itertools.combinations(domaine, k):
            S = {'domaine': domaine, 'predicats': {'P': {(e,) for e in sous_ensemble}}}
            modeles_vus += 1
            if L.satisfait(S, NON_TOUS) != L.satisfait(S, EXISTE_NON):
                equivalence_partout = False
check(equivalence_partout, "De Morgan ¬∀xP ≡ ∃x¬P sur tous les modèles énumérés à la main")
check(modeles_vus == 2 + 4 + 8, "énumération manuelle complète : 14 modèles (2^1+2^2+2^3)")
check(L.cherche_contre_modele([NON_TOUS], EXISTE_NON, 3)['refute'] is False,
      "De Morgan sens 1 : non réfuté par la recherche exhaustive")
check(L.cherche_contre_modele([EXISTE_NON], NON_TOUS, 3)['refute'] is False,
      "De Morgan sens 2 : non réfuté par la recherche exhaustive")

# ── 9) SOUNDNESS — structure ──
F = P1
check(leve(L.satisfait, [], F), "structure non-dict -> ValueError")
check(leve(L.satisfait, {'domaine': (1,)}, F), "clé predicats manquante -> ValueError")
check(leve(L.satisfait, {'domaine': (1,), 'predicats': {}, 'extra': 0}, F), "clé en trop -> ValueError")
check(leve(L.satisfait, {'domaine': (), 'predicats': {}}, F), "DOMAINE VIDE -> ValueError")
check(leve(L.satisfait, {'domaine': [1, 2], 'predicats': {}}, F), "domaine liste -> ValueError")
check(leve(L.satisfait, {'domaine': (1, True), 'predicats': {}}, F), "bool dans le domaine -> ValueError")
check(leve(L.satisfait, {'domaine': (1, 1), 'predicats': {}}, F), "domaine dupliqué -> ValueError")
check(leve(L.satisfait, {'domaine': (1,), 'predicats': []}, F), "predicats non-dict -> ValueError")
check(leve(L.satisfait, {'domaine': (1,), 'predicats': {'P': [(1,)]}}, F),
      "extension liste (pas set) -> ValueError")
check(leve(L.satisfait, {'domaine': (1,), 'predicats': {'P': {1}}}, F),
      "extension d'entiers (pas de tuples) -> ValueError")
check(leve(L.satisfait, {'domaine': (1, 2), 'predicats': {'P': {(1,), (1, 2)}}}, F),
      "ARITÉ INCOHÉRENTE dans l'extension -> ValueError")
check(leve(L.satisfait, {'domaine': (1,), 'predicats': {'P': {(9,)}}}, F),
      "extension hors domaine -> ValueError")

# ── 10) SOUNDNESS — formules ──
check(leve(L.satisfait, S1, ('pred', 'Q', (1,))), "PRÉDICAT INCONNU -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', (1, 2))), "ARITÉ INCOHÉRENTE usage vs extension -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', ('z',))), "VARIABLE LIBRE non affectée -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', ('z',)), {}), "variable libre, affectation vide -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', (True,))), "argument bool -> ValueError (True n'est pas 1)")
check(leve(L.satisfait, S1, ('pred', 'P', [1])), "args non-tuple -> ValueError")
check(leve(L.satisfait, S1, 42), "formule non-tuple -> ValueError")
check(leve(L.satisfait, S1, ('nand', P1, P2)), "opérateur inconnu -> ValueError")
check(leve(L.satisfait, S1, ('non', P1, P2)), "négation à 2 arguments -> ValueError")
check(leve(L.satisfait, S1, ('et', P1)), "conjonction à 1 argument -> ValueError")
check(leve(L.satisfait, S1, ('tous', 1, P1)), "variable de quantificateur non-str -> ValueError")
SX = {'domaine': ('x', 'y'), 'predicats': {'P': {('x',)}}}
check(leve(L.satisfait, SX, ('tous', 'x', ('pred', 'P', ('x',)))),
      "variable = élément du domaine -> ValueError (ambiguïté refusée)")
S_VIDE = {'domaine': (1, 2), 'predicats': {'Q': set()}}
check(L.satisfait(S_VIDE, ('pred', 'Q', (1,))) is False,
      "extension vide : atome FAUX dans ce modèle (pas une erreur)")
check(leve(L.satisfait, S_VIDE, ('et', ('pred', 'Q', (1,)), ('pred', 'Q', (1, 2)))),
      "arité incohérente entre deux usages (extension vide) -> ValueError")

# ── 11) SOUNDNESS — affectation ──
check(leve(L.satisfait, S1, F, [1]), "affectation non-dict -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', ('x',)), {1: 1}), "clé d'affectation non-str -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', ('x',)), {'x': 9}), "valeur hors domaine -> ValueError")
check(leve(L.satisfait, S1, ('pred', 'P', ('x',)), {'x': True}), "valeur bool -> ValueError")

# ── 12) SOUNDNESS — consequence ──
check(leve(L.consequence, S1, 'x', F), "premisses non-liste -> ValueError")
check(leve(L.consequence, S1, [('pred', 'P', ('z',))], F), "prémisse à variable libre -> ValueError")
check(leve(L.consequence, S_VIDE, [('pred', 'Q', (1,))], ('pred', 'Q', (1, 2))),
      "arité incohérente prémisse/conclusion -> ValueError")

# ── 13) SOUNDNESS — cherche_contre_modele ──
check(leve(L.cherche_contre_modele, [TOUS_P], EXISTE_P, 0), "taille_max=0 -> ValueError")
check(leve(L.cherche_contre_modele, [TOUS_P], EXISTE_P, True), "taille_max bool -> ValueError")
check(leve(L.cherche_contre_modele, [TOUS_P], EXISTE_P, "3"), "taille_max str -> ValueError")
check(leve(L.cherche_contre_modele, [TOUS_P], EXISTE_P, 3.0), "taille_max float -> ValueError")
check(leve(L.cherche_contre_modele, [TOUS_P], EXISTE_P, 7), "taille_max=7 (>6) -> ValueError")
check(leve(L.cherche_contre_modele, 'x', EXISTE_P, 2), "premisses non-liste -> ValueError")
check(leve(L.cherche_contre_modele, [('pred', 'P', ('x',))], EXISTE_P, 2),
      "formule non close -> ValueError")
check(leve(L.cherche_contre_modele, [('existe', 'x', ('pred', 'P', (1,)))], EXISTE_P, 2),
      "constante dans la formule (recherche multi-modèles) -> ValueError")
check(leve(L.cherche_contre_modele, [TOUS_P],
           ('tous', 'x', ('tous', 'y', ('pred', 'P', ('x', 'y')))), 2),
      "arité incohérente entre prémisse et conclusion -> ValueError")
check(leve(L.cherche_contre_modele, [TE_R], ET_R, 5),
      "budget dépassé (R binaire, taille 5 : 2^25 > 2^20) -> ValueError (abstention, pas de faux 'non réfuté')")

# ── 14) DÉTERMINISME ──
check(L.satisfait(S1, TOUS_P) == L.satisfait(S1, TOUS_P), "déterminisme satisfait")
check(L.consequence(S1, [EXISTE_P], TOUS_P) == L.consequence(S1, [EXISTE_P], TOUS_P),
      "déterminisme consequence")
check(L.cherche_contre_modele([EXISTE_P], TOUS_P, 3) == L.cherche_contre_modele([EXISTE_P], TOUS_P, 3),
      "déterminisme cherche_contre_modele (même contre-modèle, ordre d'énumération fixe)")

print(f"\n=== valide_logique_premier_ordre : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
