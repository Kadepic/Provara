"""
INGERE_DUMP — ingestion du DUMP COMPLET frwiktionary en STREAMING (§6.2 a, échelle pure — 2026-06-18).

Le dump français = ~3,14 Go en clair (380 Mo en .gz). On le STREAME (curl|gunzip ou fichier local) ligne par ligne
— jamais 3 Go en mémoire — en ne gardant qu'une entrée compacte par mot (1ʳᵉ occurrence, noun prioritaire). Deux
passes (adjectifs-tête, cf. convertit_kaikki) puis export du lexique noyau massif + rapport de cohérence.

Usage :
  python3 ingere_dump.py                          # streame le dump complet depuis kaikki (réseau)
  python3 ingere_dump.py --limite 50000           # borne aux N premières entrées (test/vitesse)
  python3 ingere_dump.py chemin/dump.jsonl[.gz]   # dump local
"""
from __future__ import annotations

import gzip
import json
import sys
import urllib.request

from charge_lexique import coherence, ecris
from convertit_kaikki import _passe

URL = "https://kaikki.org/frwiktionary/Fran%C3%A7ais/kaikki.org-dictionary-Fran%C3%A7ais.jsonl.gz"
SORTIE = "datasets/lexique_kaikki_full.jsonl"


def _lignes(source):
    """Itère les lignes JSONL : URL .gz (stream réseau+décompression) ou fichier local (.jsonl/.gz)."""
    if source.startswith("http"):
        resp = urllib.request.urlopen(source, timeout=120)
        for raw in gzip.GzipFile(fileobj=resp):
            yield raw.decode("utf-8", "replace")
    else:
        ouvre = gzip.open if source.endswith(".gz") else open
        with ouvre(source, "rt", encoding="utf-8") as f:
            yield from f


def _slim(e):
    """Réduit une entrée kaikki aux seuls champs utiles à convertit_entree (borne la mémoire)."""
    senses = e.get("senses") or []
    gl = (senses[0].get("glosses") if senses else None) or []
    return {"word": e.get("word"), "pos": e.get("pos"), "tags": e.get("tags"),
            "senses": [{"glosses": gl[:1]}] if gl else [],
            "hypernyms": e.get("hypernyms"), "synonyms": e.get("synonyms"), "antonyms": e.get("antonyms")}


def _mots(liens):
    return [x["word"] for x in (liens or []) if x.get("word")]


def ingere_dump(source=URL, limite=None):
    """Streame le dump -> entrées compactes : pour la taxonomie on garde 1 entrée/mot (1ʳᵉ occ., noun prioritaire),
    mais on UNIT syn/ant de TOUTES les occurrences (les antonymes vivent souvent sur le sens adjectival)."""
    best = {}                 # mot -> entrée slim retenue (nom prioritaire)
    syn_acc, ant_acc = {}, {}  # mot -> synonymes/antonymes accumulés (toutes occurrences)
    lus = 0
    for ligne in _lignes(source):
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            e = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        mot = (e.get("word") or "").strip().lower()
        pos = e.get("pos")
        if not mot or pos is None:
            continue
        syn_acc.setdefault(mot, []).extend(_mots(e.get("synonyms")))
        ant_acc.setdefault(mot, []).extend(_mots(e.get("antonyms")))
        cur = best.get(mot)
        if cur is None or (cur.get("pos") != "noun" and pos == "noun"):
            best[mot] = _slim(e)          # 1ʳᵉ occ., ou montée en grade vers un nom
        lus += 1
        if limite and lus >= limite:
            break
    entrees = []
    for mot, slim in best.items():
        slim = dict(slim)
        slim["synonyms"] = [{"word": w} for w in dict.fromkeys(syn_acc.get(mot, []))]
        slim["antonyms"] = [{"word": w} for w in dict.fromkeys(ant_acc.get(mot, []))]
        entrees.append(slim)
    base = _passe(entrees, frozenset())
    adjs = frozenset(m for m, d in base.items() if d["classe"] == "adjectif")
    return _passe(entrees, adjs) if adjs else base


def main(argv) -> int:
    source, limite = URL, None
    args = list(argv)
    if "--limite" in args:
        i = args.index("--limite")
        limite = int(args[i + 1])
        del args[i:i + 2]
    if args:
        source = args[0]
    print(f"Ingestion STREAMING depuis {'réseau' if source.startswith('http') else source}"
          f"{f' (limite {limite})' if limite else ''}…", flush=True)
    lex = ingere_dump(source, limite)
    h = coherence(lex)
    n_isa = sum(1 for d in lex.values() if d.get("hyper"))
    n_syn = sum(len(d.get("syn") or []) for d in lex.values())
    n_ant = sum(len(d.get("ant") or []) for d in lex.values())
    if lex:
        ecris(lex, SORTIE)
    print(f"Lexique : {h['entrees']} entrées | is-a={n_isa} syn={n_syn} ant={n_ant} | "
          f"acyclique={h['acyclique']} | orphelins={len(h['hyperonymes_orphelins'])}")
    print(f"Exporté -> {SORTIE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
