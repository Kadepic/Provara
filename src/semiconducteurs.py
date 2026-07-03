"""
SEMI-CONDUCTEURS — borné-physique CALCULABLE par formule (mandat FAUX=0, même posture que `physique.py`).

Deux faces du borné « semi-conducteurs » :

  1) SEUIL OPTIQUE D'ABSORPTION (relation de Planck-Einstein) :
       Un photon n'est absorbé (création paire électron-trou) que si son énergie E = h·c/λ dépasse l'énergie de gap
       Eg. La longueur d'onde MAXIMALE absorbée (le « seuil ») correspond à E = Eg :
            λ_seuil = h·c / Eg                  (Eg en joules)
       Avec Eg donné en électron-volts : Eg[J] = Eg[eV]·e.  Le MÉCANISME (Planck-Einstein) est EXACT ; les trois
       constantes h, c, e sont des DONNÉES SOURCÉES (SI 2019, valeurs EXACTES par définition).
       Ancres physiques connues : Si (Eg=1.12 eV) -> λ≈1107 nm ; GaAs (Eg=1.42 eV) -> λ≈873 nm (proche IR).

  2) NATURE DU DOPAGE (table de valence, convention fixée par la réalité) :
       - un atome du groupe III (1 électron de valence de moins que Si/Ge) crée un TROU -> accepteur -> type P :
         Bore (B), Aluminium (Al), Gallium (Ga).
       - un atome du groupe V (1 électron de valence de plus) cède un électron -> donneur -> type N :
         Arsenic (As), Antimoine (Sb).
       - les LETTRES de type 'P' / 'N' désignent directement le type : type P = dopage accepteur,
         type N = dopage donneur (vrai par définition).
       NOTE d'honnêteté : le symbole chimique du phosphore est 'P', identique à la lettre de type P. Pour ne JAMAIS
       émettre d'affirmation fausse, le jeton 'P' est interprété comme la LETTRE de type (type P = accepteur, ce qui
       est vrai) ; le phosphore-élément n'est donc pas mappé (abstention -> ValueError, faux négatif toléré),
       jamais classé à tort en accepteur.

GARANTIES (vérifiées en adverse par `valide_semiconducteurs.py`) :
  - Eg ≤ 0 ou non numérique -> ValueError (jamais une longueur d'onde absurde / négative) ;
  - dopant inconnu (ou hôte comme Si, ou non-str) -> ValueError (jamais un type inventé) ;
  - déterministe ; conservateur : faux négatif (abstention/ValueError) toléré, faux POSITIF interdit.

Stdlib uniquement. Aucun chargement lourd à l'import.
"""
from __future__ import annotations

# ── CONSTANTES SOURCÉES (SI 2019 — EXACTES par définition) ───────────────────────────────────────────────────────
H_PLANCK = 6.626_070_15e-34     # J·s   — constante de Planck (exacte)
C_LUMIERE = 299_792_458.0       # m/s   — vitesse de la lumière (exacte)
E_CHARGE = 1.602_176_634e-19    # C     — charge élémentaire (exacte)

SOURCE = "constantes SI 2019 exactes (h, c, e) ; table de valence groupes III/V"

_CHIFFRES = 10  # précision honnête de sortie (les constantes h,c,e sont exactes)


def _sig(x: float, n: int = _CHIFFRES) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ── 1) SEUIL OPTIQUE ─────────────────────────────────────────────────────────────────────────────────────────────
def energie_gap_eV_vers_joule(Eg_eV) -> float:
    """Convertit une énergie de gap eV -> joules : Eg[J] = Eg[eV]·e.  Eg_eV ≤ 0 -> ValueError."""
    if not _est_reel(Eg_eV) or Eg_eV <= 0:
        raise ValueError("energie_gap : Eg doit être un réel > 0 (eV)")
    return _sig(float(Eg_eV) * E_CHARGE)


def longueur_onde_seuil(Eg_eV) -> float:
    """
    Longueur d'onde MAXIMALE absorbée (m) pour un gap Eg (eV) : λ = h·c / (Eg·e).
    C'est le seuil — au-delà de λ (photon moins énergétique que Eg), pas d'absorption interbande.
    Eg_eV ≤ 0 ou non numérique -> ValueError.
    """
    if not _est_reel(Eg_eV) or Eg_eV <= 0:
        raise ValueError("longueur_onde_seuil : Eg doit être un réel > 0 (eV)")
    eg_joule = float(Eg_eV) * E_CHARGE
    return _sig(H_PLANCK * C_LUMIERE / eg_joule)


def longueur_onde_seuil_nm(Eg_eV) -> float:
    """Idem `longueur_onde_seuil` mais exprimée en nanomètres (1 m = 1e9 nm)."""
    return _sig(longueur_onde_seuil(Eg_eV) * 1e9)


# ── 2) DOPAGE ────────────────────────────────────────────────────────────────────────────────────────────────────
ACCEPTEUR = "accepteur/type P"
DONNEUR = "donneur/type N"

# Jeton -> nature. Lettres de type ('P','N') + symboles d'éléments des groupes III (accepteurs) et V (donneurs).
# Le phosphore ('P' chimique) est volontairement ABSENT : collision avec la lettre de type P (cf. docstring).
_DOPANTS = {
    "P": ACCEPTEUR,   # LETTRE de type P  -> dopage accepteur (vrai par définition)
    "N": DONNEUR,     # LETTRE de type N  -> dopage donneur   (vrai par définition)
    "B": ACCEPTEUR,   # bore       (groupe III)
    "Al": ACCEPTEUR,  # aluminium  (groupe III)
    "Ga": ACCEPTEUR,  # gallium    (groupe III)
    "As": DONNEUR,    # arsenic    (groupe V)
    "Sb": DONNEUR,    # antimoine  (groupe V)
}


def type_dopage(dopant) -> str:
    """
    Nature du dopage d'un semi-conducteur (Si/Ge).
      - lettre de type : 'P' -> 'accepteur/type P', 'N' -> 'donneur/type N' ;
      - élément groupe III (B, Al, Ga) -> 'accepteur/type P' ;
      - élément groupe V  (As, Sb)      -> 'donneur/type N'.
    Jeton inconnu, hôte (Si, Ge), ou non-str -> ValueError (jamais un type inventé).
    """
    if not isinstance(dopant, str):
        raise ValueError("type_dopage : le dopant doit être une chaîne (symbole ou lettre de type)")
    cle = dopant.strip()
    if cle not in _DOPANTS:
        raise ValueError(f"type_dopage : dopant inconnu '{dopant}'")
    return _DOPANTS[cle]


def dopants_connus() -> tuple:
    """Liste triée des jetons reconnus (pour introspection/validation)."""
    return tuple(sorted(_DOPANTS))
