"""
VALIDATION — FORME LISTE-DE-DICTS×CLÉ (invention_multi) : palier structurel, atome 9 — la COLONNE relationnelle.

Frontière MESURÉE : une table (liste d'enregistrements) + un champ PARAMÈTRE restait brique_manquante —
etend_liste_dicts (mono) découvre le champ dans les DONNÉES, ici le champ est un ARGUMENT (croisement
multi-arg × structures). Comblé par la 3e forme de type (_LD_OPS : projection, projection avec défaut,
agrégats/tri de colonne, sélection), détectée AVANT liste×scalaire (une clé entière matcherait (liste, int)
à tort). Registre VIDE honnête (rien ne servait la classe).

Méthode SOUND : labels par fonctions de référence, tables ADVERSARIALES (champs multiples, ordres variés,
valeurs non triées), held-out séparé, re-vérif HORS moteur ; sondes de forme = table renversée, champ RETIRÉ
du 1er enregistrement, valeur perturbée, autre champ commun.

Prouve : (1) FRONTIÈRES FERMÉES — somme/max/colonne_triee/colonne_ou_zero/sélection deviennent INVENTION ;
(2) AMBIGU HONNÊTE STRUCTUREL — `colonne` stricte (tous champs présents au spec) est INDÉCIDABLE par I/O pur
face à la projection-avec-défaut (le crash n'est pas une paire étiquetable) -> AMBIGU avec sonde
discriminante (enregistrement sans le champ) = le moteur demande de renforcer le besoin ; avec un exemple à
champ MANQUANT au spec, colonne_ou_zero est INVENTION unique ; (3) CORRECT — re-vérif hors moteur ;
(4) DÉTERMINISME ; (5) NON-RÉGRESSION des 3 autres chemins d'arité 2 ; (6) témoin hors vocab honnête.
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


# tables ADVERSARIALES : plusieurs champs, valeurs non triées, champ demandé varié.
LD = [([{"n": 3, "p": 1}, {"n": 7, "p": 2}], "n"),
      ([{"a": 5, "n": 0}, {"n": 4, "a": 1}, {"n": 9, "a": 2}], "n"),
      ([{"n": 2, "q": 8}, {"n": 6, "q": 1}], "q")]
LD_HELD = [([{"n": 6, "q": 8}, {"n": 2, "q": 5}], "n")]
LD_FRAIS = [([{"z": 4, "w": 7}, {"z": 1, "w": 3}], "z")]
# un enregistrement SANS le champ : sépare get(k,0) de d[k] (les 2 branches du filtre, leçon PBE).
G = [([{"n": 3}, {"p": 1}], "n"), ([{"n": 5}, {"n": 4}, {"q": 2}], "n")]
G_HELD = [([{"x": 1}, {"n": 9}], "n")]
G_FRAIS = [([{"n": 7}, {"y": 2}], "n")]

CIBLES = [
    ("somme_colonne", lambda x, k: sum(d[k] for d in x), LD, LD_HELD, LD_FRAIS),
    ("max_colonne", lambda x, k: max(d[k] for d in x), LD, LD_HELD, LD_FRAIS),
    ("colonne_triee", lambda x, k: sorted(d[k] for d in x), LD, LD_HELD, LD_FRAIS),
    ("colonne_ou_zero", lambda x, k: [d.get(k, 0) for d in x], G, G_HELD, G_FRAIS),
    ("avec_champ", lambda x, k: [d for d in x if k in d], G, G_HELD, G_FRAIS),
]

realisations = {}
for nom, ref, spec_in, held_in, frais in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, k), ref(x, k)) for x, k in spec_in],
                               [((x, k), ref(x, k)) for x, k in held_in])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x, k) == ref(x, k) for x, k in spec_in + held_in + frais))
    realisations[nom] = v.par

# AMBIGU HONNÊTE STRUCTUREL : colonne stricte (tous champs présents) vs projection-avec-défaut —
# indécidable par I/O pur ; la sonde discriminante est un enregistrement SANS le champ.
_ref_col = lambda x, k: [d[k] for d in x]
v = IM.examine_cible_multi("colonne",
                           [((x, k), _ref_col(x, k)) for x, k in LD],
                           [((x, k), _ref_col(x, k)) for x, k in LD_HELD])
check("colonne stricte : AMBIGU honnête (indécidable par I/O pur) avec sonde discriminante",
      v.statut == IM.AMBIGU and v.sonde is not None)

# DÉTERMINISME.
_ref_sc = CIBLES[0][1]
v2 = IM.examine_cible_multi("somme_colonne",
                            [((x, k), _ref_sc(x, k)) for x, k in LD],
                            [((x, k), _ref_sc(x, k)) for x, k in LD_HELD])
check("déterminisme (somme_colonne : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["somme_colonne"])

# HONNÊTETÉ : cible HORS vocabulaire (champ du 1er enregistrement seul) -> BRIQUE_MANQUANTE.
_ref_hors = lambda x, k: x[0][k]
v = IM.examine_cible_multi("champ_du_premier",
                           [((x, k), _ref_hors(x, k)) for x, k in LD],
                           [((x, k), _ref_hors(x, k)) for x, k in LD_HELD])
check("cible hors vocabulaire : BRIQUE_MANQUANTE honnête", v.statut == IM.BRIQUE_MANQUANTE)

# NON-RÉGRESSION : les 3 autres chemins d'arité 2 ne bougent pas.
v = IM.examine_cible_multi("n_premiers",
                           [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])],
                           [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])])
check("liste×scalaire : n_premiers reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("retire_cle",
                           [(({"a": 3, "b": 1}, "a"), {"b": 1}), (({"x": 5, "z": 9}, "z"), {"x": 5}),
                            (({"m": 7, "n": 4}, "n"), {"m": 7})],
                           [(({"u": 6, "v": 1}, "v"), {"u": 6})])
check("dict×scalaire : retire_cle reste INVENTION", v.statut == IM.INVENTION)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_liste_dicts_cle : {ok}/{total}")
assert ok == total
