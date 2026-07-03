#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERAX — out-of-the-box verification / vérification prête à l'emploi.

Run:  python3 verifie_demo.py

Runs the computation-engine validators that need NO external knowledge base
(chemistry, physics, navigation, geometry, calibration, the ia.py facade…).
Each proves FAUX=0 against external anchors. No network, no GPU, no data build.

Lance les validateurs des moteurs de calcul qui ne demandent AUCUNE base de
connaissances externe. Chacun prouve FAUX=0 contre des ancres externes.
(The full 669-check gate — python3 _nonreg.py — additionally needs the rebuilt
knowledge base; see docs/fr/VALIDATION.md.)
"""
import os
import subprocess
import sys
import time

_ROOT = os.path.dirname(os.path.abspath(__file__))

# Validators proven to run on the sample alone (no full knowledge base required).
ENGINE_VALIDATORS = [
    "valide_ia", "valide_surface_ia",              # the ia.py facade is wired
    "valide_lecteur_client",                       # the interactive fast-path (daemon) is wired
    "valide_chimie", "valide_physique", "valide_coherence_physique",
    "valide_navigation", "valide_cartographie", "valide_trigonometrie",
    "valide_geometrie2d", "valide_geometrie3d", "valide_dimensions", "valide_grandeur",
    "valide_mecanique", "valide_calcul_infinitesimal", "valide_groupes",
    "valide_arithmetique_modulaire", "valide_combinatoire",
    "valide_allen", "valide_conjugaison", "valide_references", "valide_braille",
    "valide_audio_wav", "valide_raster_png", "valide_tableur_xlsx", "valide_document_pdf",
    "valide_bayes", "valide_calibration", "valide_conformal",
    "valide_fermi", "valide_decouverte_loi",
]


def main():
    print("\n  VERAX — out-of-the-box verification (sample only, no knowledge base)\n")
    passed = failed = total_checks = 0
    t0 = time.time()
    for v in ENGINE_VALIDATORS:
        try:
            r = subprocess.run([sys.executable, os.path.join(_ROOT, "tests", f"{v}.py")],
                               capture_output=True, text=True, timeout=180,
                               env={**os.environ, "PYTHONPATH": os.pathsep.join(os.path.join(_ROOT, d) for d in ("src", "ingestion", "tests")), "VERAX_ROOT": _ROOT, "LECTEUR_DATASETS_DIR": os.path.join(_ROOT, "datasets", "lecteur")})
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"  ✗ {v:<32} ({type(e).__name__})")
            failed += 1
            continue
        # last "N/N" token = the validator's own tally
        tally = ""
        for tok in reversed(r.stdout.replace("\n", " ").split()):
            if "/" in tok and tok.replace("/", "").isdigit():
                tally = tok
                break
        if r.returncode == 0:
            passed += 1
            if tally and "/" in tally:
                try:
                    total_checks += int(tally.split("/")[1])
                except ValueError:
                    pass
            print(f"  ✓ {v:<32} {tally}")
        else:
            failed += 1
            print(f"  ✗ {v:<32} FAILED (exit {r.returncode})")

    dt = time.time() - t0
    print(f"\n  {'='*66}")
    print(f"  {passed}/{passed + failed} engine validators passed "
          f"({total_checks} individual checks) in {dt:.1f}s — 0 GPU, 0 dependencies.")
    print(f"  {'='*66}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
