"""FABRIQUE_SEMANTIQUE — dataset de compréhension vérifié par l'oracle officiel (la définition = la vérité).
RAISONNÉ : hyperonymie transitive held-out confirmée par la brique. OFFICIEL : def↔mot réversible non ambigu.
AXES : genre, synonyme, antonyme présents et corrects. HONNÊTE : relation fausse jamais émise. FORMAT : JSONL."""
from __future__ import annotations
import tempfile
from pathlib import Path

import lexique_fr as L
from fabrique_semantique import _verifie, construit_paires, fabrique, resume


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    paires = construit_paires(L.LEXIQUE)
    par_axe = {}
    for axe, instr, rep in paires:
        par_axe.setdefault(axe, []).append((instr, rep))
    e_isa = L.edges_isa()

    # 1. RAISONNÉ : « chat » est une sorte de « animal » = transitif (chat->félin->mammifère->animal), confirmé brique.
    isa_oui = {(i, rep) for i, rep in par_axe.get("est_une_sorte_de", [])}
    transitif = any("chat" in i and "animal" in i for i, _ in isa_oui) and _verifie("est_un", e_isa, "chat", "animal", True)
    r.append(_check("RAISONNÉ : hyperonymie transitive « chat → animal » émise ET confirmée par la brique (juge)",
                    transitif and _verifie("est_un", e_isa, "chien", "mammifère", True)))

    # 2. OFFICIEL : la définition de « chat » renvoie au mot « chat » (réversible, non ambigu).
    defs = {rep: i for i, rep in []}  # placeholder
    mot_def = {i: rep for i, rep in par_axe.get("mot_def", [])}
    chat_def = L.LEXIQUE["chat"]["definition"]
    reversible = any(chat_def in i and rep == "chat" for i, rep in par_axe.get("mot_def", []))
    fidele = any("chat" in i and rep == chat_def for i, rep in par_axe.get("definition", []))
    r.append(_check("OFFICIEL : mot→définition fidèle ET définition→mot réversible sur « chat »", reversible and fidele))

    # 3. AXES : genre (voiture→féminin), synonyme (voiture→auto), antonyme (grand→petit).
    genre_ok = any("voiture" in i and rep == "féminin" for i, rep in par_axe.get("genre", []))
    syn_ok = any("voiture" in i and rep in ("auto", "automobile") for i, rep in par_axe.get("synonyme", []))
    ant_ok = any("grand" in i and rep == "petit" for i, rep in par_axe.get("antonyme", []))
    r.append(_check(f"AXES : genre={genre_ok}, synonyme={syn_ok}, antonyme={ant_ok}", genre_ok and syn_ok and ant_ok))

    # 4. HONNÊTE : une relation FAUSSE (« chat » est une sorte de « véhicule ») n'est PAS confirmée -> jamais émise.
    fausse_confirmee = _verifie("est_un", e_isa, "chat", "véhicule", True)
    fausse_emise = any("chat" in i and "véhicule" in i for i, _ in isa_oui)
    r.append(_check("HONNÊTE : « chat sorte de véhicule » NON confirmée par la brique ET non émise",
                    not fausse_confirmee and not fausse_emise))

    # 5. FORMAT : JSONL bien-formé, prêt entraînement.
    with tempfile.TemporaryDirectory() as d:
        sortie = Path(d) / "sens.jsonl"
        info = fabrique(L.LEXIQUE, sortie)
        rs = resume(sortie)
        r.append(_check(f"FORMAT : {info['lignes']} lignes, {len(info['axes'])} axes, bien-formé "
                        f"({rs['valides']}/{rs['lignes']})",
                        rs["lignes"] > 0 and rs["mal_formees"] == 0 and rs["lignes"] == rs["valides"]
                        and len(info["axes"]) >= 5))

    print()
    print("FABRIQUE_SEMANTIQUE VALIDÉE — 5/5." if all(r) else f"ÉCHEC — {sum(r)}/5.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
