"""classification_surfaces.py — Classification des surfaces CLOSES (cas 2D, entièrement résolu).

FAIT MATHÉMATIQUE ÉTABLI (théorème de classification des surfaces compactes, XIXe–XXe s.) :
toute surface close (compacte, sans bord) est, à homéomorphisme près, caractérisée par
(orientabilité, caractéristique d'Euler χ), de façon BIJECTIVE :

  • orientable     : χ = 2 - 2g, g = genre (nombre d'anses) ≥ 0
        g=0 sphère (χ=2), g=1 tore (χ=0), g=2 bitore (χ=-2), … χ pair, χ ≤ 2.
  • non-orientable : χ = 2 - k, k = genre non-orientable (nb de bonnets croisés) ≥ 1
        k=1 plan projectif (χ=1), k=2 bouteille de Klein (χ=0), … χ ≤ 1.

est_sphere(χ,orientable) = (χ==2 and orientable) est l'ANALOGUE 2D de la conjecture de
Poincaré : une surface close SIMPLEMENT CONNEXE (donc orientable et χ=2) est la sphère S².
La conjecture de Poincaré (résolue par Perelman, 2003) est l'énoncé analogue en dimension 3.

DISCIPLINE FAUX=0 : toute combinaison (χ, orientable) qui ne correspond à AUCUNE surface close
réelle (χ orientable impair, χ orientable > 2, χ non-orientable > 1, types invalides) -> ValueError.
Aucune réponse n'est inventée pour une surface inexistante.
"""


def _verifie_entree(caract_euler, orientable):
    """Valide les types. χ entier (la caractéristique d'Euler d'une surface est entière),
    orientable booléen. -> ValueError sinon."""
    if isinstance(caract_euler, bool) or not isinstance(caract_euler, int):
        raise ValueError("caract_euler doit être un entier")
    if not isinstance(orientable, bool):
        raise ValueError("orientable doit être un booléen")


def genre(caract_euler, orientable):
    """Genre de la surface close de caractéristique χ donnée.

    Orientable    : genre g (nombre d'anses) = (2 - χ)/2 ; exige χ pair et χ ≤ 2.
    Non-orientable: genre non-orientable k (nombre de bonnets croisés) = 2 - χ ; exige χ ≤ 1.

    -> ValueError si aucune surface close ne possède ce (χ, orientable).
    """
    _verifie_entree(caract_euler, orientable)
    if orientable:
        # χ = 2 - 2g  =>  g = (2 - χ)/2 ; doit être entier ≥ 0
        if caract_euler % 2 != 0:
            raise ValueError("aucune surface orientable close : χ doit être pair")
        g = (2 - caract_euler) // 2
        if g < 0:
            raise ValueError("aucune surface orientable close : χ doit être ≤ 2")
        return g
    else:
        # χ = 2 - k  =>  k = 2 - χ ; doit être ≥ 1
        k = 2 - caract_euler
        if k < 1:
            raise ValueError("aucune surface non-orientable close : χ doit être ≤ 1")
        return k


def classifie_surface(caract_euler, orientable):
    """Nom canonique de la surface close de caractéristique χ et d'orientabilité donnée.

    χ=2  orientable -> 'sphère'
    χ=0  orientable -> 'tore'
    χ<0  orientable -> 'surface orientable de genre g'  (ex. χ=-2 -> genre 2)
    χ=1  non-orientable -> 'plan projectif'
    χ=0  non-orientable -> 'bouteille de Klein'
    χ<0  non-orientable -> 'surface non-orientable de genre k'

    -> ValueError si (χ, orientable) ne désigne aucune surface close.
    """
    g = genre(caract_euler, orientable)  # valide + lève si surface inexistante
    if orientable:
        if g == 0:
            return "sphère"
        if g == 1:
            return "tore"
        return f"surface orientable de genre {g}"
    else:
        if g == 1:
            return "plan projectif"
        if g == 2:
            return "bouteille de Klein"
        return f"surface non-orientable de genre {g}"


def est_sphere(caract_euler, orientable):
    """Analogue 2D de Poincaré : la surface close est-elle la sphère S² ?
    Vrai SSI χ=2 et orientable (équivalent : surface close simplement connexe).

    Valide d'abord (χ, orientable) : une combinaison ne désignant aucune surface -> ValueError.
    """
    genre(caract_euler, orientable)  # rejette les surfaces inexistantes (FAUX=0)
    return caract_euler == 2 and orientable
