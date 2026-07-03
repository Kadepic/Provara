"""
MÉDECINES ALTERNATIVES — niveau de preuve scientifique (catalogue de CONSENSUS établi).

Sujet « Pratiques non prouvées ». Domaine BORNÉ : la RÉALITÉ (les données d'efficacité) tranche.
Même posture que `essais_cliniques` / `chimie` (la réalité juge, jamais un faux) :

  • Le CATALOGUE associe à chaque pratique son niveau de preuve ÉTABLI par le consensus scientifique
    (méta-analyses, revues Cochrane, recommandations). Ce ne sont PAS des opinions : ce sont des faits
    SOURCÉS sur l'état de la preuve.
  • Toute pratique HORS catalogue, ou dont l'efficacité n'est PAS tranchée par la science,
    lève ValueError (ABSTENTION) — on n'invente JAMAIS un verdict.

NIVEAUX DE PREUVE (échelle bornée, fermée) :
  - 'aucune_preuve'   : pas d'efficacité démontrée au-delà du placebo (consensus fort) ;
  - 'preuve_faible'   : effet limité/incertain, souvent confondu avec le placebo ;
  - 'preuve_limitee'  : preuve de faible qualité sur une indication précise ;
  - 'preuve_moderee'  : efficacité de qualité modérée sur des indications définies ;
  - 'preuve_forte'    : efficacité solidement établie (réservé, aucune entrée du catalogue) ;
  - 'variable'        : hétérogène — certaines composantes actives, d'autres non (verdict non agrégeable).

CATALOGUE (état de la preuve — consensus établi) :
  - homeopathie                  -> aucune_preuve  (au-delà du placebo ; consensus fort, ex. rapports
                                    NHMRC 2015, Académies des sciences européennes) ;
  - acupuncture                  -> preuve_faible  (effet limité sur certaines douleurs, souvent placebo ;
                                    essais sham largement équivalents) ;
  - osteopathie                  -> preuve_limitee ;
  - chiropraxie                  -> preuve_limitee (lombalgie : manipulation vertébrale, preuve de
                                    faible qualité) ;
  - reiki / chakras / soins_energetiques -> aucune_preuve (pas d'effet au-delà du placebo) ;
  - magnetotherapie / lithotherapie / reflexologie -> aucune_preuve (revues systématiques négatives) ;
  - phytotherapie                -> variable       (certaines plantes actives, d'autres non) ;
  - meditation_pleine_conscience -> preuve_moderee (MBCT/MBSR : preuve de qualité modérée sur la
                                    rechute dépressive, l'anxiété, le stress).

depasse_placebo(pratique) -> bool est DÉRIVÉ du niveau (cohérence) :
  aucune_preuve -> False ; preuve_moderee/forte -> True ;
  preuve_faible / preuve_limitee / variable -> NON TRANCHÉ -> ValueError (abstention, jamais deviné).

GARANTIES STRUCTURELLES (vérifiées en adverse par `valide_medecines_alternatives.py`) :
  - niveau_preuve renvoie TOUJOURS un libellé ∈ NIVEAUX, ou lève ValueError ; jamais une invention ;
  - depasse_placebo ne renvoie JAMAIS True pour une pratique 'aucune_preuve' (faux positif interdit) ;
  - pratique hors catalogue (naturopathie, kinésiologie, biorésonance…) -> ValueError ;
  - entrée non-str / vide -> ValueError ;
  - déterministe ; conservateur (abstention tolérée, faux verdict interdit).
"""
from __future__ import annotations

import re
import unicodedata

SOURCE = (
    "consensus scientifique sur l'efficacité des médecines alternatives "
    "(méta-analyses / revues Cochrane / rapports d'agences)"
)

# Échelle de preuve — ensemble FERMÉ. Toute sortie de niveau_preuve appartient à NIVEAUX.
NIVEAUX = frozenset({
    "aucune_preuve",
    "preuve_faible",
    "preuve_limitee",
    "preuve_moderee",
    "preuve_forte",
    "variable",
})

# CATALOGUE : pratique normalisée -> niveau de preuve établi (consensus). Entrée absente -> abstention.
_CATALOGUE: dict[str, str] = {
    "homeopathie": "aucune_preuve",
    "reiki": "aucune_preuve",
    "chakras": "aucune_preuve",
    "soins_energetiques": "aucune_preuve",
    "magnetotherapie": "aucune_preuve",
    "lithotherapie": "aucune_preuve",
    "reflexologie": "aucune_preuve",
    "acupuncture": "preuve_faible",
    "osteopathie": "preuve_limitee",
    "chiropraxie": "preuve_limitee",
    "phytotherapie": "variable",
    "meditation_pleine_conscience": "preuve_moderee",
}

# Lien niveau -> dépasse-t-il le placebo ? None = NON TRANCHÉ -> abstention (jamais deviné).
_NIVEAU_VERS_PLACEBO: dict[str, bool | None] = {
    "aucune_preuve": False,    # pas d'effet au-delà du placebo (par définition du niveau)
    "preuve_faible": None,     # souvent placebo : non tranché
    "preuve_limitee": None,    # faible qualité : non tranché
    "variable": None,          # hétérogène : pas de verdict agrégé
    "preuve_moderee": True,    # efficacité de qualité modérée démontrée
    "preuve_forte": True,
}

# Synonymes EXACTS (après normalisation) -> clé canonique. Conservateur : pas de fuzzy.
_SYNONYMES: dict[str, str] = {
    "homeopathy": "homeopathie",
    "acupuncture_traditionnelle": "acupuncture",
    "osteopathy": "osteopathie",
    "chiropractic": "chiropraxie",
    "chiropratique": "chiropraxie",
    "reflexology": "reflexologie",
    "reflexologie_plantaire": "reflexologie",
    "phytotherapy": "phytotherapie",
    "soin_energetique": "soins_energetiques",
    "energy_healing": "soins_energetiques",
    "guerison_energetique": "soins_energetiques",
    "chakra": "chakras",
    "magnetotherapy": "magnetotherapie",
    "therapie_par_aimants": "magnetotherapie",
    "lithotherapy": "lithotherapie",
    "crystal_healing": "lithotherapie",
    "guerison_par_les_cristaux": "lithotherapie",
    "mindfulness": "meditation_pleine_conscience",
    "pleine_conscience": "meditation_pleine_conscience",
    "meditation_de_pleine_conscience": "meditation_pleine_conscience",
}


def _norm(pratique) -> str:
    """Normalise une pratique : minuscule, accents retirés, séparateurs -> '_'. Lève ValueError si non-str/vide."""
    if not isinstance(pratique, str):
        raise ValueError(f"pratique non textuelle : {pratique!r}")
    s = pratique.strip().lower()
    if not s:
        raise ValueError("pratique vide")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\s\-'’/.]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        raise ValueError("pratique vide après normalisation")
    return s


def _resoudre(pratique) -> str:
    """Renvoie la clé canonique du catalogue, ou lève ValueError (abstention) si hors catalogue."""
    s = _norm(pratique)
    s = _SYNONYMES.get(s, s)
    if s not in _CATALOGUE:
        raise ValueError(f"pratique hors catalogue (efficacité non répertoriée) : {pratique!r}")
    return s


def est_catalogue(pratique) -> bool:
    """True ssi la pratique (ou un de ses synonymes) figure au catalogue. Ne lève jamais."""
    try:
        _resoudre(pratique)
        return True
    except ValueError:
        return False


def pratiques() -> tuple[str, ...]:
    """Liste triée des pratiques cataloguées (clés canoniques)."""
    return tuple(sorted(_CATALOGUE))


def niveau_preuve(pratique) -> str:
    """Niveau de preuve ÉTABLI (∈ NIVEAUX) pour une pratique du catalogue.

    Pratique hors catalogue / non textuelle -> ValueError (ABSTENTION, jamais inventé).
    """
    return _CATALOGUE[_resoudre(pratique)]


def depasse_placebo(pratique) -> bool:
    """True/False ssi la pratique dépasse le placebo selon le consensus établi.

    Dérivé du niveau de preuve :
      - 'aucune_preuve' -> False ;
      - 'preuve_moderee' / 'preuve_forte' -> True ;
      - 'preuve_faible' / 'preuve_limitee' / 'variable' (NON TRANCHÉ) -> ValueError (abstention).
    Pratique hors catalogue -> ValueError.
    """
    niveau = niveau_preuve(pratique)
    verdict = _NIVEAU_VERS_PLACEBO[niveau]
    if verdict is None:
        raise ValueError(
            f"efficacité vs placebo non tranchée pour {pratique!r} (niveau {niveau!r})"
        )
    return verdict


def _p_medecines_alternatives() -> bool:
    """Preuve auto-portée : vrai sur cas connus + abstention sur entrée hors catalogue / non tranchée."""
    import medecines_alternatives as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        # niveaux établis (catalogue)
        M.niveau_preuve("homeopathie") == "aucune_preuve"
        and M.niveau_preuve("homéopathie") == "aucune_preuve"        # accent normalisé
        and M.niveau_preuve("acupuncture") == "preuve_faible"
        and M.niveau_preuve("osteopathie") == "preuve_limitee"
        and M.niveau_preuve("chiropraxie") == "preuve_limitee"
        and M.niveau_preuve("reiki") == "aucune_preuve"
        and M.niveau_preuve("phytotherapie") == "variable"
        and M.niveau_preuve("meditation_pleine_conscience") == "preuve_moderee"
        # placebo : verdicts tranchés
        and M.depasse_placebo("homeopathie") is False
        and M.depasse_placebo("reiki") is False
        and M.depasse_placebo("meditation_pleine_conscience") is True
        # abstentions : hors catalogue + efficacité non tranchée + entrée invalide
        and _leve_v(M.niveau_preuve, "naturopathie")                 # hors catalogue
        and _leve_v(M.niveau_preuve, "")                             # vide
        and _leve_v(M.niveau_preuve, None)                           # non-str
        and _leve_v(M.depasse_placebo, "phytotherapie")             # variable : non tranché
        and _leve_v(M.depasse_placebo, "acupuncture")               # faible : non tranché
        and _leve_v(M.depasse_placebo, "bioresonance")              # hors catalogue
    )


if __name__ == "__main__":
    for p in pratiques():
        n = niveau_preuve(p)
        try:
            d = depasse_placebo(p)
        except ValueError:
            d = "non_tranche"
        print(f"{p:32s} -> {n:16s} | depasse_placebo={d}")
    print("\nHors catalogue 'naturopathie' :", est_catalogue("naturopathie"))
    print("_p_medecines_alternatives() :", _p_medecines_alternatives())
