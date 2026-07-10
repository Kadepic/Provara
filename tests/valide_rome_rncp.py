"""
VALIDE ROME×RNCP — le cliquet de l'axe « formation, diplômes » (part française).

CE QU'IL GARDE. `ingere_rome_rncp` publie, pour chaque métier de la carte apparié à une appellation ROME,
les certifications RNCP ACTIVES enregistrées sous son code. Les faux naissent à TROIS endroits :

  • l'EXPANSION GENRÉE : « Abatteur / Abatteuse de carrière » doit donner « abatteur de carrière », jamais
    une forme recollée de travers qui volerait le code d'un autre métier ;
  • l'ALIGNEMENT : une forme portée par deux codes, ou un métier atteignant deux codes, doit TOMBER ;
  • la VALEUR : une fiche INACTIVE listée comme formation serait un faux ; un extrait présenté comme la
    liste serait un top-N déguisé ; un négatif non daté serait un faux différé.

ANCRES NON CIRCULAIRES. La fixture est écrite ici à la main. « Boulanger / Boulangère → D1102 » est publié
par France Travail (fiche ROME D1102), connu indépendamment du code testé ; le test ne recalcule jamais
l'alignement autrement que par la fonction testée sur des données qu'elle n'a pas produites.

CONTRE-ÉPREUVES DE SABOTAGE. Cache absent -> SystemExit qui NOMME la commande de remoissonnage (une table
vide qui ne lève pas est le pire des échecs). CSV absent du zip -> SystemExit qui nomme le motif.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_rome_rncp as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) EXPANSION GENRÉE STRUCTURELLE ──────────────────────────────────────────────────────────────────
f = R._formes_rome("Abatteur / Abatteuse de carrière")
check("abatteur de carrière" in f, "masculin + queue commune reconstruit")
check("abatteuse de carrière" in f, "féminin complet conservé")
check("abatteur / abatteuse de carrière" in f, "forme entière conservée")
check("abatteur" not in f, "le masculin NU n'est jamais généré (il volerait un autre code)")

f = R._formes_rome("Boulanger / Boulangère")
check({"boulanger", "boulangère"} <= f, "doublet pur : les deux formes simples")

f = R._formes_rome("Conducteur livreur / Conductrice livreuse de marchandises")
check("conducteur livreur de marchandises" in f, "masculin multi-mots + queue")

check(R._formes_rome("Boucher / Charcutier / Traiteur") ==
      {"boucher / charcutier / traiteur"}, "trois segments -> AUCUNE expansion (forme entière seule)")
check(R._formes_rome("Écrivain / Écrivaine, militaire") ==
      {"écrivain / écrivaine, militaire"}, "virgule -> AUCUNE expansion (leçon du vol de gestes)")
check(R._formes_rome("Agent très spécialisé / Agente") ==
      {"agent très spécialisé / agente"}, "féminin plus court que le masculin -> AUCUNE expansion")
check(R._formes_rome("") == set(), "libellé vide -> aucune forme")

# ── 2) ALIGNEMENT : les gardes d'unicité ─────────────────────────────────────────────────────────────
APPELLATIONS = [
    {"libelle_appellation_long": "Boulanger / Boulangère", "libelle_appellation_court": "", "code_rome": "D1102"},
    {"libelle_appellation_long": "Allergologue", "libelle_appellation_court": "", "code_rome": "J1129"},
    # GARDE 2 : la même forme sous DEUX codes -> écartée de l'index
    {"libelle_appellation_long": "Consultant / Consultante", "libelle_appellation_court": "", "code_rome": "M1402"},
    {"libelle_appellation_long": "Consultant / Consultante", "libelle_appellation_court": "", "code_rome": "K2111"},
    # GARDE 3 : deux appellations distinctes, deux codes, atteintes par le MÊME métier doublet
    {"libelle_appellation_long": "Vigneron", "libelle_appellation_court": "", "code_rome": "A1405"},
    {"libelle_appellation_long": "Vigneronne", "libelle_appellation_court": "", "code_rome": "A9999"},
]
METIERS = ["boulanger ou boulangère", "allergologue", "consultant ou consultante",
           "vigneron ou vigneronne", "Akyn"]
apparie = R.aligne(APPELLATIONS, METIERS)
check(apparie.get("boulanger ou boulangère") == "D1102",
      "ancre : boulanger -> D1102 (fiche ROME publiée par France Travail)")
check(apparie.get("allergologue") == "J1129", "libellé épicène apparié tel quel")
check("consultant ou consultante" not in apparie, "GARDE 2 : forme multi-codes écartée -> métier non apparié")
check("vigneron ou vigneronne" not in apparie, "GARDE 3 : métier atteignant DEUX codes -> rejeté")
check("Akyn" not in apparie, "métier sans appellation ROME -> non apparié (plafond structurel, pas un faux)")

# ── 3) FICHES ACTIVES SEULEMENT ───────────────────────────────────────────────────────────────────────
STD = [
    {"Numero_Fiche": "RNCP37537", "Intitule": "Boulanger", "Nomenclature_Europe_Niveau": "NIV3", "Actif": "ACTIVE"},
    {"Numero_Fiche": "RNCP37491", "Intitule": "Boulanger", "Nomenclature_Europe_Niveau": "NIV4", "Actif": "ACTIVE"},
    {"Numero_Fiche": "RNCP181", "Intitule": "Assistant(e) en comptabilité", "Nomenclature_Europe_Niveau": "NIV4",
     "Actif": "INACTIVE"},
]
ROME_L = [
    {"Numero_Fiche": "RNCP37537", "Codes_Rome_Code": "D1102"},
    {"Numero_Fiche": "RNCP37491", "Codes_Rome_Code": "D1102"},
    {"Numero_Fiche": "RNCP181", "Codes_Rome_Code": "M1203"},       # INACTIVE : doit tomber
    {"Numero_Fiche": "RNCP99999", "Codes_Rome_Code": "M1203"},     # hors Standard : doit tomber
]
actives, par_code, ecartes = R.fiches_actives_par_code(STD, ROME_L)
check(set(actives) == {"RNCP37537", "RNCP37491"}, "seules les fiches ACTIVE passent")
check("M1203" not in par_code, "une fiche inactive ne porte AUCUN code (pas de formation fantôme)")
check(len(par_code["D1102"]) == 2, "toutes les fiches actives du code sont là")
check(ecartes == 2, "les liens écartés sont COMPTÉS (mesuré : %d)" % ecartes)

# ── 4) LA VALEUR : exhaustive, triée, datée ; le négatif est un fait clos ────────────────────────────
v = R.valeur_rncp("D1102", "Boulanger / Boulangère", par_code["D1102"], "09/07/2026")
check(v.startswith("code ROME D1102 (Boulanger / Boulangère)"),
      "la valeur commence par le code : la granularité est DITE, jamais implicite")
check("RNCP37491" in v and "RNCP37537" in v, "AUCUN top-N : toutes les fiches actives sont listées")
check(v.index("RNCP37491") < v.index("RNCP37537"), "tri déterministe par numéro de fiche")
check("(niveau 3 CEC)" in v and "(niveau 4 CEC)" in v, "le niveau CEC est traduit depuis NIVx")
check("09/07/2026" in v, "la valeur est datée par l'EXPORT (la source date, pas l'horloge)")

v0 = R.valeur_rncp("J1129", "Allergologue", [], "09/07/2026")
check("aucune certification RNCP active" in v0, "le négatif est DIT (répertoire exhaustif : absence = fait clos)")
check("09/07/2026" in v0, "le négatif est daté : un négatif non daté est un faux différé")
check(R._niveau("") == "", "niveau absent -> rien, jamais « niveau ? »")

# ── 5) SABOTAGE : les caches manquants LÈVENT en nommant le remède ───────────────────────────────────
try:
    R._csv_du_zip("/nonexistent/zip.zip", "x", ",")
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")

_tmp = tempfile.mkdtemp(prefix="verax_rncp_")
_zvide = os.path.join(_tmp, "vide.zip")
with zipfile.ZipFile(_zvide, "w") as z:
    z.writestr("autre.txt", "x")
try:
    R._csv_du_zip(_zvide, "referentiel_appellation", ",")
    check(False, "CSV absent du zip doit lever SystemExit")
except SystemExit as e:
    check("referentiel_appellation" in str(e), "SystemExit nomme le CSV manquant")

with zipfile.ZipFile(_zvide, "w") as z:
    z.writestr("export_fiches_CSV_Standard_2026_07_09.csv", "x")
check(R._date_export_rncp(_zvide) == "09/07/2026", "la date d'export est lue dans le NOM de fichier source")

print("=== valide_rome_rncp : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
