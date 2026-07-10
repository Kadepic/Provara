"""
VALIDE LA CLÉ CANONIQUE — une clé n'est JAMAIS vide (MANQUE silencieux, mesuré le 2026-07-12).

CE QU'IL GARDE. `lecteur.ingere_table` IGNORE les clés vides — sans un mot. `_sans_articles` en produisait
pour deux familles d'entités, et 47 faits (dans 45 tables) tombaient au chargement, présents sur le disque
et introuvables à la lecture :

  • l'entité EST un article français : « D » (le langage de Walter Bright), « d », « l » — et pire,
    « d » et « l » avaient la MÊME clé vide : deux entités distinctes confondues ;
  • l'entité est écrite hors alphabet latin : `normalise` compacte sur `[^a-z0-9 ]+`, donc
    « Петергофский десант » ou « Αθανάσιος » devenaient vides — perdus à jamais.

Mesure avant/après sur les 72 041 162 faits du store : clés vides 47 -> 0 ; collisions 6 -> 4, les 4
restantes étant la MÊME personne sous deux graphies (« Jacques Bénigne » / « Jacques-Bénigne » Bossuet) —
c'est précisément le travail d'une clé canonique, pas un défaut.

ANCRE NON CIRCULAIRE : « le créateur du langage D est Walter Bright » est connu indépendamment du code.

CONTRE-ÉPREUVE DE SABOTAGE : on rejoue l'ANCIENNE règle (dépouillement sans repli) et on vérifie qu'elle
produisait bien la clé vide et la collision — sinon ce cliquet ne garderait rien.
"""
import os
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from base_faits import _ARTICLES, _sans_articles, normalise

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LE COMPORTEMENT NOMINAL EST INCHANGÉ (le repli ne s'arme que sur une clé vide) ────────────────
check(_sans_articles("la france") == "france", "les articles de tête tombent toujours")
check(_sans_articles("le mont Blanc") == "mont blanc", "normalisation + dépouillement inchangés")
check(_sans_articles("eau") == "eau", "une entité ordinaire n'est pas touchée")
check(_sans_articles("des moines") == "moines", "article pluriel dépouillé")

# ── 2) UNE CLÉ N'EST JAMAIS VIDE ─────────────────────────────────────────────────────────────────────
for e in ("d", "l", "D", "de", "la", "les", "l'", "Петергофский десант", "Αθανάσιος", "日本語"):
    check(_sans_articles(e) != "", "clé non vide pour %r" % e)

# ── 3) LES ENTITÉS-ARTICLES RESTENT DISTINCTES (le faux « D -> Lima » est mort) ──────────────────────
check(_sans_articles("d") != _sans_articles("l"), "« d » et « l » ont des clés DIFFÉRENTES")
check(_sans_articles("D") == _sans_articles("d"), "la casse ne distingue pas (clé canonique)")
check(_sans_articles("de") != _sans_articles("des"), "« de » et « des » restent distincts")

# ── 4) LES ÉCRITURES NON LATINES SURVIVENT ET RESTENT DISTINCTES ────────────────────────────────────
a, b = _sans_articles("Петергофский десант"), _sans_articles("Αθανάσιος")
check(a != b, "deux entités non latines ont des clés distinctes")
check(a == unicodedata.normalize("NFC", "Петергофский десант").casefold(), "repli NFC casefold, déterministe")
check(_sans_articles("Петергофский десант") == _sans_articles("ПЕТЕРГОФСКИЙ ДЕСАНТ"),
      "la clé non latine est insensible à la casse (idempotente)")

# ── 5) ANCRE : le fait jadis perdu est de nouveau atteignable ───────────────────────────────────────
# (lookup réel seulement si le store complet est là ; sinon la clé suffit à prouver la non-vacuité)
# La PROPRIÉTÉ gardée est : « si le disque porte le fait, le lookup DOIT le trouver ». Elle ne s'exerce
# que là où le fait est sur le disque — l'échantillon embarqué (que la suite épingle) ne porte pas « D ».
import json as _json

_dossier = os.environ.get("LECTEUR_DATASETS_DIR", "")
_table = os.path.join(_dossier, "createur_langage_programmation.jsonl") if _dossier else ""
_sur_disque = None
if _table and os.path.exists(_table):
    with open(_table, encoding="utf-8") as _fh:
        for _l in _fh:
            if _l.startswith('{"_relation"'):
                continue
            _o = _json.loads(_l)
            if _o.get("entite") == "D":
                _sur_disque = _o["valeur"]
                break
if _sur_disque is not None:
    import lecteur as L
    f = L.cherche("createur_langage_programmation", "D")
    check(f is not None and f.valeur == _sur_disque,
          "ANCRE : le fait « D » présent sur le disque est ATTEIGNABLE par lookup (jadis PERDU) "
          "— disque %r, lookup %r" % (_sur_disque, f.valeur if f else None))
    check("Walter Bright" in _sur_disque, "ANCRE INDÉPENDANTE : le créateur du langage D est Walter Bright")
else:
    check(True, "(le fait « D » n'est pas dans ce store : l'ancre de lookup ne s'exerce pas ici)")

# ── 6) CONTRE-ÉPREUVE DE SABOTAGE : l'ancienne règle produisait bien le défaut ───────────────────────
def _ancienne(entite):
    mots = normalise(entite).split()
    while mots and mots[0] in _ARTICLES:
        mots = mots[1:]
    return " ".join(mots)

check(_ancienne("d") == "" and _ancienne("l") == "",
      "SABOTAGE : l'ancienne règle vidait bien « d » et « l » (le cliquet garde quelque chose)")
check(_ancienne("d") == _ancienne("l"), "SABOTAGE : elle les CONFONDAIT (deux entités, une clé)")
check(_ancienne("Петергофский десант") == "", "SABOTAGE : elle vidait les écritures non latines")
check(_ancienne("la france") == _sans_articles("la france"), "SABOTAGE : hors clé vide, les deux coïncident")

# ── 7) LE STORE ÉCHANTILLON NE PORTE AUCUNE CLÉ VIDE ────────────────────────────────────────────────
import json

if _dossier and os.path.isdir(_dossier):
    vides = []
    for nom in sorted(os.listdir(_dossier))[:400]:            # borné : la suite doit rester rapide
        if not nom.endswith(".jsonl"):
            continue
        with open(os.path.join(_dossier, nom), encoding="utf-8") as fh:
            for ligne in fh:
                if ligne.startswith('{"_relation"'):
                    continue
                try:
                    e = json.loads(ligne)["entite"]
                except (ValueError, KeyError):
                    continue
                if e and not _sans_articles(e):
                    vides.append((nom, e))
    check(not vides, "aucune clé vide dans le store lu (%d trouvée(s))" % len(vides))
else:
    check(True, "(aucun store : scan sauté)")

# ── 8) LES CACHES SONT INVALIDÉS *MÉCANIQUEMENT* PAR UN CHANGEMENT DE CLÉ ───────────────────────────
# Défaut mesuré le 2026-07-12 : après le correctif ci-dessus, un cache CHAUD (bâti avec l'ancienne clé)
# servait encore `createur_langage_programmation("D") -> None`. Les caches STOCKENT les clés ; leur
# signature doit donc incorporer la version de la politique de clé, sinon l'invalidation repose sur la
# discipline — et la discipline a échoué.
from base_faits import CLE_VER  # noqa: E402

check(isinstance(CLE_VER, int) and CLE_VER >= 2, "base_faits.CLE_VER existe et vaut au moins 2")
_src_lect = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "src", "lecteur.py"), encoding="utf-8").read()
check("_CACHE_VER = (2, CLE_VER)" in _src_lect, "le cache marshal signe la politique de clé (CLE_VER)")
check("_COLF_VER = (2, CLE_VER)" in _src_lect, "le cache mmap .colf signe la politique de clé (CLE_VER)")

print("=== valide_cles_canoniques : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
