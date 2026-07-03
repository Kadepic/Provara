"""
SANITÉ T4 — couloir VIVANT (biologie). Vérifie les tables ingérées par ingere_t4.py SANS jamais admettre un
fait faux (FAUX=0). Trois leviers, comme le reste du chantier :
  • ENSEMBLE FERMÉ : les valeurs d'une relation à vocabulaire clos restent dans la référence vérifiée à la main
    (statut UICN ; rangs taxinomiques) -> une valeur hors-référence = anomalie -> FAIL.
  • ANCRES vérité-terrain : des entités au libellé NON ambigu dont la valeur est vérifiée indépendamment du code
    (INS->Homo sapiens, HBB->chromosome 11 humain, TP53->chromosome 17, GAL4->levure). Un homonyme parti en HORS
    fait FAIL l'ancre -> on le saurait.
  • STRUCTURE : valeurs non vides, ensembles distincts de taille bornée (un set « fermé » qui explose = filon
    mensonger).

En-tête `borne(...)` OBLIGATOIRE : charge tout le lecteur (~10 M faits) -> sans cap CPU élevé, SIGXCPU (137).
Lancer SEUL (1 chargement) en dev ; l'enregistrer dans _nonreg.py pour la gate complète (annoncé au canal).
EXIT 0 = tous les check passent ; EXIT non-nul = au moins un échec (AssertionError).
"""
from garde_ressources import borne
# 2026-06-26 : la flotte a grossi le lecteur partagé à ~33,5 M faits -> pic transitoire du chargement ~5,1 Go
# (T-OPTIM : données figées ~1 Go / 28 o-fait, le pic = dicts avant gele()). Le borne suit cette croissance.
# T-OPTIM a relevé le cap de la gate intégrée _nonreg à 14 Go ; je m'aligne à 8,0 Go (marge ~3 Go au pic).
# À rebaisser quand le backend dict-global/front-coding de T-OPTIM (RSS quasi nulle) sera intégré au lecteur.
borne(max_go=8.0, max_cpu_s=1200)

import lecteur as L
from lecteur import VERIFIE

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


def _vals(rel):
    return [f.valeur for f in L.LECTEUR.tables.get(rel, {}).values()]


# ── statut_conservation : ensemble fermé des catégories UICN (libellés FR de Wikidata) ──────────────
# Référence = catégories UICN légitimes (les 8 observées + les standards possibles dans un snapshot complet).
# Sanité STRUCTURELLE et TEMPS-STABLE : on ne fige pas le statut d'une espèce (vérité datée, EN<->VU bouge),
# on vérifie seulement que TOUTE valeur est une catégorie UICN valide.
_UICN = {
    "espèce de préoccupation mineure", "espèce quasi menacée", "espèce vulnérable",
    "espèce menacée", "espèce en danger", "espèce en danger critique",
    "espèce éteinte à l'état sauvage", "espèce disparue", "espèce éteinte",
    "espèce à données insuffisantes", "espèce non évaluée",
}
if "statut_conservation" in L.LECTEUR.tables:
    v = _vals("statut_conservation")
    hors = sorted(set(v) - _UICN)
    check(f"statut_conservation : toutes valeurs ∈ catégories UICN [hors-réf: {hors[:5]}]", not hors)
    check("statut_conservation : valeurs non vides", all(s.strip() for s in v))
    check("statut_conservation : ensemble fermé (≤ 15 catégories distinctes)", len(set(v)) <= 15)


# ── chromosome_gene : ensemble fermé « chromosome N de <espèce> » + scaffolds réels ─────────────────
# Vocabulaire clos (chromosomes/scaffolds par espèce). On NE force PAS « commence par chromosome » : des IDs
# de scaffold réels (PRELSG_*, TvY486_* pour Plasmodium/Trypanosoma) sont des assignations VRAIES.
if "chromosome_gene" in L.LECTEUR.tables:
    v = _vals("chromosome_gene")
    check("chromosome_gene : ensemble fermé (≤ 300 valeurs distinctes)", len(set(v)) <= 300)
    check("chromosome_gene : valeurs non vides (≥2 car.)", all(len(s.strip()) >= 2 for s in v))
    # ancres position chromosomique (vérifiées indépendamment : HBB/INS en 11p15, TP53 en 17p13)
    for ent, att in [("HBB", "chromosome 11 humain"), ("INS", "chromosome 11 humain"),
                     ("TP53", "chromosome 17 humain")]:
        st, f = L.repond("chromosome_gene", ent)
        check(f"ancre chromosome_gene({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── organisme_gene : valeurs = taxon hôte (noms d'espèces/souches) + ancres ──────────────────────────
if "organisme_gene" in L.LECTEUR.tables:
    v = _vals("organisme_gene")
    check("organisme_gene : ensemble d'organismes borné (≤ 5000 distincts)", len(set(v)) <= 5000)
    check("organisme_gene : valeurs non vides (≥3 car.)", all(len(s.strip()) >= 3 for s in v))
    # ancres organisme-hôte (vérifiées à la main : INS=insuline humaine ; GAL4/CDC28/URA3 = gènes de levure)
    for ent, att in [("INS", "Homo sapiens"),
                     ("GAL4", "Saccharomyces cerevisiae S288c"),
                     ("CDC28", "Saccharomyces cerevisiae S288c"),
                     ("URA3", "Saccharomyces cerevisiae S288c")]:
        st, f = L.repond("organisme_gene", ent)
        check(f"ancre organisme_gene({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── specialite_medicale_maladie : ensemble fermé de spécialités médicales (ingéré sur demande) ───────
if "specialite_medicale_maladie" in L.LECTEUR.tables:
    v = _vals("specialite_medicale_maladie")
    check("specialite_medicale_maladie : ensemble fermé (≤ 250 spécialités distinctes)", len(set(v)) <= 250)
    check("specialite_medicale_maladie : valeurs non vides (≥3 car.)", all(len(s.strip()) >= 3 for s in v))
    # ancre vérité-terrain : l'hépatite C est une maladie infectieuse -> infectiologie (vérifié indépendamment).
    st, f = L.repond("specialite_medicale_maladie", "hépatite C")
    check("ancre specialite_medicale_maladie(hépatite C) == infectiologie",
          st == VERIFIE and f.valeur == "infectiologie")


# ── taxon_rang : ensemble fermé de rangs taxinomiques (présent seulement après la vague géante) ──────
_RANGS = {
    "espèce", "sous-espèce", "genre", "sous-genre", "famille", "sous-famille", "super-famille",
    "ordre", "sous-ordre", "super-ordre", "classe", "sous-classe", "embranchement", "sous-embranchement",
    "règne", "sous-règne", "tribu", "sous-tribu", "super-tribu", "section", "sous-section", "série",
    "sous-série", "variété", "forme", "nothoespèce", "nothogenre", "ichnogenre", "ichnoespèce",
    "rameau", "domaine", "super-classe", "infra-classe", "infra-ordre", "parvordre", "cohorte",
}
if "taxon_rang" in L.LECTEUR.tables:
    v = _vals("taxon_rang")
    # Ensemble fermé : ~78 rangs distincts réels (espèce/genre/.../cultivar/clade/biovar + qq fallback EN).
    # Borne ≤120 = anti-explosion (un filon mensonger ferait exploser le nb de valeurs distinctes), pas une
    # liste blanche exhaustive (Wikidata a plus de rangs rares que la liste canonique de base).
    check(f"taxon_rang : ensemble fermé (≤ 120 rangs distincts) [obs={len(set(v))}]", len(set(v)) <= 120)
    check("taxon_rang : valeurs non vides", all(s.strip() for s in v))
    # ANCRES vérité-terrain (taxa au rang non contesté, vérifiés indépendamment du code) :
    for ent, att in [("Homo sapiens", "espèce"), ("Homo", "genre"),
                     ("Canis", "genre"), ("Panthera", "genre")]:
        st, f = L.repond("taxon_rang", ent)
        check(f"ancre taxon_rang({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── agent_pathogene_maladie : maladie infectieuse -> agent pathogène (filon CURÉ par le modèle) ───────
# SOURCE = le modèle (directive Yohan : « tu peux être la source »). Liste textbook FAUX=0. Sanité =
# structure (≥40 paires, valeurs non vides) + ancres round-trip vérifiant l'intégrité de stockage sur des
# étiologies non contestées (tuberculose=M. tuberculosis ; paludisme=Plasmodium ; COVID-19=SARS-CoV-2).
if "agent_pathogene_maladie" in L.LECTEUR.tables:
    v = _vals("agent_pathogene_maladie")
    check("agent_pathogene_maladie : ≥40 paires curées", len(v) >= 40)
    check("agent_pathogene_maladie : valeurs (pathogènes) non vides (≥4 car.)", all(len(s.strip()) >= 4 for s in v))
    for ent, att in [("tuberculose", "Mycobacterium tuberculosis"), ("paludisme", "Plasmodium"),
                     ("COVID-19", "SARS-CoV-2"), ("choléra", "Vibrio cholerae"),
                     ("tétanos", "Clostridium tetani"), ("sida", "virus de l'immunodéficience humaine"),
                     ("psittacose", "Chlamydia psittaci"), ("salmonellose", "Salmonella"),
                     ("colite pseudomembraneuse", "Clostridioides difficile"),
                     ("distomatose hépatique", "Fasciola hepatica")]:
        st, f = L.repond("agent_pathogene_maladie", ent)
        check(f"ancre agent_pathogene_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# NB sens_organe : NON validé ici — nom déjà détenu par une autre source (direction organe->sens), pas à moi.

# ── lexique zoologique FR curé (cri / petit / groupe / adjectif) ──────────────────────────────────────
# NB cri_animal / petit_animal : NON validés ici — déjà détenus par une autre lane (lexique FR de référence).

# ── solubilite_vitamine / type_glucide / nom_scientifique_champignon (filons CURÉS par le modèle) ─────
if "solubilite_vitamine" in L.LECTEUR.tables:
    v = _vals("solubilite_vitamine")
    check("solubilite_vitamine : ensemble fermé (≤ 2)", len(set(v)) <= 2)
    for ent, att in [("vitamine A", "liposoluble"), ("vitamine C", "hydrosoluble"),
                     ("vitamine K", "liposoluble")]:
        st, f = L.repond("solubilite_vitamine", ent)
        check(f"ancre solubilite_vitamine({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "type_glucide" in L.LECTEUR.tables:
    v = _vals("type_glucide")
    check("type_glucide : ensemble fermé (≤ 3)", len(set(v)) <= 3)
    for ent, att in [("glucose", "ose"), ("saccharose", "diholoside"), ("amidon", "polyoside")]:
        st, f = L.repond("type_glucide", ent)
        check(f"ancre type_glucide({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "nom_scientifique_champignon" in L.LECTEUR.tables:
    for ent, att in [("champignon de Paris", "Agaricus bisporus"),
                     ("levure de boulanger", "Saccharomyces cerevisiae"),
                     ("truffe noire", "Tuber melanosporum")]:
        st, f = L.repond("nom_scientifique_champignon", ent)
        check(f"ancre nom_scientifique_champignon({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nom_scientifique_plante : nom commun FR -> binôme latin (filon CURÉ par le modèle) ────────────────
if "nom_scientifique_plante" in L.LECTEUR.tables:
    v = _vals("nom_scientifique_plante")
    check("nom_scientifique_plante : ≥30 paires curées", len(v) >= 30)
    for ent, att in [("blé", "Triticum aestivum"), ("tomate", "Solanum lycopersicum"),
                     ("olivier", "Olea europaea"), ("vigne", "Vitis vinifera"),
                     ("concombre", "Cucumis sativus"), ("thé", "Camellia sinensis"),
                     ("betterave", "Beta vulgaris")]:
        st, f = L.repond("nom_scientifique_plante", ent)
        check(f"ancre nom_scientifique_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nom_scientifique_animal : vernaculaire FR -> binôme latin (filon CURÉ par le modèle) ──────────────
if "nom_scientifique_animal" in L.LECTEUR.tables:
    v = _vals("nom_scientifique_animal")
    check("nom_scientifique_animal : ≥40 paires curées", len(v) >= 40)
    check("nom_scientifique_animal : valeurs binomiales non vides (≥5 car.)", all(len(s.strip()) >= 5 for s in v))
    for ent, att in [("lion", "Panthera leo"), ("être humain", "Homo sapiens"),
                     ("chien", "Canis lupus familiaris"), ("abeille", "Apis mellifera"),
                     ("dromadaire", "Camelus dromedarius"), ("renne", "Rangifer tarandus"),
                     ("morse", "Odobenus rosmarus")]:
        st, f = L.repond("nom_scientifique_animal", ent)
        check(f"ancre nom_scientifique_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── botanique curée : famille / partie comestible / type de fruit + organe producteur d'enzyme ────────
if "famille_plante" in L.LECTEUR.tables:
    for ent, att in [("rosier", "rosacée"), ("blé", "poacée"),
                     ("tomate", "solanacée"), ("haricot", "fabacée"),
                     ("carotte", "apiacée"), ("chou", "brassicacée"),
                     ("courgette", "cucurbitacée"), ("thym", "lamiacée")]:
        st, f = L.repond("famille_plante", ent)
        check(f"ancre famille_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "partie_comestible_plante" in L.LECTEUR.tables:
    v = _vals("partie_comestible_plante")
    check("partie_comestible_plante : ensemble fermé (≤ 8)", len(set(v)) <= 8)
    for ent, att in [("carotte", "racine"), ("pomme de terre", "tubercule"),
                     ("brocoli", "fleur"), ("oignon", "bulbe"),
                     ("manioc", "tubercule"), ("endive", "feuille"),
                     ("rhubarbe", "tige"), ("maïs", "graine")]:
        st, f = L.repond("partie_comestible_plante", ent)
        check(f"ancre partie_comestible_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "type_fruit_botanique" in L.LECTEUR.tables:
    for ent, att in [("raisin", "baie"), ("tomate", "baie"), ("cerise", "drupe"), ("olive", "drupe")]:
        st, f = L.repond("type_fruit_botanique", ent)
        check(f"ancre type_fruit_botanique({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "organe_producteur_enzyme" in L.LECTEUR.tables:
    for ent, att in [("pepsine", "estomac"), ("trypsine", "pancréas"), ("ptyaline", "glande salivaire")]:
        st, f = L.repond("organe_producteur_enzyme", ent)
        check(f"ancre organe_producteur_enzyme({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── respiration_animal / thermoregulation_animal / groupe_aliment (filons CURÉS par le modèle) ────────
if "respiration_animal" in L.LECTEUR.tables:
    v = _vals("respiration_animal")
    check("respiration_animal : ensemble fermé (≤ 5)", len(set(v)) <= 5)
    for ent, att in [("poisson", "branchies"), ("baleine bleue", "poumons"), ("ver de terre", "peau"),
                     ("escargot", "poumons"), ("papillon", "trachées"), ("thon rouge", "branchies")]:
        st, f = L.repond("respiration_animal", ent)
        check(f"ancre respiration_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "thermoregulation_animal" in L.LECTEUR.tables:
    v = _vals("thermoregulation_animal")
    check("thermoregulation_animal : ensemble fermé (≤ 3)", len(set(v)) <= 3)
    for ent, att in [("lion", "sang chaud"), ("python", "sang froid"), ("dauphin", "sang chaud"),
                     ("autruche", "sang chaud"), ("salamandre", "sang froid"), ("anguille", "sang froid")]:
        st, f = L.repond("thermoregulation_animal", ent)
        check(f"ancre thermoregulation_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "groupe_aliment" in L.LECTEUR.tables:
    v = _vals("groupe_aliment")
    check("groupe_aliment : ensemble fermé (≤ 8)", len(set(v)) <= 8)
    for ent, att in [("pomme", "fruit"), ("carotte", "légume"),
                     ("pomme de terre", "féculent"), ("lait", "produit laitier"),
                     ("cabillaud", "poisson"), ("chou", "légume"), ("agneau", "viande")]:
        st, f = L.repond("groupe_aliment", ent)
        check(f"ancre groupe_aliment({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── classe_antibiotique / classe_therapeutique_medicament / type_dent (filons CURÉS par le modèle) ────
if "classe_antibiotique" in L.LECTEUR.tables:
    for ent, att in [("amoxicilline", "bêta-lactamine"), ("érythromycine", "macrolide"),
                     ("gentamicine", "aminoside"), ("imipénème", "carbapénème"),
                     ("clindamycine", "lincosamide"), ("rifampicine", "rifamycine"),
                     ("colistine", "polymyxine")]:
        st, f = L.repond("classe_antibiotique", ent)
        check(f"ancre classe_antibiotique({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "classe_therapeutique_medicament" in L.LECTEUR.tables:
    for ent, att in [("paracétamol", "antalgique"), ("insuline", "antidiabétique"),
                     ("morphine", "analgésique opioïde"), ("héparine", "anticoagulant"),
                     ("fluoxétine", "antidépresseur"), ("propranolol", "bêta-bloquant"),
                     ("atorvastatine", "hypolipémiant")]:
        st, f = L.repond("classe_therapeutique_medicament", ent)
        check(f"ancre classe_therapeutique_medicament({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "type_dent" in L.LECTEUR.tables:
    for ent, att in [("incisive", "couper"), ("canine", "déchirer"), ("molaire", "broyer")]:
        st, f = L.repond("type_dent", ent)
        check(f"ancre type_dent({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── role_vitamine / role_hormone / role_oligoelement : entité -> rôle (filons CURÉS par le modèle) ─────
if "role_vitamine" in L.LECTEUR.tables:
    for ent, att in [("vitamine D", "absorption du calcium"), ("vitamine C", "synthèse du collagène"),
                     ("vitamine K", "coagulation sanguine"), ("vitamine B1", "métabolisme des glucides"),
                     ("vitamine B6", "métabolisme des acides aminés"), ("vitamine B5", "synthèse de la coenzyme A")]:
        st, f = L.repond("role_vitamine", ent)
        check(f"ancre role_vitamine({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "role_hormone" in L.LECTEUR.tables:
    for ent, att in [("insuline", "diminution de la glycémie"),
                     ("glucagon", "augmentation de la glycémie"), ("ocytocine", "contractions utérines"),
                     ("prolactine", "production de lait"), ("aldostérone", "réabsorption du sodium"),
                     ("érythropoïétine", "production des globules rouges")]:
        st, f = L.repond("role_hormone", ent)
        check(f"ancre role_hormone({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "role_oligoelement" in L.LECTEUR.tables:
    for ent, att in [("fer", "transport de l'oxygène"), ("iode", "synthèse des hormones thyroïdiennes"),
                     ("potassium", "transmission de l'influx nerveux"), ("phosphore", "minéralisation osseuse"),
                     ("sélénium", "antioxydant"), ("zinc", "cicatrisation")]:
        st, f = L.repond("role_oligoelement", ent)
        check(f"ancre role_oligoelement({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "nom_groupe_animaux" in L.LECTEUR.tables:
    for ent, att in [("loup", "meute"), ("poisson", "banc"), ("abeille", "essaim")]:
        st, f = L.repond("nom_groupe_animaux", ent)
        check(f"ancre nom_groupe_animaux({ent}) == {att}", st == VERIFIE and f.valeur == att)
if "adjectif_animal" in L.LECTEUR.tables:
    for ent, att in [("chien", "canin"), ("chat", "félin"),
                     ("cheval", "équin"), ("vache", "bovin"),
                     ("lion", "léonin"), ("serpent", "ophidien"), ("aigle", "aquilin"),
                     ("lièvre", "léporin")]:
        st, f = L.repond("adjectif_animal", ent)
        check(f"ancre adjectif_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── classe_invertebre_animal : invertébré -> groupe (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ────────
if "classe_invertebre_animal" in L.LECTEUR.tables:
    v = _vals("classe_invertebre_animal")
    check("classe_invertebre_animal : ensemble fermé (≤ 8 groupes distincts)", len(set(v)) <= 8)
    check("classe_invertebre_animal : ≥12 paires curées", len(v) >= 12)
    for ent, att in [("araignée", "arachnide"), ("abeille", "insecte"),
                     ("pieuvre", "mollusque"), ("étoile de mer", "échinoderme"),
                     ("faucheux", "arachnide"), ("bernard-l'ermite", "crustacé"),
                     ("comatule", "échinoderme"), ("gorgone", "cnidaire")]:
        st, f = L.repond("classe_invertebre_animal", ent)
        check(f"ancre classe_invertebre_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── phylum_animal : animal -> EMBRANCHEMENT (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ────────────────
if "phylum_animal" in L.LECTEUR.tables:
    v = _vals("phylum_animal")
    check("phylum_animal : ensemble fermé (≤ 12 phyla distincts)", len(set(v)) <= 12)
    check("phylum_animal : ≥30 paires curées", len(v) >= 30)
    for ent, att in [("être humain", "chordés"), ("araignée", "arthropodes"),
                     ("pieuvre", "mollusques"), ("méduse", "cnidaires"),
                     ("étoile de mer", "échinodermes"), ("ver de terre", "annélides")]:
        st, f = L.repond("phylum_animal", ent)
        check(f"ancre phylum_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_symetrie_animal : animal -> symétrie corporelle (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────
if "type_symetrie_animal" in L.LECTEUR.tables:
    v = _vals("type_symetrie_animal")
    check("type_symetrie_animal : ensemble fermé (≤ 4 types distincts)", len(set(v)) <= 4)
    for ent, att in [("être humain", "bilatérale"), ("méduse", "radiaire"),
                     ("étoile de mer", "radiaire"), ("éponge de mer", "asymétrique")]:
        st, f = L.repond("type_symetrie_animal", ent)
        check(f"ancre type_symetrie_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── nombre_chambres_coeur_animal : vertébré -> nb cavités cardiaques (ENSEMBLE FERMÉ {2,3,4} ; CURÉ) ───
if "nombre_chambres_coeur_animal" in L.LECTEUR.tables:
    v = _vals("nombre_chambres_coeur_animal")
    check("nombre_chambres_coeur_animal : ensemble fermé (≤ 3 valeurs distinctes)", len(set(v)) <= 3)
    for ent, att in [("carpe", "2"), ("grenouille rousse", "3"),
                     ("crocodile du Nil", "4"), ("être humain", "4"),
                     ("morue", "2"), ("python", "3"), ("iguane", "3"), ("baleine bleue", "4")]:
        st, f = L.repond("nombre_chambres_coeur_animal", ent)
        check(f"ancre nombre_chambres_coeur_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_squelette_animal : animal -> type de squelette (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────
if "type_squelette_animal" in L.LECTEUR.tables:
    v = _vals("type_squelette_animal")
    check("type_squelette_animal : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("être humain", "endosquelette"), ("requin", "endosquelette"),
                     ("crabe", "exosquelette"), ("escargot", "exosquelette"),
                     ("ver de terre", "hydrosquelette"), ("méduse", "hydrosquelette"),
                     ("étoile de mer", "endosquelette"), ("oursin", "endosquelette"),
                     ("moule", "exosquelette")]:
        st, f = L.repond("type_squelette_animal", ent)
        check(f"ancre type_squelette_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── regne_organisme : organisme -> règne du vivant (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────
if "regne_organisme" in L.LECTEUR.tables:
    v = _vals("regne_organisme")
    check("regne_organisme : ensemble fermé (≤ 6 règnes distincts)", len(set(v)) <= 6)
    for ent, att in [("chien", "animal"), ("chêne", "végétal"),
                     ("champignon de Paris", "champignon"), ("Escherichia coli", "bactérie"),
                     ("pieuvre", "animal"), ("bolet", "champignon"), ("olivier", "végétal")]:
        st, f = L.repond("regne_organisme", ent)
        check(f"ancre regne_organisme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_metamorphose_insecte : insecte -> métamorphose (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────
if "type_metamorphose_insecte" in L.LECTEUR.tables:
    v = _vals("type_metamorphose_insecte")
    check("type_metamorphose_insecte : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("papillon", "holométabole"), ("abeille", "holométabole"),
                     ("sauterelle", "hémimétabole"), ("libellule", "hémimétabole"),
                     ("lépisme", "amétabole"), ("guêpe", "holométabole"),
                     ("termite", "hémimétabole"), ("phasme", "hémimétabole")]:
        st, f = L.repond("type_metamorphose_insecte", ent)
        check(f"ancre type_metamorphose_insecte({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── groupe_plante : plante -> grand groupe végétal (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────
if "groupe_plante" in L.LECTEUR.tables:
    v = _vals("groupe_plante")
    check("groupe_plante : ensemble fermé (≤ 5 groupes distincts)", len(set(v)) <= 5)
    for ent, att in [("rosier", "angiosperme"), ("pin", "gymnosperme"),
                     ("fougère aigle", "fougère"), ("sphaigne", "mousse"), ("laminaire", "algue"),
                     ("séquoia", "gymnosperme"), ("orchidée", "angiosperme"), ("ulve", "algue")]:
        st, f = L.repond("groupe_plante", ent)
        check(f"ancre groupe_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_muscle : muscle -> type histologique (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────────
if "type_muscle" in L.LECTEUR.tables:
    v = _vals("type_muscle")
    check("type_muscle : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("biceps", "strié squelettique"), ("myocarde", "cardiaque"),
                     ("muscle de l'intestin", "lisse"), ("langue", "strié squelettique"),
                     ("muscle de l'utérus", "lisse"), ("triceps", "strié squelettique")]:
        st, f = L.repond("type_muscle", ent)
        check(f"ancre type_muscle({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── forme_bacterie : bactérie -> forme (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────────────────
if "forme_bacterie" in L.LECTEUR.tables:
    v = _vals("forme_bacterie")
    check("forme_bacterie : ensemble fermé (≤ 4 formes distinctes)", len(set(v)) <= 4)
    for ent, att in [("staphylocoque", "coque"), ("Escherichia coli", "bacille"),
                     ("Vibrio cholerae", "vibrion"), ("Helicobacter pylori", "spirille"),
                     ("entérocoque", "coque"), ("Listeria", "bacille"), ("Bacillus anthracis", "bacille")]:
        st, f = L.repond("forme_bacterie", ent)
        check(f"ancre forme_bacterie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── coloration_gram_bacterie : bactérie -> Gram +/− (ENSEMBLE FERMÉ ; filon CURÉ ; piège coques Gram−) ──
if "coloration_gram_bacterie" in L.LECTEUR.tables:
    v = _vals("coloration_gram_bacterie")
    check("coloration_gram_bacterie : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("staphylocoque doré", "Gram positif"), ("Escherichia coli", "Gram négatif"),
                     ("méningocoque", "Gram négatif"), ("entérocoque", "Gram positif"),
                     ("Klebsiella pneumoniae", "Gram négatif"), ("Lactobacillus", "Gram positif")]:
        st, f = L.repond("coloration_gram_bacterie", ent)
        check(f"ancre coloration_gram_bacterie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_glande : glande -> type sécrétoire (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────────
if "type_glande" in L.LECTEUR.tables:
    v = _vals("type_glande")
    check("type_glande : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("thyroïde", "endocrine"), ("glande salivaire", "exocrine"), ("pancréas", "mixte"),
                     ("prostate", "exocrine"), ("testicule", "mixte"), ("ovaire", "mixte")]:
        st, f = L.repond("type_glande", ent)
        check(f"ancre type_glande({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── mode_nutrition : organisme -> autotrophe/hétérotrophe (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────
if "mode_nutrition" in L.LECTEUR.tables:
    v = _vals("mode_nutrition")
    check("mode_nutrition : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("chêne", "autotrophe"), ("lion", "hétérotrophe"),
                     ("champignon de Paris", "hétérotrophe"), ("cyanobactérie", "autotrophe"),
                     ("fougère", "autotrophe"), ("ténia", "hétérotrophe")]:
        st, f = L.repond("mode_nutrition", ent)
        check(f"ancre mode_nutrition({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_vaisseau_sanguin : vaisseau -> artère/veine/capillaire (ENSEMBLE FERMÉ ; filon CURÉ) ───────────
if "type_vaisseau_sanguin" in L.LECTEUR.tables:
    v = _vals("type_vaisseau_sanguin")
    check("type_vaisseau_sanguin : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("aorte", "artère"), ("veine cave", "veine"),
                     ("artère pulmonaire", "artère"), ("veine pulmonaire", "veine"),
                     ("artère rénale", "artère"), ("veine fémorale", "veine"),
                     ("capillaire glomérulaire", "capillaire")]:
        st, f = L.repond("type_vaisseau_sanguin", ent)
        check(f"ancre type_vaisseau_sanguin({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_leucocyte : globule blanc -> granulocyte/agranulocyte (ENSEMBLE FERMÉ ; filon CURÉ) ────────────
if "type_leucocyte" in L.LECTEUR.tables:
    v = _vals("type_leucocyte")
    check("type_leucocyte : ensemble fermé (≤ 2 classes)", len(set(v)) <= 2)
    for ent, att in [("neutrophile", "granulocyte"), ("lymphocyte", "agranulocyte"),
                     ("monocyte", "agranulocyte"), ("lymphocyte T", "agranulocyte"),
                     ("polynucléaire basophile", "granulocyte"), ("cellule NK", "agranulocyte")]:
        st, f = L.repond("type_leucocyte", ent)
        check(f"ancre type_leucocyte({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── os_type : os -> type morphologique (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────────────────
if "os_type" in L.LECTEUR.tables:
    v = _vals("os_type")
    check("os_type : ensemble fermé (≤ 5 types distincts)", len(set(v)) <= 5)
    for ent, att in [("fémur", "long"), ("os du carpe", "court"), ("sternum", "plat"),
                     ("vertèbre", "irrégulier"), ("rotule", "sésamoïde"),
                     ("cubitus", "long"), ("calcanéus", "court"), ("os occipital", "plat"),
                     ("sphénoïde", "irrégulier")]:
        st, f = L.repond("os_type", ent)
        check(f"ancre os_type({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_racine_plante : plante -> type de racine (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────────
if "type_racine_plante" in L.LECTEUR.tables:
    v = _vals("type_racine_plante")
    check("type_racine_plante : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("carotte", "pivotante"), ("blé", "fasciculée"), ("lierre", "adventice"),
                     ("navet", "pivotante"), ("oignon", "fasciculée"), ("menthe", "adventice")]:
        st, f = L.repond("type_racine_plante", ent)
        check(f"ancre type_racine_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_tige_plante : plante -> nature de la tige (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────
if "type_tige_plante" in L.LECTEUR.tables:
    v = _vals("type_tige_plante")
    check("type_tige_plante : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("blé", "herbacée"), ("chêne", "ligneuse"), ("rosier", "ligneuse"),
                     ("menthe", "herbacée"), ("hêtre", "ligneuse"), ("olivier", "ligneuse")]:
        st, f = L.repond("type_tige_plante", ent)
        check(f"ancre type_tige_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── niveau_trophique : organisme -> niveau trophique (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────
if "niveau_trophique" in L.LECTEUR.tables:
    v = _vals("niveau_trophique")
    check("niveau_trophique : ensemble fermé (≤ 3 niveaux distincts)", len(set(v)) <= 3)
    for ent, att in [("chêne", "producteur"), ("lion", "consommateur"),
                     ("champignon de Paris", "décomposeur"), ("maïs", "producteur"),
                     ("loup", "consommateur"), ("moisissure", "décomposeur")]:
        st, f = L.repond("niveau_trophique", ent)
        check(f"ancre niveau_trophique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_fecondation : animal -> interne/externe (ENSEMBLE FERMÉ ; filon CURÉ ; exception requin) ───────
if "type_fecondation" in L.LECTEUR.tables:
    v = _vals("type_fecondation")
    check("type_fecondation : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("saumon atlantique", "externe"), ("grenouille rousse", "externe"),
                     ("être humain", "interne"), ("requin", "interne"),
                     ("morue", "externe"), ("huître", "externe"), ("lion", "interne")]:
        st, f = L.repond("type_fecondation", ent)
        check(f"ancre type_fecondation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_developpement : animal -> direct/indirect (ENSEMBLE FERMÉ ; filon CURÉ ; exception araignée) ───
if "type_developpement" in L.LECTEUR.tables:
    v = _vals("type_developpement")
    check("type_developpement : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("papillon", "indirect"), ("grenouille rousse", "indirect"),
                     ("être humain", "direct"), ("araignée", "direct"),
                     ("salamandre", "indirect"), ("moustique", "indirect"), ("lion", "direct")]:
        st, f = L.repond("type_developpement", ent)
        check(f"ancre type_developpement({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── appareil_circulatoire_type : animal -> ouverte/fermée (ENSEMBLE FERMÉ ; filon CURÉ ; exception pieuvre) ─
if "appareil_circulatoire_type" in L.LECTEUR.tables:
    v = _vals("appareil_circulatoire_type")
    check("appareil_circulatoire_type : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("abeille", "ouverte"), ("escargot", "ouverte"),
                     ("être humain", "fermée"), ("pieuvre", "fermée"),
                     ("homard", "ouverte"), ("calmar", "fermée"), ("lion", "fermée")]:
        st, f = L.repond("appareil_circulatoire_type", ent)
        check(f"ancre appareil_circulatoire_type({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_cellule : procaryote/eucaryote (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────────────
if "type_cellule" in L.LECTEUR.tables:
    v = _vals("type_cellule")
    check("type_cellule : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("Escherichia coli", "procaryote"), ("neurone", "eucaryote"),
                     ("levure de boulanger", "eucaryote"), ("salmonelle", "procaryote"),
                     ("lymphocyte", "eucaryote"), ("Plasmodium", "eucaryote")]:
        st, f = L.repond("type_cellule", ent)
        check(f"ancre type_cellule({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── nature_hormone : hormone -> nature biochimique (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────
if "nature_hormone" in L.LECTEUR.tables:
    v = _vals("nature_hormone")
    check("nature_hormone : ensemble fermé (≤ 3 natures distinctes)", len(set(v)) <= 3)
    for ent, att in [("insuline", "peptidique"), ("testostérone", "stéroïde"),
                     ("adrénaline", "dérivée d'acide aminé"), ("calcitonine", "peptidique"),
                     ("œstradiol", "stéroïde"), ("triiodothyronine", "dérivée d'acide aminé")]:
        st, f = L.repond("nature_hormone", ent)
        check(f"ancre nature_hormone({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── classe_enzyme : enzyme -> classe EC (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────────────────
if "classe_enzyme" in L.LECTEUR.tables:
    v = _vals("classe_enzyme")
    check("classe_enzyme : ensemble fermé (≤ 6 classes EC distinctes)", len(set(v)) <= 6)
    for ent, att in [("catalase", "oxydoréductase"), ("amylase", "hydrolase"),
                     ("ADN ligase", "ligase"), ("ADN polymérase", "transférase"),
                     ("peroxydase", "oxydoréductase"), ("fumarase", "lyase"),
                     ("créatine kinase", "transférase"), ("uréase", "hydrolase")]:
        st, f = L.repond("classe_enzyme", ent)
        check(f"ancre classe_enzyme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_acide_amine : essentiel/non-essentiel chez l'humain (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "type_acide_amine" in L.LECTEUR.tables:
    v = _vals("type_acide_amine")
    check("type_acide_amine : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("leucine", "essentiel"), ("tryptophane", "essentiel"),
                     ("alanine", "non-essentiel"), ("glutamate", "non-essentiel")]:
        st, f = L.repond("type_acide_amine", ent)
        check(f"ancre type_acide_amine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── base_azotee_type : base azotée -> purine/pyrimidine (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────
if "base_azotee_type" in L.LECTEUR.tables:
    v = _vals("base_azotee_type")
    check("base_azotee_type : ensemble fermé (≤ 2 valeurs)", len(set(v)) <= 2)
    for ent, att in [("adénine", "purine"), ("guanine", "purine"),
                     ("cytosine", "pyrimidine"), ("uracile", "pyrimidine")]:
        st, f = L.repond("base_azotee_type", ent)
        check(f"ancre base_azotee_type({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── appariement_base_adn : base ADN -> base complémentaire (fonctionnel ; filon CURÉ) ───────────────────
if "appariement_base_adn" in L.LECTEUR.tables:
    for ent, att in [("adénine", "thymine"), ("thymine", "adénine"),
                     ("guanine", "cytosine"), ("cytosine", "guanine")]:
        st, f = L.repond("appariement_base_adn", ent)
        check(f"ancre appariement_base_adn({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── nombre_chromosomes_espece : espèce -> 2n (valeurs canoniques ; filon CURÉ ; sanité par ancres) ──────
if "nombre_chromosomes_espece" in L.LECTEUR.tables:
    v = _vals("nombre_chromosomes_espece")
    check("nombre_chromosomes_espece : valeurs entières plausibles (2..1500)",
          all(s.isdigit() and 2 <= int(s) <= 1500 for s in v))
    for ent, att in [("être humain", "46"), ("chimpanzé", "48"), ("chien", "78"), ("drosophile", "8")]:
        st, f = L.repond("nombre_chromosomes_espece", ent)
        check(f"ancre nombre_chromosomes_espece({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_arn : type d'ARN -> fonction (fonctionnel ; filon CURÉ) ──────────────────────────────────
if "fonction_arn" in L.LECTEUR.tables:
    for ent, att in [("ARN messager", "transmission de l'information génétique"),
                     ("ARN de transfert", "transport des acides aminés"),
                     ("ARN ribosomique", "constitution des ribosomes")]:
        st, f = L.repond("fonction_arn", ent)
        check(f"ancre fonction_arn({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_tissu_vegetal : tissu végétal -> fonction (fonctionnel ; filon CURÉ) ─────────────────────
if "fonction_tissu_vegetal" in L.LECTEUR.tables:
    for ent, att in [("xylème", "conduction de la sève brute"),
                     ("phloème", "conduction de la sève élaborée"),
                     ("méristème", "croissance")]:
        st, f = L.repond("fonction_tissu_vegetal", ent)
        check(f"ancre fonction_tissu_vegetal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_immunoglobuline : classe d'anticorps -> rôle (fonctionnel ; filon CURÉ) ──────────────────────
if "role_immunoglobuline" in L.LECTEUR.tables:
    for ent, att in [("immunoglobuline G", "réponse immunitaire secondaire"),
                     ("immunoglobuline A", "protection des muqueuses"),
                     ("immunoglobuline E", "allergies et infections parasitaires")]:
        st, f = L.repond("role_immunoglobuline", ent)
        check(f"ancre role_immunoglobuline({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_partie_neurone : partie du neurone -> fonction (fonctionnel ; filon CURÉ) ─────────────────
if "fonction_partie_neurone" in L.LECTEUR.tables:
    for ent, att in [("dendrite", "réception des signaux"),
                     ("axone", "transmission de l'influx nerveux"),
                     ("gaine de myéline", "accélération de l'influx nerveux")]:
        st, f = L.repond("fonction_partie_neurone", ent)
        check(f"ancre fonction_partie_neurone({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── systeme_organe_humain : organe -> système (fonctionnel ; filon CURÉ) ──────────────────────────────
if "systeme_organe_humain" in L.LECTEUR.tables:
    for ent, att in [("cœur", "système circulatoire"), ("poumon", "système respiratoire"),
                     ("rein", "système urinaire"), ("cerveau", "système nerveux")]:
        st, f = L.repond("systeme_organe_humain", ent)
        check(f"ancre systeme_organe_humain({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_systeme_humain : système -> fonction (fonctionnel ; filon CURÉ) ───────────────────────────
if "fonction_systeme_humain" in L.LECTEUR.tables:
    for ent, att in [("système circulatoire", "transport des nutriments et de l'oxygène"),
                     ("système respiratoire", "échanges gazeux"),
                     ("système urinaire", "élimination des déchets")]:
        st, f = L.repond("fonction_systeme_humain", ent)
        check(f"ancre fonction_systeme_humain({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_macronutriment : macronutriment -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────
if "role_macronutriment" in L.LECTEUR.tables:
    for ent, att in [("glucides", "source d'énergie"), ("lipides", "réserve d'énergie"),
                     ("protéines", "construction des tissus")]:
        st, f = L.repond("role_macronutriment", ent)
        check(f"ancre role_macronutriment({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_articulation : articulation -> type structural (fonctionnel ; filon CURÉ) ─────────────────────
if "type_articulation" in L.LECTEUR.tables:
    for ent, att in [("genou", "synoviale"), ("sutures du crâne", "fibreuse"),
                     ("symphyse pubienne", "cartilagineuse"), ("cheville", "synoviale"),
                     ("gomphose dentaire", "fibreuse")]:
        st, f = L.repond("type_articulation", ent)
        check(f"ancre type_articulation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── agent_dispersion_graine : mode -> agent (définitionnel ; filon CURÉ) ───────────────────────────────
if "agent_dispersion_graine" in L.LECTEUR.tables:
    for ent, att in [("anémochorie", "vent"), ("hydrochorie", "eau"), ("zoochorie", "animaux"),
                     ("myrmécochorie", "fourmis"), ("autochorie", "plante elle-même")]:
        st, f = L.repond("agent_dispersion_graine", ent)
        check(f"ancre agent_dispersion_graine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_phytohormone : hormone végétale -> rôle (fonctionnel ; filon CURÉ) ─────────────────────────────
if "role_phytohormone" in L.LECTEUR.tables:
    for ent, att in [("auxine", "croissance par élongation cellulaire"),
                     ("éthylène", "maturation des fruits"),
                     ("cytokinine", "division cellulaire"),
                     ("acide salicylique", "résistance aux pathogènes"),
                     ("jasmonate", "défense contre les herbivores")]:
        st, f = L.repond("role_phytohormone", ent)
        check(f"ancre role_phytohormone({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_neurone : type de neurone -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_neurone" in L.LECTEUR.tables:
    for ent, att in [("neurone sensitif", "transmettre l'information vers le système nerveux central"),
                     ("neurone moteur", "commander les muscles et les glandes"),
                     ("interneurone", "relier les neurones entre eux")]:
        st, f = L.repond("role_neurone", ent)
        check(f"ancre role_neurone({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_immunite : type d'immunité -> caractère (fonctionnel ; filon CURÉ) ───────────────────────
if "caractere_immunite" in L.LECTEUR.tables:
    for ent, att in [("immunité innée", "non spécifique"), ("immunité adaptative", "spécifique")]:
        st, f = L.repond("caractere_immunite", ent)
        check(f"ancre caractere_immunite({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_symbiose : relation interspécifique -> effet (définitionnel ; filon CURÉ) ────────────────
if "caractere_symbiose" in L.LECTEUR.tables:
    for ent, att in [("mutualisme", "bénéfice réciproque"),
                     ("parasitisme", "bénéfice pour l'un, préjudice pour l'autre")]:
        st, f = L.repond("caractere_symbiose", ent)
        check(f"ancre caractere_symbiose({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── resultat_division_cellulaire : division -> résultat (fonctionnel ; filon CURÉ) ─────────────────────
if "resultat_division_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("mitose", "deux cellules filles identiques"),
                     ("méiose", "quatre cellules haploïdes")]:
        st, f = L.repond("resultat_division_cellulaire", ent)
        check(f"ancre resultat_division_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── condition_respiration_cellulaire : respiration -> condition O2 (définitionnel ; filon CURÉ) ─────────
if "condition_respiration_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("respiration aérobie", "présence d'oxygène"),
                     ("respiration anaérobie", "absence d'oxygène")]:
        st, f = L.repond("condition_respiration_cellulaire", ent)
        check(f"ancre condition_respiration_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── produit_fermentation : fermentation -> produit (fonctionnel ; filon CURÉ) ──────────────────────────
if "produit_fermentation" in L.LECTEUR.tables:
    for ent, att in [("fermentation lactique", "acide lactique"),
                     ("fermentation alcoolique", "éthanol")]:
        st, f = L.repond("produit_fermentation", ent)
        check(f"ancre produit_fermentation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── duree_cycle_plante : cycle de vie -> durée (définitionnel ; filon CURÉ) ─────────────────────────────
if "duree_cycle_plante" in L.LECTEUR.tables:
    for ent, att in [("plante annuelle", "un an"), ("plante vivace", "plusieurs années")]:
        st, f = L.repond("duree_cycle_plante", ent)
        check(f"ancre duree_cycle_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_niveau_ecologique : niveau -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_niveau_ecologique" in L.LECTEUR.tables:
    for ent, att in [("population", "individus d'une même espèce dans un milieu"),
                     ("écosystème", "communauté et son milieu physique")]:
        st, f = L.repond("definition_niveau_ecologique", ent)
        check(f"ancre definition_niveau_ecologique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── produit_excretion_organe : organe -> déchet (fonctionnel ; filon CURÉ) ─────────────────────────────
if "produit_excretion_organe" in L.LECTEUR.tables:
    for ent, att in [("rein", "urine"), ("peau", "sueur"), ("foie", "bile")]:
        st, f = L.repond("produit_excretion_organe", ent)
        check(f"ancre produit_excretion_organe({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_fleur : pièce florale -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_partie_fleur" in L.LECTEUR.tables:
    for ent, att in [("pétale", "attraction des pollinisateurs"),
                     ("étamine", "organe reproducteur mâle"),
                     ("pistil", "organe reproducteur femelle")]:
        st, f = L.repond("role_partie_fleur", ent)
        check(f"ancre role_partie_fleur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── developpement_mode_reproduction : mode -> développement (définitionnel ; filon CURÉ) ───────────────
if "developpement_mode_reproduction" in L.LECTEUR.tables:
    for ent, att in [("ovipare", "développement dans un œuf hors du corps de la mère"),
                     ("vivipare", "développement dans le corps de la mère")]:
        st, f = L.repond("developpement_mode_reproduction", ent)
        check(f"ancre developpement_mode_reproduction({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── consistance_fruit : type de fruit -> consistance (définitionnel ; filon CURÉ) ──────────────────────
if "consistance_fruit" in L.LECTEUR.tables:
    for ent, att in [("drupe", "charnu"), ("baie", "charnu"), ("gousse", "sec"), ("akène", "sec")]:
        st, f = L.repond("consistance_fruit", ent)
        check(f"ancre consistance_fruit({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── agent_pollinisation : pollinisation -> agent (définitionnel ; filon CURÉ) ───────────────────────────
if "agent_pollinisation" in L.LECTEUR.tables:
    for ent, att in [("entomophilie", "insectes"), ("anémophilie", "vent"), ("hydrophilie", "eau")]:
        st, f = L.repond("agent_pollinisation", ent)
        check(f"ancre agent_pollinisation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── nature_metabolisme : voie -> nature (définitionnel ; filon CURÉ) ────────────────────────────────────
if "nature_metabolisme" in L.LECTEUR.tables:
    for ent, att in [("anabolisme", "réactions de synthèse"), ("catabolisme", "réactions de dégradation")]:
        st, f = L.repond("nature_metabolisme", ent)
        check(f"ancre nature_metabolisme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organe_digestif : organe digestif -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────
if "role_organe_digestif" in L.LECTEUR.tables:
    for ent, att in [("estomac", "digestion des protéines"),
                     ("intestin grêle", "absorption des nutriments"),
                     ("foie", "production de la bile")]:
        st, f = L.repond("role_organe_digestif", ent)
        check(f"ancre role_organe_digestif({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_cerveau : région du cerveau -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────
if "role_partie_cerveau" in L.LECTEUR.tables:
    for ent, att in [("cervelet", "équilibre et coordination des mouvements"),
                     ("bulbe rachidien", "contrôle des fonctions vitales"),
                     ("cortex cérébral", "fonctions cognitives supérieures"),
                     ("hippocampe", "mémoire"), ("thalamus", "relais des informations sensorielles"),
                     ("corps calleux", "connexion des deux hémisphères")]:
        st, f = L.repond("role_partie_cerveau", ent)
        check(f"ancre role_partie_cerveau({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── stimulus_recepteur : récepteur -> stimulus (définitionnel ; filon CURÉ) ─────────────────────────────
if "stimulus_recepteur" in L.LECTEUR.tables:
    for ent, att in [("photorécepteur", "lumière"), ("mécanorécepteur", "pression"),
                     ("thermorécepteur", "température"), ("barorécepteur", "pression artérielle"),
                     ("propriocepteur", "position du corps")]:
        st, f = L.repond("stimulus_recepteur", ent)
        check(f"ancre stimulus_recepteur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── localisation_materiel_genetique : cellule -> localisation ADN (définitionnel ; filon CURÉ) ──────────
if "localisation_materiel_genetique" in L.LECTEUR.tables:
    for ent, att in [("cellule eucaryote", "noyau"), ("cellule procaryote", "cytoplasme")]:
        st, f = L.repond("localisation_materiel_genetique", ent)
        check(f"ancre localisation_materiel_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_oeil : partie de l'œil -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────
if "role_partie_oeil" in L.LECTEUR.tables:
    for ent, att in [("cornée", "réfraction de la lumière"), ("rétine", "formation de l'image"),
                     ("iris", "régulation de la quantité de lumière")]:
        st, f = L.repond("role_partie_oeil", ent)
        check(f"ancre role_partie_oeil({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_oreille : partie de l'oreille -> rôle (fonctionnel ; filon CURÉ) ────────────────────────
if "role_partie_oreille" in L.LECTEUR.tables:
    for ent, att in [("tympan", "transmission des vibrations sonores"),
                     ("canaux semi-circulaires", "équilibre")]:
        st, f = L.repond("role_partie_oreille", ent)
        check(f"ancre role_partie_oreille({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_tissu_animal : tissu animal -> fonction (fonctionnel ; filon CURÉ) ─────────────────────────
if "fonction_tissu_animal" in L.LECTEUR.tables:
    for ent, att in [("tissu épithélial", "revêtement et protection"),
                     ("tissu musculaire", "mouvement"),
                     ("tissu nerveux", "transmission de l'information")]:
        st, f = L.repond("fonction_tissu_animal", ent)
        check(f"ancre fonction_tissu_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_phase_cardiaque : phase -> rôle (définitionnel ; filon CURÉ) ───────────────────────────────────
if "role_phase_cardiaque" in L.LECTEUR.tables:
    for ent, att in [("systole", "contraction et éjection du sang"),
                     ("diastole", "relâchement et remplissage du cœur")]:
        st, f = L.repond("role_phase_cardiaque", ent)
        check(f"ancre role_phase_cardiaque({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_type_vaisseau : type de vaisseau -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────
if "role_type_vaisseau" in L.LECTEUR.tables:
    for ent, att in [("artère", "transport du sang du cœur vers les organes"),
                     ("veine", "retour du sang vers le cœur"),
                     ("capillaire", "échanges entre le sang et les tissus")]:
        st, f = L.repond("role_type_vaisseau", ent)
        check(f"ancre role_type_vaisseau({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_leucocyte : globule blanc -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_leucocyte" in L.LECTEUR.tables:
    for ent, att in [("lymphocyte", "réponse immunitaire spécifique"),
                     ("neutrophile", "phagocytose des bactéries"),
                     ("éosinophile", "lutte contre les parasites")]:
        st, f = L.repond("role_leucocyte", ent)
        check(f"ancre role_leucocyte({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_element_squelette : ensemble osseux -> rôle (fonctionnel ; filon CURÉ) ─────────────────────────
if "role_element_squelette" in L.LECTEUR.tables:
    for ent, att in [("crâne", "protection du cerveau"),
                     ("cage thoracique", "protection du cœur et des poumons"),
                     ("colonne vertébrale", "protection de la moelle épinière")]:
        st, f = L.repond("role_element_squelette", ent)
        check(f"ancre role_element_squelette({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── destination_secretion_glande : type de glande -> destination (définitionnel ; filon CURÉ) ──────────
if "destination_secretion_glande" in L.LECTEUR.tables:
    for ent, att in [("glande endocrine", "sang"),
                     ("glande exocrine", "canal excréteur vers une surface")]:
        st, f = L.repond("destination_secretion_glande", ent)
        check(f"ancre destination_secretion_glande({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── rang_taxon_superieur : rang -> rang supérieur (définitionnel ; filon CURÉ) ──────────────────────────
if "rang_taxon_superieur" in L.LECTEUR.tables:
    for ent, att in [("espèce", "genre"), ("genre", "famille"), ("ordre", "classe")]:
        st, f = L.repond("rang_taxon_superieur", ent)
        check(f"ancre rang_taxon_superieur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_acide_nucleique : acide nucléique -> rôle (définitionnel ; filon CURÉ) ─────────────────────────
if "role_acide_nucleique" in L.LECTEUR.tables:
    for ent, att in [("ADN", "conservation de l'information génétique"),
                     ("ARN", "expression de l'information génétique")]:
        st, f = L.repond("role_acide_nucleique", ent)
        check(f"ancre role_acide_nucleique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── constituant_paroi_cellulaire : cellule -> paroi (définitionnel ; filon CURÉ) ────────────────────────
if "constituant_paroi_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("cellule végétale", "cellulose"), ("cellule bactérienne", "peptidoglycane"),
                     ("cellule fongique", "chitine")]:
        st, f = L.repond("constituant_paroi_cellulaire", ent)
        check(f"ancre constituant_paroi_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── sexe_caryotype_humain : caryotype -> sexe (définitionnel ; filon CURÉ) ──────────────────────────────
if "sexe_caryotype_humain" in L.LECTEUR.tables:
    for ent, att in [("XX", "féminin"), ("XY", "masculin")]:
        st, f = L.repond("sexe_caryotype_humain", ent)
        check(f"ancre sexe_caryotype_humain({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_pigment_biologique : pigment -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_pigment_biologique" in L.LECTEUR.tables:
    for ent, att in [("chlorophylle", "absorption de la lumière pour la photosynthèse"),
                     ("mélanine", "protection contre les rayons ultraviolets"),
                     ("hémoglobine", "transport de l'oxygène")]:
        st, f = L.repond("role_pigment_biologique", ent)
        check(f"ancre role_pigment_biologique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── organite_processus : processus -> organite (fonctionnel ; filon CURÉ) ───────────────────────────────
if "organite_processus" in L.LECTEUR.tables:
    for ent, att in [("photosynthèse", "chloroplaste"), ("respiration cellulaire", "mitochondrie"),
                     ("synthèse des protéines", "ribosome")]:
        st, f = L.repond("organite_processus", ent)
        check(f"ancre organite_processus({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_reproduction : mode -> caractère (définitionnel ; filon CURÉ) ─────────────────────────────
if "caractere_reproduction" in L.LECTEUR.tables:
    for ent, att in [("reproduction sexuée", "deux parents et brassage génétique"),
                     ("reproduction asexuée", "un seul parent et descendants identiques")]:
        st, f = L.repond("caractere_reproduction", ent)
        check(f"ancre caractere_reproduction({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_structure_locomotion_cellulaire : structure -> rôle (fonctionnel ; filon CURÉ) ─────────────────
if "role_structure_locomotion_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("flagelle", "propulsion de la cellule"),
                     ("pseudopode", "déplacement par reptation")]:
        st, f = L.repond("role_structure_locomotion_cellulaire", ent)
        check(f"ancre role_structure_locomotion_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── effet_classe_medicament : classe -> effet (fonctionnel ; filon CURÉ) ────────────────────────────────
if "effet_classe_medicament" in L.LECTEUR.tables:
    for ent, att in [("antalgique", "soulagement de la douleur"),
                     ("antibiotique", "destruction des bactéries"),
                     ("anticoagulant", "fluidification du sang")]:
        st, f = L.repond("effet_classe_medicament", ent)
        check(f"ancre effet_classe_medicament({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── mode_acquisition_immunite : immunité acquise -> mode (définitionnel ; filon CURÉ) ──────────────────
if "mode_acquisition_immunite" in L.LECTEUR.tables:
    for ent, att in [("immunité active", "production d'anticorps par l'organisme"),
                     ("immunité passive", "réception d'anticorps produits par un autre organisme")]:
        st, f = L.repond("mode_acquisition_immunite", ent)
        check(f"ancre mode_acquisition_immunite({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── composition_vaccin : type de vaccin -> antigène (définitionnel ; filon CURÉ) ────────────────────────
if "composition_vaccin" in L.LECTEUR.tables:
    for ent, att in [("vaccin vivant atténué", "agent infectieux vivant affaibli"),
                     ("vaccin inactivé", "agent infectieux tué"),
                     ("vaccin à ARN messager", "ARN codant un antigène")]:
        st, f = L.repond("composition_vaccin", ent)
        check(f"ancre composition_vaccin({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── milieu_respiration : organe respiratoire -> milieu (définitionnel ; filon CURÉ) ─────────────────────
if "milieu_respiration" in L.LECTEUR.tables:
    for ent, att in [("branchies", "milieu aquatique"), ("poumons", "milieu aérien")]:
        st, f = L.repond("milieu_respiration", ent)
        check(f"ancre milieu_respiration({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── nombre_carbone_ose : ose -> nombre de carbones (définitionnel ; filon CURÉ) ─────────────────────────
if "nombre_carbone_ose" in L.LECTEUR.tables:
    for ent, att in [("triose", "3"), ("pentose", "5"), ("hexose", "6")]:
        st, f = L.repond("nombre_carbone_ose", ent)
        check(f"ancre nombre_carbone_ose({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── liaison_polymere : macromolécule -> liaison (définitionnel ; filon CURÉ) ────────────────────────────
if "liaison_polymere" in L.LECTEUR.tables:
    for ent, att in [("protéine", "liaison peptidique"),
                     ("polysaccharide", "liaison glycosidique"),
                     ("acide nucléique", "liaison phosphodiester")]:
        st, f = L.repond("liaison_polymere", ent)
        check(f"ancre liaison_polymere({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_structure_proteine : niveau -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_structure_proteine" in L.LECTEUR.tables:
    for ent, att in [("structure primaire", "séquence des acides aminés"),
                     ("structure quaternaire", "assemblage de plusieurs chaînes")]:
        st, f = L.repond("definition_structure_proteine", ent)
        check(f"ancre definition_structure_proteine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── elements_biomolecule : biomolécule -> éléments (définitionnel ; filon CURÉ) ─────────────────────────
if "elements_biomolecule" in L.LECTEUR.tables:
    for ent, att in [("glucide", "carbone, hydrogène, oxygène"),
                     ("protéine", "carbone, hydrogène, oxygène, azote"),
                     ("acide nucléique", "carbone, hydrogène, oxygène, azote, phosphore")]:
        st, f = L.repond("elements_biomolecule", ent)
        check(f"ancre elements_biomolecule({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_genetique : terme -> définition (définitionnel ; filon CURÉ) ──────────────────────
if "definition_terme_genetique" in L.LECTEUR.tables:
    for ent, att in [("génotype", "ensemble des allèles d'un individu"),
                     ("phénotype", "ensemble des caractères observables"),
                     ("allèle", "version d'un gène")]:
        st, f = L.repond("definition_terme_genetique", ent)
        check(f"ancre definition_terme_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── expression_allele : allèle -> expression (définitionnel ; filon CURÉ) ───────────────────────────────
if "expression_allele" in L.LECTEUR.tables:
    for ent, att in [("allèle dominant", "s'exprime même à l'état hétérozygote"),
                     ("allèle récessif", "s'exprime seulement à l'état homozygote")]:
        st, f = L.repond("expression_allele", ent)
        check(f"ancre expression_allele({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── ploidie_cellule : cellule -> ploïdie (définitionnel ; filon CURÉ) ───────────────────────────────────
if "ploidie_cellule" in L.LECTEUR.tables:
    for ent, att in [("gamète", "haploïde"), ("cellule somatique", "diploïde")]:
        st, f = L.repond("ploidie_cellule", ent)
        check(f"ancre ploidie_cellule({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── evenement_phase_mitose : phase -> événement (définitionnel ; filon CURÉ) ────────────────────────────
if "evenement_phase_mitose" in L.LECTEUR.tables:
    for ent, att in [("prophase", "condensation des chromosomes"),
                     ("anaphase", "séparation des chromatides sœurs")]:
        st, f = L.repond("evenement_phase_mitose", ent)
        check(f"ancre evenement_phase_mitose({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── bilan_photosynthese : côté -> substances (définitionnel ; filon CURÉ) ───────────────────────────────
if "bilan_photosynthese" in L.LECTEUR.tables:
    for ent, att in [("réactifs de la photosynthèse", "dioxyde de carbone et eau"),
                     ("produits de la photosynthèse", "glucose et dioxygène")]:
        st, f = L.repond("bilan_photosynthese", ent)
        check(f"ancre bilan_photosynthese({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── gaz_respiration : phase -> gaz (définitionnel ; filon CURÉ) ─────────────────────────────────────────
if "gaz_respiration" in L.LECTEUR.tables:
    for ent, att in [("inspiration", "apport de dioxygène"),
                     ("expiration", "rejet de dioxyde de carbone")]:
        st, f = L.repond("gaz_respiration", ent)
        check(f"ancre gaz_respiration({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_ecologie : terme -> définition (définitionnel ; filon CURÉ) ────────────────────────
if "definition_terme_ecologie" in L.LECTEUR.tables:
    for ent, att in [("habitat", "lieu de vie d'une espèce"),
                     ("biotope", "milieu physique d'un écosystème"),
                     ("biocénose", "ensemble des êtres vivants d'un écosystème")]:
        st, f = L.repond("definition_terme_ecologie", ent)
        check(f"ancre definition_terme_ecologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_niveau_prevention : niveau -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_niveau_prevention" in L.LECTEUR.tables:
    for ent, att in [("prévention primaire", "éviter l'apparition de la maladie"),
                     ("prévention tertiaire", "limiter les complications de la maladie")]:
        st, f = L.repond("definition_niveau_prevention", ent)
        check(f"ancre definition_niveau_prevention({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_constituant_os : constituant -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_constituant_os" in L.LECTEUR.tables:
    for ent, att in [("os compact", "résistance mécanique"),
                     ("moelle osseuse rouge", "production des cellules sanguines")]:
        st, f = L.repond("role_constituant_os", ent)
        check(f"ancre role_constituant_os({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_dent : partie -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────────
if "role_partie_dent" in L.LECTEUR.tables:
    for ent, att in [("émail", "protection de la dent"), ("pulpe dentaire", "vascularisation et innervation")]:
        st, f = L.repond("role_partie_dent", ent)
        check(f"ancre role_partie_dent({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_couche_peau : couche -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────────
if "role_couche_peau" in L.LECTEUR.tables:
    for ent, att in [("épiderme", "protection"), ("derme", "soutien et sensibilité")]:
        st, f = L.repond("role_couche_peau", ent)
        check(f"ancre role_couche_peau({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_graine : partie -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────────
if "role_partie_graine" in L.LECTEUR.tables:
    for ent, att in [("tégument", "protection de la graine"), ("cotylédon", "réserve nutritive")]:
        st, f = L.repond("role_partie_graine", ent)
        check(f"ancre role_partie_graine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_mecanisme_evolution : mécanisme -> définition (définitionnel ; filon CURÉ) ──────────────
if "definition_mecanisme_evolution" in L.LECTEUR.tables:
    for ent, att in [("sélection naturelle", "tri des individus les mieux adaptés à leur milieu"),
                     ("dérive génétique", "variation aléatoire des fréquences alléliques")]:
        st, f = L.repond("definition_mecanisme_evolution", ent)
        check(f"ancre definition_mecanisme_evolution({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_virus : constituant -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────
if "role_partie_virus" in L.LECTEUR.tables:
    for ent, att in [("capside", "protection du matériel génétique"),
                     ("génome viral", "information génétique du virus")]:
        st, f = L.repond("role_partie_virus", ent)
        check(f"ancre role_partie_virus({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_immunologie : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_immunologie" in L.LECTEUR.tables:
    for ent, att in [("antigène", "substance étrangère reconnue par le système immunitaire"),
                     ("anticorps", "protéine qui neutralise un antigène")]:
        st, f = L.repond("definition_terme_immunologie", ent)
        check(f"ancre definition_terme_immunologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_cycle_viral : cycle -> caractère (définitionnel ; filon CURÉ) ─────────────────────────────
if "caractere_cycle_viral" in L.LECTEUR.tables:
    for ent, att in [("cycle lytique", "destruction de la cellule hôte"),
                     ("cycle lysogénique", "intégration du génome viral dans la cellule hôte")]:
        st, f = L.repond("caractere_cycle_viral", ent)
        check(f"ancre caractere_cycle_viral({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_rein : structure -> rôle (fonctionnel ; filon CURÉ) ─────────────────────────────────────
if "role_partie_rein" in L.LECTEUR.tables:
    for ent, att in [("glomérule", "filtration du sang"),
                     ("néphron", "unité fonctionnelle de filtration")]:
        st, f = L.repond("role_partie_rein", ent)
        check(f"ancre role_partie_rein({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_poumon : structure -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_partie_poumon" in L.LECTEUR.tables:
    for ent, att in [("alvéole pulmonaire", "échanges gazeux"), ("bronche", "conduction de l'air")]:
        st, f = L.repond("role_partie_poumon", ent)
        check(f"ancre role_partie_poumon({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_coeur : structure -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────
if "role_partie_coeur" in L.LECTEUR.tables:
    for ent, att in [("oreillette", "réception du sang"), ("ventricule", "éjection du sang")]:
        st, f = L.repond("role_partie_coeur", ent)
        check(f"ancre role_partie_coeur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_cellulaire : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("cellule", "unité de base des êtres vivants"),
                     ("cytoplasme", "milieu interne de la cellule")]:
        st, f = L.repond("definition_terme_cellulaire", ent)
        check(f"ancre definition_terme_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_classe_lipide : classe -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────────
if "role_classe_lipide" in L.LECTEUR.tables:
    for ent, att in [("triglycéride", "réserve d'énergie"),
                     ("phospholipide", "constituant des membranes cellulaires")]:
        st, f = L.repond("role_classe_lipide", ent)
        check(f"ancre role_classe_lipide({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_botanique : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_botanique" in L.LECTEUR.tables:
    for ent, att in [("photosynthèse", "production de matière organique à partir de la lumière"),
                     ("transpiration", "perte d'eau par les feuilles")]:
        st, f = L.repond("definition_terme_botanique", ent)
        check(f"ancre definition_terme_botanique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_etape_digestion : étape -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_etape_digestion" in L.LECTEUR.tables:
    for ent, att in [("digestion", "transformation des aliments en nutriments"),
                     ("absorption", "passage des nutriments dans le sang")]:
        st, f = L.repond("definition_etape_digestion", ent)
        check(f"ancre definition_etape_digestion({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_physiologie : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_physiologie" in L.LECTEUR.tables:
    for ent, att in [("homéostasie", "maintien de l'équilibre du milieu interne"),
                     ("excrétion", "élimination des déchets de l'organisme")]:
        st, f = L.repond("definition_terme_physiologie", ent)
        check(f"ancre definition_terme_physiologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_evolution : terme -> définition (définitionnel ; filon CURÉ) ──────────────────────
if "definition_terme_evolution" in L.LECTEUR.tables:
    for ent, att in [("espèce", "groupe d'individus interféconds"),
                     ("fossile", "reste ou trace d'un organisme ancien")]:
        st, f = L.repond("definition_terme_evolution", ent)
        check(f"ancre definition_terme_evolution({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── agent_selection : sélection -> agent (définitionnel ; filon CURÉ) ───────────────────────────────────
if "agent_selection" in L.LECTEUR.tables:
    for ent, att in [("sélection naturelle", "milieu naturel"), ("sélection artificielle", "être humain")]:
        st, f = L.repond("agent_selection", ent)
        check(f"ancre agent_selection({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_croisement : croisement -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_croisement" in L.LECTEUR.tables:
    for ent, att in [("croisement monohybride", "portant sur un seul caractère"),
                     ("croisement dihybride", "portant sur deux caractères")]:
        st, f = L.repond("definition_croisement", ent)
        check(f"ancre definition_croisement({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_micro_organisme : micro-organisme -> définition (définitionnel ; filon CURÉ) ─────────────
if "definition_micro_organisme" in L.LECTEUR.tables:
    for ent, att in [("bactérie", "micro-organisme unicellulaire procaryote"),
                     ("virus", "agent infectieux acellulaire")]:
        st, f = L.repond("definition_micro_organisme", ent)
        check(f"ancre definition_micro_organisme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── stimulus_tropisme : tropisme -> stimulus (définitionnel ; filon CURÉ) ───────────────────────────────
if "stimulus_tropisme" in L.LECTEUR.tables:
    for ent, att in [("phototropisme", "lumière"), ("géotropisme", "gravité"), ("hydrotropisme", "eau")]:
        st, f = L.repond("stimulus_tropisme", ent)
        check(f"ancre stimulus_tropisme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── stimulus_taxie : taxie -> stimulus (définitionnel ; filon CURÉ) ─────────────────────────────────────
if "stimulus_taxie" in L.LECTEUR.tables:
    for ent, att in [("phototaxie", "lumière"), ("chimiotaxie", "substances chimiques")]:
        st, f = L.repond("stimulus_taxie", ent)
        check(f"ancre stimulus_taxie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_division_systeme_nerveux : division -> rôle (fonctionnel ; filon CURÉ) ─────────────────────────
if "role_division_systeme_nerveux" in L.LECTEUR.tables:
    for ent, att in [("système nerveux central", "traitement de l'information"),
                     ("système nerveux périphérique", "transmission entre les centres nerveux et les organes")]:
        st, f = L.repond("role_division_systeme_nerveux", ent)
        check(f"ancre role_division_systeme_nerveux({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_sante : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────────
if "definition_terme_sante" in L.LECTEUR.tables:
    for ent, att in [("symptôme", "manifestation d'une maladie"),
                     ("épidémie", "propagation rapide d'une maladie dans une population")]:
        st, f = L.repond("definition_terme_sante", ent)
        check(f"ancre definition_terme_sante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_niveau_organisation_corps : niveau -> définition (définitionnel ; filon CURÉ) ────────────
if "definition_niveau_organisation_corps" in L.LECTEUR.tables:
    for ent, att in [("tissu", "ensemble de cellules semblables"),
                     ("organe", "ensemble de tissus assurant une fonction")]:
        st, f = L.repond("definition_niveau_organisation_corps", ent)
        check(f"ancre definition_niveau_organisation_corps({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organe_reproducteur : organe -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_organe_reproducteur" in L.LECTEUR.tables:
    for ent, att in [("ovaire", "production des ovules"), ("testicule", "production des spermatozoïdes")]:
        st, f = L.repond("role_organe_reproducteur", ent)
        check(f"ancre role_organe_reproducteur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_cellule_reproductrice : cellule -> définition (définitionnel ; filon CURÉ) ───────────────
if "definition_cellule_reproductrice" in L.LECTEUR.tables:
    for ent, att in [("ovule", "gamète femelle"), ("spermatozoïde", "gamète mâle")]:
        st, f = L.repond("definition_cellule_reproductrice", ent)
        check(f"ancre definition_cellule_reproductrice({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_reproduction : terme -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_terme_reproduction" in L.LECTEUR.tables:
    for ent, att in [("fécondation", "union des gamètes mâle et femelle"),
                     ("gestation", "développement de l'embryon dans l'utérus")]:
        st, f = L.repond("definition_terme_reproduction", ent)
        check(f"ancre definition_terme_reproduction({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_hormone_sexuelle : hormone -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────
if "role_hormone_sexuelle" in L.LECTEUR.tables:
    for ent, att in [("testostérone", "développement des caractères sexuels masculins"),
                     ("progestérone", "maintien de la grossesse")]:
        st, f = L.repond("role_hormone_sexuelle", ent)
        check(f"ancre role_hormone_sexuelle({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_caractere_sexuel : type -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_caractere_sexuel" in L.LECTEUR.tables:
    for ent, att in [("caractère sexuel primaire", "organes reproducteurs présents dès la naissance"),
                     ("caractère sexuel secondaire", "caractère apparaissant à la puberté")]:
        st, f = L.repond("definition_caractere_sexuel", ent)
        check(f"ancre definition_caractere_sexuel({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_annexe_embryonnaire : annexe -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_annexe_embryonnaire" in L.LECTEUR.tables:
    for ent, att in [("placenta", "échanges entre la mère et le fœtus"),
                     ("liquide amniotique", "protection du fœtus")]:
        st, f = L.repond("role_annexe_embryonnaire", ent)
        check(f"ancre role_annexe_embryonnaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_developpement : stade -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_terme_developpement" in L.LECTEUR.tables:
    for ent, att in [("embryon", "stade précoce du développement"),
                     ("larve", "stade juvénile chez certains animaux")]:
        st, f = L.repond("definition_terme_developpement", ent)
        check(f"ancre definition_terme_developpement({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── cause_type_diabete : type -> cause (définitionnel ; filon CURÉ) ─────────────────────────────────────
if "cause_type_diabete" in L.LECTEUR.tables:
    for ent, att in [("diabète de type 1", "déficit de production d'insuline"),
                     ("diabète de type 2", "résistance des cellules à l'insuline")]:
        st, f = L.repond("cause_type_diabete", ent)
        check(f"ancre cause_type_diabete({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_pharmacologie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_pharmacologie" in L.LECTEUR.tables:
    for ent, att in [("principe actif", "substance responsable de l'effet thérapeutique"),
                     ("excipient", "substance sans effet thérapeutique")]:
        st, f = L.repond("definition_terme_pharmacologie", ent)
        check(f"ancre definition_terme_pharmacologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_voie_administration : voie -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_voie_administration" in L.LECTEUR.tables:
    for ent, att in [("voie orale", "par la bouche"), ("voie intraveineuse", "dans une veine")]:
        st, f = L.repond("definition_voie_administration", ent)
        check(f"ancre definition_voie_administration({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_gaz_respiratoire : gaz -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────────
if "role_gaz_respiratoire" in L.LECTEUR.tables:
    for ent, att in [("dioxygène", "utilisé par les cellules pour produire de l'énergie"),
                     ("dioxyde de carbone", "déchet de la respiration cellulaire")]:
        st, f = L.repond("role_gaz_respiratoire", ent)
        check(f"ancre role_gaz_respiratoire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_nutrition : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_nutrition" in L.LECTEUR.tables:
    for ent, att in [("nutriment", "substance assimilable issue des aliments"),
                     ("calorie", "unité de mesure de l'énergie")]:
        st, f = L.repond("definition_terme_nutrition", ent)
        check(f"ancre definition_terme_nutrition({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_comportement : terme -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_terme_comportement" in L.LECTEUR.tables:
    for ent, att in [("instinct", "comportement inné"),
                     ("apprentissage", "comportement acquis par l'expérience")]:
        st, f = L.repond("definition_terme_comportement", ent)
        check(f"ancre definition_terme_comportement({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_type_maladie : type -> définition (définitionnel ; filon CURÉ) ───────────────────────────
if "definition_type_maladie" in L.LECTEUR.tables:
    for ent, att in [("maladie infectieuse", "causée par un agent pathogène"),
                     ("maladie carentielle", "due à un manque de nutriment")]:
        st, f = L.repond("definition_type_maladie", ent)
        check(f"ancre definition_type_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_relation_alimentaire : terme -> définition (définitionnel ; filon CURÉ) ────────────
if "definition_terme_relation_alimentaire" in L.LECTEUR.tables:
    for ent, att in [("proie", "organisme mangé par un autre"),
                     ("chaîne alimentaire", "suite d'êtres vivants liés par l'alimentation")]:
        st, f = L.repond("definition_terme_relation_alimentaire", ent)
        check(f"ancre definition_terme_relation_alimentaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_biochimie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────────
if "definition_terme_biochimie" in L.LECTEUR.tables:
    for ent, att in [("enzyme", "protéine qui catalyse une réaction chimique"),
                     ("substrat", "molécule transformée par une enzyme")]:
        st, f = L.repond("definition_terme_biochimie", ent)
        check(f"ancre definition_terme_biochimie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_groupe_animal : groupe -> définition (définitionnel ; filon CURÉ) ────────────────────────
if "definition_groupe_animal" in L.LECTEUR.tables:
    for ent, att in [("vertébré", "animal pourvu d'une colonne vertébrale"),
                     ("mammifère", "vertébré qui allaite ses petits")]:
        st, f = L.repond("definition_groupe_animal", ent)
        check(f"ancre definition_groupe_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_groupe_vegetal : groupe -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_groupe_vegetal" in L.LECTEUR.tables:
    for ent, att in [("angiosperme", "plante à fleurs et à fruits"),
                     ("gymnosperme", "plante à graines nues")]:
        st, f = L.repond("definition_groupe_vegetal", ent)
        check(f"ancre definition_groupe_vegetal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_reponse_immunitaire : réponse -> médiateur (définitionnel ; filon CURÉ) ──────────────────
if "caractere_reponse_immunitaire" in L.LECTEUR.tables:
    for ent, att in [("réponse humorale", "médiée par les anticorps"),
                     ("réponse cellulaire", "médiée par les lymphocytes T")]:
        st, f = L.repond("caractere_reponse_immunitaire", ent)
        check(f"ancre caractere_reponse_immunitaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_etape_expression_genetique : étape -> définition (définitionnel ; filon CURÉ) ────────────
if "definition_etape_expression_genetique" in L.LECTEUR.tables:
    for ent, att in [("transcription", "synthèse d'ARN à partir de l'ADN"),
                     ("traduction", "synthèse d'une protéine à partir de l'ARN messager")]:
        st, f = L.repond("definition_etape_expression_genetique", ent)
        check(f"ancre definition_etape_expression_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── lieu_etape_expression_genetique : étape -> lieu (définitionnel ; filon CURÉ) ────────────────────────
if "lieu_etape_expression_genetique" in L.LECTEUR.tables:
    for ent, att in [("transcription", "noyau"), ("traduction", "ribosome")]:
        st, f = L.repond("lieu_etape_expression_genetique", ent)
        check(f"ancre lieu_etape_expression_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_cytogenetique : terme -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_terme_cytogenetique" in L.LECTEUR.tables:
    for ent, att in [("chromosome", "molécule d'ADN condensée"),
                     ("caryotype", "ensemble des chromosomes d'une cellule")]:
        st, f = L.repond("definition_terme_cytogenetique", ent)
        check(f"ancre definition_terme_cytogenetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_physiologie_vegetale : terme -> définition (définitionnel ; filon CURÉ) ────────────
if "definition_terme_physiologie_vegetale" in L.LECTEUR.tables:
    for ent, att in [("sève brute", "eau et sels minéraux"),
                     ("stomate", "pore d'échange gazeux des feuilles")]:
        st, f = L.repond("definition_terme_physiologie_vegetale", ent)
        check(f"ancre definition_terme_physiologie_vegetale({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── caractere_fruit_sec : type -> caractère (définitionnel ; filon CURÉ) ────────────────────────────────
if "caractere_fruit_sec" in L.LECTEUR.tables:
    for ent, att in [("fruit sec déhiscent", "s'ouvre à maturité"),
                     ("fruit sec indéhiscent", "reste fermé à maturité")]:
        st, f = L.repond("caractere_fruit_sec", ent)
        check(f"ancre caractere_fruit_sec({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_categorie_organe_plante : catégorie -> rôle (définitionnel ; filon CURÉ) ───────────────────────
if "role_categorie_organe_plante" in L.LECTEUR.tables:
    for ent, att in [("organe végétatif", "nutrition et croissance"),
                     ("organe reproducteur", "reproduction")]:
        st, f = L.repond("role_categorie_organe_plante", ent)
        check(f"ancre role_categorie_organe_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_sang : terme -> définition (définitionnel ; filon CURÉ) ────────────────────────────
if "definition_terme_sang" in L.LECTEUR.tables:
    for ent, att in [("plasma", "partie liquide du sang"),
                     ("hématocrite", "proportion de globules rouges dans le sang")]:
        st, f = L.repond("definition_terme_sang", ent)
        check(f"ancre definition_terme_sang({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_gros_vaisseau : vaisseau -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────
if "role_gros_vaisseau" in L.LECTEUR.tables:
    for ent, att in [("aorte", "distribution du sang oxygéné dans le corps"),
                     ("artère pulmonaire", "transport du sang vers les poumons")]:
        st, f = L.repond("role_gros_vaisseau", ent)
        check(f"ancre role_gros_vaisseau({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_appareil_locomoteur : terme -> définition (définitionnel ; filon CURÉ) ─────────────
if "definition_terme_appareil_locomoteur" in L.LECTEUR.tables:
    for ent, att in [("tendon", "structure reliant un muscle à un os"),
                     ("ligament", "structure reliant deux os")]:
        st, f = L.repond("definition_terme_appareil_locomoteur", ent)
        check(f"ancre definition_terme_appareil_locomoteur({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_excretion : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_excretion" in L.LECTEUR.tables:
    for ent, att in [("urine", "liquide excrété par les reins"), ("urée", "déchet azoté du métabolisme")]:
        st, f = L.repond("definition_terme_excretion", ent)
        check(f"ancre definition_terme_excretion({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── localisation_valve_cardiaque : valve -> localisation (fonctionnel ; filon CURÉ) ─────────────────────
if "localisation_valve_cardiaque" in L.LECTEUR.tables:
    for ent, att in [("valve mitrale", "entre l'oreillette et le ventricule gauche"),
                     ("valve aortique", "à la sortie du ventricule gauche")]:
        st, f = L.repond("localisation_valve_cardiaque", ent)
        check(f"ancre localisation_valve_cardiaque({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_type_dentition : type -> définition (définitionnel ; filon CURÉ) ─────────────────────────
if "definition_type_dentition" in L.LECTEUR.tables:
    for ent, att in [("dentition lactéale", "ensemble des dents de lait"),
                     ("dentition définitive", "ensemble des dents permanentes")]:
        st, f = L.repond("definition_type_dentition", ent)
        check(f"ancre definition_type_dentition({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_neurologie : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_neurologie" in L.LECTEUR.tables:
    for ent, att in [("neurone", "cellule du système nerveux"),
                     ("synapse", "zone de communication entre deux neurones")]:
        st, f = L.repond("definition_terme_neurologie", ent)
        check(f"ancre definition_terme_neurologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_endocrinologie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_endocrinologie" in L.LECTEUR.tables:
    for ent, att in [("hormone", "messager chimique transporté par le sang"),
                     ("organe cible", "organe sur lequel agit une hormone")]:
        st, f = L.repond("definition_terme_endocrinologie", ent)
        check(f"ancre definition_terme_endocrinologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_respiration : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_respiration" in L.LECTEUR.tables:
    for ent, att in [("ventilation", "renouvellement de l'air dans les poumons"),
                     ("hématose", "oxygénation du sang")]:
        st, f = L.repond("definition_terme_respiration", ent)
        check(f"ancre definition_terme_respiration({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_circulation : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_terme_circulation" in L.LECTEUR.tables:
    for ent, att in [("circulation pulmonaire", "circulation entre le cœur et les poumons"),
                     ("pouls", "battement perçu des artères")]:
        st, f = L.repond("definition_terme_circulation", ent)
        check(f"ancre definition_terme_circulation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_digestion : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_digestion" in L.LECTEUR.tables:
    for ent, att in [("digestion mécanique", "fragmentation des aliments"),
                     ("chyme", "bouillie alimentaire issue de l'estomac")]:
        st, f = L.repond("definition_terme_digestion", ent)
        check(f"ancre definition_terme_digestion({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_cellule_immunitaire : cellule -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────
if "role_cellule_immunitaire" in L.LECTEUR.tables:
    for ent, att in [("lymphocyte B", "production des anticorps"),
                     ("phagocyte", "ingestion des agents étrangers")]:
        st, f = L.repond("role_cellule_immunitaire", ent)
        check(f"ancre role_cellule_immunitaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_reproduction_vegetale : terme -> définition (définitionnel ; filon CURÉ) ───────────
if "definition_terme_reproduction_vegetale" in L.LECTEUR.tables:
    for ent, att in [("pollinisation", "transport du pollen"), ("fructification", "formation du fruit")]:
        st, f = L.repond("definition_terme_reproduction_vegetale", ent)
        check(f"ancre definition_terme_reproduction_vegetale({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_hygiene : terme -> définition (définitionnel ; filon CURÉ) ─────────────────────────
if "definition_terme_hygiene" in L.LECTEUR.tables:
    for ent, att in [("asepsie", "absence de micro-organismes"),
                     ("stérilisation", "destruction de tous les micro-organismes")]:
        st, f = L.repond("definition_terme_hygiene", ent)
        check(f"ancre definition_terme_hygiene({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_type_mutation : type -> définition (définitionnel ; filon CURÉ) ──────────────────────────
if "definition_type_mutation" in L.LECTEUR.tables:
    for ent, att in [("mutation ponctuelle", "affecte un seul nucléotide"),
                     ("mutation chromosomique", "affecte la structure ou le nombre de chromosomes")]:
        st, f = L.repond("definition_type_mutation", ent)
        check(f"ancre definition_type_mutation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_biodiversite : terme -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_terme_biodiversite" in L.LECTEUR.tables:
    for ent, att in [("biodiversité", "variété des êtres vivants"),
                     ("espèce endémique", "espèce présente dans une seule région")]:
        st, f = L.repond("definition_terme_biodiversite", ent)
        check(f"ancre definition_terme_biodiversite({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_zygotie : état -> définition (définitionnel ; filon CURÉ) ─────────────────────────────────
if "definition_zygotie" in L.LECTEUR.tables:
    for ent, att in [("homozygote", "deux allèles identiques pour un gène"),
                     ("hétérozygote", "deux allèles différents pour un gène")]:
        st, f = L.repond("definition_zygotie", ent)
        check(f"ancre definition_zygotie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_oncologie : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_oncologie" in L.LECTEUR.tables:
    for ent, att in [("tumeur maligne", "tumeur cancéreuse"),
                     ("métastase", "propagation d'un cancer à distance")]:
        st, f = L.repond("definition_terme_oncologie", ent)
        check(f"ancre definition_terme_oncologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_type_chromosome : type -> définition (définitionnel ; filon CURÉ) ────────────────────────
if "definition_type_chromosome" in L.LECTEUR.tables:
    for ent, att in [("autosome", "chromosome non sexuel"),
                     ("chromosome sexuel", "chromosome déterminant le sexe")]:
        st, f = L.repond("definition_type_chromosome", ent)
        check(f"ancre definition_type_chromosome({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_immunite_pratique : terme -> définition (définitionnel ; filon CURÉ) ───────────────
if "definition_terme_immunite_pratique" in L.LECTEUR.tables:
    for ent, att in [("vaccination", "injection préventive stimulant l'immunité"),
                     ("allergie", "réaction excessive du système immunitaire")]:
        st, f = L.repond("definition_terme_immunite_pratique", ent)
        check(f"ancre definition_terme_immunite_pratique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_biotechnologie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_biotechnologie" in L.LECTEUR.tables:
    for ent, att in [("OGM", "organisme génétiquement modifié"),
                     ("clonage", "production d'individus génétiquement identiques")]:
        st, f = L.repond("definition_terme_biotechnologie", ent)
        check(f"ancre definition_terme_biotechnologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_systematique : terme -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_terme_systematique" in L.LECTEUR.tables:
    for ent, att in [("taxon", "groupe d'organismes classés ensemble"),
                     ("nomenclature binominale", "système de nommage à deux termes")]:
        st, f = L.repond("definition_terme_systematique", ent)
        check(f"ancre definition_terme_systematique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_parasitologie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_parasitologie" in L.LECTEUR.tables:
    for ent, att in [("parasite", "organisme vivant aux dépens d'un autre"),
                     ("hôte", "organisme hébergeant un parasite")]:
        st, f = L.repond("definition_terme_parasitologie", ent)
        check(f"ancre definition_terme_parasitologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_epidemiologie : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_epidemiologie" in L.LECTEUR.tables:
    for ent, att in [("pandémie", "épidémie à l'échelle mondiale"),
                     ("incidence", "nombre de nouveaux cas d'une maladie")]:
        st, f = L.repond("definition_terme_epidemiologie", ent)
        check(f"ancre definition_terme_epidemiologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_glande_endocrine : glande -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_glande_endocrine" in L.LECTEUR.tables:
    for ent, att in [("hypophyse", "commande des autres glandes endocrines"),
                     ("thyroïde", "régulation du métabolisme")]:
        st, f = L.repond("role_glande_endocrine", ent)
        check(f"ancre role_glande_endocrine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_systeme_nerveux_fonctionnel : division -> rôle (fonctionnel ; filon CURÉ) ──────────────────────
if "role_systeme_nerveux_fonctionnel" in L.LECTEUR.tables:
    for ent, att in [("système nerveux somatique", "contrôle des mouvements volontaires"),
                     ("système nerveux autonome", "contrôle des fonctions involontaires")]:
        st, f = L.repond("role_systeme_nerveux_fonctionnel", ent)
        check(f"ancre role_systeme_nerveux_fonctionnel({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_sn_autonome : branche -> rôle (définitionnel ; filon CURÉ) ─────────────────────────────────────
if "role_sn_autonome" in L.LECTEUR.tables:
    for ent, att in [("système nerveux sympathique", "préparation à l'action"),
                     ("système nerveux parasympathique", "favorise le repos et la digestion")]:
        st, f = L.repond("role_sn_autonome", ent)
        check(f"ancre role_sn_autonome({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_transport_membranaire : mode -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_transport_membranaire" in L.LECTEUR.tables:
    for ent, att in [("osmose", "diffusion de l'eau à travers une membrane"),
                     ("transport actif", "passage contre le gradient avec dépense d'énergie")]:
        st, f = L.repond("definition_transport_membranaire", ent)
        check(f"ancre definition_transport_membranaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_thermoregulation : type -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_thermoregulation" in L.LECTEUR.tables:
    for ent, att in [("homéotherme", "température corporelle constante"),
                     ("poïkilotherme", "température corporelle variable selon le milieu")]:
        st, f = L.repond("definition_thermoregulation", ent)
        check(f"ancre definition_thermoregulation({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_sens : sens -> perception (définitionnel ; filon CURÉ) ───────────────────────────────────
if "definition_sens" in L.LECTEUR.tables:
    for ent, att in [("vue", "perception de la lumière"), ("ouïe", "perception des sons"),
                     ("goût", "perception des saveurs")]:
        st, f = L.repond("definition_sens", ent)
        check(f"ancre definition_sens({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organite_supplementaire : organite -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────
if "role_organite_supplementaire" in L.LECTEUR.tables:
    for ent, att in [("vacuole", "stockage et maintien de la turgescence"),
                     ("centriole", "organisation de la division cellulaire")]:
        st, f = L.repond("role_organite_supplementaire", ent)
        check(f"ancre role_organite_supplementaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_systeme_urinaire : organe -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────
if "role_partie_systeme_urinaire" in L.LECTEUR.tables:
    for ent, att in [("uretère", "transport de l'urine vers la vessie"), ("vessie", "stockage de l'urine")]:
        st, f = L.repond("role_partie_systeme_urinaire", ent)
        check(f"ancre role_partie_systeme_urinaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organe_respiratoire : organe -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────
if "role_organe_respiratoire" in L.LECTEUR.tables:
    for ent, att in [("nez", "filtration et réchauffement de l'air"), ("trachée", "conduction de l'air")]:
        st, f = L.repond("role_organe_respiratoire", ent)
        check(f"ancre role_organe_respiratoire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_arc_reflexe : élément -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_terme_arc_reflexe" in L.LECTEUR.tables:
    for ent, att in [("récepteur", "structure qui capte le stimulus"),
                     ("effecteur", "organe qui exécute la réponse")]:
        st, f = L.repond("definition_terme_arc_reflexe", ent)
        check(f"ancre definition_terme_arc_reflexe({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_cycle_vie : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_cycle_vie" in L.LECTEUR.tables:
    for ent, att in [("métamorphose", "transformation profonde au cours du développement"),
                     ("mue", "changement de l'enveloppe externe")]:
        st, f = L.repond("definition_terme_cycle_vie", ent)
        check(f"ancre definition_terme_cycle_vie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_brassage_genetique : type -> définition (définitionnel ; filon CURÉ) ─────────────────────
if "definition_brassage_genetique" in L.LECTEUR.tables:
    for ent, att in [("brassage interchromosomique", "répartition aléatoire des chromosomes"),
                     ("brassage intrachromosomique", "échange de segments par crossing-over")]:
        st, f = L.repond("definition_brassage_genetique", ent)
        check(f"ancre definition_brassage_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_partie_squelette : partie -> contenu (définitionnel ; filon CURÉ) ────────────────────────
if "definition_partie_squelette" in L.LECTEUR.tables:
    for ent, att in [("squelette axial", "crâne, colonne vertébrale et cage thoracique"),
                     ("squelette appendiculaire", "membres et leurs ceintures")]:
        st, f = L.repond("definition_partie_squelette", ent)
        check(f"ancre definition_partie_squelette({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_regime_alimentaire : régime -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_regime_alimentaire" in L.LECTEUR.tables:
    for ent, att in [("herbivore", "se nourrit de végétaux"), ("carnivore", "se nourrit d'animaux")]:
        st, f = L.repond("definition_regime_alimentaire", ent)
        check(f"ancre definition_regime_alimentaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_segment_digestif : segment -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────
if "role_segment_digestif" in L.LECTEUR.tables:
    for ent, att in [("bouche", "mastication et insalivation"),
                     ("œsophage", "transport des aliments vers l'estomac")]:
        st, f = L.repond("role_segment_digestif", ent)
        check(f"ancre role_segment_digestif({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_partie_feuille : partie -> rôle (fonctionnel ; filon CURÉ) ─────────────────────────────────────
if "role_partie_feuille" in L.LECTEUR.tables:
    for ent, att in [("limbe", "surface de photosynthèse"), ("nervure", "conduction de la sève")]:
        st, f = L.repond("role_partie_feuille", ent)
        check(f"ancre role_partie_feuille({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_partie_tige : partie -> définition (définitionnel ; filon CURÉ) ──────────────────────────
if "definition_partie_tige" in L.LECTEUR.tables:
    for ent, att in [("nœud", "point d'insertion des feuilles"),
                     ("bourgeon", "ébauche de rameau ou de fleur")]:
        st, f = L.repond("definition_partie_tige", ent)
        check(f"ancre definition_partie_tige({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── secretion_organe_digestif : organe -> sécrétion (fonctionnel ; filon CURÉ) ──────────────────────────
if "secretion_organe_digestif" in L.LECTEUR.tables:
    for ent, att in [("estomac", "suc gastrique"), ("foie", "bile")]:
        st, f = L.repond("secretion_organe_digestif", ent)
        check(f"ancre secretion_organe_digestif({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_constituant_membrane : constituant -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────
if "role_constituant_membrane" in L.LECTEUR.tables:
    for ent, att in [("phospholipides", "formation de la bicouche"),
                     ("cholestérol", "régulation de la fluidité de la membrane")]:
        st, f = L.repond("role_constituant_membrane", ent)
        check(f"ancre role_constituant_membrane({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_classe_vertebre : classe -> définition (définitionnel ; filon CURÉ) ──────────────────────
if "definition_classe_vertebre" in L.LECTEUR.tables:
    for ent, att in [("poisson", "vertébré aquatique à branchies"),
                     ("mammifère", "vertébré à poils qui allaite ses petits")]:
        st, f = L.repond("definition_classe_vertebre", ent)
        check(f"ancre definition_classe_vertebre({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_groupe_invertebre : groupe -> définition (définitionnel ; filon CURÉ) ────────────────────
if "definition_groupe_invertebre" in L.LECTEUR.tables:
    for ent, att in [("insecte", "arthropode à six pattes"),
                     ("arachnide", "arthropode à huit pattes")]:
        st, f = L.repond("definition_groupe_invertebre", ent)
        check(f"ancre definition_groupe_invertebre({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_ethologie : terme -> définition (définitionnel ; filon CURÉ) ───────────────────────
if "definition_terme_ethologie" in L.LECTEUR.tables:
    for ent, att in [("territoire", "zone défendue par un animal"),
                     ("hibernation", "ralentissement de l'activité pendant l'hiver")]:
        st, f = L.repond("definition_terme_ethologie", ent)
        check(f"ancre definition_terme_ethologie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organe_lymphoide : organe -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_organe_lymphoide" in L.LECTEUR.tables:
    for ent, att in [("ganglion lymphatique", "filtration de la lymphe"),
                     ("thymus", "maturation des lymphocytes T")]:
        st, f = L.repond("role_organe_lymphoide", ent)
        check(f"ancre role_organe_lymphoide({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_annexe_peau : annexe -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────────
if "role_annexe_peau" in L.LECTEUR.tables:
    for ent, att in [("glande sudoripare", "sécrétion de la sueur"),
                     ("glande sébacée", "sécrétion du sébum")]:
        st, f = L.repond("role_annexe_peau", ent)
        check(f"ancre role_annexe_peau({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_systeme_complement : système -> fonction (fonctionnel ; filon CURÉ) ────────────────────────
if "fonction_systeme_complement" in L.LECTEUR.tables:
    for ent, att in [("système lymphatique", "circulation de la lymphe et défense"),
                     ("système musculaire", "mouvement")]:
        st, f = L.repond("fonction_systeme_complement", ent)
        check(f"ancre fonction_systeme_complement({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_liquide_corporel : liquide -> rôle (fonctionnel ; filon CURÉ) ──────────────────────────────────
if "role_liquide_corporel" in L.LECTEUR.tables:
    for ent, att in [("sang", "transport des substances dans l'organisme"),
                     ("liquide céphalorachidien", "protection du système nerveux central")]:
        st, f = L.repond("role_liquide_corporel", ent)
        check(f"ancre role_liquide_corporel({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_pigment_vegetal : pigment -> rôle (fonctionnel ; filon CURÉ) ───────────────────────────────────
if "role_pigment_vegetal" in L.LECTEUR.tables:
    for ent, att in [("chlorophylle", "absorption de la lumière pour la photosynthèse"),
                     ("anthocyane", "pigmentation rouge à bleue")]:
        st, f = L.repond("role_pigment_vegetal", ent)
        check(f"ancre role_pigment_vegetal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_microorganisme_alimentaire : micro-organisme -> usage (fonctionnel ; filon CURÉ) ───────────────
if "role_microorganisme_alimentaire" in L.LECTEUR.tables:
    for ent, att in [("levure", "fabrication du pain et de la bière"),
                     ("bactérie lactique", "fabrication du yaourt")]:
        st, f = L.repond("role_microorganisme_alimentaire", ent)
        check(f"ancre role_microorganisme_alimentaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_structure_adn : terme -> définition (définitionnel ; filon CURÉ) ───────────────────
if "definition_terme_structure_adn" in L.LECTEUR.tables:
    for ent, att in [("nucléotide", "unité de base des acides nucléiques"),
                     ("double hélice", "structure en spirale de l'ADN")]:
        st, f = L.repond("definition_terme_structure_adn", ent)
        check(f"ancre definition_terme_structure_adn({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_etape_cycle_cellulaire : étape -> définition (définitionnel ; filon CURÉ) ────────────────
if "definition_etape_cycle_cellulaire" in L.LECTEUR.tables:
    for ent, att in [("interphase", "phase de croissance et de réplication de l'ADN"),
                     ("cytocinèse", "division du cytoplasme")]:
        st, f = L.repond("definition_etape_cycle_cellulaire", ent)
        check(f"ancre definition_etape_cycle_cellulaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_physiologie_effort : terme -> définition (définitionnel ; filon CURÉ) ──────────────
if "definition_terme_physiologie_effort" in L.LECTEUR.tables:
    for ent, att in [("fréquence cardiaque", "nombre de battements du cœur par minute"),
                     ("VO2 max", "consommation maximale d'oxygène")]:
        st, f = L.repond("definition_terme_physiologie_effort", ent)
        check(f"ancre definition_terme_physiologie_effort({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_nutrition_sante : terme -> définition (définitionnel ; filon CURÉ) ─────────────────
if "definition_terme_nutrition_sante" in L.LECTEUR.tables:
    for ent, att in [("malnutrition", "déséquilibre alimentaire"), ("obésité", "excès de masse grasse")]:
        st, f = L.repond("definition_terme_nutrition_sante", ent)
        check(f"ancre definition_terme_nutrition_sante({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_microbiologie_culture : terme -> définition (définitionnel ; filon CURÉ) ───────────
if "definition_terme_microbiologie_culture" in L.LECTEUR.tables:
    for ent, att in [("colonie", "amas de micro-organismes issus d'une seule cellule"),
                     ("souche", "lignée d'un micro-organisme")]:
        st, f = L.repond("definition_terme_microbiologie_culture", ent)
        check(f"ancre definition_terme_microbiologie_culture({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_etape_formation_urine : étape -> définition (définitionnel ; filon CURÉ) ─────────────────
if "definition_etape_formation_urine" in L.LECTEUR.tables:
    for ent, att in [("filtration glomérulaire", "passage du plasma dans le néphron"),
                     ("réabsorption", "récupération de substances utiles vers le sang")]:
        st, f = L.repond("definition_etape_formation_urine", ent)
        check(f"ancre definition_etape_formation_urine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_organe_systeme_nerveux_central : organe -> rôle (fonctionnel ; filon CURÉ) ─────────────────────
if "role_organe_systeme_nerveux_central" in L.LECTEUR.tables:
    for ent, att in [("cerveau", "centre du traitement de l'information"),
                     ("moelle épinière", "transmission des messages nerveux et réflexes")]:
        st, f = L.repond("role_organe_systeme_nerveux_central", ent)
        check(f"ancre role_organe_systeme_nerveux_central({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_technique_genetique : technique -> définition (définitionnel ; filon CURÉ) ───────────────
if "definition_technique_genetique" in L.LECTEUR.tables:
    for ent, att in [("séquençage", "détermination de l'ordre des nucléotides"),
                     ("PCR", "amplification de l'ADN")]:
        st, f = L.repond("definition_technique_genetique", ent)
        check(f"ancre definition_technique_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_evolution_preuve : terme -> définition (définitionnel ; filon CURÉ) ────────────────
if "definition_terme_evolution_preuve" in L.LECTEUR.tables:
    for ent, att in [("homologie", "ressemblance due à une origine commune"),
                     ("analogie", "ressemblance due à une fonction commune")]:
        st, f = L.repond("definition_terme_evolution_preuve", ent)
        check(f"ancre definition_terme_evolution_preuve({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_categorie_aliment : catégorie -> rôle (définitionnel ; filon CURÉ) ───────────────────────
if "definition_categorie_aliment" in L.LECTEUR.tables:
    for ent, att in [("aliment énergétique", "fournit de l'énergie"),
                     ("aliment bâtisseur", "construit et renouvelle les tissus")]:
        st, f = L.repond("definition_categorie_aliment", ent)
        check(f"ancre definition_categorie_aliment({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_multiplication_vegetative : mode -> définition (définitionnel ; filon CURÉ) ──────────────
if "definition_multiplication_vegetative" in L.LECTEUR.tables:
    for ent, att in [("bouturage", "nouvelle plante à partir d'un fragment"),
                     ("greffage", "union de deux plantes")]:
        st, f = L.repond("definition_multiplication_vegetative", ent)
        check(f"ancre definition_multiplication_vegetative({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_anomalie_chromosomique : anomalie -> définition (définitionnel ; filon CURÉ) ─────────────
if "definition_anomalie_chromosomique" in L.LECTEUR.tables:
    for ent, att in [("trisomie", "présence d'un chromosome surnuméraire"),
                     ("monosomie", "absence d'un chromosome")]:
        st, f = L.repond("definition_anomalie_chromosomique", ent)
        check(f"ancre definition_anomalie_chromosomique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── role_type_dent : type -> rôle (fonctionnel ; filon CURÉ) ────────────────────────────────────────────
if "role_type_dent" in L.LECTEUR.tables:
    for ent, att in [("incisive", "couper les aliments"), ("molaire", "broyer")]:
        st, f = L.repond("role_type_dent", ent)
        check(f"ancre role_type_dent({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_etape_developpement_embryon : étape -> définition (définitionnel ; filon CURÉ) ───────────
if "definition_etape_developpement_embryon" in L.LECTEUR.tables:
    for ent, att in [("segmentation", "divisions de l'œuf fécondé"),
                     ("organogenèse", "formation des organes")]:
        st, f = L.repond("definition_etape_developpement_embryon", ent)
        check(f"ancre definition_etape_developpement_embryon({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_fruit_graine : organe -> origine (définitionnel ; filon CURÉ) ────────────────────────────
if "definition_fruit_graine" in L.LECTEUR.tables:
    for ent, att in [("fruit", "organe issu de la transformation de l'ovaire"),
                     ("graine", "organe issu de l'ovule contenant l'embryon")]:
        st, f = L.repond("definition_fruit_graine", ent)
        check(f"ancre definition_fruit_graine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_categorie_glucide : catégorie -> définition (définitionnel ; filon CURÉ) ─────────────────
if "definition_categorie_glucide" in L.LECTEUR.tables:
    for ent, att in [("ose", "glucide simple"), ("polyoside", "glucide formé de nombreux oses")]:
        st, f = L.repond("definition_categorie_glucide", ent)
        check(f"ancre definition_categorie_glucide({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_acide_gras : type -> définition (définitionnel ; filon CURÉ) ─────────────────────────────
if "definition_acide_gras" in L.LECTEUR.tables:
    for ent, att in [("acide gras saturé", "sans double liaison"),
                     ("acide gras insaturé", "avec au moins une double liaison")]:
        st, f = L.repond("definition_acide_gras", ent)
        check(f"ancre definition_acide_gras({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── definition_terme_code_genetique : terme -> définition (définitionnel ; filon CURÉ) ──────────────────
if "definition_terme_code_genetique" in L.LECTEUR.tables:
    for ent, att in [("codon", "triplet de nucléotides"),
                     ("code génétique", "correspondance entre les codons et les acides aminés")]:
        st, f = L.repond("definition_terme_code_genetique", ent)
        check(f"ancre definition_terme_code_genetique({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_arn_role : type d'ARN -> rôle (filon CURÉ par le modèle) ─────────────────────────────────────
if "type_arn_role" in L.LECTEUR.tables:
    for ent, att in [("ARN messager", "transport de l'information génétique du noyau au ribosome"),
                     ("ARN de transfert", "transport des acides aminés vers le ribosome"),
                     ("ARN ribosomique", "constituant structural du ribosome")]:
        st, f = L.repond("type_arn_role", ent)
        check(f"ancre type_arn_role({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── tissu_animal_fondamental : tissu animal -> rôle (filon CURÉ par le modèle) ────────────────────────
if "tissu_animal_fondamental" in L.LECTEUR.tables:
    for ent, att in [("tissu épithélial", "revêtement et protection des surfaces"),
                     ("tissu musculaire", "contraction"),
                     ("tissu nerveux", "transmission de l'influx nerveux")]:
        st, f = L.repond("tissu_animal_fondamental", ent)
        check(f"ancre tissu_animal_fondamental({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── tissu_vegetal_fonction : tissu végétal -> fonction (filon CURÉ par le modèle) ─────────────────────
if "tissu_vegetal_fonction" in L.LECTEUR.tables:
    for ent, att in [("xylème", "conduction de la sève brute"),
                     ("phloème", "conduction de la sève élaborée"),
                     ("méristème", "croissance par division cellulaire")]:
        st, f = L.repond("tissu_vegetal_fonction", ent)
        check(f"ancre tissu_vegetal_fonction({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── phase_mitose_evenement : phase de mitose -> événement (filon CURÉ par le modèle) ──────────────────
if "phase_mitose_evenement" in L.LECTEUR.tables:
    for ent, att in [("prophase", "condensation des chromosomes"),
                     ("anaphase", "séparation des chromatides soeurs"),
                     ("télophase", "reconstitution des enveloppes nucléaires")]:
        st, f = L.repond("phase_mitose_evenement", ent)
        check(f"ancre phase_mitose_evenement({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── niveau_organisation_vivant : niveau -> définition (filon CURÉ par le modèle) ──────────────────────
if "niveau_organisation_vivant" in L.LECTEUR.tables:
    for ent, att in [("cellule", "unité structurale et fonctionnelle de base du vivant"),
                     ("organe", "ensemble de tissus assurant une fonction"),
                     ("organisme", "être vivant complet")]:
        st, f = L.repond("niveau_organisation_vivant", ent)
        check(f"ancre niveau_organisation_vivant({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_neurone_role : type de neurone -> rôle (filon CURÉ par le modèle) ────────────────────────────
if "type_neurone_role" in L.LECTEUR.tables:
    for ent, att in [("neurone sensitif", "transmission du message nerveux des récepteurs vers le système nerveux central"),
                     ("neurone moteur", "transmission du message nerveux vers les organes effecteurs"),
                     ("interneurone", "connexion entre neurones au sein du système nerveux central")]:
        st, f = L.repond("type_neurone_role", ent)
        check(f"ancre type_neurone_role({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_inflorescence_definition : type d'inflorescence -> définition (filon CURÉ par le modèle) ──────
if "type_inflorescence_definition" in L.LECTEUR.tables:
    for ent, att in [("épi", "inflorescence à fleurs sessiles disposées le long d'un axe allongé"),
                     ("ombelle", "inflorescence dont les pédicelles partent tous d'un même point"),
                     ("capitule", "inflorescence à fleurs sessiles serrées sur un réceptacle élargi")]:
        st, f = L.repond("type_inflorescence_definition", ent)
        check(f"ancre type_inflorescence_definition({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nervation_feuille_definition : nervation foliaire -> définition (filon CURÉ par le modèle) ─────────
if "nervation_feuille_definition" in L.LECTEUR.tables:
    for ent, att in [("nervation pennée", "nervures secondaires partant d'une unique nervure principale"),
                     ("nervation parallèle", "nervures principales parallèles entre elles")]:
        st, f = L.repond("nervation_feuille_definition", ent)
        check(f"ancre nervation_feuille_definition({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── macromolecule_biologique_fonction : macromolécule -> fonction (filon CURÉ par le modèle) ───────────
if "macromolecule_biologique_fonction" in L.LECTEUR.tables:
    for ent, att in [("glucides", "source d'énergie"),
                     ("acides nucléiques", "stockage et transmission de l'information génétique")]:
        st, f = L.repond("macromolecule_biologique_fonction", ent)
        check(f"ancre macromolecule_biologique_fonction({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── regime_alimentaire (approfondissement) : ancres ajoutées run-autonome ─────────────────────────────
if "regime_alimentaire" in L.LECTEUR.tables:
    for ent, att in [("crocodile", "carnivore"), ("chat", "carnivore"), ("âne", "herbivore"),
                     ("renne", "herbivore"), ("caméléon", "insectivore"), ("ours noir", "omnivore")]:
        st, f = L.repond("regime_alimentaire", ent)
        check(f"ancre regime_alimentaire({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_culture_agricole : plante -> catégorie agronomique (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "type_culture_agricole" in L.LECTEUR.tables:
    v = _vals("type_culture_agricole")
    check("type_culture_agricole : ensemble fermé (≤ 8 catégories distinctes)", len(set(v)) <= 8)
    for ent, att in [("blé", "céréale"), ("soja", "légumineuse"), ("tournesol", "oléagineux"),
                     ("coton", "textile"), ("luzerne", "fourragère")]:
        st, f = L.repond("type_culture_agricole", ent)
        check(f"ancre type_culture_agricole({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── forme_feuille_conifere : conifère -> aiguille/écaille (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────
if "forme_feuille_conifere" in L.LECTEUR.tables:
    v = _vals("forme_feuille_conifere")
    check("forme_feuille_conifere : ensemble fermé (≤ 2 formes distinctes)", len(set(v)) <= 2)
    for ent, att in [("pin", "aiguille"), ("sapin", "aiguille"),
                     ("cyprès", "écaille"), ("thuya", "écaille")]:
        st, f = L.repond("forme_feuille_conifere", ent)
        check(f"ancre forme_feuille_conifere({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── position_yeux_animal : animal -> yeux frontaux/latéraux (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "position_yeux_animal" in L.LECTEUR.tables:
    v = _vals("position_yeux_animal")
    check("position_yeux_animal : ensemble fermé (≤ 2 positions distinctes)", len(set(v)) <= 2)
    for ent, att in [("lion", "frontale"), ("hibou", "frontale"),
                     ("lapin", "latérale"), ("cheval", "latérale")]:
        st, f = L.repond("position_yeux_animal", ent)
        check(f"ancre position_yeux_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_algue_couleur : algue -> groupe pigmentaire (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "type_algue_couleur" in L.LECTEUR.tables:
    v = _vals("type_algue_couleur")
    check("type_algue_couleur : ensemble fermé (≤ 3 groupes distincts)", len(set(v)) <= 3)
    for ent, att in [("ulve", "verte"), ("laminaire", "brune"),
                     ("fucus", "brune"), ("porphyra", "rouge")]:
        st, f = L.repond("type_algue_couleur", ent)
        check(f"ancre type_algue_couleur({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── milieu_de_vie_animal : animal -> aquatique/terrestre (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────
if "milieu_de_vie_animal" in L.LECTEUR.tables:
    v = _vals("milieu_de_vie_animal")
    check("milieu_de_vie_animal : ensemble fermé (≤ 2 milieux distincts)", len(set(v)) <= 2)
    for ent, att in [("requin", "aquatique"), ("pieuvre", "aquatique"),
                     ("lion", "terrestre"), ("escargot", "terrestre")]:
        st, f = L.repond("milieu_de_vie_animal", ent)
        check(f"ancre milieu_de_vie_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── mode_deplacement_protozoaire : protozoaire -> locomotion (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────
if "mode_deplacement_protozoaire" in L.LECTEUR.tables:
    v = _vals("mode_deplacement_protozoaire")
    check("mode_deplacement_protozoaire : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("paramécie", "cils"), ("euglène", "flagelle"),
                     ("amibe", "pseudopodes"), ("Entamoeba histolytica", "pseudopodes")]:
        st, f = L.repond("mode_deplacement_protozoaire", ent)
        check(f"ancre mode_deplacement_protozoaire({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_reserve_graine : graine -> réserve dominante (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────
if "type_reserve_graine" in L.LECTEUR.tables:
    v = _vals("type_reserve_graine")
    check("type_reserve_graine : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("blé", "amidon"), ("tournesol", "lipide"),
                     ("soja", "protéine"), ("lentille", "protéine")]:
        st, f = L.repond("type_reserve_graine", ent)
        check(f"ancre type_reserve_graine({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── activite_circadienne_animal : animal -> diurne/nocturne (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "activite_circadienne_animal" in L.LECTEUR.tables:
    v = _vals("activite_circadienne_animal")
    check("activite_circadienne_animal : ensemble fermé (≤ 2 rythmes distincts)", len(set(v)) <= 2)
    for ent, att in [("hibou", "nocturne"), ("chauve-souris", "nocturne"),
                     ("aigle royal", "diurne"), ("abeille", "diurne")]:
        st, f = L.repond("activite_circadienne_animal", ent)
        check(f"ancre activite_circadienne_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── couleur_sang_animal : animal -> couleur du sang (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────
if "couleur_sang_animal" in L.LECTEUR.tables:
    v = _vals("couleur_sang_animal")
    check("couleur_sang_animal : ensemble fermé (≤ 2 couleurs distinctes)", len(set(v)) <= 2)
    for ent, att in [("être humain", "rouge"), ("ver de terre", "rouge"),
                     ("pieuvre", "bleu"), ("homard", "bleu")]:
        st, f = L.repond("couleur_sang_animal", ent)
        check(f"ancre couleur_sang_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── domaine_vivant : organisme -> domaine de Woese (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────
if "domaine_vivant" in L.LECTEUR.tables:
    v = _vals("domaine_vivant")
    check("domaine_vivant : ensemble fermé (≤ 3 domaines distincts)", len(set(v)) <= 3)
    for ent, att in [("Escherichia coli", "bactérie"), ("méthanogène", "archée"),
                     ("être humain", "eucaryote"), ("levure de boulanger", "eucaryote")]:
        st, f = L.repond("domaine_vivant", ent)
        check(f"ancre domaine_vivant({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_digestion_animal : mammifère -> ruminant/monogastrique (ENSEMBLE FERMÉ ; filon CURÉ) ──────────
if "type_digestion_animal" in L.LECTEUR.tables:
    v = _vals("type_digestion_animal")
    check("type_digestion_animal : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("vache", "ruminant"), ("girafe", "ruminant"),
                     ("être humain", "monogastrique"), ("cheval", "monogastrique")]:
        st, f = L.repond("type_digestion_animal", ent)
        check(f"ancre type_digestion_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_dentition_animal : animal -> homodonte/hétérodonte (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "type_dentition_animal" in L.LECTEUR.tables:
    v = _vals("type_dentition_animal")
    check("type_dentition_animal : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("être humain", "hétérodonte"), ("lion", "hétérodonte"),
                     ("crocodile du Nil", "homodonte"), ("dauphin", "homodonte")]:
        st, f = L.repond("type_dentition_animal", ent)
        check(f"ancre type_dentition_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nombre_pattes_animal : animal -> nombre de pattes (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────
if "nombre_pattes_animal" in L.LECTEUR.tables:
    v = _vals("nombre_pattes_animal")
    check("nombre_pattes_animal : ensemble fermé (≤ 5 valeurs distinctes)", len(set(v)) <= 5)
    for ent, att in [("serpent", "0"), ("être humain", "2"), ("lion", "4"),
                     ("abeille", "6"), ("araignée", "8")]:
        st, f = L.repond("nombre_pattes_animal", ent)
        check(f"ancre nombre_pattes_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_oeil_animal : animal -> œil composé/simple (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────
if "type_oeil_animal" in L.LECTEUR.tables:
    v = _vals("type_oeil_animal")
    check("type_oeil_animal : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("mouche", "composé"), ("crabe", "composé"),
                     ("être humain", "simple"), ("pieuvre", "simple")]:
        st, f = L.repond("type_oeil_animal", ent)
        check(f"ancre type_oeil_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nombre_ailes_insecte : insecte -> nombre d'ailes (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "nombre_ailes_insecte" in L.LECTEUR.tables:
    v = _vals("nombre_ailes_insecte")
    check("nombre_ailes_insecte : ensemble fermé (≤ 2 valeurs distinctes)", len(set(v)) <= 2)
    for ent, att in [("mouche", "2"), ("moustique", "2"),
                     ("papillon", "4"), ("abeille", "4")]:
        st, f = L.repond("nombre_ailes_insecte", ent)
        check(f"ancre nombre_ailes_insecte({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_fleur_symetrie : plante -> symétrie florale (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "type_fleur_symetrie" in L.LECTEUR.tables:
    v = _vals("type_fleur_symetrie")
    check("type_fleur_symetrie : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("tulipe", "actinomorphe"), ("coquelicot", "actinomorphe"),
                     ("orchidée", "zygomorphe"), ("pois", "zygomorphe")]:
        st, f = L.repond("type_fleur_symetrie", ent)
        check(f"ancre type_fleur_symetrie({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_coquille_mollusque : mollusque -> type de coquille (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────
if "type_coquille_mollusque" in L.LECTEUR.tables:
    v = _vals("type_coquille_mollusque")
    check("type_coquille_mollusque : ensemble fermé (≤ 4 types distincts)", len(set(v)) <= 4)
    for ent, att in [("escargot", "univalve"), ("moule", "bivalve"),
                     ("seiche", "coquille interne"), ("limace", "sans coquille")]:
        st, f = L.repond("type_coquille_mollusque", ent)
        check(f"ancre type_coquille_mollusque({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_ecaille_poisson : poisson -> type d'écaille (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "type_ecaille_poisson" in L.LECTEUR.tables:
    v = _vals("type_ecaille_poisson")
    check("type_ecaille_poisson : ensemble fermé (≤ 4 types distincts)", len(set(v)) <= 4)
    for ent, att in [("requin", "placoïde"), ("carpe", "cycloïde"),
                     ("perche", "cténoïde"), ("esturgeon", "ganoïde")]:
        st, f = L.repond("type_ecaille_poisson", ent)
        check(f"ancre type_ecaille_poisson({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_excretion_azotee : animal -> déchet azoté (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────
if "type_excretion_azotee" in L.LECTEUR.tables:
    v = _vals("type_excretion_azotee")
    check("type_excretion_azotee : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("poisson", "ammoniac"), ("être humain", "urée"),
                     ("aigle royal", "acide urique"), ("serpent", "acide urique")]:
        st, f = L.repond("type_excretion_azotee", ent)
        check(f"ancre type_excretion_azotee({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_appendice_cephalique : mammifère -> bois/corne/défense (ENSEMBLE FERMÉ ; filon CURÉ) ──────────
if "type_appendice_cephalique" in L.LECTEUR.tables:
    v = _vals("type_appendice_cephalique")
    check("type_appendice_cephalique : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("cerf", "bois"), ("rhinocéros blanc", "corne"),
                     ("éléphant d'Afrique", "défense"), ("morse", "défense")]:
        st, f = L.repond("type_appendice_cephalique", ent)
        check(f"ancre type_appendice_cephalique({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── comportement_migrateur_oiseau : oiseau -> migrateur/sédentaire (ENSEMBLE FERMÉ ; filon CURÉ) ───────
if "comportement_migrateur_oiseau" in L.LECTEUR.tables:
    v = _vals("comportement_migrateur_oiseau")
    check("comportement_migrateur_oiseau : ensemble fermé (≤ 2 comportements distincts)", len(set(v)) <= 2)
    for ent, att in [("hirondelle", "migrateur"), ("cigogne", "migrateur"),
                     ("moineau", "sédentaire"), ("pigeon", "sédentaire")]:
        st, f = L.repond("comportement_migrateur_oiseau", ent)
        check(f"ancre comportement_migrateur_oiseau({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── mode_vie_plante : plante -> cycle de vie (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────────
if "mode_vie_plante" in L.LECTEUR.tables:
    v = _vals("mode_vie_plante")
    check("mode_vie_plante : ensemble fermé (≤ 3 cycles distincts)", len(set(v)) <= 3)
    for ent, att in [("blé", "annuelle"), ("carotte", "bisannuelle"),
                     ("chêne", "vivace"), ("rosier", "vivace")]:
        st, f = L.repond("mode_vie_plante", ent)
        check(f"ancre mode_vie_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── mode_pollinisation_plante : plante -> pollinisation (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────
if "mode_pollinisation_plante" in L.LECTEUR.tables:
    v = _vals("mode_pollinisation_plante")
    check("mode_pollinisation_plante : ensemble fermé (≤ 3 modes distincts)", len(set(v)) <= 3)
    for ent, att in [("blé", "anémogame"), ("chêne", "anémogame"),
                     ("tournesol", "entomogame"), ("lavande", "entomogame")]:
        st, f = L.repond("mode_pollinisation_plante", ent)
        check(f"ancre mode_pollinisation_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── revetement_corps_animal : animal -> tégument (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────────
if "revetement_corps_animal" in L.LECTEUR.tables:
    v = _vals("revetement_corps_animal")
    check("revetement_corps_animal : ensemble fermé (≤ 4 types distincts)", len(set(v)) <= 4)
    for ent, att in [("lion", "poils"), ("aigle royal", "plumes"),
                     ("serpent", "écailles"), ("grenouille", "peau nue")]:
        st, f = L.repond("revetement_corps_animal", ent)
        check(f"ancre revetement_corps_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── os_partie_squelette : os -> axial/appendiculaire (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "os_partie_squelette" in L.LECTEUR.tables:
    v = _vals("os_partie_squelette")
    check("os_partie_squelette : ensemble fermé (≤ 2 parties distinctes)", len(set(v)) <= 2)
    for ent, att in [("crâne", "axial"), ("côte", "axial"),
                     ("fémur", "appendiculaire"), ("clavicule", "appendiculaire")]:
        st, f = L.repond("os_partie_squelette", ent)
        check(f"ancre os_partie_squelette({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── medecin_specialiste_organe : organe -> spécialiste (filon CURÉ) ────────────────────────────────────
if "medecin_specialiste_organe" in L.LECTEUR.tables:
    for ent, att in [("cœur", "cardiologue"), ("peau", "dermatologue"),
                     ("rein", "néphrologue"), ("œil", "ophtalmologue")]:
        st, f = L.repond("medecin_specialiste_organe", ent)
        check(f"ancre medecin_specialiste_organe({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── feuillage_arbre : arbre -> caduc/persistant (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────────
if "feuillage_arbre" in L.LECTEUR.tables:
    v = _vals("feuillage_arbre")
    check("feuillage_arbre : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("chêne", "caduc"), ("mélèze", "caduc"),
                     ("pin", "persistant"), ("houx", "persistant")]:
        st, f = L.repond("feuillage_arbre", ent)
        check(f"ancre feuillage_arbre({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── port_plante : plante -> port (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────────────────────────
if "port_plante" in L.LECTEUR.tables:
    v = _vals("port_plante")
    check("port_plante : ensemble fermé (≤ 4 ports distincts)", len(set(v)) <= 4)
    for ent, att in [("chêne", "arbre"), ("rosier", "arbuste"),
                     ("blé", "herbacée"), ("vigne", "liane")]:
        st, f = L.repond("port_plante", ent)
        check(f"ancre port_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── classe_poisson : poisson -> groupe (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────────────
if "classe_poisson" in L.LECTEUR.tables:
    v = _vals("classe_poisson")
    check("classe_poisson : ensemble fermé (≤ 3 groupes distincts)", len(set(v)) <= 3)
    for ent, att in [("requin", "cartilagineux"), ("raie manta", "cartilagineux"),
                     ("thon rouge", "osseux"), ("lamproie", "agnathe")]:
        st, f = L.repond("classe_poisson", ent)
        check(f"ancre classe_poisson({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── ordre_amphibien : amphibien -> ordre (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────────────────
if "ordre_amphibien" in L.LECTEUR.tables:
    v = _vals("ordre_amphibien")
    check("ordre_amphibien : ensemble fermé (≤ 3 ordres distincts)", len(set(v)) <= 3)
    for ent, att in [("grenouille", "anoure"), ("crapaud", "anoure"),
                     ("salamandre", "urodèle"), ("cécilie", "apode")]:
        st, f = L.repond("ordre_amphibien", ent)
        check(f"ancre ordre_amphibien({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── ordre_oiseau : oiseau -> ordre taxinomique (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────
if "ordre_oiseau" in L.LECTEUR.tables:
    v = _vals("ordre_oiseau")
    check("ordre_oiseau : ensemble fermé (≤ 20 ordres distincts)", len(set(v)) <= 20)
    for ent, att in [("aigle royal", "accipitriforme"), ("moineau", "passériforme"),
                     ("canard", "ansériforme"), ("poule", "galliforme"),
                     ("manchot empereur", "sphénisciforme"), ("autruche", "struthioniforme")]:
        st, f = L.repond("ordre_oiseau", ent)
        check(f"ancre ordre_oiseau({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── ordre_reptile : reptile -> ordre taxinomique (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────
if "ordre_reptile" in L.LECTEUR.tables:
    v = _vals("ordre_reptile")
    check("ordre_reptile : ensemble fermé (≤ 4 ordres distincts)", len(set(v)) <= 4)
    for ent, att in [("serpent", "squamate"), ("iguane", "squamate"),
                     ("tortue marine", "chélonien"), ("crocodile du Nil", "crocodilien")]:
        st, f = L.repond("ordre_reptile", ent)
        check(f"ancre ordre_reptile({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── ordre_mammifere : mammifère -> ordre taxinomique (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────
if "ordre_mammifere" in L.LECTEUR.tables:
    v = _vals("ordre_mammifere")
    check("ordre_mammifere : ensemble fermé (≤ 12 ordres distincts)", len(set(v)) <= 12)
    for ent, att in [("lion", "carnivore"), ("être humain", "primate"), ("baleine bleue", "cétacé"),
                     ("chauve-souris", "chiroptère"), ("lapin", "lagomorphe"), ("cheval", "périssodactyle"),
                     ("vache", "artiodactyle")]:
        st, f = L.repond("ordre_mammifere", ent)
        check(f"ancre ordre_mammifere({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── ordre_insecte : insecte -> ordre taxinomique (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────
if "ordre_insecte" in L.LECTEUR.tables:
    v = _vals("ordre_insecte")
    check("ordre_insecte : ensemble fermé (≤ 10 ordres distincts)", len(set(v)) <= 10)
    for ent, att in [("papillon", "lépidoptère"), ("scarabée", "coléoptère"), ("mouche", "diptère"),
                     ("abeille", "hyménoptère"), ("libellule", "odonate"), ("sauterelle", "orthoptère")]:
        st, f = L.repond("ordre_insecte", ent)
        check(f"ancre ordre_insecte({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── mode_germination_graine : plante -> germination épigée/hypogée (ENSEMBLE FERMÉ ; filon CURÉ) ───────
if "mode_germination_graine" in L.LECTEUR.tables:
    v = _vals("mode_germination_graine")
    check("mode_germination_graine : ensemble fermé (≤ 2 modes distincts)", len(set(v)) <= 2)
    for ent, att in [("haricot", "épigée"), ("tournesol", "épigée"),
                     ("pois", "hypogée"), ("maïs", "hypogée")]:
        st, f = L.repond("mode_germination_graine", ent)
        check(f"ancre mode_germination_graine({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── mode_vie_champignon : champignon -> mode de vie (ENSEMBLE FERMÉ ; filon CURÉ) ──────────────────────
if "mode_vie_champignon" in L.LECTEUR.tables:
    v = _vals("mode_vie_champignon")
    check("mode_vie_champignon : ensemble fermé (≤ 3 modes distincts)", len(set(v)) <= 3)
    for ent, att in [("champignon de Paris", "saprophyte"), ("rouille", "parasite"),
                     ("bolet", "symbiotique"), ("truffe", "symbiotique")]:
        st, f = L.repond("mode_vie_champignon", ent)
        check(f"ancre mode_vie_champignon({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_genome_virus : virus -> ADN/ARN (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────────────
if "type_genome_virus" in L.LECTEUR.tables:
    v = _vals("type_genome_virus")
    check("type_genome_virus : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("virus de la grippe", "ARN"), ("SARS-CoV-2", "ARN"),
                     ("virus de la variole", "ADN"), ("virus de l'hépatite B", "ADN")]:
        st, f = L.repond("type_genome_virus", ent)
        check(f"ancre type_genome_virus({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_aliment_origine : aliment -> origine (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────────────
if "type_aliment_origine" in L.LECTEUR.tables:
    v = _vals("type_aliment_origine")
    check("type_aliment_origine : ensemble fermé (≤ 3 origines distinctes)", len(set(v)) <= 3)
    for ent, att in [("viande", "animale"), ("miel", "animale"),
                     ("pain", "végétale"), ("sel", "minérale")]:
        st, f = L.repond("type_aliment_origine", ent)
        check(f"ancre type_aliment_origine({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_chromosome_humain : chromosome -> autosome/gonosome (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────
if "type_chromosome_humain" in L.LECTEUR.tables:
    v = _vals("type_chromosome_humain")
    check("type_chromosome_humain : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("chromosome 1", "autosome"), ("chromosome 21", "autosome"),
                     ("chromosome X", "gonosome"), ("chromosome Y", "gonosome")]:
        st, f = L.repond("type_chromosome_humain", ent)
        check(f"ancre type_chromosome_humain({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_lipide_classe : lipide -> classe biochimique (ENSEMBLE FERMÉ ; filon CURÉ) ────────────────────
if "type_lipide_classe" in L.LECTEUR.tables:
    v = _vals("type_lipide_classe")
    check("type_lipide_classe : ensemble fermé (≤ 5 classes distinctes)", len(set(v)) <= 5)
    for ent, att in [("triglycéride", "glycéride"), ("lécithine", "phospholipide"),
                     ("cholestérol", "stérol"), ("cire d'abeille", "cire")]:
        st, f = L.repond("type_lipide_classe", ent)
        check(f"ancre type_lipide_classe({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_acide_gras : acide gras -> saturation (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────
if "type_acide_gras" in L.LECTEUR.tables:
    v = _vals("type_acide_gras")
    check("type_acide_gras : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("acide palmitique", "saturé"), ("acide stéarique", "saturé"),
                     ("acide oléique", "insaturé"), ("oméga-3", "insaturé")]:
        st, f = L.repond("type_acide_gras", ent)
        check(f"ancre type_acide_gras({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── forme_proteine : protéine -> forme structurale (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────
if "forme_proteine" in L.LECTEUR.tables:
    v = _vals("forme_proteine")
    check("forme_proteine : ensemble fermé (≤ 2 formes distinctes)", len(set(v)) <= 2)
    for ent, att in [("collagène", "fibreuse"), ("kératine", "fibreuse"),
                     ("hémoglobine", "globulaire"), ("insuline", "globulaire")]:
        st, f = L.repond("forme_proteine", ent)
        check(f"ancre forme_proteine({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── localisation_organe_corps : organe -> région anatomique (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────
if "localisation_organe_corps" in L.LECTEUR.tables:
    v = _vals("localisation_organe_corps")
    check("localisation_organe_corps : ensemble fermé (≤ 5 régions distinctes)", len(set(v)) <= 5)
    for ent, att in [("cerveau", "tête"), ("cœur", "thorax"),
                     ("foie", "abdomen"), ("vessie", "bassin"), ("thyroïde", "cou")]:
        st, f = L.repond("localisation_organe_corps", ent)
        check(f"ancre localisation_organe_corps({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── couleur_pigment_biologique : pigment -> couleur (filon CURÉ) ───────────────────────────────────────
if "couleur_pigment_biologique" in L.LECTEUR.tables:
    for ent, att in [("chlorophylle", "vert"), ("carotène", "orange"),
                     ("mélanine", "noir"), ("hémoglobine", "rouge")]:
        st, f = L.repond("couleur_pigment_biologique", ent)
        check(f"ancre couleur_pigment_biologique({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── nombre_cotyledons_plante : angiosperme -> mono/dicotylédone (ENSEMBLE FERMÉ ; filon CURÉ) ──────────
if "nombre_cotyledons_plante" in L.LECTEUR.tables:
    v = _vals("nombre_cotyledons_plante")
    check("nombre_cotyledons_plante : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("blé", "monocotylédone"), ("palmier", "monocotylédone"),
                     ("haricot", "dicotylédone"), ("chêne", "dicotylédone")]:
        st, f = L.repond("nombre_cotyledons_plante", ent)
        check(f"ancre nombre_cotyledons_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── division_champignon : champignon -> division (ENSEMBLE FERMÉ ; filon CURÉ) ─────────────────────────
if "division_champignon" in L.LECTEUR.tables:
    v = _vals("division_champignon")
    check("division_champignon : ensemble fermé (≤ 3 divisions distinctes)", len(set(v)) <= 3)
    for ent, att in [("bolet", "basidiomycète"), ("champignon de Paris", "basidiomycète"),
                     ("morille", "ascomycète"), ("truffe", "ascomycète")]:
        st, f = L.repond("division_champignon", ent)
        check(f"ancre division_champignon({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── classe_mollusque : mollusque -> classe (ENSEMBLE FERMÉ ; filon CURÉ) ───────────────────────────────
if "classe_mollusque" in L.LECTEUR.tables:
    v = _vals("classe_mollusque")
    check("classe_mollusque : ensemble fermé (≤ 4 classes distinctes)", len(set(v)) <= 4)
    for ent, att in [("escargot", "gastéropode"), ("moule", "bivalve"),
                     ("pieuvre", "céphalopode"), ("nautile", "céphalopode")]:
        st, f = L.repond("classe_mollusque", ent)
        check(f"ancre classe_mollusque({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── type_feuille_plante : plante -> type de feuille (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ────────
if "type_feuille_plante" in L.LECTEUR.tables:
    v = _vals("type_feuille_plante")
    check("type_feuille_plante : ensemble fermé (≤ 2 types distincts)", len(set(v)) <= 2)
    for ent, att in [("chêne", "simple"), ("érable", "simple"),
                     ("frêne", "composée"), ("marronnier", "composée")]:
        st, f = L.repond("type_feuille_plante", ent)
        check(f"ancre type_feuille_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── phyllotaxie_plante : plante -> phyllotaxie (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ─────────────
if "phyllotaxie_plante" in L.LECTEUR.tables:
    v = _vals("phyllotaxie_plante")
    check("phyllotaxie_plante : ensemble fermé (≤ 3 types distincts)", len(set(v)) <= 3)
    for ent, att in [("menthe", "opposée"), ("érable", "opposée"),
                     ("chêne", "alterne"), ("laurier-rose", "verticillée")]:
        st, f = L.repond("phyllotaxie_plante", ent)
        check(f"ancre phyllotaxie_plante({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── organe_plante_fonction : organe végétal -> fonction (filon CURÉ par le modèle) ────────────────────
if "organe_plante_fonction" in L.LECTEUR.tables:
    for ent, att in [("racine", "absorption de l'eau"), ("feuille", "photosynthèse"),
                     ("fleur", "reproduction"), ("tige", "soutien")]:
        st, f = L.repond("organe_plante_fonction", ent)
        check(f"ancre organe_plante_fonction({ent}) == {att}", st == VERIFIE and f.valeur == att)

# ── role_cellule_sanguine : cellule sanguine -> rôle (filon CURÉ par le modèle) ───────────────────────
if "role_cellule_sanguine" in L.LECTEUR.tables:
    for ent, att in [("globule rouge", "transport de l'oxygène"),
                     ("globule blanc", "défense immunitaire"), ("plaquette", "coagulation")]:
        st, f = L.repond("role_cellule_sanguine", ent)
        check(f"ancre role_cellule_sanguine({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── monomere_polymere : polymère biologique -> monomère (filon CURÉ par le modèle) ────────────────────
if "monomere_polymere" in L.LECTEUR.tables:
    v = _vals("monomere_polymere")
    check("monomere_polymere : valeurs non vides (≥6 car.)", all(len(s.strip()) >= 6 for s in v))
    for ent, att in [("protéine", "acide aminé"), ("ADN", "nucléotide"),
                     ("amidon", "glucose"), ("cellulose", "glucose")]:
        st, f = L.repond("monomere_polymere", ent)
        check(f"ancre monomere_polymere({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── fonction_organite : organite -> fonction (filon CURÉ par le modèle) ───────────────────────────────
if "fonction_organite" in L.LECTEUR.tables:
    v = _vals("fonction_organite")
    check("fonction_organite : valeurs non vides (≥5 car.)", all(len(s.strip()) >= 5 for s in v))
    for ent, att in [("mitochondrie", "respiration cellulaire"), ("chloroplaste", "photosynthèse"),
                     ("ribosome", "synthèse des protéines")]:
        st, f = L.repond("fonction_organite", ent)
        check(f"ancre fonction_organite({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── vaccin_maladie : vaccin monovalent -> maladie prévenue (filon CURÉ par le modèle) ─────────────────
if "vaccin_maladie" in L.LECTEUR.tables:
    v = _vals("vaccin_maladie")
    check("vaccin_maladie : valeurs non vides (≥3 car.)", all(len(s.strip()) >= 3 for s in v))
    for ent, att in [("BCG", "tuberculose"), ("vaccin antirabique", "rage"),
                     ("vaccin antitétanique", "tétanos")]:
        st, f = L.repond("vaccin_maladie", ent)
        check(f"ancre vaccin_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── type_microorganisme : agent pathogène -> type (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ─────────
if "type_microorganisme" in L.LECTEUR.tables:
    v = _vals("type_microorganisme")
    check("type_microorganisme : ensemble fermé (≤ 6 types distincts)", len(set(v)) <= 6)
    for ent, att in [("Mycobacterium tuberculosis", "bactérie"), ("SARS-CoV-2", "virus"),
                     ("Plasmodium", "protozoaire"), ("Candida albicans", "champignon"),
                     ("Ascaris lumbricoides", "helminthe"), ("Histoplasma capsulatum", "champignon"),
                     ("Trypanosoma brucei", "protozoaire"), ("Coxiella burnetii", "bactérie")]:
        st, f = L.repond("type_microorganisme", ent)
        check(f"ancre type_microorganisme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── organe_atteint_maladie : maladie -ite -> organe (filon CURÉ par le modèle) ────────────────────────
if "organe_atteint_maladie" in L.LECTEUR.tables:
    v = _vals("organe_atteint_maladie")
    check("organe_atteint_maladie : ≥15 paires curées", len(v) >= 15)
    check("organe_atteint_maladie : valeurs non vides (≥2 car.)", all(len(s.strip()) >= 2 for s in v))
    for ent, att in [("hépatite", "foie"), ("néphrite", "rein"),
                     ("myocardite", "cœur"), ("méningite", "méninges"),
                     ("cholécystite", "vésicule biliaire"), ("glossite", "langue"),
                     ("orchite", "testicule"), ("ostéite", "os")]:
        st, f = L.repond("organe_atteint_maladie", ent)
        check(f"ancre organe_atteint_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── substrat_enzyme : enzyme digestive -> substrat (filon CURÉ par le modèle) ─────────────────────────
if "substrat_enzyme" in L.LECTEUR.tables:
    v = _vals("substrat_enzyme")
    check("substrat_enzyme : valeurs non vides (≥3 car.)", all(len(s.strip()) >= 3 for s in v))
    for ent, att in [("amylase", "amidon"), ("lipase", "lipides"),
                     ("pepsine", "protéines"), ("lactase", "lactose"),
                     ("uréase", "urée"), ("collagénase", "collagène"),
                     ("ribonucléase", "ARN"), ("lysozyme", "peptidoglycane")]:
        st, f = L.repond("substrat_enzyme", ent)
        check(f"ancre substrat_enzyme({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── classe_vertebre_animal : animal -> classe (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ─────────────
if "classe_vertebre_animal" in L.LECTEUR.tables:
    v = _vals("classe_vertebre_animal")
    check("classe_vertebre_animal : ensemble fermé (≤ 5 classes distinctes)", len(set(v)) <= 5)
    check("classe_vertebre_animal : ≥15 paires curées", len(v) >= 15)
    for ent, att in [("dauphin", "mammifère"), ("manchot empereur", "oiseau"),
                     ("crocodile du Nil", "reptile"), ("hippocampe", "poisson"),
                     ("orque", "mammifère"), ("cachalot", "mammifère"), ("lamantin", "mammifère"),
                     ("requin-marteau", "poisson"), ("varan de Komodo", "reptile")]:
        st, f = L.repond("classe_vertebre_animal", ent)
        check(f"ancre classe_vertebre_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── mode_reproduction_animal : animal -> mode (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ─────────────
if "mode_reproduction_animal" in L.LECTEUR.tables:
    v = _vals("mode_reproduction_animal")
    check("mode_reproduction_animal : ensemble fermé (≤ 4 modes distincts)", len(set(v)) <= 4)
    for ent, att in [("poule", "ovipare"), ("ornithorynque", "ovipare"),
                     ("vache", "vivipare"), ("dauphin", "vivipare"),
                     ("vipère", "ovovivipare"), ("grand requin blanc", "ovovivipare"),
                     ("orque", "vivipare"), ("escargot", "ovipare")]:
        st, f = L.repond("mode_reproduction_animal", ent)
        check(f"ancre mode_reproduction_animal({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── regime_alimentaire : animal -> régime (ENSEMBLE FERMÉ ; filon CURÉ par le modèle) ─────────────────
if "regime_alimentaire" in L.LECTEUR.tables:
    v = _vals("regime_alimentaire")
    check("regime_alimentaire : ensemble fermé (≤ 6 régimes distincts)", len(set(v)) <= 6)
    check("regime_alimentaire : ≥18 paires curées", len(v) >= 18)
    for ent, att in [("lion", "carnivore"), ("vache", "herbivore"),
                     ("ours brun", "omnivore"), ("panda géant", "herbivore")]:
        st, f = L.repond("regime_alimentaire", ent)
        check(f"ancre regime_alimentaire({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── vitamine_carence : vitamine -> maladie de carence (filon CURÉ par le modèle) ──────────────────────
if "vitamine_carence" in L.LECTEUR.tables:
    v = _vals("vitamine_carence")
    check("vitamine_carence : valeurs non vides (≥5 car.)", all(len(s.strip()) >= 5 for s in v))
    for ent, att in [("vitamine C", "scorbut"), ("vitamine D", "rachitisme"),
                     ("vitamine B1", "béribéri"), ("vitamine B12", "anémie pernicieuse")]:
        st, f = L.repond("vitamine_carence", ent)
        check(f"ancre vitamine_carence({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── vecteur_maladie : maladie vectorielle -> arthropode vecteur (filon CURÉ par le modèle) ────────────
if "vecteur_maladie" in L.LECTEUR.tables:
    v = _vals("vecteur_maladie")
    check("vecteur_maladie : ≥10 paires curées", len(v) >= 10)
    check("vecteur_maladie : valeurs non vides (≥3 car.)", all(len(s.strip()) >= 3 for s in v))
    for ent, att in [("paludisme", "moustique anophèle"), ("maladie de Lyme", "tique"),
                     ("maladie du sommeil", "mouche tsé-tsé")]:
        st, f = L.repond("vecteur_maladie", ent)
        check(f"ancre vecteur_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── glande_hormone : hormone -> glande/organe sécréteur (filon CURÉ par le modèle) ────────────────────
if "glande_hormone" in L.LECTEUR.tables:
    v = _vals("glande_hormone")
    check("glande_hormone : ≥15 paires curées", len(v) >= 15)
    check("glande_hormone : valeurs non vides (≥4 car.)", all(len(s.strip()) >= 4 for s in v))
    for ent, att in [("insuline", "pancréas"), ("cortisol", "glande surrénale"),
                     ("thyroxine", "glande thyroïde"), ("mélatonine", "glande pinéale"),
                     ("rénine", "rein"), ("ghréline", "estomac"), ("leptine", "tissu adipeux"),
                     ("thyréostimuline", "hypophyse")]:
        st, f = L.repond("glande_hormone", ent)
        check(f"ancre glande_hormone({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── mode_heredite_maladie : maladie -> patron d'hérédité (ENSEMBLE FERMÉ + ANCRES textbook) ───────────
# P1199 hérédité génétique : ensemble fermé (~5 patrons mendéliens/mitochondrial). Ancres = hérédités
# manuel-scolaire vérifiées indépendamment (Huntington=autosomique dominante ; Tay-Sachs/Wilson=autosomique
# récessive ; Hunter/MPS II=récessive liée à l'X). Maladie multi-mode -> HORS.
if "mode_heredite_maladie" in L.LECTEUR.tables:
    v = _vals("mode_heredite_maladie")
    check("mode_heredite_maladie : ensemble fermé (≤ 10 patrons distincts)", len(set(v)) <= 10)
    check("mode_heredite_maladie : valeurs non vides (≥4 car.)", all(len(s.strip()) >= 4 for s in v))
    for ent, att in [("maladie de Huntington", "transmission autosomique dominante"),
                     ("maladie de Tay-Sachs", "transmission autosomique récessive"),
                     ("maladie de Wilson", "transmission autosomique récessive"),
                     ("maladie de Hunter", "transmission récessive liée à l'X")]:
        st, f = L.repond("mode_heredite_maladie", ent)
        check(f"ancre mode_heredite_maladie({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── proteine_du_gene : gène -> produit protéique (vocab OUVERT fonctionnel ; valeurs non vides + ANCRES) ─
# P688 « code pour » : gène -> protéine. Vocab ouvert (≈1-à-1), donc sanité = ancres textbook vérifiées
# indépendamment (ALB->albumine, REN->rénine, LEP->leptine, F8->Facteur VIII, TTR->Transthyrétine,
# APOE->Apolipoprotéine E). Un gène multi-produit est parti en HORS -> une ancre ratée ferait FAIL.
if "proteine_du_gene" in L.LECTEUR.tables:
    v = _vals("proteine_du_gene")
    check("proteine_du_gene : valeurs (produits) non vides (≥2 car.)", all(len(s.strip()) >= 2 for s in v))
    for ent, att in [("DCN", "Décorine"), ("ALB", "albumine humaine"),
                     ("APOE", "Apolipoprotéine E"), ("REN", "rénine"),
                     ("TTR", "Transthyrétine"), ("LEP", "leptine"), ("F8", "Facteur VIII")]:
        st, f = L.repond("proteine_du_gene", ent)
        check(f"ancre proteine_du_gene({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── endemique_de_taxon : taxon -> lieu d'endémisme (valeurs = lieux, ensemble borné + ANCRES) ─────────
# P183 « endémique de » : l'aire de répartition naturelle d'un taxon restreinte à UN lieu. Valeurs = lieux
# (pays/îles/régions) -> ensemble borné. Ancres = endémismes manuel-scolaire vérifiés indépendamment du code
# (ornithorynque/koala/diable de Tasmanie = Australie ; panda géant = Chine ; lémur catta/aye-aye = Madagascar).
if "endemique_de_taxon" in L.LECTEUR.tables:
    v = _vals("endemique_de_taxon")
    check("endemique_de_taxon : valeurs (lieux) non vides (≥2 car.)", all(len(s.strip()) >= 2 for s in v))
    check("endemique_de_taxon : ensemble de lieux borné (≤ 3000 distincts)", len(set(v)) <= 3000)
    for ent, att in [("ornithorynque", "Australie"), ("koala", "Australie"),
                     ("diable de Tasmanie", "Australie"), ("panda géant", "République populaire de Chine"),
                     ("lémur catta", "Madagascar"), ("Aye-aye", "Madagascar")]:
        st, f = L.repond("endemique_de_taxon", ent)
        check(f"ancre endemique_de_taxon({ent}) == {att}", st == VERIFIE and f.valeur == att)


# ── taxon_parent : taxon -> taxon parent (vocabulaire ouvert ; sanité plausible + ANCRES) ────────────
if "taxon_parent" in L.LECTEUR.tables:
    v = _vals("taxon_parent")
    check("taxon_parent : valeurs non vides (≥2 car.)", all(len(s.strip()) >= 2 for s in v))
    # FAUX=0 : un taxon ne peut être son propre parent (auto-référence circulaire = collision de libellé FR
    # entre deux QID distincts). La garde anti_self d'_ingere_geant doit garantir 0 -> on le verrouille ici.
    _self = sum(1 for k, f in L.LECTEUR.tables["taxon_parent"].items()
                if str(k).strip().lower() == str(f.valeur).strip().lower())
    check("taxon_parent : aucune auto-référence (entité == parent)", _self == 0)
    for ent, att in [("Homo sapiens", "Homo"), ("souris domestique", "Mus"), ("lion", "Panthera")]:
        st, f = L.repond("taxon_parent", ent)
        check(f"ancre taxon_parent({ent}) == {att}", st == VERIFIE and f.valeur == att)


print(f"\n=== valide_lecteur_t4 : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
