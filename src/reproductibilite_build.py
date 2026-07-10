"""
REPRODUCTIBILITÉ D'UN BUILD — déterminisme BIT-À-BIT (empreintes SHA-256 + catalogue des causes).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est un FAIT cryptographique exact, pas une corrélation :
      – un build est REPRODUCTIBLE ssi deux exécutions indépendantes produisent des artefacts
        IDENTIQUES BIT À BIT (définition de reproducible-builds.org) ;
      – l'identité bit-à-bit se constate par SHA-256 (hashlib, stdlib) : même empreinte <=> même contenu
        (à la résistance aux collisions près — aucune collision SHA-256 n'est publiquement connue) ;
      – l'empreinte d'une ARBORESCENCE est rendue STABLE en parcourant les fichiers TRIÉS par chemin
        relatif (POSIX) et en hachant des couples (chemin, contenu) à cadrage longueur-préfixé :
        elle est donc INDÉPENDANTE de l'ordre de listage du système de fichiers — LA source classique
        de non-déterminisme des outils naïfs ;
      – tout LIEN SYMBOLIQUE (en argument ou DANS un arbre, vers fichier/dossier/cible cassée) et tout
        inode NON RÉGULIER (FIFO, socket, périphérique) -> ValueError : un lien peut viser HORS de
        l'arbre (l'empreinte dépendrait d'octets étrangers), et deux arbres aux TYPES d'inode différents
        ne sont pas identiques bit-à-bit même si les contenus lus coïncident — ABSTENTION structurelle,
        jamais un verdict faux. Le module ne juge que des arbres 100 % réguliers.
  • Le CATALOGUE des sources de non-déterminisme (`causes_connues` / `remede`) est un ensemble de FAITS
    documentés par le projet Reproducible Builds (ex. l'horodatage embarqué se neutralise par la variable
    d'environnement SOURCE_DATE_EPOCH — remède standardisé).
  • `verifie_reproductible` INFÈRE des causes suspectes des NOMS/EXTENSIONS des fichiers qui diffèrent :
    ce sont des HYPOTHÈSES explicitement marquées « hypothese: » — JAMAIS présentées comme des faits,
    car le module ne peut pas savoir POURQUOI deux octets diffèrent. Seul le verdict bit-à-bit
    (`reproductible`, `fichiers_differents`) est un FAIT.

GARANTIES (vérifiées en adverse par `valide_reproductibilite_build.py`) :
  - chemin inexistant -> ValueError ; dossier vide (aucun fichier) -> ValueError ;
  - lien symbolique (en argument, ou rencontré dans l'arbre : fichier, dossier, lien cassé, lien absolu
    vers l'extérieur) -> ValueError ; FIFO/socket dans l'arbre -> ValueError (abstention, jamais un faux) ;
  - `empreinte` sur un dossier -> ValueError ; `empreinte_arbre` sur un fichier -> ValueError ;
  - types invalides (bool, int, float, None, bytes, chaîne vide) -> ValueError ;
  - `remede` sur une cause inconnue -> ValueError (jamais un remède inventé) ;
  - deux arbres au contenu identique -> MÊME empreinte, quel que soit l'ordre de création des fichiers ;
  - un seul octet changé -> empreinte DIFFÉRENTE ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `hashlib` et `os` (stdlib).
"""
from __future__ import annotations

import hashlib
import os

SOURCE = ("définition bit-à-bit + catalogue des causes : projet Reproducible Builds "
          "(reproducible-builds.org, spéc. SOURCE_DATE_EPOCH) ; empreintes : SHA-256 (FIPS 180-4)")

_BLOC = 1 << 20  # lecture par blocs d'1 Mio : empreinte de gros fichiers sans les charger en RAM


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _exige_chemin(p, role: str) -> str:
    """Chemin : str non vide, existant sur disque, PAS un lien symbolique. Tout autre type (bool, bytes,
    None…) -> ValueError. Le lien est REFUSÉ (même valide) : son identité bit-à-bit (type d'inode, cible)
    n'est pas celle du contenu pointé — hacher la cible en silence serait un verdict faux."""
    if not isinstance(p, str) or not p:
        raise ValueError(f"{role} invalide : une chaîne de caractères non vide est requise")
    if os.path.islink(p):
        raise ValueError(f"{role} est un lien symbolique : {p!r} — abstention : un lien n'est pas "
                         "un fichier/dossier régulier, pas de verdict bit-à-bit")
    if not os.path.exists(p):
        raise ValueError(f"{role} inexistant : {p!r} (abstention : rien à hacher, jamais un faux)")
    return p


def _exige_fichier(p, role: str) -> str:
    p = _exige_chemin(p, role)
    if not os.path.isfile(p):
        raise ValueError(f"{role} n'est pas un fichier régulier : {p!r}")
    return p


def _exige_dossier(p, role: str) -> str:
    p = _exige_chemin(p, role)
    if not os.path.isdir(p):
        raise ValueError(f"{role} n'est pas un dossier : {p!r}")
    return p


# ── (a) EMPREINTES ─────────────────────────────────────────────────────────────────────────────────────────────
def empreinte(chemin: str) -> str:
    """SHA-256 hexadécimal (64 caractères) du CONTENU d'un fichier RÉGULIER.
    Fichier inexistant / dossier / lien symbolique -> ValueError (abstention)."""
    chemin = _exige_fichier(chemin, "chemin")
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(_BLOC), b""):
            h.update(bloc)
    return h.hexdigest()


def _fichiers_relatifs(dossier: str) -> list[str]:
    """Chemins relatifs (séparateur POSIX '/') de tous les fichiers RÉGULIERS, TRIÉS — ordre STABLE,
    indépendant de l'ordre de listage du système de fichiers (os.walk n'est jamais supposé trié).

    Tout LIEN SYMBOLIQUE (vers fichier, dossier, ou cible cassée) et tout inode NON RÉGULIER
    (FIFO, socket, périphérique) rencontré dans l'arbre -> ValueError : un lien peut viser HORS de
    l'arbre (l'empreinte dépendrait alors d'octets étrangers à l'arbre), et deux arbres aux types
    d'inode différents ne sont pas identiques bit-à-bit même quand les contenus lus coïncident.
    ABSTENTION plutôt qu'un verdict faux (os.path.isfile SUIT les liens : il ne suffit pas)."""
    rel = []
    for racine, dirs, fichiers in os.walk(dossier, followlinks=False):
        for nom in dirs:  # os.walk range les liens-vers-dossier dans dirs (non descendus) : refusés
            complet = os.path.join(racine, nom)
            if os.path.islink(complet):
                raise ValueError(
                    f"lien symbolique (vers dossier) dans l'arbre : "
                    f"{os.path.relpath(complet, dossier)!r} — abstention, pas de verdict bit-à-bit")
        for nom in fichiers:  # os.walk range liens-vers-fichier ET liens cassés dans fichiers
            complet = os.path.join(racine, nom)
            if os.path.islink(complet):
                raise ValueError(
                    f"lien symbolique dans l'arbre : {os.path.relpath(complet, dossier)!r} — "
                    "abstention : un lien n'est pas un fichier régulier et peut viser HORS de l'arbre")
            if not os.path.isfile(complet):
                raise ValueError(
                    f"entrée non régulière (FIFO/socket/périphérique) dans l'arbre : "
                    f"{os.path.relpath(complet, dossier)!r} — abstention, pas de verdict bit-à-bit")
            rel.append(os.path.relpath(complet, dossier).replace(os.sep, "/"))
    return sorted(rel)


def empreinte_arbre(dossier: str) -> str:
    """Empreinte SHA-256 STABLE d'une arborescence : couples (chemin relatif trié, contenu), cadrés par
    longueur (préfixe 8 octets big-endian) pour éviter toute ambiguïté de concaténation.

    INDÉPENDANTE de l'ordre de listage du système de fichiers, et fonction du SEUL contenu de l'arbre :
    tout lien symbolique ou inode non régulier dans l'arbre -> ValueError (un lien pourrait faire dépendre
    l'empreinte d'octets HORS de l'arbre). Dossier vide -> ValueError (abstention : « l'empreinte d'un
    build sans artefact » n'a pas de sens ; on refuse plutôt que de rendre un hash creux)."""
    dossier = _exige_dossier(dossier, "dossier")
    fichiers = _fichiers_relatifs(dossier)
    if not fichiers:
        raise ValueError(f"dossier vide (aucun fichier) : {dossier!r} — aucun artefact à empreinter")
    h = hashlib.sha256()
    for rel in fichiers:
        octets_chemin = rel.encode("utf-8")
        h.update(len(octets_chemin).to_bytes(8, "big"))
        h.update(octets_chemin)
        contenu = empreinte(os.path.join(dossier, rel.replace("/", os.sep))).encode("ascii")
        h.update(len(contenu).to_bytes(8, "big"))
        h.update(contenu)
    return h.hexdigest()


# ── (b) COMPARAISON ────────────────────────────────────────────────────────────────────────────────────────────
def identiques(a: str, b: str) -> bool:
    """True ssi a et b sont bit-à-bit identiques : deux FICHIERS (même SHA-256) ou deux DOSSIERS
    (même empreinte d'arbre). Mélange fichier/dossier -> ValueError (comparaison mal posée)."""
    a = _exige_chemin(a, "a")
    b = _exige_chemin(b, "b")
    if os.path.isfile(a) and os.path.isfile(b):
        return empreinte(a) == empreinte(b)
    if os.path.isdir(a) and os.path.isdir(b):
        return empreinte_arbre(a) == empreinte_arbre(b)
    raise ValueError("comparaison mal posée : a et b doivent être deux fichiers OU deux dossiers")


def diff_arbres(a: str, b: str):
    """Diff bit-à-bit de deux arborescences -> (seulement_a, seulement_b, differents), trois listes TRIÉES
    de chemins relatifs POSIX. `differents` = présents des deux côtés mais au contenu distinct."""
    a = _exige_dossier(a, "a")
    b = _exige_dossier(b, "b")
    rel_a = set(_fichiers_relatifs(a))
    rel_b = set(_fichiers_relatifs(b))
    seulement_a = sorted(rel_a - rel_b)
    seulement_b = sorted(rel_b - rel_a)
    differents = sorted(
        rel for rel in rel_a & rel_b
        if empreinte(os.path.join(a, rel.replace("/", os.sep)))
        != empreinte(os.path.join(b, rel.replace("/", os.sep)))
    )
    return (seulement_a, seulement_b, differents)


# ── (c) CATALOGUE DES SOURCES DE NON-DÉTERMINISME (faits documentés, Reproducible Builds) ──────────────────────
_REMEDES = {
    "horodatage": ("fixer SOURCE_DATE_EPOCH (variable d'environnement standardisée par "
                   "reproducible-builds.org) : tous les horodatages embarqués prennent cette date"),
    "chemin_de_build_absolu": ("bâtir dans un chemin canonique fixe, ou réécrire les chemins "
                               "(-ffile-prefix-map/-fdebug-prefix-map chez GCC/Clang)"),
    "ordre_parcours_fs": ("trier explicitement les entrées (sorted()) avant tout traitement : "
                          "ne jamais dépendre de l'ordre de listage du système de fichiers"),
    "graine_aleatoire": "fixer la graine (seed constante) ou éliminer l'aléatoire de la chaîne de build",
    "parallelisme_non_ordonne": ("fusionner les résultats des tâches parallèles dans un ordre "
                                 "déterministe (tri), indépendant de l'ordonnancement"),
    "variables_environnement": "normaliser l'environnement : LANG/LC_ALL=C.UTF-8, TZ=UTC, umask fixe",
    "numero_de_build": ("supprimer le compteur, ou le dériver du CONTENU (hash du commit) "
                        "plutôt que d'un état externe incrémental"),
    "adresses_memoire_aslr": ("ne jamais sérialiser d'adresses mémoire dans les artefacts ; "
                              "comparer après normalisation (strip/objdump déterministe)"),
}


def causes_connues() -> tuple:
    """Catalogue (trié, immuable) des sources CLASSIQUES de non-déterminisme d'un build."""
    return tuple(sorted(_REMEDES))


def remede(cause) -> str:
    """Remède documenté pour une cause du catalogue. Cause inconnue -> ValueError (jamais un remède inventé)."""
    if not isinstance(cause, str) or cause not in _REMEDES:
        raise ValueError(f"cause inconnue : {cause!r} — causes admises : {causes_connues()}")
    return _REMEDES[cause]


# ── (d) VERDICT DE REPRODUCTIBILITÉ ────────────────────────────────────────────────────────────────────────────
# Indices lexicaux -> cause suspecte. HEURISTIQUE assumée : produit des HYPOTHÈSES, pas des faits.
_INDICES = (
    ((".pyc", ".o", ".obj", ".a", ".so", ".dll", ".dylib", ".exe", ".bin"), "horodatage"),
    ((".pyc", ".o", ".obj", ".a", ".so", ".dll", ".dylib", ".exe", ".bin"), "chemin_de_build_absolu"),
    ((".zip", ".tar", ".gz", ".tgz", ".jar", ".whl", ".deb", ".rpm"), "horodatage"),
    ((".zip", ".tar", ".gz", ".tgz", ".jar", ".whl", ".deb", ".rpm"), "ordre_parcours_fs"),
    (("log", "date", "time", "horodat", "timestamp"), "horodatage"),
    (("version", "buildinfo", "buildnum", "build_id", "release"), "numero_de_build"),
    (("core", "dump", "mem"), "adresses_memoire_aslr"),
)


def _causes_suspectes(fichiers_differents) -> list[str]:
    """HYPOTHÈSES (marquées telles quelles) inférées des noms/extensions des fichiers qui diffèrent."""
    hypotheses = []
    for rel in fichiers_differents:
        nom = rel.rsplit("/", 1)[-1].lower()
        for motifs, cause in _INDICES:
            if any(nom.endswith(m) if m.startswith(".") else m in nom for m in motifs):
                ligne = f"hypothese: {cause} (indice : {rel}) — non prouvée, à confirmer par diffoscope"
                if ligne not in hypotheses:
                    hypotheses.append(ligne)
    return hypotheses


def verifie_reproductible(build1: str, build2: str) -> dict:
    """Verdict bit-à-bit sur deux répertoires de build.

    Renvoie {'reproductible': bool, 'fichiers_differents': [...], 'causes_suspectes': [...]} :
      – `reproductible` et `fichiers_differents` sont des FAITS (comparaison SHA-256) ; les fichiers
        présents d'un seul côté cassent aussi la reproductibilité et figurent dans la liste, marqués
        'seulement_build1:' / 'seulement_build2:' ;
      – `causes_suspectes` = HYPOTHÈSES inférées des noms/extensions (préfixe 'hypothese:'),
        jamais des faits : le module ne peut pas savoir POURQUOI les octets diffèrent.

    Un lien symbolique ou inode non régulier dans l'un des deux arbres -> ValueError (abstention :
    le verdict bit-à-bit ne se prouve que sur des arbres 100 % réguliers)."""
    build1 = _exige_dossier(build1, "build1")
    build2 = _exige_dossier(build2, "build2")
    if not _fichiers_relatifs(build1):
        raise ValueError(f"build1 vide (aucun fichier) : {build1!r}")
    if not _fichiers_relatifs(build2):
        raise ValueError(f"build2 vide (aucun fichier) : {build2!r}")
    seulement_a, seulement_b, differents = diff_arbres(build1, build2)
    fichiers_differents = (list(differents)
                           + [f"seulement_build1:{r}" for r in seulement_a]
                           + [f"seulement_build2:{r}" for r in seulement_b])
    return {
        "reproductible": not fichiers_differents,
        "fichiers_differents": fichiers_differents,
        "causes_suspectes": _causes_suspectes(differents + seulement_a + seulement_b),
    }
