"""
INGESTION T4 — COULOIR « VIVANT » (biologie : taxons, gènes). ONLINE via QLever -> datasets/lecteur/*.jsonl.

Terminal d'ingestion parallèle #4 (cf. BRIEF_INGESTION_COMMUN.md + BRIEF_T4_VIVANT.md). FAUX=0 INVIOLABLE :
chaque relation est scoutée (scout_qlever), l'échantillon relu à l'œil, et `fonctionnel` (dans publie) rejette
tout libellé multi-valeur -> HORS. La sanité structurelle est dans valide_lecteur_t4.py (ensemble fermé / ancres).

On RÉUTILISE les fabriques de ingere_qlever (ne pas les redéfinir) :
  - `IQ._ingere_x_vers_entite(relation, propriete, categorie, source, classe_qid=...)` pour les filons
    « entité -> autre entité via propriété fonctionnelle » (organisme/chromosome d'un gène).
Pour les DEUX filons GÉANTS (taxon_rang, taxon_parent ; ~3,85 M lignes chacun), une seule requête QLever
timeout/RAM ne passe pas : on PAGINE (ORDER BY ?e + LIMIT/OFFSET) vers un snapshot _raw, puis on publie offline.

Catégories (cf. base_faits) : taxonomie (rang/parent) = `convention` (classification nomenclaturale humaine) ;
gène->organisme / gène->chromosome = `physique` (réalité biologique) ; statut UICN = `convention` (catégorie
d'évaluation officielle ; c'est la valeur courante de Wikidata, vérité datée comme population/capitale).

Usage : python3 ingere_t4.py [domaines...]   (défaut : les filons LÉGERS ; les géants sur demande explicite).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

import ingere_qlever as IQ
from ingere_wikidata import RAW, UA, charge_raw_json, publie, snapshot_brut

_DOMAINES = {}


def domaine(nom):
    def deco(fn):
        _DOMAINES[nom] = fn
        return fn
    return deco


# ───────────────────────────────────────────────────────────────────────────────────────────
#  FILONS LÉGERS (≤ ~250 k lignes) — une seule requête via la fabrique générique.
# ───────────────────────────────────────────────────────────────────────────────────────────
@domaine("organisme_gene")
def ingere_organisme_gene():
    # P703 « présent chez le taxon » : un gène appartient au génome d'UN organisme (ensemble ~ qq dizaines
    # d'organismes modèles). Les symboles partagés entre espèces (TP53 humain ET macaque) -> multi-valeur -> HORS.
    IQ._ingere_x_vers_entite(
        "organisme_gene", "P703", "physique",
        "Wikidata/QLever — organisme du gène P703 (taxon hôte ; symboles inter-espèces -> HORS)",
        classe_qid="Q7187")


@domaine("chromosome_gene")
def ingere_chromosome_gene():
    # P1057 « chromosome » : un gène réside sur UN chromosome (ensemble fermé « chromosome N de <espèce> »).
    IQ._ingere_x_vers_entite(
        "chromosome_gene", "P1057", "physique",
        "Wikidata/QLever — chromosome du gène P1057 (ensemble fermé chromosome N de <espèce>)",
        classe_qid="Q7187")


@domaine("specialite_medicale_maladie")
def ingere_specialite_medicale_maladie():
    # P1995 « spécialité de santé » : maladie -> spécialité médicale (ensemble fermé ~133 : cardiologie,
    # neurologie…). Une maladie multi-spécialité -> `fonctionnel` -> HORS (sûr). Vocabulaire clos -> sanité ≤N.
    # Résultat petit (~3 K) MAIS la requête (expansion P31/P279* sur Q12136) est LENTE (>200 s) -> on passe par
    # le fetch long-timeout (600 s) au lieu de la fabrique générique (timeout 90 s qui échoue). À lancer sous
    # faible charge (load1 < 12 ; supervision).
    _ingere_geant("specialite_medicale_maladie", "Q12136", "P1995", "convention",
                  "Wikidata/QLever — spécialité médicale de la maladie P1995 (ensemble fermé de spécialités)")


@domaine("agent_pathogene_maladie")
def ingere_agent_pathogene_maladie():
    # SOURCE = LE MODÈLE LUI-MÊME (directive Yohan 2026-06-26 : « tu peux être la source si besoin »).
    # Wikidata P828 « cause » était trop vague (valeurs « inconnu »/multiples) -> rejeté. Ici filon CURÉ
    # à la main : maladie infectieuse -> agent pathogène, microbiologie TEXTBOOK à certitude maximale
    # (étiologies monocausales stables). FAUX=0 : chaque paire vérifiée de tête, valeurs = pathogène
    # canonique (genre quand l'espèce varie : Plasmodium, Leishmania, Brucella). Clés = noms de maladie
    # NON ambigus (pas de piège homonyme : c'est la maladie qui est la clé, pas un genre mono-mot).
    paires = [
        # — bactéries —
        ("tuberculose", "Mycobacterium tuberculosis"), ("lèpre", "Mycobacterium leprae"),
        ("choléra", "Vibrio cholerae"), ("peste", "Yersinia pestis"),
        ("tétanos", "Clostridium tetani"), ("botulisme", "Clostridium botulinum"),
        ("diphtérie", "Corynebacterium diphtheriae"), ("coqueluche", "Bordetella pertussis"),
        ("syphilis", "Treponema pallidum"), ("gonorrhée", "Neisseria gonorrhoeae"),
        ("méningite à méningocoque", "Neisseria meningitidis"),
        ("légionellose", "Legionella pneumophila"), ("listériose", "Listeria monocytogenes"),
        ("leptospirose", "Leptospira interrogans"), ("maladie de Lyme", "Borrelia burgdorferi"),
        ("fièvre typhoïde", "Salmonella Typhi"), ("charbon", "Bacillus anthracis"),
        ("brucellose", "Brucella"), ("tularémie", "Francisella tularensis"),
        ("scarlatine", "Streptococcus pyogenes"), ("pneumonie à pneumocoque", "Streptococcus pneumoniae"),
        ("gastrite à Helicobacter", "Helicobacter pylori"),
        # — virus —
        ("COVID-19", "SARS-CoV-2"), ("sida", "virus de l'immunodéficience humaine"),
        ("rage", "virus de la rage"), ("rougeole", "virus de la rougeole"),
        ("rubéole", "virus de la rubéole"), ("oreillons", "virus ourlien"),
        ("varicelle", "virus varicelle-zona"), ("variole", "virus de la variole"),
        ("poliomyélite", "poliovirus"), ("hépatite A", "virus de l'hépatite A"),
        ("hépatite B", "virus de l'hépatite B"), ("hépatite C", "virus de l'hépatite C"),
        ("fièvre jaune", "virus de la fièvre jaune"), ("dengue", "virus de la dengue"),
        ("mononucléose infectieuse", "virus d'Epstein-Barr"),
        ("maladie à virus Ebola", "virus Ebola"), ("chikungunya", "virus chikungunya"),
        # — protozoaires / parasites —
        ("paludisme", "Plasmodium"), ("toxoplasmose", "Toxoplasma gondii"),
        ("leishmaniose", "Leishmania"), ("maladie de Chagas", "Trypanosoma cruzi"),
        ("amibiase", "Entamoeba histolytica"), ("giardiase", "Giardia lamblia"),
        ("bilharziose", "Schistosoma"),
        # — extension nuit 2026-06-26 (toujours textbook FAUX=0) —
        ("grippe", "virus de la grippe"), ("gangrène gazeuse", "Clostridium perfringens"),
        ("angine streptococcique", "Streptococcus pyogenes"), ("fièvre Q", "Coxiella burnetii"),
        ("typhus épidémique", "Rickettsia prowazekii"), ("mélioïdose", "Burkholderia pseudomallei"),
        ("chlamydiose", "Chlamydia trachomatis"), ("candidose", "Candida albicans"),
        ("aspergillose", "Aspergillus fumigatus"), ("maladie du sommeil", "Trypanosoma brucei"),
        ("gale", "Sarcoptes scabiei"), ("téniase", "Taenia"),
        ("ascaridiose", "Ascaris lumbricoides"), ("oxyurose", "Enterobius vermicularis"),
        ("trichinose", "Trichinella spiralis"), ("onchocercose", "Onchocerca volvulus"),
        ("filariose lymphatique", "Wuchereria bancrofti"), ("hydatidose", "Echinococcus granulosus"),
        ("hépatite E", "virus de l'hépatite E"), ("fièvre de Marburg", "virus de Marburg"),
        ("zona", "virus varicelle-zona"), ("herpès", "virus herpes simplex"),
        ("cancer du col de l'utérus", "papillomavirus humain"),
        # — approfondissement run-autonome (étiologies monocausales certaines) —
        ("psittacose", "Chlamydia psittaci"), ("érysipèle", "Streptococcus pyogenes"),
        ("syndrome de choc toxique", "Staphylococcus aureus"),
        ("fièvre pourprée des montagnes Rocheuses", "Rickettsia rickettsii"),
        ("ulcère de Buruli", "Mycobacterium ulcerans"), ("salmonellose", "Salmonella"),
        ("shigellose", "Shigella"), ("campylobactériose", "Campylobacter jejuni"),
        ("colite pseudomembraneuse", "Clostridioides difficile"),
        ("cryptococcose", "Cryptococcus neoformans"), ("histoplasmose", "Histoplasma capsulatum"),
        ("pneumocystose", "Pneumocystis jirovecii"), ("cryptosporidiose", "Cryptosporidium"),
        ("babésiose", "Babesia"), ("anguillulose", "Strongyloides stercoralis"),
        ("distomatose hépatique", "Fasciola hepatica"),
        ("variole du singe", "virus de la variole du singe"), ("hépatite D", "virus de l'hépatite D"),
        ("roséole", "herpèsvirus humain 6"),
        ("fièvre boutonneuse méditerranéenne", "Rickettsia conorii"),
        # — approfondissement run-autonome v2 (étiologies monocausales certaines) —
        ("trachome", "Chlamydia trachomatis"), ("chancre mou", "Haemophilus ducreyi"),
        ("érythème infectieux", "parvovirus B19"), ("fièvre de Lassa", "virus Lassa"),
        ("nocardiose", "Nocardia"), ("actinomycose", "Actinomyces israelii"),
        ("pian", "Treponema pallidum pertenue"), ("donovanose", "Klebsiella granulomatis"),
        ("encéphalite japonaise", "virus de l'encéphalite japonaise"),
        ("kala-azar", "Leishmania donovani"), ("fièvre de la vallée du Rift", "virus de la fièvre de la vallée du Rift"),
        # — approfondissement run-autonome v3 (étiologies monocausales certaines) —
        ("maladie des griffes du chat", "Bartonella henselae"), ("fièvre des tranchées", "Bartonella quintana"),
        ("morve", "Burkholderia mallei"), ("ehrlichiose", "Ehrlichia"), ("anaplasmose", "Anaplasma"),
        ("granulome vénérien", "Klebsiella granulomatis"), ("bartonellose", "Bartonella bacilliformis"),
        ("fièvre de Pontiac", "Legionella pneumophila"),
    ]
    publie("agent_pathogene_maladie", "physique",
           "Modèle (Claude) — microbiologie textbook curée à la main, étiologies monocausales (FAUX=0 vérifié)",
           paires)


@domaine("vecteur_maladie")
def ingere_vecteur_maladie():
    # SOURCE = LE MODÈLE (directive Yohan). Maladie à transmission vectorielle -> arthropode vecteur.
    # Textbook épidémiologie, FAUX=0 (vecteur dominant non contesté ; maladies à vecteurs multiples exclues).
    paires = [
        ("paludisme", "moustique anophèle"), ("dengue", "moustique Aedes"),
        ("fièvre jaune", "moustique Aedes"), ("chikungunya", "moustique Aedes"),
        ("Zika", "moustique Aedes"), ("fièvre du Nil occidental", "moustique Culex"),
        ("maladie de Lyme", "tique"), ("peste", "puce"),
        ("typhus épidémique", "pou"), ("maladie du sommeil", "mouche tsé-tsé"),
        ("leishmaniose", "phlébotome"), ("maladie de Chagas", "triatome"),
        ("onchocercose", "simulie"),
        # — approfondissement run-autonome (vecteur dominant non contesté) —
        ("encéphalite japonaise", "moustique Culex"), ("encéphalite à tiques", "tique"),
        ("babésiose", "tique"), ("fièvre pourprée des montagnes Rocheuses", "tique"),
        ("fièvre boutonneuse méditerranéenne", "tique"), ("typhus murin", "puce"),
        ("loase", "taon"), ("filariose lymphatique", "moustique"),
    ]
    publie("vecteur_maladie", "physique",
           "Modèle (Claude) — épidémiologie textbook curée (vecteur dominant ; FAUX=0 vérifié)", paires)


@domaine("glande_hormone")
def ingere_glande_hormone():
    # SOURCE = LE MODÈLE (directive Yohan). Hormone -> glande/organe sécréteur principal. Textbook
    # endocrinologie, FAUX=0. Hormones hypothalamo-hypophysaires ambiguës (ocytocine/ADH) EXCLUES.
    paires = [
        ("insuline", "pancréas"), ("glucagon", "pancréas"),
        ("thyroxine", "glande thyroïde"), ("triiodothyronine", "glande thyroïde"),
        ("calcitonine", "glande thyroïde"), ("parathormone", "glande parathyroïde"),
        ("cortisol", "glande surrénale"), ("aldostérone", "glande surrénale"),
        ("adrénaline", "glande surrénale"), ("testostérone", "testicule"),
        ("œstradiol", "ovaire"), ("progestérone", "ovaire"),
        ("mélatonine", "glande pinéale"), ("hormone de croissance", "hypophyse"),
        ("prolactine", "hypophyse"), ("érythropoïétine", "rein"),
        ("gastrine", "estomac"),
        # — approfondissement run-autonome (glande sécrétrice principale non ambiguë) —
        ("rénine", "rein"), ("noradrénaline", "glande surrénale"),
        ("hormone folliculostimulante", "hypophyse"), ("hormone lutéinisante", "hypophyse"),
        ("thyréostimuline", "hypophyse"), ("corticotrophine", "hypophyse"),
        ("sécrétine", "intestin grêle"), ("cholécystokinine", "intestin grêle"),
        ("ghréline", "estomac"), ("leptine", "tissu adipeux"),
        ("peptide natriurétique auriculaire", "cœur"),
        # — approfondissement run-autonome v2 (glande sécrétrice certaine) —
        ("relaxine", "ovaire"), ("hormone chorionique gonadotrope", "placenta"),
        ("facteur de croissance IGF-1", "foie"), ("thrombopoïétine", "foie"),
        ("ostéocalcine", "tissu osseux"), ("cholécalciférol", "peau"),
    ]
    publie("glande_hormone", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (glande sécrétrice principale ; FAUX=0 vérifié)", paires)


@domaine("regime_alimentaire")
def ingere_regime_alimentaire():
    # SOURCE = LE MODÈLE (directive Yohan). Animal emblématique -> régime alimentaire (ENSEMBLE FERMÉ :
    # carnivore/herbivore/omnivore/insectivore). Textbook, FAUX=0 (animaux au régime non ambigu ; clés =
    # noms communs sans piège). NB régime ≠ ordre taxinomique (panda géant=Carnivora mais herbivore).
    paires = [
        ("lion", "carnivore"), ("tigre", "carnivore"), ("loup", "carnivore"),
        ("guépard", "carnivore"), ("aigle royal", "carnivore"), ("grand requin blanc", "carnivore"),
        ("vache", "herbivore"), ("cheval", "herbivore"), ("mouton", "herbivore"),
        ("éléphant d'Afrique", "herbivore"), ("girafe", "herbivore"), ("lapin", "herbivore"),
        ("panda géant", "herbivore"), ("koala", "herbivore"), ("gorille", "herbivore"),
        ("ours brun", "omnivore"), ("sanglier", "omnivore"), ("rat", "omnivore"),
        ("corbeau", "omnivore"), ("fourmilier géant", "insectivore"), ("hérisson", "insectivore"),
        # — extension nuit (animaux courants, régime non ambigu) —
        ("hyène tachetée", "carnivore"), ("faucon pèlerin", "carnivore"), ("otarie", "carnivore"),
        ("renard roux", "carnivore"), ("orque", "carnivore"),
        ("zèbre", "herbivore"), ("gazelle", "herbivore"), ("bison d'Amérique", "herbivore"),
        ("hippopotame", "herbivore"), ("rhinocéros blanc", "herbivore"), ("chameau", "herbivore"),
        ("paresseux", "herbivore"), ("castor", "herbivore"),
        ("raton laveur", "omnivore"), ("chimpanzé", "omnivore"), ("rat surmulot", "omnivore"),
        ("taupe", "insectivore"), ("pangolin", "insectivore"),
        # — approfondissement après-midi (animaux au régime non ambigu) —
        ("léopard", "carnivore"), ("jaguar", "carnivore"), ("puma", "carnivore"),
        ("lynx", "carnivore"), ("loutre", "carnivore"), ("ours polaire", "carnivore"),
        ("dauphin", "carnivore"), ("serpent", "carnivore"), ("héron", "carnivore"), ("hibou", "carnivore"),
        ("kangourou", "herbivore"), ("antilope", "herbivore"), ("chèvre", "herbivore"),
        ("cerf", "herbivore"), ("gnou", "herbivore"), ("panda roux", "herbivore"),
        ("autruche", "omnivore"), ("cochon", "omnivore"), ("babouin", "omnivore"),
        ("musaraigne", "insectivore"), ("oryctérope", "insectivore"),
        # — approfondissement run-autonome (régime textbook non ambigu) —
        ("crocodile", "carnivore"), ("phoque", "carnivore"), ("belette", "carnivore"),
        ("hermine", "carnivore"), ("chat", "carnivore"), ("furet", "carnivore"),
        ("poulpe", "carnivore"), ("manchot empereur", "carnivore"), ("morse", "carnivore"),
        ("âne", "herbivore"), ("buffle", "herbivore"), ("yak", "herbivore"),
        ("alpaga", "herbivore"), ("lama", "herbivore"), ("marmotte", "herbivore"),
        ("capybara", "herbivore"), ("renne", "herbivore"), ("tapir", "herbivore"),
        ("okapi", "herbivore"), ("oie", "herbivore"),
        ("ours noir", "omnivore"), ("opossum", "omnivore"), ("poule", "omnivore"), ("canard", "omnivore"),
        ("caméléon", "insectivore"), ("gecko", "insectivore"), ("crapaud", "insectivore"),
        ("hirondelle", "insectivore"),
        # — approfondissement run-autonome v2 (régime non ambigu) —
        ("belette", "carnivore"), ("hermine", "carnivore"), ("glouton", "carnivore"),
        ("mangouste", "carnivore"), ("fouine", "carnivore"), ("brochet", "carnivore"),
        ("barracuda", "carnivore"), ("murène", "carnivore"),
        ("bouquetin", "herbivore"), ("chamois", "herbivore"), ("oryx", "herbivore"),
        ("impala", "herbivore"), ("koudou", "herbivore"), ("wapiti", "herbivore"),
        ("caribou", "herbivore"), ("vigogne", "herbivore"), ("capybara", "herbivore"),
        ("blaireau", "omnivore"), ("pécari", "omnivore"),
        ("tamanoir", "insectivore"), ("échidné", "insectivore"),
    ]
    publie("regime_alimentaire", "physique",
           "Modèle (Claude) — zoologie textbook curée (régime alimentaire ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("vitamine_carence")
def ingere_vitamine_carence():
    # SOURCE = LE MODÈLE (directive Yohan). Vitamine -> maladie de carence classique. Textbook nutrition,
    # FAUX=0 (carences emblématiques non contestées).
    paires = [
        ("vitamine C", "scorbut"), ("vitamine D", "rachitisme"),
        ("vitamine B1", "béribéri"), ("vitamine B3", "pellagre"),
        ("vitamine A", "héméralopie"), ("vitamine B12", "anémie pernicieuse"),
        ("vitamine B9", "anémie mégaloblastique"),
        # — approfondissement run-autonome (carences classiques certaines) —
        ("vitamine K", "syndrome hémorragique"), ("vitamine B2", "ariboflavinose"),
    ]
    publie("vitamine_carence", "physique",
           "Modèle (Claude) — nutrition textbook curée (maladie de carence ; FAUX=0 vérifié)", paires)


@domaine("classe_vertebre_animal")
def ingere_classe_vertebre_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal emblématique -> classe de vertébré (ENSEMBLE FERMÉ :
    # mammifère/oiseau/reptile/amphibien/poisson). Textbook, FAUX=0. Inclut les pièges classiques :
    # dauphin/baleine/chauve-souris = MAMMIFÈRES, manchot = OISEAU, hippocampe = POISSON.
    paires = [
        ("dauphin", "mammifère"), ("baleine bleue", "mammifère"), ("chauve-souris", "mammifère"),
        ("kangourou", "mammifère"), ("ornithorynque", "mammifère"),
        ("manchot empereur", "oiseau"), ("autruche", "oiseau"), ("aigle royal", "oiseau"),
        ("crocodile du Nil", "reptile"), ("tortue marine", "reptile"), ("caméléon", "reptile"),
        ("salamandre", "amphibien"), ("grenouille rousse", "amphibien"), ("triton", "amphibien"),
        ("grand requin blanc", "poisson"), ("thon rouge", "poisson"),
        ("saumon atlantique", "poisson"), ("hippocampe", "poisson"),
        # — extension nuit (animaux courants) —
        ("éléphant d'Afrique", "mammifère"), ("girafe", "mammifère"), ("hippopotame", "mammifère"),
        ("phoque", "mammifère"), ("chimpanzé", "mammifère"), ("chauve-souris", "mammifère"),
        ("flamant rose", "oiseau"), ("colibri", "oiseau"), ("perroquet", "oiseau"),
        ("cigogne blanche", "oiseau"),
        ("iguane", "reptile"), ("python", "reptile"), ("cobra royal", "reptile"), ("varan", "reptile"),
        ("crapaud", "amphibien"), ("axolotl", "amphibien"),
        ("raie manta", "poisson"), ("anguille", "poisson"), ("espadon", "poisson"),
        # — approfondissement après-midi (vertébrés au groupe non ambigu) —
        ("lion", "mammifère"), ("tigre", "mammifère"), ("cheval", "mammifère"), ("vache", "mammifère"),
        ("lapin", "mammifère"), ("souris", "mammifère"), ("gorille", "mammifère"),
        ("ours brun", "mammifère"), ("loup", "mammifère"), ("lynx", "mammifère"), ("koala", "mammifère"),
        ("pigeon", "oiseau"), ("canard", "oiseau"), ("hibou", "oiseau"), ("corbeau", "oiseau"),
        ("poule", "oiseau"), ("héron", "oiseau"),
        ("lézard", "reptile"), ("gecko", "reptile"), ("vipère", "reptile"), ("alligator", "reptile"),
        ("rainette", "amphibien"),
        ("carpe", "poisson"), ("truite", "poisson"), ("sardine", "poisson"), ("morue", "poisson"),
        ("brochet", "poisson"),
        # — approfondissement run-autonome (vertébrés au groupe non ambigu ; pièges inclus) —
        ("orque", "mammifère"), ("cachalot", "mammifère"), ("lamantin", "mammifère"),
        ("rhinocéros blanc", "mammifère"), ("zèbre", "mammifère"), ("panda géant", "mammifère"),
        ("renard roux", "mammifère"), ("hyène tachetée", "mammifère"), ("léopard", "mammifère"),
        ("jaguar", "mammifère"), ("guépard", "mammifère"), ("loutre", "mammifère"),
        ("castor", "mammifère"), ("hérisson", "mammifère"), ("paresseux", "mammifère"),
        ("orang-outan", "mammifère"), ("babouin", "mammifère"), ("morse", "mammifère"),
        ("cygne", "oiseau"), ("oie", "oiseau"), ("moineau", "oiseau"), ("mésange", "oiseau"),
        ("faucon pèlerin", "oiseau"), ("vautour", "oiseau"), ("pélican", "oiseau"),
        ("mouette", "oiseau"), ("toucan", "oiseau"), ("paon", "oiseau"), ("hirondelle", "oiseau"),
        ("kiwi", "oiseau"), ("émeu", "oiseau"),
        ("boa", "reptile"), ("anaconda", "reptile"), ("tortue terrestre", "reptile"),
        ("gavial", "reptile"), ("varan de Komodo", "reptile"),
        ("salamandre tachetée", "amphibien"), ("grenouille verte", "amphibien"), ("protée", "amphibien"),
        ("requin-marteau", "poisson"), ("poisson-clown", "poisson"), ("hareng", "poisson"),
        ("maquereau", "poisson"), ("perche", "poisson"), ("esturgeon", "poisson"),
        ("murène", "poisson"), ("mérou", "poisson"),
        # — approfondissement run-autonome v2 (espèces univoques) —
        ("belette", "mammifère"), ("hermine", "mammifère"), ("furet", "mammifère"),
        ("glouton", "mammifère"), ("lamantin", "mammifère"), ("narval", "mammifère"), ("béluga", "mammifère"),
        ("rossignol", "oiseau"), ("alouette", "oiseau"), ("geai", "oiseau"), ("pie", "oiseau"),
        ("grive", "oiseau"), ("faisan", "oiseau"), ("caille", "oiseau"), ("grue", "oiseau"),
        ("pélican", "oiseau"), ("cormoran", "oiseau"),
        ("anolis", "reptile"), ("scinque", "reptile"), ("mamba", "reptile"), ("crotale", "reptile"),
        ("anaconda", "reptile"), ("couleuvre", "reptile"), ("orvet", "reptile"),
        ("pélobate", "amphibien"), ("sonneur", "amphibien"), ("cécilie", "amphibien"),
        ("gardon", "poisson"), ("brème", "poisson"), ("silure", "poisson"), ("congre", "poisson"),
        ("dorade", "poisson"), ("turbot", "poisson"), ("sole", "poisson"), ("esturgeon", "poisson"),
        ("lamproie", "poisson"),
    ]
    publie("classe_vertebre_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (classe de vertébré ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_reproduction_animal")
def ingere_mode_reproduction_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> mode de reproduction (ENSEMBLE FERMÉ : ovipare/
    # vivipare/ovovivipare). Textbook, FAUX=0. Inclut l'ornithorynque (mammifère OVIPARE, exception célèbre).
    paires = [
        ("poule", "ovipare"), ("crocodile du Nil", "ovipare"), ("tortue marine", "ovipare"),
        ("manchot empereur", "ovipare"), ("ornithorynque", "ovipare"), ("saumon atlantique", "ovipare"),
        ("grenouille rousse", "ovipare"),
        ("vache", "vivipare"), ("éléphant d'Afrique", "vivipare"), ("chauve-souris", "vivipare"),
        ("dauphin", "vivipare"), ("kangourou", "vivipare"), ("être humain", "vivipare"),
        # — approfondissement après-midi (mode non ambigu) —
        ("cobra royal", "ovipare"), ("python", "ovipare"), ("autruche", "ovipare"),
        ("aigle royal", "ovipare"), ("crapaud", "ovipare"), ("thon rouge", "ovipare"),
        ("abeille", "ovipare"), ("papillon", "ovipare"), ("araignée", "ovipare"), ("canard", "ovipare"),
        ("lion", "vivipare"), ("tigre", "vivipare"), ("chien", "vivipare"), ("chat", "vivipare"),
        ("cheval", "vivipare"), ("lapin", "vivipare"), ("souris", "vivipare"),
        ("baleine bleue", "vivipare"), ("girafe", "vivipare"), ("gorille", "vivipare"),
        # — approfondissement run-autonome (mode non ambigu) —
        ("oie", "ovipare"), ("pigeon", "ovipare"), ("perroquet", "ovipare"), ("flamant rose", "ovipare"),
        ("héron", "ovipare"), ("hibou", "ovipare"), ("corbeau", "ovipare"), ("cygne", "ovipare"),
        ("moineau", "ovipare"), ("tortue terrestre", "ovipare"), ("escargot", "ovipare"),
        ("fourmi", "ovipare"), ("mouche", "ovipare"), ("coccinelle", "ovipare"), ("sauterelle", "ovipare"),
        ("truite", "ovipare"), ("hareng", "ovipare"), ("carpe", "ovipare"),
        ("chimpanzé", "vivipare"), ("rhinocéros blanc", "vivipare"), ("zèbre", "vivipare"),
        ("hippopotame", "vivipare"), ("orque", "vivipare"), ("cachalot", "vivipare"),
        ("phoque", "vivipare"), ("ours brun", "vivipare"), ("loup", "vivipare"), ("renard roux", "vivipare"),
        ("mouton", "vivipare"), ("chèvre", "vivipare"), ("cochon", "vivipare"), ("cerf", "vivipare"),
        ("vipère", "ovovivipare"), ("grand requin blanc", "ovovivipare"),
        # — approfondissement run-autonome v2 (mode non ambigu) —
        ("pintade", "ovipare"), ("faisan", "ovipare"), ("caille", "ovipare"), ("gecko", "ovipare"),
        ("iguane", "ovipare"), ("varan", "ovipare"), ("couleuvre", "ovipare"), ("brochet", "ovipare"),
        ("sardine", "ovipare"), ("morue", "ovipare"), ("guêpe", "ovipare"), ("coccinelle", "ovipare"),
        ("libellule", "ovipare"),
        ("rhinocéros blanc", "vivipare"), ("zèbre", "vivipare"), ("girafe", "vivipare"),
        ("phoque", "vivipare"), ("chauve-souris", "vivipare"), ("kangourou", "vivipare"),
        ("boa", "ovovivipare"), ("anaconda", "ovovivipare"), ("orvet", "ovovivipare"),
    ]
    publie("mode_reproduction_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (mode de reproduction ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_microorganisme")
def ingere_type_microorganisme():
    # SOURCE = LE MODÈLE (directive Yohan). Agent pathogène -> type de micro-organisme (ENSEMBLE FERMÉ :
    # bactérie/virus/protozoaire/champignon/helminthe). Textbook microbiologie, FAUX=0. Complète
    # agent_pathogene_maladie en classant les agents.
    paires = [
        ("Mycobacterium tuberculosis", "bactérie"), ("Vibrio cholerae", "bactérie"),
        ("Yersinia pestis", "bactérie"), ("Treponema pallidum", "bactérie"),
        ("Escherichia coli", "bactérie"), ("Clostridium tetani", "bactérie"),
        ("Helicobacter pylori", "bactérie"), ("Borrelia burgdorferi", "bactérie"),
        ("SARS-CoV-2", "virus"), ("virus de l'immunodéficience humaine", "virus"),
        ("virus de la rage", "virus"), ("poliovirus", "virus"), ("virus Ebola", "virus"),
        ("virus de la variole", "virus"),
        ("Plasmodium", "protozoaire"), ("Toxoplasma gondii", "protozoaire"),
        ("Leishmania", "protozoaire"), ("Trypanosoma cruzi", "protozoaire"),
        ("Entamoeba histolytica", "protozoaire"), ("Giardia lamblia", "protozoaire"),
        ("Candida albicans", "champignon"), ("Aspergillus fumigatus", "champignon"),
        ("Schistosoma", "helminthe"),
        # — approfondissement run-autonome (classification microbiologique certaine) —
        ("Mycobacterium leprae", "bactérie"), ("Clostridium botulinum", "bactérie"),
        ("Corynebacterium diphtheriae", "bactérie"), ("Bordetella pertussis", "bactérie"),
        ("Neisseria gonorrhoeae", "bactérie"), ("Neisseria meningitidis", "bactérie"),
        ("Legionella pneumophila", "bactérie"), ("Listeria monocytogenes", "bactérie"),
        ("Bacillus anthracis", "bactérie"), ("Streptococcus pneumoniae", "bactérie"),
        ("Streptococcus pyogenes", "bactérie"), ("Staphylococcus aureus", "bactérie"),
        ("Coxiella burnetii", "bactérie"), ("Rickettsia prowazekii", "bactérie"),
        ("Rickettsia rickettsii", "bactérie"), ("Chlamydia psittaci", "bactérie"),
        ("Clostridioides difficile", "bactérie"), ("Salmonella", "bactérie"),
        ("Shigella", "bactérie"), ("Campylobacter jejuni", "bactérie"),
        ("virus de la rougeole", "virus"), ("virus de l'hépatite B", "virus"),
        ("virus de l'hépatite C", "virus"), ("virus de la dengue", "virus"),
        ("virus d'Epstein-Barr", "virus"), ("papillomavirus humain", "virus"),
        ("virus herpes simplex", "virus"), ("virus de Marburg", "virus"),
        ("Trypanosoma brucei", "protozoaire"), ("Cryptosporidium", "protozoaire"),
        ("Babesia", "protozoaire"),
        ("Cryptococcus neoformans", "champignon"), ("Histoplasma capsulatum", "champignon"),
        ("Pneumocystis jirovecii", "champignon"),
        ("Taenia", "helminthe"), ("Ascaris lumbricoides", "helminthe"),
        ("Enterobius vermicularis", "helminthe"), ("Trichinella spiralis", "helminthe"),
        ("Onchocerca volvulus", "helminthe"), ("Wuchereria bancrofti", "helminthe"),
        ("Echinococcus granulosus", "helminthe"), ("Fasciola hepatica", "helminthe"),
        ("Strongyloides stercoralis", "helminthe"),
        # — approfondissement run-autonome v2 (classification certaine) —
        ("Brucella", "bactérie"), ("Francisella tularensis", "bactérie"), ("Yersinia pestis", "bactérie"),
        ("Treponema pallidum", "bactérie"), ("Borrelia burgdorferi", "bactérie"), ("Leptospira", "bactérie"),
        ("virus de la grippe", "virus"), ("rotavirus", "virus"), ("norovirus", "virus"),
        ("Naegleria", "protozoaire"), ("Balantidium coli", "protozoaire"),
        ("Mucor", "champignon"), ("Trichophyton", "champignon"),
        ("Fasciola hepatica", "helminthe"), ("Enterobius vermicularis", "helminthe"),
    ]
    publie("type_microorganisme", "physique",
           "Modèle (Claude) — microbiologie textbook curée (type de micro-organisme ; ensemble fermé ; FAUX=0)", paires)


@domaine("organe_atteint_maladie")
def ingere_organe_atteint_maladie():
    # SOURCE = LE MODÈLE (directive Yohan). Maladie inflammatoire (-ite) -> organe atteint (la racine du
    # nom DÉSIGNE l'organe : hépat-ite=foie, néphr-ite=rein). Textbook, FAUX=0 (correspondance étymologique
    # non contestée).
    paires = [
        ("hépatite", "foie"), ("néphrite", "rein"), ("gastrite", "estomac"),
        ("colite", "côlon"), ("cystite", "vessie"), ("otite", "oreille"),
        ("dermatite", "peau"), ("méningite", "méninges"), ("myocardite", "cœur"),
        ("bronchite", "bronches"), ("laryngite", "larynx"), ("appendicite", "appendice"),
        ("pancréatite", "pancréas"), ("encéphalite", "cerveau"), ("arthrite", "articulation"),
        ("pneumonie", "poumon"), ("rhinite", "nez"), ("conjonctivite", "œil"),
        # — approfondissement run-autonome (correspondance étymologique -ite -> organe) —
        ("tendinite", "tendon"), ("sinusite", "sinus"), ("amygdalite", "amygdales"),
        ("phlébite", "veine"), ("kératite", "cornée"), ("entérite", "intestin"),
        ("stomatite", "bouche"), ("glossite", "langue"), ("myosite", "muscle"),
        ("ostéite", "os"), ("péricardite", "péricarde"), ("prostatite", "prostate"),
        ("mastite", "sein"), ("orchite", "testicule"), ("salpingite", "trompe de Fallope"),
        ("gingivite", "gencive"), ("œsophagite", "œsophage"), ("cholécystite", "vésicule biliaire"),
        # — approfondissement run-autonome v2 (correspondance étymologique -ite -> organe) —
        ("thyroïdite", "thyroïde"), ("épididymite", "épididyme"), ("rétinite", "rétine"),
        ("névrite", "nerf"), ("myélite", "moelle épinière"), ("spondylite", "vertèbre"),
        ("endométrite", "endomètre"), ("urétrite", "urètre"), ("adénite", "ganglion lymphatique"),
        ("lymphangite", "vaisseau lymphatique"), ("cervicite", "col de l'utérus"),
        ("balanite", "gland"), ("kératite", "cornée"), ("uvéite", "uvée"),
        # — approfondissement run-autonome v3 (-ite -> organe) —
        ("pleurésie", "plèvre"), ("rectite", "rectum"), ("vaginite", "vagin"),
        ("bursite", "bourse séreuse"), ("fasciite", "fascia"), ("synovite", "membrane synoviale"),
        ("périostite", "périoste"), ("parotidite", "parotide"), ("blépharite", "paupière"),
        ("sclérite", "sclère"), ("pyélonéphrite", "rein"), ("urétérite", "uretère"), ("splénite", "rate"),
    ]
    publie("organe_atteint_maladie", "physique",
           "Modèle (Claude) — médecine textbook curée (organe atteint ; correspondance étymologique ; FAUX=0)", paires)


@domaine("substrat_enzyme")
def ingere_substrat_enzyme():
    # SOURCE = LE MODÈLE (directive Yohan). Enzyme digestive -> substrat hydrolysé. Textbook biochimie, FAUX=0.
    paires = [
        ("amylase", "amidon"), ("lipase", "lipides"), ("pepsine", "protéines"),
        ("trypsine", "protéines"), ("lactase", "lactose"), ("maltase", "maltose"),
        ("sucrase", "saccharose"), ("cellulase", "cellulose"), ("nucléase", "acides nucléiques"),
        # — approfondissement run-autonome (hydrolases, substrat certain) —
        ("lysozyme", "peptidoglycane"), ("uréase", "urée"), ("chymotrypsine", "protéines"),
        ("élastase", "élastine"), ("collagénase", "collagène"), ("hyaluronidase", "acide hyaluronique"),
        ("pectinase", "pectine"), ("ribonucléase", "ARN"), ("désoxyribonucléase", "ADN"),
        ("peptidase", "peptides"), ("phospholipase", "phospholipides"),
        # — approfondissement run-autonome v2 (substrat certain) —
        ("invertase", "saccharose"), ("chitinase", "chitine"), ("plasmine", "fibrine"),
        ("ATPase", "ATP"), ("gélatinase", "gélatine"), ("kératinase", "kératine"),
        ("glucoamylase", "amidon"),
    ]
    publie("substrat_enzyme", "physique",
           "Modèle (Claude) — biochimie textbook curée (substrat enzymatique ; FAUX=0 vérifié)", paires)


@domaine("fonction_organite")
def ingere_fonction_organite():
    # SOURCE = LE MODÈLE (directive Yohan). Organite cellulaire -> fonction principale. Textbook biologie
    # cellulaire, FAUX=0 (fonctions canoniques non contestées).
    paires = [
        ("mitochondrie", "respiration cellulaire"), ("chloroplaste", "photosynthèse"),
        ("ribosome", "synthèse des protéines"), ("noyau", "stockage de l'information génétique"),
        ("appareil de Golgi", "maturation des protéines"), ("lysosome", "digestion cellulaire"),
    ]
    publie("fonction_organite", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (fonction d'organite ; FAUX=0 vérifié)", paires)


@domaine("vaccin_maladie")
def ingere_vaccin_maladie():
    # SOURCE = LE MODÈLE (directive Yohan). Vaccin MONOVALENT -> maladie prévenue. Textbook, FAUX=0
    # (vaccins polyvalents type ROR exclus pour rester fonctionnel monocible).
    paires = [
        ("BCG", "tuberculose"), ("vaccin antipoliomyélitique", "poliomyélite"),
        ("vaccin antirabique", "rage"), ("vaccin contre la fièvre jaune", "fièvre jaune"),
        ("vaccin antitétanique", "tétanos"), ("vaccin contre l'hépatite B", "hépatite B"),
        ("vaccin contre la variole", "variole"),
    ]
    publie("vaccin_maladie", "physique",
           "Modèle (Claude) — vaccinologie textbook curée (vaccin monovalent -> maladie ; FAUX=0 vérifié)", paires)


@domaine("classe_invertebre_animal")
def ingere_classe_invertebre_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Invertébré emblématique -> groupe (ENSEMBLE FERMÉ : arachnide/
    # insecte/crustacé/mollusque/annélide/cnidaire/échinoderme). Textbook, FAUX=0. Corrige araignée≠insecte.
    paires = [
        ("araignée", "arachnide"), ("scorpion", "arachnide"),
        ("abeille", "insecte"), ("fourmi", "insecte"), ("papillon", "insecte"),
        ("crabe", "crustacé"), ("crevette", "crustacé"),
        ("escargot", "mollusque"), ("pieuvre", "mollusque"), ("moule", "mollusque"),
        ("ver de terre", "annélide"), ("méduse", "cnidaire"), ("corail", "cnidaire"),
        ("étoile de mer", "échinoderme"), ("oursin", "échinoderme"),
        # — extension nuit (invertébrés courants) —
        ("coccinelle", "insecte"), ("libellule", "insecte"), ("sauterelle", "insecte"),
        ("moustique", "insecte"), ("scarabée", "insecte"),
        ("tique", "arachnide"), ("mygale", "arachnide"),
        ("homard", "crustacé"), ("écrevisse", "crustacé"),
        ("huître", "mollusque"), ("calmar", "mollusque"), ("seiche", "mollusque"), ("limace", "mollusque"),
        ("sangsue", "annélide"), ("anémone de mer", "cnidaire"), ("concombre de mer", "échinoderme"),
        # — approfondissement après-midi (invertébrés au groupe non ambigu) —
        ("criquet", "insecte"), ("grillon", "insecte"), ("mouche", "insecte"), ("guêpe", "insecte"),
        ("hanneton", "insecte"), ("cigale", "insecte"), ("termite", "insecte"),
        ("blatte", "insecte"), ("mante religieuse", "insecte"),
        ("cloporte", "crustacé"), ("krill", "crustacé"), ("langoustine", "crustacé"),
        ("bigorneau", "mollusque"), ("palourde", "mollusque"), ("nautile", "mollusque"),
        ("acarien", "arachnide"), ("hydre", "cnidaire"), ("ophiure", "échinoderme"),
        # — approfondissement run-autonome (invertébrés au groupe non ambigu) —
        ("puce", "insecte"), ("pou", "insecte"), ("charançon", "insecte"), ("doryphore", "insecte"),
        ("perce-oreille", "insecte"), ("phasme", "insecte"), ("punaise", "insecte"),
        ("frelon", "insecte"), ("bourdon", "insecte"), ("taon", "insecte"),
        ("faucheux", "arachnide"), ("tarentule", "arachnide"),
        ("bernard-l'ermite", "crustacé"), ("daphnie", "crustacé"), ("balane", "crustacé"),
        ("tourteau", "crustacé"),
        ("buccin", "mollusque"), ("coquille Saint-Jacques", "mollusque"), ("patelle", "mollusque"),
        ("ormeau", "mollusque"),
        ("néréis", "annélide"), ("physalie", "cnidaire"), ("gorgone", "cnidaire"),
        ("comatule", "échinoderme"),
        # — approfondissement run-autonome (groupe certain) —
        ("langouste", "crustacé"), ("tourteau", "crustacé"), ("anatife", "crustacé"),
        ("éphémère", "insecte"), ("pou", "insecte"), ("phasme", "insecte"), ("perce-oreille", "insecte"),
        ("nudibranche", "mollusque"), ("conque", "mollusque"), ("praire", "mollusque"), ("telline", "mollusque"),
        ("opilion", "arachnide"), ("pseudoscorpion", "arachnide"),
        ("tubifex", "annélide"), ("arénicole", "annélide"),
        ("holothurie", "échinoderme"), ("crinoïde", "échinoderme"),
        # — approfondissement run-autonome v2 (+ plathelminthe = 8e groupe) —
        ("copépode", "crustacé"), ("anatife", "crustacé"),
        ("veuve noire", "arachnide"), ("tarentule", "arachnide"),
        ("ténia", "plathelminthe"), ("planaire", "plathelminthe"), ("douve du foie", "plathelminthe"),
    ]
    publie("classe_invertebre_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (groupe d'invertébré ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("phylum_animal")
def ingere_phylum_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal emblématique -> EMBRANCHEMENT (phylum), niveau SUPÉRIEUR à
    # classe_vertebre/invertebre_animal (ENSEMBLE FERMÉ des grands phyla animaux). Textbook zoologie, FAUX=0.
    # Distinct de classe_invertebre (arachnide/insecte… = classe) : ici Arthropodes/Mollusques/Cnidaires…
    # Pièges classiques inclus : TOUS les vertébrés = Chordés (poisson/oiseau/humain/dauphin) ;
    # araignée+crabe+insecte = Arthropodes ; pieuvre+escargot = Mollusques ; méduse+corail = Cnidaires ;
    # étoile de mer+oursin = Échinodermes ; ver de terre+sangsue = Annélides ; éponge = Spongiaires.
    paires = [
        # — Chordés (tous les vertébrés) —
        ("être humain", "chordés"), ("dauphin", "chordés"), ("aigle royal", "chordés"),
        ("grenouille rousse", "chordés"), ("grand requin blanc", "chordés"), ("crocodile du Nil", "chordés"),
        ("thon rouge", "chordés"), ("serpent", "chordés"),
        # — Arthropodes (insectes, arachnides, crustacés, myriapodes) —
        ("araignée", "arthropodes"), ("scorpion", "arthropodes"), ("abeille", "arthropodes"),
        ("fourmi", "arthropodes"), ("papillon", "arthropodes"), ("crabe", "arthropodes"),
        ("crevette", "arthropodes"), ("homard", "arthropodes"), ("mille-pattes", "arthropodes"),
        ("scolopendre", "arthropodes"), ("libellule", "arthropodes"), ("coccinelle", "arthropodes"),
        # — Mollusques —
        ("escargot", "mollusques"), ("pieuvre", "mollusques"), ("moule", "mollusques"),
        ("huître", "mollusques"), ("calmar", "mollusques"), ("seiche", "mollusques"), ("limace", "mollusques"),
        # — Cnidaires —
        ("méduse", "cnidaires"), ("corail", "cnidaires"), ("anémone de mer", "cnidaires"), ("hydre", "cnidaires"),
        # — Échinodermes —
        ("étoile de mer", "échinodermes"), ("oursin", "échinodermes"), ("concombre de mer", "échinodermes"),
        ("ophiure", "échinodermes"),
        # — Annélides —
        ("ver de terre", "annélides"), ("sangsue", "annélides"),
        # — Plathelminthes (vers plats) —
        ("ténia", "plathelminthes"), ("planaire", "plathelminthes"), ("douve du foie", "plathelminthes"),
        # — Nématodes (vers ronds) —
        ("ascaris", "nématodes"), ("oxyure", "nématodes"),
        # — Spongiaires (éponges) —
        ("éponge de mer", "spongiaires"),
        # — approfondissement run-autonome (instanciation, phyla existants) —
        ("lion", "chordés"), ("éléphant d'Afrique", "chordés"), ("baleine bleue", "chordés"),
        ("manchot empereur", "chordés"), ("python", "chordés"), ("tortue marine", "chordés"),
        ("salamandre", "chordés"), ("hippocampe", "chordés"), ("raie manta", "chordés"),
        ("mouche", "arthropodes"), ("criquet", "arthropodes"), ("guêpe", "arthropodes"),
        ("scarabée", "arthropodes"), ("mante religieuse", "arthropodes"), ("tique", "arthropodes"),
        ("écrevisse", "arthropodes"), ("krill", "arthropodes"), ("cloporte", "arthropodes"),
        ("nautile", "mollusques"), ("palourde", "mollusques"), ("bigorneau", "mollusques"),
        ("coquille Saint-Jacques", "mollusques"),
        ("physalie", "cnidaires"), ("gorgone", "cnidaires"),
        ("ophiure", "échinodermes"), ("comatule", "échinodermes"), ("concombre de mer", "échinodermes"),
        ("néréis", "annélides"),
        # — approfondissement run-autonome v2 (phyla existants) —
        ("lamantin", "chordés"), ("narval", "chordés"), ("anolis", "chordés"), ("pélican", "chordés"),
        ("gardon", "chordés"), ("sole", "chordés"),
        ("cétoine", "arthropodes"), ("capricorne", "arthropodes"), ("gendarme", "arthropodes"),
        ("agrion", "arthropodes"), ("opilion", "arthropodes"), ("langouste", "arthropodes"),
        ("anatife", "arthropodes"), ("daphnie", "arthropodes"),
        ("nudibranche", "mollusques"), ("praire", "mollusques"), ("telline", "mollusques"),
        ("aplysie", "mollusques"), ("argonaute", "mollusques"),
        ("holothurie", "échinodermes"), ("crinoïde", "échinodermes"),
        ("tubifex", "annélides"), ("arénicole", "annélides"),
    ]
    publie("phylum_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (embranchement/phylum ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_symetrie_animal")
def ingere_type_symetrie_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> type de symétrie corporelle (ADULTE) ; ENSEMBLE FERMÉ :
    # bilatérale / radiaire / asymétrique. Textbook zoologie, FAUX=0. Cnidaires+échinodermes ADULTES = radiaire
    # (les échinodermes ont une larve bilatérale → on précise « adulte ») ; éponge = asymétrique ; tout le reste
    # (bilatériens) = bilatérale, y compris pieuvre/escargot (mollusques) et arthropodes.
    paires = [
        ("être humain", "bilatérale"), ("papillon", "bilatérale"), ("poisson", "bilatérale"),
        ("chien", "bilatérale"), ("escargot", "bilatérale"), ("ver de terre", "bilatérale"),
        ("abeille", "bilatérale"), ("crabe", "bilatérale"), ("pieuvre", "bilatérale"),
        ("homard", "bilatérale"), ("grenouille", "bilatérale"), ("serpent", "bilatérale"),
        ("méduse", "radiaire"), ("corail", "radiaire"), ("anémone de mer", "radiaire"),
        ("hydre", "radiaire"), ("étoile de mer", "radiaire"), ("oursin", "radiaire"),
        ("éponge de mer", "asymétrique"),
        # — approfondissement run-autonome (symétrie adulte certaine) —
        ("lion", "bilatérale"), ("cheval", "bilatérale"), ("souris", "bilatérale"),
        ("mouche", "bilatérale"), ("scorpion", "bilatérale"), ("scarabée", "bilatérale"),
        ("fourmi", "bilatérale"), ("calmar", "bilatérale"), ("seiche", "bilatérale"),
        ("sangsue", "bilatérale"), ("criquet", "bilatérale"), ("libellule", "bilatérale"),
        ("ophiure", "radiaire"), ("concombre de mer", "radiaire"), ("comatule", "radiaire"),
    ]
    publie("type_symetrie_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (symétrie corporelle adulte ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("nombre_chambres_coeur_animal")
def ingere_nombre_chambres_coeur_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal vertébré -> nombre de cavités cardiaques ; ENSEMBLE FERMÉ
    # {2,3,4}. Textbook anatomie comparée, FAUX=0. Poisson=2 (1 oreillette+1 ventricule) ; amphibien=3 ;
    # reptile=3 SAUF crocodiliens=4 (exception célèbre) ; oiseau=4 ; mammifère=4. Valeurs = chaînes numériques.
    paires = [
        ("carpe", "2"), ("requin", "2"), ("thon rouge", "2"), ("saumon atlantique", "2"),
        ("grenouille rousse", "3"), ("salamandre", "3"), ("triton", "3"),
        ("lézard", "3"), ("serpent", "3"), ("tortue marine", "3"),
        ("crocodile du Nil", "4"), ("alligator", "4"),
        ("aigle royal", "4"), ("pigeon", "4"), ("manchot empereur", "4"),
        ("être humain", "4"), ("chien", "4"), ("dauphin", "4"), ("éléphant d'Afrique", "4"),
        # — approfondissement run-autonome (anatomie comparée certaine {2,3,4}) —
        ("morue", "2"), ("sardine", "2"), ("hareng", "2"), ("perche", "2"),
        ("anguille", "2"), ("truite", "2"), ("brochet", "2"), ("hippocampe", "2"),
        ("crapaud", "3"), ("axolotl", "3"), ("iguane", "3"), ("gecko", "3"),
        ("varan", "3"), ("cobra royal", "3"), ("vipère", "3"), ("caméléon", "3"),
        ("tortue terrestre", "3"), ("python", "3"),
        ("lion", "4"), ("tigre", "4"), ("cheval", "4"), ("vache", "4"),
        ("baleine bleue", "4"), ("orque", "4"), ("autruche", "4"), ("hibou", "4"),
        ("chimpanzé", "4"), ("chat", "4"),
        # — approfondissement run-autonome (anatomie comparée certaine {2,3,4}) —
        ("brochet", "2"), ("perche", "2"), ("hareng", "2"), ("sole", "2"),
        ("rainette", "3"), ("salamandre", "3"), ("caméléon", "3"),
        ("souris", "4"), ("lapin", "4"), ("manchot empereur", "4"), ("perroquet", "4"), ("girafe", "4"),
    ]
    publie("nombre_chambres_coeur_animal", "physique",
           "Modèle (Claude) — anatomie comparée textbook curée (cavités cardiaques ; ensemble fermé {2,3,4} ; FAUX=0 vérifié)", paires)


@domaine("type_squelette_animal")
def ingere_type_squelette_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> type de squelette ; ENSEMBLE FERMÉ : endosquelette /
    # exosquelette / hydrosquelette. Textbook zoologie, FAUX=0. Vertébrés = endosquelette (requin = cartilage
    # mais interne → endo) ; arthropodes + escargot (coquille) = exosquelette ; vers/cnidaires = hydrosquelette.
    paires = [
        ("être humain", "endosquelette"), ("chien", "endosquelette"), ("poisson", "endosquelette"),
        ("requin", "endosquelette"), ("aigle royal", "endosquelette"), ("grenouille rousse", "endosquelette"),
        ("crabe", "exosquelette"), ("abeille", "exosquelette"), ("scorpion", "exosquelette"),
        ("escargot", "exosquelette"), ("crevette", "exosquelette"), ("homard", "exosquelette"),
        ("ver de terre", "hydrosquelette"), ("méduse", "hydrosquelette"),
        ("anémone de mer", "hydrosquelette"), ("sangsue", "hydrosquelette"),
        # — approfondissement run-autonome (type de squelette certain ; échinodermes = endo ossicules) —
        ("lion", "endosquelette"), ("cheval", "endosquelette"), ("baleine bleue", "endosquelette"),
        ("manchot empereur", "endosquelette"), ("python", "endosquelette"), ("tortue marine", "endosquelette"),
        ("salamandre", "endosquelette"), ("thon rouge", "endosquelette"),
        ("étoile de mer", "endosquelette"), ("oursin", "endosquelette"),
        ("fourmi", "exosquelette"), ("papillon", "exosquelette"), ("criquet", "exosquelette"),
        ("scarabée", "exosquelette"), ("araignée", "exosquelette"), ("écrevisse", "exosquelette"),
        ("moule", "exosquelette"), ("huître", "exosquelette"), ("bigorneau", "exosquelette"),
        ("hydre", "hydrosquelette"), ("planaire", "hydrosquelette"),
        # — approfondissement run-autonome v2 —
        ("belette", "endosquelette"), ("narval", "endosquelette"), ("anolis", "endosquelette"),
        ("pélican", "endosquelette"), ("gardon", "endosquelette"), ("crapaud", "endosquelette"),
        ("cétoine", "exosquelette"), ("capricorne", "exosquelette"), ("langouste", "exosquelette"),
        ("anatife", "exosquelette"), ("praire", "exosquelette"), ("telline", "exosquelette"),
        ("tubifex", "hydrosquelette"), ("arénicole", "hydrosquelette"), ("néréis", "hydrosquelette"),
    ]
    publie("type_squelette_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (type de squelette ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("regne_organisme")
def ingere_regne_organisme():
    # SOURCE = LE MODÈLE (directive Yohan). Organisme emblématique -> RÈGNE du vivant ; ENSEMBLE FERMÉ :
    # animal / végétal / champignon / bactérie. Textbook biologie, FAUX=0. (On s'en tient aux 4 règnes aux
    # exemplaires NON ambigus ; protistes/archées exclus = labels obscurs/débattus → on n'invente pas.)
    paires = [
        ("chien", "animal"), ("être humain", "animal"), ("abeille", "animal"), ("méduse", "animal"),
        ("aigle royal", "animal"),
        ("rosier", "végétal"), ("chêne", "végétal"), ("blé", "végétal"), ("fougère", "végétal"),
        ("mousse", "végétal"),
        ("champignon de Paris", "champignon"), ("levure de boulanger", "champignon"),
        ("amanite tue-mouches", "champignon"), ("pénicillium", "champignon"),
        ("Escherichia coli", "bactérie"), ("streptocoque", "bactérie"), ("bacille de Koch", "bactérie"),
        # — approfondissement run-autonome (règne certain, exemplaires non ambigus) —
        ("lion", "animal"), ("tigre", "animal"), ("éléphant d'Afrique", "animal"), ("baleine bleue", "animal"),
        ("requin", "animal"), ("papillon", "animal"), ("escargot", "animal"), ("pieuvre", "animal"),
        ("étoile de mer", "animal"), ("crabe", "animal"), ("fourmi", "animal"), ("serpent", "animal"),
        ("maïs", "végétal"), ("riz", "végétal"), ("tournesol", "végétal"), ("pommier", "végétal"),
        ("tulipe", "végétal"), ("lavande", "végétal"), ("olivier", "végétal"), ("sapin", "végétal"),
        ("pin", "végétal"),
        ("bolet", "champignon"), ("girolle", "champignon"), ("truffe", "champignon"), ("morille", "champignon"),
        ("staphylocoque", "bactérie"), ("pneumocoque", "bactérie"), ("salmonelle", "bactérie"),
        ("Helicobacter pylori", "bactérie"), ("Listeria", "bactérie"),
        # — approfondissement run-autonome (règne certain) —
        ("dauphin", "animal"), ("loutre", "animal"), ("hippocampe", "animal"), ("ver de terre", "animal"),
        ("sangsue", "animal"), ("oursin", "animal"), ("corbeau", "animal"), ("grenouille", "animal"),
        ("orchidée", "végétal"), ("bambou", "végétal"), ("cactus", "végétal"), ("nénuphar", "végétal"),
        ("menthe", "végétal"), ("basilic", "végétal"),
        ("cèpe", "champignon"), ("russule", "champignon"), ("pleurote", "champignon"), ("morille", "champignon"),
        ("Vibrio cholerae", "bactérie"), ("Clostridium tetani", "bactérie"),
        # — approfondissement run-autonome v3 —
        ("tigre", "animal"), ("loutre", "animal"), ("pieuvre", "animal"), ("crabe", "animal"),
        ("libellule", "animal"), ("crevette", "animal"),
        ("tournesol", "végétal"), ("tulipe", "végétal"), ("lavande", "végétal"), ("olivier", "végétal"),
        ("fougère", "végétal"),
        ("amanite phalloïde", "champignon"), ("girolle", "champignon"), ("bolet", "champignon"),
        ("Mycobacterium tuberculosis", "bactérie"), ("Yersinia pestis", "bactérie"),
    ]
    publie("regne_organisme", "physique",
           "Modèle (Claude) — biologie textbook curée (règne du vivant ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_metamorphose_insecte")
def ingere_type_metamorphose_insecte():
    # SOURCE = LE MODÈLE (directive Yohan). Insecte -> type de métamorphose ; ENSEMBLE FERMÉ : holométabole
    # (complète, avec nymphe) / hémimétabole (incomplète) / amétabole (aucune). Textbook entomologie, FAUX=0.
    paires = [
        ("papillon", "holométabole"), ("coléoptère", "holométabole"), ("mouche", "holométabole"),
        ("abeille", "holométabole"), ("fourmi", "holométabole"), ("moustique", "holométabole"),
        ("coccinelle", "holométabole"), ("scarabée", "holométabole"),
        ("sauterelle", "hémimétabole"), ("libellule", "hémimétabole"), ("criquet", "hémimétabole"),
        ("punaise", "hémimétabole"), ("blatte", "hémimétabole"), ("cigale", "hémimétabole"),
        ("lépisme", "amétabole"),
        # — approfondissement run-autonome (type de métamorphose certain) —
        ("guêpe", "holométabole"), ("frelon", "holométabole"), ("hanneton", "holométabole"),
        ("charançon", "holométabole"), ("doryphore", "holométabole"), ("puce", "holométabole"),
        ("bourdon", "holométabole"), ("taon", "holométabole"),
        ("perce-oreille", "hémimétabole"), ("mante religieuse", "hémimétabole"), ("phasme", "hémimétabole"),
        ("termite", "hémimétabole"), ("grillon", "hémimétabole"), ("puceron", "hémimétabole"),
        ("éphémère", "hémimétabole"),
        # — approfondissement run-autonome v2 —
        ("luciole", "holométabole"), ("ténébrion", "holométabole"), ("bousier", "holométabole"),
        ("dytique", "holométabole"), ("carabe", "holométabole"), ("cétoine", "holométabole"),
        ("capricorne", "holométabole"), ("lucane", "holométabole"),
        ("cercope", "hémimétabole"), ("gerris", "hémimétabole"), ("notonecte", "hémimétabole"),
        ("pou", "hémimétabole"), ("cochenille", "hémimétabole"),
        ("collembole", "amétabole"), ("machilis", "amétabole"),
    ]
    publie("type_metamorphose_insecte", "physique",
           "Modèle (Claude) — entomologie textbook curée (type de métamorphose ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("groupe_plante")
def ingere_groupe_plante():
    # SOURCE = LE MODÈLE (directive Yohan). Plante -> grand groupe végétal ; ENSEMBLE FERMÉ : angiosperme /
    # gymnosperme / fougère / mousse / algue. Textbook botanique, FAUX=0. Angiospermes = plantes à fleurs ;
    # gymnospermes = conifères/ginkgo (graines nues) ; fougères = ptéridophytes ; mousses = bryophytes.
    paires = [
        ("rosier", "angiosperme"), ("chêne", "angiosperme"), ("blé", "angiosperme"),
        ("tournesol", "angiosperme"), ("pommier", "angiosperme"), ("tulipe", "angiosperme"),
        ("pin", "gymnosperme"), ("sapin", "gymnosperme"), ("épicéa", "gymnosperme"),
        ("if", "gymnosperme"), ("ginkgo", "gymnosperme"),
        ("fougère aigle", "fougère"), ("polypode", "fougère"), ("prêle", "fougère"),
        ("sphaigne", "mousse"), ("polytric", "mousse"),
        ("laminaire", "algue"), ("fucus", "algue"),
        # — approfondissement run-autonome (grand groupe végétal certain) —
        ("maïs", "angiosperme"), ("riz", "angiosperme"), ("lavande", "angiosperme"),
        ("olivier", "angiosperme"), ("tomate", "angiosperme"), ("carotte", "angiosperme"),
        ("orchidée", "angiosperme"), ("palmier", "angiosperme"), ("bambou", "angiosperme"),
        ("nénuphar", "angiosperme"), ("menthe", "angiosperme"), ("lys", "angiosperme"),
        ("coquelicot", "angiosperme"),
        ("mélèze", "gymnosperme"), ("cèdre", "gymnosperme"), ("séquoia", "gymnosperme"),
        ("cyprès", "gymnosperme"), ("genévrier", "gymnosperme"),
        ("capillaire", "fougère"),
        ("ulve", "algue"), ("sargasse", "algue"),
    ]
    publie("groupe_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (grand groupe végétal ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_muscle")
def ingere_type_muscle():
    # SOURCE = LE MODÈLE (directive Yohan). Muscle -> type histologique ; ENSEMBLE FERMÉ : strié squelettique /
    # lisse / cardiaque. Textbook histologie, FAUX=0. Squelettiques = volontaires (biceps, diaphragme) ;
    # lisses = involontaires des viscères ; cardiaque = myocarde (strié mais involontaire, catégorie à part).
    paires = [
        ("biceps", "strié squelettique"), ("quadriceps", "strié squelettique"),
        ("deltoïde", "strié squelettique"), ("diaphragme", "strié squelettique"),
        ("myocarde", "cardiaque"),
        ("muscle de l'estomac", "lisse"), ("muscle de l'intestin", "lisse"),
        ("muscle de la vessie", "lisse"), ("muscle des artères", "lisse"),
        # — approfondissement run-autonome (type histologique certain) —
        ("triceps", "strié squelettique"), ("grand pectoral", "strié squelettique"),
        ("grand dorsal", "strié squelettique"), ("trapèze", "strié squelettique"),
        ("masséter", "strié squelettique"), ("gastrocnémien", "strié squelettique"),
        ("soléaire", "strié squelettique"), ("langue", "strié squelettique"),
        ("grand glutéal", "strié squelettique"),
        ("muscle de l'utérus", "lisse"), ("muscle des bronches", "lisse"),
        ("muscle de l'œsophage", "lisse"), ("muscle de l'iris", "lisse"), ("muscle du côlon", "lisse"),
        # — approfondissement run-autonome v2 —
        ("abdominaux", "strié squelettique"), ("ischio-jambiers", "strié squelettique"),
        ("muscle brachial", "strié squelettique"), ("sartorius", "strié squelettique"),
        ("muscle ciliaire", "lisse"), ("muscle de l'urètre", "lisse"), ("muscle de la trachée", "lisse"),
    ]
    publie("type_muscle", "physique",
           "Modèle (Claude) — histologie textbook curée (type de muscle ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("forme_bacterie")
def ingere_forme_bacterie():
    # SOURCE = LE MODÈLE (directive Yohan). Bactérie -> forme (morphologie) ; ENSEMBLE FERMÉ : coque / bacille /
    # spirille / vibrion. Textbook microbiologie, FAUX=0. coque = sphérique, bacille = bâtonnet, spirille =
    # hélicoïdale, vibrion = virgule.
    paires = [
        ("staphylocoque", "coque"), ("streptocoque", "coque"), ("pneumocoque", "coque"),
        ("méningocoque", "coque"), ("gonocoque", "coque"),
        ("Escherichia coli", "bacille"), ("salmonelle", "bacille"), ("bacille de Koch", "bacille"),
        ("bacille du tétanos", "bacille"),
        ("Vibrio cholerae", "vibrion"),
        ("Helicobacter pylori", "spirille"),
        # — approfondissement run-autonome (morphologie certaine ; bacilles) —
        ("entérocoque", "coque"),
        ("Listeria", "bacille"), ("Bacillus anthracis", "bacille"), ("Pseudomonas aeruginosa", "bacille"),
        ("Klebsiella pneumoniae", "bacille"), ("Shigella", "bacille"), ("Legionella pneumophila", "bacille"),
        ("Lactobacillus", "bacille"), ("Clostridium botulinum", "bacille"),
        ("Corynebacterium diphtheriae", "bacille"),
        # — approfondissement run-autonome v2 (morphologie certaine) —
        ("Proteus", "bacille"), ("Enterobacter", "bacille"), ("Serratia", "bacille"),
        ("Mycobacterium tuberculosis", "bacille"), ("Bacillus subtilis", "bacille"),
        ("Yersinia pestis", "bacille"), ("Bordetella pertussis", "bacille"),
        ("Neisseria", "coque"), ("Moraxella", "coque"),
        ("Campylobacter jejuni", "spirille"), ("Treponema pallidum", "spirille"),
        ("Borrelia burgdorferi", "spirille"), ("Leptospira", "spirille"),
    ]
    publie("forme_bacterie", "physique",
           "Modèle (Claude) — microbiologie textbook curée (forme bactérienne ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("coloration_gram_bacterie")
def ingere_coloration_gram_bacterie():
    # SOURCE = LE MODÈLE (directive Yohan). Bactérie -> réponse à la coloration de Gram ; ENSEMBLE FERMÉ :
    # Gram positif / Gram négatif. Textbook bactériologie, FAUX=0. PIÈGE PÉDAGOGIQUE : méningocoque/gonocoque
    # sont des COQUES mais Gram NÉGATIF (Neisseria). Bacille de Koch EXCLU (acido-alcoolo-résistant, statut Gram
    # ambigu → on n'invente pas).
    paires = [
        ("staphylocoque doré", "Gram positif"), ("streptocoque", "Gram positif"),
        ("pneumocoque", "Gram positif"), ("Clostridium tetani", "Gram positif"),
        ("Listeria", "Gram positif"),
        ("Escherichia coli", "Gram négatif"), ("salmonelle", "Gram négatif"),
        ("Vibrio cholerae", "Gram négatif"), ("Helicobacter pylori", "Gram négatif"),
        ("méningocoque", "Gram négatif"), ("gonocoque", "Gram négatif"),
        ("Pseudomonas aeruginosa", "Gram négatif"),
        # — approfondissement run-autonome (coloration de Gram certaine) —
        ("entérocoque", "Gram positif"), ("Bacillus anthracis", "Gram positif"),
        ("Corynebacterium diphtheriae", "Gram positif"), ("Clostridium botulinum", "Gram positif"),
        ("Lactobacillus", "Gram positif"), ("Streptococcus pyogenes", "Gram positif"),
        ("Clostridioides difficile", "Gram positif"),
        ("Klebsiella pneumoniae", "Gram négatif"), ("Legionella pneumophila", "Gram négatif"),
        ("Shigella", "Gram négatif"), ("Salmonella", "Gram négatif"),
        ("Campylobacter jejuni", "Gram négatif"), ("Bordetella pertussis", "Gram négatif"),
        ("Haemophilus influenzae", "Gram négatif"), ("Yersinia pestis", "Gram négatif"),
        # — approfondissement run-autonome v2 (Gram certain) —
        ("Brucella", "Gram négatif"), ("Francisella tularensis", "Gram négatif"),
        ("Bacteroides", "Gram négatif"), ("Proteus", "Gram négatif"), ("Acinetobacter", "Gram négatif"),
        ("Moraxella", "Gram négatif"), ("Neisseria", "Gram négatif"),
        ("Actinomyces", "Gram positif"), ("Corynebacterium diphtheriae", "Gram positif"),
        ("Bacillus anthracis", "Gram positif"),
    ]
    publie("coloration_gram_bacterie", "physique",
           "Modèle (Claude) — bactériologie textbook curée (coloration de Gram ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_glande")
def ingere_type_glande():
    # SOURCE = LE MODÈLE (directive Yohan). Glande -> type sécrétoire ; ENSEMBLE FERMÉ : endocrine (déverse
    # dans le sang) / exocrine (déverse par un canal) / mixte. Textbook physiologie, FAUX=0. Pancréas = mixte
    # (îlots endocrines + acini exocrines).
    paires = [
        ("thyroïde", "endocrine"), ("hypophyse", "endocrine"), ("glande surrénale", "endocrine"),
        ("parathyroïde", "endocrine"), ("épiphyse", "endocrine"),
        ("glande salivaire", "exocrine"), ("glande sudoripare", "exocrine"),
        ("glande sébacée", "exocrine"), ("glande lacrymale", "exocrine"),
        ("glande mammaire", "exocrine"), ("foie", "exocrine"),
        ("pancréas", "mixte"),
        # — approfondissement run-autonome (type sécrétoire certain) —
        ("glande gastrique", "exocrine"), ("prostate", "exocrine"), ("glande cérumineuse", "exocrine"),
        ("glande de Bartholin", "exocrine"),
        ("testicule", "mixte"), ("ovaire", "mixte"),
        # — approfondissement run-autonome v2 —
        ("corps jaune", "endocrine"), ("placenta", "endocrine"),
        ("glande de Meibomius", "exocrine"), ("glande de Brunner", "exocrine"),
        ("glande intestinale", "exocrine"), ("glande à venin", "exocrine"),
        ("glande de Cowper", "exocrine"), ("glande gastrique", "exocrine"),
    ]
    publie("type_glande", "physique",
           "Modèle (Claude) — physiologie textbook curée (type de glande ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_nutrition")
def ingere_mode_nutrition():
    # SOURCE = LE MODÈLE (directive Yohan). Organisme -> mode de nutrition ; ENSEMBLE FERMÉ : autotrophe
    # (produit sa matière organique, ex. photosynthèse) / hétérotrophe (la prélève sur d'autres). Textbook
    # biologie, FAUX=0. Plantes/algues = autotrophes ; animaux/champignons = hétérotrophes.
    paires = [
        ("rosier", "autotrophe"), ("chêne", "autotrophe"), ("blé", "autotrophe"),
        ("laminaire", "autotrophe"), ("tournesol", "autotrophe"),
        ("être humain", "hétérotrophe"), ("lion", "hétérotrophe"), ("champignon de Paris", "hétérotrophe"),
        ("levure de boulanger", "hétérotrophe"), ("abeille", "hétérotrophe"), ("ver de terre", "hétérotrophe"),
        # — approfondissement run-autonome (mode de nutrition certain) —
        ("maïs", "autotrophe"), ("riz", "autotrophe"), ("fougère", "autotrophe"), ("mousse", "autotrophe"),
        ("cyanobactérie", "autotrophe"), ("sapin", "autotrophe"), ("olivier", "autotrophe"),
        ("cactus", "autotrophe"),
        ("tigre", "hétérotrophe"), ("vache", "hétérotrophe"), ("requin", "hétérotrophe"),
        ("méduse", "hétérotrophe"), ("escargot", "hétérotrophe"), ("moisissure", "hétérotrophe"),
        ("amibe", "hétérotrophe"), ("ténia", "hétérotrophe"),
        # — approfondissement run-autonome v2 —
        ("orge", "autotrophe"), ("avoine", "autotrophe"), ("pin", "autotrophe"), ("sapin", "autotrophe"),
        ("spiruline", "autotrophe"), ("phytoplancton", "autotrophe"), ("fougère", "autotrophe"),
        ("paramécie", "hétérotrophe"), ("hydre", "hétérotrophe"), ("ver de terre", "hétérotrophe"),
        ("papillon", "hétérotrophe"), ("moisissure", "hétérotrophe"),
    ]
    publie("mode_nutrition", "physique",
           "Modèle (Claude) — biologie textbook curée (mode de nutrition ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_vaisseau_sanguin")
def ingere_type_vaisseau_sanguin():
    # SOURCE = LE MODÈLE (directive Yohan). Vaisseau -> type ; ENSEMBLE FERMÉ : artère (part du cœur) / veine
    # (revient au cœur) / capillaire. Textbook anatomie, FAUX=0. PIÈGE : artère pulmonaire (sang désoxygéné) et
    # veine pulmonaire (sang oxygéné) gardent leur TYPE structurel (départ/retour du cœur), pas selon l'oxygène.
    paires = [
        ("aorte", "artère"), ("artère pulmonaire", "artère"), ("artère carotide", "artère"),
        ("artère fémorale", "artère"), ("artère coronaire", "artère"),
        ("veine cave", "veine"), ("veine porte", "veine"), ("veine jugulaire", "veine"),
        ("veine pulmonaire", "veine"), ("veine saphène", "veine"),
        ("capillaire sanguin", "capillaire"),
        # — approfondissement run-autonome (type de vaisseau certain) —
        ("artère rénale", "artère"), ("artère iliaque", "artère"), ("artère mésentérique", "artère"),
        ("artère sous-clavière", "artère"), ("artère brachiale", "artère"), ("artère radiale", "artère"),
        ("artère hépatique", "artère"),
        ("veine fémorale", "veine"), ("veine rénale", "veine"), ("veine iliaque", "veine"),
        ("veine sous-clavière", "veine"), ("veine basilique", "veine"), ("veine céphalique", "veine"),
        ("capillaire glomérulaire", "capillaire"),
        # — approfondissement run-autonome v2 —
        ("artère splénique", "artère"), ("artère ophtalmique", "artère"), ("artère cérébrale", "artère"),
        ("artère poplitée", "artère"), ("artère axillaire", "artère"), ("tronc cœliaque", "artère"),
        ("veine azygos", "veine"), ("veine cave supérieure", "veine"), ("veine poplitée", "veine"),
        ("veine axillaire", "veine"), ("veine ombilicale", "veine"), ("veine mésentérique", "veine"),
        ("capillaire pulmonaire", "capillaire"),
    ]
    publie("type_vaisseau_sanguin", "physique",
           "Modèle (Claude) — anatomie textbook curée (type de vaisseau sanguin ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_leucocyte")
def ingere_type_leucocyte():
    # SOURCE = LE MODÈLE (directive Yohan). Globule blanc -> grande classe ; ENSEMBLE FERMÉ : granulocyte
    # (polynucléaire) / agranulocyte (mononucléaire). Textbook hématologie, FAUX=0. Neutrophile/éosinophile/
    # basophile = granulocytes ; lymphocyte/monocyte = agranulocytes.
    paires = [
        ("neutrophile", "granulocyte"), ("éosinophile", "granulocyte"), ("basophile", "granulocyte"),
        ("lymphocyte", "agranulocyte"), ("monocyte", "agranulocyte"),
        # — approfondissement run-autonome (classe de leucocyte certaine) —
        ("polynucléaire neutrophile", "granulocyte"), ("polynucléaire éosinophile", "granulocyte"),
        ("polynucléaire basophile", "granulocyte"),
        ("lymphocyte B", "agranulocyte"), ("lymphocyte T", "agranulocyte"), ("cellule NK", "agranulocyte"),
    ]
    publie("type_leucocyte", "physique",
           "Modèle (Claude) — hématologie textbook curée (classe de leucocyte ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("os_type")
def ingere_os_type():
    # SOURCE = LE MODÈLE (directive Yohan). Os -> type morphologique ; ENSEMBLE FERMÉ : long / court / plat /
    # irrégulier / sésamoïde. Textbook anatomie, FAUX=0. Côte = os PLAT (classification standard) ; rotule =
    # sésamoïde (le plus gros) ; vertèbre = irrégulier.
    paires = [
        ("fémur", "long"), ("humérus", "long"), ("tibia", "long"), ("radius", "long"), ("phalange", "long"),
        ("os du carpe", "court"), ("os du tarse", "court"), ("scaphoïde", "court"),
        ("sternum", "plat"), ("omoplate", "plat"), ("os pariétal", "plat"), ("os frontal", "plat"), ("côte", "plat"),
        ("vertèbre", "irrégulier"), ("os iliaque", "irrégulier"), ("sacrum", "irrégulier"),
        ("rotule", "sésamoïde"),
        # — approfondissement run-autonome (type d'os certain, closed-set) —
        ("cubitus", "long"), ("péroné", "long"), ("métacarpien", "long"), ("métatarsien", "long"),
        ("clavicule", "long"),
        ("lunatum", "court"), ("trapèze", "court"), ("calcanéus", "court"), ("cuboïde", "court"),
        ("os occipital", "plat"), ("os temporal", "plat"), ("os nasal", "plat"),
        ("sphénoïde", "irrégulier"), ("ethmoïde", "irrégulier"), ("mandibule", "irrégulier"),
        ("maxillaire", "irrégulier"), ("os hyoïde", "irrégulier"),
        # — approfondissement run-autonome v2 —
        ("pisiforme", "court"), ("trapézoïde", "court"), ("capitatum", "court"), ("hamatum", "court"),
        ("cunéiforme", "court"), ("talus", "court"), ("scaphoïde", "court"),
        ("os zygomatique", "irrégulier"), ("palatin", "irrégulier"), ("atlas", "irrégulier"),
        ("axis", "irrégulier"),
        ("vomer", "plat"), ("os lacrymal", "plat"),
    ]
    publie("os_type", "physique",
           "Modèle (Claude) — anatomie textbook curée (type d'os ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_racine_plante")
def ingere_type_racine_plante():
    # SOURCE = LE MODÈLE (directive Yohan). Plante -> type d'appareil racinaire ; ENSEMBLE FERMÉ : pivotante
    # (1 racine principale) / fasciculée (en touffe, monocotylédones) / adventice (sur tige/feuille). Textbook
    # botanique, FAUX=0.
    paires = [
        ("carotte", "pivotante"), ("betterave", "pivotante"), ("pissenlit", "pivotante"),
        ("chêne", "pivotante"), ("radis", "pivotante"),
        ("blé", "fasciculée"), ("maïs", "fasciculée"), ("poireau", "fasciculée"), ("gazon", "fasciculée"),
        ("lierre", "adventice"), ("fraisier", "adventice"),
        # — approfondissement run-autonome (type racinaire certain) —
        ("navet", "pivotante"), ("panais", "pivotante"), ("luzerne", "pivotante"),
        ("soja", "pivotante"), ("haricot", "pivotante"), ("tournesol", "pivotante"),
        ("riz", "fasciculée"), ("orge", "fasciculée"), ("avoine", "fasciculée"),
        ("oignon", "fasciculée"), ("ail", "fasciculée"), ("tulipe", "fasciculée"), ("bambou", "fasciculée"),
        ("menthe", "adventice"),
    ]
    publie("type_racine_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (type de racine ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_tige_plante")
def ingere_type_tige_plante():
    # SOURCE = LE MODÈLE (directive Yohan). Plante -> nature de la tige ; ENSEMBLE FERMÉ : herbacée (tendre,
    # verte) / ligneuse (bois). Textbook botanique, FAUX=0.
    paires = [
        ("blé", "herbacée"), ("tournesol", "herbacée"), ("pissenlit", "herbacée"),
        ("tulipe", "herbacée"), ("maïs", "herbacée"), ("fougère aigle", "herbacée"),
        ("chêne", "ligneuse"), ("pin", "ligneuse"), ("rosier", "ligneuse"),
        ("pommier", "ligneuse"), ("vigne", "ligneuse"),
        # — approfondissement run-autonome (nature de tige certaine) —
        ("riz", "herbacée"), ("orge", "herbacée"), ("avoine", "herbacée"), ("menthe", "herbacée"),
        ("basilic", "herbacée"), ("persil", "herbacée"), ("laitue", "herbacée"),
        ("marguerite", "herbacée"), ("coquelicot", "herbacée"), ("trèfle", "herbacée"),
        ("hêtre", "ligneuse"), ("sapin", "ligneuse"), ("épicéa", "ligneuse"), ("olivier", "ligneuse"),
        ("cerisier", "ligneuse"), ("poirier", "ligneuse"), ("bouleau", "ligneuse"), ("érable", "ligneuse"),
        ("peuplier", "ligneuse"), ("lilas", "ligneuse"),
    ]
    publie("type_tige_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (nature de la tige ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("niveau_trophique")
def ingere_niveau_trophique():
    # SOURCE = LE MODÈLE (directive Yohan). Organisme -> niveau trophique ; ENSEMBLE FERMÉ : producteur
    # (autotrophe) / consommateur (mange d'autres êtres) / décomposeur (recycle la matière morte). Textbook
    # écologie, FAUX=0. Cohérent avec mode_nutrition (producteur=autotrophe, consommateur/décomposeur=hétéro).
    paires = [
        ("chêne", "producteur"), ("blé", "producteur"), ("laminaire", "producteur"),
        ("rosier", "producteur"), ("phytoplancton", "producteur"),
        ("lion", "consommateur"), ("lapin", "consommateur"), ("être humain", "consommateur"),
        ("abeille", "consommateur"), ("requin", "consommateur"),
        ("champignon de Paris", "décomposeur"), ("ver de terre", "décomposeur"),
        ("Escherichia coli", "décomposeur"),
        # — approfondissement run-autonome (niveau trophique certain) —
        ("maïs", "producteur"), ("riz", "producteur"), ("tournesol", "producteur"),
        ("sapin", "producteur"), ("mousse", "producteur"), ("fougère", "producteur"),
        ("tigre", "consommateur"), ("vache", "consommateur"), ("mouton", "consommateur"),
        ("loup", "consommateur"), ("aigle royal", "consommateur"), ("souris", "consommateur"),
        ("papillon", "consommateur"), ("escargot", "consommateur"), ("dauphin", "consommateur"),
        ("sardine", "consommateur"), ("méduse", "consommateur"), ("grenouille", "consommateur"),
        ("moisissure", "décomposeur"),
        # — approfondissement run-autonome v2 —
        ("orge", "producteur"), ("avoine", "producteur"), ("mousse", "producteur"), ("fougère", "producteur"),
        ("tigre", "consommateur"), ("loup", "consommateur"), ("hibou", "consommateur"),
        ("renard roux", "consommateur"), ("abeille", "consommateur"), ("sardine", "consommateur"),
        ("levure de boulanger", "décomposeur"), ("cloporte", "décomposeur"),
    ]
    publie("niveau_trophique", "physique",
           "Modèle (Claude) — écologie textbook curée (niveau trophique ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_fecondation")
def ingere_type_fecondation():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> type de fécondation ; ENSEMBLE FERMÉ : externe (gamètes
    # rejetés dans le milieu, surtout aquatique) / interne. Textbook zoologie, FAUX=0. EXCEPTION : le requin a
    # une fécondation INTERNE (ptérygopodes), contrairement aux poissons osseux.
    paires = [
        ("saumon atlantique", "externe"), ("carpe", "externe"), ("truite", "externe"),
        ("grenouille rousse", "externe"), ("oursin", "externe"), ("corail", "externe"),
        ("être humain", "interne"), ("chien", "interne"), ("aigle royal", "interne"),
        ("serpent", "interne"), ("requin", "interne"), ("abeille", "interne"), ("escargot", "interne"),
        # — approfondissement run-autonome (type de fécondation certain) —
        ("morue", "externe"), ("sardine", "externe"), ("hareng", "externe"), ("thon rouge", "externe"),
        ("anguille", "externe"), ("méduse", "externe"), ("étoile de mer", "externe"),
        ("moule", "externe"), ("huître", "externe"),
        ("lion", "interne"), ("vache", "interne"), ("cheval", "interne"), ("python", "interne"),
        ("crocodile du Nil", "interne"), ("tortue marine", "interne"), ("pigeon", "interne"),
        ("scorpion", "interne"), ("araignée", "interne"), ("fourmi", "interne"),
    ]
    publie("type_fecondation", "physique",
           "Modèle (Claude) — zoologie textbook curée (type de fécondation ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_developpement")
def ingere_type_developpement():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> type de développement ; ENSEMBLE FERMÉ : direct (le jeune
    # ressemble à l'adulte) / indirect (passe par une larve + métamorphose). Textbook zoologie, FAUX=0.
    # EXCEPTION : l'araignée a un développement DIRECT (pas de stade larvaire), contrairement aux insectes.
    paires = [
        ("grenouille rousse", "indirect"), ("papillon", "indirect"), ("coccinelle", "indirect"),
        ("mouche", "indirect"), ("abeille", "indirect"), ("oursin", "indirect"), ("crabe", "indirect"),
        ("être humain", "direct"), ("chien", "direct"), ("aigle royal", "direct"),
        ("serpent", "direct"), ("araignée", "direct"), ("escargot", "direct"), ("scorpion", "direct"),
        # — approfondissement run-autonome (développement direct/indirect certain) —
        ("moustique", "indirect"), ("guêpe", "indirect"), ("scarabée", "indirect"),
        ("libellule", "indirect"), ("crapaud", "indirect"), ("salamandre", "indirect"),
        ("homard", "indirect"), ("étoile de mer", "indirect"),
        ("lion", "direct"), ("cheval", "direct"), ("vache", "direct"), ("python", "direct"),
        ("tortue marine", "direct"), ("pigeon", "direct"), ("souris", "direct"),
    ]
    publie("type_developpement", "physique",
           "Modèle (Claude) — zoologie textbook curée (développement direct/indirect ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("appareil_circulatoire_type")
def ingere_appareil_circulatoire_type():
    # SOURCE = LE MODÈLE (directive Yohan). Animal -> type de circulation ; ENSEMBLE FERMÉ : ouverte (hémolymphe
    # baignant les organes) / fermée (sang confiné dans des vaisseaux). Textbook zoologie, FAUX=0. EXCEPTIONS :
    # la pieuvre (céphalopode) a une circulation FERMÉE, contrairement aux autres mollusques ; le ver de terre
    # (annélide) aussi.
    paires = [
        ("abeille", "ouverte"), ("criquet", "ouverte"), ("papillon", "ouverte"),
        ("escargot", "ouverte"), ("crabe", "ouverte"), ("crevette", "ouverte"), ("araignée", "ouverte"),
        ("être humain", "fermée"), ("carpe", "fermée"), ("aigle royal", "fermée"),
        ("ver de terre", "fermée"), ("pieuvre", "fermée"), ("sangsue", "fermée"),
        # — approfondissement run-autonome (circulation ouverte/fermée certaine) —
        ("fourmi", "ouverte"), ("mouche", "ouverte"), ("scarabée", "ouverte"), ("scorpion", "ouverte"),
        ("homard", "ouverte"), ("écrevisse", "ouverte"), ("moule", "ouverte"), ("huître", "ouverte"),
        ("coccinelle", "ouverte"), ("libellule", "ouverte"),
        ("lion", "fermée"), ("chien", "fermée"), ("dauphin", "fermée"), ("requin", "fermée"),
        ("serpent", "fermée"), ("grenouille", "fermée"), ("calmar", "fermée"), ("seiche", "fermée"),
        ("néréis", "fermée"),
    ]
    publie("appareil_circulatoire_type", "physique",
           "Modèle (Claude) — zoologie textbook curée (circulation ouverte/fermée ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_cellule")
def ingere_type_cellule():
    # SOURCE = LE MODÈLE (directive Yohan). Cellule/organisme -> type cellulaire ; ENSEMBLE FERMÉ : procaryote
    # (sans noyau, bactéries/archées) / eucaryote (à noyau). Textbook biologie cellulaire, FAUX=0.
    paires = [
        ("Escherichia coli", "procaryote"), ("staphylocoque", "procaryote"),
        ("cyanobactérie", "procaryote"), ("bacille de Koch", "procaryote"),
        ("neurone", "eucaryote"), ("levure de boulanger", "eucaryote"), ("paramécie", "eucaryote"),
        ("cellule musculaire", "eucaryote"), ("hépatocyte", "eucaryote"), ("amibe", "eucaryote"),
        # — approfondissement run-autonome (type cellulaire certain) —
        ("salmonelle", "procaryote"), ("Vibrio cholerae", "procaryote"), ("Helicobacter pylori", "procaryote"),
        ("Listeria", "procaryote"), ("pneumocoque", "procaryote"), ("streptocoque", "procaryote"),
        ("entérocoque", "procaryote"), ("méningocoque", "procaryote"),
        ("spermatozoïde", "eucaryote"), ("ovule", "eucaryote"), ("lymphocyte", "eucaryote"),
        ("fibroblaste", "eucaryote"), ("ostéocyte", "eucaryote"), ("cellule végétale", "eucaryote"),
        ("moisissure", "eucaryote"), ("Plasmodium", "eucaryote"),
        # — approfondissement run-autonome v2 (archées = procaryotes) —
        ("méthanogène", "procaryote"), ("halobactérie", "procaryote"),
        ("Mycobacterium tuberculosis", "procaryote"), ("Pseudomonas aeruginosa", "procaryote"),
        ("euglène", "eucaryote"), ("trypanosome", "eucaryote"), ("globule blanc", "eucaryote"),
        ("ostéoblaste", "eucaryote"), ("cellule épithéliale", "eucaryote"),
    ]
    publie("type_cellule", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (procaryote/eucaryote ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("nature_hormone")
def ingere_nature_hormone():
    # SOURCE = LE MODÈLE (directive Yohan). Hormone -> nature biochimique ; ENSEMBLE FERMÉ : peptidique /
    # stéroïde / dérivée d'acide aminé. Textbook endocrinologie, FAUX=0. Stéroïdes = dérivés du cholestérol
    # (sexuelles + corticostéroïdes) ; dérivées d'AA = catécholamines + hormones thyroïdiennes + mélatonine.
    paires = [
        ("insuline", "peptidique"), ("glucagon", "peptidique"), ("hormone de croissance", "peptidique"),
        ("ocytocine", "peptidique"), ("prolactine", "peptidique"),
        ("testostérone", "stéroïde"), ("œstrogène", "stéroïde"), ("progestérone", "stéroïde"),
        ("cortisol", "stéroïde"), ("aldostérone", "stéroïde"),
        ("adrénaline", "dérivée d'acide aminé"), ("noradrénaline", "dérivée d'acide aminé"),
        ("thyroxine", "dérivée d'acide aminé"), ("mélatonine", "dérivée d'acide aminé"),
        # — approfondissement run-autonome (nature biochimique certaine) —
        ("hormone antidiurétique", "peptidique"), ("calcitonine", "peptidique"),
        ("parathormone", "peptidique"), ("sécrétine", "peptidique"), ("gastrine", "peptidique"),
        ("leptine", "peptidique"), ("ghréline", "peptidique"), ("thyréostimuline", "peptidique"),
        ("œstradiol", "stéroïde"), ("DHEA", "stéroïde"), ("corticostérone", "stéroïde"),
        ("triiodothyronine", "dérivée d'acide aminé"), ("dopamine", "dérivée d'acide aminé"),
        # — approfondissement run-autonome v2 (nature certaine) —
        ("cholécystokinine", "peptidique"), ("motiline", "peptidique"), ("érythropoïétine", "peptidique"),
        ("vasopressine", "peptidique"), ("inhibine", "peptidique"), ("relaxine", "peptidique"),
        ("glucagon", "peptidique"),
        ("cortisone", "stéroïde"), ("calcitriol", "stéroïde"), ("désoxycorticostérone", "stéroïde"),
    ]
    publie("nature_hormone", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (nature d'hormone ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("classe_enzyme")
def ingere_classe_enzyme():
    # SOURCE = LE MODÈLE (directive Yohan). Enzyme -> classe EC ; ENSEMBLE FERMÉ : oxydoréductase / transférase /
    # hydrolase / lyase / isomérase / ligase. Textbook biochimie (nomenclature EC), FAUX=0.
    paires = [
        ("catalase", "oxydoréductase"), ("lactate déshydrogénase", "oxydoréductase"),
        ("ADN polymérase", "transférase"), ("hexokinase", "transférase"),
        ("amylase", "hydrolase"), ("lipase", "hydrolase"), ("pepsine", "hydrolase"),
        ("trypsine", "hydrolase"), ("lactase", "hydrolase"), ("lysozyme", "hydrolase"),
        ("anhydrase carbonique", "lyase"), ("aldolase", "lyase"),
        ("phosphoglucose isomérase", "isomérase"),
        ("ADN ligase", "ligase"),
        # — approfondissement run-autonome (classe EC certaine) —
        ("peroxydase", "oxydoréductase"), ("alcool déshydrogénase", "oxydoréductase"),
        ("créatine kinase", "transférase"), ("aspartate aminotransférase", "transférase"),
        ("chymotrypsine", "hydrolase"), ("ribonucléase", "hydrolase"), ("uréase", "hydrolase"),
        ("phosphatase alcaline", "hydrolase"), ("cellulase", "hydrolase"), ("maltase", "hydrolase"),
        ("élastase", "hydrolase"),
        ("fumarase", "lyase"), ("pyruvate décarboxylase", "lyase"),
        ("triose phosphate isomérase", "isomérase"),
        ("pyruvate carboxylase", "ligase"),
        # — approfondissement run-autonome v2 (classe EC certaine) —
        ("glucose-6-phosphate déshydrogénase", "oxydoréductase"), ("monoamine oxydase", "oxydoréductase"),
        ("pyruvate kinase", "transférase"), ("glucokinase", "transférase"),
        ("maltase", "hydrolase"), ("nucléase", "hydrolase"), ("phospholipase", "hydrolase"),
        ("citrate lyase", "lyase"),
        ("topoisomérase", "isomérase"),
        ("glutamine synthétase", "ligase"),
    ]
    publie("classe_enzyme", "physique",
           "Modèle (Claude) — biochimie textbook curée (classe EC d'enzyme ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_acide_amine")
def ingere_type_acide_amine():
    # SOURCE = LE MODÈLE (directive Yohan). Acide aminé -> essentiel/non-essentiel CHEZ L'HUMAIN ; ENSEMBLE
    # FERMÉ. Textbook nutrition/biochimie, FAUX=0. ⚠️ N'inclut QUE les cas NON AMBIGUS : les 9 essentiels stricts
    # et 5 non-essentiels nets. EXCLUS = les conditionnellement essentiels (arginine, cystéine, glutamine,
    # glycine, proline, tyrosine) pour ne pas trancher un cas débattu.
    paires = [
        ("leucine", "essentiel"), ("isoleucine", "essentiel"), ("valine", "essentiel"),
        ("lysine", "essentiel"), ("méthionine", "essentiel"), ("phénylalanine", "essentiel"),
        ("thréonine", "essentiel"), ("tryptophane", "essentiel"), ("histidine", "essentiel"),
        ("alanine", "non-essentiel"), ("asparagine", "non-essentiel"), ("aspartate", "non-essentiel"),
        ("glutamate", "non-essentiel"), ("sérine", "non-essentiel"),
    ]
    publie("type_acide_amine", "physique",
           "Modèle (Claude) — biochimie/nutrition textbook curée (AA essentiel/non-essentiel chez l'humain ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("base_azotee_type")
def ingere_base_azotee_type():
    # SOURCE = LE MODÈLE (directive Yohan). Base azotée -> famille ; ENSEMBLE FERMÉ : purine (2 cycles) /
    # pyrimidine (1 cycle). Textbook biologie moléculaire, FAUX=0. Purines = Adénine, Guanine ; pyrimidines =
    # Cytosine, Thymine, Uracile.
    paires = [
        ("adénine", "purine"), ("guanine", "purine"),
        ("cytosine", "pyrimidine"), ("thymine", "pyrimidine"), ("uracile", "pyrimidine"),
    ]
    publie("base_azotee_type", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (purine/pyrimidine ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("appariement_base_adn")
def ingere_appariement_base_adn():
    # SOURCE = LE MODÈLE (directive Yohan). Base de l'ADN -> base complémentaire DANS L'ADN (Watson-Crick) ;
    # fonctionnel. Textbook, FAUX=0. A-T et G-C (dans l'ADN ; dans l'ARN l'adénine s'apparie à l'uracile, hors
    # périmètre ici pour rester fonctionnel univoque ADN).
    paires = [
        ("adénine", "thymine"), ("thymine", "adénine"),
        ("guanine", "cytosine"), ("cytosine", "guanine"),
    ]
    publie("appariement_base_adn", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (appariement Watson-Crick ADN ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("nombre_chromosomes_espece")
def ingere_nombre_chromosomes_espece():
    # SOURCE = LE MODÈLE (directive Yohan). Espèce -> nombre de chromosomes (2n, cellule somatique). Valeurs =
    # entiers (chaînes). Textbook génétique, FAUX=0 ; valeurs canoniques non contestées. Pas un petit ensemble
    # fermé -> sanité par ANCRES + plage plausible.
    paires = [
        ("être humain", "46"), ("chimpanzé", "48"), ("chien", "78"), ("chat", "38"),
        ("souris domestique", "40"), ("drosophile", "8"), ("pois", "14"), ("maïs", "20"),
        ("blé tendre", "42"), ("poule", "78"), ("vache", "60"), ("cheval", "64"),
        # — approfondissement après-midi (valeurs 2n canoniques certaines) —
        ("mouton", "54"), ("chèvre", "60"), ("âne", "62"), ("lapin", "44"), ("rat", "42"),
        ("gorille", "48"), ("orang-outan", "48"), ("pomme de terre", "48"),
        ("tomate", "24"), ("riz", "24"), ("oignon", "16"),
    ]
    publie("nombre_chromosomes_espece", "physique",
           "Modèle (Claude) — génétique textbook curée (nombre de chromosomes 2n ; valeurs canoniques ; FAUX=0 vérifié)", paires)


@domaine("fonction_arn")
def ingere_fonction_arn():
    # SOURCE = LE MODÈLE (directive Yohan). Type d'ARN -> fonction principale. Textbook biologie moléculaire,
    # FAUX=0 ; fonctionnel (un type d'ARN -> une fonction canonique).
    paires = [
        ("ARN messager", "transmission de l'information génétique"),
        ("ARN de transfert", "transport des acides aminés"),
        ("ARN ribosomique", "constitution des ribosomes"),
        ("ARN interférent", "régulation de l'expression génétique"),
    ]
    publie("fonction_arn", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (fonction des types d'ARN ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("fonction_tissu_vegetal")
def ingere_fonction_tissu_vegetal():
    # SOURCE = LE MODÈLE (directive Yohan). Tissu végétal -> fonction principale. Textbook botanique, FAUX=0 ;
    # cas univoques uniquement (parenchyme multifonctionnel exclu pour rester fonctionnel).
    paires = [
        ("xylème", "conduction de la sève brute"),
        ("phloème", "conduction de la sève élaborée"),
        ("épiderme", "protection"),
        ("méristème", "croissance"),
    ]
    publie("fonction_tissu_vegetal", "physique",
           "Modèle (Claude) — botanique textbook curée (fonction des tissus végétaux ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_immunoglobuline")
def ingere_role_immunoglobuline():
    # SOURCE = LE MODÈLE (directive Yohan). Classe d'anticorps -> rôle principal. Textbook immunologie, FAUX=0 ;
    # fonctionnel (chaque classe d'Ig -> son rôle canonique).
    paires = [
        ("immunoglobuline G", "réponse immunitaire secondaire"),
        ("immunoglobuline M", "réponse immunitaire primaire"),
        ("immunoglobuline A", "protection des muqueuses"),
        ("immunoglobuline E", "allergies et infections parasitaires"),
        ("immunoglobuline D", "récepteur des lymphocytes B"),
    ]
    publie("role_immunoglobuline", "physique",
           "Modèle (Claude) — immunologie textbook curée (rôle des classes d'immunoglobulines ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("fonction_partie_neurone")
def ingere_fonction_partie_neurone():
    # SOURCE = LE MODÈLE (directive Yohan). Partie du neurone -> fonction. Textbook neurobiologie, FAUX=0 ;
    # fonctionnel (chaque composant -> son rôle canonique).
    paires = [
        ("dendrite", "réception des signaux"),
        ("axone", "transmission de l'influx nerveux"),
        ("corps cellulaire", "intégration des signaux"),
        ("gaine de myéline", "accélération de l'influx nerveux"),
    ]
    publie("fonction_partie_neurone", "physique",
           "Modèle (Claude) — neurobiologie textbook curée (fonction des parties du neurone ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("systeme_organe_humain")
def ingere_systeme_organe_humain():
    # SOURCE = LE MODÈLE (directive Yohan). Organe -> système/appareil principal auquel il appartient. Textbook
    # anatomie/physiologie, FAUX=0 ; fonctionnel (organe principal -> son système).
    paires = [
        ("cœur", "système circulatoire"), ("poumon", "système respiratoire"),
        ("estomac", "système digestif"), ("rein", "système urinaire"),
        ("cerveau", "système nerveux"), ("peau", "système tégumentaire"),
        ("testicule", "système reproducteur"), ("ovaire", "système reproducteur"),
    ]
    publie("systeme_organe_humain", "physique",
           "Modèle (Claude) — anatomie textbook curée (organe -> système ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("fonction_systeme_humain")
def ingere_fonction_systeme_humain():
    # SOURCE = LE MODÈLE (directive Yohan). Système/appareil du corps -> fonction principale. Textbook
    # physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("système circulatoire", "transport des nutriments et de l'oxygène"),
        ("système respiratoire", "échanges gazeux"),
        ("système digestif", "digestion des aliments"),
        ("système nerveux", "coordination de l'organisme"),
        ("système urinaire", "élimination des déchets"),
        ("système endocrinien", "régulation hormonale"),
        ("système immunitaire", "défense de l'organisme"),
        ("système squelettique", "soutien du corps"),
    ]
    publie("fonction_systeme_humain", "physique",
           "Modèle (Claude) — physiologie textbook curée (système -> fonction ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_macronutriment")
def ingere_role_macronutriment():
    # SOURCE = LE MODÈLE (directive Yohan). Macronutriment / constituant alimentaire -> rôle principal. Textbook
    # nutrition, FAUX=0 ; fonctionnel.
    paires = [
        ("glucides", "source d'énergie"),
        ("lipides", "réserve d'énergie"),
        ("protéines", "construction des tissus"),
        ("fibres alimentaires", "transit intestinal"),
        ("eau", "hydratation de l'organisme"),
    ]
    publie("role_macronutriment", "physique",
           "Modèle (Claude) — nutrition textbook curée (macronutriment -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("type_articulation")
def ingere_type_articulation():
    # SOURCE = LE MODÈLE (directive Yohan). Articulation -> type structural. Textbook anatomie, FAUX=0 ;
    # fonctionnel. Synoviale = mobile, cartilagineuse = semi-mobile, fibreuse = immobile.
    paires = [
        ("genou", "synoviale"), ("épaule", "synoviale"), ("hanche", "synoviale"), ("coude", "synoviale"),
        ("sutures du crâne", "fibreuse"),
        ("symphyse pubienne", "cartilagineuse"), ("disque intervertébral", "cartilagineuse"),
        # — approfondissement run-autonome (type structural certain) —
        ("cheville", "synoviale"), ("poignet", "synoviale"),
        ("articulation temporo-mandibulaire", "synoviale"), ("articulation du doigt", "synoviale"),
        ("articulation du pouce", "synoviale"),
        ("gomphose dentaire", "fibreuse"), ("syndesmose tibio-fibulaire", "fibreuse"),
    ]
    publie("type_articulation", "physique",
           "Modèle (Claude) — anatomie textbook curée (articulation -> type structural ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("agent_dispersion_graine")
def ingere_agent_dispersion_graine():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de dissémination des graines -> agent disperseur. Textbook
    # botanique/écologie, FAUX=0 ; définitionnel (chaque mode -> son agent).
    paires = [
        ("anémochorie", "vent"), ("hydrochorie", "eau"),
        ("zoochorie", "animaux"), ("barochorie", "gravité"),
        ("anthropochorie", "homme"),
        # — approfondissement run-autonome (mode de dispersion -> agent certain) —
        ("myrmécochorie", "fourmis"), ("autochorie", "plante elle-même"),
    ]
    publie("agent_dispersion_graine", "physique",
           "Modèle (Claude) — botanique textbook curée (mode de dispersion -> agent ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_phytohormone")
def ingere_role_phytohormone():
    # SOURCE = LE MODÈLE (directive Yohan). Hormone végétale -> rôle principal. Textbook physiologie végétale,
    # FAUX=0 ; fonctionnel (rôle canonique).
    paires = [
        ("auxine", "croissance par élongation cellulaire"),
        ("gibbérelline", "germination et élongation des tiges"),
        ("éthylène", "maturation des fruits"),
        ("cytokinine", "division cellulaire"),
        ("acide abscissique", "dormance et fermeture des stomates"),
        # — approfondissement run-autonome (phytohormones, rôle canonique certain) —
        ("brassinostéroïde", "croissance cellulaire"),
        ("acide salicylique", "résistance aux pathogènes"),
        ("jasmonate", "défense contre les herbivores"),
    ]
    publie("role_phytohormone", "physique",
           "Modèle (Claude) — physiologie végétale textbook curée (phytohormone -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_neurone")
def ingere_role_neurone():
    # SOURCE = LE MODÈLE (directive Yohan). Type fonctionnel de neurone -> rôle. Textbook neurobiologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("neurone sensitif", "transmettre l'information vers le système nerveux central"),
        ("neurone moteur", "commander les muscles et les glandes"),
        ("interneurone", "relier les neurones entre eux"),
    ]
    publie("role_neurone", "physique",
           "Modèle (Claude) — neurobiologie textbook curée (type de neurone -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_immunite")
def ingere_caractere_immunite():
    # SOURCE = LE MODÈLE (directive Yohan). Type d'immunité -> caractère distinctif. Textbook immunologie, FAUX=0 ;
    # fonctionnel. Innée = non spécifique et immédiate ; adaptative = spécifique avec mémoire.
    paires = [
        ("immunité innée", "non spécifique"),
        ("immunité adaptative", "spécifique"),
    ]
    publie("caractere_immunite", "physique",
           "Modèle (Claude) — immunologie textbook curée (type d'immunité -> caractère ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_symbiose")
def ingere_caractere_symbiose():
    # SOURCE = LE MODÈLE (directive Yohan). Type de relation interspécifique -> effet sur les partenaires.
    # Textbook écologie, FAUX=0 ; définitionnel.
    paires = [
        ("mutualisme", "bénéfice réciproque"),
        ("commensalisme", "bénéfice pour l'un, neutre pour l'autre"),
        ("parasitisme", "bénéfice pour l'un, préjudice pour l'autre"),
        ("compétition", "préjudice pour les deux"),
    ]
    publie("caractere_symbiose", "physique",
           "Modèle (Claude) — écologie textbook curée (relation interspécifique -> effet ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("resultat_division_cellulaire")
def ingere_resultat_division_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Type de division cellulaire -> résultat. Textbook biologie cellulaire,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("mitose", "deux cellules filles identiques"),
        ("méiose", "quatre cellules haploïdes"),
    ]
    publie("resultat_division_cellulaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (division -> résultat ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("condition_respiration_cellulaire")
def ingere_condition_respiration_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Type de respiration cellulaire -> condition en oxygène. Textbook
    # biochimie, FAUX=0 ; définitionnel.
    paires = [
        ("respiration aérobie", "présence d'oxygène"),
        ("respiration anaérobie", "absence d'oxygène"),
        ("fermentation", "absence d'oxygène"),
    ]
    publie("condition_respiration_cellulaire", "physique",
           "Modèle (Claude) — biochimie textbook curée (respiration cellulaire -> condition O2 ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("produit_fermentation")
def ingere_produit_fermentation():
    # SOURCE = LE MODÈLE (directive Yohan). Type de fermentation -> produit principal. Textbook microbiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("fermentation lactique", "acide lactique"),
        ("fermentation alcoolique", "éthanol"),
        ("fermentation acétique", "acide acétique"),
    ]
    publie("produit_fermentation", "physique",
           "Modèle (Claude) — microbiologie textbook curée (fermentation -> produit ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("duree_cycle_plante")
def ingere_duree_cycle_plante():
    # SOURCE = LE MODÈLE (directive Yohan). Type de cycle de vie d'une plante -> durée. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("plante annuelle", "un an"),
        ("plante bisannuelle", "deux ans"),
        ("plante vivace", "plusieurs années"),
    ]
    publie("duree_cycle_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (cycle de vie -> durée ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_niveau_ecologique")
def ingere_definition_niveau_ecologique():
    # SOURCE = LE MODÈLE (directive Yohan). Niveau d'organisation écologique -> définition. Textbook écologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("population", "individus d'une même espèce dans un milieu"),
        ("communauté", "ensemble des populations d'un milieu"),
        ("écosystème", "communauté et son milieu physique"),
        ("biosphère", "ensemble des écosystèmes de la Terre"),
    ]
    publie("definition_niveau_ecologique", "physique",
           "Modèle (Claude) — écologie textbook curée (niveau d'organisation -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("produit_excretion_organe")
def ingere_produit_excretion_organe():
    # SOURCE = LE MODÈLE (directive Yohan). Organe excréteur -> déchet principal éliminé. Textbook physiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("rein", "urine"), ("peau", "sueur"),
        ("poumon", "dioxyde de carbone"), ("foie", "bile"),
    ]
    publie("produit_excretion_organe", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe excréteur -> déchet ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_fleur")
def ingere_role_partie_fleur():
    # SOURCE = LE MODÈLE (directive Yohan). Pièce florale -> rôle. Textbook botanique, FAUX=0 ; fonctionnel.
    paires = [
        ("pétale", "attraction des pollinisateurs"),
        ("étamine", "organe reproducteur mâle"),
        ("pistil", "organe reproducteur femelle"),
        ("sépale", "protection du bouton floral"),
    ]
    publie("role_partie_fleur", "physique",
           "Modèle (Claude) — botanique textbook curée (pièce florale -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("developpement_mode_reproduction")
def ingere_developpement_mode_reproduction():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de reproduction -> lieu de développement de l'embryon. Textbook
    # zoologie, FAUX=0 ; définitionnel (distinct de mode_reproduction_animal qui classe les espèces).
    paires = [
        ("ovipare", "développement dans un œuf hors du corps de la mère"),
        ("vivipare", "développement dans le corps de la mère"),
        ("ovovivipare", "œufs incubés dans le corps de la mère"),
    ]
    publie("developpement_mode_reproduction", "physique",
           "Modèle (Claude) — zoologie textbook curée (mode de reproduction -> développement ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("consistance_fruit")
def ingere_consistance_fruit():
    # SOURCE = LE MODÈLE (directive Yohan). Type botanique de fruit -> consistance (charnu/sec). Textbook
    # botanique, FAUX=0 ; définitionnel (distinct de type_fruit_botanique qui classe les espèces).
    paires = [
        ("drupe", "charnu"), ("baie", "charnu"),
        ("gousse", "sec"), ("akène", "sec"), ("caryopse", "sec"), ("capsule", "sec"),
    ]
    publie("consistance_fruit", "physique",
           "Modèle (Claude) — botanique textbook curée (type de fruit -> consistance ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("agent_pollinisation")
def ingere_agent_pollinisation():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de pollinisation -> agent pollinisateur. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("entomophilie", "insectes"), ("anémophilie", "vent"),
        ("hydrophilie", "eau"), ("ornithophilie", "oiseaux"),
    ]
    publie("agent_pollinisation", "physique",
           "Modèle (Claude) — botanique textbook curée (pollinisation -> agent ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("nature_metabolisme")
def ingere_nature_metabolisme():
    # SOURCE = LE MODÈLE (directive Yohan). Voie métabolique -> nature des réactions. Textbook biochimie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("anabolisme", "réactions de synthèse"),
        ("catabolisme", "réactions de dégradation"),
    ]
    publie("nature_metabolisme", "physique",
           "Modèle (Claude) — biochimie textbook curée (métabolisme -> nature ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organe_digestif")
def ingere_role_organe_digestif():
    # SOURCE = LE MODÈLE (directive Yohan). Organe du tube digestif / glande annexe -> rôle principal. Textbook
    # physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("estomac", "digestion des protéines"),
        ("intestin grêle", "absorption des nutriments"),
        ("gros intestin", "absorption de l'eau"),
        ("foie", "production de la bile"),
        ("pancréas", "production d'enzymes digestives"),
    ]
    publie("role_organe_digestif", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe digestif -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_cerveau")
def ingere_role_partie_cerveau():
    # SOURCE = LE MODÈLE (directive Yohan). Région encéphalique -> rôle principal. Textbook neuroanatomie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("cervelet", "équilibre et coordination des mouvements"),
        ("bulbe rachidien", "contrôle des fonctions vitales"),
        ("hypothalamus", "régulation du milieu interne"),
        ("cortex cérébral", "fonctions cognitives supérieures"),
        # — approfondissement run-autonome (région encéphalique -> rôle certain) —
        ("hippocampe", "mémoire"),
        ("amygdale cérébrale", "traitement des émotions"),
        ("thalamus", "relais des informations sensorielles"),
        ("corps calleux", "connexion des deux hémisphères"),
        ("bulbe olfactif", "olfaction"),
    ]
    publie("role_partie_cerveau", "physique",
           "Modèle (Claude) — neuroanatomie textbook curée (région du cerveau -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("stimulus_recepteur")
def ingere_stimulus_recepteur():
    # SOURCE = LE MODÈLE (directive Yohan). Type de récepteur sensoriel -> stimulus détecté. Textbook physiologie
    # sensorielle, FAUX=0 ; définitionnel.
    paires = [
        ("photorécepteur", "lumière"), ("mécanorécepteur", "pression"),
        ("chimiorécepteur", "substances chimiques"), ("thermorécepteur", "température"),
        ("nocicepteur", "douleur"),
        # — approfondissement run-autonome (récepteur -> stimulus, définitionnel certain) —
        ("barorécepteur", "pression artérielle"), ("osmorécepteur", "osmolarité"),
        ("propriocepteur", "position du corps"), ("électrorécepteur", "champ électrique"),
    ]
    publie("stimulus_recepteur", "physique",
           "Modèle (Claude) — physiologie sensorielle textbook curée (récepteur -> stimulus ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("localisation_materiel_genetique")
def ingere_localisation_materiel_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Type de cellule -> localisation du matériel génétique. Textbook
    # biologie cellulaire, FAUX=0 ; définitionnel.
    paires = [
        ("cellule eucaryote", "noyau"),
        ("cellule procaryote", "cytoplasme"),
    ]
    publie("localisation_materiel_genetique", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (cellule -> localisation de l'ADN ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_oeil")
def ingere_role_partie_oeil():
    # SOURCE = LE MODÈLE (directive Yohan). Partie de l'œil -> rôle. Textbook anatomie sensorielle, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("cornée", "réfraction de la lumière"),
        ("cristallin", "mise au point de l'image"),
        ("rétine", "formation de l'image"),
        ("iris", "régulation de la quantité de lumière"),
        ("nerf optique", "transmission du signal au cerveau"),
    ]
    publie("role_partie_oeil", "physique",
           "Modèle (Claude) — anatomie sensorielle textbook curée (partie de l'œil -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_oreille")
def ingere_role_partie_oreille():
    # SOURCE = LE MODÈLE (directive Yohan). Partie de l'oreille -> rôle. Textbook anatomie sensorielle, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("tympan", "transmission des vibrations sonores"),
        ("cochlée", "transformation des vibrations en signaux nerveux"),
        ("canaux semi-circulaires", "équilibre"),
        ("pavillon", "captation des sons"),
    ]
    publie("role_partie_oreille", "physique",
           "Modèle (Claude) — anatomie sensorielle textbook curée (partie de l'oreille -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("fonction_tissu_animal")
def ingere_fonction_tissu_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Type fondamental de tissu animal -> fonction. Textbook histologie,
    # FAUX=0 ; fonctionnel (les 4 tissus fondamentaux).
    paires = [
        ("tissu épithélial", "revêtement et protection"),
        ("tissu conjonctif", "soutien et liaison"),
        ("tissu musculaire", "mouvement"),
        ("tissu nerveux", "transmission de l'information"),
    ]
    publie("fonction_tissu_animal", "physique",
           "Modèle (Claude) — histologie textbook curée (tissu animal -> fonction ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_phase_cardiaque")
def ingere_role_phase_cardiaque():
    # SOURCE = LE MODÈLE (directive Yohan). Phase du cycle cardiaque -> rôle. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("systole", "contraction et éjection du sang"),
        ("diastole", "relâchement et remplissage du cœur"),
    ]
    publie("role_phase_cardiaque", "physique",
           "Modèle (Claude) — physiologie textbook curée (phase cardiaque -> rôle ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_type_vaisseau")
def ingere_role_type_vaisseau():
    # SOURCE = LE MODÈLE (directive Yohan). Type de vaisseau sanguin -> rôle (distinct de type_vaisseau_sanguin
    # qui classe les vaisseaux nommés). Textbook physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("artère", "transport du sang du cœur vers les organes"),
        ("veine", "retour du sang vers le cœur"),
        ("capillaire", "échanges entre le sang et les tissus"),
    ]
    publie("role_type_vaisseau", "physique",
           "Modèle (Claude) — physiologie textbook curée (type de vaisseau -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_leucocyte")
def ingere_role_leucocyte():
    # SOURCE = LE MODÈLE (directive Yohan). Type de globule blanc -> rôle (distinct de type_leucocyte qui donne
    # granulocyte/agranulocyte). Textbook immunologie, FAUX=0 ; fonctionnel.
    paires = [
        ("lymphocyte", "réponse immunitaire spécifique"),
        ("neutrophile", "phagocytose des bactéries"),
        ("monocyte", "phagocytose des débris"),
        ("éosinophile", "lutte contre les parasites"),
        ("basophile", "réaction allergique"),
    ]
    publie("role_leucocyte", "physique",
           "Modèle (Claude) — immunologie textbook curée (globule blanc -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_element_squelette")
def ingere_role_element_squelette():
    # SOURCE = LE MODÈLE (directive Yohan). Ensemble osseux -> rôle de protection/soutien. Textbook anatomie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("crâne", "protection du cerveau"),
        ("cage thoracique", "protection du cœur et des poumons"),
        ("colonne vertébrale", "protection de la moelle épinière"),
    ]
    publie("role_element_squelette", "physique",
           "Modèle (Claude) — anatomie textbook curée (ensemble osseux -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("destination_secretion_glande")
def ingere_destination_secretion_glande():
    # SOURCE = LE MODÈLE (directive Yohan). Type de glande -> destination de la sécrétion. Textbook physiologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("glande endocrine", "sang"),
        ("glande exocrine", "canal excréteur vers une surface"),
    ]
    publie("destination_secretion_glande", "physique",
           "Modèle (Claude) — physiologie textbook curée (type de glande -> destination de sécrétion ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("rang_taxon_superieur")
def ingere_rang_taxon_superieur():
    # SOURCE = LE MODÈLE (directive Yohan). Rang taxinomique -> rang immédiatement supérieur. Textbook
    # systématique, FAUX=0 ; définitionnel (hiérarchie linnéenne classique).
    paires = [
        ("espèce", "genre"), ("genre", "famille"), ("famille", "ordre"),
        ("ordre", "classe"), ("classe", "embranchement"), ("embranchement", "règne"),
    ]
    publie("rang_taxon_superieur", "physique",
           "Modèle (Claude) — systématique textbook curée (rang -> rang supérieur ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_acide_nucleique")
def ingere_role_acide_nucleique():
    # SOURCE = LE MODÈLE (directive Yohan). Acide nucléique -> rôle (distinct de fonction_arn, par type d'ARN).
    # Textbook biologie moléculaire, FAUX=0 ; définitionnel.
    paires = [
        ("ADN", "conservation de l'information génétique"),
        ("ARN", "expression de l'information génétique"),
    ]
    publie("role_acide_nucleique", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (acide nucléique -> rôle ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("constituant_paroi_cellulaire")
def ingere_constituant_paroi_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Type de cellule -> constituant principal de sa paroi. Textbook
    # biologie cellulaire, FAUX=0 ; définitionnel.
    paires = [
        ("cellule végétale", "cellulose"),
        ("cellule bactérienne", "peptidoglycane"),
        ("cellule fongique", "chitine"),
    ]
    publie("constituant_paroi_cellulaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (cellule -> constituant de la paroi ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("sexe_caryotype_humain")
def ingere_sexe_caryotype_humain():
    # SOURCE = LE MODÈLE (directive Yohan). Caryotype des chromosomes sexuels -> sexe (humain). Textbook
    # génétique, FAUX=0 ; définitionnel.
    paires = [
        ("XX", "féminin"),
        ("XY", "masculin"),
    ]
    publie("sexe_caryotype_humain", "physique",
           "Modèle (Claude) — génétique humaine textbook curée (caryotype sexuel -> sexe ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_pigment_biologique")
def ingere_role_pigment_biologique():
    # SOURCE = LE MODÈLE (directive Yohan). Pigment biologique -> rôle. Textbook biologie, FAUX=0 ; fonctionnel.
    paires = [
        ("chlorophylle", "absorption de la lumière pour la photosynthèse"),
        ("mélanine", "protection contre les rayons ultraviolets"),
        ("hémoglobine", "transport de l'oxygène"),
    ]
    publie("role_pigment_biologique", "physique",
           "Modèle (Claude) — biologie textbook curée (pigment -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("organite_processus")
def ingere_organite_processus():
    # SOURCE = LE MODÈLE (directive Yohan). Processus cellulaire -> organite où il a lieu (inverse de
    # fonction_organite). Textbook biologie cellulaire, FAUX=0 ; fonctionnel.
    paires = [
        ("photosynthèse", "chloroplaste"),
        ("respiration cellulaire", "mitochondrie"),
        ("synthèse des protéines", "ribosome"),
        ("digestion cellulaire", "lysosome"),
    ]
    publie("organite_processus", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (processus -> organite ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_reproduction")
def ingere_caractere_reproduction():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de reproduction -> caractère génétique. Textbook biologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("reproduction sexuée", "deux parents et brassage génétique"),
        ("reproduction asexuée", "un seul parent et descendants identiques"),
    ]
    publie("caractere_reproduction", "physique",
           "Modèle (Claude) — biologie textbook curée (mode de reproduction -> caractère ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_structure_locomotion_cellulaire")
def ingere_role_structure_locomotion_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Structure de locomotion cellulaire -> rôle. Textbook biologie
    # cellulaire, FAUX=0 ; fonctionnel.
    paires = [
        ("flagelle", "propulsion de la cellule"),
        ("cil", "déplacement et brassage des liquides"),
        ("pseudopode", "déplacement par reptation"),
    ]
    publie("role_structure_locomotion_cellulaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (structure de locomotion -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("effet_classe_medicament")
def ingere_effet_classe_medicament():
    # SOURCE = LE MODÈLE (directive Yohan). Classe pharmacologique -> effet recherché (distinct de
    # classe_therapeutique_medicament qui classe les médicaments). Textbook pharmacologie, FAUX=0 ; fonctionnel.
    paires = [
        ("antalgique", "soulagement de la douleur"),
        ("antipyrétique", "baisse de la fièvre"),
        ("anti-inflammatoire", "réduction de l'inflammation"),
        ("antibiotique", "destruction des bactéries"),
        ("antiviral", "inhibition des virus"),
        ("anticoagulant", "fluidification du sang"),
        ("diurétique", "augmentation de l'élimination urinaire"),
    ]
    publie("effet_classe_medicament", "physique",
           "Modèle (Claude) — pharmacologie textbook curée (classe -> effet ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("mode_acquisition_immunite")
def ingere_mode_acquisition_immunite():
    # SOURCE = LE MODÈLE (directive Yohan). Type d'immunité acquise -> mode (distinct de caractere_immunite
    # innée/adaptative). Textbook immunologie, FAUX=0 ; définitionnel.
    paires = [
        ("immunité active", "production d'anticorps par l'organisme"),
        ("immunité passive", "réception d'anticorps produits par un autre organisme"),
    ]
    publie("mode_acquisition_immunite", "physique",
           "Modèle (Claude) — immunologie textbook curée (immunité acquise -> mode ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("composition_vaccin")
def ingere_composition_vaccin():
    # SOURCE = LE MODÈLE (directive Yohan). Type de vaccin -> nature de l'antigène. Textbook immunologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("vaccin vivant atténué", "agent infectieux vivant affaibli"),
        ("vaccin inactivé", "agent infectieux tué"),
        ("vaccin sous-unitaire", "fragment de l'agent infectieux"),
        ("vaccin à ARN messager", "ARN codant un antigène"),
    ]
    publie("composition_vaccin", "physique",
           "Modèle (Claude) — immunologie textbook curée (type de vaccin -> antigène ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("milieu_respiration")
def ingere_milieu_respiration():
    # SOURCE = LE MODÈLE (directive Yohan). Organe respiratoire -> milieu de respiration (distinct de
    # respiration_animal qui donne l'organe par espèce). Textbook zoologie, FAUX=0 ; définitionnel.
    paires = [
        ("branchies", "milieu aquatique"),
        ("poumons", "milieu aérien"),
        ("trachées", "milieu aérien"),
    ]
    publie("milieu_respiration", "physique",
           "Modèle (Claude) — zoologie textbook curée (organe respiratoire -> milieu ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("nombre_carbone_ose")
def ingere_nombre_carbone_ose():
    # SOURCE = LE MODÈLE (directive Yohan). Catégorie d'ose -> nombre d'atomes de carbone. Textbook biochimie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("triose", "3"), ("tétrose", "4"), ("pentose", "5"), ("hexose", "6"), ("heptose", "7"),
    ]
    publie("nombre_carbone_ose", "physique",
           "Modèle (Claude) — biochimie textbook curée (ose -> nombre de carbones ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("liaison_polymere")
def ingere_liaison_polymere():
    # SOURCE = LE MODÈLE (directive Yohan). Macromolécule biologique -> liaison chimique entre ses unités.
    # Textbook biochimie, FAUX=0 ; définitionnel.
    paires = [
        ("protéine", "liaison peptidique"),
        ("polysaccharide", "liaison glycosidique"),
        ("acide nucléique", "liaison phosphodiester"),
        ("triglycéride", "liaison ester"),
    ]
    publie("liaison_polymere", "physique",
           "Modèle (Claude) — biochimie textbook curée (macromolécule -> liaison ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_structure_proteine")
def ingere_definition_structure_proteine():
    # SOURCE = LE MODÈLE (directive Yohan). Niveau de structure d'une protéine -> définition. Textbook
    # biochimie, FAUX=0 ; définitionnel.
    paires = [
        ("structure primaire", "séquence des acides aminés"),
        ("structure secondaire", "hélices alpha et feuillets bêta"),
        ("structure tertiaire", "repliement tridimensionnel de la chaîne"),
        ("structure quaternaire", "assemblage de plusieurs chaînes"),
    ]
    publie("definition_structure_proteine", "physique",
           "Modèle (Claude) — biochimie textbook curée (structure protéique -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("elements_biomolecule")
def ingere_elements_biomolecule():
    # SOURCE = LE MODÈLE (directive Yohan). Classe de biomolécule -> éléments chimiques constitutifs principaux.
    # Textbook biochimie, FAUX=0 ; définitionnel.
    paires = [
        ("glucide", "carbone, hydrogène, oxygène"),
        ("lipide", "carbone, hydrogène, oxygène"),
        ("protéine", "carbone, hydrogène, oxygène, azote"),
        ("acide nucléique", "carbone, hydrogène, oxygène, azote, phosphore"),
    ]
    publie("elements_biomolecule", "physique",
           "Modèle (Claude) — biochimie textbook curée (biomolécule -> éléments ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_genetique")
def ingere_definition_terme_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de génétique -> définition. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("génotype", "ensemble des allèles d'un individu"),
        ("phénotype", "ensemble des caractères observables"),
        ("allèle", "version d'un gène"),
        ("gène", "segment d'ADN portant une information héréditaire"),
        ("mutation", "modification de la séquence d'ADN"),
    ]
    publie("definition_terme_genetique", "physique",
           "Modèle (Claude) — génétique textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("expression_allele")
def ingere_expression_allele():
    # SOURCE = LE MODÈLE (directive Yohan). Type d'allèle -> condition d'expression. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("allèle dominant", "s'exprime même à l'état hétérozygote"),
        ("allèle récessif", "s'exprime seulement à l'état homozygote"),
    ]
    publie("expression_allele", "physique",
           "Modèle (Claude) — génétique textbook curée (allèle -> expression ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("ploidie_cellule")
def ingere_ploidie_cellule():
    # SOURCE = LE MODÈLE (directive Yohan). Type de cellule -> ploïdie. Textbook génétique, FAUX=0 ; définitionnel.
    paires = [
        ("gamète", "haploïde"),
        ("cellule somatique", "diploïde"),
        ("zygote", "diploïde"),
    ]
    publie("ploidie_cellule", "physique",
           "Modèle (Claude) — génétique textbook curée (cellule -> ploïdie ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("evenement_phase_mitose")
def ingere_evenement_phase_mitose():
    # SOURCE = LE MODÈLE (directive Yohan). Phase de la mitose -> événement caractéristique. Textbook biologie
    # cellulaire, FAUX=0 ; définitionnel.
    paires = [
        ("prophase", "condensation des chromosomes"),
        ("métaphase", "alignement des chromosomes sur la plaque équatoriale"),
        ("anaphase", "séparation des chromatides sœurs"),
        ("télophase", "formation de deux noyaux"),
    ]
    publie("evenement_phase_mitose", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (phase de mitose -> événement ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("bilan_photosynthese")
def ingere_bilan_photosynthese():
    # SOURCE = LE MODÈLE (directive Yohan). Côté de l'équation de la photosynthèse -> substances. Textbook
    # biologie végétale, FAUX=0 ; définitionnel.
    paires = [
        ("réactifs de la photosynthèse", "dioxyde de carbone et eau"),
        ("produits de la photosynthèse", "glucose et dioxygène"),
    ]
    publie("bilan_photosynthese", "physique",
           "Modèle (Claude) — biologie végétale textbook curée (photosynthèse -> bilan ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("gaz_respiration")
def ingere_gaz_respiration():
    # SOURCE = LE MODÈLE (directive Yohan). Phase de la respiration -> gaz échangé. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("inspiration", "apport de dioxygène"),
        ("expiration", "rejet de dioxyde de carbone"),
    ]
    publie("gaz_respiration", "physique",
           "Modèle (Claude) — physiologie textbook curée (respiration -> gaz ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_ecologie")
def ingere_definition_terme_ecologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'écologie -> définition. Textbook écologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("habitat", "lieu de vie d'une espèce"),
        ("niche écologique", "rôle et place d'une espèce dans son écosystème"),
        ("biotope", "milieu physique d'un écosystème"),
        ("biocénose", "ensemble des êtres vivants d'un écosystème"),
    ]
    publie("definition_terme_ecologie", "physique",
           "Modèle (Claude) — écologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_niveau_prevention")
def ingere_definition_niveau_prevention():
    # SOURCE = LE MODÈLE (directive Yohan). Niveau de prévention en santé -> définition. Textbook santé publique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("prévention primaire", "éviter l'apparition de la maladie"),
        ("prévention secondaire", "dépister et traiter précocement la maladie"),
        ("prévention tertiaire", "limiter les complications de la maladie"),
    ]
    publie("definition_niveau_prevention", "physique",
           "Modèle (Claude) — santé publique textbook curée (niveau de prévention -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_constituant_os")
def ingere_role_constituant_os():
    # SOURCE = LE MODÈLE (directive Yohan). Constituant d'un os -> rôle. Textbook anatomie, FAUX=0 ; fonctionnel.
    paires = [
        ("os compact", "résistance mécanique"),
        ("os spongieux", "légèreté et amortissement"),
        ("moelle osseuse rouge", "production des cellules sanguines"),
        ("périoste", "croissance en épaisseur et nutrition de l'os"),
    ]
    publie("role_constituant_os", "physique",
           "Modèle (Claude) — anatomie textbook curée (constituant osseux -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_dent")
def ingere_role_partie_dent():
    # SOURCE = LE MODÈLE (directive Yohan). Partie d'une dent -> rôle. Textbook anatomie, FAUX=0 ; fonctionnel.
    paires = [
        ("émail", "protection de la dent"),
        ("dentine", "soutien de l'émail"),
        ("pulpe dentaire", "vascularisation et innervation"),
        ("racine de la dent", "ancrage dans la mâchoire"),
    ]
    publie("role_partie_dent", "physique",
           "Modèle (Claude) — anatomie textbook curée (partie de dent -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_couche_peau")
def ingere_role_couche_peau():
    # SOURCE = LE MODÈLE (directive Yohan). Couche de la peau -> rôle. Textbook anatomie, FAUX=0 ; fonctionnel.
    paires = [
        ("épiderme", "protection"),
        ("derme", "soutien et sensibilité"),
        ("hypoderme", "réserve de graisse et isolation thermique"),
    ]
    publie("role_couche_peau", "physique",
           "Modèle (Claude) — anatomie textbook curée (couche de peau -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_graine")
def ingere_role_partie_graine():
    # SOURCE = LE MODÈLE (directive Yohan). Partie d'une graine -> rôle. Textbook botanique, FAUX=0 ; fonctionnel.
    paires = [
        ("tégument", "protection de la graine"),
        ("cotylédon", "réserve nutritive"),
        ("embryon", "origine de la nouvelle plante"),
    ]
    publie("role_partie_graine", "physique",
           "Modèle (Claude) — botanique textbook curée (partie de graine -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_mecanisme_evolution")
def ingere_definition_mecanisme_evolution():
    # SOURCE = LE MODÈLE (directive Yohan). Mécanisme de l'évolution -> définition. Textbook biologie évolutive,
    # FAUX=0 ; définitionnel.
    paires = [
        ("sélection naturelle", "tri des individus les mieux adaptés à leur milieu"),
        ("mutation", "source de variation génétique"),
        ("dérive génétique", "variation aléatoire des fréquences alléliques"),
        ("migration", "échange de gènes entre populations"),
    ]
    publie("definition_mecanisme_evolution", "physique",
           "Modèle (Claude) — biologie évolutive textbook curée (mécanisme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_virus")
def ingere_role_partie_virus():
    # SOURCE = LE MODÈLE (directive Yohan). Constituant d'un virus -> rôle. Textbook virologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("capside", "protection du matériel génétique"),
        ("enveloppe virale", "reconnaissance et entrée dans la cellule hôte"),
        ("génome viral", "information génétique du virus"),
    ]
    publie("role_partie_virus", "physique",
           "Modèle (Claude) — virologie textbook curée (constituant viral -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_immunologie")
def ingere_definition_terme_immunologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'immunologie -> définition. Textbook immunologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("antigène", "substance étrangère reconnue par le système immunitaire"),
        ("anticorps", "protéine qui neutralise un antigène"),
        ("agent pathogène", "agent responsable d'une maladie"),
    ]
    publie("definition_terme_immunologie", "physique",
           "Modèle (Claude) — immunologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_cycle_viral")
def ingere_caractere_cycle_viral():
    # SOURCE = LE MODÈLE (directive Yohan). Type de cycle viral -> caractère. Textbook virologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("cycle lytique", "destruction de la cellule hôte"),
        ("cycle lysogénique", "intégration du génome viral dans la cellule hôte"),
    ]
    publie("caractere_cycle_viral", "physique",
           "Modèle (Claude) — virologie textbook curée (cycle viral -> caractère ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_rein")
def ingere_role_partie_rein():
    # SOURCE = LE MODÈLE (directive Yohan). Structure du rein -> rôle. Textbook physiologie rénale, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("glomérule", "filtration du sang"),
        ("tubule rénal", "réabsorption de l'eau et des nutriments"),
        ("néphron", "unité fonctionnelle de filtration"),
    ]
    publie("role_partie_rein", "physique",
           "Modèle (Claude) — physiologie rénale textbook curée (structure du rein -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_poumon")
def ingere_role_partie_poumon():
    # SOURCE = LE MODÈLE (directive Yohan). Structure pulmonaire -> rôle. Textbook physiologie respiratoire,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("alvéole pulmonaire", "échanges gazeux"),
        ("bronche", "conduction de l'air"),
        ("plèvre", "protection et lubrification du poumon"),
    ]
    publie("role_partie_poumon", "physique",
           "Modèle (Claude) — physiologie respiratoire textbook curée (structure pulmonaire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_coeur")
def ingere_role_partie_coeur():
    # SOURCE = LE MODÈLE (directive Yohan). Structure du cœur -> rôle. Textbook physiologie cardiaque, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("oreillette", "réception du sang"),
        ("ventricule", "éjection du sang"),
        ("valve cardiaque", "empêcher le reflux du sang"),
    ]
    publie("role_partie_coeur", "physique",
           "Modèle (Claude) — physiologie cardiaque textbook curée (structure du cœur -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_cellulaire")
def ingere_definition_terme_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de biologie cellulaire -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("cellule", "unité de base des êtres vivants"),
        ("organite", "structure spécialisée de la cellule"),
        ("cytoplasme", "milieu interne de la cellule"),
        ("membrane plasmique", "limite contrôlant les échanges de la cellule"),
    ]
    publie("definition_terme_cellulaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_classe_lipide")
def ingere_role_classe_lipide():
    # SOURCE = LE MODÈLE (directive Yohan). Classe de lipide -> rôle principal. Textbook biochimie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("triglycéride", "réserve d'énergie"),
        ("phospholipide", "constituant des membranes cellulaires"),
        ("cire", "protection imperméable"),
    ]
    publie("role_classe_lipide", "physique",
           "Modèle (Claude) — biochimie textbook curée (classe de lipide -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_botanique")
def ingere_definition_terme_botanique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de botanique -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("photosynthèse", "production de matière organique à partir de la lumière"),
        ("transpiration", "perte d'eau par les feuilles"),
        ("germination", "développement de l'embryon de la graine"),
    ]
    publie("definition_terme_botanique", "physique",
           "Modèle (Claude) — botanique textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_etape_digestion")
def ingere_definition_etape_digestion():
    # SOURCE = LE MODÈLE (directive Yohan). Étape de la digestion -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("digestion", "transformation des aliments en nutriments"),
        ("absorption", "passage des nutriments dans le sang"),
        ("défécation", "élimination des déchets non digérés"),
    ]
    publie("definition_etape_digestion", "physique",
           "Modèle (Claude) — physiologie textbook curée (étape de digestion -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_physiologie")
def ingere_definition_terme_physiologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de physiologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("homéostasie", "maintien de l'équilibre du milieu interne"),
        ("métabolisme", "ensemble des réactions chimiques de l'organisme"),
        ("excrétion", "élimination des déchets de l'organisme"),
    ]
    publie("definition_terme_physiologie", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_evolution")
def ingere_definition_terme_evolution():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de biologie évolutive -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("espèce", "groupe d'individus interféconds"),
        ("spéciation", "formation de nouvelles espèces"),
        ("adaptation", "caractère favorable à la survie dans un milieu"),
        ("fossile", "reste ou trace d'un organisme ancien"),
    ]
    publie("definition_terme_evolution", "physique",
           "Modèle (Claude) — biologie évolutive textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("agent_selection")
def ingere_agent_selection():
    # SOURCE = LE MODÈLE (directive Yohan). Type de sélection -> agent sélecteur. Textbook biologie évolutive,
    # FAUX=0 ; définitionnel.
    paires = [
        ("sélection naturelle", "milieu naturel"),
        ("sélection artificielle", "être humain"),
        ("sélection sexuelle", "choix du partenaire"),
    ]
    publie("agent_selection", "physique",
           "Modèle (Claude) — biologie évolutive textbook curée (sélection -> agent ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_croisement")
def ingere_definition_croisement():
    # SOURCE = LE MODÈLE (directive Yohan). Type de croisement génétique -> définition. Textbook génétique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("croisement monohybride", "portant sur un seul caractère"),
        ("croisement dihybride", "portant sur deux caractères"),
    ]
    publie("definition_croisement", "physique",
           "Modèle (Claude) — génétique textbook curée (croisement -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_micro_organisme")
def ingere_definition_micro_organisme():
    # SOURCE = LE MODÈLE (directive Yohan). Micro-organisme -> définition. Textbook microbiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("bactérie", "micro-organisme unicellulaire procaryote"),
        ("virus", "agent infectieux acellulaire"),
        ("levure", "champignon unicellulaire"),
    ]
    publie("definition_micro_organisme", "physique",
           "Modèle (Claude) — microbiologie textbook curée (micro-organisme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("stimulus_tropisme")
def ingere_stimulus_tropisme():
    # SOURCE = LE MODÈLE (directive Yohan). Tropisme végétal -> stimulus. Textbook physiologie végétale, FAUX=0 ;
    # définitionnel.
    paires = [
        ("phototropisme", "lumière"), ("géotropisme", "gravité"),
        ("hydrotropisme", "eau"), ("thigmotropisme", "contact"),
    ]
    publie("stimulus_tropisme", "physique",
           "Modèle (Claude) — physiologie végétale textbook curée (tropisme -> stimulus ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("stimulus_taxie")
def ingere_stimulus_taxie():
    # SOURCE = LE MODÈLE (directive Yohan). Taxie (déplacement orienté) -> stimulus. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("phototaxie", "lumière"), ("chimiotaxie", "substances chimiques"),
        ("thermotaxie", "température"),
    ]
    publie("stimulus_taxie", "physique",
           "Modèle (Claude) — biologie textbook curée (taxie -> stimulus ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_division_systeme_nerveux")
def ingere_role_division_systeme_nerveux():
    # SOURCE = LE MODÈLE (directive Yohan). Division du système nerveux -> rôle. Textbook neurophysiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("système nerveux central", "traitement de l'information"),
        ("système nerveux périphérique", "transmission entre les centres nerveux et les organes"),
    ]
    publie("role_division_systeme_nerveux", "physique",
           "Modèle (Claude) — neurophysiologie textbook curée (division du SN -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_sante")
def ingere_definition_terme_sante():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de santé/médecine -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("symptôme", "manifestation d'une maladie"),
        ("diagnostic", "identification d'une maladie"),
        ("épidémie", "propagation rapide d'une maladie dans une population"),
    ]
    publie("definition_terme_sante", "physique",
           "Modèle (Claude) — médecine textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_niveau_organisation_corps")
def ingere_definition_niveau_organisation_corps():
    # SOURCE = LE MODÈLE (directive Yohan). Niveau d'organisation du corps -> définition. Textbook biologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("tissu", "ensemble de cellules semblables"),
        ("organe", "ensemble de tissus assurant une fonction"),
        ("système", "ensemble d'organes coopérant à une grande fonction"),
        ("organisme", "ensemble des systèmes d'un être vivant"),
    ]
    publie("definition_niveau_organisation_corps", "physique",
           "Modèle (Claude) — biologie textbook curée (niveau d'organisation -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organe_reproducteur")
def ingere_role_organe_reproducteur():
    # SOURCE = LE MODÈLE (directive Yohan). Organe reproducteur -> rôle. Textbook physiologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("ovaire", "production des ovules"),
        ("testicule", "production des spermatozoïdes"),
        ("utérus", "développement de l'embryon"),
    ]
    publie("role_organe_reproducteur", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe reproducteur -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_cellule_reproductrice")
def ingere_definition_cellule_reproductrice():
    # SOURCE = LE MODÈLE (directive Yohan). Cellule de la reproduction -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("ovule", "gamète femelle"),
        ("spermatozoïde", "gamète mâle"),
        ("zygote", "cellule issue de la fécondation"),
    ]
    publie("definition_cellule_reproductrice", "physique",
           "Modèle (Claude) — biologie textbook curée (cellule reproductrice -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_reproduction")
def ingere_definition_terme_reproduction():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de la reproduction -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("fécondation", "union des gamètes mâle et femelle"),
        ("gestation", "développement de l'embryon dans l'utérus"),
        ("puberté", "acquisition de la capacité de se reproduire"),
    ]
    publie("definition_terme_reproduction", "physique",
           "Modèle (Claude) — biologie textbook curée (terme de reproduction -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_hormone_sexuelle")
def ingere_role_hormone_sexuelle():
    # SOURCE = LE MODÈLE (directive Yohan). Hormone sexuelle -> rôle principal. Textbook endocrinologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("testostérone", "développement des caractères sexuels masculins"),
        ("œstrogène", "développement des caractères sexuels féminins"),
        ("progestérone", "maintien de la grossesse"),
    ]
    publie("role_hormone_sexuelle", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (hormone sexuelle -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_caractere_sexuel")
def ingere_definition_caractere_sexuel():
    # SOURCE = LE MODÈLE (directive Yohan). Type de caractère sexuel -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("caractère sexuel primaire", "organes reproducteurs présents dès la naissance"),
        ("caractère sexuel secondaire", "caractère apparaissant à la puberté"),
    ]
    publie("definition_caractere_sexuel", "physique",
           "Modèle (Claude) — biologie textbook curée (caractère sexuel -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_annexe_embryonnaire")
def ingere_role_annexe_embryonnaire():
    # SOURCE = LE MODÈLE (directive Yohan). Annexe embryonnaire -> rôle. Textbook embryologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("placenta", "échanges entre la mère et le fœtus"),
        ("cordon ombilical", "liaison entre le fœtus et le placenta"),
        ("liquide amniotique", "protection du fœtus"),
    ]
    publie("role_annexe_embryonnaire", "physique",
           "Modèle (Claude) — embryologie textbook curée (annexe embryonnaire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_developpement")
def ingere_definition_terme_developpement():
    # SOURCE = LE MODÈLE (directive Yohan). Stade de développement -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("embryon", "stade précoce du développement"),
        ("fœtus", "stade avancé du développement avant la naissance"),
        ("larve", "stade juvénile chez certains animaux"),
    ]
    publie("definition_terme_developpement", "physique",
           "Modèle (Claude) — biologie textbook curée (stade de développement -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("cause_type_diabete")
def ingere_cause_type_diabete():
    # SOURCE = LE MODÈLE (directive Yohan). Type de diabète -> cause. Textbook médecine, FAUX=0 ; définitionnel.
    paires = [
        ("diabète de type 1", "déficit de production d'insuline"),
        ("diabète de type 2", "résistance des cellules à l'insuline"),
        ("diabète gestationnel", "apparition pendant la grossesse"),
    ]
    publie("cause_type_diabete", "physique",
           "Modèle (Claude) — médecine textbook curée (type de diabète -> cause ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_pharmacologie")
def ingere_definition_terme_pharmacologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de pharmacologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("principe actif", "substance responsable de l'effet thérapeutique"),
        ("excipient", "substance sans effet thérapeutique"),
        ("posologie", "dose et fréquence de prise d'un médicament"),
        ("effet secondaire", "effet non recherché d'un médicament"),
    ]
    publie("definition_terme_pharmacologie", "physique",
           "Modèle (Claude) — pharmacologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_voie_administration")
def ingere_definition_voie_administration():
    # SOURCE = LE MODÈLE (directive Yohan). Voie d'administration d'un médicament -> définition. Textbook
    # pharmacologie, FAUX=0 ; définitionnel.
    paires = [
        ("voie orale", "par la bouche"),
        ("voie intraveineuse", "dans une veine"),
        ("voie cutanée", "sur la peau"),
        ("voie inhalée", "par les poumons"),
    ]
    publie("definition_voie_administration", "physique",
           "Modèle (Claude) — pharmacologie textbook curée (voie d'administration -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_gaz_respiratoire")
def ingere_role_gaz_respiratoire():
    # SOURCE = LE MODÈLE (directive Yohan). Gaz respiratoire -> rôle dans l'organisme. Textbook physiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("dioxygène", "utilisé par les cellules pour produire de l'énergie"),
        ("dioxyde de carbone", "déchet de la respiration cellulaire"),
    ]
    publie("role_gaz_respiratoire", "physique",
           "Modèle (Claude) — physiologie textbook curée (gaz respiratoire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_nutrition")
def ingere_definition_terme_nutrition():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de nutrition -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("nutriment", "substance assimilable issue des aliments"),
        ("calorie", "unité de mesure de l'énergie"),
        ("ration alimentaire", "quantité d'aliments consommée par jour"),
    ]
    publie("definition_terme_nutrition", "physique",
           "Modèle (Claude) — nutrition textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_comportement")
def ingere_definition_terme_comportement():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'éthologie -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("instinct", "comportement inné"),
        ("apprentissage", "comportement acquis par l'expérience"),
        ("réflexe", "réponse automatique à un stimulus"),
    ]
    publie("definition_terme_comportement", "physique",
           "Modèle (Claude) — éthologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_type_maladie")
def ingere_definition_type_maladie():
    # SOURCE = LE MODÈLE (directive Yohan). Type de maladie -> définition par sa cause. Textbook médecine,
    # FAUX=0 ; définitionnel.
    paires = [
        ("maladie infectieuse", "causée par un agent pathogène"),
        ("maladie génétique", "due à une anomalie des gènes"),
        ("maladie carentielle", "due à un manque de nutriment"),
        ("maladie auto-immune", "le système immunitaire attaque l'organisme"),
    ]
    publie("definition_type_maladie", "physique",
           "Modèle (Claude) — médecine textbook curée (type de maladie -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_relation_alimentaire")
def ingere_definition_terme_relation_alimentaire():
    # SOURCE = LE MODÈLE (directive Yohan). Terme des relations alimentaires -> définition. Textbook écologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("proie", "organisme mangé par un autre"),
        ("prédateur", "organisme qui chasse et mange d'autres organismes"),
        ("chaîne alimentaire", "suite d'êtres vivants liés par l'alimentation"),
    ]
    publie("definition_terme_relation_alimentaire", "physique",
           "Modèle (Claude) — écologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_biochimie")
def ingere_definition_terme_biochimie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de biochimie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("enzyme", "protéine qui catalyse une réaction chimique"),
        ("substrat", "molécule transformée par une enzyme"),
        ("catalyseur", "substance qui accélère une réaction"),
    ]
    publie("definition_terme_biochimie", "physique",
           "Modèle (Claude) — biochimie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_groupe_animal")
def ingere_definition_groupe_animal():
    # SOURCE = LE MODÈLE (directive Yohan). Grand groupe animal -> définition (distinct de classe/phylum par
    # espèce). Textbook zoologie, FAUX=0 ; définitionnel.
    paires = [
        ("vertébré", "animal pourvu d'une colonne vertébrale"),
        ("invertébré", "animal dépourvu de colonne vertébrale"),
        ("mammifère", "vertébré qui allaite ses petits"),
        ("oiseau", "vertébré couvert de plumes"),
    ]
    publie("definition_groupe_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (groupe animal -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_groupe_vegetal")
def ingere_definition_groupe_vegetal():
    # SOURCE = LE MODÈLE (directive Yohan). Grand groupe végétal -> définition (distinct de groupe_plante par
    # espèce). Textbook botanique, FAUX=0 ; définitionnel.
    paires = [
        ("angiosperme", "plante à fleurs et à fruits"),
        ("gymnosperme", "plante à graines nues"),
        ("fougère", "plante à spores sans graines"),
        ("mousse", "plante sans vaisseaux conducteurs"),
    ]
    publie("definition_groupe_vegetal", "physique",
           "Modèle (Claude) — botanique textbook curée (groupe végétal -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_reponse_immunitaire")
def ingere_caractere_reponse_immunitaire():
    # SOURCE = LE MODÈLE (directive Yohan). Type de réponse immunitaire -> médiateur. Textbook immunologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("réponse humorale", "médiée par les anticorps"),
        ("réponse cellulaire", "médiée par les lymphocytes T"),
    ]
    publie("caractere_reponse_immunitaire", "physique",
           "Modèle (Claude) — immunologie textbook curée (réponse immunitaire -> médiateur ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_etape_expression_genetique")
def ingere_definition_etape_expression_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Étape de l'expression génétique -> définition. Textbook biologie
    # moléculaire, FAUX=0 ; définitionnel.
    paires = [
        ("transcription", "synthèse d'ARN à partir de l'ADN"),
        ("traduction", "synthèse d'une protéine à partir de l'ARN messager"),
        ("réplication", "copie de l'ADN"),
    ]
    publie("definition_etape_expression_genetique", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (étape -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("lieu_etape_expression_genetique")
def ingere_lieu_etape_expression_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Étape de l'expression génétique -> lieu cellulaire (eucaryote).
    # Textbook biologie cellulaire, FAUX=0 ; définitionnel.
    paires = [
        ("transcription", "noyau"),
        ("traduction", "ribosome"),
        ("réplication", "noyau"),
    ]
    publie("lieu_etape_expression_genetique", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (étape -> lieu ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_cytogenetique")
def ingere_definition_terme_cytogenetique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de cytogénétique -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("chromosome", "molécule d'ADN condensée"),
        ("chromatide", "moitié d'un chromosome dupliqué"),
        ("caryotype", "ensemble des chromosomes d'une cellule"),
    ]
    publie("definition_terme_cytogenetique", "physique",
           "Modèle (Claude) — cytogénétique textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_physiologie_vegetale")
def ingere_definition_terme_physiologie_vegetale():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de physiologie végétale -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("sève brute", "eau et sels minéraux"),
        ("sève élaborée", "eau et matières organiques"),
        ("stomate", "pore d'échange gazeux des feuilles"),
    ]
    publie("definition_terme_physiologie_vegetale", "physique",
           "Modèle (Claude) — physiologie végétale textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("caractere_fruit_sec")
def ingere_caractere_fruit_sec():
    # SOURCE = LE MODÈLE (directive Yohan). Type de fruit sec -> caractère d'ouverture. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("fruit sec déhiscent", "s'ouvre à maturité"),
        ("fruit sec indéhiscent", "reste fermé à maturité"),
    ]
    publie("caractere_fruit_sec", "physique",
           "Modèle (Claude) — botanique textbook curée (fruit sec -> caractère ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_categorie_organe_plante")
def ingere_role_categorie_organe_plante():
    # SOURCE = LE MODÈLE (directive Yohan). Catégorie d'organe végétal -> rôle. Textbook botanique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("organe végétatif", "nutrition et croissance"),
        ("organe reproducteur", "reproduction"),
    ]
    publie("role_categorie_organe_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (catégorie d'organe -> rôle ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_sang")
def ingere_definition_terme_sang():
    # SOURCE = LE MODÈLE (directive Yohan). Terme relatif au sang -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("plasma", "partie liquide du sang"),
        ("sérum", "plasma dépourvu de facteurs de coagulation"),
        ("hématocrite", "proportion de globules rouges dans le sang"),
    ]
    publie("definition_terme_sang", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme du sang -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_gros_vaisseau")
def ingere_role_gros_vaisseau():
    # SOURCE = LE MODÈLE (directive Yohan). Gros vaisseau nommé -> rôle. Textbook physiologie cardiovasculaire,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("aorte", "distribution du sang oxygéné dans le corps"),
        ("artère pulmonaire", "transport du sang vers les poumons"),
        ("veine pulmonaire", "transport du sang oxygéné des poumons vers le cœur"),
        ("veine cave", "retour du sang vers le cœur"),
    ]
    publie("role_gros_vaisseau", "physique",
           "Modèle (Claude) — physiologie cardiovasculaire textbook curée (gros vaisseau -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_appareil_locomoteur")
def ingere_definition_terme_appareil_locomoteur():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de l'appareil locomoteur -> définition. Textbook anatomie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("muscle", "organe contractile"),
        ("tendon", "structure reliant un muscle à un os"),
        ("ligament", "structure reliant deux os"),
        ("articulation", "jonction entre deux os"),
    ]
    publie("definition_terme_appareil_locomoteur", "physique",
           "Modèle (Claude) — anatomie textbook curée (terme locomoteur -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_excretion")
def ingere_definition_terme_excretion():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de l'excrétion -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("urine", "liquide excrété par les reins"),
        ("urée", "déchet azoté du métabolisme"),
        ("vessie", "réservoir d'urine"),
    ]
    publie("definition_terme_excretion", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme d'excrétion -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("localisation_valve_cardiaque")
def ingere_localisation_valve_cardiaque():
    # SOURCE = LE MODÈLE (directive Yohan). Valve cardiaque -> localisation. Textbook anatomie cardiaque, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("valve mitrale", "entre l'oreillette et le ventricule gauche"),
        ("valve tricuspide", "entre l'oreillette et le ventricule droit"),
        ("valve aortique", "à la sortie du ventricule gauche"),
        ("valve pulmonaire", "à la sortie du ventricule droit"),
    ]
    publie("localisation_valve_cardiaque", "physique",
           "Modèle (Claude) — anatomie cardiaque textbook curée (valve -> localisation ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_type_dentition")
def ingere_definition_type_dentition():
    # SOURCE = LE MODÈLE (directive Yohan). Type de dentition -> définition. Textbook anatomie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("dentition lactéale", "ensemble des dents de lait"),
        ("dentition définitive", "ensemble des dents permanentes"),
    ]
    publie("definition_type_dentition", "physique",
           "Modèle (Claude) — anatomie textbook curée (type de dentition -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_neurologie")
def ingere_definition_terme_neurologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de neurologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("neurone", "cellule du système nerveux"),
        ("influx nerveux", "signal électrique"),
        ("synapse", "zone de communication entre deux neurones"),
        ("neurotransmetteur", "molécule de communication chimique entre neurones"),
    ]
    publie("definition_terme_neurologie", "physique",
           "Modèle (Claude) — neurologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_endocrinologie")
def ingere_definition_terme_endocrinologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'endocrinologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("hormone", "messager chimique transporté par le sang"),
        ("glande endocrine", "glande qui produit des hormones"),
        ("organe cible", "organe sur lequel agit une hormone"),
    ]
    publie("definition_terme_endocrinologie", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_respiration")
def ingere_definition_terme_respiration():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de la respiration -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("ventilation", "renouvellement de l'air dans les poumons"),
        ("hématose", "oxygénation du sang"),
        ("capacité vitale", "volume d'air maximal mobilisable"),
    ]
    publie("definition_terme_respiration", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme respiration -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_circulation")
def ingere_definition_terme_circulation():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de la circulation -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("circulation pulmonaire", "circulation entre le cœur et les poumons"),
        ("circulation systémique", "circulation entre le cœur et les organes"),
        ("pouls", "battement perçu des artères"),
        ("pression artérielle", "pression du sang sur la paroi des artères"),
    ]
    publie("definition_terme_circulation", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme circulation -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_digestion")
def ingere_definition_terme_digestion():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de la digestion -> définition. Textbook physiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("digestion mécanique", "fragmentation des aliments"),
        ("digestion chimique", "transformation des aliments par les enzymes"),
        ("bol alimentaire", "aliments mâchés et imprégnés de salive"),
        ("chyme", "bouillie alimentaire issue de l'estomac"),
    ]
    publie("definition_terme_digestion", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme digestion -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_cellule_immunitaire")
def ingere_role_cellule_immunitaire():
    # SOURCE = LE MODÈLE (directive Yohan). Cellule immunitaire -> rôle. Textbook immunologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("lymphocyte B", "production des anticorps"),
        ("lymphocyte T", "coordination et exécution de la réponse immunitaire"),
        ("phagocyte", "ingestion des agents étrangers"),
    ]
    publie("role_cellule_immunitaire", "physique",
           "Modèle (Claude) — immunologie textbook curée (cellule immunitaire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_reproduction_vegetale")
def ingere_definition_terme_reproduction_vegetale():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de reproduction végétale -> définition. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("pollinisation", "transport du pollen"),
        ("fécondation", "union des gamètes mâle et femelle"),
        ("fructification", "formation du fruit"),
    ]
    publie("definition_terme_reproduction_vegetale", "physique",
           "Modèle (Claude) — botanique textbook curée (terme reproduction végétale -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_hygiene")
def ingere_definition_terme_hygiene():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'hygiène/microbiologie -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("asepsie", "absence de micro-organismes"),
        ("antisepsie", "destruction des micro-organismes sur les tissus vivants"),
        ("stérilisation", "destruction de tous les micro-organismes"),
        ("désinfection", "destruction des micro-organismes sur les surfaces"),
    ]
    publie("definition_terme_hygiene", "physique",
           "Modèle (Claude) — hygiène textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_type_mutation")
def ingere_definition_type_mutation():
    # SOURCE = LE MODÈLE (directive Yohan). Type de mutation -> définition. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("mutation ponctuelle", "affecte un seul nucléotide"),
        ("mutation chromosomique", "affecte la structure ou le nombre de chromosomes"),
    ]
    publie("definition_type_mutation", "physique",
           "Modèle (Claude) — génétique textbook curée (type de mutation -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_biodiversite")
def ingere_definition_terme_biodiversite():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de biodiversité -> définition. Textbook écologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("biodiversité", "variété des êtres vivants"),
        ("espèce endémique", "espèce présente dans une seule région"),
        ("espèce invasive", "espèce introduite qui prolifère"),
    ]
    publie("definition_terme_biodiversite", "physique",
           "Modèle (Claude) — écologie textbook curée (terme biodiversité -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_zygotie")
def ingere_definition_zygotie():
    # SOURCE = LE MODÈLE (directive Yohan). État allélique -> définition. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("homozygote", "deux allèles identiques pour un gène"),
        ("hétérozygote", "deux allèles différents pour un gène"),
    ]
    publie("definition_zygotie", "physique",
           "Modèle (Claude) — génétique textbook curée (zygotie -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_oncologie")
def ingere_definition_terme_oncologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'oncologie -> définition. Textbook médecine, FAUX=0 ;
    # définitionnel.
    paires = [
        ("tumeur", "masse de cellules anormales"),
        ("tumeur bénigne", "tumeur non cancéreuse"),
        ("tumeur maligne", "tumeur cancéreuse"),
        ("métastase", "propagation d'un cancer à distance"),
    ]
    publie("definition_terme_oncologie", "physique",
           "Modèle (Claude) — médecine textbook curée (terme oncologie -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_type_chromosome")
def ingere_definition_type_chromosome():
    # SOURCE = LE MODÈLE (directive Yohan). Type de chromosome -> définition. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("autosome", "chromosome non sexuel"),
        ("chromosome sexuel", "chromosome déterminant le sexe"),
    ]
    publie("definition_type_chromosome", "physique",
           "Modèle (Claude) — génétique textbook curée (type de chromosome -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_immunite_pratique")
def ingere_definition_terme_immunite_pratique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de pratique immunitaire -> définition. Textbook immunologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("vaccination", "injection préventive stimulant l'immunité"),
        ("sérothérapie", "injection d'anticorps"),
        ("allergie", "réaction excessive du système immunitaire"),
    ]
    publie("definition_terme_immunite_pratique", "physique",
           "Modèle (Claude) — immunologie textbook curée (terme pratique -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_biotechnologie")
def ingere_definition_terme_biotechnologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de biotechnologie -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("OGM", "organisme génétiquement modifié"),
        ("clonage", "production d'individus génétiquement identiques"),
        ("thérapie génique", "correction d'un gène défectueux"),
    ]
    publie("definition_terme_biotechnologie", "physique",
           "Modèle (Claude) — biotechnologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_systematique")
def ingere_definition_terme_systematique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de systématique -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("taxon", "groupe d'organismes classés ensemble"),
        ("espèce", "unité de base de la classification"),
        ("nomenclature binominale", "système de nommage à deux termes"),
    ]
    publie("definition_terme_systematique", "physique",
           "Modèle (Claude) — systématique textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_parasitologie")
def ingere_definition_terme_parasitologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de parasitologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("parasite", "organisme vivant aux dépens d'un autre"),
        ("hôte", "organisme hébergeant un parasite"),
        ("vecteur", "organisme transmettant un agent pathogène"),
    ]
    publie("definition_terme_parasitologie", "physique",
           "Modèle (Claude) — parasitologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_epidemiologie")
def ingere_definition_terme_epidemiologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'épidémiologie -> définition. Textbook, FAUX=0 ; définitionnel.
    paires = [
        ("endémie", "présence habituelle d'une maladie dans une région"),
        ("épidémie", "augmentation rapide du nombre de cas d'une maladie"),
        ("pandémie", "épidémie à l'échelle mondiale"),
        ("incidence", "nombre de nouveaux cas d'une maladie"),
    ]
    publie("definition_terme_epidemiologie", "physique",
           "Modèle (Claude) — épidémiologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_glande_endocrine")
def ingere_role_glande_endocrine():
    # SOURCE = LE MODÈLE (directive Yohan). Glande endocrine -> rôle principal. Textbook endocrinologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("hypophyse", "commande des autres glandes endocrines"),
        ("thyroïde", "régulation du métabolisme"),
        ("glandes surrénales", "réponse au stress"),
        ("pancréas endocrine", "régulation de la glycémie"),
    ]
    publie("role_glande_endocrine", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (glande endocrine -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_systeme_nerveux_fonctionnel")
def ingere_role_systeme_nerveux_fonctionnel():
    # SOURCE = LE MODÈLE (directive Yohan). Division fonctionnelle du système nerveux -> rôle. Textbook
    # neurophysiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("système nerveux somatique", "contrôle des mouvements volontaires"),
        ("système nerveux autonome", "contrôle des fonctions involontaires"),
    ]
    publie("role_systeme_nerveux_fonctionnel", "physique",
           "Modèle (Claude) — neurophysiologie textbook curée (division fonctionnelle du SN -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_sn_autonome")
def ingere_role_sn_autonome():
    # SOURCE = LE MODÈLE (directive Yohan). Branche du système nerveux autonome -> rôle. Textbook physiologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("système nerveux sympathique", "préparation à l'action"),
        ("système nerveux parasympathique", "favorise le repos et la digestion"),
    ]
    publie("role_sn_autonome", "physique",
           "Modèle (Claude) — physiologie textbook curée (SN autonome -> rôle ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_transport_membranaire")
def ingere_definition_transport_membranaire():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de transport membranaire -> définition. Textbook biologie
    # cellulaire, FAUX=0 ; définitionnel.
    paires = [
        ("diffusion", "passage passif selon le gradient de concentration"),
        ("osmose", "diffusion de l'eau à travers une membrane"),
        ("transport actif", "passage contre le gradient avec dépense d'énergie"),
    ]
    publie("definition_transport_membranaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (transport membranaire -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_thermoregulation")
def ingere_definition_thermoregulation():
    # SOURCE = LE MODÈLE (directive Yohan). Type thermique d'organisme -> définition. Textbook physiologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("homéotherme", "température corporelle constante"),
        ("poïkilotherme", "température corporelle variable selon le milieu"),
    ]
    publie("definition_thermoregulation", "physique",
           "Modèle (Claude) — physiologie textbook curée (thermorégulation -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_sens")
def ingere_definition_sens():
    # SOURCE = LE MODÈLE (directive Yohan). Sens -> ce qu'il perçoit. Textbook physiologie sensorielle, FAUX=0 ;
    # définitionnel.
    paires = [
        ("vue", "perception de la lumière"),
        ("ouïe", "perception des sons"),
        ("odorat", "perception des odeurs"),
        ("goût", "perception des saveurs"),
        ("toucher", "perception du contact"),
    ]
    publie("definition_sens", "physique",
           "Modèle (Claude) — physiologie sensorielle textbook curée (sens -> perception ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organite_supplementaire")
def ingere_role_organite_supplementaire():
    # SOURCE = LE MODÈLE (directive Yohan). Organite (complément de fonction_organite) -> rôle. Textbook biologie
    # cellulaire, FAUX=0 ; fonctionnel.
    paires = [
        ("vacuole", "stockage et maintien de la turgescence"),
        ("réticulum endoplasmique", "synthèse et transport des molécules"),
        ("centriole", "organisation de la division cellulaire"),
        ("cytosquelette", "soutien et forme de la cellule"),
    ]
    publie("role_organite_supplementaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (organite -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_systeme_urinaire")
def ingere_role_partie_systeme_urinaire():
    # SOURCE = LE MODÈLE (directive Yohan). Organe du système urinaire -> rôle. Textbook physiologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("rein", "filtration du sang et production d'urine"),
        ("uretère", "transport de l'urine vers la vessie"),
        ("vessie", "stockage de l'urine"),
        ("urètre", "évacuation de l'urine"),
    ]
    publie("role_partie_systeme_urinaire", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe urinaire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organe_respiratoire")
def ingere_role_organe_respiratoire():
    # SOURCE = LE MODÈLE (directive Yohan). Organe respiratoire (voies) -> rôle. Textbook physiologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("nez", "filtration et réchauffement de l'air"),
        ("trachée", "conduction de l'air"),
        ("diaphragme", "muscle de la ventilation"),
    ]
    publie("role_organe_respiratoire", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe respiratoire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_arc_reflexe")
def ingere_definition_terme_arc_reflexe():
    # SOURCE = LE MODÈLE (directive Yohan). Élément du réflexe -> définition. Textbook neurophysiologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("arc réflexe", "trajet nerveux d'un réflexe"),
        ("récepteur", "structure qui capte le stimulus"),
        ("effecteur", "organe qui exécute la réponse"),
    ]
    publie("definition_terme_arc_reflexe", "physique",
           "Modèle (Claude) — neurophysiologie textbook curée (élément du réflexe -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_cycle_vie")
def ingere_definition_terme_cycle_vie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme du cycle de vie -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("cycle de vie", "suite des étapes de la vie d'un organisme"),
        ("métamorphose", "transformation profonde au cours du développement"),
        ("mue", "changement de l'enveloppe externe"),
    ]
    publie("definition_terme_cycle_vie", "physique",
           "Modèle (Claude) — biologie textbook curée (terme cycle de vie -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_brassage_genetique")
def ingere_definition_brassage_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Type de brassage génétique -> définition. Textbook génétique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("brassage interchromosomique", "répartition aléatoire des chromosomes"),
        ("brassage intrachromosomique", "échange de segments par crossing-over"),
    ]
    publie("definition_brassage_genetique", "physique",
           "Modèle (Claude) — génétique textbook curée (brassage -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_partie_squelette")
def ingere_definition_partie_squelette():
    # SOURCE = LE MODÈLE (directive Yohan). Partie du squelette -> définition/contenu. Textbook anatomie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("squelette axial", "crâne, colonne vertébrale et cage thoracique"),
        ("squelette appendiculaire", "membres et leurs ceintures"),
    ]
    publie("definition_partie_squelette", "physique",
           "Modèle (Claude) — anatomie textbook curée (partie du squelette -> contenu ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_regime_alimentaire")
def ingere_definition_regime_alimentaire():
    # SOURCE = LE MODÈLE (directive Yohan). Régime alimentaire -> définition (distinct de regime_alimentaire qui
    # classe les espèces). Textbook zoologie, FAUX=0 ; définitionnel.
    paires = [
        ("herbivore", "se nourrit de végétaux"),
        ("carnivore", "se nourrit d'animaux"),
        ("omnivore", "se nourrit de végétaux et d'animaux"),
        ("insectivore", "se nourrit d'insectes"),
    ]
    publie("definition_regime_alimentaire", "physique",
           "Modèle (Claude) — zoologie textbook curée (régime -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_segment_digestif")
def ingere_role_segment_digestif():
    # SOURCE = LE MODÈLE (directive Yohan). Segment du tube digestif (complément de role_organe_digestif) -> rôle.
    # Textbook physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("bouche", "mastication et insalivation"),
        ("œsophage", "transport des aliments vers l'estomac"),
        ("rectum", "stockage des matières fécales"),
    ]
    publie("role_segment_digestif", "physique",
           "Modèle (Claude) — physiologie textbook curée (segment digestif -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_partie_feuille")
def ingere_role_partie_feuille():
    # SOURCE = LE MODÈLE (directive Yohan). Partie d'une feuille -> rôle. Textbook botanique, FAUX=0 ; fonctionnel.
    paires = [
        ("limbe", "surface de photosynthèse"),
        ("pétiole", "relie le limbe à la tige"),
        ("nervure", "conduction de la sève"),
    ]
    publie("role_partie_feuille", "physique",
           "Modèle (Claude) — botanique textbook curée (partie de feuille -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_partie_tige")
def ingere_definition_partie_tige():
    # SOURCE = LE MODÈLE (directive Yohan). Partie d'une tige -> définition. Textbook botanique, FAUX=0 ;
    # définitionnel.
    paires = [
        ("nœud", "point d'insertion des feuilles"),
        ("entre-nœud", "portion de tige entre deux nœuds"),
        ("bourgeon", "ébauche de rameau ou de fleur"),
    ]
    publie("definition_partie_tige", "physique",
           "Modèle (Claude) — botanique textbook curée (partie de tige -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("secretion_organe_digestif")
def ingere_secretion_organe_digestif():
    # SOURCE = LE MODÈLE (directive Yohan). Organe digestif -> sécrétion produite. Textbook physiologie, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("glandes salivaires", "salive"),
        ("estomac", "suc gastrique"),
        ("pancréas", "suc pancréatique"),
        ("foie", "bile"),
    ]
    publie("secretion_organe_digestif", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe digestif -> sécrétion ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_constituant_membrane")
def ingere_role_constituant_membrane():
    # SOURCE = LE MODÈLE (directive Yohan). Constituant de la membrane plasmique -> rôle. Textbook biologie
    # cellulaire, FAUX=0 ; fonctionnel.
    paires = [
        ("phospholipides", "formation de la bicouche"),
        ("protéines membranaires", "transport et communication"),
        ("cholestérol", "régulation de la fluidité de la membrane"),
    ]
    publie("role_constituant_membrane", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (constituant membranaire -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_classe_vertebre")
def ingere_definition_classe_vertebre():
    # SOURCE = LE MODÈLE (directive Yohan). Classe de vertébrés -> définition (distinct de classe_vertebre_animal
    # par espèce). Textbook zoologie, FAUX=0 ; définitionnel.
    paires = [
        ("poisson", "vertébré aquatique à branchies"),
        ("amphibien", "vertébré à peau nue"),
        ("reptile", "vertébré à écailles"),
        ("oiseau", "vertébré à plumes"),
        ("mammifère", "vertébré à poils qui allaite ses petits"),
    ]
    publie("definition_classe_vertebre", "physique",
           "Modèle (Claude) — zoologie textbook curée (classe de vertébré -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_groupe_invertebre")
def ingere_definition_groupe_invertebre():
    # SOURCE = LE MODÈLE (directive Yohan). Groupe d'invertébrés -> définition (distinct de classe_invertebre_animal
    # par espèce). Textbook zoologie, FAUX=0 ; définitionnel.
    paires = [
        ("insecte", "arthropode à six pattes"),
        ("arachnide", "arthropode à huit pattes"),
        ("crustacé", "arthropode souvent aquatique à carapace"),
        ("mollusque", "invertébré à corps mou"),
    ]
    publie("definition_groupe_invertebre", "physique",
           "Modèle (Claude) — zoologie textbook curée (groupe d'invertébré -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_ethologie")
def ingere_definition_terme_ethologie():
    # SOURCE = LE MODÈLE (directive Yohan). Terme d'éthologie -> définition. Textbook biologie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("territoire", "zone défendue par un animal"),
        ("migration", "déplacement saisonnier d'animaux"),
        ("hibernation", "ralentissement de l'activité pendant l'hiver"),
        ("parade nuptiale", "comportement de séduction"),
    ]
    publie("definition_terme_ethologie", "physique",
           "Modèle (Claude) — éthologie textbook curée (terme -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organe_lymphoide")
def ingere_role_organe_lymphoide():
    # SOURCE = LE MODÈLE (directive Yohan). Organe lymphoïde -> rôle. Textbook immunologie, FAUX=0 ; fonctionnel.
    paires = [
        ("ganglion lymphatique", "filtration de la lymphe"),
        ("rate", "filtration du sang et réponse immunitaire"),
        ("thymus", "maturation des lymphocytes T"),
    ]
    publie("role_organe_lymphoide", "physique",
           "Modèle (Claude) — immunologie textbook curée (organe lymphoïde -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_annexe_peau")
def ingere_role_annexe_peau():
    # SOURCE = LE MODÈLE (directive Yohan). Annexe cutanée -> rôle. Textbook anatomie, FAUX=0 ; fonctionnel.
    paires = [
        ("poil", "protection et thermorégulation"),
        ("glande sudoripare", "sécrétion de la sueur"),
        ("glande sébacée", "sécrétion du sébum"),
        ("ongle", "protection de l'extrémité des doigts"),
    ]
    publie("role_annexe_peau", "physique",
           "Modèle (Claude) — anatomie textbook curée (annexe cutanée -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("fonction_systeme_complement")
def ingere_fonction_systeme_complement():
    # SOURCE = LE MODÈLE (directive Yohan). Système du corps (complément de fonction_systeme_humain) -> fonction.
    # Textbook physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("système lymphatique", "circulation de la lymphe et défense"),
        ("système tégumentaire", "protection externe du corps"),
        ("système reproducteur", "reproduction"),
        ("système musculaire", "mouvement"),
    ]
    publie("fonction_systeme_complement", "physique",
           "Modèle (Claude) — physiologie textbook curée (système -> fonction ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_liquide_corporel")
def ingere_role_liquide_corporel():
    # SOURCE = LE MODÈLE (directive Yohan). Liquide corporel -> rôle. Textbook physiologie, FAUX=0 ; fonctionnel.
    paires = [
        ("sang", "transport des substances dans l'organisme"),
        ("lymphe", "drainage et défense"),
        ("liquide céphalorachidien", "protection du système nerveux central"),
    ]
    publie("role_liquide_corporel", "physique",
           "Modèle (Claude) — physiologie textbook curée (liquide corporel -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_pigment_vegetal")
def ingere_role_pigment_vegetal():
    # SOURCE = LE MODÈLE (directive Yohan). Pigment végétal -> rôle/couleur. Textbook botanique, FAUX=0 ;
    # fonctionnel.
    paires = [
        ("chlorophylle", "absorption de la lumière pour la photosynthèse"),
        ("caroténoïde", "pigment accessoire jaune-orangé"),
        ("anthocyane", "pigmentation rouge à bleue"),
    ]
    publie("role_pigment_vegetal", "physique",
           "Modèle (Claude) — botanique textbook curée (pigment végétal -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("role_microorganisme_alimentaire")
def ingere_role_microorganisme_alimentaire():
    # SOURCE = LE MODÈLE (directive Yohan). Micro-organisme utile en alimentation -> usage. Textbook microbiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("levure", "fabrication du pain et de la bière"),
        ("bactérie lactique", "fabrication du yaourt"),
        ("moisissure", "affinage de certains fromages"),
    ]
    publie("role_microorganisme_alimentaire", "physique",
           "Modèle (Claude) — microbiologie textbook curée (micro-organisme -> usage alimentaire ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_structure_adn")
def ingere_definition_terme_structure_adn():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de structure des acides nucléiques -> définition. Textbook
    # biologie moléculaire, FAUX=0 ; définitionnel.
    paires = [
        ("nucléotide", "unité de base des acides nucléiques"),
        ("double hélice", "structure en spirale de l'ADN"),
        ("base azotée", "composant variable du nucléotide"),
    ]
    publie("definition_terme_structure_adn", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (structure ADN -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_etape_cycle_cellulaire")
def ingere_definition_etape_cycle_cellulaire():
    # SOURCE = LE MODÈLE (directive Yohan). Étape du cycle cellulaire -> définition. Textbook biologie cellulaire,
    # FAUX=0 ; définitionnel.
    paires = [
        ("interphase", "phase de croissance et de réplication de l'ADN"),
        ("mitose", "division du noyau"),
        ("cytocinèse", "division du cytoplasme"),
    ]
    publie("definition_etape_cycle_cellulaire", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (étape du cycle cellulaire -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_physiologie_effort")
def ingere_definition_terme_physiologie_effort():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de physiologie de l'effort -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("fréquence cardiaque", "nombre de battements du cœur par minute"),
        ("débit cardiaque", "volume de sang éjecté par le cœur par minute"),
        ("VO2 max", "consommation maximale d'oxygène"),
    ]
    publie("definition_terme_physiologie_effort", "physique",
           "Modèle (Claude) — physiologie textbook curée (terme effort -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_nutrition_sante")
def ingere_definition_terme_nutrition_sante():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de nutrition/santé -> définition. Textbook, FAUX=0 ;
    # définitionnel.
    paires = [
        ("régime équilibré", "apports adaptés aux besoins de l'organisme"),
        ("malnutrition", "déséquilibre alimentaire"),
        ("obésité", "excès de masse grasse"),
    ]
    publie("definition_terme_nutrition_sante", "physique",
           "Modèle (Claude) — nutrition textbook curée (terme santé -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_microbiologie_culture")
def ingere_definition_terme_microbiologie_culture():
    # SOURCE = LE MODÈLE (directive Yohan). Terme de culture microbienne -> définition. Textbook microbiologie,
    # FAUX=0 ; définitionnel.
    paires = [
        ("milieu de culture", "support nutritif de croissance des micro-organismes"),
        ("colonie", "amas de micro-organismes issus d'une seule cellule"),
        ("souche", "lignée d'un micro-organisme"),
    ]
    publie("definition_terme_microbiologie_culture", "physique",
           "Modèle (Claude) — microbiologie textbook curée (terme culture -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_etape_formation_urine")
def ingere_definition_etape_formation_urine():
    # SOURCE = LE MODÈLE (directive Yohan). Étape de la formation de l'urine -> définition. Textbook physiologie
    # rénale, FAUX=0 ; définitionnel.
    paires = [
        ("filtration glomérulaire", "passage du plasma dans le néphron"),
        ("réabsorption", "récupération de substances utiles vers le sang"),
        ("sécrétion tubulaire", "ajout de substances à l'urine"),
    ]
    publie("definition_etape_formation_urine", "physique",
           "Modèle (Claude) — physiologie rénale textbook curée (étape -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_organe_systeme_nerveux_central")
def ingere_role_organe_systeme_nerveux_central():
    # SOURCE = LE MODÈLE (directive Yohan). Organe du système nerveux central -> rôle. Textbook neurophysiologie,
    # FAUX=0 ; fonctionnel.
    paires = [
        ("cerveau", "centre du traitement de l'information"),
        ("moelle épinière", "transmission des messages nerveux et réflexes"),
        ("tronc cérébral", "contrôle des fonctions vitales"),
    ]
    publie("role_organe_systeme_nerveux_central", "physique",
           "Modèle (Claude) — neurophysiologie textbook curée (organe du SNC -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_technique_genetique")
def ingere_definition_technique_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Technique de génétique -> définition. Textbook biologie moléculaire,
    # FAUX=0 ; définitionnel.
    paires = [
        ("séquençage", "détermination de l'ordre des nucléotides"),
        ("PCR", "amplification de l'ADN"),
        ("électrophorèse", "séparation des fragments d'ADN"),
    ]
    publie("definition_technique_genetique", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (technique -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_evolution_preuve")
def ingere_definition_terme_evolution_preuve():
    # SOURCE = LE MODÈLE (directive Yohan). Terme des preuves de l'évolution -> définition. Textbook biologie
    # évolutive, FAUX=0 ; définitionnel.
    paires = [
        ("homologie", "ressemblance due à une origine commune"),
        ("analogie", "ressemblance due à une fonction commune"),
        ("organe vestigial", "organe atrophié hérité d'un ancêtre"),
    ]
    publie("definition_terme_evolution_preuve", "physique",
           "Modèle (Claude) — biologie évolutive textbook curée (preuve -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_categorie_aliment")
def ingere_definition_categorie_aliment():
    # SOURCE = LE MODÈLE (directive Yohan). Catégorie fonctionnelle d'aliment -> rôle. Textbook nutrition, FAUX=0 ;
    # définitionnel.
    paires = [
        ("aliment énergétique", "fournit de l'énergie"),
        ("aliment bâtisseur", "construit et renouvelle les tissus"),
        ("aliment protecteur", "régule le fonctionnement de l'organisme"),
    ]
    publie("definition_categorie_aliment", "physique",
           "Modèle (Claude) — nutrition textbook curée (catégorie d'aliment -> rôle ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_multiplication_vegetative")
def ingere_definition_multiplication_vegetative():
    # SOURCE = LE MODÈLE (directive Yohan). Mode de multiplication végétative -> définition. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("bouturage", "nouvelle plante à partir d'un fragment"),
        ("marcottage", "enracinement d'une tige restée attachée à la plante"),
        ("greffage", "union de deux plantes"),
        ("division", "séparation de touffes"),
    ]
    publie("definition_multiplication_vegetative", "physique",
           "Modèle (Claude) — botanique textbook curée (multiplication végétative -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_anomalie_chromosomique")
def ingere_definition_anomalie_chromosomique():
    # SOURCE = LE MODÈLE (directive Yohan). Anomalie du nombre de chromosomes -> définition. Textbook génétique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("trisomie", "présence d'un chromosome surnuméraire"),
        ("monosomie", "absence d'un chromosome"),
    ]
    publie("definition_anomalie_chromosomique", "physique",
           "Modèle (Claude) — génétique textbook curée (anomalie chromosomique -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("role_type_dent")
def ingere_role_type_dent():
    # SOURCE = LE MODÈLE (directive Yohan). Type de dent -> rôle (distinct de type_dent qui classe les dents
    # nommées). Textbook anatomie, FAUX=0 ; fonctionnel.
    paires = [
        ("incisive", "couper les aliments"),
        ("canine", "déchirer"),
        ("prémolaire", "écraser"),
        ("molaire", "broyer"),
    ]
    publie("role_type_dent", "physique",
           "Modèle (Claude) — anatomie textbook curée (type de dent -> rôle ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_etape_developpement_embryon")
def ingere_definition_etape_developpement_embryon():
    # SOURCE = LE MODÈLE (directive Yohan). Étape du développement embryonnaire -> définition. Textbook
    # embryologie, FAUX=0 ; définitionnel.
    paires = [
        ("segmentation", "divisions de l'œuf fécondé"),
        ("gastrulation", "formation des feuillets embryonnaires"),
        ("organogenèse", "formation des organes"),
    ]
    publie("definition_etape_developpement_embryon", "physique",
           "Modèle (Claude) — embryologie textbook curée (étape -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_fruit_graine")
def ingere_definition_fruit_graine():
    # SOURCE = LE MODÈLE (directive Yohan). Organe de la reproduction végétale -> origine. Textbook botanique,
    # FAUX=0 ; définitionnel.
    paires = [
        ("fruit", "organe issu de la transformation de l'ovaire"),
        ("graine", "organe issu de l'ovule contenant l'embryon"),
    ]
    publie("definition_fruit_graine", "physique",
           "Modèle (Claude) — botanique textbook curée (fruit/graine -> origine ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_categorie_glucide")
def ingere_definition_categorie_glucide():
    # SOURCE = LE MODÈLE (directive Yohan). Catégorie de glucide -> définition (distinct de type_glucide par
    # molécule). Textbook biochimie, FAUX=0 ; définitionnel.
    paires = [
        ("ose", "glucide simple"),
        ("diholoside", "glucide formé de deux oses"),
        ("polyoside", "glucide formé de nombreux oses"),
    ]
    publie("definition_categorie_glucide", "physique",
           "Modèle (Claude) — biochimie textbook curée (catégorie de glucide -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_acide_gras")
def ingere_definition_acide_gras():
    # SOURCE = LE MODÈLE (directive Yohan). Type d'acide gras -> définition. Textbook biochimie, FAUX=0 ;
    # définitionnel.
    paires = [
        ("acide gras saturé", "sans double liaison"),
        ("acide gras insaturé", "avec au moins une double liaison"),
    ]
    publie("definition_acide_gras", "physique",
           "Modèle (Claude) — biochimie textbook curée (acide gras -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("definition_terme_code_genetique")
def ingere_definition_terme_code_genetique():
    # SOURCE = LE MODÈLE (directive Yohan). Terme du code génétique -> définition. Textbook biologie moléculaire,
    # FAUX=0 ; définitionnel.
    paires = [
        ("codon", "triplet de nucléotides"),
        ("code génétique", "correspondance entre les codons et les acides aminés"),
        ("anticodon", "triplet complémentaire de l'ARN de transfert"),
    ]
    publie("definition_terme_code_genetique", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (code génétique -> définition ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("type_arn_role")
def ingere_type_arn_role():
    # SOURCE = LE MODÈLE. Type d'ARN -> rôle biologique. Textbook biologie moléculaire, définitionnel, FAUX=0.
    paires = [
        ("ARN messager", "transport de l'information génétique du noyau au ribosome"),
        ("ARN de transfert", "transport des acides aminés vers le ribosome"),
        ("ARN ribosomique", "constituant structural du ribosome"),
    ]
    publie("type_arn_role", "physique",
           "Modèle (Claude) — biologie moléculaire textbook curée (rôle de type d'ARN ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("tissu_animal_fondamental")
def ingere_tissu_animal_fondamental():
    # SOURCE = LE MODÈLE. Les 4 tissus animaux fondamentaux -> rôle. Textbook histologie, ensemble fermé, FAUX=0.
    paires = [
        ("tissu épithélial", "revêtement et protection des surfaces"),
        ("tissu conjonctif", "soutien et liaison des autres tissus"),
        ("tissu musculaire", "contraction"),
        ("tissu nerveux", "transmission de l'influx nerveux"),
    ]
    publie("tissu_animal_fondamental", "physique",
           "Modèle (Claude) — histologie textbook curée (rôle des 4 tissus animaux fondamentaux ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("tissu_vegetal_fonction")
def ingere_tissu_vegetal_fonction():
    # SOURCE = LE MODÈLE. Tissu végétal (libellés non ambigus) -> fonction. Textbook botanique, FAUX=0.
    paires = [
        ("xylème", "conduction de la sève brute"),
        ("phloème", "conduction de la sève élaborée"),
        ("méristème", "croissance par division cellulaire"),
        ("collenchyme", "soutien des organes jeunes"),
        ("sclérenchyme", "soutien des organes matures"),
    ]
    publie("tissu_vegetal_fonction", "physique",
           "Modèle (Claude) — botanique textbook curée (fonction de tissu végétal ; libellés non ambigus ; FAUX=0 vérifié)", paires)


@domaine("phase_mitose_evenement")
def ingere_phase_mitose_evenement():
    # SOURCE = LE MODÈLE. Phase de la mitose -> événement caractéristique. Textbook biologie cellulaire, ensemble fermé, FAUX=0.
    paires = [
        ("prophase", "condensation des chromosomes"),
        ("métaphase", "alignement des chromosomes sur la plaque équatoriale"),
        ("anaphase", "séparation des chromatides soeurs"),
        ("télophase", "reconstitution des enveloppes nucléaires"),
    ]
    publie("phase_mitose_evenement", "physique",
           "Modèle (Claude) — biologie cellulaire textbook curée (événement par phase de mitose ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("niveau_organisation_vivant")
def ingere_niveau_organisation_vivant():
    # SOURCE = LE MODÈLE. Niveau d'organisation du vivant -> définition. Textbook biologie, définitionnel, FAUX=0.
    paires = [
        ("cellule", "unité structurale et fonctionnelle de base du vivant"),
        ("tissu", "ensemble de cellules semblables assurant une même fonction"),
        ("organe", "ensemble de tissus assurant une fonction"),
        ("appareil", "ensemble d'organes concourant à une grande fonction"),
        ("organisme", "être vivant complet"),
    ]
    publie("niveau_organisation_vivant", "physique",
           "Modèle (Claude) — biologie textbook curée (définition de niveau d'organisation du vivant ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("type_neurone_role")
def ingere_type_neurone_role():
    # SOURCE = LE MODÈLE. Type fonctionnel de neurone -> rôle. Textbook neurophysiologie, ensemble fermé, FAUX=0.
    paires = [
        ("neurone sensitif", "transmission du message nerveux des récepteurs vers le système nerveux central"),
        ("neurone moteur", "transmission du message nerveux vers les organes effecteurs"),
        ("interneurone", "connexion entre neurones au sein du système nerveux central"),
    ]
    publie("type_neurone_role", "physique",
           "Modèle (Claude) — neurophysiologie textbook curée (rôle de type de neurone ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_inflorescence_definition")
def ingere_type_inflorescence_definition():
    # SOURCE = LE MODÈLE. Type d'inflorescence -> définition. Textbook botanique, définitionnel, FAUX=0.
    paires = [
        ("épi", "inflorescence à fleurs sessiles disposées le long d'un axe allongé"),
        ("grappe", "inflorescence à fleurs pédicellées disposées le long d'un axe allongé"),
        ("ombelle", "inflorescence dont les pédicelles partent tous d'un même point"),
        ("capitule", "inflorescence à fleurs sessiles serrées sur un réceptacle élargi"),
        ("panicule", "grappe composée de grappes"),
        # — approfondissement run-autonome v3 (termes botaniques certains) —
        ("corymbe", "grappe dont les fleurs atteignent toutes le même niveau"),
        ("cyme", "inflorescence dont l'axe se termine par une fleur"),
        ("spadice", "épi à axe charnu entouré d'une spathe"),
        ("chaton", "épi souple et retombant de fleurs unisexuées"),
        ("ombelle composée", "ombelle dont chaque rayon porte une petite ombelle"),
    ]
    publie("type_inflorescence_definition", "physique",
           "Modèle (Claude) — botanique textbook curée (définition de type d'inflorescence ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("nervation_feuille_definition")
def ingere_nervation_feuille_definition():
    # SOURCE = LE MODÈLE. Type de nervation foliaire -> définition. Textbook botanique, définitionnel, FAUX=0.
    paires = [
        ("nervation pennée", "nervures secondaires partant d'une unique nervure principale"),
        ("nervation palmée", "plusieurs nervures principales partant de la base du limbe"),
        ("nervation parallèle", "nervures principales parallèles entre elles"),
    ]
    publie("nervation_feuille_definition", "physique",
           "Modèle (Claude) — botanique textbook curée (définition de nervation foliaire ; définitionnel ; FAUX=0 vérifié)", paires)


@domaine("macromolecule_biologique_fonction")
def ingere_macromolecule_biologique_fonction():
    # SOURCE = LE MODÈLE. Macromolécule biologique -> fonction principale. Textbook biochimie, FAUX=0.
    paires = [
        ("glucides", "source d'énergie"),
        ("lipides", "réserve d'énergie et constitution des membranes"),
        ("protéines", "fonctions structurales et catalytiques"),
        ("acides nucléiques", "stockage et transmission de l'information génétique"),
    ]
    publie("macromolecule_biologique_fonction", "physique",
           "Modèle (Claude) — biochimie textbook curée (fonction de macromolécule biologique ; FAUX=0 vérifié)", paires)


@domaine("type_culture_agricole")
def ingere_type_culture_agricole():
    # SOURCE = LE MODÈLE. Plante cultivée -> catégorie agronomique ; ENSEMBLE FERMÉ : céréale / légumineuse /
    # oléagineux / sucrière / textile / fourragère. Textbook agronomie, FAUX=0 (classification d'usage).
    paires = [
        ("blé", "céréale"), ("maïs", "céréale"), ("riz", "céréale"), ("orge", "céréale"),
        ("avoine", "céréale"), ("seigle", "céréale"),
        ("soja", "légumineuse"), ("pois", "légumineuse"), ("haricot", "légumineuse"),
        ("lentille", "légumineuse"), ("fève", "légumineuse"), ("pois chiche", "légumineuse"),
        ("tournesol", "oléagineux"), ("colza", "oléagineux"), ("arachide", "oléagineux"), ("sésame", "oléagineux"),
        ("betterave sucrière", "sucrière"), ("canne à sucre", "sucrière"),
        ("coton", "textile"), ("lin", "textile"), ("chanvre", "textile"),
        ("luzerne", "fourragère"), ("trèfle", "fourragère"),
        # — approfondissement run-autonome (catégorie certaine) —
        ("millet", "céréale"), ("sorgho", "céréale"), ("épeautre", "céréale"),
        ("lentille", "légumineuse"), ("lupin", "légumineuse"),
        ("olivier", "oléagineux"), ("noix", "oléagineux"),
        ("betterave fourragère", "fourragère"), ("maïs fourrager", "fourragère"),
        ("jute", "textile"), ("sisal", "textile"),
    ]
    publie("type_culture_agricole", "convention",
           "Modèle (Claude) — agronomie textbook curée (catégorie de culture ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("forme_feuille_conifere")
def ingere_forme_feuille_conifere():
    # SOURCE = LE MODÈLE. Conifère -> forme du feuillage ; ENSEMBLE FERMÉ : aiguille / écaille. Textbook
    # botanique, FAUX=0. Pins/sapins/épicéas/mélèzes = aiguilles ; cyprès/thuyas/genévriers = écailles.
    paires = [
        ("pin", "aiguille"), ("sapin", "aiguille"), ("épicéa", "aiguille"), ("mélèze", "aiguille"),
        ("cèdre", "aiguille"), ("if", "aiguille"), ("pin sylvestre", "aiguille"),
        ("cyprès", "écaille"), ("thuya", "écaille"), ("genévrier", "écaille"),
    ]
    publie("forme_feuille_conifere", "physique",
           "Modèle (Claude) — botanique textbook curée (feuillage de conifère ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("position_yeux_animal")
def ingere_position_yeux_animal():
    # SOURCE = LE MODÈLE. Animal -> position des yeux ; ENSEMBLE FERMÉ : frontale (prédateurs, vision binoculaire)
    # / latérale (proies, large champ). Textbook éthologie/anatomie, FAUX=0 (règle prédateur/proie classique).
    paires = [
        ("lion", "frontale"), ("tigre", "frontale"), ("aigle royal", "frontale"), ("hibou", "frontale"),
        ("chouette", "frontale"), ("loup", "frontale"), ("guépard", "frontale"), ("chat", "frontale"),
        ("chimpanzé", "frontale"), ("être humain", "frontale"),
        ("lapin", "latérale"), ("cheval", "latérale"), ("vache", "latérale"), ("zèbre", "latérale"),
        ("mouton", "latérale"), ("chèvre", "latérale"), ("gazelle", "latérale"), ("souris", "latérale"),
        ("pigeon", "latérale"), ("antilope", "latérale"),
        # — approfondissement run-autonome v2 (prédateur frontal / proie latéral) —
        ("chat", "frontale"), ("ours brun", "frontale"), ("faucon pèlerin", "frontale"), ("loup", "frontale"),
        ("chouette", "frontale"), ("panthère", "frontale"),
        ("poule", "latérale"), ("canard", "latérale"), ("oie", "latérale"), ("bison", "latérale"),
        ("gnou", "latérale"), ("girafe", "latérale"),
    ]
    publie("position_yeux_animal", "physique",
           "Modèle (Claude) — éthologie textbook curée (yeux frontaux/latéraux ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_algue_couleur")
def ingere_type_algue_couleur():
    # SOURCE = LE MODÈLE. Algue -> grand groupe pigmentaire ; ENSEMBLE FERMÉ : verte (chlorophytes) / brune
    # (phéophytes) / rouge (rhodophytes). Textbook phycologie, FAUX=0.
    paires = [
        ("ulve", "verte"), ("laitue de mer", "verte"), ("chlorelle", "verte"), ("spirogyre", "verte"),
        ("laminaire", "brune"), ("fucus", "brune"), ("sargasse", "brune"), ("varech", "brune"),
        ("porphyra", "rouge"), ("dulse", "rouge"), ("coralline", "rouge"),
    ]
    publie("type_algue_couleur", "physique",
           "Modèle (Claude) — phycologie textbook curée (groupe d'algue ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("milieu_de_vie_animal")
def ingere_milieu_de_vie_animal():
    # SOURCE = LE MODÈLE. Animal -> milieu de vie ; ENSEMBLE FERMÉ : aquatique / terrestre. Textbook écologie,
    # FAUX=0. Espèces au milieu NON ambigu uniquement ; amphibiens/semi-aquatiques/volants EXCLUS.
    paires = [
        ("poisson", "aquatique"), ("requin", "aquatique"), ("thon rouge", "aquatique"),
        ("baleine bleue", "aquatique"), ("dauphin", "aquatique"), ("pieuvre", "aquatique"),
        ("méduse", "aquatique"), ("étoile de mer", "aquatique"), ("moule", "aquatique"),
        ("crabe", "aquatique"), ("crevette", "aquatique"), ("hippocampe", "aquatique"),
        ("raie manta", "aquatique"), ("calmar", "aquatique"), ("oursin", "aquatique"),
        ("corail", "aquatique"), ("anémone de mer", "aquatique"),
        ("lion", "terrestre"), ("tigre", "terrestre"), ("éléphant d'Afrique", "terrestre"),
        ("serpent", "terrestre"), ("lézard", "terrestre"), ("souris", "terrestre"),
        ("fourmi", "terrestre"), ("escargot", "terrestre"), ("ver de terre", "terrestre"),
        ("araignée", "terrestre"), ("scorpion", "terrestre"), ("mille-pattes", "terrestre"),
        # — approfondissement run-autonome (espèces univoques) —
        ("saumon atlantique", "aquatique"), ("morue", "aquatique"), ("sardine", "aquatique"),
        ("murène", "aquatique"), ("mérou", "aquatique"), ("homard", "aquatique"),
        ("seiche", "aquatique"), ("oursin", "aquatique"), ("éponge de mer", "aquatique"),
        ("tortue marine", "aquatique"), ("hareng", "aquatique"),
        ("tigre", "terrestre"), ("girafe", "terrestre"), ("zèbre", "terrestre"), ("loup", "terrestre"),
        ("renard roux", "terrestre"), ("ours brun", "terrestre"), ("chameau", "terrestre"),
        ("koala", "terrestre"), ("gecko", "terrestre"), ("cloporte", "terrestre"),
        ("hérisson", "terrestre"), ("taupe", "terrestre"),
        # — approfondissement run-autonome v3 —
        ("anguille", "aquatique"), ("congre", "aquatique"), ("langouste", "aquatique"),
        ("écrevisse", "aquatique"), ("carpe", "aquatique"), ("brochet", "aquatique"),
        ("perche", "aquatique"), ("hareng", "aquatique"),
        ("lézard", "terrestre"), ("gecko", "terrestre"), ("varan", "terrestre"), ("scarabée", "terrestre"),
        ("criquet", "terrestre"), ("sauterelle", "terrestre"), ("termite", "terrestre"), ("limace", "terrestre"),
    ]
    publie("milieu_de_vie_animal", "physique",
           "Modèle (Claude) — écologie textbook curée (milieu de vie aquatique/terrestre ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_deplacement_protozoaire")
def ingere_mode_deplacement_protozoaire():
    # SOURCE = LE MODÈLE. Protozoaire -> organe locomoteur ; ENSEMBLE FERMÉ : cils / flagelle / pseudopodes.
    # Textbook protistologie, FAUX=0. Paramécie = ciliés ; euglène/trypanosome = flagellés ; amibe = rhizopodes.
    paires = [
        ("paramécie", "cils"),
        ("euglène", "flagelle"), ("trypanosome", "flagelle"), ("Giardia lamblia", "flagelle"),
        ("Trypanosoma cruzi", "flagelle"),
        ("amibe", "pseudopodes"), ("Entamoeba histolytica", "pseudopodes"),
    ]
    publie("mode_deplacement_protozoaire", "physique",
           "Modèle (Claude) — protistologie textbook curée (locomotion ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_reserve_graine")
def ingere_type_reserve_graine():
    # SOURCE = LE MODÈLE. Graine/plante -> nature de la réserve dominante ; ENSEMBLE FERMÉ : amidon (céréales) /
    # lipide (oléagineux) / protéine (protéagineux). Textbook botanique/agronomie, FAUX=0 (catégories agronomiques).
    paires = [
        ("blé", "amidon"), ("maïs", "amidon"), ("riz", "amidon"), ("orge", "amidon"), ("avoine", "amidon"),
        ("châtaigne", "amidon"),
        ("tournesol", "lipide"), ("colza", "lipide"), ("arachide", "lipide"), ("lin", "lipide"),
        ("sésame", "lipide"), ("noix", "lipide"), ("noisette", "lipide"),
        ("soja", "protéine"), ("pois", "protéine"), ("lentille", "protéine"), ("fève", "protéine"),
        ("haricot", "protéine"), ("pois chiche", "protéine"),
    ]
    publie("type_reserve_graine", "convention",
           "Modèle (Claude) — agronomie textbook curée (réserve de graine ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("activite_circadienne_animal")
def ingere_activite_circadienne_animal():
    # SOURCE = LE MODÈLE. Animal -> rythme d'activité ; ENSEMBLE FERMÉ : diurne / nocturne. Textbook éthologie,
    # FAUX=0 (espèces au rythme NON ambigu ; les espèces crépusculaires/flexibles comme le chat/lion EXCLUES).
    paires = [
        ("hibou", "nocturne"), ("chouette", "nocturne"), ("chauve-souris", "nocturne"),
        ("hérisson", "nocturne"), ("rat", "nocturne"), ("luciole", "nocturne"), ("blaireau", "nocturne"),
        ("aigle royal", "diurne"), ("faucon pèlerin", "diurne"), ("abeille", "diurne"),
        ("écureuil", "diurne"), ("hirondelle", "diurne"), ("lézard", "diurne"),
        # — approfondissement run-autonome v2 —
        ("engoulevent", "nocturne"), ("loris", "nocturne"), ("opossum", "nocturne"),
        ("raton laveur", "nocturne"), ("civette", "nocturne"), ("ver luisant", "nocturne"),
        ("libellule", "diurne"), ("guêpe", "diurne"), ("marmotte", "diurne"), ("suricate", "diurne"),
        ("papillon de jour", "diurne"),
    ]
    publie("activite_circadienne_animal", "physique",
           "Modèle (Claude) — éthologie textbook curée (rythme diurne/nocturne ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("couleur_sang_animal")
def ingere_couleur_sang_animal():
    # SOURCE = LE MODÈLE. Animal -> couleur du sang/hémolymphe ; ENSEMBLE FERMÉ : rouge (hémoglobine au fer) /
    # bleu (hémocyanine au cuivre). Textbook physiologie, FAUX=0. Insectes (hémolymphe sans pigment) EXCLUS.
    paires = [
        ("être humain", "rouge"), ("lion", "rouge"), ("poisson", "rouge"), ("grenouille", "rouge"),
        ("aigle royal", "rouge"), ("ver de terre", "rouge"), ("sangsue", "rouge"),
        ("pieuvre", "bleu"), ("calmar", "bleu"), ("seiche", "bleu"), ("crabe", "bleu"),
        ("homard", "bleu"), ("crevette", "bleu"), ("escargot", "bleu"), ("limule", "bleu"),
    ]
    publie("couleur_sang_animal", "physique",
           "Modèle (Claude) — physiologie textbook curée (couleur du sang ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("domaine_vivant")
def ingere_domaine_vivant():
    # SOURCE = LE MODÈLE. Organisme -> domaine du vivant (classification de Woese) ; ENSEMBLE FERMÉ : bactérie /
    # archée / eucaryote. Textbook biologie, FAUX=0. Eucaryotes = à noyau (animaux/végétaux/champignons/protistes).
    paires = [
        ("Escherichia coli", "bactérie"), ("staphylocoque", "bactérie"), ("cyanobactérie", "bactérie"),
        ("salmonelle", "bactérie"), ("streptocoque", "bactérie"),
        ("méthanogène", "archée"), ("halobactérie", "archée"),
        ("être humain", "eucaryote"), ("levure de boulanger", "eucaryote"),
        ("champignon de Paris", "eucaryote"), ("amibe", "eucaryote"), ("paramécie", "eucaryote"),
        ("chêne", "eucaryote"), ("lion", "eucaryote"),
        # — approfondissement run-autonome (domaine certain) —
        ("Vibrio cholerae", "bactérie"), ("Helicobacter pylori", "bactérie"), ("Listeria", "bactérie"),
        ("Mycobacterium tuberculosis", "bactérie"), ("pneumocoque", "bactérie"),
        ("chien", "eucaryote"), ("rosier", "eucaryote"), ("blé", "eucaryote"), ("mouche", "eucaryote"),
        ("euglène", "eucaryote"), ("moisissure", "eucaryote"),
    ]
    publie("domaine_vivant", "physique",
           "Modèle (Claude) — biologie textbook curée (domaine de Woese ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_digestion_animal")
def ingere_type_digestion_animal():
    # SOURCE = LE MODÈLE. Mammifère -> type digestif ; ENSEMBLE FERMÉ : ruminant (estomac à 4 compartiments) /
    # monogastrique (estomac simple). Textbook physiologie animale, FAUX=0. Chameau (pseudo-ruminant) EXCLU.
    paires = [
        ("vache", "ruminant"), ("mouton", "ruminant"), ("chèvre", "ruminant"), ("girafe", "ruminant"),
        ("cerf", "ruminant"), ("bison", "ruminant"), ("gnou", "ruminant"), ("antilope", "ruminant"),
        ("être humain", "monogastrique"), ("chien", "monogastrique"), ("chat", "monogastrique"),
        ("cheval", "monogastrique"), ("cochon", "monogastrique"), ("lapin", "monogastrique"),
        ("rat", "monogastrique"), ("souris", "monogastrique"),
        # — approfondissement run-autonome (type digestif certain) —
        ("bison", "ruminant"), ("buffle", "ruminant"), ("renne", "ruminant"), ("élan", "ruminant"),
        ("bouquetin", "ruminant"), ("yack", "ruminant"),
        ("lion", "monogastrique"), ("tigre", "monogastrique"), ("ours brun", "monogastrique"),
        ("éléphant d'Afrique", "monogastrique"), ("loup", "monogastrique"),
    ]
    publie("type_digestion_animal", "physique",
           "Modèle (Claude) — physiologie animale textbook curée (ruminant/monogastrique ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_dentition_animal")
def ingere_type_dentition_animal():
    # SOURCE = LE MODÈLE. Animal -> type de dentition ; ENSEMBLE FERMÉ : hétérodonte (dents différenciées :
    # incisives/canines/molaires) / homodonte (dents toutes semblables). Textbook anatomie, FAUX=0. PIÈGE :
    # le DAUPHIN (cétacé à dents) est HOMODONTE malgré son statut de mammifère.
    paires = [
        ("être humain", "hétérodonte"), ("lion", "hétérodonte"), ("chien", "hétérodonte"),
        ("chat", "hétérodonte"), ("cheval", "hétérodonte"), ("vache", "hétérodonte"),
        ("éléphant d'Afrique", "hétérodonte"), ("sanglier", "hétérodonte"),
        ("crocodile du Nil", "homodonte"), ("requin", "homodonte"), ("dauphin", "homodonte"),
        ("lézard", "homodonte"), ("varan", "homodonte"),
        # — approfondissement run-autonome (dentition certaine) —
        ("souris", "hétérodonte"), ("rat", "hétérodonte"), ("lapin", "hétérodonte"),
        ("ours brun", "hétérodonte"), ("loup", "hétérodonte"), ("renard roux", "hétérodonte"),
        ("chauve-souris", "hétérodonte"), ("hippopotame", "hétérodonte"),
        ("serpent", "homodonte"), ("gecko", "homodonte"), ("iguane", "homodonte"),
        ("thon rouge", "homodonte"), ("python", "homodonte"),
        # — approfondissement run-autonome v3 —
        ("tigre", "hétérodonte"), ("ours brun", "hétérodonte"), ("phacochère", "hétérodonte"),
        ("morse", "hétérodonte"), ("hippopotame", "hétérodonte"),
        ("carpe", "homodonte"), ("perche", "homodonte"), ("brochet", "homodonte"),
        ("cachalot", "homodonte"), ("anguille", "homodonte"),
    ]
    publie("type_dentition_animal", "physique",
           "Modèle (Claude) — anatomie textbook curée (homodonte/hétérodonte ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("nombre_pattes_animal")
def ingere_nombre_pattes_animal():
    # SOURCE = LE MODÈLE. Animal -> nombre de pattes ; ENSEMBLE FERMÉ {0,2,4,6,8}. Textbook zoologie, FAUX=0.
    # Insectes = 6, arachnides = 8, tétrapodes terrestres = 4, oiseaux/humain = 2, serpents/vers = 0.
    paires = [
        ("serpent", "0"), ("ver de terre", "0"), ("escargot", "0"), ("limace", "0"),
        ("être humain", "2"), ("aigle royal", "2"), ("autruche", "2"), ("manchot empereur", "2"),
        ("pigeon", "2"), ("poule", "2"), ("moineau", "2"),
        ("lion", "4"), ("tigre", "4"), ("chien", "4"), ("chat", "4"), ("cheval", "4"), ("vache", "4"),
        ("éléphant d'Afrique", "4"), ("grenouille", "4"), ("lézard", "4"), ("crocodile du Nil", "4"),
        ("tortue marine", "4"), ("salamandre", "4"),
        ("abeille", "6"), ("fourmi", "6"), ("papillon", "6"), ("mouche", "6"), ("scarabée", "6"),
        ("criquet", "6"), ("libellule", "6"), ("moustique", "6"),
        ("araignée", "8"), ("scorpion", "8"), ("tique", "8"), ("acarien", "8"), ("mygale", "8"),
        # — approfondissement run-autonome (espèces univoques) —
        ("anguille", "0"), ("méduse", "0"), ("sangsue", "0"),
        ("tigre", "4"), ("éléphant d'Afrique", "4"), ("vache", "4"), ("mouton", "4"), ("cochon", "4"),
        ("ours brun", "4"), ("loup", "4"), ("renard roux", "4"), ("hippopotame", "4"), ("girafe", "4"),
        ("zèbre", "4"), ("cerf", "4"), ("lapin", "4"), ("rat", "4"), ("crocodile du Nil", "4"),
        ("salamandre", "4"), ("tortue marine", "4"), ("gecko", "4"), ("varan", "4"), ("iguane", "4"),
        ("guêpe", "6"), ("frelon", "6"), ("coccinelle", "6"), ("hanneton", "6"), ("cigale", "6"),
        ("termite", "6"), ("puceron", "6"), ("blatte", "6"), ("grillon", "6"), ("mante religieuse", "6"),
        ("perce-oreille", "6"),
        ("faucheux", "8"), ("tarentule", "8"),
        ("perroquet", "2"), ("corbeau", "2"), ("flamant rose", "2"),
        # — approfondissement run-autonome v2 (espèces univoques) —
        ("léopard", "4"), ("jaguar", "4"), ("guépard", "4"), ("hyène tachetée", "4"),
        ("rhinocéros blanc", "4"), ("chameau", "4"), ("koala", "4"), ("paresseux", "4"), ("tatou", "4"),
        ("termite", "6"), ("blatte", "6"), ("luciole", "6"), ("doryphore", "6"),
        ("opilion", "8"), ("pseudoscorpion", "8"),
        ("hibou", "2"), ("manchot empereur", "2"), ("cigogne", "2"),
        # — approfondissement run-autonome v3 —
        ("vache", "4"), ("mouton", "4"), ("chèvre", "4"), ("cochon", "4"), ("girafe", "4"),
        ("ours brun", "4"), ("loup", "4"), ("renard roux", "4"), ("hippopotame", "4"),
        ("guêpe", "6"), ("mouche", "6"), ("moustique", "6"), ("cigale", "6"),
        ("aigle royal", "2"), ("autruche", "2"), ("perroquet", "2"),
        ("ver de terre", "0"), ("sangsue", "0"), ("méduse", "0"),
    ]
    publie("nombre_pattes_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (nombre de pattes ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_oeil_animal")
def ingere_type_oeil_animal():
    # SOURCE = LE MODÈLE. Animal -> type d'œil ; ENSEMBLE FERMÉ : composé (à facettes : insectes/crustacés) /
    # simple (à cristallin unique : vertébrés/céphalopodes/arachnides). Textbook zoologie, FAUX=0.
    paires = [
        ("mouche", "composé"), ("abeille", "composé"), ("libellule", "composé"), ("papillon", "composé"),
        ("fourmi", "composé"), ("criquet", "composé"), ("crabe", "composé"), ("crevette", "composé"),
        ("homard", "composé"),
        ("lion", "simple"), ("aigle royal", "simple"), ("être humain", "simple"), ("poisson", "simple"),
        ("serpent", "simple"), ("pieuvre", "simple"), ("calmar", "simple"), ("araignée", "simple"),
        ("scorpion", "simple"),
        # — approfondissement run-autonome (type d'œil certain) —
        ("guêpe", "composé"), ("moustique", "composé"), ("coccinelle", "composé"), ("hanneton", "composé"),
        ("cigale", "composé"), ("écrevisse", "composé"), ("krill", "composé"),
        ("tigre", "simple"), ("chien", "simple"), ("chat", "simple"), ("cheval", "simple"),
        ("grenouille", "simple"), ("crocodile du Nil", "simple"), ("seiche", "simple"), ("escargot", "simple"),
        # — approfondissement run-autonome v2 (type d'œil certain) —
        ("frelon", "composé"), ("scarabée", "composé"), ("sauterelle", "composé"), ("papillon", "composé"),
        ("fourmi", "composé"),
        ("lézard", "simple"), ("tortue marine", "simple"), ("souris", "simple"), ("vache", "simple"),
        ("requin", "simple"),
    ]
    publie("type_oeil_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (œil composé/simple ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("nombre_ailes_insecte")
def ingere_nombre_ailes_insecte():
    # SOURCE = LE MODÈLE. Insecte ailé -> nombre d'ailes ; ENSEMBLE FERMÉ {2,4}. Textbook entomologie, FAUX=0.
    # Diptères (mouches/moustiques) = 2 ailes (les postérieures réduites en haltères) ; la plupart = 4.
    paires = [
        ("mouche", "2"), ("moustique", "2"), ("taon", "2"), ("syrphe", "2"), ("tipule", "2"),
        ("papillon", "4"), ("abeille", "4"), ("guêpe", "4"), ("frelon", "4"), ("libellule", "4"),
        ("coccinelle", "4"), ("hanneton", "4"), ("scarabée", "4"), ("criquet", "4"), ("cigale", "4"),
        ("sauterelle", "4"),
    ]
    publie("nombre_ailes_insecte", "physique",
           "Modèle (Claude) — entomologie textbook curée (nombre d'ailes ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_fleur_symetrie")
def ingere_type_fleur_symetrie():
    # SOURCE = LE MODÈLE. Plante -> symétrie florale ; ENSEMBLE FERMÉ : actinomorphe (régulière, radiaire) /
    # zygomorphe (irrégulière, 1 plan de symétrie). Textbook botanique, FAUX=0 (cas non ambigus).
    paires = [
        ("tulipe", "actinomorphe"), ("coquelicot", "actinomorphe"), ("géranium", "actinomorphe"),
        ("primevère", "actinomorphe"), ("renoncule", "actinomorphe"), ("églantine", "actinomorphe"),
        ("lis", "actinomorphe"),
        ("orchidée", "zygomorphe"), ("pois", "zygomorphe"), ("muflier", "zygomorphe"),
        ("sauge", "zygomorphe"), ("violette", "zygomorphe"), ("glycine", "zygomorphe"),
        ("genêt", "zygomorphe"), ("pensée", "zygomorphe"), ("lavande", "zygomorphe"),
    ]
    publie("type_fleur_symetrie", "physique",
           "Modèle (Claude) — botanique textbook curée (symétrie florale ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_coquille_mollusque")
def ingere_type_coquille_mollusque():
    # SOURCE = LE MODÈLE. Mollusque -> type de coquille ; ENSEMBLE FERMÉ : univalve / bivalve / coquille interne /
    # sans coquille. Textbook zoologie, FAUX=0. PIÈGE : seiche/calmar = coquille INTERNE ; limace/pieuvre = SANS.
    paires = [
        ("escargot", "univalve"), ("bigorneau", "univalve"), ("buccin", "univalve"), ("patelle", "univalve"),
        ("ormeau", "univalve"), ("conque", "univalve"), ("nautile", "univalve"), ("colimaçon", "univalve"),
        ("moule", "bivalve"), ("huître", "bivalve"), ("palourde", "bivalve"),
        ("coquille Saint-Jacques", "bivalve"), ("coque", "bivalve"), ("praire", "bivalve"),
        ("seiche", "coquille interne"), ("calmar", "coquille interne"),
        ("limace", "sans coquille"), ("pieuvre", "sans coquille"), ("nudibranche", "sans coquille"),
        # — approfondissement run-autonome v2 —
        ("planorbe", "univalve"), ("vignot", "univalve"), ("murex", "univalve"), ("bulot", "univalve"),
        ("clam", "bivalve"), ("couteau", "bivalve"), ("pétoncle", "bivalve"), ("anodonte", "bivalve"),
        ("calmar", "coquille interne"),
        ("aplysie", "sans coquille"),
        # — approfondissement run-autonome v3 —
        ("turritelle", "univalve"), ("porcelaine", "univalve"), ("cône", "univalve"), ("troque", "univalve"),
        ("moule zébrée", "bivalve"), ("lucine", "bivalve"), ("mye", "bivalve"),
        ("sépiole", "coquille interne"),
    ]
    publie("type_coquille_mollusque", "physique",
           "Modèle (Claude) — zoologie textbook curée (type de coquille ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_ecaille_poisson")
def ingere_type_ecaille_poisson():
    # SOURCE = LE MODÈLE. Poisson -> type d'écaille ; ENSEMBLE FERMÉ : placoïde (requins/raies) / cycloïde /
    # cténoïde / ganoïde (esturgeons). Textbook ichtyologie, FAUX=0.
    paires = [
        ("requin", "placoïde"), ("grand requin blanc", "placoïde"), ("raie manta", "placoïde"),
        ("roussette", "placoïde"),
        ("saumon atlantique", "cycloïde"), ("carpe", "cycloïde"), ("hareng", "cycloïde"),
        ("sardine", "cycloïde"), ("anguille", "cycloïde"),
        ("perche", "cténoïde"), ("bar", "cténoïde"), ("sole", "cténoïde"),
        ("esturgeon", "ganoïde"),
        # — approfondissement run-autonome v2 —
        ("gardon", "cycloïde"), ("brème", "cycloïde"), ("tanche", "cycloïde"), ("brochet", "cycloïde"),
        ("dorade", "cténoïde"), ("rouget", "cténoïde"), ("mérou", "cténoïde"),
        ("polyptère", "ganoïde"), ("lépisosté", "ganoïde"),
        ("pastenague", "placoïde"), ("torpille", "placoïde"),
    ]
    publie("type_ecaille_poisson", "physique",
           "Modèle (Claude) — ichtyologie textbook curée (type d'écaille ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_excretion_azotee")
def ingere_type_excretion_azotee():
    # SOURCE = LE MODÈLE. Animal -> déchet azoté principal ; ENSEMBLE FERMÉ : ammoniac (aquatiques) / urée
    # (mammifères, amphibiens) / acide urique (oiseaux, reptiles, insectes). Textbook physiologie, FAUX=0.
    paires = [
        ("poisson", "ammoniac"), ("carpe", "ammoniac"), ("têtard", "ammoniac"), ("thon rouge", "ammoniac"),
        ("être humain", "urée"), ("lion", "urée"), ("chien", "urée"), ("vache", "urée"),
        ("grenouille", "urée"), ("requin", "urée"), ("dauphin", "urée"),
        ("aigle royal", "acide urique"), ("pigeon", "acide urique"), ("serpent", "acide urique"),
        ("lézard", "acide urique"), ("crocodile du Nil", "acide urique"), ("criquet", "acide urique"),
        ("escargot", "acide urique"),
        # — approfondissement run-autonome v2 —
        ("sardine", "ammoniac"), ("hareng", "ammoniac"),
        ("mouton", "urée"), ("cheval", "urée"), ("éléphant d'Afrique", "urée"), ("baleine bleue", "urée"),
        ("poule", "acide urique"), ("autruche", "acide urique"), ("perroquet", "acide urique"),
        ("tortue marine", "acide urique"), ("gecko", "acide urique"), ("varan", "acide urique"),
    ]
    publie("type_excretion_azotee", "physique",
           "Modèle (Claude) — physiologie textbook curée (déchet azoté ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_appendice_cephalique")
def ingere_type_appendice_cephalique():
    # SOURCE = LE MODÈLE. Mammifère -> type d'appendice céphalique ; ENSEMBLE FERMÉ : bois (ramures osseuses
    # caduques) / corne (kératine, permanente) / défense (dent allongée). Textbook zoologie, FAUX=0. PIÈGE :
    # le cerf porte des BOIS (pas des cornes) ; le rhinocéros une CORNE ; l'éléphant des DÉFENSES (incisives).
    paires = [
        ("cerf", "bois"), ("élan", "bois"), ("renne", "bois"), ("chevreuil", "bois"), ("daim", "bois"),
        ("vache", "corne"), ("chèvre", "corne"), ("mouton", "corne"), ("bouquetin", "corne"),
        ("mouflon", "corne"), ("rhinocéros blanc", "corne"), ("antilope", "corne"), ("gnou", "corne"),
        ("buffle", "corne"), ("bison", "corne"),
        ("éléphant d'Afrique", "défense"), ("morse", "défense"), ("sanglier", "défense"),
        ("phacochère", "défense"), ("narval", "défense"),
        # — approfondissement run-autonome (appendice certain) —
        ("wapiti", "bois"), ("caribou", "bois"), ("cariacou", "bois"), ("orignal", "bois"),
        ("oryx", "corne"), ("addax", "corne"), ("springbok", "corne"), ("impala", "corne"),
        ("koudou", "corne"), ("isard", "corne"), ("chamois", "corne"), ("yack", "corne"),
        ("babiroussa", "défense"), ("hippopotame", "défense"),
    ]
    publie("type_appendice_cephalique", "physique",
           "Modèle (Claude) — zoologie textbook curée (bois/corne/défense ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("comportement_migrateur_oiseau")
def ingere_comportement_migrateur_oiseau():
    # SOURCE = LE MODÈLE. Oiseau -> comportement migratoire ; ENSEMBLE FERMÉ : migrateur / sédentaire. Textbook
    # ornithologie, FAUX=0 (espèces au comportement non ambigu ; migrateurs partiels EXCLUS).
    paires = [
        ("hirondelle", "migrateur"), ("cigogne", "migrateur"), ("grue", "migrateur"),
        ("martinet", "migrateur"), ("coucou", "migrateur"), ("oie cendrée", "migrateur"),
        ("rossignol", "migrateur"), ("sterne arctique", "migrateur"),
        ("moineau", "sédentaire"), ("pigeon", "sédentaire"), ("mésange", "sédentaire"),
        ("merle", "sédentaire"), ("pic vert", "sédentaire"), ("geai", "sédentaire"),
        ("corbeau", "sédentaire"), ("chouette", "sédentaire"),
        # — approfondissement run-autonome v2 —
        ("fauvette", "migrateur"), ("pouillot", "migrateur"), ("gobemouche", "migrateur"),
        ("loriot", "migrateur"), ("huppe", "migrateur"), ("bécasse", "migrateur"),
        ("grue cendrée", "migrateur"), ("oie sauvage", "migrateur"),
        ("troglodyte", "sédentaire"), ("sittelle", "sédentaire"), ("pic épeiche", "sédentaire"),
        ("buse", "sédentaire"), ("faisan", "sédentaire"), ("perdrix", "sédentaire"),
    ]
    publie("comportement_migrateur_oiseau", "physique",
           "Modèle (Claude) — ornithologie textbook curée (migrateur/sédentaire ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_vie_plante")
def ingere_mode_vie_plante():
    # SOURCE = LE MODÈLE. Plante -> cycle de vie ; ENSEMBLE FERMÉ : annuelle (1 an) / bisannuelle (2 ans) /
    # vivace (plusieurs années). Textbook botanique, FAUX=0 (cas non ambigus).
    paires = [
        ("blé", "annuelle"), ("maïs", "annuelle"), ("tournesol", "annuelle"), ("riz", "annuelle"),
        ("haricot", "annuelle"), ("tomate", "annuelle"), ("courgette", "annuelle"), ("coquelicot", "annuelle"),
        ("pois", "annuelle"),
        ("carotte", "bisannuelle"), ("betterave", "bisannuelle"), ("chou", "bisannuelle"),
        ("persil", "bisannuelle"), ("poireau", "bisannuelle"),
        ("chêne", "vivace"), ("hêtre", "vivace"), ("pin", "vivace"), ("rosier", "vivace"),
        ("menthe", "vivace"), ("lavande", "vivace"), ("pissenlit", "vivace"), ("fougère", "vivace"),
        ("tulipe", "vivace"), ("vigne", "vivace"), ("fraisier", "vivace"),
        # — approfondissement run-autonome v2 —
        ("orge", "annuelle"), ("avoine", "annuelle"), ("seigle", "annuelle"), ("lin", "annuelle"),
        ("soja", "annuelle"), ("lentille", "annuelle"), ("laitue", "annuelle"), ("radis", "annuelle"),
        ("épinard", "annuelle"), ("concombre", "annuelle"),
        ("oignon", "bisannuelle"), ("céleri", "bisannuelle"), ("fenouil", "bisannuelle"), ("digitale", "bisannuelle"),
        ("olivier", "vivace"), ("framboisier", "vivace"), ("asperge", "vivace"), ("artichaut", "vivace"),
        ("rhubarbe", "vivace"), ("iris", "vivace"), ("muguet", "vivace"), ("bambou", "vivace"),
    ]
    publie("mode_vie_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (cycle de vie ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_pollinisation_plante")
def ingere_mode_pollinisation_plante():
    # SOURCE = LE MODÈLE. Plante -> mode de pollinisation ; ENSEMBLE FERMÉ : anémogame (vent) / entomogame
    # (insectes). Textbook botanique, FAUX=0 (cas non ambigus ; graminées/arbres à chatons = vent ; plantes
    # à fleurs colorées/nectar = insectes).
    paires = [
        ("blé", "anémogame"), ("maïs", "anémogame"), ("orge", "anémogame"), ("seigle", "anémogame"),
        ("noisetier", "anémogame"), ("chêne", "anémogame"), ("bouleau", "anémogame"), ("peuplier", "anémogame"),
        ("tournesol", "entomogame"), ("colza", "entomogame"), ("pommier", "entomogame"),
        ("cerisier", "entomogame"), ("tilleul", "entomogame"), ("lavande", "entomogame"),
        ("trèfle", "entomogame"), ("coquelicot", "entomogame"), ("sauge", "entomogame"),
        # — approfondissement run-autonome (mode certain) —
        ("avoine", "anémogame"), ("seigle", "anémogame"), ("graminée", "anémogame"),
        ("charme", "anémogame"), ("frêne", "anémogame"), ("ortie", "anémogame"),
        ("pommier", "entomogame"), ("poirier", "entomogame"), ("framboisier", "entomogame"),
        ("thym", "entomogame"), ("romarin", "entomogame"), ("acacia", "entomogame"), ("bleuet", "entomogame"),
        # — approfondissement run-autonome v2 —
        ("platane", "anémogame"), ("cyprès", "anémogame"), ("if", "anémogame"), ("aulne", "anémogame"),
        ("pissenlit", "entomogame"), ("marguerite", "entomogame"), ("aubépine", "entomogame"),
        ("fraisier", "entomogame"), ("fève", "entomogame"), ("luzerne", "entomogame"),
        ("bourrache", "entomogame"), ("courgette", "entomogame"),
    ]
    publie("mode_pollinisation_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (pollinisation anémogame/entomogame ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("revetement_corps_animal")
def ingere_revetement_corps_animal():
    # SOURCE = LE MODÈLE. Animal -> revêtement du corps (tégument) ; ENSEMBLE FERMÉ : poils / plumes / écailles /
    # peau nue. Textbook zoologie, FAUX=0. Mammifères = poils, oiseaux = plumes, reptiles/poissons = écailles,
    # amphibiens = peau nue.
    paires = [
        ("lion", "poils"), ("chien", "poils"), ("chat", "poils"), ("souris", "poils"),
        ("éléphant d'Afrique", "poils"), ("chauve-souris", "poils"),
        ("aigle royal", "plumes"), ("moineau", "plumes"), ("manchot empereur", "plumes"),
        ("autruche", "plumes"), ("poule", "plumes"),
        ("serpent", "écailles"), ("lézard", "écailles"), ("crocodile du Nil", "écailles"),
        ("carpe", "écailles"), ("thon rouge", "écailles"),
        ("grenouille", "peau nue"), ("crapaud", "peau nue"), ("salamandre", "peau nue"),
        # — approfondissement run-autonome (tégument certain) —
        ("tigre", "poils"), ("loup", "poils"), ("ours brun", "poils"), ("cheval", "poils"),
        ("mouton", "poils"), ("hérisson", "poils"), ("écureuil", "poils"), ("renard roux", "poils"),
        ("hibou", "plumes"), ("perroquet", "plumes"), ("flamant rose", "plumes"), ("canard", "plumes"),
        ("pigeon", "plumes"), ("moineau", "plumes"),
        ("lézard", "écailles"), ("varan", "écailles"), ("tortue marine", "écailles"), ("python", "écailles"),
        ("saumon atlantique", "écailles"), ("sardine", "écailles"),
        ("triton", "peau nue"), ("axolotl", "peau nue"),
        # — approfondissement run-autonome v2 (tégument certain) —
        ("rhinocéros blanc", "poils"), ("zèbre", "poils"), ("girafe", "poils"), ("kangourou", "poils"),
        ("koala", "poils"), ("lapin", "poils"), ("hamster", "poils"), ("lion", "poils"),
        ("vautour", "plumes"), ("faucon pèlerin", "plumes"), ("mésange", "plumes"), ("cygne", "plumes"),
        ("oie", "plumes"), ("autruche", "plumes"),
        ("cobra royal", "écailles"), ("vipère", "écailles"), ("iguane", "écailles"), ("caméléon", "écailles"),
        ("crocodile du Nil", "écailles"), ("carpe", "écailles"),
        ("cécilie", "peau nue"), ("crapaud", "peau nue"),
    ]
    publie("revetement_corps_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (tégument ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("os_partie_squelette")
def ingere_os_partie_squelette():
    # SOURCE = LE MODÈLE. Os -> partie du squelette ; ENSEMBLE FERMÉ : axial (crâne/colonne/thorax) /
    # appendiculaire (membres + ceintures). Textbook anatomie, FAUX=0.
    paires = [
        ("crâne", "axial"), ("vertèbre", "axial"), ("côte", "axial"), ("sternum", "axial"),
        ("os hyoïde", "axial"), ("sacrum", "axial"), ("os occipital", "axial"), ("os frontal", "axial"),
        ("os pariétal", "axial"), ("os temporal", "axial"), ("mandibule", "axial"), ("coccyx", "axial"),
        ("humérus", "appendiculaire"), ("fémur", "appendiculaire"), ("tibia", "appendiculaire"),
        ("péroné", "appendiculaire"), ("radius", "appendiculaire"), ("cubitus", "appendiculaire"),
        ("omoplate", "appendiculaire"), ("clavicule", "appendiculaire"), ("os iliaque", "appendiculaire"),
        ("rotule", "appendiculaire"), ("métacarpien", "appendiculaire"), ("métatarsien", "appendiculaire"),
        ("phalange", "appendiculaire"),
        # — approfondissement run-autonome v3 —
        ("os sphénoïde", "axial"), ("os ethmoïde", "axial"), ("os nasal", "axial"), ("vomer", "axial"),
        ("os palatin", "axial"), ("os zygomatique", "axial"), ("os temporal", "axial"),
        ("scaphoïde", "appendiculaire"), ("calcanéus", "appendiculaire"), ("talus", "appendiculaire"),
        ("pubis", "appendiculaire"), ("ischion", "appendiculaire"), ("ilion", "appendiculaire"),
        ("cuboïde", "appendiculaire"),
    ]
    publie("os_partie_squelette", "physique",
           "Modèle (Claude) — anatomie textbook curée (squelette axial/appendiculaire ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("medecin_specialiste_organe")
def ingere_medecin_specialiste_organe():
    # SOURCE = LE MODÈLE. Organe/système -> médecin spécialiste. Textbook médecine, FAUX=0 ; fonctionnel
    # (spécialité de référence non contestée).
    paires = [
        ("cœur", "cardiologue"), ("peau", "dermatologue"), ("œil", "ophtalmologue"),
        ("rein", "néphrologue"), ("poumon", "pneumologue"), ("système nerveux", "neurologue"),
        ("appareil digestif", "gastro-entérologue"), ("dent", "dentiste"), ("sang", "hématologue"),
        ("appareil urinaire", "urologue"), ("glande endocrine", "endocrinologue"),
        ("oreille", "oto-rhino-laryngologiste"), ("articulation", "rhumatologue"),
        ("cerveau", "neurologue"), ("estomac", "gastro-entérologue"), ("foie", "hépatologue"),
        # — approfondissement run-autonome (spécialiste de référence) —
        ("appareil génital féminin", "gynécologue"), ("enfant", "pédiatre"),
        ("personne âgée", "gériatre"), ("cancer", "oncologue"), ("pied", "podologue"),
        ("veine", "phlébologue"), ("système immunitaire", "immunologue"), ("nez", "oto-rhino-laryngologiste"),
        ("vaisseau sanguin", "angiologue"),
        # — approfondissement run-autonome v3 —
        ("rectum", "proctologue"), ("sein", "sénologue"), ("grossesse", "obstétricien"),
        ("articulations", "rhumatologue"), ("appareil respiratoire", "pneumologue"),
        ("appareil locomoteur", "orthopédiste"), ("anus", "proctologue"),
    ]
    publie("medecin_specialiste_organe", "convention",
           "Modèle (Claude) — médecine textbook curée (organe -> spécialiste ; fonctionnel ; FAUX=0 vérifié)", paires)


@domaine("feuillage_arbre")
def ingere_feuillage_arbre():
    # SOURCE = LE MODÈLE. Arbre -> persistance du feuillage ; ENSEMBLE FERMÉ : caduc (perd ses feuilles) /
    # persistant. Textbook botanique, FAUX=0. Info INDÉPENDANTE de feuillu/conifère : le MÉLÈZE est un conifère
    # CADUC ; le HOUX est un feuillu PERSISTANT.
    paires = [
        ("chêne", "caduc"), ("hêtre", "caduc"), ("bouleau", "caduc"), ("érable", "caduc"),
        ("tilleul", "caduc"), ("peuplier", "caduc"), ("marronnier", "caduc"), ("frêne", "caduc"),
        ("charme", "caduc"), ("mélèze", "caduc"), ("platane", "caduc"), ("noyer", "caduc"),
        ("pin", "persistant"), ("sapin", "persistant"), ("épicéa", "persistant"), ("cèdre", "persistant"),
        ("if", "persistant"), ("houx", "persistant"), ("laurier", "persistant"), ("olivier", "persistant"),
        ("cyprès", "persistant"), ("buis", "persistant"),
    ]
    publie("feuillage_arbre", "physique",
           "Modèle (Claude) — botanique textbook curée (feuillage caduc/persistant ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("port_plante")
def ingere_port_plante():
    # SOURCE = LE MODÈLE. Plante -> port (forme de croissance) ; ENSEMBLE FERMÉ : arbre / arbuste / herbacée /
    # liane. Textbook botanique, FAUX=0 (exemples au port non ambigu).
    paires = [
        ("chêne", "arbre"), ("hêtre", "arbre"), ("pin", "arbre"), ("sapin", "arbre"), ("érable", "arbre"),
        ("platane", "arbre"), ("peuplier", "arbre"), ("olivier", "arbre"), ("pommier", "arbre"),
        ("cerisier", "arbre"),
        ("rosier", "arbuste"), ("lavande", "arbuste"), ("buis", "arbuste"), ("houx", "arbuste"),
        ("lilas", "arbuste"), ("groseillier", "arbuste"), ("romarin", "arbuste"),
        ("blé", "herbacée"), ("maïs", "herbacée"), ("tournesol", "herbacée"), ("pissenlit", "herbacée"),
        ("tulipe", "herbacée"), ("menthe", "herbacée"), ("ortie", "herbacée"), ("marguerite", "herbacée"),
        ("vigne", "liane"), ("lierre", "liane"), ("glycine", "liane"), ("liseron", "liane"),
        ("clématite", "liane"),
        # — approfondissement run-autonome (port certain) —
        ("tilleul", "arbre"), ("frêne", "arbre"), ("marronnier", "arbre"), ("noyer", "arbre"),
        ("séquoia", "arbre"), ("châtaignier", "arbre"), ("charme", "arbre"), ("saule", "arbre"),
        ("noisetier", "arbuste"), ("sureau", "arbuste"), ("aubépine", "arbuste"), ("genêt", "arbuste"),
        ("bruyère", "arbuste"), ("groseillier", "arbuste"), ("forsythia", "arbuste"),
        ("trèfle", "herbacée"), ("luzerne", "herbacée"), ("avoine", "herbacée"), ("orge", "herbacée"),
        ("pâquerette", "herbacée"), ("bouton d'or", "herbacée"), ("plantain", "herbacée"),
        ("chèvrefeuille", "liane"), ("passiflore", "liane"), ("vigne vierge", "liane"),
    ]
    publie("port_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (port végétal ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("classe_poisson")
def ingere_classe_poisson():
    # SOURCE = LE MODÈLE. Poisson -> grand groupe ; ENSEMBLE FERMÉ : cartilagineux (chondrichtyens : requins/
    # raies) / osseux (ostéichtyens : la plupart) / agnathe (sans mâchoire : lamproie). Textbook ichtyologie, FAUX=0.
    paires = [
        ("requin", "cartilagineux"), ("grand requin blanc", "cartilagineux"),
        ("requin-marteau", "cartilagineux"), ("raie manta", "cartilagineux"), ("roussette", "cartilagineux"),
        ("thon rouge", "osseux"), ("saumon atlantique", "osseux"), ("carpe", "osseux"), ("morue", "osseux"),
        ("sardine", "osseux"), ("hareng", "osseux"), ("truite", "osseux"), ("perche", "osseux"),
        ("anguille", "osseux"), ("hippocampe", "osseux"), ("brochet", "osseux"), ("espadon", "osseux"),
        ("maquereau", "osseux"), ("murène", "osseux"), ("mérou", "osseux"), ("esturgeon", "osseux"),
        ("lamproie", "agnathe"),
        # — approfondissement run-autonome (espèces univoques) —
        ("anchois", "osseux"), ("sole", "osseux"), ("turbot", "osseux"), ("bar", "osseux"),
        ("dorade", "osseux"), ("rouget", "osseux"), ("merlu", "osseux"), ("flétan", "osseux"),
        ("lotte", "osseux"), ("poisson-clown", "osseux"), ("colin", "osseux"),
        ("aiguillat", "cartilagineux"), ("requin-baleine", "cartilagineux"), ("requin-tigre", "cartilagineux"),
        ("raie", "cartilagineux"), ("myxine", "agnathe"),
        # — approfondissement run-autonome (espèces univoques) —
        ("gardon", "osseux"), ("brème", "osseux"), ("tanche", "osseux"), ("silure", "osseux"),
        ("congre", "osseux"), ("bar", "osseux"), ("dorade", "osseux"), ("turbot", "osseux"),
        ("pastenague", "cartilagineux"), ("torpille", "cartilagineux"), ("chimère", "cartilagineux"),
        # — approfondissement run-autonome v3 —
        ("vivaneau", "osseux"), ("lieu noir", "osseux"), ("baudroie", "osseux"), ("poisson-lune", "osseux"),
        ("lompe", "osseux"), ("capelan", "osseux"), ("rascasse", "osseux"),
        ("requin-pèlerin", "cartilagineux"), ("requin-bouledogue", "cartilagineux"), ("ange de mer", "cartilagineux"),
    ]
    publie("classe_poisson", "physique",
           "Modèle (Claude) — ichtyologie textbook curée (groupe de poisson ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("ordre_amphibien")
def ingere_ordre_amphibien():
    # SOURCE = LE MODÈLE. Amphibien -> ordre ; ENSEMBLE FERMÉ : anoure (sans queue : grenouilles/crapauds) /
    # urodèle (avec queue : salamandres/tritons) / apode (sans pattes : cécilies). Textbook herpétologie, FAUX=0.
    paires = [
        ("grenouille", "anoure"), ("grenouille rousse", "anoure"), ("grenouille verte", "anoure"),
        ("crapaud", "anoure"), ("rainette", "anoure"),
        ("salamandre", "urodèle"), ("triton", "urodèle"), ("axolotl", "urodèle"),
        ("protée", "urodèle"), ("salamandre tachetée", "urodèle"),
        ("cécilie", "apode"),
        # — approfondissement run-autonome (ordre certain) —
        ("crapaud commun", "anoure"), ("pélobate", "anoure"), ("sonneur", "anoure"),
        ("grenouille taureau", "anoure"),
        ("nécture", "urodèle"), ("sirène", "urodèle"), ("salamandre géante", "urodèle"),
        ("gymnophione", "apode"),
    ]
    publie("ordre_amphibien", "physique",
           "Modèle (Claude) — herpétologie textbook curée (ordre d'amphibien ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("ordre_oiseau")
def ingere_ordre_oiseau():
    # SOURCE = LE MODÈLE. Oiseau -> ordre taxinomique (vue moderne) ; ENSEMBLE FERMÉ des grands ordres.
    # Textbook ornithologie, FAUX=0. Exemples univoques uniquement.
    paires = [
        ("aigle royal", "accipitriforme"), ("vautour", "accipitriforme"), ("buse", "accipitriforme"),
        ("milan", "accipitriforme"),
        ("faucon pèlerin", "falconiforme"),
        ("hibou", "strigiforme"), ("chouette", "strigiforme"),
        ("moineau", "passériforme"), ("mésange", "passériforme"), ("hirondelle", "passériforme"),
        ("corbeau", "passériforme"), ("merle", "passériforme"), ("pinson", "passériforme"),
        ("rouge-gorge", "passériforme"), ("étourneau", "passériforme"),
        ("canard", "ansériforme"), ("oie", "ansériforme"), ("cygne", "ansériforme"),
        ("poule", "galliforme"), ("dinde", "galliforme"), ("faisan", "galliforme"),
        ("perdrix", "galliforme"), ("caille", "galliforme"), ("paon", "galliforme"),
        ("manchot empereur", "sphénisciforme"),
        ("autruche", "struthioniforme"),
        ("perroquet", "psittaciforme"),
        ("pigeon", "columbiforme"),
        ("flamant rose", "phœnicoptériforme"),
        ("pic", "piciforme"), ("toucan", "piciforme"),
        ("martinet", "apodiforme"), ("colibri", "apodiforme"),
        # — approfondissement run-autonome (espèces univoques) —
        ("rossignol", "passériforme"), ("fauvette", "passériforme"), ("alouette", "passériforme"),
        ("geai", "passériforme"), ("pie", "passériforme"), ("grive", "passériforme"),
        ("mésange bleue", "passériforme"),
        ("épervier", "accipitriforme"), ("busard", "accipitriforme"), ("gypaète", "accipitriforme"),
        ("crécerelle", "falconiforme"),
        ("grand-duc", "strigiforme"), ("effraie", "strigiforme"),
        ("sarcelle", "ansériforme"), ("eider", "ansériforme"),
        ("pintade", "galliforme"), ("tétras", "galliforme"), ("gélinotte", "galliforme"),
        ("tourterelle", "columbiforme"),
        ("ara", "psittaciforme"), ("perruche", "psittaciforme"),
        # — approfondissement run-autonome (espèces + ordres univoques) —
        ("bouvreuil", "passériforme"), ("chardonneret", "passériforme"), ("troglodyte", "passériforme"),
        ("bergeronnette", "passériforme"), ("pinson", "passériforme"),
        ("autour", "accipitriforme"), ("circaète", "accipitriforme"),
        ("colombe", "columbiforme"),
        ("pélican", "pélécaniforme"), ("héron", "pélécaniforme"),
        ("cigogne", "ciconiiforme"), ("grue", "gruiforme"), ("foulque", "gruiforme"),
        # — approfondissement run-autonome v3 —
        ("grimpereau", "passériforme"), ("bruant", "passériforme"), ("serin", "passériforme"),
        ("verdier", "passériforme"), ("roitelet", "passériforme"),
        ("balbuzard", "accipitriforme"), ("bondrée", "accipitriforme"),
        ("harle", "ansériforme"), ("tadorne", "ansériforme"),
        ("goéland", "charadriiforme"), ("sterne", "charadriiforme"), ("mouette", "charadriiforme"),
        ("courlis", "charadriiforme"), ("avocette", "charadriiforme"),
        ("albatros", "procellariiforme"), ("pétrel", "procellariiforme"),
    ]
    publie("ordre_oiseau", "physique",
           "Modèle (Claude) — ornithologie textbook curée (ordre d'oiseau ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("ordre_reptile")
def ingere_ordre_reptile():
    # SOURCE = LE MODÈLE. Reptile -> ordre taxinomique ; ENSEMBLE FERMÉ : squamate (serpents+lézards) /
    # chélonien (tortues) / crocodilien. Textbook herpétologie, FAUX=0.
    paires = [
        ("serpent", "squamate"), ("lézard", "squamate"), ("gecko", "squamate"), ("varan", "squamate"),
        ("iguane", "squamate"), ("caméléon", "squamate"), ("cobra royal", "squamate"),
        ("vipère", "squamate"), ("python", "squamate"), ("boa", "squamate"),
        ("tortue marine", "chélonien"), ("tortue terrestre", "chélonien"),
        ("crocodile du Nil", "crocodilien"), ("alligator", "crocodilien"), ("gavial", "crocodilien"),
        ("caïman", "crocodilien"),
        # — approfondissement run-autonome (espèces univoques) —
        ("couleuvre", "squamate"), ("mamba", "squamate"), ("crotale", "squamate"), ("orvet", "squamate"),
        ("anaconda", "squamate"), ("scinque", "squamate"), ("varan de Komodo", "squamate"),
        ("tortue d'Hermann", "chélonien"), ("tortue luth", "chélonien"), ("cistude", "chélonien"),
        # — approfondissement run-autonome v2 (espèces univoques) —
        ("anolis", "squamate"), ("dragon barbu", "squamate"), ("tarente", "squamate"),
        ("basilic", "squamate"), ("agame", "squamate"),
        ("émyde", "chélonien"), ("trionyx", "chélonien"),
        # — approfondissement run-autonome v3 —
        ("héloderme", "squamate"), ("lézard vert", "squamate"), ("lézard des murailles", "squamate"),
        ("seps", "squamate"), ("orvet", "squamate"),
        ("tortue grecque", "chélonien"), ("tortue géante", "chélonien"), ("caouanne", "chélonien"),
        ("matamata", "chélonien"),
        ("faux-gavial", "crocodilien"),
    ]
    publie("ordre_reptile", "physique",
           "Modèle (Claude) — herpétologie textbook curée (ordre de reptile ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("ordre_mammifere")
def ingere_ordre_mammifere():
    # SOURCE = LE MODÈLE. Mammifère -> ordre taxinomique (vue classique) ; ENSEMBLE FERMÉ des grands ordres.
    # Textbook zoologie, FAUX=0. Pièges : baleine/dauphin = CÉTACÉS, chauve-souris = CHIROPTÈRES, lapin =
    # LAGOMORPHE (pas rongeur). Groupes à statut d'ordre ambigu (marsupiaux/insectivores) EXCLUS.
    paires = [
        ("lion", "carnivore"), ("tigre", "carnivore"), ("loup", "carnivore"), ("ours brun", "carnivore"),
        ("chat", "carnivore"), ("chien", "carnivore"), ("phoque", "carnivore"),
        ("hyène tachetée", "carnivore"), ("loutre", "carnivore"), ("renard roux", "carnivore"),
        ("léopard", "carnivore"), ("guépard", "carnivore"),
        ("être humain", "primate"), ("chimpanzé", "primate"), ("gorille", "primate"),
        ("orang-outan", "primate"), ("babouin", "primate"),
        ("souris", "rongeur"), ("rat", "rongeur"), ("écureuil", "rongeur"), ("castor", "rongeur"),
        ("hamster", "rongeur"), ("marmotte", "rongeur"), ("cobaye", "rongeur"),
        ("baleine bleue", "cétacé"), ("dauphin", "cétacé"), ("orque", "cétacé"), ("cachalot", "cétacé"),
        ("chauve-souris", "chiroptère"),
        ("éléphant d'Afrique", "proboscidien"),
        ("lapin", "lagomorphe"), ("lièvre", "lagomorphe"),
        ("cheval", "périssodactyle"), ("âne", "périssodactyle"), ("zèbre", "périssodactyle"),
        ("rhinocéros blanc", "périssodactyle"), ("tapir", "périssodactyle"),
        ("vache", "artiodactyle"), ("mouton", "artiodactyle"), ("chèvre", "artiodactyle"),
        ("cochon", "artiodactyle"), ("girafe", "artiodactyle"), ("hippopotame", "artiodactyle"),
        ("chameau", "artiodactyle"), ("cerf", "artiodactyle"),
        # — approfondissement run-autonome (espèces univoques) —
        ("belette", "carnivore"), ("hermine", "carnivore"), ("furet", "carnivore"),
        ("raton laveur", "carnivore"), ("ours polaire", "carnivore"), ("otarie", "carnivore"),
        ("fouine", "carnivore"), ("putois", "carnivore"), ("mangouste", "carnivore"),
        ("ouistiti", "primate"), ("macaque", "primate"), ("gibbon", "primate"), ("mandrill", "primate"),
        ("gerbille", "rongeur"), ("ragondin", "rongeur"), ("porc-épic", "rongeur"),
        ("chinchilla", "rongeur"), ("campagnol", "rongeur"),
        ("marsouin", "cétacé"), ("béluga", "cétacé"), ("narval", "cétacé"), ("baleine à bosse", "cétacé"),
        ("bouquetin", "artiodactyle"), ("chamois", "artiodactyle"), ("buffle", "artiodactyle"),
        ("renne", "artiodactyle"), ("élan", "artiodactyle"), ("okapi", "artiodactyle"),
        ("lama", "artiodactyle"), ("alpaga", "artiodactyle"), ("dromadaire", "artiodactyle"),
        ("bison", "artiodactyle"),
        ("éléphant d'Asie", "proboscidien"),
        # — approfondissement run-autonome v2 (espèces univoques) —
        ("glouton", "carnivore"), ("blaireau", "carnivore"), ("genette", "carnivore"),
        ("lémur", "primate"), ("capucin", "primate"), ("tarsier", "primate"),
        ("lemming", "rongeur"), ("agouti", "rongeur"), ("écureuil volant", "rongeur"),
        ("rorqual", "cétacé"), ("baleine franche", "cétacé"),
        ("roussette", "chiroptère"), ("pipistrelle", "chiroptère"),
        ("pécari", "artiodactyle"), ("springbok", "artiodactyle"), ("oryx", "artiodactyle"),
        ("impala", "artiodactyle"), ("koudou", "artiodactyle"), ("addax", "artiodactyle"),
        # — approfondissement run-autonome v3 —
        ("suricate", "carnivore"), ("ratel", "carnivore"), ("panda roux", "carnivore"), ("civette", "carnivore"),
        ("aye-aye", "primate"), ("galago", "primate"), ("tamarin", "primate"),
        ("gerboise", "rongeur"), ("loir", "rongeur"), ("ondatra", "rongeur"),
        ("gazelle", "artiodactyle"), ("mouflon", "artiodactyle"),
        ("vampire", "chiroptère"), ("noctule", "chiroptère"),
    ]
    publie("ordre_mammifere", "physique",
           "Modèle (Claude) — zoologie textbook curée (ordre de mammifère ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("ordre_insecte")
def ingere_ordre_insecte():
    # SOURCE = LE MODÈLE. Insecte -> ordre taxinomique ; ENSEMBLE FERMÉ des grands ordres. Textbook entomologie,
    # FAUX=0. Ordres formels univoques ; groupes à statut débattu (isoptères/phasmoptères) EXCLUS.
    paires = [
        ("papillon", "lépidoptère"),
        ("scarabée", "coléoptère"), ("coccinelle", "coléoptère"), ("hanneton", "coléoptère"),
        ("charançon", "coléoptère"), ("doryphore", "coléoptère"), ("lucane", "coléoptère"),
        ("mouche", "diptère"), ("moustique", "diptère"), ("taon", "diptère"),
        ("abeille", "hyménoptère"), ("fourmi", "hyménoptère"), ("guêpe", "hyménoptère"),
        ("frelon", "hyménoptère"), ("bourdon", "hyménoptère"),
        ("libellule", "odonate"),
        ("sauterelle", "orthoptère"), ("criquet", "orthoptère"), ("grillon", "orthoptère"),
        ("punaise", "hémiptère"), ("cigale", "hémiptère"), ("puceron", "hémiptère"),
        # — approfondissement run-autonome (espèces univoques) —
        ("luciole", "coléoptère"), ("bousier", "coléoptère"), ("carabe", "coléoptère"),
        ("ténébrion", "coléoptère"),
        ("mite", "lépidoptère"), ("sphinx", "lépidoptère"),
        ("syrphe", "diptère"), ("tipule", "diptère"),
        ("bourdon", "hyménoptère"), ("ichneumon", "hyménoptère"),
        ("cochenille", "hémiptère"),
        ("courtilière", "orthoptère"),
        # — approfondissement run-autonome v2 (espèces univoques) —
        ("cétoine", "coléoptère"), ("capricorne", "coléoptère"), ("dytique", "coléoptère"),
        ("machaon", "lépidoptère"), ("paon-du-jour", "lépidoptère"), ("bombyx", "lépidoptère"),
        ("abeille charpentière", "hyménoptère"),
        ("gendarme", "hémiptère"), ("notonecte", "hémiptère"),
        ("agrion", "odonate"), ("dectique", "orthoptère"), ("bombyle", "diptère"),
        # — approfondissement run-autonome v3 —
        ("staphylin", "coléoptère"), ("scolyte", "coléoptère"), ("vrillette", "coléoptère"),
        ("drosophile", "diptère"), ("œstre", "diptère"),
        ("piéride", "lépidoptère"), ("vulcain", "lépidoptère"), ("processionnaire", "lépidoptère"),
        ("cynips", "hyménoptère"), ("tenthrède", "hyménoptère"), ("xylocope", "hyménoptère"),
        ("gerris", "hémiptère"), ("nèpe", "hémiptère"),
        ("aeschne", "odonate"), ("sympétrum", "odonate"),
    ]
    publie("ordre_insecte", "physique",
           "Modèle (Claude) — entomologie textbook curée (ordre d'insecte ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_germination_graine")
def ingere_mode_germination_graine():
    # SOURCE = LE MODÈLE. Plante -> mode de germination ; ENSEMBLE FERMÉ : épigée (cotylédons sortent de terre)
    # / hypogée (cotylédons restent sous terre). Textbook botanique, FAUX=0 (exemples classiques).
    paires = [
        ("haricot", "épigée"), ("ricin", "épigée"), ("courge", "épigée"), ("courgette", "épigée"),
        ("tournesol", "épigée"), ("radis", "épigée"), ("hêtre", "épigée"),
        ("pois", "hypogée"), ("fève", "hypogée"), ("maïs", "hypogée"), ("chêne", "hypogée"),
        ("pois chiche", "hypogée"), ("châtaigne", "hypogée"), ("blé", "hypogée"),
        # — approfondissement run-autonome (germination certaine) —
        ("tomate", "épigée"), ("lin", "épigée"), ("moutarde", "épigée"), ("cresson", "épigée"),
        ("concombre", "épigée"), ("laitue", "épigée"),
        ("noisette", "hypogée"), ("lentille", "hypogée"), ("vesce", "hypogée"),
    ]
    publie("mode_germination_graine", "physique",
           "Modèle (Claude) — botanique textbook curée (germination épigée/hypogée ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("mode_vie_champignon")
def ingere_mode_vie_champignon():
    # SOURCE = LE MODÈLE. Champignon -> mode de vie ; ENSEMBLE FERMÉ : saprophyte (matière morte) / parasite
    # (sur hôte vivant) / symbiotique (mycorhize). Textbook mycologie, FAUX=0 (exemples canoniques).
    paires = [
        ("champignon de Paris", "saprophyte"), ("levure de boulanger", "saprophyte"),
        ("moisissure", "saprophyte"), ("coprin", "saprophyte"), ("pleurote", "saprophyte"),
        ("pénicillium", "saprophyte"),
        ("charbon des céréales", "parasite"), ("rouille", "parasite"), ("oïdium", "parasite"),
        ("ergot du seigle", "parasite"),
        ("bolet", "symbiotique"), ("cèpe", "symbiotique"), ("girolle", "symbiotique"),
        ("amanite tue-mouches", "symbiotique"), ("truffe", "symbiotique"), ("russule", "symbiotique"),
        ("lactaire", "symbiotique"),
        # — approfondissement run-autonome (mode de vie certain) —
        ("rosé des prés", "saprophyte"), ("agaric", "saprophyte"), ("coprin chevelu", "saprophyte"),
        ("fusariose", "parasite"), ("anthracnose", "parasite"), ("fumagine", "parasite"),
        ("chanterelle", "symbiotique"), ("pied-de-mouton", "symbiotique"), ("cortinaire", "symbiotique"),
    ]
    publie("mode_vie_champignon", "physique",
           "Modèle (Claude) — mycologie textbook curée (mode de vie ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_genome_virus")
def ingere_type_genome_virus():
    # SOURCE = LE MODÈLE. Virus -> nature de son génome ; ENSEMBLE FERMÉ : ADN / ARN. Textbook virologie,
    # FAUX=0 (base de la classification de Baltimore ; exemples non contestés).
    paires = [
        ("virus de la grippe", "ARN"), ("virus de l'immunodéficience humaine", "ARN"),
        ("virus de la rage", "ARN"), ("poliovirus", "ARN"), ("virus Ebola", "ARN"),
        ("virus de la rougeole", "ARN"), ("virus de l'hépatite C", "ARN"), ("virus de la dengue", "ARN"),
        ("SARS-CoV-2", "ARN"), ("virus de la fièvre jaune", "ARN"), ("rotavirus", "ARN"),
        ("virus chikungunya", "ARN"),
        ("virus de la variole", "ADN"), ("virus herpes simplex", "ADN"), ("virus de l'hépatite B", "ADN"),
        ("papillomavirus humain", "ADN"), ("adénovirus", "ADN"), ("virus d'Epstein-Barr", "ADN"),
        ("virus varicelle-zona", "ADN"), ("virus de la variole du singe", "ADN"), ("cytomégalovirus", "ADN"),
        # — approfondissement run-autonome (génome certain) —
        ("virus de l'hépatite A", "ARN"), ("virus de l'hépatite E", "ARN"), ("norovirus", "ARN"),
        ("virus ourlien", "ARN"), ("virus de la rubéole", "ARN"), ("virus Zika", "ARN"),
        ("virus respiratoire syncytial", "ARN"), ("virus du Nil occidental", "ARN"), ("virus de Marburg", "ARN"),
        ("parvovirus B19", "ADN"), ("virus du molluscum contagiosum", "ADN"),
        # — approfondissement run-autonome (génome certain) —
        ("rhinovirus", "ARN"), ("virus de la fièvre aphteuse", "ARN"),
        ("virus de la mosaïque du tabac", "ARN"), ("coronavirus", "ARN"), ("virus de l'hépatite delta", "ARN"),
        ("virus de la peste porcine", "ARN"),
        ("baculovirus", "ADN"), ("virus de la mosaïque du chou-fleur", "ADN"),
        # — approfondissement run-autonome v2 —
        ("virus Nipah", "ARN"), ("virus de la stomatite vésiculeuse", "ARN"), ("arénavirus", "ARN"),
        ("virus de la rougeole", "ARN"), ("virus de la vaccine", "ADN"), ("herpèsvirus B", "ADN"),
    ]
    publie("type_genome_virus", "physique",
           "Modèle (Claude) — virologie textbook curée (génome ADN/ARN ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_aliment_origine")
def ingere_type_aliment_origine():
    # SOURCE = LE MODÈLE. Aliment -> origine ; ENSEMBLE FERMÉ : animale / végétale / minérale. Textbook
    # nutrition, FAUX=0 (aliments de base non transformés à origine non ambiguë).
    paires = [
        ("viande", "animale"), ("poisson", "animale"), ("lait", "animale"), ("fromage", "animale"),
        ("yaourt", "animale"), ("œuf", "animale"), ("beurre", "animale"), ("miel", "animale"),
        ("bœuf", "animale"), ("poulet", "animale"), ("crevette", "animale"),
        ("pain", "végétale"), ("riz", "végétale"), ("blé", "végétale"), ("maïs", "végétale"),
        ("pomme", "végétale"), ("carotte", "végétale"), ("huile d'olive", "végétale"),
        ("haricot", "végétale"), ("lentille", "végétale"), ("café", "végétale"), ("sucre", "végétale"),
        ("sel", "minérale"), ("eau", "minérale"),
        # — approfondissement run-autonome v2 (origine certaine) —
        ("agneau", "animale"), ("veau", "animale"), ("dinde", "animale"), ("jambon", "animale"),
        ("huître", "animale"), ("moule", "animale"), ("crevette", "animale"),
        ("orge", "végétale"), ("avoine", "végétale"), ("soja", "végétale"), ("lentille", "végétale"),
        ("olive", "végétale"), ("noix", "végétale"), ("amande", "végétale"), ("chocolat", "végétale"),
        ("bicarbonate de soude", "minérale"),
    ]
    publie("type_aliment_origine", "convention",
           "Modèle (Claude) — nutrition textbook curée (origine de l'aliment ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_chromosome_humain")
def ingere_type_chromosome_humain():
    # SOURCE = LE MODÈLE. Chromosome humain -> type ; ENSEMBLE FERMÉ : autosome (paires 1-22) / gonosome
    # (chromosomes sexuels X, Y). Textbook génétique, FAUX=0 (caryotype humain standard).
    paires = [(f"chromosome {i}", "autosome") for i in range(1, 23)]
    paires += [("chromosome X", "gonosome"), ("chromosome Y", "gonosome")]
    publie("type_chromosome_humain", "physique",
           "Modèle (Claude) — génétique textbook curée (autosome/gonosome ; caryotype humain ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_lipide_classe")
def ingere_type_lipide_classe():
    # SOURCE = LE MODÈLE. Lipide -> classe biochimique ; ENSEMBLE FERMÉ : glycéride / phospholipide /
    # sphingolipide / stérol / cire. Textbook biochimie, FAUX=0 (exemples canoniques).
    paires = [
        ("triglycéride", "glycéride"),
        ("lécithine", "phospholipide"), ("phosphatidylcholine", "phospholipide"),
        ("sphingomyéline", "sphingolipide"), ("cérébroside", "sphingolipide"),
        ("cholestérol", "stérol"),
        ("cire d'abeille", "cire"),
        # — approfondissement run-autonome (classe certaine) —
        ("monoglycéride", "glycéride"), ("diglycéride", "glycéride"),
        ("phosphatidylsérine", "phospholipide"), ("cardiolipine", "phospholipide"),
        ("ganglioside", "sphingolipide"),
        ("ergostérol", "stérol"), ("phytostérol", "stérol"),
        ("cire de carnauba", "cire"), ("lanoline", "cire"),
        # — approfondissement run-autonome v2 —
        ("phosphatidyléthanolamine", "phospholipide"), ("phosphatidylinositol", "phospholipide"),
        ("céramide", "sphingolipide"), ("sitostérol", "stérol"), ("lanostérol", "stérol"),
        ("blanc de baleine", "cire"),
    ]
    publie("type_lipide_classe", "physique",
           "Modèle (Claude) — biochimie textbook curée (classe de lipide ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_acide_gras")
def ingere_type_acide_gras():
    # SOURCE = LE MODÈLE. Acide gras -> saturation ; ENSEMBLE FERMÉ : saturé (pas de double liaison) / insaturé.
    # Textbook biochimie, FAUX=0. Saturés = palmitique/stéarique ; insaturés = oléique/linoléique/oméga-3.
    paires = [
        ("acide palmitique", "saturé"), ("acide stéarique", "saturé"), ("acide butyrique", "saturé"),
        ("acide laurique", "saturé"), ("acide myristique", "saturé"), ("acide caprique", "saturé"),
        ("acide oléique", "insaturé"), ("acide linoléique", "insaturé"),
        ("acide alpha-linolénique", "insaturé"), ("acide arachidonique", "insaturé"),
        ("oméga-3", "insaturé"), ("oméga-6", "insaturé"), ("acide palmitoléique", "insaturé"),
        # — approfondissement run-autonome (saturation certaine) —
        ("acide caprylique", "saturé"), ("acide caproïque", "saturé"), ("acide arachidique", "saturé"),
        ("acide béhénique", "saturé"),
        ("acide érucique", "insaturé"), ("acide gamma-linolénique", "insaturé"),
        ("acide docosahexaénoïque", "insaturé"), ("acide eicosapentaénoïque", "insaturé"),
        # — approfondissement run-autonome v2 (saturation certaine) —
        ("acide margarique", "saturé"), ("acide pentadécanoïque", "saturé"), ("acide cérotique", "saturé"),
        ("acide myristoléique", "insaturé"), ("acide vaccénique", "insaturé"),
        ("acide nervonique", "insaturé"), ("acide ricinoléique", "insaturé"),
    ]
    publie("type_acide_gras", "physique",
           "Modèle (Claude) — biochimie textbook curée (acide gras saturé/insaturé ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("forme_proteine")
def ingere_forme_proteine():
    # SOURCE = LE MODÈLE. Protéine -> forme structurale ; ENSEMBLE FERMÉ : fibreuse (allongée, structurale) /
    # globulaire (repliée, soluble). Textbook biochimie, FAUX=0. Fibreuses = collagène/kératine ; globulaires =
    # hémoglobine/enzymes/anticorps.
    paires = [
        ("collagène", "fibreuse"), ("kératine", "fibreuse"), ("élastine", "fibreuse"),
        ("fibroïne", "fibreuse"),
        ("hémoglobine", "globulaire"), ("myoglobine", "globulaire"), ("albumine", "globulaire"),
        ("insuline", "globulaire"), ("immunoglobuline", "globulaire"), ("lysozyme", "globulaire"),
        # — approfondissement run-autonome (forme certaine) —
        ("fibrine", "fibreuse"), ("titine", "fibreuse"),
        ("catalase", "globulaire"), ("pepsine", "globulaire"), ("amylase", "globulaire"),
        ("ferritine", "globulaire"), ("transferrine", "globulaire"),
    ]
    publie("forme_proteine", "physique",
           "Modèle (Claude) — biochimie textbook curée (protéine fibreuse/globulaire ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("localisation_organe_corps")
def ingere_localisation_organe_corps():
    # SOURCE = LE MODÈLE. Organe -> grande région anatomique ; ENSEMBLE FERMÉ : tête / cou / thorax / abdomen /
    # bassin. Textbook anatomie, FAUX=0. ⚠ Organes traversant plusieurs régions (œsophage, trachée) EXCLUS.
    paires = [
        ("cerveau", "tête"), ("œil", "tête"), ("hypophyse", "tête"),
        ("larynx", "cou"), ("pharynx", "cou"), ("thyroïde", "cou"),
        ("cœur", "thorax"), ("poumon", "thorax"), ("thymus", "thorax"),
        ("estomac", "abdomen"), ("foie", "abdomen"), ("rate", "abdomen"), ("pancréas", "abdomen"),
        ("intestin grêle", "abdomen"), ("rein", "abdomen"), ("vésicule biliaire", "abdomen"),
        ("vessie", "bassin"), ("utérus", "bassin"), ("ovaire", "bassin"), ("prostate", "bassin"),
        ("rectum", "bassin"),
        # — approfondissement run-autonome (région certaine) —
        ("cervelet", "tête"), ("hypothalamus", "tête"), ("glande pinéale", "tête"), ("oreille interne", "tête"),
        ("amygdales", "cou"), ("parathyroïde", "cou"),
        ("bronches", "thorax"), ("plèvre", "thorax"),
        ("côlon", "abdomen"), ("appendice", "abdomen"), ("duodénum", "abdomen"),
        ("glande surrénale", "abdomen"),
        ("trompe de Fallope", "bassin"),
        # — approfondissement run-autonome v3 —
        ("langue", "tête"), ("sinus", "tête"), ("mâchoire", "tête"),
        ("médiastin", "thorax"),
        ("jéjunum", "abdomen"), ("iléon", "abdomen"), ("cæcum", "abdomen"), ("uretère", "abdomen"),
        ("péritoine", "abdomen"),
        ("vésicule séminale", "bassin"), ("canal déférent", "bassin"), ("vagin", "bassin"),
    ]
    publie("localisation_organe_corps", "physique",
           "Modèle (Claude) — anatomie textbook curée (organe -> région du corps ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("couleur_pigment_biologique")
def ingere_couleur_pigment_biologique():
    # SOURCE = LE MODÈLE. Pigment biologique -> couleur dominante. Textbook biochimie, FAUX=0. ⚠ Anthocyane
    # EXCLUE (couleur variable selon le pH) ; on ne garde que les pigments à couleur non ambiguë.
    paires = [
        ("chlorophylle", "vert"), ("carotène", "orange"), ("xanthophylle", "jaune"),
        ("lycopène", "rouge"), ("mélanine", "noir"), ("hémoglobine", "rouge"),
        ("bilirubine", "jaune"), ("phycocyanine", "bleu"),
        # — approfondissement run-autonome (couleur certaine) —
        ("biliverdine", "vert"), ("astaxanthine", "rose"), ("lutéine", "jaune"),
        ("hémocyanine", "bleu"), ("chlorophylle b", "vert"),
        # — approfondissement run-autonome v2 (couleur certaine ; anthocyane exclue car variable) —
        ("fucoxanthine", "brun"), ("phycoérythrine", "rouge"), ("urobiline", "jaune"),
        ("zéaxanthine", "jaune"), ("bétalaïne", "rouge"), ("eumélanine", "noir"),
    ]
    publie("couleur_pigment_biologique", "physique",
           "Modèle (Claude) — biochimie textbook curée (pigment -> couleur ; FAUX=0 vérifié)", paires)


@domaine("nombre_cotyledons_plante")
def ingere_nombre_cotyledons_plante():
    # SOURCE = LE MODÈLE. Angiosperme -> classe selon les cotylédons ; ENSEMBLE FERMÉ : monocotylédone /
    # dicotylédone. Textbook botanique, FAUX=0. ⚠ Uniquement des ANGIOSPERMES (les gymnospermes n'entrent pas
    # dans cette dichotomie). Monocots = graminées/liliacées/palmiers ; dicots = le reste des plantes à fleurs.
    paires = [
        ("blé", "monocotylédone"), ("maïs", "monocotylédone"), ("riz", "monocotylédone"),
        ("orge", "monocotylédone"), ("avoine", "monocotylédone"), ("tulipe", "monocotylédone"),
        ("oignon", "monocotylédone"), ("ail", "monocotylédone"), ("poireau", "monocotylédone"),
        ("palmier", "monocotylédone"), ("bambou", "monocotylédone"), ("orchidée", "monocotylédone"),
        ("lys", "monocotylédone"), ("gingembre", "monocotylédone"), ("canne à sucre", "monocotylédone"),
        ("haricot", "dicotylédone"), ("pois", "dicotylédone"), ("chêne", "dicotylédone"),
        ("hêtre", "dicotylédone"), ("rosier", "dicotylédone"), ("pommier", "dicotylédone"),
        ("tournesol", "dicotylédone"), ("tomate", "dicotylédone"), ("carotte", "dicotylédone"),
        ("lavande", "dicotylédone"), ("menthe", "dicotylédone"), ("soja", "dicotylédone"),
        ("olivier", "dicotylédone"), ("vigne", "dicotylédone"), ("chou", "dicotylédone"),
        ("fraisier", "dicotylédone"), ("tilleul", "dicotylédone"),
    ]
    publie("nombre_cotyledons_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (mono/dicotylédone ; angiospermes ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("division_champignon")
def ingere_division_champignon():
    # SOURCE = LE MODÈLE. Champignon -> division ; ENSEMBLE FERMÉ : basidiomycète (spores sur basides ;
    # champignons à chapeau) / ascomycète (spores dans des asques ; morille/truffe/levure). Textbook mycologie,
    # FAUX=0 (exemples classiques non contestés).
    paires = [
        ("bolet", "basidiomycète"), ("girolle", "basidiomycète"), ("amanite tue-mouches", "basidiomycète"),
        ("champignon de Paris", "basidiomycète"), ("cèpe", "basidiomycète"), ("russule", "basidiomycète"),
        ("lactaire", "basidiomycète"), ("coprin", "basidiomycète"), ("pleurote", "basidiomycète"),
        ("shiitake", "basidiomycète"),
        ("morille", "ascomycète"), ("truffe", "ascomycète"), ("pénicillium", "ascomycète"),
        ("levure de boulanger", "ascomycète"), ("aspergillus", "ascomycète"), ("pézize", "ascomycète"),
        # — approfondissement run-autonome (division certaine) —
        ("rosé des prés", "basidiomycète"), ("lépiote", "basidiomycète"), ("vesse-de-loup", "basidiomycète"),
        ("polypore", "basidiomycète"), ("amanite phalloïde", "basidiomycète"), ("pied-de-mouton", "basidiomycète"),
        ("clavaire", "basidiomycète"),
        ("gyromitre", "ascomycète"), ("helvelle", "ascomycète"),
    ]
    publie("division_champignon", "physique",
           "Modèle (Claude) — mycologie textbook curée (division fongique ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("classe_mollusque")
def ingere_classe_mollusque():
    # SOURCE = LE MODÈLE. Mollusque -> classe ; ENSEMBLE FERMÉ : gastéropode (coquille spiralée/limace) /
    # bivalve (2 valves) / céphalopode (tentacules). Textbook zoologie, FAUX=0. Sous-classification du phylum
    # Mollusques (distinct de classe_invertebre où la valeur EST « mollusque »).
    paires = [
        ("escargot", "gastéropode"), ("limace", "gastéropode"), ("bigorneau", "gastéropode"),
        ("patelle", "gastéropode"), ("buccin", "gastéropode"), ("ormeau", "gastéropode"),
        ("moule", "bivalve"), ("huître", "bivalve"), ("palourde", "bivalve"),
        ("coquille Saint-Jacques", "bivalve"), ("coque", "bivalve"),
        ("pieuvre", "céphalopode"), ("calmar", "céphalopode"), ("seiche", "céphalopode"),
        ("nautile", "céphalopode"),
        # — approfondissement run-autonome (classe certaine) —
        ("conque", "gastéropode"), ("murex", "gastéropode"), ("nudibranche", "gastéropode"),
        ("bulot", "gastéropode"), ("colimaçon", "gastéropode"),
        ("praire", "bivalve"), ("telline", "bivalve"), ("couteau", "bivalve"), ("pétoncle", "bivalve"),
        ("coque", "bivalve"),
        ("sépiole", "céphalopode"),
        # — approfondissement run-autonome v2 —
        ("patelle", "gastéropode"), ("ormeau", "gastéropode"), ("planorbe", "gastéropode"),
        ("aplysie", "gastéropode"), ("vignot", "gastéropode"),
        ("moule zébrée", "bivalve"), ("clam", "bivalve"), ("anodonte", "bivalve"),
        ("argonaute", "céphalopode"),
    ]
    publie("classe_mollusque", "physique",
           "Modèle (Claude) — zoologie textbook curée (classe de mollusque ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_feuille_plante")
def ingere_type_feuille_plante():
    # SOURCE = LE MODÈLE. Plante -> type de feuille ; ENSEMBLE FERMÉ : simple (1 limbe) / composée (folioles).
    # Textbook botanique, FAUX=0. Composées = frêne/marronnier/robinier/rosier (folioles distinctes).
    paires = [
        ("chêne", "simple"), ("hêtre", "simple"), ("érable", "simple"), ("tilleul", "simple"),
        ("peuplier", "simple"), ("bouleau", "simple"), ("charme", "simple"), ("laurier", "simple"),
        ("magnolia", "simple"), ("vigne", "simple"), ("platane", "simple"), ("menthe", "simple"),
        ("basilic", "simple"),
        ("frêne", "composée"), ("marronnier", "composée"), ("robinier", "composée"), ("noyer", "composée"),
        ("sureau", "composée"), ("rosier", "composée"), ("trèfle", "composée"), ("fraisier", "composée"),
        ("sorbier", "composée"), ("glycine", "composée"),
    ]
    publie("type_feuille_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (type de feuille simple/composée ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("phyllotaxie_plante")
def ingere_phyllotaxie_plante():
    # SOURCE = LE MODÈLE. Plante -> phyllotaxie (disposition des feuilles sur la tige) ; ENSEMBLE FERMÉ :
    # alterne / opposée / verticillée. Textbook botanique, FAUX=0. Lamiacées+oléacées+érable+marronnier =
    # OPPOSÉE ; laurier-rose/gaillet/prêle = VERTICILLÉE ; chêne/hêtre/rosier/graminées = ALTERNE.
    paires = [
        ("menthe", "opposée"), ("basilic", "opposée"), ("sauge", "opposée"), ("thym", "opposée"),
        ("lavande", "opposée"), ("lilas", "opposée"), ("frêne", "opposée"), ("olivier", "opposée"),
        ("érable", "opposée"), ("marronnier", "opposée"), ("œillet", "opposée"),
        ("chêne", "alterne"), ("hêtre", "alterne"), ("rosier", "alterne"), ("pommier", "alterne"),
        ("tournesol", "alterne"), ("blé", "alterne"), ("bouleau", "alterne"), ("saule", "alterne"),
        ("peuplier", "alterne"),
        ("laurier-rose", "verticillée"), ("gaillet", "verticillée"), ("prêle", "verticillée"),
    ]
    publie("phyllotaxie_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (phyllotaxie ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("organe_plante_fonction")
def ingere_organe_plante_fonction():
    # SOURCE = LE MODÈLE (directive Yohan). Organe végétal -> fonction principale. Textbook botanique, FAUX=0.
    paires = [
        ("racine", "absorption de l'eau"), ("feuille", "photosynthèse"),
        ("fleur", "reproduction"), ("tige", "soutien"), ("fruit", "protection de la graine"),
    ]
    publie("organe_plante_fonction", "physique",
           "Modèle (Claude) — botanique textbook curée (fonction d'organe végétal ; FAUX=0 vérifié)", paires)


@domaine("role_vitamine")
def ingere_role_vitamine():
    # SOURCE = LE MODÈLE. Vitamine -> rôle physiologique principal. Textbook nutrition, FAUX=0.
    paires = [
        ("vitamine D", "absorption du calcium"), ("vitamine K", "coagulation sanguine"),
        ("vitamine A", "vision"), ("vitamine C", "synthèse du collagène"),
        ("vitamine B12", "formation des globules rouges"), ("vitamine B9", "synthèse de l'ADN"),
        ("vitamine E", "antioxydant"),
        # — approfondissement run-autonome (rôle canonique certain des vitamines B) —
        ("vitamine B1", "métabolisme des glucides"), ("vitamine B2", "métabolisme énergétique"),
        ("vitamine B3", "métabolisme énergétique"), ("vitamine B5", "synthèse de la coenzyme A"),
        ("vitamine B6", "métabolisme des acides aminés"), ("vitamine B8", "métabolisme des acides gras"),
    ]
    publie("role_vitamine", "physique",
           "Modèle (Claude) — nutrition textbook curée (rôle de vitamine ; FAUX=0 vérifié)", paires)


@domaine("role_hormone")
def ingere_role_hormone():
    # SOURCE = LE MODÈLE. Hormone -> effet physiologique principal. Textbook endocrinologie, FAUX=0.
    paires = [
        ("insuline", "diminution de la glycémie"), ("glucagon", "augmentation de la glycémie"),
        ("adrénaline", "accélération du rythme cardiaque"), ("cortisol", "réponse au stress"),
        ("hormone antidiurétique", "réabsorption de l'eau"), ("ocytocine", "contractions utérines"),
        ("mélatonine", "régulation du sommeil"), ("thyroxine", "augmentation du métabolisme"),
        ("parathormone", "augmentation de la calcémie"), ("calcitonine", "diminution de la calcémie"),
        # — approfondissement run-autonome (effet physiologique principal certain) —
        ("hormone de croissance", "croissance des tissus"), ("prolactine", "production de lait"),
        ("testostérone", "développement des caractères sexuels masculins"),
        ("œstrogène", "développement des caractères sexuels féminins"),
        ("progestérone", "maintien de la grossesse"), ("aldostérone", "réabsorption du sodium"),
        ("érythropoïétine", "production des globules rouges"),
        ("leptine", "régulation de la satiété"), ("ghréline", "stimulation de l'appétit"),
    ]
    publie("role_hormone", "physique",
           "Modèle (Claude) — endocrinologie textbook curée (effet d'hormone ; FAUX=0 vérifié)", paires)


@domaine("role_oligoelement")
def ingere_role_oligoelement():
    # SOURCE = LE MODÈLE. Minéral / oligo-élément -> rôle physiologique principal. Textbook, FAUX=0.
    paires = [
        ("fer", "transport de l'oxygène"), ("calcium", "minéralisation osseuse"),
        ("iode", "synthèse des hormones thyroïdiennes"), ("sodium", "équilibre hydrique"),
        ("potassium", "transmission de l'influx nerveux"), ("magnésium", "contraction musculaire"),
        ("fluor", "protection de l'émail dentaire"),
        # — approfondissement run-autonome (rôle physiologique principal certain) —
        ("phosphore", "minéralisation osseuse"), ("sélénium", "antioxydant"),
        ("chlore", "équilibre acido-basique"), ("zinc", "cicatrisation"),
    ]
    publie("role_oligoelement", "physique",
           "Modèle (Claude) — physiologie textbook curée (rôle d'oligo-élément ; FAUX=0 vérifié)", paires)


@domaine("classe_antibiotique")
def ingere_classe_antibiotique():
    # SOURCE = LE MODÈLE. Antibiotique -> classe (ENSEMBLE FERMÉ : bêta-lactamine/macrolide/aminoside…).
    # Textbook pharmacologie, FAUX=0.
    paires = [
        ("pénicilline", "bêta-lactamine"), ("amoxicilline", "bêta-lactamine"),
        ("ceftriaxone", "céphalosporine"), ("ciprofloxacine", "fluoroquinolone"),
        ("doxycycline", "tétracycline"), ("érythromycine", "macrolide"),
        ("azithromycine", "macrolide"), ("gentamicine", "aminoside"),
        ("streptomycine", "aminoside"), ("vancomycine", "glycopeptide"),
        # — approfondissement run-autonome (classe pharmacologique certaine) —
        ("clarithromycine", "macrolide"), ("ampicilline", "bêta-lactamine"),
        ("céfotaxime", "céphalosporine"), ("lévofloxacine", "fluoroquinolone"),
        ("minocycline", "tétracycline"), ("amikacine", "aminoside"), ("tobramycine", "aminoside"),
        ("clindamycine", "lincosamide"), ("imipénème", "carbapénème"), ("méropénème", "carbapénème"),
        ("aztréonam", "monobactame"), ("colistine", "polymyxine"), ("linézolide", "oxazolidinone"),
        ("rifampicine", "rifamycine"), ("métronidazole", "nitro-imidazole"),
        ("sulfaméthoxazole", "sulfamide"),
        # — approfondissement run-autonome v2 (classe certaine) —
        ("céfixime", "céphalosporine"), ("ceftazidime", "céphalosporine"),
        ("norfloxacine", "fluoroquinolone"), ("moxifloxacine", "fluoroquinolone"),
        ("spiramycine", "macrolide"), ("josamycine", "macrolide"),
        ("nétilmicine", "aminoside"), ("pénicilline G", "bêta-lactamine"),
        ("pipéracilline", "bêta-lactamine"), ("ertapénème", "carbapénème"), ("doripénème", "carbapénème"),
    ]
    publie("classe_antibiotique", "physique",
           "Modèle (Claude) — pharmacologie textbook curée (classe d'antibiotique ; FAUX=0 vérifié)", paires)


@domaine("classe_therapeutique_medicament")
def ingere_classe_therapeutique_medicament():
    # SOURCE = LE MODÈLE. Médicament -> classe thérapeutique principale. Textbook, FAUX=0 (classe primaire
    # non contestée ; médicaments multi-classes ramenés à leur classe canonique).
    paires = [
        ("paracétamol", "antalgique"), ("aspirine", "anti-inflammatoire"),
        ("ibuprofène", "anti-inflammatoire"), ("amoxicilline", "antibiotique"),
        ("oméprazole", "inhibiteur de la pompe à protons"), ("salbutamol", "bronchodilatateur"),
        ("insuline", "antidiabétique"), ("morphine", "analgésique opioïde"),
        ("warfarine", "anticoagulant"), ("furosémide", "diurétique"),
        # — approfondissement run-autonome (classe thérapeutique canonique certaine) —
        ("diclofénac", "anti-inflammatoire"), ("naproxène", "anti-inflammatoire"),
        ("codéine", "analgésique opioïde"), ("tramadol", "analgésique opioïde"),
        ("fentanyl", "analgésique opioïde"), ("héparine", "anticoagulant"),
        ("ésoméprazole", "inhibiteur de la pompe à protons"), ("pantoprazole", "inhibiteur de la pompe à protons"),
        ("metformine", "antidiabétique"), ("loratadine", "antihistaminique"),
        ("cétirizine", "antihistaminique"), ("fluoxétine", "antidépresseur"),
        ("atorvastatine", "hypolipémiant"), ("simvastatine", "hypolipémiant"),
        ("propranolol", "bêta-bloquant"), ("diazépam", "anxiolytique"),
        # — approfondissement run-autonome v2 (classe canonique certaine) —
        ("kétoprofène", "anti-inflammatoire"), ("célécoxib", "anti-inflammatoire"),
        ("oxycodone", "analgésique opioïde"),
        ("ramipril", "antihypertenseur"), ("énalapril", "antihypertenseur"), ("amlodipine", "antihypertenseur"),
        ("aténolol", "bêta-bloquant"), ("bisoprolol", "bêta-bloquant"),
        ("rosuvastatine", "hypolipémiant"), ("pravastatine", "hypolipémiant"),
        ("sertraline", "antidépresseur"), ("paroxétine", "antidépresseur"),
        ("lorazépam", "anxiolytique"), ("alprazolam", "anxiolytique"),
        ("desloratadine", "antihistaminique"),
    ]
    publie("classe_therapeutique_medicament", "physique",
           "Modèle (Claude) — pharmacologie textbook curée (classe thérapeutique ; FAUX=0 vérifié)", paires)


@domaine("type_dent")
def ingere_type_dent():
    # SOURCE = LE MODÈLE. Type de dent -> fonction masticatoire. Textbook, FAUX=0.
    paires = [
        ("incisive", "couper"), ("canine", "déchirer"),
        ("prémolaire", "écraser"), ("molaire", "broyer"),
    ]
    publie("type_dent", "physique",
           "Modèle (Claude) — anatomie dentaire textbook curée (fonction de la dent ; FAUX=0 vérifié)", paires)


@domaine("respiration_animal")
def ingere_respiration_animal():
    # SOURCE = LE MODÈLE. Animal -> organe/mode respiratoire (ENSEMBLE FERMÉ : branchies/poumons/trachées/
    # peau). Textbook, FAUX=0. Corrige idées reçues : baleine/dauphin = POUMONS (pas branchies).
    paires = [
        ("poisson", "branchies"), ("grand requin blanc", "branchies"), ("carpe commune", "branchies"),
        ("baleine bleue", "poumons"), ("dauphin", "poumons"), ("crocodile du Nil", "poumons"),
        ("manchot empereur", "poumons"), ("abeille", "trachées"), ("sauterelle", "trachées"),
        ("ver de terre", "peau"),
        # — approfondissement run-autonome (organe respiratoire certain, closed-set) —
        ("thon rouge", "branchies"), ("saumon atlantique", "branchies"), ("morue", "branchies"),
        ("hippocampe", "branchies"), ("raie manta", "branchies"),
        ("lion", "poumons"), ("aigle royal", "poumons"), ("python", "poumons"),
        ("tortue marine", "poumons"), ("escargot", "poumons"),
        ("papillon", "trachées"), ("fourmi", "trachées"), ("scarabée", "trachées"),
        ("criquet", "trachées"), ("sangsue", "peau"),
    ]
    publie("respiration_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (respiration ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("thermoregulation_animal")
def ingere_thermoregulation_animal():
    # SOURCE = LE MODÈLE. Animal -> thermorégulation (ENSEMBLE FERMÉ : sang chaud/sang froid). Textbook,
    # FAUX=0. Poissons à endothermie régionale (thon, requins lamnidés) ÉVITÉS -> carpe/morue (ectothermes nets).
    paires = [
        ("lion", "sang chaud"), ("vache", "sang chaud"), ("aigle royal", "sang chaud"),
        ("manchot empereur", "sang chaud"), ("dauphin", "sang chaud"), ("ornithorynque", "sang chaud"),
        ("python", "sang froid"), ("crocodile du Nil", "sang froid"), ("grenouille rousse", "sang froid"),
        ("carpe commune", "sang froid"), ("morue", "sang froid"), ("tortue marine", "sang froid"),
        ("iguane", "sang froid"),
        # — approfondissement run-autonome (thermorégulation certaine, ectothermes nets) —
        ("tigre", "sang chaud"), ("éléphant d'Afrique", "sang chaud"), ("chauve-souris", "sang chaud"),
        ("baleine bleue", "sang chaud"), ("ours brun", "sang chaud"), ("autruche", "sang chaud"),
        ("pigeon", "sang chaud"), ("hibou", "sang chaud"), ("chimpanzé", "sang chaud"),
        ("souris domestique", "sang chaud"),
        ("salamandre", "sang froid"), ("gecko", "sang froid"), ("varan", "sang froid"),
        ("cobra royal", "sang froid"), ("lézard", "sang froid"), ("vipère", "sang froid"),
        ("crapaud", "sang froid"), ("saumon atlantique", "sang froid"), ("sardine", "sang froid"),
        ("anguille", "sang froid"),
    ]
    publie("thermoregulation_animal", "physique",
           "Modèle (Claude) — zoologie textbook curée (thermorégulation ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("groupe_aliment")
def ingere_groupe_aliment():
    # SOURCE = LE MODÈLE. Aliment -> groupe alimentaire (ENSEMBLE FERMÉ). Textbook nutrition, FAUX=0.
    # Aliments à classification ambiguë (tomate, avocat) ÉVITÉS. pomme de terre = féculent (nutritionnel).
    paires = [
        ("pomme", "fruit"), ("banane", "fruit"), ("orange", "fruit"), ("fraise", "fruit"),
        ("carotte", "légume"), ("épinard", "légume"), ("brocoli", "légume"), ("haricot vert", "légume"),
        ("pain", "féculent"), ("riz", "féculent"), ("pâtes", "féculent"), ("pomme de terre", "féculent"),
        ("lait", "produit laitier"), ("fromage", "produit laitier"), ("yaourt", "produit laitier"),
        ("bœuf", "viande"), ("poulet", "viande"), ("porc", "viande"),
        ("saumon", "poisson"), ("thon", "poisson"),
        # — approfondissement run-autonome (groupe alimentaire certain, closed-set) —
        ("poire", "fruit"), ("raisin", "fruit"), ("kiwi", "fruit"), ("cerise", "fruit"),
        ("melon", "fruit"), ("ananas", "fruit"), ("mangue", "fruit"), ("pêche", "fruit"),
        ("abricot", "fruit"), ("pastèque", "fruit"), ("framboise", "fruit"),
        ("chou", "légume"), ("courgette", "légume"), ("poireau", "légume"), ("poivron", "légume"),
        ("concombre", "légume"), ("laitue", "légume"), ("radis", "légume"), ("navet", "légume"),
        ("asperge", "légume"), ("chou-fleur", "légume"),
        ("blé", "féculent"), ("maïs", "féculent"), ("semoule", "féculent"),
        ("agneau", "viande"), ("veau", "viande"), ("dinde", "viande"), ("canard", "viande"),
        ("lapin", "viande"),
        ("sardine", "poisson"), ("maquereau", "poisson"), ("truite", "poisson"),
        ("cabillaud", "poisson"), ("sole", "poisson"), ("merlu", "poisson"),
        # — approfondissement run-autonome v2 (groupe certain) —
        ("clémentine", "fruit"), ("mandarine", "fruit"), ("pamplemousse", "fruit"), ("litchi", "fruit"),
        ("figue", "fruit"), ("prune", "fruit"), ("mûre", "fruit"), ("groseille", "fruit"),
        ("endive", "légume"), ("fenouil", "légume"), ("artichaut", "légume"), ("céleri", "légume"),
        ("navet", "légume"), ("épinard", "légume"), ("poireau", "légume"),
        ("semoule", "féculent"), ("quinoa", "féculent"), ("polenta", "féculent"), ("patate douce", "féculent"),
        ("agneau", "viande"), ("veau", "viande"), ("dinde", "viande"), ("lapin", "viande"),
        ("lieu", "poisson"), ("colin", "poisson"), ("lotte", "poisson"), ("perche", "poisson"),
    ]
    publie("groupe_aliment", "convention",
           "Modèle (Claude) — nutrition textbook curée (groupe alimentaire ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("famille_plante")
def ingere_famille_plante():
    # SOURCE = LE MODÈLE. Plante cultivée/courante -> famille botanique. Textbook botanique, FAUX=0.
    paires = [
        ("rosier", "rosacée"), ("pommier", "rosacée"), ("cerisier", "rosacée"),
        ("blé", "poacée"), ("maïs", "poacée"), ("riz", "poacée"),
        ("tournesol", "astéracée"), ("pissenlit", "astéracée"),
        ("chêne", "fagacée"), ("hêtre", "fagacée"),
        ("tomate", "solanacée"), ("pomme de terre", "solanacée"), ("poivron", "solanacée"),
        ("haricot", "fabacée"), ("pois", "fabacée"),
        ("lavande", "lamiacée"), ("menthe", "lamiacée"),
        # — approfondissement run-autonome (familles botaniques certaines, suffixe -acée) —
        ("fraisier", "rosacée"), ("poirier", "rosacée"), ("abricotier", "rosacée"),
        ("pêcher", "rosacée"), ("amandier", "rosacée"), ("framboisier", "rosacée"),
        ("orge", "poacée"), ("avoine", "poacée"), ("canne à sucre", "poacée"),
        ("bambou", "poacée"), ("seigle", "poacée"),
        ("laitue", "astéracée"), ("camomille", "astéracée"), ("artichaut", "astéracée"),
        ("aubergine", "solanacée"), ("tabac", "solanacée"), ("piment", "solanacée"),
        ("soja", "fabacée"), ("lentille", "fabacée"), ("luzerne", "fabacée"),
        ("trèfle", "fabacée"), ("arachide", "fabacée"),
        ("thym", "lamiacée"), ("romarin", "lamiacée"), ("sauge", "lamiacée"), ("basilic", "lamiacée"),
        ("carotte", "apiacée"), ("persil", "apiacée"), ("céleri", "apiacée"), ("fenouil", "apiacée"),
        ("chou", "brassicacée"), ("moutarde", "brassicacée"), ("radis", "brassicacée"),
        ("navet", "brassicacée"), ("colza", "brassicacée"),
        ("courgette", "cucurbitacée"), ("concombre", "cucurbitacée"), ("melon", "cucurbitacée"),
        ("pastèque", "cucurbitacée"),
        ("figuier", "moracée"), ("mûrier", "moracée"),
        # — approfondissement run-autonome v2 (famille certaine) —
        ("amandier", "rosacée"), ("prunier", "rosacée"), ("aubépine", "rosacée"), ("ronce", "rosacée"),
        ("millet", "poacée"), ("sorgho", "poacée"),
        ("pâquerette", "astéracée"), ("marguerite", "astéracée"), ("chardon", "astéracée"), ("bardane", "astéracée"),
        ("pétunia", "solanacée"), ("belladone", "solanacée"),
        ("genêt", "fabacée"), ("robinier", "fabacée"), ("vesce", "fabacée"),
        ("origan", "lamiacée"), ("mélisse", "lamiacée"), ("sarriette", "lamiacée"),
        ("aneth", "apiacée"), ("coriandre", "apiacée"), ("cerfeuil", "apiacée"),
        ("cresson", "brassicacée"), ("roquette", "brassicacée"),
        ("potiron", "cucurbitacée"), ("coloquinte", "cucurbitacée"),
        ("oranger", "rutacée"), ("citronnier", "rutacée"), ("mandarinier", "rutacée"),
        # — approfondissement run-autonome v3 —
        ("néflier", "rosacée"), ("cognassier", "rosacée"), ("sorgho", "poacée"), ("fétuque", "poacée"),
        ("chicorée", "astéracée"), ("salsifis", "astéracée"), ("souci", "astéracée"), ("dahlia", "astéracée"),
        ("hysope", "lamiacée"), ("marjolaine", "lamiacée"),
        ("lupin", "fabacée"), ("sainfoin", "fabacée"),
        ("datura", "solanacée"), ("morelle", "solanacée"), ("giroflée", "brassicacée"),
    ]
    publie("famille_plante", "convention",
           "Modèle (Claude) — botanique textbook curée (famille de plante ; FAUX=0 vérifié)", paires)


@domaine("partie_comestible_plante")
def ingere_partie_comestible_plante():
    # SOURCE = LE MODÈLE. Légume/plante -> partie comestible (ENSEMBLE FERMÉ : racine/tubercule/feuille/
    # fleur/fruit/graine/tige/bulbe). Textbook, FAUX=0. Corrige idées reçues : pomme de terre=TUBERCULE,
    # brocoli=FLEUR.
    paires = [
        ("carotte", "racine"), ("radis", "racine"), ("betterave", "racine"),
        ("pomme de terre", "tubercule"),
        ("épinard", "feuille"), ("laitue", "feuille"), ("chou", "feuille"),
        ("brocoli", "fleur"), ("chou-fleur", "fleur"), ("artichaut", "fleur"),
        ("tomate", "fruit"), ("courgette", "fruit"),
        ("petit pois", "graine"), ("haricot", "graine"),
        ("asperge", "tige"), ("céleri", "tige"),
        ("oignon", "bulbe"), ("ail", "bulbe"),
        # — approfondissement run-autonome (partie comestible certaine, closed-set) —
        ("navet", "racine"), ("panais", "racine"),
        ("patate douce", "tubercule"), ("igname", "tubercule"), ("manioc", "tubercule"),
        ("topinambour", "tubercule"),
        ("blette", "feuille"), ("cresson", "feuille"), ("mâche", "feuille"), ("endive", "feuille"),
        ("aubergine", "fruit"), ("poivron", "fruit"), ("concombre", "fruit"), ("potiron", "fruit"),
        ("lentille", "graine"), ("pois chiche", "graine"), ("fève", "graine"), ("maïs", "graine"),
        ("rhubarbe", "tige"), ("échalote", "bulbe"),
    ]
    publie("partie_comestible_plante", "physique",
           "Modèle (Claude) — botanique textbook curée (partie comestible ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("type_fruit_botanique")
def ingere_type_fruit_botanique():
    # SOURCE = LE MODÈLE. Fruit -> type botanique (baie/drupe…). Textbook botanique, FAUX=0. Fruits à
    # classification complexe (faux-fruits : fraise/pomme) ÉVITÉS.
    paires = [
        ("raisin", "baie"), ("tomate", "baie"), ("groseille", "baie"), ("myrtille", "baie"),
        ("cerise", "drupe"), ("pêche", "drupe"), ("prune", "drupe"), ("abricot", "drupe"),
        ("olive", "drupe"), ("mangue", "drupe"), ("datte", "drupe"),
        # — approfondissement après-midi (classification botanique certaine) —
        ("kiwi", "baie"), ("banane", "baie"), ("avocat", "baie"), ("poivron", "baie"),
        ("aubergine", "baie"), ("cassis", "baie"),
        ("noix de coco", "drupe"), ("café", "drupe"), ("nectarine", "drupe"),
        # — approfondissement run-autonome (drupes/baies non contestées) —
        ("mirabelle", "drupe"), ("quetsche", "drupe"), ("jujube", "drupe"),
        ("kaki", "baie"), ("goyave", "baie"), ("physalis", "baie"),
        # — approfondissement run-autonome v2 (drupes/baies non contestées) —
        ("prunelle", "drupe"), ("merise", "drupe"), ("cornouille", "drupe"),
        ("arbouse", "baie"), ("airelle", "baie"), ("canneberge", "baie"), ("épine-vinette", "baie"),
    ]
    publie("type_fruit_botanique", "convention",
           "Modèle (Claude) — botanique textbook curée (type de fruit ; FAUX=0 vérifié)", paires)


@domaine("organe_producteur_enzyme")
def ingere_organe_producteur_enzyme():
    # SOURCE = LE MODÈLE. Enzyme digestive -> organe producteur. Textbook physiologie, FAUX=0.
    paires = [
        ("pepsine", "estomac"), ("trypsine", "pancréas"), ("chymotrypsine", "pancréas"),
        ("amylase pancréatique", "pancréas"), ("ptyaline", "glande salivaire"),
    ]
    publie("organe_producteur_enzyme", "physique",
           "Modèle (Claude) — physiologie textbook curée (organe producteur d'enzyme ; FAUX=0 vérifié)", paires)


@domaine("nom_scientifique_animal")
def ingere_nom_scientifique_animal():
    # SOURCE = LE MODÈLE. Nom vernaculaire FR -> nom scientifique (binôme latin). Textbook zoologie, FAUX=0.
    # Noms communs AMBIGUS (plusieurs espèces : zèbre, dauphin/gorille génériques) ÉVITÉS -> clé non ambiguë.
    paires = [
        ("lion", "Panthera leo"), ("tigre", "Panthera tigris"), ("léopard", "Panthera pardus"),
        ("jaguar", "Panthera onca"), ("guépard", "Acinonyx jubatus"), ("loup gris", "Canis lupus"),
        ("chien", "Canis lupus familiaris"), ("renard roux", "Vulpes vulpes"), ("chat", "Felis catus"),
        ("ours brun", "Ursus arctos"), ("ours polaire", "Ursus maritimus"),
        ("panda géant", "Ailuropoda melanoleuca"), ("éléphant d'Afrique", "Loxodonta africana"),
        ("éléphant d'Asie", "Elephas maximus"), ("girafe", "Giraffa camelopardalis"),
        ("hippopotame", "Hippopotamus amphibius"), ("rhinocéros blanc", "Ceratotherium simum"),
        ("cheval", "Equus caballus"), ("âne", "Equus asinus"), ("vache", "Bos taurus"),
        ("mouton", "Ovis aries"), ("chèvre", "Capra hircus"), ("sanglier", "Sus scrofa"),
        ("lapin européen", "Oryctolagus cuniculus"), ("souris domestique", "Mus musculus"),
        ("rat brun", "Rattus norvegicus"), ("être humain", "Homo sapiens"),
        ("chimpanzé", "Pan troglodytes"), ("koala", "Phascolarctos cinereus"),
        ("ornithorynque", "Ornithorhynchus anatinus"), ("grand dauphin", "Tursiops truncatus"),
        ("baleine bleue", "Balaenoptera musculus"), ("orque", "Orcinus orca"),
        ("aigle royal", "Aquila chrysaetos"), ("faucon pèlerin", "Falco peregrinus"),
        ("pigeon biset", "Columba livia"), ("moineau domestique", "Passer domesticus"),
        ("manchot empereur", "Aptenodytes forsteri"), ("autruche", "Struthio camelus"),
        ("crocodile du Nil", "Crocodylus niloticus"), ("abeille", "Apis mellifera"),
        ("mouche domestique", "Musca domestica"), ("grenouille rousse", "Rana temporaria"),
        ("grand requin blanc", "Carcharodon carcharias"), ("saumon atlantique", "Salmo salar"),
        ("thon rouge", "Thunnus thynnus"), ("morue", "Gadus morhua"), ("carpe commune", "Cyprinus carpio"),
        # — approfondissement run-autonome (binômes certains, clés non ambiguës) —
        ("dromadaire", "Camelus dromedarius"), ("renne", "Rangifer tarandus"),
        ("hyène tachetée", "Crocuta crocuta"), ("oryctérope", "Orycteropus afer"),
        ("morse", "Odobenus rosmarus"), ("furet", "Mustela putorius furo"),
        ("cobaye", "Cavia porcellus"),
        # — approfondissement run-autonome v2 (binômes certains, espèces européennes) —
        ("loutre d'Europe", "Lutra lutra"), ("blaireau européen", "Meles meles"),
        ("hérisson d'Europe", "Erinaceus europaeus"), ("écureuil roux", "Sciurus vulgaris"),
        ("lynx boréal", "Lynx lynx"), ("bison d'Europe", "Bison bonasus"),
        ("chamois", "Rupicapra rupicapra"), ("bouquetin des Alpes", "Capra ibex"),
        ("marmotte alpine", "Marmota marmota"), ("castor d'Europe", "Castor fiber"),
        ("hermine", "Mustela erminea"), ("belette", "Mustela nivalis"), ("fouine", "Martes foina"),
    ]
    publie("nom_scientifique_animal", "convention",
           "Modèle (Claude) — zoologie textbook curée (nom vernaculaire FR -> binôme latin ; FAUX=0 vérifié)", paires)


@domaine("nom_scientifique_plante")
def ingere_nom_scientifique_plante():
    # SOURCE = LE MODÈLE. Nom commun FR de plante -> nom scientifique (binôme latin). Textbook botanique,
    # FAUX=0. Hybrides à notation ambiguë (fraisier/oranger ×) et noms génériques (rosier) ÉVITÉS.
    paires = [
        ("blé", "Triticum aestivum"), ("maïs", "Zea mays"), ("riz", "Oryza sativa"),
        ("orge", "Hordeum vulgare"), ("avoine", "Avena sativa"), ("seigle", "Secale cereale"),
        ("pomme de terre", "Solanum tuberosum"), ("tomate", "Solanum lycopersicum"),
        ("carotte", "Daucus carota"), ("oignon", "Allium cepa"), ("ail", "Allium sativum"),
        ("pommier", "Malus domestica"), ("vigne", "Vitis vinifera"), ("olivier", "Olea europaea"),
        ("tournesol", "Helianthus annuus"), ("chêne pédonculé", "Quercus robur"),
        ("hêtre commun", "Fagus sylvatica"), ("pin sylvestre", "Pinus sylvestris"),
        ("épicéa commun", "Picea abies"), ("bouleau verruqueux", "Betula pendula"),
        ("lavande vraie", "Lavandula angustifolia"), ("basilic", "Ocimum basilicum"),
        ("soja", "Glycine max"), ("caféier", "Coffea arabica"), ("cacaoyer", "Theobroma cacao"),
        ("canne à sucre", "Saccharum officinarum"), ("tabac", "Nicotiana tabacum"),
        ("pois", "Pisum sativum"), ("haricot commun", "Phaseolus vulgaris"),
        ("citronnier", "Citrus limon"), ("cerisier", "Prunus avium"),
        ("abricotier", "Prunus armeniaca"), ("pêcher", "Prunus persica"),
        # — approfondissement run-autonome (binômes certains) —
        ("courgette", "Cucurbita pepo"), ("concombre", "Cucumis sativus"),
        ("melon", "Cucumis melo"), ("pastèque", "Citrullus lanatus"),
        ("laitue", "Lactuca sativa"), ("épinard", "Spinacia oleracea"),
        ("betterave", "Beta vulgaris"), ("chou", "Brassica oleracea"),
        ("lin", "Linum usitatissimum"), ("fève", "Vicia faba"),
        ("lentille", "Lens culinaris"), ("arachide", "Arachis hypogaea"),
        ("thé", "Camellia sinensis"), ("gingembre", "Zingiber officinale"),
        ("prunier", "Prunus domestica"), ("poirier", "Pyrus communis"),
        ("noyer", "Juglans regia"), ("châtaignier", "Castanea sativa"),
        # — approfondissement run-autonome v2 (binômes certains) —
        ("tilleul", "Tilia cordata"), ("érable sycomore", "Acer pseudoplatanus"),
        ("frêne", "Fraxinus excelsior"), ("charme", "Carpinus betulus"), ("aulne", "Alnus glutinosa"),
        ("saule blanc", "Salix alba"), ("noisetier", "Corylus avellana"), ("if", "Taxus baccata"),
        ("genévrier", "Juniperus communis"), ("houx", "Ilex aquifolium"), ("lierre", "Hedera helix"),
        ("ortie", "Urtica dioica"), ("pissenlit", "Taraxacum officinale"),
        ("coquelicot", "Papaver rhoeas"), ("thym", "Thymus vulgaris"),
        ("menthe poivrée", "Mentha piperita"), ("persil", "Petroselinum crispum"),
    ]
    publie("nom_scientifique_plante", "convention",
           "Modèle (Claude) — botanique textbook curée (nom commun FR -> binôme latin ; FAUX=0 vérifié)", paires)


@domaine("solubilite_vitamine")
def ingere_solubilite_vitamine():
    # SOURCE = LE MODÈLE. Vitamine -> solubilité (ENSEMBLE FERMÉ : hydrosoluble/liposoluble). Textbook
    # nutrition, FAUX=0 (A/D/E/K liposolubles ; B et C hydrosolubles).
    paires = [
        ("vitamine A", "liposoluble"), ("vitamine D", "liposoluble"), ("vitamine E", "liposoluble"),
        ("vitamine K", "liposoluble"),
        ("vitamine C", "hydrosoluble"), ("vitamine B1", "hydrosoluble"), ("vitamine B6", "hydrosoluble"),
        ("vitamine B9", "hydrosoluble"), ("vitamine B12", "hydrosoluble"),
    ]
    publie("solubilite_vitamine", "physique",
           "Modèle (Claude) — nutrition textbook curée (solubilité de vitamine ; ensemble fermé ; FAUX=0)", paires)


@domaine("type_glucide")
def ingere_type_glucide():
    # SOURCE = LE MODÈLE. Glucide -> type (ENSEMBLE FERMÉ : ose/diholoside/polyoside). Textbook biochimie, FAUX=0.
    paires = [
        ("glucose", "ose"), ("fructose", "ose"), ("galactose", "ose"),
        ("saccharose", "diholoside"), ("lactose", "diholoside"), ("maltose", "diholoside"),
        ("amidon", "polyoside"), ("glycogène", "polyoside"), ("cellulose", "polyoside"),
    ]
    publie("type_glucide", "physique",
           "Modèle (Claude) — biochimie textbook curée (type de glucide ; ensemble fermé ; FAUX=0 vérifié)", paires)


@domaine("nom_scientifique_champignon")
def ingere_nom_scientifique_champignon():
    # SOURCE = LE MODÈLE. Nom commun FR de champignon -> nom scientifique (binôme). Textbook mycologie, FAUX=0.
    paires = [
        ("champignon de Paris", "Agaricus bisporus"), ("amanite tue-mouches", "Amanita muscaria"),
        ("amanite phalloïde", "Amanita phalloides"), ("cèpe de Bordeaux", "Boletus edulis"),
        ("truffe noire", "Tuber melanosporum"), ("girolle", "Cantharellus cibarius"),
        ("levure de boulanger", "Saccharomyces cerevisiae"),
    ]
    publie("nom_scientifique_champignon", "convention",
           "Modèle (Claude) — mycologie textbook curée (nom commun FR -> binôme latin ; FAUX=0 vérifié)", paires)


# COLLISION (nuit 2026-06-26) : cri_animal + petit_animal DÉJÀ faits par une autre lane (« lexique français
# de référence », même direction, 30/28 entrées plus riches que mes 13/14) -> ABANDONNÉS (redondants).


@domaine("nom_groupe_animaux")
def ingere_nom_groupe_animaux():
    # SOURCE = LE MODÈLE. Animal -> nom du groupe (collectif). Lexique FR borné -> `convention`. FAUX=0.
    paires = [
        ("loup", "meute"), ("poisson", "banc"), ("oiseau", "volée"), ("abeille", "essaim"),
        ("mouton", "troupeau"), ("lion", "troupe"), ("vache", "troupeau"),
        # — approfondissement run-autonome (collectifs FR classiques certains) —
        ("chien", "meute"), ("éléphant", "troupeau"), ("fourmi", "colonie"),
        ("perdrix", "compagnie"), ("sanglier", "compagnie"), ("cerf", "harde"),
        ("buffle", "troupeau"), ("manchot", "colonie"),
    ]
    publie("nom_groupe_animaux", "convention",
           "Modèle (Claude) — lexique zoologique FR curé (nom collectif ; FAUX=0 vérifié)", paires)


@domaine("adjectif_animal")
def ingere_adjectif_animal():
    # SOURCE = LE MODÈLE. Animal -> adjectif relationnel (racine latine). Lexique FR borné -> `convention`. FAUX=0.
    paires = [
        ("chien", "canin"), ("chat", "félin"), ("cheval", "équin"), ("vache", "bovin"),
        ("mouton", "ovin"), ("porc", "porcin"), ("chèvre", "caprin"),
        # — approfondissement run-autonome (adjectif relationnel certain) —
        ("lion", "léonin"), ("loup", "lupin"), ("âne", "asin"), ("oiseau", "aviaire"),
        ("serpent", "ophidien"), ("taureau", "taurin"), ("renard", "vulpin"),
        ("singe", "simiesque"), ("éléphant", "éléphantin"), ("aigle", "aquilin"),
        ("lièvre", "léporin"),
    ]
    publie("adjectif_animal", "convention",
           "Modèle (Claude) — lexique zoologique FR curé (adjectif relationnel ; FAUX=0 vérifié)", paires)


# COLLISION (nuit 2026-06-26) : sens_organe DÉJÀ pris par une autre source (« physiologie de référence »,
# direction organe->sens). Mon inverse (sens->organe) serait redondant -> ABANDONNÉ, je ne touche pas leur table.


@domaine("role_cellule_sanguine")
def ingere_role_cellule_sanguine():
    # SOURCE = LE MODÈLE (directive Yohan). Cellule sanguine -> rôle principal. Textbook, FAUX=0.
    paires = [
        ("globule rouge", "transport de l'oxygène"), ("globule blanc", "défense immunitaire"),
        ("plaquette", "coagulation"),
    ]
    publie("role_cellule_sanguine", "physique",
           "Modèle (Claude) — hématologie textbook curée (rôle des cellules sanguines ; FAUX=0 vérifié)", paires)


@domaine("monomere_polymere")
def ingere_monomere_polymere():
    # SOURCE = LE MODÈLE (directive Yohan). Polymère biologique -> son monomère. Textbook biochimie, FAUX=0.
    paires = [
        ("protéine", "acide aminé"), ("ADN", "nucléotide"), ("ARN", "nucléotide"),
        ("amidon", "glucose"), ("glycogène", "glucose"), ("cellulose", "glucose"),
    ]
    publie("monomere_polymere", "physique",
           "Modèle (Claude) — biochimie textbook curée (monomère d'un polymère biologique ; FAUX=0 vérifié)", paires)


# REJETÉ (nuit 2026-06-26) : type_nomenclatural_taxon (P427, genre->espèce-type). Vocab ouvert fonctionnel
# (33 178 faits, fonct=100 %) MAIS les LABELS DE GENRE (mot latin unique) sont homonymes cross-règnes
# (zoologie/botanique/mycologie sous codes distincts) : « Drosophila » (mouche) -> « Agaricus fibrillosus »
# (le genre FONGIQUE homonyme). Quand un seul règne est dans QLever, `fonctionnel` ne voit qu'une valeur et
# laisse passer un fait trompeur/faux. Les binômes (espèces) n'ont pas ce défaut, les genres si -> NE PAS reprendre.


@domaine("mode_heredite_maladie")
def ingere_mode_heredite_maladie():
    # P1199 « mode de transmission » (hérédité génétique) : maladie -> patron d'hérédité. ENSEMBLE FERMÉ
    # (~5 : autosomique récessive/dominante, récessive/dominante liée à l'X, mitochondriale). À NE PAS
    # confondre avec P1060 « mode de transmission » épidémiologique (déjà REJETÉ). Fait génétique réel ->
    # `physique`. Une maladie à plusieurs modes -> `fonctionnel` -> HORS. Petit (~50) mais closed-set propre.
    IQ._ingere_x_vers_entite(
        "mode_heredite_maladie", "P1199", "physique",
        "Wikidata/QLever — mode d'hérédité génétique de la maladie P1199 (ensemble fermé de patrons)",
        classe_qid="Q12136")


@domaine("proteine_du_gene")
def ingere_proteine_du_gene():
    # P688 « code pour » : un gène code pour son produit protéique (DCN -> Décorine, INS -> insuline).
    # VOCABULAIRE OUVERT fonctionnel (≈1-à-1, scout fonctionnel=100 %) : le scout le classe REJET car ce
    # n'est PAS un ensemble fermé, mais c'est le même profil que taxon_parent -> sanité par ANCRES (produits
    # protéiques vérifiés indépendamment). Un gène à PLUSIEURS produits -> `fonctionnel` -> HORS (sûr).
    # Fait biologique réel -> catégorie `physique`.
    IQ._ingere_x_vers_entite(
        "proteine_du_gene", "P688", "physique",
        "Wikidata/QLever — produit protéique du gène P688 (vocab ouvert fonctionnel ; multi-produit -> HORS)",
        classe_qid="Q7187")


@domaine("endemique_de_taxon")
def ingere_endemique_de_taxon():
    # P183 « endémique de » : un taxon dont l'aire de répartition naturelle est restreinte à UN lieu
    # (Madagascar, Hainan, île Lord Howe…). NE PAS appeler « habitat » (malhonnête : c'est l'endémisme,
    # pas le biotope). Fait biologique/géographique réel -> catégorie `physique`. Un taxon endémique de
    # PLUSIEURS lieux -> `fonctionnel` -> HORS (sûr). Scout : 217 lieux distincts / ratio 0,055 / fonctionnel
    # 98 %. Sanité = ancres (taxon non ambigu -> son territoire) + valeurs = lieux, ensemble borné.
    IQ._ingere_x_vers_entite(
        "endemique_de_taxon", "P183", "physique",
        "Wikidata/QLever — endémique de P183 (aire de répartition restreinte ; multi-lieux -> HORS)",
        classe_qid="Q16521")


@domaine("statut_conservation")
def ingere_statut_conservation():
    # P141 « statut de conservation » : catégorie UICN (ensemble fermé ~10). Valeur courante de Wikidata
    # (vérité datée comme population/capitale). `fonctionnel` -> HORS si plusieurs systèmes d'évaluation.
    IQ._ingere_x_vers_entite(
        "statut_conservation", "P141", "convention",
        "Wikidata/QLever — statut de conservation UICN P141 (catégorie courante ; ensemble fermé)",
        classe_qid="Q16521")


# ───────────────────────────────────────────────────────────────────────────────────────────
#  FILONS GÉANTS (~3,85 M lignes) — fetch PAGINÉ (ORDER BY ?e + LIMIT/OFFSET) -> snapshot _raw -> publie.
# ───────────────────────────────────────────────────────────────────────────────────────────
def _fetch_pagine(relation: str, classe_qid: str, prop: str, page: int = 300000, timeout: int = 600) -> list:
    """Récupère TOUTES les lignes « entité (classe_qid) -> valeur (prop) » par PAGES déterministes
    (ORDER BY ?e). Réutilise le snapshot _raw si présent (offline). Une seule requête à 3,85 M lignes
    sature timeout+RAM ; on borne chaque page à `page` lignes. FAUX=0 inchangé (mêmes filtres labels FR)."""
    chemin = os.path.join(RAW, relation + ".json")
    rows = charge_raw_json(chemin)                     # lit .json.xz (archivage) sinon .json, offline transparent
    if rows is not None:
        print(f"  [snapshot réutilisé : {relation}.json{'.xz' if os.path.exists(chemin + '.xz') else ''} — {len(rows)} lignes, offline]")
        return rows
    # 1) tentative SINGLE-SHOT (pas d'ORDER BY/OFFSET : QLever fait un seul scan, bien plus rapide qu'un
    #    re-tri par page). Si elle aboutit on évite la pagination O(offset).
    try:
        q1 = f"""SELECT ?eLabel ?vLabel WHERE {{
          ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?o .
          ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }}"""
        url = IQ.ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(IQ.PREFIXES + q1)
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "application/sparql-results+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            rows = json.loads(r.read())["results"]["bindings"]
        print(f"  single-shot -> {len(rows)} lignes")
        snapshot_brut(relation, rows)
        return rows
    except Exception as e:
        print(f"  single-shot KO ({str(e)[:80]}) -> repli pagination")
    rows: list = []
    offset = 0
    while True:
        q = f"""SELECT ?eLabel ?vLabel WHERE {{
          ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?o .
          ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }} ORDER BY ?e LIMIT {page} OFFSET {offset}"""
        url = IQ.ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(IQ.PREFIXES + q)
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "application/sparql-results+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            lot = json.loads(r.read())["results"]["bindings"]
        rows.extend(lot)
        print(f"  page offset={offset:>8d} -> +{len(lot)} (cumul {len(rows)})", flush=True)
        if len(lot) < page:
            break
        offset += page
    snapshot_brut(relation, rows)
    return rows


def _ingere_geant(relation: str, classe_qid: str, prop: str, categorie: str, source: str,
                  *, anti_self: bool = False):
    print(f"== {relation} (Wikidata/QLever {prop}, PAGINÉ, classe {classe_qid}) ==")
    rows = _fetch_pagine(relation, classe_qid, prop)
    print(f"  {len(rows)} lignes brutes.")
    paires = IQ._paires(rows, "eLabel", "vLabel")
    if anti_self:
        # Garde anti-circulaire (aligné sur _ingere_nonself) : une hiérarchie (taxon parent) ne peut se
        # boucler sur elle-même. Une collision de libellé FR entre DEUX QID distincts (entité et parent
        # homonymes) produirait entite==valeur = fait circulaire FAUX -> écarté vers HORS. FAUX=0 préservé.
        avant = len(paires)
        paires = [(e, v) for (e, v) in paires if e.strip().lower() != v.strip().lower()]
        n_self = avant - len(paires)
        if n_self:
            print(f"  [anti-self : {n_self} paires circulaires (entité==valeur) écartées -> HORS]")
    publie(relation, categorie, source, paires)


@domaine("taxon_rang")
def ingere_taxon_rang():
    # P105 « rang taxinomique » : ensemble fermé (espèce/genre/famille/sous-famille/ichnogenre…), ~qq dizaines.
    _ingere_geant("taxon_rang", "Q16521", "P105", "convention",
                  "Wikidata/QLever — rang taxinomique P105 (ensemble fermé de rangs)")


@domaine("taxon_parent")
def ingere_taxon_parent():
    # P171 « taxon supérieur » : taxon -> taxon parent (fonctionnel, vocabulaire ouvert ~millions). Sanité =
    # nom de taxon plausible + ANCRES vérité-terrain (Homo sapiens->Homo, lion->Panthera, souris dom.->Mus).
    _ingere_geant("taxon_parent", "Q16521", "P171", "convention",
                  "Wikidata/QLever — taxon parent P171 (arbre taxinomique ; fonctionnel)",
                  anti_self=True)


# filons LÉGERS par défaut (les géants : « python3 ingere_t4.py taxon_rang taxon_parent »).
_LEGERS = ["organisme_gene", "chromosome_gene", "statut_conservation"]
# specialite_medicale_maladie : requête lente (>200 s) -> sur demande, sous faible charge.

if __name__ == "__main__":
    import sys
    noms = sys.argv[1:] or _LEGERS
    for nom in noms:
        if nom not in _DOMAINES:
            print(f"!! domaine inconnu : {nom} (connus : {', '.join(_DOMAINES)})")
            continue
        _DOMAINES[nom]()
