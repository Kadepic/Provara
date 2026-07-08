"""
VALIDATION de la BASE DE FAITS VÉRIFIÉS (`base_faits.py`) — juge load-bearing des catégories 2/3/4.

Jusqu'ici base_faits n'était testé QU'indirectement (quelques faits via le classifieur). Ce validateur
verrouille ses INVARIANTS de soundness, sans changer son comportement (bornage pur) :

  1. INTÉGRITÉ des données : chaque Fait porte une valeur non vide, une catégorie connue, une source.
  2. RÉCUPÉRABILITÉ : tout fait stocké est retrouvé par `cherche(relation, entite)` (clé canonique).
  3. ROBUSTESSE de `normalise` : idempotente, insensible casse/accents/ponctuation/espaces.
  4. ARTICLES : `_sans_articles` retire les déterminants de tête (la/le/les/du/des/de/d/l).
  5. NL CORRECT : `repond_nl` rend le bon fait pour des formulations canoniques (chaque catégorie).
  6. SOUNDNESS ADVERSE (le cœur) : sur une large batterie d'INCONNUS (entité absente, relation absente,
     hors-gabarit), `repond_nl`/`cherche` ne renvoient JAMAIS un faux — toujours (HORS, None) / None.
  7. INVARIANT GLOBAL : sur un batch mixte, tout VÉRIFIÉ porte un Fait complet (valeur+catégorie+source).
"""
from __future__ import annotations

from garde_ressources import borne

import base_faits as BF

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


CATS = {BF.CAT_PHYSIQUE, BF.CAT_PASSE, BF.CAT_CONVENTION}

# 1) INTÉGRITÉ : chaque Fait est complet et bien typé.
for (rel, ent), fait in BF.FAITS.items():
    check(f"intégrité ({rel!r},{ent!r}) : valeur+catégorie∈CATS+source",
          isinstance(fait.valeur, str) and fait.valeur.strip() != ""
          and fait.categorie in CATS
          and isinstance(fait.source, str) and fait.source.strip() != "")

# 2) RÉCUPÉRABILITÉ : tout fait stocké se retrouve par cherche (clé canonique), objet identique.
for (rel, ent), fait in BF.FAITS.items():
    check(f"récupérable ({rel!r},{ent!r}) -> même Fait", BF.cherche(rel, ent) is fait)

# 3) ROBUSTESSE de normalise.
check("normalise idempotente",
      all(BF.normalise(BF.normalise(s)) == BF.normalise(s)
          for s in ["  La  FRANCE !! ", "Révolution Française", "Œil", "déjà-vu", "A+B = C"]))
check("normalise insensible casse/accents", BF.normalise("FRÂNCÉ") == BF.normalise("france"))
check("normalise compacte ponctuation/espaces", BF.normalise("  a , b ;;  c  ") == "a b c")
check("normalise ne garde que [a-z0-9 ]", all(c.isalnum() or c == " " for c in BF.normalise("É@#1—b!")))

# 4) ARTICLES : retrait des déterminants de tête (et eux seuls).
check("_sans_articles('la France') == 'france'", BF._sans_articles("la France") == "france")
check("_sans_articles('de l eau') == 'eau'", BF._sans_articles("de l eau") == "eau")
check("_sans_articles n'enlève pas un mot interne", BF._sans_articles("mont blanc") == "mont blanc")

# 5) NL CORRECT : une formulation canonique par catégorie -> VÉRIFIÉ + bon fait.
cas_ok = [
    ("Quelle est la capitale de la France ?", "Paris", BF.CAT_PHYSIQUE),
    ("capitale du Japon", "Tokyo", BF.CAT_PHYSIQUE),
    ("Quel est le pluriel de cheval ?", "chevaux", BF.CAT_CONVENTION),
    ("Quelle est la vitesse de la lumière ?", "299792458", BF.CAT_PHYSIQUE),
    ("En quelle année a eu lieu la révolution française ?", "1789", BF.CAT_PASSE),
    ("capitale du Portugal", "Lisbonne", BF.CAT_PHYSIQUE),
    ("capitale des États-Unis", "Washington", BF.CAT_PHYSIQUE),
    ("symbole chimique de l'hydrogène", "H", BF.CAT_PHYSIQUE),
    ("symbole chimique du sodium", "Na", BF.CAT_PHYSIQUE),
    ("pluriel de bijou", "bijoux", BF.CAT_CONVENTION),
    ("pluriel de journal", "journaux", BF.CAT_CONVENTION),
    ("quelle est l'unité de la seconde ?", "temps", BF.CAT_CONVENTION),
    ("en quelle année la première guerre mondiale ?", "1914", BF.CAT_PASSE),
    ("à quelle température l'eau gèle", "0", BF.CAT_PHYSIQUE),
    ("point de congélation de l'eau", "0", BF.CAT_PHYSIQUE),
    ("température d'ébullition de l'eau", "100", BF.CAT_PHYSIQUE),
]
for q, attendu, cat in cas_ok:
    st, f = BF.repond_nl(q)
    check(f"NL VÉRIFIÉ « {q[:34]}… » -> {attendu}",
          st == BF.VERIFIE and f is not None and attendu in f.valeur and f.categorie == cat)

# 6) SOUNDNESS ADVERSE : aucun faux sur les inconnus.
#    (a) gabarit reconnu mais ENTITÉ absente -> HORS, jamais inventé.
pieges_entite = [
    "Quelle est la capitale de la Mongolie ?", "capitale du Burkina Faso",
    "Quel est le pluriel de licorne ?", "symbole chimique du plomb",
    "définition de zorglub",
    # « point de fusion du fer/or » ne doit PAS matcher la congélation de l'EAU (0 °C) — régression 2026-07-08
    "point de fusion du fer", "point de fusion de l'or",
]
for q in pieges_entite:
    st, f = BF.repond_nl(q)
    check(f"adverse entité inconnue -> HORS : « {q[:32]}… »", st == BF.HORS and f is None)

#    (b) hors gabarit / relation absente -> HORS.
pieges_hors = [
    "Quel est ton plat préféré ?", "Qui a peint la Joconde ?",
    "Quelle est la population du Brésil ?", "Raconte-moi une blague.",
    "", "   ", "azerty qwerty",
]
for q in pieges_hors:
    st, f = BF.repond_nl(q)
    check(f"adverse hors-base -> HORS : « {q[:32]}… »", st == BF.HORS and f is None)

#    (c) cherche sur clé inconnue -> None (jamais un Fait).
check("cherche clé inconnue -> None", BF.cherche("capitale", "atlantide") is None)
check("cherche relation inconnue -> None", BF.cherche("monnaie", "france") is None)

# 6bis) ANCRES extension lot #3 — valeurs vérifiées indépendamment (garde anti-typo de la transcription).
ANCRES_EXT = {
    ("capitale", "islande"): "Reykjavik", ("capitale", "croatie"): "Zagreb", ("capitale", "cuba"): "La Havane",
    ("capitale", "pakistan"): "Islamabad", ("capitale", "nouvelle zelande"): "Wellington",
    ("capitale", "senegal"): "Dakar", ("capitale", "irak"): "Bagdad",
    ("symbole_chimique", "bore"): "B", ("symbole_chimique", "silicium"): "Si",
    ("symbole_chimique", "antimoine"): "Sb", ("symbole_chimique", "cesium"): "Cs",
    ("symbole_chimique", "vanadium"): "V", ("symbole_chimique", "molybdene"): "Mo",
    ("annee", "decouverte de l amerique"): "1492", ("annee", "naufrage du titanic"): "1912",
    ("annee", "chute de l urss"): "1991", ("annee", "attentats du 11 septembre"): "2001",
}
for (rel, ent), attendu in ANCRES_EXT.items():
    f = BF.cherche(rel, ent)
    check(f"ancre ext {rel}({ent}) == {attendu}", f is not None and attendu in f.valeur)
# plomb DOIT rester inconnu (piège adverse préservé malgré l'extension des symboles).
check("plomb reste inconnu (piège adverse préservé)", BF.cherche("symbole_chimique", "plomb") is None)

# 7) INVARIANT GLOBAL : tout VÉRIFIÉ d'un batch mixte porte un Fait complet.
batch = [q for q, *_ in cas_ok] + pieges_entite + pieges_hors
for q in batch:
    st, f = BF.repond_nl(q)
    if st == BF.VERIFIE:
        check(f"VÉRIFIÉ complet : « {q[:28]}… »",
              f is not None and bool(f.valeur) and f.categorie in CATS and bool(f.source))

print(f"\nBASE_FAITS VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
