"""
DYNAMIQUE DES POPULATIONS — modèles DONNÉS, résolus exactement (PARTIE V, B-PHY).

Le sujet dit « modèles donnés » : le modèle est POSÉ par l'utilisateur, et le module en tire les
conséquences. Il ne CHOISIT jamais le modèle à la place de l'appelant, et ne prétend jamais qu'un modèle
décrit une population réelle — c'est une conséquence mathématique, pas une prédiction écologique.

MODÈLES IMPLÉMENTÉS (chacun nommé, avec ses hypothèses écrites) :
  • MALTHUS (exponentiel continu)  : N(t) = N0·e^(r·t).  Hypothèse : ressources illimitées.
  • VERHULST (logistique continu)  : N(t) = K / (1 + ((K−N0)/N0)·e^(−r·t)).  Capacité de charge K.
  • LOGISTIQUE DISCRÈTE            : N_{n+1} = r·N_n·(1 − N_n/K).  Attention : ce modèle BIFURQUE.
  • LOTKA-VOLTERRA (proie/prédateur) : l'ÉQUILIBRE non trivial, exact. `ecologie.py` porte déjà les
    dérivées instantanées ; on ne les duplique pas, on expose l'équilibre et l'invariant du système.

CE QUE LE MODULE REFUSE DE FAIRE (le cœur du FAUX=0) :
  • La logistique DISCRÈTE est chaotique pour r > 3,569946… (constante de Feigenbaum, seuil d'accumulation
    des doublements de période). Au-delà, la trajectoire dépend de la précision de N0 : une valeur « à long
    terme » n'y a aucun sens. `regime_logistique_discrete(r)` NOMME le régime, et `logistique_discrete`
    au-delà du seuil rend la trajectoire en la MARQUANT chaotique — jamais un point d'équilibre inventé.
  • La dérive démographique stochastique est hors périmètre : ces modèles sont DÉTERMINISTES, et le disent.

GARANTIES (vérifiées en adverse par `valide_dynamique_populations.py`) :
  - N0 <= 0, K <= 0, t < 0, n non entier -> ValueError ;
  - bool / str / NaN / ±inf -> ValueError ;
  - `croissance_logistique` avec N0 > K est ACCEPTÉ (population au-dessus de la capacité : elle décroît
    vers K, c'est le comportement correct du modèle) mais N0 == K rend K, sans division par zéro ;
  - `temps_de_doublement` avec r <= 0 -> ValueError (une population qui ne croît pas ne double pas) ;
  - `equilibre_lotka_volterra` avec un paramètre nul -> ValueError (équilibre indéfini) ;
  - déterministe, pur, stdlib seule (`math`).
"""
from __future__ import annotations

import math

SOURCE = ("Malthus (exponentiel), Verhulst 1838 (logistique), May 1976 (logistique discrète et chaos), "
          "Lotka-Volterra (équilibre proie-prédateur)")

# Seuil d'accumulation des doublements de période (constante de Feigenbaum) pour la carte logistique.
SEUIL_CHAOS = 3.5699456718695445
_SIG = 10


def _sig(x: float) -> float:
    if x == 0:
        return 0.0
    return float("%.*g" % (_SIG, x))


def _reel(x, nom: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError("%s invalide : un réel fini est requis (bool/str/NaN/inf refusés)" % nom)
    return float(x)


def _positif(x, nom: str) -> float:
    v = _reel(x, nom)
    if v <= 0:
        raise ValueError("%s doit être strictement positif (reçu %g)" % (nom, v))
    return v


def _duree(t) -> float:
    v = _reel(t, "temps")
    if v < 0:
        raise ValueError("temps négatif : le modèle n'est pas rétro-projeté ici (abstention)")
    return v


# ── MALTHUS : croissance exponentielle ────────────────────────────────────────────────────────────────────
def croissance_exponentielle(N0, r, t) -> float:
    """N(t) = N0·e^(r·t). Hypothèse EXPLICITE : ressources illimitées (aucune capacité de charge)."""
    N0 = _positif(N0, "N0")
    r = _reel(r, "r")
    t = _duree(t)
    return _sig(N0 * math.exp(r * t))


def temps_de_doublement(r) -> float:
    """t tel que N(t) = 2·N0, soit ln(2)/r. r <= 0 -> ValueError (une population qui décroît ne double pas)."""
    r = _reel(r, "r")
    if r <= 0:
        raise ValueError("temps de doublement indéfini pour r <= 0 : la population ne croît pas")
    return _sig(math.log(2.0) / r)


def taux_depuis_doublement(t_double) -> float:
    """r = ln(2)/t : l'inverse exact du précédent (boucle fermée)."""
    t = _positif(t_double, "temps de doublement")
    return _sig(math.log(2.0) / t)


# ── VERHULST : croissance logistique continue ─────────────────────────────────────────────────────────────
def croissance_logistique(N0, r, K, t) -> float:
    """N(t) = K / (1 + ((K−N0)/N0)·e^(−r·t)). Capacité de charge K : la population y tend quand t -> ∞.

    N0 > K est légal (surpopulation) : la population DÉCROÎT vers K. N0 == K rend K exactement."""
    N0 = _positif(N0, "N0")
    r = _reel(r, "r")
    K = _positif(K, "K")
    t = _duree(t)
    if N0 == K:
        return _sig(K)
    a = (K - N0) / N0
    return _sig(K / (1.0 + a * math.exp(-r * t)))


def point_inflexion_logistique(K) -> float:
    """La croissance logistique est maximale en N = K/2 (fait exact : la dérivée seconde s'y annule)."""
    return _sig(_positif(K, "K") / 2.0)


def capacite_atteinte(N, K, tolerance=0.01) -> bool:
    """La population est-elle à la capacité de charge, à `tolerance` relative près ?"""
    N = _positif(N, "N")
    K = _positif(K, "K")
    tol = _reel(tolerance, "tolerance")
    if tol < 0:
        raise ValueError("tolérance négative")
    return abs(N - K) <= tol * K


# ── MAY : logistique DISCRÈTE, et son chaos ───────────────────────────────────────────────────────────────
def regime_logistique_discrete(r) -> str:
    """Nomme le régime asymptotique de N_{n+1} = r·N_n·(1 − N_n/K), fait établi (May 1976).

    r < 1        : extinction        (le seul point fixe est 0)
    1 <= r < 3   : équilibre stable  (point fixe non nul K·(1 − 1/r))
    3 <= r < 3,4494… : cycle de période 2
    3,4494… <= r < 3,5699… : doublements de période successifs
    r >= 3,5699… : CHAOS — aucune valeur asymptotique n'existe."""
    r = _reel(r, "r")
    if r < 0:
        raise ValueError("r négatif : le modèle n'est pas défini")
    if r < 1:
        return "extinction"
    if r < 3:
        return "équilibre stable"
    if r < 3.4494897:
        return "cycle de période 2"
    if r < SEUIL_CHAOS:
        return "doublements de période"
    return "chaos"


def point_fixe_logistique_discrete(r, K) -> float:
    """Point fixe non nul K·(1 − 1/r). ABSTENTION hors du régime où il est STABLE (1 <= r < 3) :
    au-delà, le point fixe existe encore mathématiquement mais la suite ne l'atteint JAMAIS — le rendre
    comme « la » valeur d'équilibre serait un faux."""
    r = _reel(r, "r")
    K = _positif(K, "K")
    regime = regime_logistique_discrete(r)
    if regime != "équilibre stable":
        raise ValueError("aucun équilibre atteint : régime « %s » (r = %g). "
                         "Le point fixe existe mais est instable ou inexistant." % (regime, r))
    return _sig(K * (1.0 - 1.0 / r))


def logistique_discrete(N0, r, K, generations) -> dict:
    """Trajectoire exacte de N_{n+1} = r·N_n·(1 − N_n/K), avec son régime NOMMÉ.

    Renvoie {'trajectoire': [...], 'regime': str, 'chaotique': bool}. En régime chaotique, `chaotique`
    vaut True : la trajectoire est exacte pour CE N0, et ne dit rien de l'asymptote."""
    N0 = _positif(N0, "N0")
    r = _reel(r, "r")
    K = _positif(K, "K")
    if isinstance(generations, bool) or not isinstance(generations, int) or generations < 1:
        raise ValueError("generations : entier >= 1 requis")
    if generations > 10000:
        raise ValueError("generations > 10000 : budget d'itération honnête (abstention)")
    if N0 > K:
        raise ValueError("N0 > K : la carte logistique discrète rend une population négative dès la "
                         "première itération (modèle hors de son domaine de validité)")
    regime = regime_logistique_discrete(r)
    N = N0
    traj = [_sig(N)]
    for _ in range(generations):
        N = r * N * (1.0 - N / K)
        if N < 0 or not math.isfinite(N):
            raise ValueError("trajectoire sortie du domaine (population négative ou non finie)")
        traj.append(_sig(N))
    return {"trajectoire": traj, "regime": regime, "chaotique": regime == "chaos"}


# ── LOTKA-VOLTERRA : l'équilibre, exact ───────────────────────────────────────────────────────────────────
def equilibre_lotka_volterra(alpha, beta, gamma, delta) -> tuple:
    """Équilibre non trivial du système proie(x)/prédateur(y) :
        dx/dt = alpha·x − beta·x·y      dy/dt = delta·x·y − gamma·y
    -> (x*, y*) = (gamma/delta, alpha/beta).

    FAIT contre-intuitif que le module expose : l'effectif d'ÉQUILIBRE des proies ne dépend QUE des
    paramètres du prédateur, et réciproquement. Un paramètre nul -> ValueError (équilibre indéfini)."""
    a = _positif(alpha, "alpha")
    b = _positif(beta, "beta")
    g = _positif(gamma, "gamma")
    d = _positif(delta, "delta")
    return (_sig(g / d), _sig(a / b))
