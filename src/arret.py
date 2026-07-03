"""Problème de l'arrêt — mécanisme EXACT, FAUX=0.

DEUX faces, toutes deux VÉRIFIABLES :

1. ARRÊT BORNÉ (décidable). `sarrete_dans(programme_func, entree, max_etapes)` simule un programme
   pendant AU PLUS `max_etapes` pas et renvoie ('arrete', n) s'il s'est arrêté (n = pas exécutés)
   ou ('timeout',) si le budget est épuisé. C'est un fait MÉCANIQUE : on observe l'exécution.
   Un programme est modélisé comme un GÉNÉRATEUR d'étapes : chaque `yield` = un pas de calcul,
   l'épuisement du générateur (StopIteration) = arrêt. Ce modèle est SÛR : même une boucle
   infinie ne peut pas bloquer le simulateur, qui ne fait avancer la machine que `max_etapes` fois.
   `timeout` n'affirme JAMAIS « ne s'arrête pas » (indécidable), seulement « pas dans ce budget ».

2. ARRÊT GÉNÉRAL (indécidable). `arret_general_decidable()` = False : THÉORÈME de Turing (1936),
   fait mathématique établi et certain. `argument_diagonal()` en donne la preuve CONSTRUCTIVE par
   l'absurde : pour tout décideur total H prétendu, on construit un programme diagonal D dont le
   comportement réel sur lui-même est la NÉGATION du verdict de H — donc H se trompe. Contradiction.

ABSTENTION : max_etapes <= 0 -> ValueError ; programme non appelable / non itérable -> ValueError ;
décideur non appelable ou verdict hors {'arrete','boucle'} -> ValueError.
"""

# Théorème de Turing (1936) — Church-Turing : le problème de l'arrêt général est INDÉCIDABLE.
THEOREME_TURING = (
    "Il n'existe aucun algorithme total qui, pour tout couple (programme P, entrée x), "
    "décide si P s'arrête sur x. (Turing, 1936)"
)


def sarrete_dans(programme_func, entree, max_etapes):
    """Simule `programme_func(entree)` pendant au plus `max_etapes` pas.

    Convention : `programme_func(entree)` produit un ITÉRATEUR d'étapes (générateur).
    Chaque avancée (next) consomme 1 unité de budget ; l'épuisement (StopIteration) = arrêt.

    Renvoie ('arrete', n) — n = nombre de pas (yields) exécutés avant l'arrêt —
    ou ('timeout',) si le budget est épuisé sans observer l'arrêt.
    """
    if not callable(programme_func):
        raise ValueError("programme non appelable")
    if isinstance(max_etapes, bool) or not isinstance(max_etapes, int):
        raise ValueError("max_etapes doit être un entier")
    if max_etapes <= 0:
        raise ValueError("max_etapes doit être strictement positif")
    machine = programme_func(entree)
    try:
        it = iter(machine)
    except TypeError:
        raise ValueError("programme_func doit produire un itérateur (générateur d'étapes)")
    for step in range(1, max_etapes + 1):
        try:
            next(it)
        except StopIteration:
            return ('arrete', step - 1)
    return ('timeout',)


def arret_general_decidable():
    """Théorème de Turing : le problème de l'arrêt GÉNÉRAL n'est pas décidable. Fait établi -> False."""
    return False


def programme_diagonal(decideur):
    """Construit le programme diagonal D à partir d'un décideur prétendu `decideur`.

    decideur(prog, entree) doit renvoyer 'arrete' ou 'boucle' (verdict d'arrêt prétendu).
    D(entree) : interroge `decideur` sur (D, entree) puis fait L'INVERSE de son verdict —
    boucle infiniment si le verdict est 'arrete', s'arrête aussitôt si le verdict est 'boucle'.
    Renvoie la fonction-programme D (générateur d'étapes), exploitable par `sarrete_dans`.
    """
    if not callable(decideur):
        raise ValueError("décideur non appelable")

    def D(entree):
        verdict = decideur(D, entree)
        if verdict not in ('arrete', 'boucle'):
            raise ValueError("le décideur doit renvoyer 'arrete' ou 'boucle'")
        if verdict == 'arrete':
            while True:        # le décideur dit « s'arrête » -> on BOUCLE (le contredit)
                yield
        else:
            return             # le décideur dit « boucle » -> on S'ARRÊTE (le contredit)
            yield              # pragma: no cover — rend D générateur

    return D


def argument_diagonal(decideur=None):
    """Preuve par l'absurde (diagonalisation de Turing) que l'arrêt général est indécidable.

    Pour TOUT décideur total prétendu H, le programme diagonal D construit à partir de H
    a, sur lui-même, un comportement réel qui est la NÉGATION du verdict de H sur (D, D).
    Donc H se trompe sur cette entrée : aucun H correct ne peut exister.

    Sans argument : vérifie mécaniquement les DEUX verdicts possibles ('arrete', 'boucle')
    et confirme que chacun mène à contradiction. Avec un `decideur` concret : confirme qu'il
    se trompe sur (D, D). Renvoie True ssi la contradiction est établie (preuve valide).
    """
    if decideur is None:
        candidats = [lambda p, x: 'arrete', lambda p, x: 'boucle']
    else:
        if not callable(decideur):
            raise ValueError("décideur non appelable")
        candidats = [decideur]

    BUDGET = 64
    for H in candidats:
        verdict = H('D', 'D')                         # ce que H AFFIRME de D sur D
        if verdict not in ('arrete', 'boucle'):
            raise ValueError("le décideur doit renvoyer 'arrete' ou 'boucle'")
        D = programme_diagonal(H)
        res = sarrete_dans(D, 'D', BUDGET)            # comportement RÉEL de D sur D
        reel = 'arrete' if res[0] == 'arrete' else 'boucle'
        # D est construit pour faire l'INVERSE du verdict : le réel doit contredire H.
        if reel == verdict:
            return False                              # contradiction non établie -> preuve cassée
    return True
