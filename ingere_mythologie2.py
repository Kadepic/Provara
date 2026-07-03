"""
INGESTION MYTHOLOGIES — extension `domaine_dieu` (égyptiens + nordiques) + `pantheon_dieu`  (OFFLINE).

SOURCE : mythologies de référence. Faits STABLES et CERTAINS (attributions/panthéons canoniques).

FAUX=0 — discipline : attributions principales NON CONTESTÉES. `domaine_dieu` étendu SANS recouvrir les
dieux grecs déjà ingérés. `pantheon_dieu` = dieu -> panthéon ; un dieu = un panthéon (apollon rangé en
grec ; les noms romains [jupiter…] sont distincts des noms grecs -> pas de collision). Clés FR minuscules.

Usage : python3 ingere_mythologie2.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie
from ingere_mythologie import _DIEUX as _DIEUX_GRECS  # (grec, domaine, équivalent romain)

# (dieu, domaine principal) — égyptiens + nordiques (AUCUN nom grec déjà ingéré)
_EGYPTIENS = [
    ("râ", "soleil"), ("osiris", "mort et au-delà"), ("isis", "magie"),
    ("anubis", "momification et morts"), ("horus", "ciel et royauté"), ("seth", "chaos et désert"),
    ("thot", "savoir et écriture"), ("bastet", "foyer et chats"), ("hathor", "amour et joie"),
    ("sobek", "Nil et crocodiles"), ("maât", "justice et ordre"), ("ptah", "artisans et création"),
]
_NORDIQUES = [
    ("odin", "sagesse et guerre"), ("thor", "tonnerre"), ("loki", "malice"),
    ("freyja", "amour et fertilité"), ("tyr", "guerre et droit"), ("baldr", "lumière"),
    ("heimdall", "garde du Bifröst"), ("frigg", "mariage et foyer"), ("njörd", "mer et vents"),
]

# panthéons (dieu -> panthéon). Grecs/romains/égyptiens/nordiques.
_GRECS = ["zeus", "héra", "poséidon", "déméter", "athéna", "apollon", "artémis", "arès",
          "aphrodite", "héphaïstos", "hermès", "hestia", "hadès", "dionysos", "cronos"]
_ROMAINS = ["jupiter", "junon", "neptune", "cérès", "minerve", "diane", "mars", "vénus",
            "vulcain", "mercure", "vesta", "pluton", "bacchus", "saturne", "cupidon"]


def ingere():
    print("== MYTHOLOGIES — domaine (grecs+égyptiens+nordiques) + panthéons ==")
    # publie RÉÉCRIT le fichier -> on republie la table COMPLÈTE (grecs inclus) pour ne rien perdre.
    grecs = [(d, dom) for d, dom, _ in _DIEUX_GRECS]
    publie("domaine_dieu", "convention", "mythologie de référence (grecque/égyptienne/nordique) — attributions canoniques",
           grecs + _EGYPTIENS + _NORDIQUES)
    pantheon = ([(d, "grec") for d in _GRECS] + [(d, "romain") for d in _ROMAINS]
                + [(d, "égyptien") for d, _ in _EGYPTIENS] + [(d, "nordique") for d, _ in _NORDIQUES])
    publie("pantheon_dieu", "convention", "mythologie de référence (dieu -> panthéon)", pantheon)


if __name__ == "__main__":
    ingere()
