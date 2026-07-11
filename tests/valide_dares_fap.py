"""
VALIDE DARES×FAP — le cliquet de l'axe « rémunération médiane » (part FRANCE, MIX).

CE QU'IL GARDE. La chaîne métier -> ROME v4 -> FAP-2009 -> médiane a une COUTURE DE MILLÉSIME (la table de
passage Dares parle ROME v3, le store parle v4 — piège documenté : tatoueur D1208 v3 / D1244 v4) et deux
pièges de sémantique :

  • la GARDE DE STABILITÉ v3/v4 : un code n'est accepté que si ses affectations Dares FAP-2009 et FAP-2021
    portent le même intitulé de famille — un code dont la famille a changé d'intitulé est HORS ;
  • la GRANULARITÉ : la médiane est PAR FAMILLE de métiers, jamais « du métier » — la valeur doit le DIRE ;
  • l'affectation PAR QUALIFICATION ($FAP9RAQ, clés à 6 caractères) ne doit JAMAIS fuir dans la table
    directe : la qualification d'un MÉTIER n'existe pas.

ANCRES NON CIRCULAIRES. « J1501 -> V0Z60 Aides-soignants » est l'affectation publiée par la Dares dans la
table de passage ; « 1 549 €/mois » est la médiane 2017-2019 publiée dans le fichier du portail — connues
indépendamment du code testé (lues dans les fichiers Dares, jamais recalculées).

CONTRE-ÉPREUVE DE SABOTAGE. Cache absent -> SystemExit qui NOMME la commande de remoissonnage ; médiane
implausible -> ValueError (un fichier corrompu ne publie RIEN).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_dares_fap as D

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LE PARSEUR $FAP9RSQ : part directe seulement, le bloc RAQ ne fuit jamais ─────────────────────
_SAS = '''/* en-tête */
proc format ;
value  $FAP9RSQ
"J1501","J1502"                                                 =\t"V0Z60"
"K2503"                                                         =\t"T3Z61"
 Other                                                          ="ZZZZZ";
run;
proc format ;
value $FAP9RAQ
"F14011","F14012"                                                                = "B0Z20"
 Other = "ZZZZZ";
run;
'''
_tmp = tempfile.mkdtemp(prefix="verax_fap_")
_sas = os.path.join(_tmp, "passage.txt")
with open(_sas, "w", encoding="latin1") as f:
    f.write(_SAS)
_sauve = D.C_PASSAGE
D.C_PASSAGE = _sas
t = D.passage_rsq()
D.C_PASSAGE = _sauve
check(t == {"J1501": "V0Z60", "J1502": "V0Z60", "K2503": "T3Z61"},
      "le parseur lit la part DIRECTE ($FAP9RSQ) et s'arrête à Other : les clés RAQ (6 car.) ne fuient pas")

# ── 2) LA GARDE DE STABILITÉ v3/v4 ───────────────────────────────────────────────────────────────────
check(D.stable_v3_v4("Aides-soignants", ["Aides-soignants"]),
      "stabilité : intitulé identique -> stable")
check(D.stable_v3_v4("Aides-soignants", ["Aides-soignants et professions assimilées"]),
      "stabilité : inclusion d'un intitulé dans l'autre -> stable (famille élargie, même champ)")
check(D.stable_v3_v4("Agents de sécurité et de surveillance", ["agents de sécurité et de surveillance"]),
      "stabilité : la comparaison plie casse et accents (normalisation locale)")
check(not D.stable_v3_v4("Cadres de la communication", ["Producteurs de spectacles et promoteurs d'artistes"]),
      "stabilité : famille au nom DIFFÉRENT -> instable -> HORS (cas réel : agent artistique)")
check(not D.stable_v3_v4("", ["Aides-soignants"]),
      "stabilité : intitulé 2009 VIDE -> jamais stable (pas de certificat par défaut)")

# ── 3) LA VALEUR : granularité, période et champ DITS ───────────────────────────────────────────────
v = D.valeur_fap("V0Z60", "Aides-soignants", "J1501", "1549")
check(v.startswith("famille professionnelle FAP-2009 V0Z60"),
      "la valeur commence par la FAMILLE : la granularité est dite")
check("médiane PAR FAMILLE de métiers, pas par métier précis" in v,
      "la valeur dit explicitement le niveau de la médiane")
check("2017-2019" in v and "1549 €/mois" in v, "période et médiane dans la valeur (vérité datée)")
check("salariés à temps complet hors apprentis et stagiaires" in v,
      "le champ documenté de la série est dit (une médiane sans champ serait un faux différé)")
check("stable entre FAP-2009 et FAP-2021" in v,
      "la valeur dit que la couture v3/v4 a été certifiée pour ce code")

# ── 4) MÉDIANES : plausibilité et niveaux ────────────────────────────────────────────────────────────
_csv = os.path.join(_tmp, "salaires.csv")
with open(_csv, "w", encoding="utf-8") as f:
    f.write('"Fap3,""Annee"",""Salaire_median"""\n'
            '"V0Z60,""2017-2019"",1549"\n'
            '"V0Z,""2017-2019"",1600"\n'          # niveau 87 : hors granularité fine, ignoré
            '"T3Z61,""2003-2005"",1150"\n')       # autre période : ignorée
_sauve_s = D.C_SALAIRES
D.C_SALAIRES = _csv
m = D.medianes_fap()
check(m == {"V0Z60": "1549"},
      "medianes_fap : période épinglée, niveaux 22/87 ignorés, déquotage du fichier portail")
with open(_csv, "a", encoding="utf-8") as f:
    f.write('"X9X99,""2017-2019"",42"\n')          # 42 €/mois : implausible
try:
    D.medianes_fap()
    check(False, "une médiane implausible doit faire échouer TOUTE la publication")
except ValueError as e:
    check("implausible" in str(e), "médiane hors 800..15000 €/mois -> ValueError (fichier suspect)")
D.C_SALAIRES = _sauve_s

# ── 5) SABOTAGE : cache absent -> SystemExit nommant le remède ──────────────────────────────────────
D.C_PASSAGE = "/nonexistent/passage.txt"
try:
    D.passage_rsq()
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")
finally:
    D.C_PASSAGE = _sauve

print("=== valide_dares_fap : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
