"""
VALIDATION — FORME TABLE×TABLE (invention_multi) : palier structurel, atome 11 — la JOINTURE.

REFERME L'ALGÈBRE RELATIONNELLE DE BASE : colonne (atome 9) ✓, sélection ✓, groupby/pivot/dégroupage
(atomes 2/7/8) ✓, jointure ✓. Frontière MESURÉE : jointure interne, clés communes, semi/anti-jointure =
brique_manquante. La CLÉ de jointure est DÉCOUVERTE dans les données (champs présents dans tous les
enregistrements des deux tables, patron etend_synthese) puis cuite en littéral ; les sondes (retrait d'une
correspondance, valeur de clé perturbée, doublon = multiplicité, SWAP) discriminent clé et variante.

Méthode SOUND : labels par fonctions de référence, tables ADVERSARIALES (correspondances partielles — des
enregistrements avec ET sans vis-à-vis, ordres non triés), held-out séparé, re-vérif HORS moteur.

Prouve : (1) FRONTIÈRES FERMÉES — jointure_interne, ids_communs, semi_jointure, anti_jointure deviennent
INVENTION avec la clé CORRECTE ; (2) DEUX CHAMPS COMMUNS — la bonne clé est discriminée par le spec (jointure
sur 'id', pas sur 'g') ; (3) CORRECT — re-vérif hors moteur, MULTIPLICITÉ vérifiée (doublon de clé -> deux
lignes jointes) ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — concat reste EXISTE_DEJA, les autres formes
d'arité 2 intactes ; (6) témoin hors vocab honnête (jointure externe gauche avec défaut).
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
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


# tables ADVERSARIALES : correspondances PARTIELLES (avec et sans vis-à-vis), ordres non triés.
T1 = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}, {"id": 3, "n": "c"}]
U1 = [{"id": 2, "v": 20}, {"id": 1, "v": 10}, {"id": 8, "v": 80}]
T2 = [{"id": 6, "n": "y"}, {"id": 5, "n": "x"}]
U2 = [{"id": 6, "v": 3}, {"id": 4, "v": 8}]
SPEC = [(T1, U1), (T2, U2)]
HELD = [([{"id": 9, "n": "m"}, {"id": 7, "n": "w"}], [{"id": 9, "v": 1}, {"id": 4, "v": 2}])]
FRAIS = [([{"id": 3, "n": "q"}], [{"id": 3, "v": 5}, {"id": 3, "v": 6}])]     # multiplicité

CIBLES = [
    ("jointure_interne", lambda a, b: [{**da, **db} for da in a for db in b if da["id"] == db["id"]]),
    ("ids_communs",      lambda a, b: sorted({d["id"] for d in a} & {d["id"] for d in b})),
    ("semi_jointure",    lambda a, b: [da for da in a if da["id"] in {d["id"] for d in b}]),
    ("anti_jointure",    lambda a, b: [da for da in a if da["id"] not in {d["id"] for d in b}]),
]

realisations = {}
for nom, ref in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((a, b), ref(a, b)) for a, b in SPEC],
                               [((a, b), ref(a, b)) for a, b in HELD])
    check(f"{nom} : frontière FERMÉE (INVENTION, clé découverte)",
          v.statut == IM.INVENTION and "'id'" in v.par)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(a, b) == ref(a, b) for a, b in SPEC + HELD + FRAIS))
    realisations[nom] = v.par

# MULTIPLICITÉ : un doublon de clé côté b -> deux lignes jointes.
check("multiplicité : doublon de clé -> deux lignes jointes",
      _fn2(realisations["jointure_interne"])([{"id": 3, "n": "q"}], [{"id": 3, "v": 5}, {"id": 3, "v": 6}])
      == [{"id": 3, "n": "q", "v": 5}, {"id": 3, "n": "q", "v": 6}])

# DEUX CHAMPS COMMUNS : 'id' et 'g' présents partout — le spec (où joindre sur g diffère) impose la bonne clé.
A2 = [{"id": 1, "g": 0, "n": "a"}, {"id": 2, "g": 0, "n": "b"}]
B2 = [{"id": 1, "g": 9, "v": 5}, {"id": 3, "g": 0, "v": 7}]
_ref_j2 = lambda a, b: [{**da, **db} for da in a for db in b if da["id"] == db["id"]]
v = IM.examine_cible_multi("jointure_deux_cles",
                           [((A2, B2), _ref_j2(A2, B2)),
                            (([{"id": 4, "g": 1, "n": "c"}], [{"id": 4, "g": 2, "v": 1}]),
                             _ref_j2([{"id": 4, "g": 1, "n": "c"}], [{"id": 4, "g": 2, "v": 1}]))],
                           [(([{"id": 6, "g": 3, "n": "d"}], [{"id": 6, "g": 8, "v": 2}]),
                             _ref_j2([{"id": 6, "g": 3, "n": "d"}], [{"id": 6, "g": 8, "v": 2}]))])
check("deux champs communs : la jointure est sur 'id' (le spec discrimine la clé)",
      v.statut == IM.INVENTION and "'id'" in v.par and "'g'" not in v.par)

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("jointure_interne",
                            [((a, b), _ref_0(a, b)) for a, b in SPEC],
                            [((a, b), _ref_0(a, b)) for a, b in HELD])
check("déterminisme (jointure : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["jointure_interne"])

# HONNÊTETÉ : jointure externe gauche avec défaut = HORS vocabulaire -> BRIQUE_MANQUANTE.
_ref_lj = lambda a, b: [{**da, **nx[0]} if (nx := [db for db in b if db["id"] == da["id"]]) else {**da, "v": 0}
                        for da in a]
v = IM.examine_cible_multi("jointure_gauche_defaut",
                           [((a, b), _ref_lj(a, b)) for a, b in SPEC],
                           [((a, b), _ref_lj(a, b)) for a, b in HELD])
check("cible hors vocabulaire (jointure gauche à défaut) : BRIQUE_MANQUANTE honnête",
      v.statut == IM.BRIQUE_MANQUANTE)

# NON-RÉGRESSION : concat tables EXISTE_DEJA ; formes voisines intactes.
_ref_c = lambda a, b: a + b
v = IM.examine_cible_multi("concat_tables",
                           [((a, b), _ref_c(a, b)) for a, b in SPEC],
                           [((a, b), _ref_c(a, b)) for a, b in HELD])
check("concat_tables : reste EXISTE_DEJA (registre de la forme)", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("somme_colonne",
                           [(([{"n": 3, "p": 1}, {"n": 7, "p": 2}], "n"), 10),
                            (([{"a": 5, "n": 0}, {"n": 4, "a": 1}], "n"), 4)],
                           [(([{"n": 6}, {"n": 2}], "n"), 8)])
check("liste-de-dicts×clé : somme_colonne reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_jointure : {ok}/{total}")
assert ok == total
