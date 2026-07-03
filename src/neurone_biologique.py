"""
neurone_biologique.py — Réseaux neuronaux biologiques (modèle intègre-et-tire).

Capacité FAUX=0 : mécanismes EXACTS/établis de l'électrophysiologie du neurone.
- Modèle leaky integrate-and-fire (LIF) simplifié + potentiel d'action (PA).
- depasse_seuil : un PA se déclenche quand le potentiel membranaire atteint le seuil.
- potentiel_repos : fait établi (-70 mV, valeur de référence du potentiel de repos).
- frequence_decharge : courbe f-I rectifiée (réponse fréquence/courant, partie linéaire),
  bornée par la période réfractaire (fréquence maximale physique).

Fonctions PURES déterministes. Abstention par ValueError sur entrée invalide/inconnue :
JAMAIS une valeur inventée. Toute grandeur non numérique ou physiquement absurde
(gain négatif, période réfractaire <= 0) lève ValueError.

Références (établies, neurophysiologie classique) :
- Potentiel de repos neuronal typique : -70 mV.
- Seuil de déclenchement du PA : ~ -55 mV.
- Modèle LIF : Lapicque (1907) ; Gerstner & Kistler, "Spiking Neuron Models".
"""

# Faits établis (constantes de référence, mV).
POTENTIEL_REPOS_MV = -70.0       # potentiel de repos membranaire typique
SEUIL_DEFAUT_MV = -55.0          # seuil de déclenchement du potentiel d'action


def _num(x, nom):
    """Valide qu'une grandeur est un réel fini (et non un booléen). Sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être numérique réel, reçu {x!r}")
    xf = float(x)
    # rejette NaN / inf
    if xf != xf or xf in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} doit être fini, reçu {x!r}")
    return xf


def potentiel_repos():
    """Fait : potentiel de repos du neurone = -70 mV (valeur de référence établie)."""
    return POTENTIEL_REPOS_MV


def depasse_seuil(potentiel_mV, seuil_mV=SEUIL_DEFAUT_MV):
    """
    Le neurone déclenche un potentiel d'action quand le potentiel membranaire
    atteint (>=) le seuil de dépolarisation.

    Renvoie True si potentiel_mV >= seuil_mV (déclenchement du PA), False sinon.
    ValueError si une entrée n'est pas numérique réelle finie.
    """
    p = _num(potentiel_mV, "potentiel_mV")
    s = _num(seuil_mV, "seuil_mV")
    return p >= s


def frequence_decharge(courant, seuil_courant, gain):
    """
    Réponse fréquence-courant (courbe f-I) rectifiée du modèle LIF simplifié :

        f = max(0, gain * (courant - seuil_courant))

    En dessous du courant seuil (rhéobase), le neurone ne décharge pas (f = 0).
    Au-dessus, la fréquence croît linéairement avec le courant injecté.

    courant, seuil_courant : intensités (mêmes unités, p.ex. nA).
    gain : pente de la courbe f-I (Hz par unité de courant), doit être >= 0.

    ValueError si une entrée n'est pas numérique réelle finie, ou si gain < 0
    (une pente négative serait physiquement absurde : abstention plutôt que faux).
    """
    i = _num(courant, "courant")
    s = _num(seuil_courant, "seuil_courant")
    g = _num(gain, "gain")
    if g < 0:
        raise ValueError(f"gain doit être >= 0 (pente f-I), reçu {g}")
    f = g * (i - s)
    return f if f > 0.0 else 0.0


def frequence_max_refractaire(periode_refractaire_ms):
    """
    Fréquence de décharge maximale imposée par la période réfractaire :

        f_max = 1000 / periode_refractaire_ms   (Hz, période en ms)

    Un neurone ne peut pas émettre deux PA plus rapprochés que sa période
    réfractaire ; celle-ci borne donc la fréquence maximale.

    ValueError si la période n'est pas numérique réelle finie ou <= 0.
    """
    t = _num(periode_refractaire_ms, "periode_refractaire_ms")
    if t <= 0.0:
        raise ValueError(f"periode_refractaire_ms doit être > 0, reçu {t}")
    return 1000.0 / t


def frequence_decharge_bornee(courant, seuil_courant, gain, periode_refractaire_ms):
    """
    Courbe f-I rectifiée ET bornée par la période réfractaire :

        f = min( max(0, gain*(courant - seuil_courant)),  1000/periode_refractaire_ms )

    Combine la réponse linéaire f-I et le plafond physique de fréquence.
    ValueError si une entrée est invalide (cf. frequence_decharge / frequence_max_refractaire).
    """
    f = frequence_decharge(courant, seuil_courant, gain)
    fmax = frequence_max_refractaire(periode_refractaire_ms)
    return f if f < fmax else fmax
