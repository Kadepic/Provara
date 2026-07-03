"""
INGESTION PROPRIÉTÉS DES ÉLÉMENTS -> datasets/lecteur/*.jsonl  (ONLINE, lancé à la main).

SOURCE : Periodic-Table-JSON (Bowserinator, CC-BY-SA 3.0 ; GitHub raw, NON rate-limité -> tourne EN PARALLÈLE
de Wikidata sans partager de limite). Complète le tableau périodique par les propriétés PHYSIQUES STABLES :
masse atomique standard (u), électronégativité de Pauling, état physique à conditions standard.

SOUNDNESS (FAUX=0) :
  • JOINTURE LANGUE-NEUTRE : on relie chaque élément PTJSON à son NOM FRANÇAIS via le SYMBOLE chimique
    (datasets/lecteur/symbole_chimique.jsonl, issu de Wikidata) -> aucune traduction hasardeuse de noms.
  • Z 1..118 confirmés uniquement (le 119e de PTJSON = placeholder, écarté).
  • Valeurs numériques/contrôlées, telles que la source autoritative les donne ; SOURCE CITÉE ; ancres
    spot-check côté valide_lecteur (masses/électronégativités/états que je vérifie indépendamment).
  • Relations NEUVES (masse_atomique / electronegativite / etat_standard) -> pas de collision amorce ;
    réconciliation idempotente via publie().

Usage : python3 ingere_elements_ptjson.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

import json
import os
import urllib.request

import sources
from ingere_wikidata import DOSSIER, RAW, UA, publie, snapshot_brut

URL = sources.url("periodic-table-json")
PHASE_FR = {"Gas": "gaz", "Solid": "solide", "Liquid": "liquide"}
# Catégories CONFIRMÉES -> terme français contrôlé (chaque entrée vérifiée à la main). Les catégories
# « unknown, probably… » (PRÉDICTIONS pour éléments superlourds non confirmés) sont ABSENTES -> écartées
# (FAUX=0 : une prédiction n'est pas un fait). diatomic/polyatomic nonmetal -> « non-métal » (sûr).
CATEGORIE_FR = {
    "transition metal": "métal de transition",
    "post-transition metal": "métal pauvre",
    "alkali metal": "métal alcalin",
    "alkaline earth metal": "métal alcalino-terreux",
    "metalloid": "métalloïde",
    "diatomic nonmetal": "non-métal",
    "polyatomic nonmetal": "non-métal",
    "noble gas": "gaz noble",
    "lanthanide": "lanthanide",
    "actinide": "actinide",
}


def _symbole_vers_nom() -> dict[str, str]:
    """Construit {symbole -> nom_fr} depuis le dataset symbole_chimique (Wikidata FR). Jointure stable."""
    chemin = os.path.join(DOSSIER, "symbole_chimique.jsonl")
    if not os.path.exists(chemin):
        raise SystemExit("symbole_chimique.jsonl absent -> lancer d'abord : python3 ingere_wikidata.py elements")
    m: dict[str, str] = {}
    with open(chemin, encoding="utf-8") as fh:
        for ln in fh:
            o = json.loads(ln)
            if "_relation" in o:
                continue
            m[o["valeur"]] = o["entite"]            # symbole -> nom français
    return m


def _charge_ou_fetch() -> list:
    chemin = os.path.join(RAW, "ptjson.json")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as fh:
            els = json.load(fh)
        print(f"  [snapshot réutilisé : ptjson.json — {len(els)} éléments, offline]")
        return els
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    els = json.loads(urllib.request.urlopen(req, timeout=60).read())["elements"]
    snapshot_brut("ptjson", els)
    return els


def ingere():
    print("== PROPRIÉTÉS DES ÉLÉMENTS (Periodic-Table-JSON) ==")
    sym2nom = _symbole_vers_nom()
    els = _charge_ou_fetch()
    print(f"  {len(els)} éléments bruts ; jointure par symbole sur {len(sym2nom)} noms FR.")
    masse, electroneg, etat = [], [], []
    periode, groupe, fusion, ebullition, config, categorie = [], [], [], [], [], []
    affinite, ionisation, capacite = [], [], []
    apparies = 0
    for e in els:
        z = e.get("number")
        if not isinstance(z, int) or not (1 <= z <= 118):
            continue
        nom = sym2nom.get(e.get("symbol"))
        if not nom:                                  # symbole non relié à un nom FR -> HORS (jamais inventé)
            continue
        apparies += 1
        if e.get("atomic_mass") is not None:
            masse.append((nom, str(e["atomic_mass"])))
        if e.get("electronegativity_pauling") is not None:
            electroneg.append((nom, str(e["electronegativity_pauling"])))
        ph = PHASE_FR.get(e.get("phase"))
        if ph:
            etat.append((nom, ph))
        # période = ligne du tableau, non ambiguë pour les 118.
        if isinstance(e.get("period"), int):
            periode.append((nom, str(e["period"])))
        # groupe = colonne IUPAC 1..18 — SOUND uniquement hors bloc f : les lanthanides/actinides (bloc f)
        # n'ont pas de numéro de groupe standard (dispute conventionnelle) -> écartés (HORS honnête).
        if e.get("block") in ("s", "p", "d") and isinstance(e.get("group"), int) and 1 <= e["group"] <= 18:
            groupe.append((nom, str(e["group"])))
        # points de fusion / ébullition = constantes physiques en KELVIN (unité unique).
        if e.get("melt") is not None:
            fusion.append((nom, str(e["melt"])))
        if e.get("boil") is not None:
            ebullition.append((nom, str(e["boil"])))
        # configuration électronique de l'état fondamental (notation gaz noble) — capture les anomalies
        # d'Aufbau (Cr=[Ar] 3d5 4s1, Cu, Pd…) telles que mesurées. Bornée par la physique quantique.
        if e.get("electron_configuration_semantic"):
            config.append((nom, e["electron_configuration_semantic"]))
        # catégorie -> terme FR contrôlé ; les catégories prédictives (« unknown… ») sont absentes du dico -> HORS.
        cat_fr = CATEGORIE_FR.get(e.get("category"))
        if cat_fr:
            categorie.append((nom, cat_fr))
        # constantes physiques (langue-neutre, unités fixes) : affinité électronique (kJ/mol),
        # 1ʳᵉ énergie d'ionisation (kJ/mol), capacité thermique molaire (J/mol·K).
        if e.get("electron_affinity") is not None:
            affinite.append((nom, str(e["electron_affinity"])))
        ion = e.get("ionization_energies")
        if ion:
            ionisation.append((nom, str(ion[0])))
        if e.get("molar_heat") is not None:
            capacite.append((nom, str(e["molar_heat"])))
    print(f"  {apparies} éléments appariés nom_fr<-symbole.")
    SRC = "Periodic-Table-JSON (Bowserinator, CC-BY-SA 3.0)"
    publie("masse_atomique", "physique", SRC + " — masse atomique standard (u)", masse)
    publie("electronegativite", "physique", SRC + " — électronégativité (échelle de Pauling)", electroneg)
    publie("etat_standard", "physique", SRC + " — état physique à conditions standard (gaz/solide/liquide)", etat)
    publie("periode_element", "convention", SRC + " — période (ligne du tableau périodique)", periode)
    publie("groupe_element", "convention", SRC + " — groupe IUPAC 1..18 (blocs s/p/d uniquement)", groupe)
    publie("point_fusion", "physique", SRC + " — point de fusion (K)", fusion)
    publie("point_ebullition", "physique", SRC + " — point d'ébullition (K)", ebullition)
    publie("configuration_electronique", "physique",
           SRC + " — configuration électronique de l'état fondamental (notation gaz noble)", config)
    publie("categorie_element", "convention",
           SRC + " — catégorie (terme FR contrôlé ; éléments confirmés uniquement)", categorie)
    publie("affinite_electronique", "physique", SRC + " — affinité électronique (kJ/mol)", affinite)
    publie("energie_ionisation", "physique", SRC + " — 1ʳᵉ énergie d'ionisation (kJ/mol)", ionisation)
    publie("capacite_thermique_molaire", "physique", SRC + " — capacité thermique molaire (J/mol·K)", capacite)


if __name__ == "__main__":
    ingere()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
