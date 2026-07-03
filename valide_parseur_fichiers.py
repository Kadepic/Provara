#!/usr/bin/env python3
"""
VALIDATION de parseur_fichiers.py — routeur de formats. FAUX=0 : type inconnu/binaire -> HORS (jamais deviné),
parse échoué -> ERREUR honnête, format reconnu -> contenu structuré exact. Crée des fichiers temporaires, léger.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import zipfile

import parseur_fichiers as P


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

    with tempfile.TemporaryDirectory() as d:
        def ecrire(nom, contenu, binaire=False):
            p = os.path.join(d, nom)
            with open(p, "wb" if binaire else "w", encoding=None if binaire else "utf-8") as f:
                f.write(contenu)
            return p

        # JSON
        pj = ecrire("data.json", json.dumps({"a": 1, "b": [2, 3]}))
        r = P.lit(pj)
        check("JSON -> VERIFIE, contenu = dict exact",
              r["statut"] == P.VERIFIE and r["contenu"] == {"a": 1, "b": [2, 3]})

        # CSV
        pc = ecrire("t.csv", "nom,age\nalice,30\nbob,25\n")
        r = P.lit(pc)
        check("CSV -> VERIFIE, 3 lignes dont l'en-tête",
              r["statut"] == P.VERIFIE and r["contenu"][0] == ["nom", "age"] and len(r["contenu"]) == 3)

        # XML / SVG
        px = ecrire("f.svg", '<svg width="10"><rect/></svg>')
        r = P.lit(px)
        check("SVG(XML) -> VERIFIE, racine svg", r["statut"] == P.VERIFIE and r["meta"]["racine"] == "svg")

        # INI
        pi = ecrire("c.ini", "[section]\ncle = valeur\n")
        r = P.lit(pi)
        check("INI -> VERIFIE, section/clé",
              r["statut"] == P.VERIFIE and r["contenu"]["section"]["cle"] == "valeur")

        # texte
        pt = ecrire("note.txt", "ligne1\nligne2\n")
        r = P.lit(pt)
        check("TEXTE -> VERIFIE, contenu brut", r["statut"] == P.VERIFIE and "ligne1" in r["contenu"])

        # ZIP (détecté aussi par magic bytes)
        pz = os.path.join(d, "arch.zip")
        with zipfile.ZipFile(pz, "w") as z:
            z.writestr("dedans.txt", "coucou")
        r = P.lit(pz)
        check("ZIP -> VERIFIE, liste des entrées", r["statut"] == P.VERIFIE and "dedans.txt" in r["contenu"]["entrees"])
        # magic bytes : un .zip renommé en extension inconnue reste détecté zip
        pz2 = os.path.join(d, "arch.bidon")
        os.rename(pz, pz2)
        check("MAGIC BYTES : conteneur ZIP reconnu malgré extension inconnue", P.detecte_type(pz2) == "zip")

        # SQLite
        ps = os.path.join(d, "base.sqlite")
        con = sqlite3.connect(ps)
        con.execute("CREATE TABLE t(x INTEGER)")
        con.commit(); con.close()
        r = P.lit(ps)
        check("SQLITE -> VERIFIE, liste des tables", r["statut"] == P.VERIFIE and "t" in r["contenu"]["tables"])

        # FAUX=0 : JSON malformé -> ERREUR honnête (jamais un contenu inventé)
        pjb = ecrire("bad.json", "{ pas du json")
        r = P.lit(pjb)
        check("FAUX=0 : JSON malformé -> ERREUR (raison), contenu None",
              r["statut"] == P.ERREUR and r["contenu"] is None and "meta" in r)

        # FAUX=0 : format inconnu/binaire -> HORS (on ne devine pas)
        pb = ecrire("mystere.xyz", b"\x00\x01\x02\x03binaire", binaire=True)
        r = P.lit(pb)
        check("FAUX=0 : format inconnu -> HORS (jamais un contenu deviné)",
              r["statut"] == P.HORS and r["contenu"] is None)

        # FAUX=0 : fichier introuvable -> ERREUR
        check("FAUX=0 : fichier introuvable -> ERREUR",
              P.lit(os.path.join(d, "nexiste.pas"))["statut"] == P.ERREUR)

    check("formats_supportes() se décrit honnêtement", "json" in P.formats_supportes() and "sqlite" in P.formats_supportes())

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as d2:
        pj = os.path.join(d2, "x.json")
        with open(pj, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ok": True}))
        import ia
        r = ia.lit_fichier(pj)
        check("CÂBLAGE ia.lit_fichier : JSON -> VERIFIE", r["statut"] == P.VERIFIE and r["contenu"] == {"ok": True})

    print(f"\n=== valide_parseur_fichiers : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
