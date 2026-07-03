"""
VALIDATION du CLASSIFIEUR DE NATURE DE DOMAINE.

Le test central est la GARANTIE DE SOUNDNESS : aucune branche n'émet de faux.
- Les faits connus sont rendus EXACTEMENT (avec source).
- Les faits INCONNUS -> jamais VÉRIFIÉ (HORS honnête), jamais une valeur inventée.
- Le NON-BORNÉ (goût/opinion/futur/fiction/éthique) -> ABSTENTION, jamais une prétention au vrai.
- L'arithmétique fermée -> calculée et exacte ; le garde anti-DoS tient.
- La demande structurée (nécessité) -> VÉRIFIÉE par l'exécuteur (held-out) ou HORS, jamais un faux.
"""
from __future__ import annotations

from garde_ressources import borne

import base_faits
import classifieur_domaine as C

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# 1) FAITS CONNUS rendus exactement, bonne nature.
r = C.repond("Quelle est la capitale de la France ?")
check("capitale France -> physique/VÉRIFIÉ/Paris",
      r.nature == C.PHYSIQUE and r.statut == C.VERIFIE and r.valeur == "Paris" and r.source)
r = C.repond("pluriel de cheval")
check("pluriel cheval -> convention/VÉRIFIÉ/chevaux",
      r.nature == C.CONVENTION and r.statut == C.VERIFIE and r.valeur == "chevaux")
r = C.repond("En quelle année la révolution française ?")
check("révolution française -> passe/VÉRIFIÉ/1789",
      r.nature == C.PASSE and r.statut == C.VERIFIE and r.valeur.startswith("1789"))

# 2) ARITHMÉTIQUE fermée -> nécessité calculée, exacte.
r = C.repond("Combien font 17 * 23 + 4 ?")
check("17*23+4 -> necessite/VÉRIFIÉ/395", r.nature == C.NECESSITE and r.statut == C.VERIFIE and r.valeur == "395")
r = C.repond("calcule (100 - 1) // 7")
check("(100-1)//7 -> 14", r.statut == C.VERIFIE and r.valeur == "14")

# 3) GARDE ANTI-DoS : exposant géant -> PAS de calcul (None), donc pas VÉRIFIÉ-arithmétique.
r = C.repond("combien font 2 ** 99999999 ?")
check("2**99999999 -> jamais un calcul monstre (pas VÉRIFIÉ-arith)",
      not (r.statut == C.VERIFIE and r.source == "évaluation arithmétique"))

# 4) NON-BORNÉ -> ABSTENTION (jamais d'affirmation de vérité).
NB = ["Quel est ton plat préféré ?", "Devrait-on coloniser Mars ?", "À ton avis, quel est le plus beau pays ?",
      "Invente une histoire sur un dragon.", "Quel est le sens de la vie ?", "Faut-il devenir végétarien ?",
      "Que se passerait-il si la Lune disparaissait ?"]
for t in NB:
    r = C.repond(t)
    check(f"non-borné ABSTENTION : « {t[:32]}… »", r.statut == C.ABSTENTION and r.nature == C.NON_BORNE)

# 4bis) GATE SUR LE RÉSULTAT (raffinement 2026-07-02) : un marqueur SOUPLE (opinion/goût) n'avorte plus
#       une question qu'un juge borné VÉRIFIE — le résultat prime la catégorie. Les marqueurs DURS
#       (futur/contrefactuel) restent préemptifs : un fait présent n'est pas une vérité du monde demandé.
r = C.repond("À ton avis, quelle est la capitale de la France ?")
check("souple + fait vérifié -> VÉRIFIÉ/Paris (le résultat prime la catégorie)",
      r.statut == C.VERIFIE and r.valeur == "Paris")
r = C.repond("Que se passerait-il si la capitale de la France changeait ?")
check("dur (contrefactuel) + fait présent -> ABSTENTION (jamais un fait présent pour un autre monde)",
      r.statut == C.ABSTENTION and r.nature == C.NON_BORNE)
r = C.repond("Qui a inventé le téléphone ?")
check("collision « inventé » -> saveur FACTUELLE (hors base, jamais opinion), jamais VÉRIFIÉ à tort",
      r.statut != C.VERIFIE and r.nature != C.NON_BORNE)

# 5) SOUNDNESS ADVERSE : faits du monde/passé NON couverts -> jamais VÉRIFIÉ (HORS honnête).
PIEGES = ["Quelle est la capitale de la Mongolie ?", "Qui a peint la Joconde ?",
          "En quelle année est mort Napoléon ?", "Quelle est la population du Brésil ?",
          "Quelle est la hauteur du mont Everest ?", "Qui a inventé le téléphone ?",
          "Quelle est la capitale de l'Australie ?", "Quel est le symbole chimique du plomb ?"]
for t in PIEGES:
    r = C.repond(t)
    check(f"piège factuel inconnu -> jamais VÉRIFIÉ : « {t[:32]}… »", r.statut != C.VERIFIE)

# 6) DEMANDE STRUCTURÉE (nécessité) : solvable -> VÉRIFIÉ ; incohérente -> HORS (jamais un faux).
r = C.repond(point_entree="somme_carres", signature="xs", exemples=[([1, 2, 3], 14), ([2, 3], 13)],
             exemples_held=[([5], 25), ([0, 4], 16)])
check("structurée somme_carres -> necessite/VÉRIFIÉ", r.nature == C.NECESSITE and r.statut == C.VERIFIE and r.valeur)
r = C.repond(point_entree="incoherent", signature="x", exemples=[([3, 1, 2], 42)], exemples_held=[([5], 99)])
check("structurée incohérente -> necessite/HORS (pas de faux)", r.nature == C.NECESSITE and r.statut == C.HORS)

# 7) Demande vide -> HORS, pas de plantage.
check("vide -> HORS", C.repond("").statut == C.HORS and C.repond(None).statut == C.HORS)

# 8) INVARIANT GLOBAL : sur TOUT le batch ci-dessus, aucun VÉRIFIÉ ne sort sans valeur ni source.
for t in NB + PIEGES + ["Quelle est la capitale de la France ?", "Combien font 2 + 2 ?"]:
    r = C.repond(t)
    if r.statut == C.VERIFIE:
        check(f"VÉRIFIÉ porte valeur+source : « {t[:28]}… »", bool(r.valeur) and bool(r.source))

# 9) RÈGLE POSÉE (route structurée vers le moteur regle) — sound : conformité par prédicat explicite,
#    lettre par lookup exact, abstention sur interprétation/donnée manquante, HORS si introuvable.
r = C.repond(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"temperature": 3})
check("conformité HACCP 3°C -> regle/VÉRIFIÉ/CONFORME",
      r.nature == C.REGLE and r.statut == C.VERIFIE and r.valeur == "CONFORME" and r.source)
r = C.repond(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"temperature": 8})
check("conformité HACCP 8°C -> regle/VÉRIFIÉ/NON_CONFORME",
      r.nature == C.REGLE and r.statut == C.VERIFIE and r.valeur == "NON_CONFORME")
r = C.repond(scope="FR", ident="Code civil art. 414", cas={"age": 20})
check("majorité 20 ans -> CONFORME", r.statut == C.VERIFIE and r.valeur == "CONFORME")
r = C.repond(scope="FR", ident="Code civil art. 414", cas={"age": 16})
check("majorité 16 ans -> NON_CONFORME", r.statut == C.VERIFIE and r.valeur == "NON_CONFORME")
# Lettre seule (cas absent) -> lookup exact, donnée vérifiée.
r = C.repond(scope="FR", ident="Code de la route R413-3")
check("lettre R413-3 -> regle/VÉRIFIÉ + contenu + source",
      r.nature == C.REGLE and r.statut == C.VERIFIE and "50 km/h" in r.valeur and r.source)
# Règle d'INTERPRÉTATION (pas de prédicat) -> ABSTENTION, jamais une fausse conformité.
r = C.repond(scope="FR", ident="Code civil art. 9", cas={"quoi": "vie privée"})
check("vie privée (interprétation) -> regle/ABSTENTION", r.nature == C.REGLE and r.statut == C.ABSTENTION)
r = C.repond(scope="UE", ident="RGPD art. 5", cas={})
check("RGPD art.5 (principes) -> ABSTENTION", r.statut == C.ABSTENTION)
# Donnée MANQUANTE dans le cas -> ABSTENTION (on ne devine pas).
r = C.repond(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"autre": 1})
check("conformité sans le champ requis -> ABSTENTION", r.statut == C.ABSTENTION)
# Règle INTROUVABLE -> HORS honnête (jamais inventée), jamais VÉRIFIÉ.
r = C.repond(scope="FR", ident="Article imaginaire 999", cas={"x": 1})
check("règle introuvable -> regle/HORS (jamais inventée)", r.nature == C.REGLE and r.statut == C.HORS)
# DATÉ : une règle non encore en vigueur à la date demandée -> jamais une conformité VÉRIFIÉE.
r = C.repond(scope="ACME", ident="Remise fidélité", cas={"anciennete_mois": 24}, date="2020-01-01")
check("règle non en vigueur en 2020 -> jamais VÉRIFIÉ", r.statut != C.VERIFIE)

# 10) SOUNDNESS GLOBALE route-règle : sur un batch de cas, aucun VÉRIFIÉ sans valeur+source, et
#     un cas d'interprétation/introuvable ne sort JAMAIS en VÉRIFIÉ.
batch_regle = [
    dict(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"temperature": 5}),
    dict(scope="FR", ident="Code civil art. 9", cas={"quoi": "x"}),
    dict(scope="FR", ident="Article imaginaire 999", cas={"x": 1}),
    dict(scope="UE", ident="RGPD art. 5"),
]
for kw in batch_regle:
    r = C.repond(**kw)
    if r.statut == C.VERIFIE:
        check(f"route-règle VÉRIFIÉ complet : {kw['ident'][:24]}", bool(r.valeur) and bool(r.source))

print(f"\nCLASSIFIEUR VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
