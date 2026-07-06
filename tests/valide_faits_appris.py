# -*- coding: utf-8 -*-
"""Gate FAITS APPRIS DU WEB (faits_appris.py + câblage assistant_nl) — apprentissage local des faits STRUCTURÉS
trouvés en ligne, réutilisables hors-ligne (demande Yohan 2026-07-06). FAUX=0 : seul le structuré est appris,
toujours attribué + daté ; jamais de valeur vide/sans source ; le texte libre (Wikipédia) n'entre jamais ici."""
import os
import tempfile

os.environ["FAITS_APPRIS_PATH"] = os.path.join(tempfile.mkdtemp(), "appris.jsonl")
import faits_appris as FA  # noqa: E402

_ok = [0]
_ko = [0]


def check(cond, label):
    if cond:
        _ok[0] += 1
    else:
        _ko[0] += 1
        print("  FAIL:", label)


FA._HORLOGE = lambda: "2026-07-06"           # horloge déterministe

# — apprentissage + rappel —
check(FA.apprend("capitale", "Ruritanie", "Strelsau", "Wikidata"), "apprend un fait structuré")
check(FA.rappelle("capitale", "Ruritanie")["valeur"] == "Strelsau", "rappelle la valeur apprise")
check(FA.rappelle_texte("capitale", "Ruritanie") == "Strelsau  (appris de Wikidata le 2026-07-06)",
      "rappel FORMATÉ : attribué ET daté (instantané honnête, pas une vérité intemporelle)")
check(FA.rappelle_texte("Capitale", "ruritanie") is not None, "clé insensible casse/accents")
check(FA.rappelle("capitale", "Syldavie") is None, "fait jamais appris -> None")

# — FRONTIÈRE FAUX=0 : valeur vide / source manquante jamais apprises —
check(FA.apprend("population", "Wakanda", "", "Wikidata") is False, "valeur vide -> refus (jamais un fait creux)")
check(FA.apprend("population", "Wakanda", None, "Wikidata") is False, "valeur None -> refus")
check(FA.apprend("x", "y", "z", "") is False, "source manquante -> refus (un fait appris est TOUJOURS attribué)")
check(FA.rappelle("population", "Wakanda") is None, "aucun de ces refus n'a été écrit")

# — DERNIER GAGNANT (rafraîchissement naturel sans réécriture) —
FA.apprend("capitale", "Ruritanie", "Zenda", "Wikidata", date="2026-07-08")
check(FA.rappelle("capitale", "Ruritanie")["valeur"] == "Zenda", "dernier apprentissage d'une clé fait foi")
check(FA.nombre_appris() == 1, "clé unique comptée une fois malgré 2 apprentissages")

# — CÂBLAGE assistant_nl : apprend en ligne, ressert HORS-LIGNE, attribué —
import assistant_nl as A          # noqa: E402
import veille_structure as VS     # noqa: E402
import classifieur_bornage as CB  # noqa: E402

VS.interroge = lambda attribut, entite, timeout=20: (
    ("Paris-sur-Ruritanie", "Wikidata") if attribut == "capitale" and "borduristan" in entite.lower() else None)
c = CB.classe("quelle est la capitale du Borduristan ?")
A._TRANSPORT = lambda url, timeout=15: (200, b"x")
r1 = A._cherche_sources("quelle est la capitale du Borduristan ?", c)
check(r1.statut == A.FAIT and "Paris-sur-Ruritanie" in r1.texte, "web ON : fait Wikidata rendu ET appris")

A._TRANSPORT = None
os.environ.pop("IA_WEB", None)
r2 = A._cherche_sources("quelle est la capitale du Borduristan ?", c)
check(r2.statut == A.FAIT and "Paris-sur-Ruritanie" in r2.texte and "appris de Wikidata" in r2.texte,
      "web OFF : le fait APPRIS est resservi, attribué + daté (réutilisable hors-ligne)")
r3 = A._cherche_sources("quelle est la capitale de la Syldavie ?", c)
check(r3.statut == A.HORS, "web OFF, fait jamais appris -> abstention honnête (jamais une invention)")

print("=== valide_faits_appris : %d/%d ===" % (_ok[0], _ok[0] + _ko[0]))
import sys  # noqa: E402
sys.exit(0 if _ko[0] == 0 else 1)
