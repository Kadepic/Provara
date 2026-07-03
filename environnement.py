"""
ENVIRONNEMENT & PORTFOLIO POLYGLOTTE — la brique qui « trie les langages selon le besoin » (2026-07-02, vision Yohan).

IDÉE (Yohan) : en CUMULANT les langages, la frontière des fonctionnalités devient l'UNION de ce que tous les
langages présents savent faire ; l'IA n'a qu'à TRIER selon le besoin pour prendre l'excellence là où elle est
(perf native = C/Rust, écosystème data/ML = Python, web/async = JS, logique = Prolog, ensembles = SQL, flux-texte
= awk/sed…). C'est le principe PORTFOLIO (cf. routeur.py, SATzilla) appliqué au CHOIX DE LANGAGE.

RÔLE : détecter ce qui est RÉELLEMENT exécutable sur cette machine (souverain, découverte locale, zéro réseau),
mapper chaque langage à ses FORCES (registre curé = connaissance établie stable, pas du non-borné), et TRIER les
langages présents pour un besoin donné. Ce que l'IA n'a pas encore, elle sait le PROPOSER à l'installation
(`suggestions_install`) — « la seule limite = ce qui existe, et on peut installer le reste ».

FAUX=0 (invariant préservé, ce module n'émet AUCUN fait faux) :
  • Un langage est déclaré DISPONIBLE seulement si son exécutable RÉPOND réellement (which + le binaire existe) —
    jamais supposé présent. Absent -> il va dans les SUGGESTIONS d'installation, jamais dans les disponibles.
  • `pour_besoin()` ne retourne QUE des langages présents (aucune promesse sur l'absent).
  • Le multi-langage ne change PAS l'invariant du reste : le CHOIX de langage n'affirme rien ; c'est le JUGE
    (juge.py + Executeur) qui tranche PASS/FAIL par exécution réelle contre held-out, quel que soit le langage.
Stdlib pur (shutil/subprocess), déterministe, caché.
"""
from __future__ import annotations

import shutil
import subprocess

# Registre CURÉ des langages : commande de détection + FORCES (tags de besoin où le langage excelle) +
# nom d'Executeur associé (executeur.EXECUTEURS) si le projet sait déjà générer/juger ce langage + commande
# d'installation suggérée si absent. Les forces sont de la connaissance d'ingénierie ÉTABLIE (stable), pas un avis.
RUNTIMES: dict[str, dict] = {
    "python":     {"cmd": "python3", "executeur": "python",
                   "forces": ("general", "ecosysteme", "data", "ml", "scripting", "prototypage"),
                   "install": "sudo apt-get install -y python3"},
    "javascript": {"cmd": "node", "executeur": "javascript",
                   "forces": ("web", "async", "json", "ui", "scripting"),
                   "install": "sudo apt-get install -y nodejs npm"},
    "perl":       {"cmd": "perl", "executeur": "perl",
                   "forces": ("texte", "regex", "scripting"),
                   "install": "sudo apt-get install -y perl"},
    "bash":       {"cmd": "bash", "executeur": "bash",
                   "forces": ("systeme", "orchestration", "fichiers", "glue"),
                   "install": "sudo apt-get install -y bash"},
    "awk":        {"cmd": "awk", "executeur": None,
                   "forces": ("texte", "flux", "colonnes"),
                   "install": "sudo apt-get install -y gawk"},
    "sed":        {"cmd": "sed", "executeur": None,
                   "forces": ("texte", "flux", "substitution"),
                   "install": "sudo apt-get install -y sed"},
    "sql":        {"cmd": "sqlite3", "executeur": "sql",
                   "forces": ("donnees", "ensembles", "requetes", "jointures"),
                   "install": "sudo apt-get install -y sqlite3"},
    "jq":         {"cmd": "jq", "executeur": None,
                   "forces": ("json", "transformation"),
                   "install": "sudo apt-get install -y jq"},
    # Langages ABSENTS ici mais à fort levier une fois installés (perf native, stats, logique…) :
    "c":          {"cmd": "gcc", "executeur": "c",
                   "forces": ("perf", "natif", "systeme", "memoire"),
                   "install": "sudo apt-get install -y gcc"},
    "cpp":        {"cmd": "g++", "executeur": "cpp",
                   "forces": ("perf", "natif", "calcul", "memoire"),
                   "install": "sudo apt-get install -y g++"},
    "rust":       {"cmd": "rustc", "executeur": "rust",
                   "forces": ("perf", "natif", "surete", "concurrence"),
                   "install": "sudo apt-get install -y rustc"},
    "go":         {"cmd": "go", "executeur": "go",
                   "forces": ("perf", "concurrence", "reseau", "natif"),
                   "install": "sudo apt-get install -y golang"},
    "julia":      {"cmd": "julia", "executeur": None,
                   "forces": ("num", "calcul", "stats", "perf"),
                   "install": "sudo apt-get install -y julia"},
    "r":          {"cmd": "Rscript", "executeur": "r",
                   "forces": ("stats", "num", "donnees"),
                   "install": "sudo apt-get install -y r-base"},
    "prolog":     {"cmd": "swipl", "executeur": "prolog",
                   "forces": ("logique", "contraintes", "symbolique"),
                   "install": "sudo apt-get install -y swi-prolog"},
}

_DETECTE: dict | None = None


def _repond(cmd: str) -> bool:
    """Le binaire `cmd` est-il RÉELLEMENT exécutable ? which suffit (présence sur le PATH) — FAUX=0 : on ne
    déclare présent que ce que le système localise, jamais une supposition."""
    return shutil.which(cmd) is not None


def detecte(rafraichit: bool = False) -> dict:
    """Mappe chaque langage connu -> True/False selon sa présence RÉELLE (caché). Souverain, aucun réseau."""
    global _DETECTE
    if _DETECTE is None or rafraichit:
        _DETECTE = {lang: _repond(info["cmd"]) for lang, info in RUNTIMES.items()}
    return dict(_DETECTE)


def disponibles() -> list:
    """Langages RÉELLEMENT présents (triés). C'est l'espace d'exécution actuel de l'IA."""
    return sorted(lang for lang, present in detecte().items() if present)


def executeurs_disponibles() -> list:
    """Langages présents QUE le projet sait déjà générer/juger (ont un Executeur dans executeur.EXECUTEURS)."""
    return sorted(lang for lang in disponibles() if RUNTIMES[lang]["executeur"])


def pour_besoin(besoin: str, seulement_presents: bool = True) -> list:
    """TRI de Yohan : langages classés par adéquation à un `besoin` (tag de force : perf/web/stats/logique/
    texte/donnees/…). Par défaut ne retourne QUE des langages PRÉSENTS (FAUX=0 : aucune promesse sur l'absent) ;
    `seulement_presents=False` inclut les absents (utiles pour proposer une installation). Ordre : match du besoin
    d'abord, puis langages plus spécialisés (moins de forces = plus focalisé) avant les généralistes."""
    b = besoin.strip().lower()
    cands = disponibles() if seulement_presents else list(RUNTIMES)
    scored = [(lang, RUNTIMES[lang]["forces"]) for lang in cands if b in RUNTIMES[lang]["forces"]]
    # spécialisation croissante : peu de forces = plus focalisé sur ce besoin -> priorité ; départage alpha
    scored.sort(key=lambda lf: (len(lf[1]), lf[0]))
    return [lang for lang, _f in scored]


def suggestions_install(besoin: str | None = None) -> list:
    """Ce que l'IA POURRAIT gagner en installant : langages ABSENTS (optionnellement filtrés par `besoin`),
    avec leur commande d'installation. Répond à « la seule limite = ce qui existe, et on peut installer le reste ».
    N'installe RIEN (souverain) : propose seulement les commandes à exécuter par l'utilisateur."""
    pres = detecte()
    out = []
    for lang, info in RUNTIMES.items():
        if pres[lang]:
            continue
        if besoin is not None and besoin.strip().lower() not in info["forces"]:
            continue
        out.append({"langage": lang, "forces": list(info["forces"]), "commande": info["install"]})
    out.sort(key=lambda d: d["langage"])
    return out


def peut_installer() -> dict:
    """Capacités d'installation RÉELLES de la machine (pour savoir si `suggestions_install` est actionnable).
    FAUX=0 : on teste la présence des installateurs, on n'affirme pas la connectivité réseau (non testée ici)."""
    return {
        "apt": _repond("apt-get") or _repond("apt"),
        "npm": _repond("npm"),
        "pip": _repond("pip3") or _repond("pip"),
        "sudo": _repond("sudo"),
        "cargo": _repond("cargo"),
    }
