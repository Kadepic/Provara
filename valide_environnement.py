#!/usr/bin/env python3
"""
VALIDATION de environnement.py — portfolio polyglotte : détecte les langages présents, TRIE par besoin,
propose l'installation des absents. FAUX=0 : jamais un langage non-présent déclaré disponible.
Léger (shutil/subprocess), n'installe RIEN, ne charge pas le lecteur.
"""
from __future__ import annotations

import shutil
import sys

import environnement as E


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

    det = E.detecte()
    dispo = E.disponibles()

    # ── Détection RÉELLE (FAUX=0 : présent ⟺ le système le localise) ────────────────────────────
    check("python présent (on tourne dessus)", det.get("python") is True and "python" in dispo)
    check("DÉTECTION FIDÈLE : disponibles() == which() pour chaque langage",
          all((lang in dispo) == (shutil.which(E.RUNTIMES[lang]["cmd"]) is not None) for lang in E.RUNTIMES))
    check("FAUX=0 : un langage non localisé n'est JAMAIS dans disponibles()",
          all(shutil.which(E.RUNTIMES[lang]["cmd"]) is not None for lang in dispo))

    # ── TRI par besoin (le geste de Yohan) ──────────────────────────────────────────────────────
    web = E.pour_besoin("web")
    check("TRI : besoin 'web' -> langages présents pertinents (javascript si présent)",
          all(l in dispo for l in web) and ("javascript" in web if det.get("javascript") else True))
    texte = E.pour_besoin("texte")
    check("TRI : besoin 'texte' -> uniquement des présents", all(l in dispo for l in texte))
    check("TRI FAUX=0 : pour_besoin(présents) ne retourne QUE des présents",
          all(l in dispo for b in ("perf", "web", "stats", "logique", "texte", "donnees") for l in E.pour_besoin(b)))
    # un besoin dont AUCUN langage présent n'est spécialiste -> [] honnête (pas d'invention)
    perf_presents = E.pour_besoin("perf")
    perf_tous = E.pour_besoin("perf", seulement_presents=False)
    check("TRI : 'perf' inclut c/rust/go quand on autorise les absents",
          {"c", "rust", "go"} <= set(perf_tous))
    check("TRI FAUX=0 : les 'perf' présents ⊆ disponibles (pas de promesse sur l'absent)",
          set(perf_presents) <= set(dispo))

    # ── Executeurs réellement utilisables (présents ET connus du juge polyglotte) ─────────────────
    exe = E.executeurs_disponibles()
    check("EXECUTEURS : ⊆ disponibles ET ont un Executeur déclaré",
          all(l in dispo and E.RUNTIMES[l]["executeur"] for l in exe))
    check("EXECUTEURS : python en fait partie", "python" in exe)

    # ── Suggestions d'installation (« la seule limite = ce qui existe, on installe le reste ») ────
    sugg = E.suggestions_install()
    langs_sugg = {s["langage"] for s in sugg}
    check("INSTALL : les suggestions sont EXACTEMENT les langages absents",
          langs_sugg == {l for l in E.RUNTIMES if not det[l]})
    check("INSTALL : aucune suggestion pour un langage déjà présent",
          not (langs_sugg & set(dispo)))
    check("INSTALL : chaque suggestion porte une commande + ses forces",
          all(s["commande"] and s["forces"] for s in sugg))
    sugg_perf = {s["langage"] for s in E.suggestions_install("perf")}
    check("INSTALL : suggestions filtrées par besoin ('perf' -> compilateurs natifs si absents)",
          sugg_perf == {l for l in E.RUNTIMES if not det[l] and "perf" in E.RUNTIMES[l]["forces"]})

    # ── Capacités d'installation de la machine ────────────────────────────────────────────────────
    pi = E.peut_installer()
    check("PEUT_INSTALLER : reflète which() (apt/sudo/npm/pip/cargo)",
          pi["apt"] == (shutil.which("apt-get") is not None or shutil.which("apt") is not None)
          and pi["sudo"] == (shutil.which("sudo") is not None))

    # ── Cache idempotent ──────────────────────────────────────────────────────────────────────────
    check("CACHE : detecte() idempotent", E.detecte() == det)

    # Rapport lisible de l'état réel (utile à l'humain, pas un check)
    print(f"\n  → disponibles : {dispo}")
    print(f"  → à installer (levier) : {sorted(langs_sugg)}")

    print(f"\n=== valide_environnement : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
