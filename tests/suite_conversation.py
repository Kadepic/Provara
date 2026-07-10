# -*- coding: utf-8 -*-
"""RUNNER de la SUITE CONVERSATIONNELLE — protection automatique unique des gates de l'assistant conversationnel.

Ces validateurs (assistant de chat : grammaire, conjugaison, OCR, traduction, composition, fraîcheur, confiance,
langue, stats-NL, documents, patrons, capacités du chat) NE sont PAS dans la liste codée en dur de `_nonreg.py`
(la gate CŒUR du moteur de faits). Ce runner les lance TOUS en sous-processus isolés, avec le bon environnement,
et sort en échec (code ≠ 0) dès qu'un seul régresse. À lancer avant un commit touchant `interface/` ou une brique
conversationnelle.

Usage :  python3 tests/suite_conversation.py
FAUX=0 : chaque gate reste souverain (aucune logique de réponse ici) ; on n'agrège que des verdicts."""
from __future__ import annotations

import os
import subprocess
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)

# Gates conversationnels agrégés (ordre : léger -> lourd). Ceux déjà couverts par _nonreg (conversation,
# assistant_nl, fraicheur, restitution) sont INCLUS aussi pour faire de cette suite un contrôle COMPLET autonome.
GATES = [
    "valide_grammaire_fr", "valide_formes_verbales", "valide_ocr", "valide_traduction", "valide_composition",
    "valide_fraicheur", "valide_confiance", "valide_langue", "valide_explications", "valide_fonction_stats_nl",
    "valide_extrait_pdf", "valide_lecteur_document", "valide_interroge_donnees", "valide_faits_conversation", "valide_cinematique_nl",
    "valide_situation", "valide_pont_grandeurs", "valide_et_si_pourquoi", "valide_tete_polysemique",
    "valide_pont_electrique", "valide_pont_hydraulique", "valide_roue_energie", "valide_roues_compilees",
    "valide_graphe_roues", "valide_sujets",
    # VAGUE A (2026-07-10 nuit, mandat « traiter tout le backlog des sujets ») : 19 briques conceptuelles
    # neuves, chacune avec mécanisme exact, abstention structurelle et gate à ancres NON CIRCULAIRES.
    # Elles ferment à ZÉRO le backlog des PARTIES I et II (14 + 21 sujets non traités -> 0).
    "valide_valeurs_propres", "valide_anneaux_corps", "valide_limites_usuelles",
    "valide_logique_premier_ordre", "valide_developpement_decimal", "valide_equations_polynomiales",
    "valide_integrale_elementaire", "valide_conjectures_celebres", "valide_geometrie_hyperbolique",
    "valide_cinematique_uniformement_acceleree", "valide_energie_mecanique", "valide_rotation_solide",
    "valide_thermique", "valide_circuits_kirchhoff", "valide_induction_em", "valide_optique_geometrique",
    "valide_interferences_diffraction", "valide_effet_doppler", "valide_atome_hydrogene",
    # VAGUE B : ferment à ZÉRO le backlog des PARTIES III (chimie/matériaux), IV (Terre) et une part de V.
    "valide_configuration_electronique", "valide_proprietes_periodiques", "valide_isomerie_constitutionnelle",
    "valide_proprietes_mecaniques_materiaux", "valide_conductivite_materiaux", "valide_tectonique_plaques",
    "valide_temps_geologiques", "valide_classification_roches", "valide_cycle_eau", "valide_effet_de_serre",
    "valide_climats_biomes", "valide_expression_genique", "valide_selection_naturelle",
    "valide_reseau_trophique", "valide_etiologie_infectieuse",
    # VAGUE C : PARTIES VI a XII. (« versification_fr » non batie — limite de session — sujet NON TRAITÉ.)
    "valide_finance_actualisation", "valide_elasticite_prix", "valide_pyramide_ages",
    "valide_mobilite_sociale", "valide_compression_sans_perte", "valide_codes_correcteurs",
    "valide_musique_gammes", "valide_colorimetrie", "valide_bilan_energetique",
    "valide_reproductibilite_build", "valide_datation_radiocarbone", "valide_calendriers",
    "valide_formats_locaux", "valide_anatomie_systemes",
    "valide_apprentissage_patrons", "valide_conversation",
    "valide_capacites_chat", "valide_assistant_nl", "valide_maj", "valide_veille_structure", "valide_cablage",
    "valide_faits_appris", "valide_tronc", "valide_debiaisage", "valide_sources", "valide_sequenceur",
    "valide_atomes",                 # cliquet : aucune fonction publique orpheline (dette ia.py qui ne peut que fondre)
    # bancs de COMPRÉHENSION qui passent sur l'ÉCHANTILLON (les autres — paraphrases/synonymes/raisonnement —
    # exigent la base COMPLÈTE : trous de données sur le sample, à lancer manuellement avec LECTEUR_DATASETS_DIR).
    "banc_constructions",
]


def _env():
    e = dict(os.environ)
    # le pipeline conversationnel importe depuis interface/ + src/ + ingestion/
    pp = os.pathsep.join([os.path.join(_RACINE, "interface"), os.path.join(_RACINE, "src"),
                          os.path.join(_RACINE, "ingestion")])
    e["PYTHONPATH"] = pp + (os.pathsep + e["PYTHONPATH"] if e.get("PYTHONPATH") else "")
    import tempfile
    e.setdefault("LECTEUR_DATASETS_DIR", os.path.join(_RACINE, "datasets", "lecteur"))  # échantillon embarqué
    e.setdefault("LECTEUR_CACHE_DIR", os.path.join(tempfile.gettempdir(), "verax_suite_conv"))  # hors repo
    # journal de routage du tronc HORS ~/.verax réel : les conversations de test ne polluent pas le signal
    # d'apprentissage du séquenceur (même principe que la purge des convs de test).
    e.setdefault("TRONC_ROUTAGE_PATH", os.path.join(tempfile.gettempdir(), "verax_suite_conv", "tronc_routage.jsonl"))
    e.setdefault("IA_PLEINE", "1")
    # NB : on ne fixe PAS LECTEUR_AMORCE_SEULE — les gates qui en ont besoin (composition/traduction) le posent
    # eux-mêmes (os.environ.setdefault), sans affecter les gates qui chargent l'échantillon (capacites_chat…).
    return e


def main() -> int:
    env = _env()
    resultats = []
    echecs = 0
    print("=" * 66)
    print("SUITE CONVERSATIONNELLE — %d gates" % len(GATES))
    print("=" * 66)
    for nom in GATES:
        chemin = os.path.join(_ICI, nom + ".py")
        if not os.path.isfile(chemin):
            print("  %-30s INTROUVABLE" % nom)
            resultats.append((nom, "INTROUVABLE"))
            echecs += 1
            continue
        try:
            r = subprocess.run([sys.executable, chemin], cwd=_RACINE, env=env,
                               capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            print("  %-30s TIMEOUT" % nom)
            resultats.append((nom, "TIMEOUT"))
            echecs += 1
            continue
        # score « N/M » extrait de la dernière ligne « === ... : N/M === » si présente
        score = ""
        for ligne in reversed((r.stdout or "").splitlines()):
            if "===" in ligne and "/" in ligne:
                score = ligne.strip().strip("= ").split(":")[-1].strip()
                break
        ok = (r.returncode == 0)
        if not ok:
            echecs += 1
        marque = "OK  " if ok else "ÉCHEC"
        print("  %-30s %s %s" % (nom, marque, score))
        if not ok:                                   # en cas d'échec, montrer la fin de sortie pour diagnostiquer
            tail = "\n".join((r.stdout or "").splitlines()[-6:] + (r.stderr or "").splitlines()[-4:])
            print("    ┃ " + tail.replace("\n", "\n    ┃ "))
        resultats.append((nom, marque + " " + score))
    print("=" * 66)
    total = len(GATES)
    print("SUITE CONVERSATIONNELLE : %d/%d gates au vert" % (total - echecs, total))
    print("=" * 66)
    return 0 if echecs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
