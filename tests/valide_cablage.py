# -*- coding: utf-8 -*-
"""Gate CÂBLAGE — plus jamais « construit mais pas branché » (exigence Yohan, 2026-07-06 : « il faut vraiment
que tout ce qui a été construit soit câblé sinon on ne va pas s'en sortir »).

Vérifie STATIQUEMENT, à chaque exécution de la suite :
  1. ATTEIGNABILITÉ : chaque module de src/ doit être ATTEIGNABLE depuis les points d'entrée du PRODUIT
     (lance.py, verax_boot.py -> serveur -> repond -> ia/capacites/…) par la fermeture transitive des imports
     (imports paresseux dans les fonctions inclus : détection ligne à ligne). Un module que seuls les TESTS
     importent n'est PAS câblé au produit -> ROUGE, sauf s'il est dans l'allowlist AVEC une raison écrite.
  2. CAPS : chaque `def _cap_xxx` de interface/repond.py doit être RÉFÉRENCÉ ailleurs dans le fichier
     (cascade ou appel) — le bug vécu du cap météo défini mais jamais appelé devient impossible à re-livrer.
  3. PONTS assistant_nl : les fonctions d'état conversationnel (note_*, reprend_clarification, oublie_etat)
     doivent être appelées depuis interface/ (un état que personne ne consomme est mort).

FAUX=0 : l'audit ne prouve pas que le câblage est CORRECT (les bancs fonctionnels s'en chargent), il prouve
qu'aucune brique n'est ORPHELINE. Toute exception doit être assumée par écrit dans _ALLOWLIST."""
import os
import re
import sys

NONREG_SCAN_SOURCES = True   # gate-SCANNER (parcourt l'arbre des sources par chemin) : le cache de _nonreg la relance toujours


_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)

# Points d'entrée du PRODUIT (le .exe et le lancement source). Les tests/démos n'en font PAS partie.
_ENTREES = ("lance", "verax_boot", "serveur", "repond")

# Modules src/ NON atteignables ASSUMÉS : VIDE et ça doit le rester (mandat Yohan 2026-07-06 : « on ne doit
# plus avoir d'orphelin, assumé ou non — sinon c'est de la dette, et il faut 0 dette »).
_ALLOWLIST: dict = {}

_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\b|import\s+([\w.\s,]+?)(?:\s+as\s+\w+)?\s*(?:#.*)?$)")


def _modules() -> dict:
    """name -> chemin, pour src/, ingestion/, interface/ + les entrées à la racine."""
    m = {}
    for dossier in ("src", "ingestion", "interface"):
        d = os.path.join(_RACINE, dossier)
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                m[f[:-3]] = os.path.join(d, f)
    for f in ("lance.py", "verax_boot.py"):
        m[f[:-3]] = os.path.join(_RACINE, f)
    return m


def _imports_de(chemin: str) -> set:
    noms = set()
    with open(chemin, encoding="utf-8", errors="ignore") as f:
        for ligne in f:
            m = _IMPORT_RE.match(ligne)
            if not m:
                continue
            if m.group(1):
                noms.add(m.group(1).split(".")[0])
            else:
                for part in m.group(2).split(","):
                    nom = part.strip().split(" as ")[0].split(".")[0].strip()
                    if nom:
                        noms.add(nom)
    return noms


def _caables_par_le_build() -> set:
    """Modules câblés PAR LE BUILD, prouvé en LISANT build_exe.bat (« --hidden-import X ») : le manifeste
    d'analyse PyInstaller (_precharge_verax) est consommé par le bootloader du .exe, pas par un import runtime.
    Vérifié, jamais assumé — et sans TRAVERSER ses imports (ce manifeste importe tout : le traverser rendrait
    l'audit aveugle)."""
    noms = set()
    try:
        with open(os.path.join(_RACINE, "build_exe.bat"), encoding="utf-8", errors="ignore") as f:
            noms |= set(re.findall(r"--hidden-import\s+\"?([\w.]+)\"?", f.read()))
    except OSError:
        pass
    return {n.split(".")[0] for n in noms}


def main() -> int:
    mods = _modules()
    graphe = {nom: _imports_de(ch) & set(mods) for nom, ch in mods.items()}
    atteints, pile = set(), [e for e in _ENTREES if e in mods]
    while pile:
        n = pile.pop()
        if n in atteints:
            continue
        atteints.add(n)
        pile.extend(graphe.get(n, ()))
    atteints |= _caables_par_le_build() & set(mods)     # APRÈS le parcours (sinon les entrées ne sont pas traversées)
    ko = []
    src_mods = {nom for nom, ch in mods.items() if os.sep + "src" + os.sep in ch}
    for nom in sorted(src_mods - atteints):
        if nom in _ALLOWLIST:
            continue
        ko.append("ORPHELIN produit : src/%s.py (importé par aucun chemin depuis %s)" % (nom, "/".join(_ENTREES)))
    for nom in sorted(set(_ALLOWLIST) - (src_mods - atteints)):
        ko.append("ALLOWLIST périmée : %s est atteignable (retirer l'entrée)" % nom)
    # 2. CAPS de repond.py : définis => référencés ailleurs dans le fichier.
    src_repond = open(mods["repond"], encoding="utf-8").read()
    for cap in re.findall(r"^def (_cap_\w+)\(", src_repond, re.M):
        if len(re.findall(r"\b%s\b" % cap, src_repond)) < 2:
            ko.append("CAP NON CÂBLÉ : repond.%s défini mais jamais référencé (cascade ?)" % cap)
    # 3. Ponts d'état assistant_nl : consommés côté interface.
    src_iface = src_repond + open(mods["serveur"], encoding="utf-8").read()
    src_assist = open(mods["assistant_nl"], encoding="utf-8").read()
    for fn in re.findall(r"^def (note_\w+|reprend_\w+|oublie_\w+)\(", src_assist, re.M):
        if not re.search(r"\b%s\b" % fn, src_iface) and len(re.findall(r"\b%s\b" % fn, src_assist)) < 2:
            ko.append("PONT MORT : assistant_nl.%s jamais consommé (ni interface/ ni en interne)" % fn)
    for ligne in ko:
        print("  FAIL:", ligne)
    print("=== valide_cablage : %d module(s) src atteignables, %d orphelin(s) assumé(s), %d problème(s) ==="
          % (len(src_mods & atteints), len(_ALLOWLIST), len(ko)))
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
