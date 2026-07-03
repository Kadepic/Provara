"""
VALIDATION T8 — HISTOIRE, DATES & POLITIQUE (couloir d'ingestion). FAUX=0 INVIOLABLE.

Charge UNIQUEMENT les relations T8 présentes dans un Lecteur frais (léger) et verrouille les invariants du
PATRON DATE/ANNÉE + des relations politiques ouvertes :

  1. PLAGE/FORME : toute valeur d'une relation DATE est une ANNÉE (entier signé, regex ^-?\\d{1,4}$) DANS la
                   plage historique de sa relation -> aucune date future / saisie aberrante n'a fui.
  2. INTÉGRITÉ   : relation ouverte (predecesseur_etat) = libellé ≥2 caractères, non vide.
  3. ANCRES      : années vérifiées À LA MAIN, indépendamment du code (ONU 1945, URSS dissoute 1991…) -> ancrage
                   NON circulaire.
  4. SOUNDNESS   : adverse — entité multi-valeur (HORS via fonctionnel), entité absente, relation absente ->
                   TOUJOURS HORS (None). Jamais un faux, jamais une devinette.

EXIT 0 = tous les check passent. Lancer SEUL (1 chargement léger) en dev ; enregistrer dans _nonreg.py pour le gate.
"""
from __future__ import annotations

import json
import os
import re

from garde_ressources import borne

borne(max_go=4.0, max_cpu_s=900)   # OPTIM amorce-seule : ne charge QUE les relations T8 (~2,1 M faits) dans un Lecteur
# frais, plus le full-load global des 33,5 M faits ; 4 Go large (pic ~2 Go).

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L
from lecteur import HORS, VERIFIE

DOSSIER = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")

# Plages historiques par relation DATE (DOIVENT refléter ingere_t8.DATES). ymax = 2026 (présent).
PLAGES = {
    "annee_fondation_pays":         (-4000, 2026),
    "annee_creation_organisation":  (-1000, 2026),
    "annee_dissolution":            (-1000, 2026),
    "date_evenement":               (-4000, 2026),
    "annee_fondation_parti_politique": (1500, 2026),   # via pont REST (CirrusSearch+wbgetentities, SPARQL down)
    "annee_fondation_organisation_internationale": (1500, 2026),   # pont REST
    "annee_debut_guerre":              (-4000, 2026),   # pont REST (P580 start time)
    "annee_signature_traite":          (-4000, 2026),   # pont REST (P585 date de signature)
    "annee_fondation_etat_historique": (-4000, 2026),   # pont REST (P571 ; états antiques inclus, ex. Rome -753)
    "annee_debut_dynastie":            (-4000, 2026),   # pont REST (P571 sur Q164950 dynastie)
    "annee_fin_guerre":                (-4000, 2026),   # pont REST (P582 sur Q198)
    "annee_debut_bataille":            (-4000, 2026),   # P580 début sur Q178561 (bataille)
    "annee_fin_bataille":              (-4000, 2026),   # P582 fin sur Q178561 (bataille)
    "annee_entree_vigueur_traite":     (-1000, 2026),   # P7588 entrée en vigueur sur Q131569 (traité)
    "annee_debut_revolution":          (-1000, 2026),   # P580 début sur Q10931 (révolution)
    "annee_fin_revolution":            (-1000, 2026),   # P582 fin sur Q10931 (révolution)
    "annee_adoption_constitution":     (-1000, 2026),   # P571 inception sur Q7755 (constitution)
    "annee_debut_siege":               (-4000, 2026),   # P580 début sur Q188055 siège (hors Q178561 bataille)
    "annee_fin_siege":                 (-4000, 2026),   # P582 fin sur Q188055 siège (hors Q178561)
    "annee_debut_operation_militaire": (-4000, 2026),   # P580 début sur Q645883 (hors bataille/siège)
    "annee_fin_operation_militaire":   (-4000, 2026),   # P582 fin sur Q645883 (hors bataille/siège)
    "annee_fin_dynastie":              (-4000, 2026),   # pont REST (P576 sur Q164950)
    "annee_fondation_organisation_militaire": (1000, 2026),   # pont REST (P571 sur Q17149090 organisation armée)
    "annee_debut_regne":               (-4000, 2026),   # QUALIF (P39 monarque Q12097 + qualificatif P580 début)
    "annee_fin_regne":                 (-4000, 2026),   # QUALIF (P39 monarque Q12097 + qualificatif P582 fin)
    "annee_fin_mandat_chef_etat":            (-4000, 2026),   # QUALIF (P39 Q48352 + P582 ; mandat terminé = borné)
    "annee_fin_mandat_chef_gouvernement":    (-4000, 2026),   # QUALIF (P39 Q2285706 + P582 ; mandat terminé)
    "annee_debut_mandat_chef_etat":          (-4000, 2026),   # QUALIF (P39 Q48352 + P580 ; prise de fonction figée)
    "annee_debut_mandat_chef_gouvernement":  (-4000, 2026),   # QUALIF (P39 Q2285706 + P580 ; prise de fonction)
    "annee_fin_mandat_ministre":             (-4000, 2026),   # QUALIF (P39 Q83307 hors PM + P582 ; mono-portefeuille)
    "annee_debut_mandat_ministre":           (-4000, 2026),   # QUALIF (P39 Q83307 hors PM + P580)
    "annee_fin_mandat_ambassadeur":          (-4000, 2026),   # QUALIF (P39 Q121998 + P582 ; mono-poste survit)
    "annee_debut_mandat_ambassadeur":        (-4000, 2026),   # QUALIF (P39 Q121998 + P580)
    "annee_fin_mandat_gouverneur":           (-4000, 2026),   # QUALIF (P39 Q132050 + P582)
    "annee_debut_mandat_gouverneur":         (-4000, 2026),   # QUALIF (P39 Q132050 + P580)
    "annee_fin_mandat_juge":                 (-4000, 2026),   # QUALIF (P39 Q16533 + P582 ; haute fonction judiciaire)
    "annee_debut_mandat_juge":               (-4000, 2026),   # QUALIF (P39 Q16533 + P580)
}
OUVERTES = ["predecesseur_etat", "pays_parti_politique",
            "capitale_etat_historique", "forme_de_gouvernement_etat_historique",
            "monnaie_etat_historique", "langue_officielle_etat_historique",
            "religion_etat_historique", "position_politique_parti",
            "siege_organisation_internationale",
            "conflit_parent_bataille", "lieu_signature_traite", "lieu_bataille",
            "predecesseur_etat_historique", "successeur_etat_historique",
            "pays_organisation_militaire", "metropole_colonie", "pays_constitution",
            "pays_coup_etat", "pays_assassinat",
            "pays_guerre_civile", "pays_genocide",
            "conflit_parent_siege", "conflit_parent_operation_militaire",
            "predecesseur_personne", "successeur_personne",
            "circonscription_electorale_personne",
            "groupe_parlementaire_personne", "diocese_personne",
            "nomme_par_personne", "election_acces_personne",
            "maison_noble_personne", "parti_personne",
            "vainqueur_election", "fonction_brigue_election",
            "pays_election", "pays_referendum",
            "pays_revolution", "pays_massacre", "pays_manifestation", "pays_siege",
            "pays_attentat", "pays_greve",
            "parti_predecesseur", "parti_successeur",
            "fonction_predecesseur", "fonction_successeur",
            "traite_predecesseur", "traite_successeur",
            "organisation_internationale_predecesseur", "organisation_internationale_successeur",
            "pays_ordre_honorifique", "lieu_guerre",
            "lieu_siege", "lieu_attentat", "lieu_massacre",
            "lieu_manifestation", "lieu_coup_etat", "lieu_assassinat",
            "lieu_guerre_civile", "lieu_genocide", "lieu_revolution",
            "lieu_operation_militaire", "pays_operation_militaire",
            "pays_bataille", "lieu_greve",
            "juridiction_fonction", "pays_operateur_fonction",
            "autorite_nomination_fonction",
            "fonction_chef_etat_pays", "fonction_chef_gouvernement_pays",
            "pays_parlement", "pays_banque_centrale", "pays_agence_renseignement"]   # entité -> entité
RELATIONS = list(PLAGES) + OUVERTES

_AN = re.compile(r"^-?\d{1,4}$")

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


def _entete(chemin):
    with open(chemin, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if brut:
                t = json.loads(brut)
                return t["_categorie"], t["_source"]
    raise ValueError(f"{chemin} : en-tête manquant")


# --- Chargement léger : seules les relations T8 PRÉSENTES dans un Lecteur frais. ---
lec = L.Lecteur()
presentes = []
for rel in RELATIONS:
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        continue
    cat, src = _entete(chemin)
    lec.charge_jsonl(rel, chemin, cat, src)
    presentes.append(rel)
check(f"au moins une relation T8 chargée (présentes : {presentes})", len(presentes) > 0)

# 1) FORME ANNÉE + PLAGE : toute valeur DATE est un entier signé dans [ymin, ymax].
for rel, (lo, hi) in PLAGES.items():
    if rel not in presentes:
        continue
    t = lec.tables.get(rel, {})
    n = len(t)
    mauvais = None
    for cle, fait in t.items():
        v = fait.valeur
        if not (isinstance(v, str) and _AN.match(v)):
            mauvais = (cle, v, "non-année")
            break
        if not (lo <= int(v) <= hi):
            mauvais = (cle, v, "hors-plage")
            break
    check(f"{rel} : {n} faits, tous année ∈ [{lo},{hi}] [contre-ex: {mauvais}]", n > 0 and mauvais is None)

# 2) INTÉGRITÉ relations ouvertes : valeur = libellé ≥2 caractères non vide.
for rel in OUVERTES:
    if rel not in presentes:
        continue
    t = lec.tables.get(rel, {})
    n = len(t)
    mauvais = next((c for c, f in t.items() if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 2)), None)
    check(f"{rel} : {n} faits, libellés ≥2 car. non vides [contre-ex: {mauvais}]", n > 0 and mauvais is None)

# 3) ANCRES — vérité-terrain indépendante (correspondance exacte d'année / d'entité).
ANCRES_DATE = [
    # (relation, entité, année attendue)
    ("annee_fondation_pays", "Australie", "1901"),       # fédération australienne
    ("annee_fondation_pays", "Brésil", "1822"),          # indépendance
    ("annee_dissolution", "Union soviétique", "1991"),   # dissolution de l'URSS
    ("annee_dissolution", "Tchécoslovaquie", "1992"),    # partition
    ("annee_dissolution", "Empire ottoman", "1922"),     # abolition du sultanat
    ("annee_dissolution", "Yougoslavie", "1992"),
    ("date_evenement", "bataille d'Austerlitz", "1805"),
    ("date_evenement", "bataille de Waterloo", "1815"),
    ("annee_fondation_parti_politique", "Parti communiste chinois", "1921"),
    ("annee_fondation_parti_politique", "Parti social-démocrate d'Allemagne", "1863"),
    ("annee_fondation_parti_politique", "Union chrétienne-démocrate d'Allemagne", "1945"),
    ("annee_fondation_organisation_internationale", "Organisation des Nations unies", "1945"),
    ("annee_fondation_organisation_internationale", "Organisation mondiale de la santé", "1948"),
    ("annee_debut_guerre", "guerre de Corée", "1950"),
    ("annee_signature_traite", "traité sur l'Antarctique", "1959"),
    ("annee_fondation_etat_historique", "Tchécoslovaquie", "1918"),
    ("annee_fondation_etat_historique", "Empire russe", "1721"),
    ("annee_debut_dynastie", "période Joseon", "1392"),
    ("annee_debut_dynastie", "Dynastie saoudienne", "1744"),
    ("annee_debut_dynastie", "Goryeo", "918"),
    ("annee_fin_guerre", "guerre de Corée", "1953"),
    ("annee_fin_guerre", "guerres napoléoniennes", "1815"),
    ("annee_debut_bataille", "bataille de Stalingrad", "1942"),
    ("annee_debut_bataille", "bataille de Verdun", "1916"),
    ("annee_debut_bataille", "bataille de Gettysburg", "1863"),
    ("annee_debut_bataille", "première bataille de la Marne", "1914"),
    ("annee_fin_bataille", "bataille de Stalingrad", "1943"),
    ("annee_fin_bataille", "bataille de la Somme", "1916"),
    ("annee_fin_bataille", "bataille de Gettysburg", "1863"),
    ("annee_entree_vigueur_traite", "traité de Lisbonne", "2009"),
    ("annee_entree_vigueur_traite", "traité de Nice", "2003"),
    ("annee_entree_vigueur_traite", "traité instituant la Communauté économique européenne", "1958"),
    ("annee_debut_revolution", "Révolution française", "1789"),
    ("annee_debut_revolution", "révolution d'Octobre", "1917"),
    ("annee_fin_revolution", "Révolution française", "1799"),
    ("annee_adoption_constitution", "constitution des États-Unis", "1787"),
    ("annee_adoption_constitution", "Constitution de la Croatie", "1990"),
    ("annee_debut_siege", "siège de Léningrad", "1941"),
    ("annee_debut_siege", "siège de Boston", "1775"),
    ("annee_fin_siege", "siège de Léningrad", "1944"),
    ("annee_fin_siege", "siège de Boston", "1776"),
    ("annee_debut_operation_militaire", "opération Barbarossa", "1941"),
    ("annee_debut_operation_militaire", "opération Market Garden", "1944"),
    ("annee_debut_operation_militaire", "opération Torch", "1942"),
    ("annee_fin_operation_militaire", "opération Husky", "1943"),
    ("annee_fin_operation_militaire", "opération Market Garden", "1944"),
    ("annee_fin_dynastie", "période Joseon", "1897"),
    ("annee_fin_dynastie", "dynastie Pahlavi", "1979"),
    ("annee_fondation_organisation_militaire", "Al-Qaïda", "1988"),
    ("annee_fondation_organisation_militaire", "Armia Krajowa", "1942"),
    # annee_creation_organisation (P571 sur Q43229, classe générique « organisation ») — vérité-terrain
    # indépendante, entités survivant au fonctionnel (mono-valeur) et vérifiées dans le .jsonl.
    ("annee_creation_organisation", "Organisation des Nations unies", "1945"),
    ("annee_creation_organisation", "Comité international de la Croix-Rouge", "1863"),
    ("annee_creation_organisation", "Organisation mondiale de la santé", "1948"),
    ("annee_creation_organisation", "Union européenne", "1993"),
    # Règnes de souverains (qualificatifs P39+P580/P582) — ancres mono-royaume survivant au fonctionnel,
    # vérifiées dans le .jsonl (les multi-royaumes à années distinctes, ex. Louis XIV, sont HORS = correct).
    ("annee_debut_regne", "Frédéric X de Danemark", "2024"),
    ("annee_debut_regne", "Marguerite II de Danemark", "1972"),
    ("annee_debut_regne", "Alaric Ier", "395"),
    ("annee_fin_regne", "Henri IV de France", "1610"),
    ("annee_fin_regne", "Charlemagne", "814"),
    ("annee_fin_regne", "Frédéric IX de Danemark", "1972"),
    # Fin de mandat (P39 fonction + qualificatif P582) — mandats terminés, mono-mandat, vérifiés dans le .jsonl.
    ("annee_fin_mandat_chef_etat", "François Hollande", "2017"),
    ("annee_fin_mandat_chef_etat", "Jacques Chirac", "2007"),
    ("annee_fin_mandat_chef_etat", "Woodrow Wilson", "1921"),
    ("annee_fin_mandat_chef_gouvernement", "Tony Blair", "2007"),
    ("annee_fin_mandat_chef_gouvernement", "Gordon Brown", "2010"),
    ("annee_fin_mandat_chef_gouvernement", "Margaret Thatcher", "1990"),
    # Début de mandat (P39 fonction + qualificatif P580 = prise de fonction), mono-mandat, vérifiés dans le .jsonl.
    ("annee_debut_mandat_chef_etat", "François Hollande", "2012"),
    ("annee_debut_mandat_chef_etat", "Jacques Chirac", "1995"),
    ("annee_debut_mandat_chef_etat", "Abraham Lincoln", "1861"),
    ("annee_debut_mandat_chef_gouvernement", "Tony Blair", "1997"),
    ("annee_debut_mandat_chef_gouvernement", "Gordon Brown", "2007"),
    ("annee_debut_mandat_chef_gouvernement", "Margaret Thatcher", "1979"),
    # Ministres mono-portefeuille (P39 Q83307 hors chef de gouvernement + qualif) — vérifiés dans le .jsonl.
    ("annee_fin_mandat_ministre", "Hubert Védrine", "2002"),
    ("annee_fin_mandat_ministre", "Henry Kissinger", "1977"),
    ("annee_fin_mandat_ministre", "Condoleezza Rice", "2009"),
    ("annee_debut_mandat_ministre", "Hubert Védrine", "1997"),
    ("annee_debut_mandat_ministre", "Henry Kissinger", "1973"),
    ("annee_debut_mandat_ministre", "Colin Powell", "2001"),
    # Ambassadeurs / gouverneurs (mono-poste) — vérifiés dans le .jsonl (gouverneurs de Hong Kong = série propre).
    ("annee_fin_mandat_ambassadeur", "Caroline Kennedy", "2017"),
    ("annee_fin_mandat_ambassadeur", "Pamela Harriman", "1997"),
    ("annee_debut_mandat_ambassadeur", "Pamela Harriman", "1993"),
    ("annee_fin_mandat_gouverneur", "Chris Patten", "1997"),
    ("annee_fin_mandat_gouverneur", "David Wilson", "1992"),
    ("annee_fin_mandat_gouverneur", "Murray MacLehose", "1982"),
    ("annee_debut_mandat_gouverneur", "Chris Patten", "1992"),
    ("annee_debut_mandat_gouverneur", "Murray MacLehose", "1971"),
    ("annee_debut_mandat_gouverneur", "David Wilson", "1987"),
    # Juges (haute fonction judiciaire, mono-charge) — vérifiés dans le .jsonl (Cour suprême des États-Unis).
    ("annee_fin_mandat_juge", "Sandra Day O'Connor", "2006"),
    ("annee_fin_mandat_juge", "Byron White", "1993"),
    ("annee_debut_mandat_juge", "Sandra Day O'Connor", "1981"),
    ("annee_debut_mandat_juge", "David Souter", "1990"),
]
for rel, ent, vrai in ANCRES_DATE:
    if rel not in presentes:
        continue
    st, f = lec.repond(rel, ent)
    check(f"ANCRE {rel}({ent}) = {vrai} [{st}, {f.valeur if f else None}]",
          st == VERIFIE and f is not None and f.valeur == vrai)

ANCRES_OUV = [
    # (relation, entité, valeur attendue — sous-chaîne, libellé exact Wikidata FR)
    ("predecesseur_etat", "Inde", "Raj britannique"),
    ("predecesseur_etat", "Italie", "royaume d'Italie"),
    ("pays_parti_politique", "Parti communiste français", "France"),
    ("pays_parti_politique", "Congrès national indien", "Inde"),
    ("pays_parti_politique", "Parti libéral du Canada", "Canada"),
    ("pays_parti_politique", "Congrès national africain", "Afrique du Sud"),
    ("capitale_etat_historique", "Union soviétique", "Moscou"),
    ("capitale_etat_historique", "Tchécoslovaquie", "Prague"),
    ("capitale_etat_historique", "Rome antique", "Rome"),
    ("forme_de_gouvernement_etat_historique", "dynastie Qing", "monarchie absolue"),
    ("forme_de_gouvernement_etat_historique", "empire d'Autriche", "monarchie absolue"),
    ("monnaie_etat_historique", "Union soviétique", "rouble soviétique"),
    ("monnaie_etat_historique", "Tchécoslovaquie", "couronne tchécoslovaque"),
    ("langue_officielle_etat_historique", "Raj britannique", "anglais"),
    ("langue_officielle_etat_historique", "Empire ottoman", "turc ottoman"),
    ("religion_etat_historique", "Empire ottoman", "sunnisme"),
    ("religion_etat_historique", "empire d'Autriche", "catholicisme"),
    ("position_politique_parti", "La France insoumise", "gauche radicale"),
    ("position_politique_parti", "Rassemblement national", "extrême droite"),
    ("position_politique_parti", "Parti social-démocrate d'Allemagne", "centre gauche"),
    ("siege_organisation_internationale", "Organisation mondiale de la santé", "Genève"),
    ("siege_organisation_internationale", "Organisation des Nations unies", "New York"),
    ("conflit_parent_bataille", "bataille de Stalingrad", "front de l'Est"),
    ("conflit_parent_bataille", "bataille de Gettysburg", "guerre de Sécession"),
    ("vainqueur_election", "élection présidentielle française de 2017", "Emmanuel Macron"),
    ("vainqueur_election", "élection présidentielle française de 2012", "François Hollande"),
    ("vainqueur_election", "élection présidentielle française de 1981", "François Mitterrand"),
    ("vainqueur_election", "élection présidentielle russe de 1996", "Boris Eltsine"),
    ("fonction_brigue_election", "élection présidentielle française de 2017", "président de la République française"),
    ("fonction_brigue_election", "élection présidentielle française de 2022", "président de la République française"),
    ("fonction_brigue_election", "élection présidentielle tunisienne de 2019", "président de la République tunisienne"),
    ("fonction_brigue_election", "élections législatives togolaises de 2024", "député à l'Assemblée nationale du Togo"),
    ("pays_election", "élection présidentielle française de 2017", "France"),
    ("pays_election", "élection présidentielle américaine de 2020", "États-Unis"),
    ("pays_election", "élections générales gabonaises de 2023", "Gabon"),
    ("pays_election", "élection présidentielle brésilienne de 2018", "Brésil"),
    ("pays_referendum", "référendum sur l'appartenance du Royaume-Uni à l'Union européenne", "Royaume-Uni"),
    ("pays_referendum", "Référendum constitutionnel gabonais de 2024", "Gabon"),
    ("pays_referendum", "Référendum gambien de 1970", "Gambie"),
    ("pays_revolution", "Révolution française", "France"),
    ("pays_revolution", "révolution d'Octobre", "République russe"),
    ("pays_massacre", "massacre d'Oradour-sur-Glane", "France"),
    ("pays_massacre", "massacre de Nankin", "république de Chine"),
    ("pays_manifestation", "Mai 68", "France"),
    ("pays_manifestation", "Marche sur Washington pour l'emploi et la liberté", "États-Unis"),
    ("pays_siege", "siège de Léningrad", "Union soviétique"),
    ("pays_attentat", "attentats du 11 septembre 2001", "États-Unis"),
    ("pays_attentat", "attentat contre Charlie Hebdo", "France"),
    ("pays_greve", "grève des mineurs à Marikana", "Afrique du Sud"),
    ("pays_greve", "grève des mineurs au Colorado en 1927 et 1928", "États-Unis"),
    ("parti_predecesseur", "Rassemblement national", "Front national"),
    ("parti_successeur", "Front national", "Rassemblement national"),
    ("parti_successeur", "Rassemblement pour la République", "Union pour un mouvement populaire"),
    ("fonction_successeur", "évêque de Johannesbourg", "archevêque de Johannesbourg"),
    ("fonction_successeur", "ambassadeur de l'archiduché d'Autriche", "ambassadeur de l'empire d'Autriche"),
    ("fonction_predecesseur", "ambassadeur de l'empire austro-hongrois", "ambassadeur de l'empire d'Autriche"),
    ("fonction_predecesseur", "archevêque de Johannesbourg", "évêque de Johannesbourg"),
    ("traite_successeur", "traité instituant la Communauté économique européenne", "traité sur le fonctionnement de l'Union européenne"),
    ("traite_successeur", "Accord de libre-échange nord-américain", "accord Canada–États-Unis–Mexique"),
    ("traite_predecesseur", "accord Canada–États-Unis–Mexique", "Accord de libre-échange nord-américain"),
    ("traite_predecesseur", "Accord de libre-échange nord-américain", "Accord de libre-échange canado-américain"),
    ("organisation_internationale_successeur", "Alliance des États du Sahel", "Confédération des États du Sahel"),
    ("organisation_internationale_successeur", "Europe de la liberté et de la démocratie", "Europe de la liberté et de la démocratie directe"),
    ("organisation_internationale_predecesseur", "Confédération des États du Sahel", "Alliance des États du Sahel"),
    ("pays_ordre_honorifique", "Medal of Honor", "États-Unis"),
    ("pays_ordre_honorifique", "ordre national de la Légion d'honneur", "France"),
    ("lieu_guerre", "première guerre de Mysore", "Mysore"),
    ("lieu_guerre", "guerre d'Espagne", "péninsule Ibérique"),
    ("lieu_siege", "siège de Bagdad", "Bagdad"),
    ("lieu_siege", "siège de Léningrad", "Saint-Pétersbourg"),
    ("lieu_attentat", "attentat contre Charlie Hebdo", "10 rue Nicolas-Appert"),
    ("lieu_attentat", "attentat d'Oklahoma City", "bâtiment fédéral Alfred P. Murrah"),
    ("lieu_massacre", "massacre d'Oradour-sur-Glane", "Oradour-sur-Glane"),
    ("lieu_manifestation", "Mai 68", "France"),
    ("lieu_coup_etat", "coup d'État de 1991 au Lesotho", "Maseru"),
    ("lieu_coup_etat", "coup d'État de 1973 au Chili", "Chili"),
    ("lieu_assassinat", "assassinat d'Abraham Lincoln", "théâtre Ford"),
    ("lieu_guerre_civile", "guerre civile rwandaise", "Rwanda"),
    ("lieu_genocide", "Holodomor", "république socialiste soviétique d'Ukraine"),
    ("lieu_revolution", "Révolution française", "France"),
    ("lieu_revolution", "révolution russe", "Empire russe"),
    ("lieu_operation_militaire", "opération Serval", "Mali"),
    ("lieu_operation_militaire", "opération Mousquetaire", "canal de Suez"),
    ("pays_operation_militaire", "intervention militaire de 2011 en Libye", "Libye"),
    ("pays_operation_militaire", "intervention militaire en Gambie", "Gambie"),
    ("pays_bataille", "bataille de Gettysburg", "États-Unis"),
    ("pays_bataille", "bataille de Stalingrad", "Russie"),
    ("lieu_greve", "grève des mineurs à Marikana", "Marikana"),
    ("lieu_greve", "Grève des mineurs britanniques de 1984-1985", "Royaume-Uni"),
    ("juridiction_fonction", "maire de Paris", "Paris"),
    ("juridiction_fonction", "Premier ministre du Royaume-Uni", "Royaume-Uni"),
    ("juridiction_fonction", "Conseiller scientifique du président des États-Unis", "États-Unis"),
    ("pays_operateur_fonction", "ambassadeur de France aux États-Unis", "France"),
    ("pays_operateur_fonction", "ambassadeur de Gambie au Royaume-Uni", "Gambie"),
    ("autorite_nomination_fonction", "Premier ministre du Tadjikistan", "président du Tadjikistan"),
    ("autorite_nomination_fonction", "président du Conseil des ministres de Pologne", "président de la République de Pologne"),
    ("fonction_chef_etat_pays", "France", "président de la République française"),
    ("fonction_chef_etat_pays", "Japon", "empereur du Japon"),
    ("fonction_chef_gouvernement_pays", "France", "Premier ministre français"),
    ("fonction_chef_gouvernement_pays", "Allemagne", "chancelier fédéral"),
    ("pays_parlement", "Congrès des États-Unis", "États-Unis"),
    ("pays_parlement", "Diète du Japon", "Japon"),
    ("pays_parlement", "Parlement européen", "Union européenne"),
    ("pays_banque_centrale", "Banque de France", "France"),
    ("pays_banque_centrale", "Banque centrale européenne", "Allemagne"),
    ("pays_agence_renseignement", "Central Intelligence Agency", "États-Unis"),
    ("pays_agence_renseignement", "Mossad", "Israël"),
    ("lieu_signature_traite", "Convention de Bonn", "Bonn"),
    ("lieu_signature_traite", "traité de Shimoda", "Shimoda"),
    ("lieu_bataille", "bataille de Stalingrad", "Volgograd"),
    ("lieu_bataille", "bataille de Verdun", "Verdun"),
    ("predecesseur_etat_historique", "Autriche-Hongrie", "empire d'Autriche"),
    ("predecesseur_etat_historique", "Haut-Empire romain", "République romaine tardive"),
    ("successeur_etat_historique", "république de Chine", "République populaire de Chine"),
    ("successeur_etat_historique", "dynastie Yuan en Chine", "dynastie Ming"),
    ("pays_organisation_militaire", "Hezbollah", "Liban"),
    ("pays_organisation_militaire", "Armia Krajowa", "Pologne"),
    ("metropole_colonie", "Raj britannique", "Empire britannique"),
    ("metropole_colonie", "Taïwan sous domination japonaise", "empire du Japon"),
    ("pays_constitution", "constitution de l'Inde", "Inde"),
    ("pays_constitution", "Constitution du Japon", "Japon"),
    ("pays_coup_etat", "Euromaïdan", "Ukraine"),
    ("pays_coup_etat", "révolution des Œillets", "Portugal"),
    ("pays_assassinat", "assassinat de John F. Kennedy", "États-Unis"),
    ("pays_assassinat", "assassinat d'Abraham Lincoln", "États-Unis"),
    ("pays_guerre_civile", "guerre d'Espagne", "Espagne"),
    ("pays_guerre_civile", "guerre civile syrienne", "Syrie"),
    ("pays_genocide", "génocide arménien", "Empire ottoman"),
    ("pays_genocide", "Holodomor", "Union soviétique"),
    ("conflit_parent_siege", "siège de Léningrad", "front de l'Est"),
    ("conflit_parent_siege", "siège de Sébastopol", "guerre de Crimée"),
    ("conflit_parent_operation_militaire", "opération Deadlight", "Seconde Guerre mondiale"),
    ("conflit_parent_operation_militaire", "opération Tempête", "Seconde Guerre mondiale"),
    # Succession de dirigeants (P39 + qualificatif ENTITÉ pq:P1365/P1366) — personnes à succession UNIQUE
    # (mono-fonction) survivant au fonctionnel, vérifiées à la main (généalogie monarchique notoire).
    ("predecesseur_personne", "Élisabeth II", "George VI"),
    ("predecesseur_personne", "Édouard VII", "Victoria"),
    ("predecesseur_personne", "George VI", "Édouard VIII"),
    ("predecesseur_personne", "Akihito", "Hirohito"),
    ("predecesseur_personne", "Albert II de Belgique", "Baudouin Ier de Belgique"),
    ("successeur_personne", "Élisabeth II", "Charles III"),
    ("successeur_personne", "Victoria", "Édouard VII"),
    ("successeur_personne", "Édouard VII", "George V"),
    ("successeur_personne", "Charles III", "William de Galles"),
    # Circonscription électorale (P39 + qualificatif ENTITÉ pq:P768) — élus mono-circonscription survivant au
    # fonctionnel (les multi-circonscriptions, ex. Churchill/Mélenchon/Pelosi, sont HORS), vérité-terrain notoire.
    ("circonscription_electorale_personne", "Jean Jaurès", "Tarn"),
    ("circonscription_electorale_personne", "Georges Clemenceau", "18e arrondissement de Paris"),
    ("circonscription_electorale_personne", "Pierre Mendès France", "Isère"),
    ("circonscription_electorale_personne", "Abraham Lincoln", "Illinois"),
    ("circonscription_electorale_personne", "Alexandria Ocasio-Cortez", "New York"),
    ("circonscription_electorale_personne", "Bernie Sanders", "Vermont"),
    # Groupe parlementaire (P39 + qualificatif ENTITÉ pq:P4100) — élus mono-groupe (les transfuges → HORS), vérifiés.
    ("groupe_parlementaire_personne", "Helmut Kohl", "CDU/CSU"),
    ("groupe_parlementaire_personne", "Wolfgang Schäuble", "CDU/CSU"),
    ("groupe_parlementaire_personne", "Joschka Fischer", "Les Verts"),
    ("groupe_parlementaire_personne", "Hans-Dietrich Genscher", "FDP"),
    ("groupe_parlementaire_personne", "Jean-Marie Le Pen", "non-inscrits"),
    # Diocèse d'un ecclésiastique (P39 + qualificatif ENTITÉ pq:P708) — évêques mono-siège, vérité-terrain notoire.
    ("diocese_personne", "Ambroise de Milan", "Milan"),
    ("diocese_personne", "Thomas Becket", "Cantorbéry"),
    ("diocese_personne", "Irénée de Lyon", "Lyon"),
    ("diocese_personne", "Nicolas de Myre", "Myre"),
    ("diocese_personne", "Stanislas de Szczepanów", "Cracovie"),
    # Nommé par (P39 + qualificatif ENTITÉ pq:P748, appariteur personne) — titulaires nommés par une seule
    # personne distincte (multi-nominateur → HORS), vérité-terrain notoire (administrations Biden/Trudeau).
    ("nomme_par_personne", "Antony Blinken", "Joe Biden"),
    ("nomme_par_personne", "Kate Bedingfield", "Joe Biden"),
    ("nomme_par_personne", "Bud Olson", "Pierre Elliott Trudeau"),
    # Élection d'accès (P39 + qualificatif ENTITÉ pq:P2715) — élus mono-élection (réélus → HORS), chefs d'État/
    # figures notoires vérifiés indépendamment (élection présidentielle/européenne/régionale datée et publique).
    ("election_acces_personne", "Daniel Noboa", "équatorienne de 2023"),
    ("election_acces_personne", "Béji Caïd Essebsi", "tunisienne de 2014"),
    ("election_acces_personne", "Carola Rackete", "européennes de 2024"),
    ("election_acces_personne", "Marine Tondelier", "Hauts-de-France"),
    ("election_acces_personne", "Claude Chirac", "Corrèze"),
    ("election_acces_personne", "Emmanuel Macron", "française de 2017"),   # son élection d'ACCÈS (1ʳᵉ) = 2017
    # Maison/famille noble (wdt:P53) — appartenance dynastique unique (double maison → HORS), vérité-terrain notoire.
    ("maison_noble_personne", "Marie-Antoinette d'Autriche", "Habsbourg"),
    ("maison_noble_personne", "Élisabeth II", "Windsor"),
    ("maison_noble_personne", "Napoléon Ier", "Bonaparte"),
    ("maison_noble_personne", "Henri VIII", "Tudor"),
    ("maison_noble_personne", "Catherine de Médicis", "Médicis"),
    # Parti politique d'une personne (wdt:P102) — mono-parti (transfuges → HORS), affiliation notoire vérifiée.
    ("parti_personne", "Joe Biden", "démocrate"),
    ("parti_personne", "Margaret Thatcher", "conservateur"),
    ("parti_personne", "Helmut Kohl", "chrétienne-démocrate"),
    ("parti_personne", "Olaf Scholz", "social-démocrate"),
    ("parti_personne", "Tony Blair", "travailliste"),
    ("parti_personne", "Lionel Jospin", "socialiste"),
]
for rel, ent, attendu in ANCRES_OUV:
    if rel not in presentes:
        continue
    st, f = lec.repond(rel, ent)
    check(f"ANCRE {rel}({ent}) ~ {attendu!r} [{st}, {f.valeur if f else None}]",
          st == VERIFIE and f is not None and attendu.lower() in f.valeur.lower())

# 4) SOUNDNESS ADVERSE — entité absente, relation absente, mauvaise relation -> TOUJOURS HORS.
ADVERSE = [
    ("annee_fondation_pays", "pays-qui-nexiste-pas-zzz"),
    ("annee_fondation_pays", "Everest"),               # bonne base, mauvaise relation (Everest n'est pas un pays)
    ("relation_inexistante_t8", "France"),
    ("predecesseur_etat", "entite-inconnue-zzz"),
    ("predecesseur_personne", "personne-inconnue-zzz"),
    ("successeur_personne", "Emmanuel Macron"),   # multi-fonction -> HORS (fonctionnel), jamais une devinette
    ("circonscription_electorale_personne", "Winston Churchill"),  # multi-circonscription -> HORS (fonctionnel)
    ("circonscription_electorale_personne", "ville-imaginaire-zzz"),
    ("groupe_parlementaire_personne", "groupe-fantome-zzz"),
    ("diocese_personne", "eveque-inexistant-zzz"),
    ("nomme_par_personne", "personne-jamais-nommee-zzz"),
    ("election_acces_personne", "candidat-fantome-zzz"),
    ("maison_noble_personne", "roturier-sans-maison-zzz"),
    ("maison_noble_personne", "Charles Quint"),   # multi-maison (Habsbourg + sous-branche) -> HORS (fonctionnel)
    ("parti_personne", "apolitique-inconnu-zzz"),
    ("parti_personne", "Bernie Sanders"),   # multi-parti (Union de la liberté + démocrate) -> HORS (fonctionnel)
]
for rel, ent in ADVERSE:
    st, f = lec.repond(rel, ent)
    check(f"SOUNDNESS {rel}({ent}) -> HORS [{st}]", st == HORS and f is None)

print(f"\n=== T8 : {ok}/{total} checks PASS ===")
if ok != total:
    raise SystemExit(1)
