"""
VALIDE L'UNICITÉ DES RELATIONS — deux scripts, une relation, deux sémantiques : le dernier écrivain gagne.

LE DÉFAUT MESURÉ (2026-07-12). `ingere_wikidata.ecrit_jsonl` RÉGÉNÈRE le fichier de la relation. Si deux
scripts d'ingestion publient le MÊME nom de relation, celui qui tourne en dernier efface l'autre — sans
un mot. Cas vécu : `famille_langue` était publiée par
  • `ingere_langues_famille.py` — catalogue curé, 81 langues, GRANDES familles (« français -> romane ») ;
  • `ingere_langues.py`         — Wikidata, famille IMMÉDIATE (« français -> langue d'oïl »).
Le second a écrasé le premier. Le store répondait « famille de l'anglais : langues angliques », et
`valide_lecteur` (qui exige la base COMPLÈTE et ne tourne donc PAS dans la suite) échouait sur SIX ancres
— hindi et finnois avaient purement disparu. La relation Wikidata s'appelle désormais
`famille_immediate_langue` : deux questions, deux noms.

CE QUE CE CLIQUET GARDE. Toute collision NOUVELLE rougit. Les collisions connues sont listées ici, chacune
avec la RAISON qui la rend inoffensive — et cette raison est vérifiable : les scripts d'une collision
tolérée doivent publier des faits sur des entités DISJOINTES ou identiques, jamais deux sémantiques.
Ajouter un nom à l'allowlist sans raison écrite est un refus de gate.
"""
import os
import re
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ING = os.path.join(_RACINE, "ingestion")
_PUBLIE = re.compile(r'publie\(\s*["\']([a-z0-9_]+)["\']')

# Collisions CONNUES et tolérées : relation -> (scripts attendus, raison vérifiée).
# Elles enrichissent une même relation par lots DISJOINTS (le dernier écrivain reconstruit le fichier
# depuis SA source ; c'est un défaut de conception hérité, borné ici, à résorber lot par lot).
_TOLEREES = {
    "domaine_dieu": ({"ingere_mythologie.py", "ingere_mythologie2.py", "ingere_mythologie3.py"},
                     "trois panthéons, entités disjointes ; même sémantique (le domaine du dieu)"),
    "pantheon_dieu": ({"ingere_mythologie2.py", "ingere_mythologie3.py"},
                      "deux panthéons, entités disjointes ; même sémantique"),
    "pays_ville": ({"ingere_qlever.py", "ingere_villes.py"},
                   "même sémantique (le pays de la ville) ; le second élargit le premier"),
    "point_culminant": ({"ingere_qlever.py", "ingere_wikidata.py"},
                        "même sémantique (le point culminant du pays)"),
    "regime_alimentaire": ({"ingere_regime_alimentaire.py", "ingere_t4.py"},
                           "même sémantique (le régime alimentaire du taxon)"),
}

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def collisions() -> dict:
    par_rel = {}
    for nom in sorted(os.listdir(_ING)):
        if not nom.endswith(".py"):
            continue
        with open(os.path.join(_ING, nom), encoding="utf-8", errors="ignore") as fh:
            for rel in set(_PUBLIE.findall(fh.read())):
                par_rel.setdefault(rel, set()).add(nom)
    return {r: s for r, s in par_rel.items() if len(s) > 1}


trouvees = collisions()

# 1) AUCUNE collision inconnue.
inconnues = {r: s for r, s in trouvees.items() if r not in _TOLEREES}
check(not inconnues,
      "aucune relation publiée par plusieurs scripts hors allowlist (%s)"
      % ", ".join("%s <- %s" % (r, sorted(s)) for r, s in sorted(inconnues.items())) or "aucune")

# 2) Les tolérées le sont EXACTEMENT (ni script en plus, ni en moins : une dérive est une collision neuve).
for rel, (attendus, _raison) in sorted(_TOLEREES.items()):
    reels = trouvees.get(rel, set())
    check(reels == attendus,
          "collision tolérée « %s » : scripts inchangés (attendu %s, mesuré %s)"
          % (rel, sorted(attendus), sorted(reels)))

# 3) L'allowlist ne périme pas : une entrée dont la collision a disparu doit être RETIRÉE.
check(not (set(_TOLEREES) - set(trouvees)),
      "allowlist à jour : %s n'est plus en collision, retirer l'entrée"
      % sorted(set(_TOLEREES) - set(trouvees)))

# 4) LE CAS FONDATEUR NE DOIT JAMAIS REVENIR : `famille_langue` a UN SEUL producteur, le catalogue curé ;
#    la table Wikidata porte un nom qui dit ce qu'elle contient.
prod_fam = trouvees.get("famille_langue")
check(prod_fam is None, "« famille_langue » n'est plus en collision (le cas fondateur est clos)")
src_wd = open(os.path.join(_ING, "ingere_langues.py"), encoding="utf-8").read()
check("famille_immediate_langue" in src_wd and 'publie("famille_langue"' not in src_wd,
      "ingere_langues.py publie `famille_immediate_langue` (le nom dit le contenu)")
src_cur = open(os.path.join(_ING, "ingere_langues_famille.py"), encoding="utf-8").read()
check('publie("famille_langue"' in src_cur, "ingere_langues_famille.py reste le seul producteur curé")

# 5) ANCRE NON CIRCULAIRE (si le store est là) : le français est une langue ROMANE, l'anglais GERMANIQUE.
_dossier = os.environ.get("LECTEUR_DATASETS_DIR", "")
_t = os.path.join(_dossier, "famille_langue.jsonl") if _dossier else ""
if _t and os.path.exists(_t):
    import json
    table = {}
    with open(_t, encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.startswith('{"_relation"'):
                continue
            o = json.loads(ligne)
            table[o["entite"]] = o["valeur"]
    for langue, famille in (("français", "romane"), ("anglais", "germanique"), ("russe", "slave"),
                            ("arabe", "sémitique"), ("hindi", "indo-aryenne"), ("finnois", "ouralienne")):
        check(table.get(langue) == famille,
              "ANCRE : famille_langue(« %s ») == « %s » (mesuré : %r)" % (langue, famille, table.get(langue)))
else:
    check(True, "(store complet absent : les ancres de famille sont sautées)")

print("=== valide_collision_relations : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
