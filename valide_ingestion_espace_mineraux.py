#!/usr/bin/env python3
"""
VALIDATION des veines ingérées 2026-07-02 (run autonome) : ESPACE (sondes) + MINÉRAUX (espèces IMA).
FAUX=0 par ANCRES EXTERNES : des faits de vérité-terrain indépendants (Voyager 1 lancé par Titan IIIE en 1977,
fluorine = CaF₂…) DOIVENT être servis exactement ; un fait FAUX ne doit PAS l'être (contrôles négatifs) ; toute
entité absente -> HORS honnête. Léger : charge UNIQUEMENT les .jsonl concernés dans un Lecteur frais (pas le corpus).
"""
from __future__ import annotations

import os
import sys

os.environ["LECTEUR_AMORCE_SEULE"] = "1"       # AVANT l'import : Lecteur léger, pas d'auto-chargement massif
import lecteur as L

_DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "lecteur")


def _lec(*relations):
    """Lecteur frais chargé des SEULES relations demandées (chemin léger, offline)."""
    lec = L.Lecteur()
    for rel in relations:
        lec.charge_jsonl(rel, os.path.join(_DS, rel + ".jsonl"),
                         "passe", "test")          # catégorie/source ignorées : l'en-tête du fichier prime pour le lookup
    return lec


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    def cherche(lec, rel, ent):
        f = lec.cherche(rel, ent)               # renvoie le Fait ou None (lookup exact, sinon HORS)
        return f.valeur if f is not None else None

    # ── ESPACE : sondes spatiales ──────────────────────────────────────────────────────────────
    esp = _lec("lanceur_sonde", "operateur_sonde", "annee_lancement_sonde", "fabricant_sonde")
    check("lanceur : Voyager 1 -> Titan IIIE", cherche(esp, "lanceur_sonde", "Voyager 1") == "Titan IIIE")
    check("lanceur : Voyager 2 -> Titan IIIE", cherche(esp, "lanceur_sonde", "Voyager 2") == "Titan IIIE")
    check("lanceur : Hayabusa -> M-V", cherche(esp, "lanceur_sonde", "Hayabusa") == "M-V")
    check("opérateur : Luna 10 -> Union soviétique",
          cherche(esp, "operateur_sonde", "Luna 10") == "Union soviétique")
    check("année : Cassini -> 1997", cherche(esp, "annee_lancement_sonde", "Cassini") == "1997")
    check("année : New Horizons -> 2006", cherche(esp, "annee_lancement_sonde", "New Horizons") == "2006")
    check("année : Voyager 1 -> 1977", cherche(esp, "annee_lancement_sonde", "Voyager 1") == "1977")
    check("FAUX=0 : sonde inexistante -> HORS", cherche(esp, "lanceur_sonde", "Millennium Falcon") is None)
    check("FAUX=0 : année de lancement toujours dans [1957,2035]",
          all(1957 <= int(f.valeur) <= 2035 for f in esp.tables["annee_lancement_sonde"].values()))

    # ── MINÉRAUX : espèces IMA ─────────────────────────────────────────────────────────────────
    mi = _lec("formule_chimique_mineral", "systeme_cristallin", "durete_mohs_mineral")
    check("formule : fluorine -> CaF₂", cherche(mi, "formule_chimique_mineral", "fluorine") == "CaF₂")
    check("formule : sphalérite -> ZnS", cherche(mi, "formule_chimique_mineral", "sphalérite") == "ZnS")
    check("formule : hématite -> Fe₂O₃", cherche(mi, "formule_chimique_mineral", "hématite") == "Fe₂O₃")
    check("formule : béryl -> Be₃Al₂Si₆O₁₈",
          cherche(mi, "formule_chimique_mineral", "béryl") == "Be₃Al₂Si₆O₁₈")
    check("système : hématite -> système cristallin trigonal",
          cherche(mi, "systeme_cristallin", "hématite") == "système cristallin trigonal")
    # dureté de Mohs : les minéraux de RÉFÉRENCE de l'échelle sortent exacts (vérité-terrain la plus dure)
    check("Mohs : talc -> 1.0 (minéral de référence)", cherche(mi, "durete_mohs_mineral", "talc") == "1.0")
    check("Mohs : quartz -> 7.0", cherche(mi, "durete_mohs_mineral", "quartz") == "7.0")
    check("Mohs : diamant -> 10.0 (max de l'échelle)", cherche(mi, "durete_mohs_mineral", "diamant") == "10.0")
    check("FAUX=0 : toute dureté de Mohs dans [1,10]",
          all(1.0 <= float(f.valeur) <= 10.0 for f in mi.tables["durete_mohs_mineral"].values()))
    check("FAUX=0 : minéral inventé -> HORS", cherche(mi, "formule_chimique_mineral", "kryptonite") is None)
    check("FAUX=0 : formule ≠ contre-valeur (fluorine n'est pas NaCl)",
          cherche(mi, "formule_chimique_mineral", "fluorine") != "NaCl")

    # ── AVIATION : premier vol des modèles d'aéronef ───────────────────────────────────────────
    av = _lec("annee_premier_vol_aeronef")
    check("aviation : Boeing 747 -> 1969", cherche(av, "annee_premier_vol_aeronef", "Boeing 747") == "1969")
    check("aviation : Supermarine Spitfire -> 1936",
          cherche(av, "annee_premier_vol_aeronef", "Supermarine Spitfire") == "1936")
    check("aviation : Boeing 707 -> 1957", cherche(av, "annee_premier_vol_aeronef", "Boeing 707") == "1957")
    check("FAUX=0 : tout premier vol dans [1900,2035]",
          all(1900 <= int(f.valeur) <= 2035 for f in av.tables["annee_premier_vol_aeronef"].values()))
    check("FAUX=0 : aéronef inventé -> HORS", cherche(av, "annee_premier_vol_aeronef", "Millennium Falcon") is None)

    print(f"\n=== valide_ingestion_espace_mineraux : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
