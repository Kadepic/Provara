"""
TAXONOMIE DES SUJETS — parseur de `SUJETS_BORNE_OU_NON.md` en source de vérité machine-lisible.

Yohan a cartographié ~990 sujets-feuilles + 133 candidats, chacun annoté BORNÉ (B-NEC/B-PHY/B-FAIT/
B-CONV) ou NON-BORNÉ (NB-SUBJ/NB-OUV/NB-SPEC/NB-NORM/NB-INDEC) ou MIX. Ce module lit ce document et
expose chaque feuille comme un `Sujet`. C'est la CARTE qui pilote « créer les briques manquantes et
répondre sur tous les points bornés » : on ne devine pas les familles, on suit le document.

Anti-dérive : le parseur ne porte AUCUN jugement de vérité — il reflète fidèlement ce que Yohan a
écrit. La classification borné/mécanisme vit dans `couverture_borne.py` (séparation des responsabilités).
"""
from __future__ import annotations

import dataclasses
import os
import re

# Le document vit à la racine du projet. FROZEN-AWARE (.exe PyInstaller) : la carte est embarquée à la racine
# du bundle (`sys._MEIPASS`) — sans ça le produit ignorerait sa propre carte (vécu e2e 2026-07-10 : le
# diagnostic n'affichait pas la couverture dans le .exe).
import sys as _sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUNDLE = getattr(_sys, "_MEIPASS", "")
DOC = os.path.join(_RACINE, "SUJETS_BORNE_OU_NON.md")
if _BUNDLE and not os.path.exists(DOC):
    DOC = os.path.join(_BUNDLE, "SUJETS_BORNE_OU_NON.md")
# ANNEXES AUTO (métiers × axes, domaines × axes) : générées par `outils/genere_sujets.py`, gitignorées car
# DÉRIVABLES du store (frugalité : 11 Mo de texte régénérable ne vivent pas dans git). Absentes -> ignorées.
DOC_AUTO = os.path.join(_RACINE, "SUJETS_ANNEXES_AUTO.md")
if _BUNDLE and not os.path.exists(DOC_AUTO):                # annexes auto : présentes seulement si générées
    DOC_AUTO = os.path.join(_BUNDLE, "SUJETS_ANNEXES_AUTO.md")

# Codes de bornage reconnus (cf. légende du document).
BORNE = {"B-NEC", "B-PHY", "B-FAIT", "B-CONV"}          # la réalité fixe la réponse, accès suffisant
FRONTIERE = {"NB-OUV"}                                   # borné EN PRINCIPE, accès manquant (science ouverte)
NON_BORNE = {"NB-SUBJ", "NB-SPEC", "NB-NORM", "NB-INDEC"}
MIXTE = {"MIX"}                                          # part bornée + part non-bornée
CODES = BORNE | FRONTIERE | NON_BORNE | MIXTE

# Une feuille = `  - <libellé> :: <CODE>   → <prefixe> : <raison>`. Le code est le 1er token après `::`.
_RX_FEUILLE = re.compile(r"^\s*-\s+(.*?)\s*::\s*([A-Z][A-Z-]*)\b\s*(?:→\s*(.*))?$")
_RX_PARTIE = re.compile(r"^#\s+(PARTIE\s+[^\n]+|ANNEXE[^\n]*)$")
_RX_SECTION = re.compile(r"^##\s+(.+?)\s*$")
# Préfixes de la colonne « ce qui borne » à retirer pour ne garder que la raison.
_RX_PREFIXE = re.compile(r"^(?:ce qui le borne\s*:|borné\s*\?\s*par quoi\s*:)\s*", re.IGNORECASE)


@dataclasses.dataclass(frozen=True)
class Sujet:
    libelle: str          # intitulé du sujet-feuille
    code: str             # code de bornage (B-NEC, NB-SUBJ, MIX, …)
    raison: str           # « ce qui le borne » / verdict
    partie: str           # grande partie (PARTIE I — …)
    section: str          # sous-section (## I.1 — Logique), "" si aucune
    ligne: int            # n° de ligne dans le document (traçabilité)

    @property
    def borne(self) -> bool:
        """La réalité fixe-t-elle la réponse AVEC accès suffisant ? (B-* — répondable en principe maintenant)."""
        return self.code in BORNE

    @property
    def frontiere(self) -> bool:
        """Borné EN PRINCIPE mais sans accès (NB-OUV) — réponse honnête = HORS « ouvert »."""
        return self.code in FRONTIERE

    @property
    def mixte(self) -> bool:
        return self.code in MIXTE

    @property
    def non_borne(self) -> bool:
        return self.code in NON_BORNE


def charge(chemin: str = DOC) -> list[Sujet]:
    """Parse le document et renvoie la liste de tous les sujets-feuilles, dans l'ordre du fichier.

    Robuste : ignore les lignes vides, les en-têtes, la légende et la « zone libre » (feuilles à code vide).
    Une feuille n'est retenue que si son code ∈ CODES (élimine les exemples de légende et les gabarits vides)."""
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"Document de taxonomie introuvable : {chemin}")
    sujets: list[Sujet] = []
    partie = section = ""
    with open(chemin, encoding="utf-8") as f:
        for i, brut in enumerate(f, start=1):
            ligne = brut.rstrip("\n")
            mp = _RX_PARTIE.match(ligne)
            if mp:
                partie, section = mp.group(1).strip(), ""
                continue
            ms = _RX_SECTION.match(ligne)
            if ms:
                section = ms.group(1).strip()
                continue
            mf = _RX_FEUILLE.match(ligne)
            if not mf:
                continue
            libelle, code, raison = mf.group(1).strip(), mf.group(2).strip(), (mf.group(3) or "").strip()
            if code not in CODES:        # exclut légende (« B-NEC — borné par… ») et gabarits vides
                continue
            raison = _RX_PREFIXE.sub("", raison).strip()
            sujets.append(Sujet(libelle, code, raison, partie, section, i))
    return sujets


def charge_tout() -> list[Sujet]:
    """La carte COMPLÈTE : le document committé + les annexes auto si elles ont été générées (métiers × axes,
    domaines × axes). C'est l'entrée du moteur de couverture (`couverture_borne`)."""
    tous = charge(DOC)
    if os.path.exists(DOC_AUTO):
        tous += charge(DOC_AUTO)
    return tous


def bornes(chemin: str = DOC) -> list[Sujet]:
    """Les sujets BORNÉS (B-*) — ceux sur lesquels l'IA DOIT pouvoir apporter une réponse vérifiée."""
    return [s for s in charge(chemin) if s.borne]


def par_code(chemin: str = DOC) -> dict[str, list[Sujet]]:
    """Regroupe les sujets par code de bornage."""
    out: dict[str, list[Sujet]] = {}
    for s in charge(chemin):
        out.setdefault(s.code, []).append(s)
    return out


if __name__ == "__main__":
    tous = charge()
    groupes = {}
    for s in tous:
        groupes[s.code] = groupes.get(s.code, 0) + 1
    print(f"=== TAXONOMIE — {DOC}")
    print(f"Total feuilles parsées : {len(tous)}\n")
    print("Répartition par code de bornage :")
    for code in sorted(groupes, key=lambda c: -groupes[c]):
        nature = ("BORNÉ" if code in BORNE else "FRONTIÈRE" if code in FRONTIERE
                  else "MIXTE" if code in MIXTE else "non-borné")
        print(f"  {code:9s} {groupes[code]:4d}   [{nature}]")
    nb_borne = sum(1 for s in tous if s.borne)
    nb_mix = sum(1 for s in tous if s.mixte)
    print(f"\nBORNÉS (B-*) : {nb_borne}   |   MIXTES : {nb_mix}   |   FRONTIÈRE (NB-OUV) : "
          f"{sum(1 for s in tous if s.frontiere)}   |   NON-BORNÉS : {sum(1 for s in tous if s.non_borne)}")
    print("\nExemples de sujets bornés (5 premiers) :")
    for s in [s for s in tous if s.borne][:5]:
        print(f"  · [{s.code}] {s.libelle}  ({s.partie})")
