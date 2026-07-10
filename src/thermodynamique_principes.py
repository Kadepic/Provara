"""
THERMODYNAMIQUE — PREMIER et DEUXIÈME PRINCIPES comme MÉCANISME de calcul (PARTIE II, B-PHY).

Distinct des voisins réservés (importés, JAMAIS modifiés) :
  • `coherence_physique` JUGE un dispositif déclaré (VIOLE/COHERENT/HORS) sur une spec figée ;
  • `entropie_thermo` ne calcule ΔS que pour un transfert ISOTHERME réversible (Q/T).
Ici, les deux principes comme PRIMITIVES directement appelables : bilan d'énergie interne, travaux
thermodynamiques usuels, variations d'entropie de processus NON isothermes (échauffement, gaz parfait),
critère de spontanéité et borne de Carnot.

POSTURE FAUX=0 (identique à `geometries_non_euclidiennes` / `entropie_thermo`) : chaque formule est un
THÉORÈME/DÉFINITION exact, et l'abstention est STRUCTURELLE — toute entrée hors-domaine lève `ValueError`,
JAMAIS un résultat faux. Un faux négatif (abstention) est toléré ; un faux POSITIF est INTERDIT.

MÉCANISME (conventions NOMMÉES — le signe est le piège) :
  • PREMIER PRINCIPE, convention THERMODYNAMIQUE (physicienne) :
        variation_energie_interne(Q, W) = Q − W
    où W est le travail FOURNI PAR le système sur l'extérieur (détente W>0). ATTENTION : la convention
    CHIMISTE écrit ΔU = Q + W avec W = travail REÇU par le système — signe opposé. On tient la convention
    thermodynamique de bout en bout (les travaux ci-dessous sont donc les travaux FOURNIS par le système).
  • TRAVAIL fourni par le système :
        travail_isotherme_gaz_parfait(n, T, V1, V2) = n·R·T·ln(V2/V1)   (détente isotherme réversible, gaz parfait)
        travail_isobare(P, V1, V2)                  = P·(V2 − V1)
        travail_adiabatique(n, Cv, T1, T2)          = −n·Cv·(T2 − T1)
    (adiabatique Q=0 : W_fourni = −ΔU = −n·Cv·ΔT ; NB : une DIFFÉRENCE de température est invariante par
     changement d'origine °C↔K, donc ce travail-là ne souffre PAS de l'ambiguïté d'unité.)
  • DEUXIÈME PRINCIPE — variations d'entropie de processus NON isothermes (le manque exact comblé) :
        entropie_echauffement(m, c, T1, T2)          = m·c·ln(T2/T1)            (T en KELVIN)
        entropie_detente_isotherme(n, V1, V2)        = n·R·ln(V2/V1)
        entropie_gaz_parfait(n, Cv, T1, T2, V1, V2)  = n·Cv·ln(T2/T1) + n·R·ln(V2/V1)   (T en KELVIN)
        entropie_univers(dS_systeme, dS_exterieur)   = dS_systeme + dS_exterieur
        spontane(dS_univers)                          = (dS_univers > 0)   (délégué à `entropie_thermo.spontane`)
  • BORNE DE CARNOT :
        rendement_carnot(Tf, Tc)     = 1 − Tf/Tc     (Tc > Tf > 0 requis)
        verifie_second_principe(rendement, Tf, Tc)   -> ValueError si rendement > rendement_carnot(Tf, Tc)
        (la décision « viole Carnot » est déléguée au JUGE `coherence_physique.juge_dispositif`.)

GARANTIES (vérifiées en adverse par `valide_thermodynamique_principes.py`) :
  - température ≤ 0 K -> ValueError (échelle Kelvin absolue ; jamais une température absolue négative) ;
  - LE PIÈGE DES °C : dans un logarithme de températures (échauffement, gaz parfait), une entrée qui
    ressemble à des degrés Celsius (valeur < 100 K) est AMBIGUË ; on NE devine PAS -> ValueError. Exemple :
    27 → 127 « °C » donnerait m·c·ln(127/27) ≈ 5,4× la vraie valeur : refusé plutôt que faussé ;
  - n ≤ 0, c ≤ 0, m ≤ 0, Cv ≤ 0, P ≤ 0, V ≤ 0 -> ValueError ;
  - T1 == T2 ou V1 == V2 dans un logarithme -> renvoie 0.0 EXACTEMENT (pas d'erreur : ΔS nul, réversible) ;
  - Tf ≥ Tc dans Carnot -> ValueError (aucun travail extractible) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ; déterministe ; conservateur.

Sortie flottante ARRONDIE à 10 chiffres significatifs (précision honnête). Le module n'importe que la stdlib
(`math`) plus les deux voisins réservés (`entropie_thermo`, `coherence_physique`) — AUCUNE dépendance externe.
"""
from __future__ import annotations

import math

import coherence_physique
import entropie_thermo

# Constante des gaz parfaits. Valeur CONVENTIONNELLE à 4 décimales (celle des calculs à la main / manuels) ;
# la valeur CODATA exacte est 8.314462618 J·mol⁻¹·K⁻¹. Marquée APPROCHÉE : on ne prétend pas à l'exactitude
# au-delà, et les ancres de la gate sont calculées avec cette même valeur (cohérence).
R = 8.314  # J·mol⁻¹·K⁻¹ (approché, conventionnel)

SOURCE = ("1er principe ΔU=Q−W (convention thermodynamique) + 2nd principe / entropie de Clausius "
          "+ borne de Carnot (thermodynamique classique)")

_CHIFFRES_SIGNIFICATIFS = 10
_SEUIL_CELSIUS_K = 100.0  # sous ce seuil (K), une température de ln(T2/T1) est ambiguë avec des °C -> abstention


def _arrondi(x: float) -> float:
    """Arrondit à 10 chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0.0:
        return 0.0
    return round(x, _CHIFFRES_SIGNIFICATIFS - 1 - int(math.floor(math.log10(abs(x)))))


def _reel(x, nom: str) -> float:
    """Coerce un réel FINI ; refuse bool (True n'est pas 1), non-numérique, NaN/inf."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : réel attendu, reçu {x!r}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} : valeur non finie {x!r}")
    return xf


def _positif(x, nom: str) -> float:
    """Réel fini strictement positif (n, m, c, Cv, P, V…). ≤ 0 -> ValueError."""
    xf = _reel(x, nom)
    if xf <= 0.0:
        raise ValueError(f"{nom} : valeur strictement positive requise, reçu {xf}")
    return xf


def _temperature(T, nom: str = "T") -> float:
    """Température absolue : réel fini > 0 (Kelvin). T ≤ 0 K -> ValueError (échelle absolue)."""
    Tf = _reel(T, nom)
    if Tf <= 0.0:
        raise ValueError(f"{nom} : température absolue > 0 K requise, reçu {Tf}")
    return Tf


def _temperature_kelvin_stricte(T, nom: str) -> float:
    """Température destinée à un ln(T2/T1) : Kelvin > 0 ET ≥ seuil anti-°C.

    Une valeur < 100 est trop probablement des degrés Celsius pour être utilisée sans risque de FAUX
    (facteur d'erreur important dans le logarithme). On ABSTIENT plutôt que deviner l'unité."""
    Tf = _temperature(T, nom)
    if Tf < _SEUIL_CELSIUS_K:
        raise ValueError(
            f"{nom} = {Tf} : ambigu (ressemble à des °C). La KELVIN est requise ; "
            f"une valeur < {_SEUIL_CELSIUS_K:.0f} K est refusée pour éviter un faux (pas de devinette d'unité).")
    return Tf


# ── PREMIER PRINCIPE ─────────────────────────────────────────────────────────────────────────────────────────--
def variation_energie_interne(Q, W) -> float:
    """ΔU = Q − W (convention THERMODYNAMIQUE : W = travail FOURNI par le système). Q, W en J.

    ATTENTION : la convention CHIMISTE (ΔU = Q + W, W reçu) donnerait le signe opposé — on ne mélange pas."""
    Qf = _reel(Q, "Q")
    Wf = _reel(W, "W")
    return _arrondi(Qf - Wf)


def travail_isotherme_gaz_parfait(n, T, V1, V2) -> float:
    """W fourni = n·R·T·ln(V2/V1) (détente isotherme réversible d'un gaz parfait). n,T,V>0 ; V1==V2 -> 0.0."""
    nf = _positif(n, "n")
    Tf = _temperature(T, "T")
    v1 = _positif(V1, "V1")
    v2 = _positif(V2, "V2")
    if v1 == v2:
        return 0.0
    return _arrondi(nf * R * Tf * math.log(v2 / v1))


def travail_isobare(P, V1, V2) -> float:
    """W fourni = P·(V2 − V1) (transformation isobare). P>0, V>0 ; V1==V2 -> 0.0."""
    Pf = _positif(P, "P")
    v1 = _positif(V1, "V1")
    v2 = _positif(V2, "V2")
    if v1 == v2:
        return 0.0
    return _arrondi(Pf * (v2 - v1))


def travail_adiabatique(n, Cv, T1, T2) -> float:
    """W fourni = −n·Cv·(T2 − T1) (transformation adiabatique Q=0 : W = −ΔU). n,Cv>0, T>0 ; T1==T2 -> 0.0.

    La DIFFÉRENCE (T2−T1) est invariante °C↔K : pas d'ambiguïté d'unité ici (mais T>0 K reste exigé)."""
    nf = _positif(n, "n")
    cv = _positif(Cv, "Cv")
    t1 = _temperature(T1, "T1")
    t2 = _temperature(T2, "T2")
    if t1 == t2:
        return 0.0
    return _arrondi(-nf * cv * (t2 - t1))


# ── DEUXIÈME PRINCIPE — ENTROPIE (processus non isothermes) ────────────────────────────────────────────────────
def entropie_echauffement(m, c, T1, T2) -> float:
    """ΔS = m·c·ln(T2/T1) (J/K) — échauffement à capacité c constante. m,c>0 ; T1,T2 en KELVIN.

    Les températures < 100 K sont REFUSÉES (ambiguïté avec des °C — cf. docstring de module). T1==T2 -> 0.0."""
    mf = _positif(m, "m")
    cf = _positif(c, "c")
    t1 = _temperature_kelvin_stricte(T1, "T1")
    t2 = _temperature_kelvin_stricte(T2, "T2")
    if t1 == t2:
        return 0.0
    return _arrondi(mf * cf * math.log(t2 / t1))


def entropie_detente_isotherme(n, V1, V2) -> float:
    """ΔS = n·R·ln(V2/V1) (J/K) — détente isotherme d'un gaz parfait. n,V>0 ; V1==V2 -> 0.0."""
    nf = _positif(n, "n")
    v1 = _positif(V1, "V1")
    v2 = _positif(V2, "V2")
    if v1 == v2:
        return 0.0
    return _arrondi(nf * R * math.log(v2 / v1))


def entropie_gaz_parfait(n, Cv, T1, T2, V1, V2) -> float:
    """ΔS = n·Cv·ln(T2/T1) + n·R·ln(V2/V1) (J/K) — gaz parfait, variation d'état générale.

    n,Cv,V>0 ; T1,T2 en KELVIN (< 100 K refusé : ambiguïté °C). Les deux termes s'annulent chacun
    indépendamment (T1==T2 -> 1er terme nul ; V1==V2 -> 2e terme nul)."""
    nf = _positif(n, "n")
    cv = _positif(Cv, "Cv")
    t1 = _temperature_kelvin_stricte(T1, "T1")
    t2 = _temperature_kelvin_stricte(T2, "T2")
    v1 = _positif(V1, "V1")
    v2 = _positif(V2, "V2")
    terme_T = 0.0 if t1 == t2 else nf * cv * math.log(t2 / t1)
    terme_V = 0.0 if v1 == v2 else nf * R * math.log(v2 / v1)
    return _arrondi(terme_T + terme_V)


def entropie_univers(dS_systeme, dS_exterieur) -> float:
    """ΔS_univers = ΔS_système + ΔS_extérieur (J/K). Somme des deux contributions (sans contrainte de signe)."""
    ds = _reel(dS_systeme, "dS_systeme")
    de = _reel(dS_exterieur, "dS_exterieur")
    return _arrondi(ds + de)


def spontane(dS_univers) -> bool:
    """Critère du 2nd principe : spontané ssi ΔS_univers > 0 (strict). Délégué à `entropie_thermo.spontane`.

    ΔS = 0 -> réversible (NON spontané au sens strict) ; ΔS < 0 -> impossible spontanément."""
    return entropie_thermo.spontane(dS_univers)


# ── BORNE DE CARNOT ──────────────────────────────────────────────────────────────────────────────────────────--
def rendement_carnot(Tf, Tc) -> float:
    """Rendement maximal d'un moteur thermique = 1 − Tf/Tc (Tf froide, Tc chaude, en KELVIN).

    Tc > Tf > 0 requis ; Tf ≥ Tc -> ValueError (aucun travail extractible)."""
    tf = _temperature(Tf, "Tf")
    tc = _temperature(Tc, "Tc")
    if tf >= tc:
        raise ValueError(f"Tf ({tf} K) ≥ Tc ({tc} K) : source froide ≥ source chaude, aucun travail extractible")
    return _arrondi(1.0 - tf / tc)


def verifie_second_principe(rendement, Tf, Tc) -> float:
    """Vérifie qu'un rendement DÉCLARÉ ne dépasse pas la borne de Carnot. Renvoie le rendement si conforme.

    rendement > rendement_carnot(Tf, Tc) -> ValueError (2nd principe violé). La décision « viole Carnot »
    est confirmée par le JUGE `coherence_physique.juge_dispositif` (moteur_thermique). rendement < 0 -> ValueError."""
    rf = _reel(rendement, "rendement")
    if rf < 0.0:
        raise ValueError(f"rendement : valeur ≥ 0 attendue, reçu {rf}")
    carnot = rendement_carnot(Tf, Tc)   # valide aussi Tf, Tc (> 0 et Tc > Tf)
    tf = float(Tf)
    tc = float(Tc)
    statut, raison, _loi = coherence_physique.juge_dispositif(
        {"type": "moteur_thermique", "rendement": rf, "t_chaud_K": tc, "t_froid_K": tf})
    if statut == coherence_physique.VIOLE:
        raise ValueError(f"2nd principe violé : {raison}")
    # Garde-fou local (déterministe) redondant avec le juge : ne jamais laisser passer un dépassement.
    if rf > carnot + 1e-9:
        raise ValueError(f"rendement {rf} > rendement de Carnot {carnot} (Tf={tf} K, Tc={tc} K)")
    return rf
