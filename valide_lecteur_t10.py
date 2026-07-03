"""
VALIDATION T10 — SPORT & COMPÉTITIONS (couloir d'ingestion). FAUX=0 INVIOLABLE.

Charge UNIQUEMENT les relations T10 dans un Lecteur frais (léger : ~160 k faits, PAS les 10 M du gate complet)
et verrouille les invariants :

  1. sport_competition (compétition -> sport, ENSEMBLE FERMÉ de disciplines) :
       • table non vide ; ratio distinct/entités très bas (fermeture confirmée DEPUIS la donnée) ;
       • toute valeur = libellé ≥2 car. avec une lettre (pas de date/nombre nu fuité) ;
       • contrôle positif : les disciplines-noyau (football, tennis, cyclisme sur route…) présentes ;
       • ANCRES vérité-terrain indépendantes (Tour de France 2000→cyclisme, Coupe du monde 1930→football).
  2. pays_equipe_nationale (équipe nationale de foot -> ÉTAT SOUVERAIN, valeur ∈ ~196 pays) :
       • toute valeur ∈ ensemble fermé de pays (≥2 car., lettre) ; nombre de valeurs distinctes ≤ ~210 ;
       • ANCRES vérité-terrain (France→France, Brésil→Brésil, Angleterre→Royaume-Uni = État souverain correct).
  3. SOUNDNESS ADVERSE : entité absente, mauvaise relation, homonyme multi-valeur -> TOUJOURS HORS (None).

`fonctionnel` (à l'ingestion) garantit déjà 1 valeur/entité (multi -> HORS). EXIT 0 = tous les checks PASS.
Lancer SEUL (1 chargement léger) en dev ; enregistrer dans _nonreg.py pour le gate.
"""
from __future__ import annotations

import json
import os
import unicodedata

from garde_ressources import borne

borne(max_go=3.0, max_cpu_s=1800)   # OPTIM amorce-seule : ne charge QUE les relations T10 (~0,73 M faits) dans un
# Lecteur frais, plus le full-load global des 33,5 M faits ; 3 Go large (était 14 quand il chargeait tout).

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L
from lecteur import HORS, VERIFIE

DOSSIER = os.path.join(os.path.dirname(__file__), "datasets", "lecteur")

RELATIONS = {
    "sport_competition":      "convention",
    "pays_equipe_nationale":  "physique",
    "vainqueur_competition":  "passe",
    "ligue_club":             "convention",   # club -> ligue (P118) via GARDE anti-homonyme
    "stade_club":             "physique",     # club -> stade (P115) via GARDE anti-homonyme (LIEU -> T1)
    "pays_competition":       "physique",     # compétition -> pays P17 (état souverain)
    "sport_equipe":           "convention",   # équipe -> sport P641 (set fermé) via GARDE anti-homonyme
    "organisateur_competition": "convention", # compétition -> organisateur P664 (vocab ouvert)
    "siege_club":             "physique",     # club -> ville-siège P159 via GARDE anti-homonyme (LIEU -> T1)
    "epreuve_sport":          "convention",   # épreuve -> sport P641 (set fermé ; clé unique)
    "ville_equipe":           "physique",     # équipe -> ville-siège P159 via GARDE anti-homonyme (LIEU -> T1)
    "pays_equipe_sport":      "physique",     # équipe -> pays souverain P17 (combo garde + filtre souverain)
    "ligue_parente_saison":   "convention",   # saison -> ligue/compétition parente P3450 (clé saison unique)
    "federation_internationale_sport": "convention",  # sport -> fédération MONDIALE (source = savoir Claude vérifié)
    "categorie_epreuve_athletisme": "convention",     # épreuve athlé -> famille (taxonomie World Athletics)
    "surface_tournoi_tennis":  "convention",          # Grand Chelem -> surface (canonique)
    "pays_sportif_athlete":    "physique",            # athlète -> pays sportif P1532 (combo garde + souverain)
}

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    return cond


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _a_une_lettre(v: str) -> bool:
    return any(c.isalpha() for c in v)


def _entete(chemin):
    with open(chemin, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if brut:
                t = json.loads(brut)
                return t.get("_categorie"), t.get("_source")
    raise ValueError(f"{chemin} : en-tête manquant")


# --- Chargement léger : seules les relations T10 dans un Lecteur frais. ---
lec = L.Lecteur()
manquants = []
for rel in RELATIONS:
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        manquants.append(rel)
        continue
    cat, src = _entete(chemin)
    lec.charge_jsonl(rel, chemin, cat, src)
check(f"DATASETS présents (aucun manquant : {manquants})", not manquants)

# ============================================================================================
# 1) sport_competition — ENSEMBLE FERMÉ de disciplines.
# ============================================================================================
t = lec.tables.get("sport_competition", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
ratio = len(distinct) / n if n else 1.0
print(f"-- sport_competition : {n} entités, {len(distinct)} valeurs distinctes, ratio={ratio:.4f}")
check(f"sport_competition : table non vide ({n})", n > 0)
check(f"sport_competition : fermeture OK (ratio {ratio:.4f} ≤ 0.05)", ratio <= 0.05)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"sport_competition : toutes valeurs ≥2 car. avec lettre [contre-ex {mauvais!r}]", mauvais is None)
NOYAU_SPORT = ["football", "tennis", "cyclisme sur route", "athletisme", "basket-ball",
               "rugby a xv", "hockey sur glace", "handball", "natation sportive"]
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_SPORT if c in presents]
check(f"sport_competition : contrôle positif {len(trouves)}/5+ disciplines-noyau ({trouves[:5]})", len(trouves) >= 5)

ANCRES_SPORT = [
    ("Tour de France 2000", "cyclisme sur route"),
    ("Coupe du monde de football 1930", "football"),
    ("Wimbledon 2023 simple quad", "tennis en fauteuil roulant"),
]
for ent, vrai in ANCRES_SPORT:
    st, f = lec.repond("sport_competition", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE sport_competition({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 2) pays_equipe_nationale — valeur ∈ ensemble fermé de PAYS (états souverains).
# ============================================================================================
t = lec.tables.get("pays_equipe_nationale", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
print(f"-- pays_equipe_nationale : {n} entités, {len(distinct)} valeurs distinctes")
check(f"pays_equipe_nationale : table non vide ({n})", n > 0)
check(f"pays_equipe_nationale : valeurs distinctes ≤ 210 (set fermé de pays : {len(distinct)})", len(distinct) <= 210)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"pays_equipe_nationale : toutes valeurs = pays plausible [contre-ex {mauvais!r}]", mauvais is None)
NOYAU_PAYS = ["france", "bresil", "allemagne", "argentine", "espagne", "italie", "japon"]
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_PAYS if c in presents]
check(f"pays_equipe_nationale : contrôle positif {len(trouves)}/4+ pays-noyau ({trouves[:5]})", len(trouves) >= 4)

ANCRES_PAYS = [
    ("équipe de France de football", "France"),
    ("équipe du Brésil de football", "Brésil"),
    ("équipe d'Allemagne de football", "Allemagne"),
    ("équipe d'Argentine de football", "Argentine"),
    ("équipe d'Angleterre de football", "Royaume-Uni"),   # nation constitutive -> État souverain (P17) = correct
]
for ent, vrai in ANCRES_PAYS:
    st, f = lec.repond("pays_equipe_nationale", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE pays_equipe_nationale({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 3) vainqueur_competition — VOCAB OUVERT (clé = édition datée UNIQUE ; valeur = vainqueur).
#    Jugé par : valeurs plausibles + ANCRES vérité-terrain (palmarès connus, vérifiés indépendamment).
#    La clé étant l'édition datée, il n'y a pas de piège homonyme (≠ ligue_club/stade_club rejetés).
# ============================================================================================
t = lec.tables.get("vainqueur_competition", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- vainqueur_competition : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"vainqueur_competition : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"vainqueur_competition : tous vainqueurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_VAINQ = [
    ("championnat d'Angleterre de football 1965-1966", "Liverpool FC"),
    ("championnat d'Italie de football 1960-1961", "Juventus FC"),
    ("Coupe du monde de football 2018", "équipe de France de football"),
    ("Ligue des champions de l'UEFA 2022-2023", "Manchester City FC"),
]
for ent, vrai in ANCRES_VAINQ:
    st, f = lec.repond("vainqueur_competition", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE vainqueur_competition({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 4) ligue_club — club -> ligue (P118) via GARDE ANTI-HOMONYME (libellés clubs mono-QID seulement).
#    L'homonyme (« Real Madrid » porté par 2 QID) est ÉCARTÉ -> HORS (vérifié en section adverse).
#    Vocab ouvert (championnats nommés). Ancres = clubs au libellé UNIQUE dont la ligue est connue.
# ============================================================================================
t = lec.tables.get("ligue_club", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- ligue_club : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"ligue_club : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"ligue_club : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
# ANCRES positives vérifiées vs vérité indépendante (clubs au libellé UNIQUE -> gardés par la garde).
# « Real Madrid CF » (libellé non ambigu) est gardé ET correct ; « Real Madrid » (ambigu, 2 QID) est écarté (cf. adverse).
ANCRES_LIGUE = [
    ("Liverpool FC", "championnat d'Angleterre de football"),
    ("Juventus FC", "championnat d'Italie de football"),
    ("Bayern Munich", "championnat d'Allemagne de football"),
    ("Real Madrid CF", "championnat d'Espagne de football"),
]
for ent, vrai in ANCRES_LIGUE:
    st, f = lec.repond("ligue_club", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE ligue_club({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 5) stade_club — club -> stade (P115) via GARDE ANTI-HOMONYME. Valeur = LIEU (vocab ouvert).
# ============================================================================================
t = lec.tables.get("stade_club", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- stade_club : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"stade_club : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"stade_club : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_STADE = [
    ("Liverpool FC", "Anfield"),
    ("Arsenal FC", "Emirates Stadium"),
    ("Real Madrid CF", "Bernabéu"),
    ("Tottenham Hotspur", "Tottenham Hotspur Stadium"),
]
for ent, vrai in ANCRES_STADE:
    st, f = lec.repond("stade_club", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE stade_club({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 6) pays_competition — compétition -> pays P17 (état souverain ; valeur ∈ ensemble fermé de pays).
# ============================================================================================
t = lec.tables.get("pays_competition", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
print(f"-- pays_competition : {n} entités, {len(distinct)} valeurs distinctes")
check(f"pays_competition : table non vide ({n})", n > 0)
check(f"pays_competition : valeurs distinctes ≤ 210 (set fermé de pays : {len(distinct)})", len(distinct) <= 210)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"pays_competition : toutes valeurs = pays plausible [contre-ex {mauvais!r}]", mauvais is None)
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_PAYS if c in presents]
check(f"pays_competition : contrôle positif {len(trouves)}/4+ pays-noyau ({trouves[:5]})", len(trouves) >= 4)
ANCRES_PAYS_COMP = [
    ("Tour de France 2020", "France"),
    ("championnat d'Espagne de football 2019-2020", "Espagne"),
    ("Open d'Australie 2020", "Australie"),
    ("championnat d'Angleterre de football 2018-2019", "Royaume-Uni"),  # Angleterre -> État souverain (P17)
]
for ent, vrai in ANCRES_PAYS_COMP:
    st, f = lec.repond("pays_competition", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE pays_competition({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 7) sport_equipe — équipe -> sport (P641, ENSEMBLE FERMÉ) via GARDE ANTI-HOMONYME.
# ============================================================================================
t = lec.tables.get("sport_equipe", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
ratio = len(distinct) / n if n else 1.0
print(f"-- sport_equipe : {n} entités, {len(distinct)} valeurs distinctes, ratio={ratio:.4f}")
check(f"sport_equipe : table non vide ({n})", n > 0)
check(f"sport_equipe : fermeture OK (ratio {ratio:.4f} ≤ 0.10)", ratio <= 0.10)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"sport_equipe : toutes valeurs ≥2 car. avec lettre [contre-ex {mauvais!r}]", mauvais is None)
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_SPORT if c in presents]
check(f"sport_equipe : contrôle positif {len(trouves)}/3+ disciplines-noyau ({trouves[:5]})", len(trouves) >= 3)
ANCRES_EQUIPE = [
    ("équipe d'Inde de cricket", "cricket"),
    ("équipe de Nouvelle-Zélande de rugby à XV", "rugby à XV"),
    ("équipe du Canada de hockey sur glace", "hockey sur glace"),
    ("équipe du Brésil de volley-ball", "volley-ball"),
]
for ent, vrai in ANCRES_EQUIPE:
    st, f = lec.repond("sport_equipe", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE sport_equipe({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 8) organisateur_competition — compétition -> organisateur (P664, vocab ouvert : fédérations/organismes).
#    Clé = compétition à libellé unique/daté (PAS la classe club infectée) ; fonctionnel rejette les multi.
# ============================================================================================
t = lec.tables.get("organisateur_competition", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- organisateur_competition : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"organisateur_competition : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"organisateur_competition : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_ORG = [
    ("Coupe du monde de football 2018", "Fédération internationale de football association"),
    ("Ligue des champions de l'UEFA 2022-2023", "Union des associations européennes de football"),
    ("1 000 kilomètres d'Imola 1983", "Fédération internationale de l'automobile"),
]
for ent, vrai in ANCRES_ORG:
    st, f = lec.repond("organisateur_competition", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE organisateur_competition({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 9) siege_club — club -> ville-siège (P159) via GARDE ANTI-HOMONYME. Valeur = LIEU (vocab ouvert).
# ============================================================================================
t = lec.tables.get("siege_club", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- siege_club : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"siege_club : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"siege_club : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_SIEGE = [
    ("Liverpool FC", "Liverpool"),
    ("Arsenal FC", "Londres"),
    ("Juventus FC", "Turin"),
    ("Real Madrid CF", "Madrid"),   # libellé propre gardé ; « Real Madrid » ambigu écarté (cf. adverse)
]
for ent, vrai in ANCRES_SIEGE:
    st, f = lec.repond("siege_club", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE siege_club({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 10) epreuve_sport — épreuve sportive -> sport (P641, ENSEMBLE FERMÉ). Clé = épreuve à libellé unique.
# ============================================================================================
t = lec.tables.get("epreuve_sport", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
ratio = len(distinct) / n if n else 1.0
print(f"-- epreuve_sport : {n} entités, {len(distinct)} valeurs distinctes, ratio={ratio:.4f}")
check(f"epreuve_sport : table non vide ({n})", n > 0)
check(f"epreuve_sport : fermeture OK (ratio {ratio:.4f} ≤ 0.10)", ratio <= 0.10)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"epreuve_sport : toutes valeurs ≥2 car. avec lettre [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_EPREUVE = [
    ("1 500 mètres féminin aux Jeux olympiques d'été de 1972", "athlétisme"),
    ("1 500 mètres féminin aux Jeux olympiques d'été de 1976", "athlétisme"),
    ("1 000 mètres masculin de patinage de vitesse sur piste courte aux Jeux olympiques d'hiver de 2022",
     "patinage de vitesse sur piste courte"),
]
for ent, vrai in ANCRES_EPREUVE:
    st, f = lec.repond("epreuve_sport", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE epreuve_sport({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 11) ville_equipe — équipe sportive -> ville-siège (P159) via GARDE ANTI-HOMONYME. Valeur = LIEU.
# ============================================================================================
t = lec.tables.get("ville_equipe", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- ville_equipe : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"ville_equipe : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"ville_equipe : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
ANCRES_VILLE_EQ = [
    ("Red Sox de Boston", "Boston"),
    ("Lakers de Los Angeles", "Los Angeles"),
    ("Bulls de Chicago", "Chicago"),
    ("Celtics de Boston", "Boston"),
]
for ent, vrai in ANCRES_VILLE_EQ:
    st, f = lec.repond("ville_equipe", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE ville_equipe({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 12) pays_equipe_sport — équipe sportive -> pays SOUVERAIN (P17, combo garde mono-QID + filtre Q3624078).
# ============================================================================================
t = lec.tables.get("pays_equipe_sport", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
print(f"-- pays_equipe_sport : {n} entités, {len(distinct)} valeurs distinctes")
check(f"pays_equipe_sport : table non vide ({n})", n > 0)
check(f"pays_equipe_sport : valeurs distinctes ≤ 210 (set fermé de pays souverains : {len(distinct)})", len(distinct) <= 210)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"pays_equipe_sport : toutes valeurs = pays plausible [contre-ex {mauvais!r}]", mauvais is None)
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_PAYS if c in presents]
check(f"pays_equipe_sport : contrôle positif {len(trouves)}/4+ pays-noyau ({trouves[:5]})", len(trouves) >= 4)
ANCRES_PAYS_EQ = [
    ("équipe d'Inde de cricket", "Inde"),
    ("équipe du Brésil de volley-ball", "Brésil"),
    ("équipe du Canada de hockey sur glace", "Canada"),
    ("équipe d'Argentine de football", "Argentine"),
    ("équipe d'Angleterre de cricket", "Royaume-Uni"),   # nation constitutive -> État souverain (P17) = correct
]
for ent, vrai in ANCRES_PAYS_EQ:
    st, f = lec.repond("pays_equipe_sport", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE pays_equipe_sport({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 13) ligue_parente_saison — saison sportive -> ligue/compétition parente (P3450, vocab ouvert ; anti-self).
# ============================================================================================
t = lec.tables.get("ligue_parente_saison", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- ligue_parente_saison : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"ligue_parente_saison : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"ligue_parente_saison : toutes valeurs plausibles (≥2 car., lettre) [contre-ex {mauvais!r}]", mauvais is None)
self_ref = next((e for e, f in t.items() if _norm(e) == _norm(f.valeur)), None)
check(f"ligue_parente_saison : aucun self-ref (entite==valeur) [contre-ex {self_ref!r}]", self_ref is None)
ANCRES_LIGUE_SAISON = [
    ("Formule 3 Euro Series 2012", "Formule 3 Euro Series"),
    ("Formule 3 Euro Series 2011", "Formule 3 Euro Series"),
    ("1 000 kilomètres de Monza 1967", "1 000 kilomètres de Monza"),
]
for ent, vrai in ANCRES_LIGUE_SAISON:
    st, f = lec.repond("ligue_parente_saison", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE ligue_parente_saison({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 14) federation_internationale_sport — sport -> fédération MONDIALE. SOURCE = SAVOIR CLAUDE vérifié (Wikidata
#     contaminé par les organes continentaux). Faits institutionnels stables, gouvernance non contestée seulement.
# ============================================================================================
t = lec.tables.get("federation_internationale_sport", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
print(f"-- federation_internationale_sport : {n} entités, {len(set(valeurs))} valeurs distinctes")
check(f"federation_internationale_sport : table non vide ({n})", n > 0)
mauvais = next((v for v in valeurs if not (len(v.strip()) >= 3 and _a_une_lettre(v))), None)
check(f"federation_internationale_sport : valeurs = noms de fédération plausibles [contre-ex {mauvais!r}]", mauvais is None)
# ANCRES vérité-terrain (savoir stable indépendant ; spot-check de faits notoires).
ANCRES_FED = [
    ("football", "Fédération internationale de football association"),
    ("basket-ball", "Fédération internationale de basket-ball"),
    ("rugby à XV", "World Rugby"),
    ("natation", "World Aquatics"),
    ("athlétisme", "World Athletics"),
    ("tennis", "Fédération internationale de tennis"),
]
for ent, vrai in ANCRES_FED:
    st, f = lec.repond("federation_internationale_sport", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE federation_internationale_sport({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 15) categorie_epreuve_athletisme — épreuve d'athlétisme -> famille (course/saut/lancer/marche/combiné).
#     SOURCE = savoir Claude (taxonomie World Athletics canonique, non débattue).
# ============================================================================================
t = lec.tables.get("categorie_epreuve_athletisme", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
print(f"-- categorie_epreuve_athletisme : {n} entités, {len(distinct)} valeurs distinctes")
check(f"categorie_epreuve_athletisme : table non vide ({n})", n > 0)
FAMILLES = {"course", "saut", "lancer", "marche", "épreuve combinée"}
hors = distinct - FAMILLES
check(f"categorie_epreuve_athletisme : valeurs ∈ ensemble fermé {FAMILLES} [hors-set {hors}]", not hors)
ANCRES_ATHLE = [
    ("100 mètres", "course"), ("saut en longueur", "saut"),
    ("lancer du poids", "lancer"), ("décathlon", "épreuve combinée"),
]
for ent, vrai in ANCRES_ATHLE:
    st, f = lec.repond("categorie_epreuve_athletisme", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE categorie_epreuve_athletisme({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 16) surface_tournoi_tennis — tournoi du Grand Chelem -> surface. SOURCE = savoir Claude (canonique).
# ============================================================================================
t = lec.tables.get("surface_tournoi_tennis", {})
n = len(t)
print(f"-- surface_tournoi_tennis : {n} entités")
check(f"surface_tournoi_tennis : table non vide ({n})", n > 0)
ANCRES_TENNIS = [
    ("Roland-Garros", "terre battue"),
    ("Tournoi de Wimbledon", "gazon"),
    ("US Open de tennis", "dur"),
    ("Open d'Australie de tennis", "dur"),
]
for ent, vrai in ANCRES_TENNIS:
    st, f = lec.repond("surface_tournoi_tennis", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE surface_tournoi_tennis({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 17) pays_sportif_athlete — athlète -> pays SOUVERAIN sportif (P1532, combo garde mono-QID + filtre Q3624078).
# ============================================================================================
t = lec.tables.get("pays_sportif_athlete", {})
n = len(t)
valeurs = [f.valeur for f in t.values()]
distinct = set(valeurs)
print(f"-- pays_sportif_athlete : {n} entités, {len(distinct)} valeurs distinctes")
check(f"pays_sportif_athlete : table non vide ({n})", n > 0)
check(f"pays_sportif_athlete : valeurs distinctes ≤ 210 (pays souverains : {len(distinct)})", len(distinct) <= 210)
mauvais = next((v for v in distinct if not (len(v.strip()) >= 2 and _a_une_lettre(v))), None)
check(f"pays_sportif_athlete : toutes valeurs = pays plausible [contre-ex {mauvais!r}]", mauvais is None)
presents = {_norm(v) for v in distinct}
trouves = [c for c in NOYAU_PAYS if c in presents]
check(f"pays_sportif_athlete : contrôle positif {len(trouves)}/4+ pays-noyau ({trouves[:5]})", len(trouves) >= 4)
ANCRES_ATHL_PAYS = [
    ("Usain Bolt", "Jamaïque"),
    ("Rafael Nadal", "Espagne"),
    ("Roger Federer", "Suisse"),
    ("LeBron James", "États-Unis"),
    ("Lionel Messi", "Argentine"),
    ("Teddy Riner", "France"),
]
for ent, vrai in ANCRES_ATHL_PAYS:
    st, f = lec.repond("pays_sportif_athlete", ent)
    bon = st == VERIFIE and f is not None and _norm(f.valeur) == _norm(vrai)
    check(f"ANCRE pays_sportif_athlete({ent!r}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# ============================================================================================
# 18) SOUNDNESS ADVERSE — entité absente / mauvaise relation -> TOUJOURS HORS.
# ============================================================================================
ADVERSE = [
    ("sport_competition", "competition-qui-nexiste-pas-zzz"),
    ("sport_competition", "équipe de France de football"),     # bonne entité d'une AUTRE relation -> HORS
    ("pays_equipe_nationale", "équipe-bidon-inexistante-zzz"),
    ("pays_equipe_nationale", "Tour de France 2000"),          # bonne entité d'une AUTRE relation -> HORS
    ("relation_inexistante_t10", "football"),
    ("ligue_club", "Real Madrid"),                             # HOMONYME (2 QID) ÉCARTÉ par la garde -> HORS
    ("stade_club", "Real Madrid"),                             # HOMONYME (2 QID) ÉCARTÉ par la garde -> HORS
    ("siege_club", "Real Madrid"),                             # HOMONYME (2 QID) ÉCARTÉ par la garde -> HORS
    ("organisateur_competition", "championnat d'Angleterre de football"),  # SELF-REF filtré (anti-self) -> HORS
    ("epreuve_sport", "Liverpool FC"),                         # un club n'est pas une épreuve -> HORS
    ("ville_equipe", "Tour de France 2000"),                   # une compétition n'est pas une équipe -> HORS
    ("vainqueur_competition", "Real Madrid"),                  # un CLUB n'est pas une édition -> HORS
    ("ligue_parente_saison", "Liverpool FC"),                  # un club n'est pas une saison -> HORS
    ("federation_internationale_sport", "boxe"),               # ABSTENTION (gouvernance contestée IBA/World Boxing) -> HORS
    ("federation_internationale_sport", "Liverpool FC"),       # un club n'est pas un sport -> HORS
    ("surface_tournoi_tennis", "US Open"),                     # « US Open » nu ambigu (tennis/golf) -> désambiguïsé -> HORS
    ("categorie_epreuve_athletisme", "natation"),              # pas une épreuve d'athlétisme -> HORS
    ("pays_sportif_athlete", "Liverpool FC"),                  # un club n'est pas un athlète -> HORS
]
for rel, ent in ADVERSE:
    st, f = lec.repond(rel, ent)
    check(f"SOUNDNESS {rel}({ent!r}) -> HORS [{st}]", st == HORS and f is None)

print(f"\n=== T10 : {ok}/{total} checks PASS ===")
if ok != total:
    raise SystemExit(1)
