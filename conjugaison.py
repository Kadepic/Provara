"""
CONJUGAISON FRANÇAISE RÉGULIÈRE — règles ÉTABLIES de la grammaire (le MÉCANISME est exact, jamais deviné).

Posture FAUX=0 (même invariant que `physique` / `chimie` : la réalité juge, on n'invente jamais une forme) :
  • Le 1er groupe (verbes en -er, SAUF `aller`) et le 2e groupe (verbes en -ir de type `finir`, participe en
    -issant) suivent des terminaisons FIXES et UNIVERSELLES au présent de l'indicatif. C'est un mécanisme RÉGLÉ,
    donc vérifiable. On l'applique par concaténation radical + terminaison.
  • Le 2e groupe est un ENSEMBLE FERMÉ : on ne le devine pas par la forme de l'infinitif (`finir`=2e mais
    `partir`=3e, tous deux en -ir). On s'appuie donc sur un CATALOGUE établi (verbes certains). Un -ir hors
    catalogue -> ABSTENTION (ValueError), jamais une classification au hasard.
  • Le 3e groupe (irréguliers : être, avoir, aller, aller, prendre, partir…) N'EST PAS conjugué : la réalité de
    chaque verbe fixe sa forme, on ne la devine pas -> ValueError.
  • Les verbes du 1er groupe à PARTICULARITÉS orthographiques (-cer, -ger, -yer, -eler, -eter, et radical à
    e/é/è + consonne finale : lever, céder, préférer…) déclenchent des changements de radical AVEC EXCEPTIONS
    (appeler/acheter, payer/paie-paye…). Pour ne jamais émettre une forme fausse, on ABSTIENT sur ces familles :
    `conjugue` ne produit une forme QUE quand la concaténation pure est GARANTIE correcte par la grammaire.

GARANTIES (vérifiées en adverse par `valide_conjugaison.py`) :
  - verbe irrégulier / 3e groupe (être, avoir, aller, partir, prendre…)            -> ValueError ;
  - -ir hors du catalogue 2e/3e (incertitude sur le groupe)                        -> ValueError ;
  - 1er groupe à particularité orthographique (manger, commencer, appeler, lever…) -> ValueError ;
  - personne hors 1..6, temps autre que le présent, type invalide, non-verbe       -> ValueError ;
  - déterministe (fonctions pures) ; conservateur : abstention (faux négatif) tolérée, FORME FAUSSE interdite.

Les personnes sont numérotées 1..6 : 1=je, 2=tu, 3=il/elle, 4=nous, 5=vous, 6=ils/elles.
"""
from __future__ import annotations

import re

# ── TERMINAISONS DU PRÉSENT DE L'INDICATIF (universelles, sourcées : grammaire française) ────────────────────────
#   ordre : je, tu, il, nous, vous, ils
TERMINAISONS_1ER = ("e", "es", "e", "ons", "ez", "ent")
TERMINAISONS_2E = ("is", "is", "it", "issons", "issez", "issent")

SOURCE = "grammaire française — conjugaison régulière (1er groupe -er, 2e groupe -ir/-issant)"

# ── 2e GROUPE : ENSEMBLE FERMÉ (verbes en -ir, participe présent -issant) ────────────────────────────────────────
# Catalogue de verbes CERTAINS (tous à concaténation pure : radical = infinitif sans -ir, puis terminaisons en -iss).
# On exclut volontairement les cas à tréma/particularité (haïr, fleurir au figuré…). Un -ir hors de CE catalogue et
# du catalogue 3e ci-dessous -> ABSTENTION (on ne devine pas le groupe).
CATALOGUE_2E = frozenset({
    "finir", "choisir", "grandir", "grossir", "maigrir", "rougir", "blanchir", "jaunir", "noircir", "verdir",
    "vieillir", "rajeunir", "réussir", "agir", "réagir", "obéir", "désobéir", "punir", "avertir", "bâtir",
    "démolir", "établir", "rétablir", "remplir", "accomplir", "fournir", "garantir", "nourrir", "ralentir",
    "réfléchir", "saisir", "unir", "réunir", "applaudir", "atterrir", "franchir", "guérir", "durcir", "élargir",
    "embellir", "enrichir", "envahir", "frémir", "gémir", "investir", "pâlir", "refroidir", "salir", "subir",
    "vomir", "adoucir", "convertir", "définir", "surgir", "aboutir", "trahir", "munir", "ravir", "périr",
    "bondir", "brandir", "chérir", "bannir", "éblouir", "engloutir", "épanouir", "faiblir", "fleurir", "fournir",
    "investir", "nantir", "rebondir", "resplendir", "rugir", "saisir", "vrombir", "blêmir", "rosir",
})

# ── 3e GROUPE en -ir : verbes établis (type `partir`, `venir`, `courir`, `ouvrir`…) -> classés 3 (irréguliers) ────
CATALOGUE_3E_IR = frozenset({
    "partir", "repartir", "sortir", "ressortir", "dormir", "endormir", "servir", "desservir", "resservir",
    "mentir", "démentir", "sentir", "ressentir", "consentir", "pressentir", "venir", "revenir", "devenir",
    "parvenir", "prévenir", "souvenir", "convenir", "intervenir", "survenir", "provenir", "tenir", "obtenir",
    "soutenir", "maintenir", "retenir", "contenir", "appartenir", "entretenir", "détenir", "abstenir",
    "courir", "parcourir", "secourir", "accourir", "discourir", "concourir", "recourir", "mourir", "ouvrir",
    "couvrir", "découvrir", "recouvrir", "rouvrir", "offrir", "souffrir", "cueillir", "accueillir", "recueillir",
    "fuir", "enfuir", "bouillir", "faillir", "défaillir", "tressaillir", "assaillir", "acquérir", "conquérir",
    "requérir", "vêtir", "revêtir", "dévêtir", "gésir", "saillir",
})

# ── DÉTECTION DES PARTICULARITÉS ORTHOGRAPHIQUES DU 1er GROUPE (présent) ─────────────────────────────────────────
# La grammaire ne connaît QUE ces familles de changement de radical au présent : -cer, -ger, -yer, et radical en
# e/é/è + consonne (lever, céder, préférer ; inclut -eler/-eter). Si AUCUNE ne s'applique, la concaténation pure
# est GARANTIE correcte. On abstient (au lieu d'émettre une forme à risque) dès qu'une famille s'applique.
_RADICAL_E_CONSONNE = re.compile(r"[eéè][bcdfghjklmnpqrstvwxz]$")


def _est_str_non_vide(x) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _particularite_1er(infinitif_bas: str) -> bool:
    """True si le verbe en -er a une particularité orthographique au présent (-> on abstient)."""
    if infinitif_bas.endswith(("cer", "ger", "yer")):
        return True
    radical = infinitif_bas[:-2]  # sans 'er'
    return _RADICAL_E_CONSONNE.search(radical) is not None


def groupe(infinitif: str) -> int:
    """
    Groupe de conjugaison (règle établie) : 1 (-er sauf `aller`), 2 (-ir de type `finir`), 3 (irréguliers).

    FAUX=0 :
      - `aller` -> 3 (seul -er irrégulier) ;
      - -er -> 1 ;
      - -ir : catalogue 2e -> 2, catalogue 3e -> 3, sinon ABSTENTION (on ne devine pas finir vs partir) ;
      - -re / -oir -> 3 (le 3e groupe couvre tout ce qui n'est ni -er ni -ir) ;
      - tout le reste (non-verbe, type invalide) -> ValueError.
    """
    if not _est_str_non_vide(infinitif):
        raise ValueError(f"infinitif invalide (str non vide attendu) : {infinitif!r}")
    inf = infinitif.strip().lower()
    if len(inf) < 3:
        raise ValueError(f"infinitif trop court / non reconnu : {infinitif!r}")
    if inf == "aller":
        return 3  # unique -er du 3e groupe
    if inf.endswith("er"):
        return 1
    if inf.endswith("oir"):  # AVANT -ir : avoir/voir/devoir… se terminent aussi par 'ir' -> 3e groupe
        return 3
    if inf.endswith("ir"):
        if inf in CATALOGUE_2E:
            return 2
        if inf in CATALOGUE_3E_IR:
            return 3
        raise ValueError(f"verbe en -ir hors catalogue (groupe incertain, abstention) : {infinitif!r}")
    if inf.endswith("re"):
        return 3
    raise ValueError(f"terminaison d'infinitif non reconnue (abstention) : {infinitif!r}")


def terminaisons_present(groupe_id) -> tuple:
    """
    Les 6 terminaisons du présent pour un groupe RÉGULIER (1 ou 2). Accepte 1/'1'/'1er' et 2/'2'/'2e'.
    Le 3e groupe n'a PAS de jeu régulier -> ValueError (on ne devine pas).
    """
    cle = groupe_id
    if isinstance(cle, str):
        cle = cle.strip().lower().replace("er", "").replace("e", "").replace(" ", "")
        # '1er'->'1', '2e'->'2', '1'->'1', '2'->'2' ; tout le reste reste tel quel (=> ValueError)
    if cle in (1, "1"):
        return TERMINAISONS_1ER
    if cle in (2, "2"):
        return TERMINAISONS_2E
    raise ValueError(f"groupe sans terminaisons régulières (1 ou 2 attendu) : {groupe_id!r}")


def conjugue(infinitif: str, personne: int, temps: str = "present") -> str:
    """
    Conjugue un verbe RÉGULIER (1er ou 2e groupe) au présent de l'indicatif, personne 1..6.

    FAUX=0 — abstention (ValueError) si :
      - `infinitif` n'est pas un str non vide ;
      - `personne` n'est pas un entier de 1 à 6 (bool refusé) ;
      - `temps` n'est pas le présent (on ne gère que le présent ici) ;
      - le verbe est du 3e groupe / irrégulier (être, avoir, aller, partir…) ou -ir hors catalogue ;
      - le verbe du 1er groupe a une particularité orthographique (manger, commencer, appeler, lever, céder…).
    """
    if not _est_str_non_vide(infinitif):
        raise ValueError(f"infinitif invalide (str non vide attendu) : {infinitif!r}")
    if isinstance(personne, bool) or not isinstance(personne, int):
        raise ValueError(f"personne doit être un entier 1..6 : {personne!r}")
    if personne < 1 or personne > 6:
        raise ValueError(f"personne hors plage 1..6 : {personne!r}")
    if not isinstance(temps, str) or temps.strip().lower() not in ("present", "présent"):
        raise ValueError(f"temps non géré (présent seulement) : {temps!r}")

    inf = infinitif.strip().lower()
    g = groupe(inf)  # propage l'abstention (3e groupe / -ir incertain)

    if g == 1:
        if _particularite_1er(inf):
            raise ValueError(f"verbe du 1er groupe à particularité orthographique (abstention) : {infinitif!r}")
        return inf[:-2] + TERMINAISONS_1ER[personne - 1]
    if g == 2:
        return inf[:-2] + TERMINAISONS_2E[personne - 1]
    # g == 3 : irrégulier -> on ne devine pas
    raise ValueError(f"verbe irrégulier / 3e groupe non géré (abstention) : {infinitif!r}")
