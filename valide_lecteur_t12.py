"""
VALIDATEUR T12 — sanité FAUX=0 des relations RELIGION / MYTHOLOGIE / PHILOSOPHIE (OFFLINE).

Charge UNIQUEMENT les datasets T12 dans un Lecteur frais (léger : pas le chargement complet 10 M faits)
et vérifie, sans réseau, chaque relation = vocab OUVERT (entité→entité-nommée fonctionnelle) :
  • chaque valeur plausible (≥2 car., a une lettre) ;
  • ANCRES vérité-terrain : paires connues indépendamment (généalogie mythologique / écoles philo) résolues
    EXACTEMENT par le lecteur. `fonctionnel` (à l'ingestion) garantit déjà 1 valeur/entité (multi -> HORS),
    d'où les ancres MULTI volontairement absentes (Aphrodite : Ouranos/Zeus -> HORS = correct).
Seules les relations dont le dataset est présent sont validées (ingestion incrémentale). EXIT 0 = tout PASS.
"""
from garde_ressources import borne
# OPTIM amorce-seule : ne charge QUE les relations T12 (~0,7 k faits) dans un Lecteur frais, plus le full-load
# global des 33,5 M faits → 2 Go très large (était 8 quand l'import chargeait toute la base).
borne(max_go=2.0, max_cpu_s=900)

import json
import os
import sys
import unicodedata

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L

_DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "lecteur")
_ECHECS = []


def check(cond, message):
    print(f"  [{'OK ' if cond else 'FAIL'}] {message}")
    if not cond:
        _ECHECS.append(message)
    return cond


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _a_une_lettre(v: str) -> bool:
    return any(c.isalpha() for c in v)


# Relation -> (catégorie attendue, liste d'ancres vérité-terrain (entité, valeur attendue)).
# Les ancres MULTI-valeur sont volontairement EXCLUES (fonctionnel les met en HORS = FAUX=0).
_RELATIONS = {
    "pere_divinite": ("convention", [
        # Mythologie grecque, généalogie de référence (vérité connue indépendamment)
        ("Arès", "Zeus"), ("Athéna", "Zeus"), ("Apollon", "Zeus"), ("Artémis", "Zeus"),
        ("Héphaïstos", "Zeus"), ("Hermès", "Zeus"), ("Perséphone", "Zeus"), ("Héraclès", "Zeus"),
        ("Zeus", "Cronos"), ("Poséidon", "Cronos"), ("Hadès", "Cronos"),
        ("Héra", "Cronos"), ("Déméter", "Cronos"), ("Cronos", "Ouranos"),
    ]),
    "mere_divinite": ("convention", [
        # Mythologie grecque, généalogie de référence (vérité connue indépendamment)
        ("Apollon", "Léto"), ("Artémis", "Léto"), ("Arès", "Héra"), ("Hermès", "Maïa"),
        ("Athéna", "Métis"), ("Héphaïstos", "Héra"), ("Héraclès", "Alcmène"), ("Hébé", "Héra"),
        ("Aphrodite", "Dioné"), ("Cronos", "Gaïa"), ("Zeus", "Rhéa"), ("Poséidon", "Rhéa"),
    ]),
    "pere_personnage_mythique": ("convention", [
        # Élargissement de pere_divinite aux héros/personnages mythiques (multi-tradition -> HORS)
        ("Zeus", "Cronos"), ("Héraclès", "Zeus"), ("Énée", "Anchise"), ("Hector", "Priam"), ("Pâris", "Priam"),
    ]),
    "mere_personnage_mythique": ("convention", [
        ("Héraclès", "Alcmène"), ("Persée", "Danaé"), ("Hélène", "Léda"),
        ("Énée", "Aphrodite"), ("Hector", "Hécube"),
    ]),
    "conjoint_divinite": ("convention", [
        # Couples divins mono-conjoint (Wikidata fonctionnel ; multi -> HORS). Symétriques.
        ("Hadès", "Perséphone"), ("Perséphone", "Hadès"), ("Téthys", "Océan"), ("Océan", "Téthys"),
    ]),
    "conjoint_personnage_mythique": ("convention", [
        ("Hadès", "Perséphone"), ("Orphée", "Eurydice"), ("Tobit", "Anna"),
        ("Isis", "Osiris"), ("Nout", "Geb"),
    ]),
    "fondateur_ordre_religieux": ("convention", [
        ("ordre cistercien de la Stricte Observance", "Armand Jean Le Bouthillier de Rancé"),
        ("Congrégation des Religieuses de Jésus-Marie", "Claudine Thévenet"),
        ("Ordre des Carmes Déchaussés Séculiers", "Jean Soreth"),
        ("franciscaines clarisses", "Charles-Louis Lavigne"),
    ]),
    "religion_ordre_religieux": ("convention", [
        ("Filles de la Sagesse", "catholicisme"), ("Layène", "islam"), ("Qalandariyya", "islam"),
    ]),
    "dedicace_edifice_religieux": ("convention", [
        ("église Saint-Jean-Baptiste de Bourgoin-Jallieu", "Jean-Baptiste"),
        ("pro-cathédrale Saint-Jean-Baptiste de Calvi", "Jean-Baptiste"),
        ("chapelle de Sainte-Anne", "Anne"), ("temple de Léto", "Léto"),
        ("chapelle Saint-Antoine-de-Padoue de Carosse", "Antoine de Padoue"),
    ]),
    # ecole_philosophe (P1416) REJETÉ (FAUX=0) : affiliation = fourre-tout (universités/partis/ordres) ≠ école
    # de pensée. Non ingéré -> dataset absent -> ignoré. maitre_philosophe via occupation P106 (P31 était vide).
    "maitre_philosophe": ("convention", [
        # Lignées intellectuelles mono-maître, vérité connue indépendamment (multi-maître -> HORS = correct)
        ("Aristote", "Platon"), ("Speusippe", "Platon"), ("Plotin", "Ammonios Saccas"),
        ("Épictète", "Musonius Rufus"), ("Vinoba Bhave", "Mohandas Karamchand Gandhi"),
        ("Arcésilas de Pitane", "Cratès d'Athènes"), ("Edith Stein", "Edmund Husserl"),
    ]),
    # mouvement_philosophe (P135) : version HONNÊTE de ecole_philosophe (P1416 rejeté). Courants purs, multi-
    # courant -> HORS (Sartre/Russell absents = correct). Ancres mono-courant connues indépendamment.
    # domaine_philosophe (P101) REJETÉ (fonctionnel 55 %, mêle médecine/sociologie/journalisme) -> non ingéré.
    "mouvement_philosophe": ("convention", [
        ("Épicure", "épicurisme"), ("Zénon de Cition", "stoïcisme"), ("Pyrrhon d'Élis", "pyrrhonisme"),
        ("Diogène de Sinope", "cynisme"), ("Antisthène", "cynisme"), ("Sénèque", "stoïcisme"),
        ("Sextus Empiricus", "pyrrhonisme"), ("Hypatie", "néoplatonisme"),
    ]),
    # « moi-source » (savoir canonique curé + vérifié adversarialement). Ancres = sous-ensemble vérifié.
    "monture_divinite": ("convention", [
        ("Vishnou", "Garuda"), ("Shiva", "Nandi"), ("Ganesh", "Mûshika"),
        ("Indra", "Airavata"), ("Odin", "Sleipnir"),
    ]),
    "arme_divinite": ("convention", [
        ("Zeus", "foudre"), ("Poséidon", "trident"), ("Thor", "Mjöllnir"),
        ("Indra", "Vajra"), ("Apollon", "arc"),
    ]),
    "attribut_saint": ("convention", [
        ("Saint Pierre", "clés"), ("Saint Laurent", "gril"), ("Sainte Catherine d'Alexandrie", "roue"),
        ("Saint Sébastien", "flèches"), ("Saint Jérôme", "lion"),
    ]),
    "patronage_saint": ("convention", [
        ("Saint Florian", "pompiers"), ("Saint Éloi", "orfèvres"), ("Sainte Cécile", "musiciens"),
        ("Saint Christophe", "voyageurs"), ("Saint Vincent", "vignerons"),
    ]),
    "plante_sacree_divinite": ("convention", [
        ("Apollon", "laurier"), ("Athéna", "olivier"), ("Dionysos", "vigne"),
        ("Zeus", "chêne"), ("Aphrodite", "myrte"),
    ]),
    "symbole_divinite": ("convention", [
        ("Apollon", "lyre"), ("Hermès", "caducée"), ("Dionysos", "thyrse"),
        ("Asclépios", "bâton serpentin"), ("Hécate", "torche"),
    ]),
    "equivalent_grec_divinite_romaine": ("convention", [
        ("Jupiter", "Zeus"), ("Neptune", "Poséidon"), ("Vénus", "Aphrodite"),
        ("Mars", "Arès"), ("Mercure", "Hermès"),
    ]),
    "symbole_evangeliste": ("convention", [
        ("Marc", "lion"), ("Luc", "taureau"), ("Jean", "aigle"), ("Matthieu", "homme ailé"),
    ]),
    "vertu_opposee_peche": ("convention", [
        ("orgueil", "humilité"), ("luxure", "chasteté"), ("paresse", "diligence"),
        ("gourmandise", "tempérance"),
    ]),
    "parede_divinite": ("convention", [
        ("Vishnou", "Lakshmi"), ("Shiva", "Parvati"), ("Hadès", "Perséphone"),
        ("Osiris", "Isis"), ("Zeus", "Héra"),
    ]),
    "incarnation_de": ("convention", [
        ("Rama", "Vishnou"), ("Krishna", "Vishnou"), ("Narasimha", "Vishnou"), ("Matsya", "Vishnou"),
    ]),
    "fondateur_courant_philosophique": ("convention", [
        ("stoïcisme", "Zénon de Cition"), ("épicurisme", "Épicure"), ("platonisme", "Platon"),
        ("marxisme", "Karl Marx"), ("phénoménologie", "Edmund Husserl"),
    ]),
    "objet_branche_philosophie": ("convention", [
        ("éthique", "la morale"), ("épistémologie", "la connaissance"),
        ("logique", "le raisonnement valide"), ("esthétique", "le beau"),
    ]),
    "symbole_religion": ("convention", [
        ("christianisme", "croix"), ("judaïsme", "étoile de David"), ("bouddhisme", "roue du dharma"),
        ("hindouisme", "Om"), ("taoïsme", "yin-yang"),
    ]),
    "religion_fete": ("convention", [
        ("Noël", "christianisme"), ("Aïd el-Fitr", "islam"), ("Holi", "hindouisme"),
        ("Hanoucca", "judaïsme"),
    ]),
    "fonction_dieu_trimurti": ("convention", [
        ("Brahma", "création"), ("Vishnou", "préservation"), ("Shiva", "destruction"),
    ]),
    "domaine_muse": ("convention", [
        ("Calliope", "poésie épique"), ("Clio", "histoire"), ("Melpomène", "tragédie"),
        ("Terpsichore", "danse"), ("Uranie", "astronomie"),
    ]),
    "role_archange": ("convention", [
        ("Michel", "combat"), ("Gabriel", "messager"), ("Raphaël", "guérison"),
    ]),
    "astre_personnifie": ("convention", [
        ("Hélios", "Soleil"), ("Séléné", "Lune"), ("Éos", "Aurore"),
    ]),
    "chef_religion": ("convention", [
        ("catholicisme", "pape"), ("ismaélisme nizârite", "aga khan"),
    ]),
    "dieu_supreme_religion": ("convention", [
        ("islam", "Allah"), ("judaïsme", "YHWH"), ("zoroastrisme", "Ahura Mazda"), ("sikhisme", "Waheguru"),
    ]),
    "temperament_humeur": ("convention", [
        ("sanguin", "sang"), ("colérique", "bile jaune"), ("mélancolique", "bile noire"), ("flegmatique", "flegme"),
    ]),
    "humeur_element": ("convention", [
        ("sang", "air"), ("flegme", "eau"), ("bile jaune", "feu"), ("bile noire", "terre"),
    ]),
    "metal_planete_alchimie": ("convention", [
        ("Soleil", "or"), ("Lune", "argent"), ("Mars", "fer"), ("Vénus", "cuivre"), ("Saturne", "plomb"),
    ]),
    "tueur_de_monstre": ("convention", [
        ("Méduse", "Persée"), ("Minotaure", "Thésée"), ("Hydre de Lerne", "Héraclès"),
        ("Chimère", "Bellérophon"), ("Python", "Apollon"),
    ]),
    "fleuve_enfers_fonction": ("convention", [
        ("Léthé", "oubli"), ("Styx", "serment"), ("Achéron", "douleur"),
        ("Cocyte", "lamentations"), ("Phlégéthon", "feu"),
    ]),
    "demeure_dieu": ("convention", [
        ("Zeus", "Olympe"), ("Hadès", "Enfers"), ("Poséidon", "mer"),
    ]),
}


def _charge(lec, relation, categorie):
    chemin = os.path.join(_DS, relation + ".jsonl")
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as fh:
        tete = json.loads(fh.readline())
    lec.charge_jsonl(relation, chemin, tete.get("_categorie", categorie),
                     tete.get("_source", "T12"), articles=bool(tete.get("_articles", True)))
    return lec.tables.get(relation, {})


def valide_ouvert(lec, relation, categorie, ancres):
    t = _charge(lec, relation, categorie)
    if t is None:
        print(f"-- {relation} : dataset absent (non encore ingéré) -> ignoré")
        return False
    n_ent = len(t)
    valeurs = [f.valeur for f in t.values()]
    print(f"-- {relation} : {n_ent} entités, {len(set(valeurs))} valeurs distinctes")
    check(n_ent > 0, f"{relation} : table non vide")
    check(all(len(v.strip()) >= 2 and _a_une_lettre(v) for v in valeurs),
          f"{relation} : toutes les valeurs plausibles (≥2 car., lettre)")
    if ancres:
        ok = 0
        for ent, attendu in ancres:
            f = lec.cherche(relation, ent)
            bon = f is not None and _norm(f.valeur) == _norm(attendu)
            if not bon:
                print(f"     ancre RATÉE : {ent!r} -> {f.valeur if f else 'HORS'!r} (attendu {attendu!r})")
            ok += bon
        check(ok == len(ancres), f"{relation} : {ok}/{len(ancres)} ancres vérité-terrain exactes")
    else:
        print(f"     (pas encore d'ancres renseignées pour {relation})")
    return True


def main():
    lec = L.Lecteur()
    presents = 0
    for rel, (cat, ancres) in _RELATIONS.items():
        if valide_ouvert(lec, rel, cat, ancres):
            presents += 1
    print()
    check(presents > 0, "au moins une relation T12 présente et validée")
    if _ECHECS:
        print(f"ÉCHEC : {len(_ECHECS)} check(s) en échec.")
        return 1
    print("OK : tous les checks T12 passent (FAUX=0 maintenu).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
