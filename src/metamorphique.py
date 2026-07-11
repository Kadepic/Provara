"""
PROPRIÉTÉS MÉTAMORPHIQUES — le held-out durci SANS oracle exact (chantier FORGE atome 6 ; Chen 1998,
survey Segura 2016). Une propriété relie f(T(x)) à f(x) sans connaître la sortie attendue : elle juge des
entrées NEUVES gratuitement, là où chaque paire du held-out coûte un étiquetage.

STATUT ÉPISTÉMIQUE (la clé de la soundness) : une propriété est DÉCLARÉE par l'utilisateur/moteur — c'est
une EXIGENCE du spec, pas un fait sur le monde. Un candidat qui la viole ne satisfait pas le besoin ->
écarté, témoin tracé. Une propriété erronée rend donc le moteur PLUS CONSERVATEUR (refus/frontière),
jamais un faux servi : FAUX=0 préservé par construction. Transformations DÉTERMINISTES uniquement
(rejouables ; pas de hasard — cf. la règle du held-out durci à froid).

Deux effets sur examine_cible (opt-in `proprietes=`) :
  • DURCIR   — une réalisation qui reproduit toutes les paires mais viole une propriété est écartée
               (le spec par paires seul ne voyait pas la violation) ;
  • TRANCHER — un AMBIGU (≥2 réalisations sous les paires) devient INVENTION si la propriété tue les
               candidats non conformes et qu'il ne reste qu'UN comportement : résolution SANS aller-retour
               utilisateur (le dual de besoin_a_renforcer).
"""
from __future__ import annotations

# ── le catalogue (Segura 2016 : permutation / duplication / homogénéité — les relations sans oracle les
#    plus déclarées). Chaque propriété : s_applique (domaine du probe), transformes (T déterministes),
#    relie (la relation attendue entre f(x) et f(T(x))). Extensible : une propriété CUSTOM est un dict
#    de même forme passé directement à examine_cible.
def _egal_type_exact(y, yt):
    """Égalité TYPE-EXACTE sur bool (même garde que moteur_invention._reproduit : 1 n'est pas True)."""
    return y == yt and isinstance(y, bool) == isinstance(yt, bool)


def _liste(x, n=2):
    return isinstance(x, list) and len(x) >= n


PROPRIETES: dict[str, dict] = {
    # f(perm(x)) == f(x) — fonctions d'ENSEMBLE/multi-ensemble (somme, max, médiane, comptages…).
    "invariance_permutation": {
        "s_applique": _liste,
        "transformes": [lambda x: x[::-1], lambda x: x[1:] + x[:1]],
        "relie": _egal_type_exact,
    },
    # f(x + x) == f(x) — fonctions insensibles à la multiplicité (max, min, nb_distinct, tout_positif…).
    "invariance_duplication": {
        "s_applique": _liste,
        "transformes": [lambda x: x + x],
        "relie": _egal_type_exact,
    },
    # f([2e]) == 2·f(x) — fonctions LINÉAIRES en les valeurs (somme, somme partielle, amplitude…).
    "homogeneite_double": {
        "s_applique": lambda x: _liste(x) and all(isinstance(e, int) and not isinstance(e, bool) for e in x),
        "transformes": [lambda x: [e * 2 for e in x]],
        "relie": lambda y, yt: isinstance(y, int) and not isinstance(y, bool) and yt == 2 * y,
    },
}


def resoud(proprietes):
    """Noms du catalogue -> règles ; un dict custom (même forme) passe tel quel. Nom inconnu = ValueError
    (jamais une propriété silencieusement ignorée : elle fait partie du spec)."""
    regles = []
    for p in proprietes:
        if isinstance(p, dict):
            regles.append((p.get("nom", "custom"), p))
        elif p in PROPRIETES:
            regles.append((p, PROPRIETES[p]))
        else:
            raise ValueError(f"propriété métamorphique inconnue : {p!r}")
    return regles


def respecte(f, regles, entrees):
    """f respecte-t-elle chaque règle sur les entrées où elle s'applique ?

    Renvoie (True, None) ou (False, temoin) — temoin = (nom_propriete, x, tx) lisible/actionnable.
    Sémantique d'erreur SOUND : f erre sur x -> probe muet (aucune affirmation) ; f(x) passe mais f(T(x))
    erre -> VIOLATION (l'exigence porte sur T(x) aussi). Aucune entrée applicable -> respect VACU (on
    n'affirme rien au-delà du spec ; les paires, elles, restent jugées)."""
    for nom, regle in regles:
        s_applique, transformes, relie = regle["s_applique"], regle["transformes"], regle["relie"]
        for x in entrees:
            if not s_applique(x):
                continue
            try:
                y = f(x)
            except Exception:
                continue
            for T in transformes:
                tx = T(x)
                try:
                    yt = f(tx)
                except Exception:
                    return False, (nom, x, tx)
                if not relie(y, yt):
                    return False, (nom, x, tx)
    return True, None
