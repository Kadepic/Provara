"""
INGESTION T12 — RELIGION, MYTHOLOGIE & PHILOSOPHIE  (ONLINE, lancé à la main).

Couloir T12 du palier 1 (le BORNÉ). Lis BRIEF_INGESTION_COMMUN.md + BRIEF_T12_RELIGION_MYTHO_PHILO.md.
Réutilise les fabriques de `ingere_qlever` (NE redéfinit PAS de fabrique). FAUX=0 INVIOLABLE :
`fonctionnel` (1 valeur/entité ; multi-valeur -> HORS) + filtre valeur-plausible + ancres vérité-terrain
(dans valide_lecteur_t12). Catégorie `convention` (faits culturels fixés par le corpus mythologique/doctrinal).

Relations (toutes = entité→valeur-entité fonctionnelle, vocab OUVERT jugé comme un lieu : fonctionnel + ancres) :
  GÉNÉALOGIE MYTHOLOGIQUE (divinité Q22989102) :
    - pere_divinite   P22  (divinité -> père ; ex. Arès->Zeus, Zeus->Cronos ; Aphrodite multi -> HORS)
    - mere_divinite   P25  (divinité -> mère)
  PHILOSOPHIE (philosophe Q4964182) :
    - ecole_philosophe P1416 (philosophe -> école/courant ; vocab semi-fermé de courants)
    - maitre_philosophe P1066 (philosophe -> maître / « élève de » ; souvent fonctionnel)

DÉJÀ fait (NE PAS refaire) : domaine_dieu, pantheon_dieu, animal_dieu, origine_creature, fondateur_religion,
religion_lieu_culte, lieu_saint_religion, jour_saint_religion, texte_sacre, lieu_culte, element_zodiaque,
ordre_signe_chinois.
DÉFÉRÉ (multi-valeur fonctionnel -> jamais désactiver) : conjoint_divinite (P26), influence (P737).

Usage : python3 ingere_t12.py [relations...]   (défaut : toutes)   puis valide_lecteur_t12.py OFFLINE.
"""
from __future__ import annotations

import sys

import ingere_qlever as IQ

_T12 = {}


def _t12(nom):
    def deco(fn):
        _T12[nom] = fn
        return fn
    return deco


def _a_une_lettre(v: str) -> bool:
    return any(c.isalpha() for c in v)


def _ingere_manuel(relation, paires, source):
    """Source = SAVOIR CANONIQUE CURÉ (« moi-source », directive Yohan 2026-06-26) — pour les faits BORNÉS,
    non disputés, que Wikidata n'expose PAS proprement (attributs iconographiques de divinités : monture/vâhana,
    arme signature). FAUX=0 conservé par : (1) restriction au canonique non contesté, (2) vérification
    ADVERSARIALE indépendante préalable (agent sceptique : seuls les CONFIRM passent), (3) `publie` applique
    `fonctionnel` (toute entité multi-valeur -> HORS) + réconciliation amorce. Les paires sont EN DUR ici =
    traçables/auditables dans le code (pas de hand-typing volatile)."""
    print(f"== {relation} (SAVOIR CANONIQUE CURÉ, vérifié adversarialement ; {len(paires)} paires) ==")
    IQ.publie(relation, "convention", source, list(paires))


def _ingere_occupation(relation, propriete, occ_qid, source):
    """Vocab OUVERT « personne d'occupation <occ_qid> -> entité nommée via <propriete> fonctionnelle ».
    Variante de _ingere_ouvert filtrant par OCCUPATION (P106) au lieu de l'instance (P31/P279*) : indispensable
    quand la « classe » est en réalité un métier (philosophe Q4964182 n'a PAS d'instances P31 -> P31/P279* vide).
    REJETTE les valeurs sans lettre (date/nombre fui = FAUX). `fonctionnel` (publie) écarte les entités à valeurs
    multiples (plusieurs maîtres -> HORS = sûr). Réutilise le snapshot _raw OFFLINE si présent."""
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P106 wd:{occ_qid} ; wdt:{propriete} ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P106={occ_qid} + {propriete}, filtre valeur-nommée) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires nommées-plausibles (dates/nombres rejetés).")
    IQ.publie(relation, "convention", source, paires)


def _ingere_ouvert(relation, propriete, classe_qid, source):
    """Vocab OUVERT (divinité/philosophe -> entité nommée) jugé par fonctionnel + filtre valeur-personne.
    Identique à _ingere_x_vers_entite mais REJETTE toute valeur sans lettre (une date/un nombre qui aurait fui
    = fait FAUX). `fonctionnel` (dans publie) écarte les entités multi-valeur (parents multiples, doubles
    traditions : Aphrodite -> Ouranos/Zeus) -> HORS = sûr. Réutilise le snapshot _raw OFFLINE si présent."""
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{propriete} ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever {propriete}, filtre valeur-nommée) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires nommées-plausibles (dates/nombres rejetés).")
    IQ.publie(relation, "convention", source, paires)


# ---- GÉNÉALOGIE MYTHOLOGIQUE ----

@_t12("pere_divinite")
def ingere_pere_divinite():
    _ingere_ouvert(
        "pere_divinite", "P22", "Q22989102",
        "Wikidata/QLever — père de la divinité P22 (généalogie mythologique ; multi-parent -> HORS)")


@_t12("mere_divinite")
def ingere_mere_divinite():
    _ingere_ouvert(
        "mere_divinite", "P25", "Q22989102",
        "Wikidata/QLever — mère de la divinité P25 (généalogie mythologique ; multi-parent -> HORS)")


# ---- PHILOSOPHIE (occupation P106=Q4964182 ; classe P31 Q4964182 est VIDE) ----
#
# REJETÉ (FAUX=0) : ecole_philosophe (P1416 « affiliation »). Scout P106 relu : la valeur n'est PAS une école
# de pensée mais un fourre-tout d'affiliations — départements universitaires (Stanford, Montréal), PARTIS
# politiques (groupe CDU/CSU au Bundestag = des politiciens), ordres religieux (Opus Dei, Habad-Loubavitch),
# think tanks (Cato Institute). Le nom « école du philosophe » serait MALHONNÊTE (cf. piège « grade militaire =
# Armée de terre »). Non ingéré. La généalogie intellectuelle passe par maitre_philosophe ci-dessous.

# LEÇON T9 « ne pas conclure épuisé » : pere/mere_divinite (classe divinité Q22989102) ratait les HÉROS/personnages
# mythiques (Persée/Hector/Énée/Aaron…). Classe élargie « personnage mythique » Q4271324 = 6× plus (2394+1394 faits
# fonctionnels vs 664). Méthode identique (fonctionnel : Apollon/Achille/Persée multi-tradition -> HORS = sûr).
# Superset propre de pere/mere_divinite (extension sans contradiction). Snapshot _raw offline (cache du probe).

def _ingere_fusion_raw(relation, sources_raw, source):
    """Fusionne plusieurs snapshots _raw QLever (classes qui se recouvrent sans superclasse commune) en UNE
    relation. publie applique fonctionnel (dédup + multi-valeur incohérente -> HORS). Offline."""
    import json as _json, os as _os
    from ingere_wikidata import RAW as _RAW
    paires = []
    for nom_raw in sources_raw:
        chemin = _os.path.join(_RAW, nom_raw + ".json")
        rows = _json.load(open(chemin, encoding="utf-8"))
        paires += [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"== {relation} (fusion {sources_raw} -> {len(paires)} paires brutes, offline) ==")
    IQ.publie(relation, "convention", source, paires)


@_t12("fondateur_ordre_religieux")
def ingere_fondateur_ordre_religieux():
    # ordre religieux (Q2061186) -> son fondateur (P112). 583 mono / 638 (fonc 92 %). Multi -> HORS.
    _ingere_ouvert(
        "fondateur_ordre_religieux", "P112", "Q2061186",
        "Wikidata/QLever — fondateur de l'ordre religieux P112 (multi -> HORS)")


@_t12("religion_ordre_religieux")
def ingere_religion_ordre_religieux():
    # ordre religieux (Q2061186) -> sa religion (P140). 167 mono / 179 (fonc 93 %), set fermé ~22 (catholicisme/
    # islam/… capte les ordres soufis). Multi -> HORS.
    _ingere_ouvert(
        "religion_ordre_religieux", "P140", "Q2061186",
        "Wikidata/QLever — religion de l'ordre religieux P140 (multi -> HORS)")


@_t12("dedicace_edifice_religieux")
def ingere_dedicace_edifice_religieux():
    # Édifice religieux -> saint/divinité/figure à qui il est dédié (P825). Classes église Q16970 + temple Q44539
    # (recouvrement partiel, pas de superclasse Wikidata commune -> fusion). Veine PROPRE ~98 % fonctionnel,
    # ~515-831 valeurs (set quasi-fermé de dédicataires). Contenu RELIGIEUX (lane T12), claim posté au board.
    _ingere_fusion_raw(
        "dedicace_edifice_religieux", ["dedicace_eglise", "dedicace_temple"],
        "Wikidata/QLever — dédicataire de l'édifice religieux P825 (saint/divinité ; multi -> HORS)")


@_t12("pere_personnage_mythique")
def ingere_pere_personnage_mythique():
    _ingere_ouvert(
        "pere_personnage_mythique", "P22", "Q4271324",
        "Wikidata/QLever — père du personnage mythique P22 (héros/divinités/figures légendaires ; multi -> HORS ; "
        "élargit pere_divinite via leçon T9)")


@_t12("mere_personnage_mythique")
def ingere_mere_personnage_mythique():
    _ingere_ouvert(
        "mere_personnage_mythique", "P25", "Q4271324",
        "Wikidata/QLever — mère du personnage mythique P25 (héros/divinités/figures légendaires ; multi -> HORS ; "
        "élargit mere_divinite via leçon T9)")


@_t12("conjoint_personnage_mythique")
def ingere_conjoint_personnage_mythique():
    # Élargit conjoint_divinite à la classe personnage mythique Q4271324 (leçon T9) : 1041 mono vs 135.
    # Héros/figures (Orphée->Eurydice, Tobit->Anna, Isis->Osiris…). Multi (Amphitrite, Eurydice homonymes) -> HORS.
    _ingere_ouvert(
        "conjoint_personnage_mythique", "P26", "Q4271324",
        "Wikidata/QLever — conjoint du personnage mythique P26 (multi -> HORS ; élargit conjoint_divinite, leçon T9)")


@_t12("conjoint_divinite")
def ingere_conjoint_divinite():
    # divinité (Q22989102) -> son conjoint UNIQUE enregistré (P26). Méthode QLever prouvée (= pere/mere) :
    # fonctionnel rejette les multi (Zeus, Poséidon multi-nymphes, Héphaïstos Aglaé/Aphrodite/Charis -> HORS = sûr,
    # résout proprement le cas disputé). Reste 135 couples mono (Hadès<->Perséphone, Téthys<->Océan…). DISTINCT de
    # parede_divinite (moi-source) : parede = parèdre principale même pour dieux polygames (Zeus->Héra) ; conjoint =
    # conjoint unique selon Wikidata (HORS si plusieurs). Snapshot _raw offline (réutilise le cache du probe).
    _ingere_ouvert(
        "conjoint_divinite", "P26", "Q22989102",
        "Wikidata/QLever — conjoint de la divinité P26 (multi-conjoint -> HORS ; complète parede_divinite)")


@_t12("maitre_philosophe")
def ingere_maitre_philosophe():
    # philosophe (occupation P106 Q4964182) -> son maître (P1066 « élève de », valeur = le maître). Les multi-
    # maîtres (Platon : Socrate/Théodore/…, Théophraste : Aristote/Platon) -> fonctionnel -> HORS = sûr. Restent
    # les lignées mono-maître documentées (Aristote->Platon, Plotin->Ammonios Saccas, Épictète->Musonius Rufus).
    _ingere_occupation(
        "maitre_philosophe", "P1066", "Q4964182",
        "Wikidata/QLever — maître du philosophe P1066 (« élève de », occupation philosophe ; multi-maître -> HORS)")


@_t12("mouvement_philosophe")
def ingere_mouvement_philosophe():
    # philosophe (P106 Q4964182) -> son MOUVEMENT/courant de pensée (P135 « mouvement », valeur = le courant).
    # C'est la version HONNÊTE de ecole_philosophe (P1416 rejeté) : P135 ne rend QUE de vrais courants —
    # stoïcisme/épicurisme/cynisme/platonisme/néoplatonisme/marxisme/philosophie analytique… AUCUNE contamination
    # (départements universitaires / partis / think tanks absents, contrairement à P1416). Probe : 1134 entités,
    # fonctionnel 78 %, top-15 = courants purs. Multi-mouvement (Sartre : existentialisme/marxisme/phénoménologie ;
    # Russell : analytique/libre-pensée) -> fonctionnel -> HORS = sûr. Reste les mono-courant nets.
    _ingere_occupation(
        "mouvement_philosophe", "P135", "Q4964182",
        "Wikidata/QLever — mouvement/courant du philosophe P135 (occupation philosophe ; multi-courant -> HORS)")


# ---- ATTRIBUTS ICONOGRAPHIQUES DES DIVINITÉS (« moi-source » : Wikidata n'expose pas ces propriétés
#      proprement → savoir canonique curé + vérifié adversarialement ; FAUX=0 conservateur, multi -> HORS) ----
#
# Vérification adversariale 2026-06-26 (agent sceptique) : 24 CONFIRM / 3 REJECT. ÉCARTÉS (doute réel) :
#   Durga->tigre (monture primaire = LION, tigre régional) ; Shani->corbeau (montures concurrentes, pas de
#   standard) ; Héphaïstos->marteau (outil de forge, pas une arme de combat maniée — relation mal appliquée).

_MONTURE_DIVINITE = [
    # Vâhana hindous (canoniques, une monture par divinité) + montures mythologiques nordiques
    ("Vishnou", "Garuda"), ("Shiva", "Nandi"), ("Brahma", "Hamsa"), ("Ganesh", "Mûshika"),
    ("Indra", "Airavata"), ("Kârttikeya", "paon"), ("Yama", "buffle"), ("Agni", "bélier"),
    ("Saraswati", "Hamsa"), ("Lakshmi", "chouette"), ("Varuna", "Makara"), ("Kâma", "perroquet"),
    ("Odin", "Sleipnir"),
]

_ARME_DIVINITE = [
    # Arme signature (de combat) — gréco-romain, nordique, hindou ; canonique non disputé
    ("Zeus", "foudre"), ("Poséidon", "trident"), ("Apollon", "arc"), ("Arès", "lance"),
    ("Thor", "Mjöllnir"), ("Odin", "Gungnir"), ("Indra", "Vajra"), ("Shiva", "trishula"),
    ("Héraclès", "massue"), ("Artémis", "arc"), ("Athéna", "lance"),
]


# Saints — Wikidata class-based inopérant (saint = P31 humain, pas une classe peuplée) → « moi-source ».
# Vérification adversariale 2026-06-26 : 30 CONFIRM / 3 REJECT. ÉCARTÉS (multi-patronage co-canonique) :
#   Saint Luc->médecins (ET peintres) ; Saint Nicolas->enfants (ET marins) ; Saint Michel->parachutistes (étroit).
_ATTRIBUT_SAINT = [
    # Attribut iconographique primaire (hagiographie : par quoi le saint est identifié dans l'art chrétien)
    ("Saint Pierre", "clés"), ("Saint Laurent", "gril"), ("Sainte Catherine d'Alexandrie", "roue"),
    ("Saint Sébastien", "flèches"), ("Saint Jérôme", "lion"), ("Sainte Lucie", "yeux"),
    ("Saint Roch", "chien"), ("Saint Jacques le Majeur", "coquille"), ("Sainte Barbe", "tour"),
    ("Saint Georges", "dragon"), ("Sainte Agathe", "seins"), ("Saint André", "croix en X"),
    ("Sainte Apolline", "tenailles"), ("Saint Denis", "tête (céphalophore)"),
    ("Saint Antoine le Grand", "cochon"), ("Sainte Cécile", "orgue"), ("Saint Hubert", "cerf"),
    ("Saint Jean-Baptiste", "agneau"),
]

_PATRONAGE_SAINT = [
    # Patronage primaire dominant (saint patron de …) ; multi-patronage co-canonique -> écarté à la vérif
    ("Saint Christophe", "voyageurs"), ("Saint Jude", "causes désespérées"), ("Sainte Cécile", "musiciens"),
    ("Saint Florian", "pompiers"), ("Saint Éloi", "orfèvres"), ("Saint Crépin", "cordonniers"),
    ("Saint Yves", "juristes"), ("Saint Hubert", "chasseurs"), ("Saint Antoine de Padoue", "objets perdus"),
    ("Sainte Apolline", "dentistes"), ("Saint Blaise", "maux de gorge"), ("Saint Vincent", "vignerons"),
]


@_t12("attribut_saint")
def ingere_attribut_saint():
    _ingere_manuel(
        "attribut_saint", _ATTRIBUT_SAINT,
        "iconographie hagiographique canonique curée (attribut d'identification ; vérifié adversarialement) — "
        "« moi-source » : saint = P31 humain, classe Wikidata inopérante")


@_t12("patronage_saint")
def ingere_patronage_saint():
    _ingere_manuel(
        "patronage_saint", _PATRONAGE_SAINT,
        "patronage primaire canonique curé (saint patron de … ; vérifié adversarialement, multi-patronage -> HORS) "
        "— « moi-source » : classe Wikidata inopérante")


# Plante sacrée & symbole-objet (gréco-romain) — « moi-source », vérif adversariale 14 CONFIRM / 6 REJECT.
# ÉCARTÉS : Héra->grenade (plutôt Perséphone), Artémis->cyprès (funéraire), Iris->arc-en-ciel (phénomène≠objet),
# Déméter->torche (ambigu Hécate), Poséidon->trident (=arme), Hadès->casque (concurrents bident/Cerbère).
_PLANTE_SACREE_DIVINITE = [
    ("Apollon", "laurier"), ("Athéna", "olivier"), ("Dionysos", "vigne"), ("Zeus", "chêne"),
    ("Aphrodite", "myrte"), ("Déméter", "blé"), ("Pan", "pin"), ("Héraclès", "peuplier"),
]

_SYMBOLE_DIVINITE = [
    # Objet-emblème primaire (NI animal [cf. animal_dieu] NI arme [cf. arme_divinite])
    ("Apollon", "lyre"), ("Hermès", "caducée"), ("Dionysos", "thyrse"),
    ("Asclépios", "bâton serpentin"), ("Hécate", "torche"), ("Pan", "flûte de Pan"),
]


# Équivalences / correspondances religieuses canoniques — « moi-source », vérif 25 CONFIRM / 1 REJECT.
# ÉCARTÉ : envie->charité (la vertu opposée à l'envie = bienveillance, pas de standard unique ; charité s'oppose
# plutôt à l'avarice).
_EQUIVALENT_GREC_DIVINITE_ROMAINE = [
    ("Jupiter", "Zeus"), ("Junon", "Héra"), ("Neptune", "Poséidon"), ("Minerve", "Athéna"),
    ("Vénus", "Aphrodite"), ("Mars", "Arès"), ("Mercure", "Hermès"), ("Diane", "Artémis"),
    ("Vulcain", "Héphaïstos"), ("Cérès", "Déméter"), ("Bacchus", "Dionysos"), ("Pluton", "Hadès"),
    ("Vesta", "Hestia"), ("Saturne", "Cronos"), ("Cupidon", "Éros"),
]

_SYMBOLE_EVANGELISTE = [
    # Tétramorphe (assignation de Jérôme, standard occidental dominant)
    ("Matthieu", "homme ailé"), ("Marc", "lion"), ("Luc", "taureau"), ("Jean", "aigle"),
]

_VERTU_OPPOSEE_PECHE = [
    # Sept péchés capitaux -> vertu opposée (théologie morale catholique)
    ("orgueil", "humilité"), ("avarice", "générosité"), ("colère", "patience"),
    ("luxure", "chasteté"), ("gourmandise", "tempérance"), ("paresse", "diligence"),
]


# Parèdre & avatars (panthéons hindou/grec/égyptien/nordique) — « moi-source », vérif 20 CONFIRM / 3 REJECT.
# ÉCARTÉS : Krishna->Radha (amante≠épouse, c'est Rukmini), Héphaïstos->Aphrodite (Hésiode dit Aglaé/Charis,
# disputé), Bouddha->Vishnou (avatar syncrétique contesté, remplacé par Balarama dans plusieurs listes vishnouites).
_PAREDE_DIVINITE = [
    # Parèdre/épouse principale (une par divinité ; multi/disputé -> écarté à la vérif)
    ("Vishnou", "Lakshmi"), ("Shiva", "Parvati"), ("Brahma", "Saraswati"), ("Rama", "Sita"),
    ("Hadès", "Perséphone"), ("Poséidon", "Amphitrite"), ("Osiris", "Isis"), ("Geb", "Nout"),
    ("Shu", "Tefnout"), ("Zeus", "Héra"), ("Odin", "Frigg"),
]

_INCARNATION_DE = [
    # Avatar/incarnation -> la divinité dont il est l'avatar (Dashavatara de Vishnou, canon vishnouite)
    ("Rama", "Vishnou"), ("Krishna", "Vishnou"), ("Narasimha", "Vishnou"), ("Vâmana", "Vishnou"),
    ("Varaha", "Vishnou"), ("Parashurama", "Vishnou"), ("Matsya", "Vishnou"), ("Kurma", "Vishnou"),
    ("Kalki", "Vishnou"),
]


# Philosophie (structure des courants/branches) — « moi-source », vérif 15 CONFIRM / 6 REJECT.
# ÉCARTÉS : cynisme->Antisthène (contesté vs Diogène), existentialisme/structuralisme/empirisme (pas de fondateur
# unique), métaphysique->l'être (recoupe ontologie), politique->le pouvoir (trop étroit, relève de science po).
_FONDATEUR_COURANT_PHILOSOPHIQUE = [
    ("stoïcisme", "Zénon de Cition"), ("épicurisme", "Épicure"), ("pyrrhonisme", "Pyrrhon d'Élis"),
    ("platonisme", "Platon"), ("aristotélisme", "Aristote"), ("néoplatonisme", "Plotin"),
    ("marxisme", "Karl Marx"), ("positivisme", "Auguste Comte"), ("utilitarisme", "Jeremy Bentham"),
    ("phénoménologie", "Edmund Husserl"),
]

_OBJET_BRANCHE_PHILOSOPHIE = [
    ("éthique", "la morale"), ("épistémologie", "la connaissance"), ("logique", "le raisonnement valide"),
    ("esthétique", "le beau"), ("ontologie", "l'être"),
]


# Religions comparées — « moi-source », vérif 17 CONFIRM / 3 REJECT.
# ÉCARTÉS : islam->croissant (symbole ottoman/politique, l'islam n'a pas de symbole unique canonique),
# jaïnisme->main (élément du Jain Prateek Chihna, pas le symbole entier), Diwali->hindouisme (fête partagée
# jaïnisme/sikhisme/bouddhisme).
_SYMBOLE_RELIGION = [
    ("christianisme", "croix"), ("judaïsme", "étoile de David"), ("bouddhisme", "roue du dharma"),
    ("hindouisme", "Om"), ("taoïsme", "yin-yang"), ("sikhisme", "Khanda"), ("zoroastrisme", "faravahar"),
]

_RELIGION_FETE = [
    # Fête religieuse -> religion d'appartenance (fêtes significativement partagées -> écartées)
    ("Noël", "christianisme"), ("Pâques", "christianisme"), ("Aïd el-Fitr", "islam"), ("Holi", "hindouisme"),
    ("Hanoucca", "judaïsme"), ("Yom Kippour", "judaïsme"), ("Vesak", "bouddhisme"),
]

_FONCTION_DIEU_TRIMURTI = [
    ("Brahma", "création"), ("Vishnou", "préservation"), ("Shiva", "destruction"),
]


# Muses / archanges / astres personnifiés — « moi-source », vérif 14 CONFIRM / 1 REJECT.
# ÉCARTÉ : Polymnie->hymnes (domaine multivalué : rhétorique/chant sacré/pantomime, pas de standard unique).
_DOMAINE_MUSE = [
    ("Calliope", "poésie épique"), ("Clio", "histoire"), ("Érato", "poésie lyrique"), ("Euterpe", "musique"),
    ("Melpomène", "tragédie"), ("Terpsichore", "danse"), ("Thalie", "comédie"), ("Uranie", "astronomie"),
]

_ROLE_ARCHANGE = [
    ("Michel", "combat"), ("Gabriel", "messager"), ("Raphaël", "guérison"),
]

_ASTRE_PERSONNIFIE = [
    ("Hélios", "Soleil"), ("Séléné", "Lune"), ("Éos", "Aurore"),
]


# Chef suprême & dieu suprême — « moi-source », vérif 6 CONFIRM / 6 REJECT (frontière : la plupart des religions
# sont décentralisées -> pas de chef suprême ; « Dieu »/« Brahman » = pas un nom propre de dieu suprême unique).
# ÉCARTÉS : bouddhisme tibétain/orthodoxe/anglicanisme/lamaïsme->chef (primus inter pares / autocéphale),
# christianisme->Dieu (appellatif générique), hindouisme->Brahman (suprême contesté Vishnou/Shiva/Devi).
_CHEF_RELIGION = [
    ("catholicisme", "pape"), ("ismaélisme nizârite", "aga khan"),
]

_DIEU_SUPREME_RELIGION = [
    ("islam", "Allah"), ("judaïsme", "YHWH"), ("zoroastrisme", "Ahura Mazda"), ("sikhisme", "Waheguru"),
]


# Histoire des idées : théorie des humeurs (Hippocrate-Galien) & alchimie classique — « moi-source », 15/15 CONFIRM.
# Conventions historiques fixées par le corpus (catégorie convention), pas des faits scientifiques littéraux.
_TEMPERAMENT_HUMEUR = [
    ("sanguin", "sang"), ("colérique", "bile jaune"), ("mélancolique", "bile noire"), ("flegmatique", "flegme"),
]

_HUMEUR_ELEMENT = [
    ("sang", "air"), ("flegme", "eau"), ("bile jaune", "feu"), ("bile noire", "terre"),
]

_METAL_PLANETE_ALCHIMIE = [
    # Septénaire alchimique classique (planète -> métal), uniforme dans la tradition
    ("Soleil", "or"), ("Lune", "argent"), ("Mars", "fer"), ("Vénus", "cuivre"),
    ("Mercure", "mercure"), ("Jupiter", "étain"), ("Saturne", "plomb"),
]


# Héros tueur de monstre (mythe grec) — « moi-source », vérif 7/8 CONFIRM. ÉCARTÉ : Sphinx->Œdipe (suicide, non tué).
# dieu_createur_mythologie ABANDONNÉ (5/6 rejetés : mythes de création pluriels, pas de créateur unique dominant —
# Ymir=géant non créateur, Chaos=vide, Atoum/Ptah/Amon concurrents, Izanagi+Izanami conjoints) = relation NON bornée.
_TUEUR_DE_MONSTRE = [
    ("Méduse", "Persée"), ("Minotaure", "Thésée"), ("Hydre de Lerne", "Héraclès"),
    ("Chimère", "Bellérophon"), ("Lion de Némée", "Héraclès"), ("Python", "Apollon"),
    ("Géryon", "Héraclès"),
]


# Fleuves des Enfers & demeures divines (mythe grec) — « moi-source », vérif 8 CONFIRM / 3 REJECT.
# ÉCARTÉS : Odin/Thor->Asgard (royaume partagé, valeur non spécifique au dieu), Héphaïstos->Lemnos (demeure
# contestée Olympe/Etna/Lemnos).
_FLEUVE_ENFERS_FONCTION = [
    ("Léthé", "oubli"), ("Styx", "serment"), ("Achéron", "douleur"),
    ("Cocyte", "lamentations"), ("Phlégéthon", "feu"),
]

_DEMEURE_DIEU = [
    ("Zeus", "Olympe"), ("Hadès", "Enfers"), ("Poséidon", "mer"),
]


@_t12("fleuve_enfers_fonction")
def ingere_fleuve_enfers_fonction():
    _ingere_manuel(
        "fleuve_enfers_fonction", _FLEUVE_ENFERS_FONCTION,
        "mythologie grecque canonique curée (fleuve des Enfers -> notion associée ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("demeure_dieu")
def ingere_demeure_dieu():
    _ingere_manuel(
        "demeure_dieu", _DEMEURE_DIEU,
        "mythologie grecque canonique curée (divinité -> demeure mythologique ; vérifié adversarialement, demeure "
        "non spécifique/contestée -> HORS) — « moi-source »")


@_t12("tueur_de_monstre")
def ingere_tueur_de_monstre():
    _ingere_manuel(
        "tueur_de_monstre", _TUEUR_DE_MONSTRE,
        "mythologie grecque canonique curée (monstre -> héros qui le vainc ; vérifié adversarialement) — « moi-source »")


@_t12("temperament_humeur")
def ingere_temperament_humeur():
    _ingere_manuel(
        "temperament_humeur", _TEMPERAMENT_HUMEUR,
        "histoire de la médecine canonique curée (tempérament -> humeur galénique ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("humeur_element")
def ingere_humeur_element():
    _ingere_manuel(
        "humeur_element", _HUMEUR_ELEMENT,
        "système hippocratico-galénique canonique curé (humeur -> élément classique ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("metal_planete_alchimie")
def ingere_metal_planete_alchimie():
    _ingere_manuel(
        "metal_planete_alchimie", _METAL_PLANETE_ALCHIMIE,
        "alchimie classique canonique curée (planète -> métal, septénaire ; vérifié adversarialement) — « moi-source »")


@_t12("chef_religion")
def ingere_chef_religion():
    _ingere_manuel(
        "chef_religion", _CHEF_RELIGION,
        "religions comparées canonique curé (religion -> chef spirituel suprême unique ; vérifié adversarialement, "
        "structures décentralisées -> HORS) — « moi-source »")


@_t12("dieu_supreme_religion")
def ingere_dieu_supreme_religion():
    _ingere_manuel(
        "dieu_supreme_religion", _DIEU_SUPREME_RELIGION,
        "religions comparées canonique curé (religion -> nom propre du dieu suprême ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("domaine_muse")
def ingere_domaine_muse():
    _ingere_manuel(
        "domaine_muse", _DOMAINE_MUSE,
        "mythologie grecque canonique curée (Muse -> art présidé ; vérifié adversarialement) — « moi-source »")


@_t12("role_archange")
def ingere_role_archange():
    _ingere_manuel(
        "role_archange", _ROLE_ARCHANGE,
        "angélologie abrahamique canonique curée (archange -> rôle principal ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("astre_personnifie")
def ingere_astre_personnifie():
    _ingere_manuel(
        "astre_personnifie", _ASTRE_PERSONNIFIE,
        "mythologie grecque canonique curée (divinité -> astre personnifié ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("symbole_religion")
def ingere_symbole_religion():
    _ingere_manuel(
        "symbole_religion", _SYMBOLE_RELIGION,
        "religions comparées canonique curé (religion -> symbole primaire ; vérifié adversarialement) — « moi-source »")


@_t12("religion_fete")
def ingere_religion_fete():
    _ingere_manuel(
        "religion_fete", _RELIGION_FETE,
        "religions comparées canonique curé (fête -> religion ; vérifié adversarialement, fête partagée -> HORS) — "
        "« moi-source »")


@_t12("fonction_dieu_trimurti")
def ingere_fonction_dieu_trimurti():
    _ingere_manuel(
        "fonction_dieu_trimurti", _FONCTION_DIEU_TRIMURTI,
        "hindouisme canonique curé (divinité de la Trimurti -> fonction cosmique ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("fondateur_courant_philosophique")
def ingere_fondateur_courant_philosophique():
    _ingere_manuel(
        "fondateur_courant_philosophique", _FONDATEUR_COURANT_PHILOSOPHIQUE,
        "histoire de la philosophie canonique curée (courant -> fondateur ; vérifié adversarialement, contesté -> "
        "HORS) — « moi-source » ; pendant inverse de mouvement_philosophe")


@_t12("objet_branche_philosophie")
def ingere_objet_branche_philosophie():
    _ingere_manuel(
        "objet_branche_philosophie", _OBJET_BRANCHE_PHILOSOPHIE,
        "philosophie canonique curée (branche -> objet d'étude primaire ; vérifié adversarialement) — « moi-source »")


@_t12("parede_divinite")
def ingere_parede_divinite():
    _ingere_manuel(
        "parede_divinite", _PAREDE_DIVINITE,
        "savoir mythologique canonique curé (parèdre/épouse principale ; vérifié adversarialement, disputé -> HORS) "
        "— « moi-source »")


@_t12("incarnation_de")
def ingere_incarnation_de():
    _ingere_manuel(
        "incarnation_de", _INCARNATION_DE,
        "savoir hindou canonique curé (avatar -> divinité source, Dashavatara ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("equivalent_grec_divinite_romaine")
def ingere_equivalent_grec_divinite_romaine():
    _ingere_manuel(
        "equivalent_grec_divinite_romaine", _EQUIVALENT_GREC_DIVINITE_ROMAINE,
        "interpretatio romana canonique curée (divinité romaine -> équivalent grec ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("symbole_evangeliste")
def ingere_symbole_evangeliste():
    _ingere_manuel(
        "symbole_evangeliste", _SYMBOLE_EVANGELISTE,
        "tétramorphe canonique curé (évangéliste -> symbole, assignation de Jérôme ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("vertu_opposee_peche")
def ingere_vertu_opposee_peche():
    _ingere_manuel(
        "vertu_opposee_peche", _VERTU_OPPOSEE_PECHE,
        "théologie morale catholique curée (péché capital -> vertu opposée ; vérifié adversarialement) — "
        "« moi-source »")


@_t12("plante_sacree_divinite")
def ingere_plante_sacree_divinite():
    _ingere_manuel(
        "plante_sacree_divinite", _PLANTE_SACREE_DIVINITE,
        "savoir mythologique canonique curé (plante/arbre sacré gréco-romain ; vérifié adversarialement) — "
        "« moi-source » : non exposé proprement par Wikidata")


@_t12("symbole_divinite")
def ingere_symbole_divinite():
    _ingere_manuel(
        "symbole_divinite", _SYMBOLE_DIVINITE,
        "savoir mythologique canonique curé (objet-emblème primaire, hors animal/arme ; vérifié adversarialement) "
        "— « moi-source » : non exposé proprement par Wikidata")


@_t12("monture_divinite")
def ingere_monture_divinite():
    _ingere_manuel(
        "monture_divinite", _MONTURE_DIVINITE,
        "savoir mythologique canonique curé (vâhana hindous + montures nordiques ; vérifié adversarialement) — "
        "« moi-source » : non exposé proprement par Wikidata")


@_t12("arme_divinite")
def ingere_arme_divinite():
    _ingere_manuel(
        "arme_divinite", _ARME_DIVINITE,
        "savoir mythologique canonique curé (arme signature de combat ; vérifié adversarialement) — "
        "« moi-source » : non exposé proprement par Wikidata")


# Défaut = relations confirmées propres (FAUX=0). REJETÉS : ecole_philosophe (P1416 affiliation = fourre-tout),
# domaine_philosophe (P101 = champ de travail générique : médecine/sociologie/journalisme mêlés, fonctionnel 55 %).
_DEFAUT = ["pere_divinite", "mere_divinite", "conjoint_divinite",
           "pere_personnage_mythique", "mere_personnage_mythique", "conjoint_personnage_mythique",
           "dedicace_edifice_religieux", "fondateur_ordre_religieux", "religion_ordre_religieux",
           "maitre_philosophe", "mouvement_philosophe",
           "monture_divinite", "arme_divinite", "attribut_saint", "patronage_saint",
           "plante_sacree_divinite", "symbole_divinite",
           "equivalent_grec_divinite_romaine", "symbole_evangeliste", "vertu_opposee_peche",
           "parede_divinite", "incarnation_de",
           "fondateur_courant_philosophique", "objet_branche_philosophie",
           "symbole_religion", "religion_fete", "fonction_dieu_trimurti",
           "domaine_muse", "role_archange", "astre_personnifie",
           "chef_religion", "dieu_supreme_religion",
           "temperament_humeur", "humeur_element", "metal_planete_alchimie", "tueur_de_monstre",
           "fleuve_enfers_fonction", "demeure_dieu"]


def main(argv):
    cibles = argv[1:] if len(argv) > 1 else list(_DEFAUT)
    inconnues = [c for c in cibles if c not in _T12]
    if inconnues:
        print(f"Relations inconnues : {inconnues}\nDisponibles : {list(_T12)}")
        return 1
    for nom in cibles:
        print(f"\n########## {nom} ##########")
        _T12[nom]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
