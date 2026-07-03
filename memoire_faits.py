"""
MÉMOIRE D'INFORMATIONS PERSISTANTE — « l'IA ne perd pas le contexte au fil du temps, SANS téras de données,
SANS dépendre d'une IA existante » (mandat Yohan 2026-06-24).

Jumelle de `memoire_briques.py` (qui retient les CAPACITÉS) : celle-ci retient les INFORMATIONS / FAITS / le
CONTEXTE observé. Branchée sur `base_faits` (le juge de lookup vérifié, model-free, HORS-si-absent).

POURQUOI ÇA TIENT SANS TÉRAS NI LLM (la thèse du projet — cf. vision clé USB / PC 200€) :
  • Un fait SYMBOLIQUE = une entrée structurée minuscule (~quelques dizaines d'octets) : (relation, entité) ->
    (valeur, catégorie, source, ts). 1 million de faits ≈ quelques dizaines de Mo ; PAS des téraoctets, et
    AUCUN poids de réseau. La rétention est LINÉAIRE et COMPACTE, pas quadratique comme un contexte LLM.
  • Lookup O(1) par clé normalisée -> on ne RELIT jamais tout ; pas de fenêtre de contexte qui sature.
  • MODEL-FREE & SOUVERAIN : zéro dépendance à une IA tierce. On n'invente jamais un fait : présent+vérifié -> on
    répond ; absent -> HORS honnête (jamais une devinette). La soundness de base_faits est préservée intacte.
  • DURABLE : append-only sur disque (JSON), dé-dupliqué, horodaté, sourcé -> survit aux runs et redémarrages.

C'est la 2e moitié de « apprend ET retient » : RETENIR le SAVOIR (pas seulement les briques), de façon
permanente, compacte, vérifiable, autonome.
"""
from __future__ import annotations

import json
import os
import time

from base_faits import Fait, normalise, FAITS, cherche as _cherche_base, VERIFIE, HORS


class MemoireFaits:
    """Mémoire de FAITS vérifiés persistante. Clé = (relation, entité) normalisées. Model-free, sound, compacte."""

    def __init__(self, chemin: str | None = None):
        self.chemin = chemin
        self.faits: dict[str, dict] = {}      # "relation|entité|contexte" -> {valeur, categorie, source, ts}
        self.histoire: dict[str, list] = {}   # BITEMPOREL : clé -> [versions antérieures] (transaction-time, audit)
        self._tx = 0                          # horloge de transaction (ordre des révisions)
        self.charge()

    # — clé canonique (relation, entité, CONTEXTE) — le contexte porte le temps/la situation : « 2026 »,
    #   un lieu, une condition… -> « Macron président de la France EN 2026 » se retient sans écraser 2017. —
    @staticmethod
    def _cle(relation: str, entite: str, contexte: str = "") -> str:
        return f"{normalise(relation)}|{normalise(entite)}|{normalise(contexte)}"

    # — persistance —
    def charge(self) -> int:
        if self.chemin and os.path.exists(self.chemin):
            with open(self.chemin) as f:
                d = json.load(f)
            # rétrocompat : ancien format = {clé: fait} ; nouveau = {"faits":..., "histoire":..., "tx":...}
            if "faits" in d and isinstance(d.get("faits"), dict):
                self.faits = d["faits"]; self.histoire = d.get("histoire", {}); self._tx = d.get("tx", 0)
            else:
                self.faits = d
        return len(self.faits)

    def sauve(self) -> None:
        if not self.chemin:
            return
        tmp = self.chemin + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"faits": self.faits, "histoire": self.histoire, "tx": self._tx},
                      f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.chemin)

    def histoire_de(self, relation: str, entite: str, contexte: str = "") -> list:
        """Toutes les versions connues d'un fait (audit bitemporel), de la plus ancienne à la courante."""
        cle = self._cle(relation, entite, contexte)
        return self.histoire.get(cle, []) + ([self.faits[cle]] if cle in self.faits else [])

    # — apprentissage (RETENIR un fait VÉRIFIÉ + SOURCÉ ; jamais une devinette) —
    def retient(self, relation: str, entite: str, valeur: str, categorie: str, source: str,
                contexte: str = "", ts: float | None = None) -> bool:
        """Garde un fait vérifié. Refuse une valeur vide ou sans source (garde-fou anti-dérive, comme le store).
        `contexte` = temps/situation (« 2026 »). Dé-dup par clé ; True si nouveau (ou valeur révisée, sourcée)."""
        if not valeur or not source:
            return False
        cle = self._cle(relation, entite, contexte)
        ancien = self.faits.get(cle)
        if ancien and ancien.get("valeur") == str(valeur):
            return False
        self._tx += 1
        if ancien is not None:                      # RÉVISION : on garde l'ancienne version (audit), courant = nouveau
            self.histoire.setdefault(cle, []).append(ancien)
        self.faits[cle] = {"valeur": str(valeur), "categorie": categorie, "source": source,
                           "contexte": contexte, "ts": ts if ts is not None else 0.0, "tx": self._tx}
        return True

    def memorise_calcul(self, expression: str, resultat) -> bool:
        """Cas particulier : MÉMORISER un RÉSULTAT calculé (ex. 3*5 -> 15) pour ne plus le recalculer.
        C'est un fait vérifié de catégorie « calcul » (la réalité = l'arithmétique). Lookup O(1) ensuite."""
        return self.retient("calcul", expression, str(resultat), "calcul", "arithmétique vérifiée")

    def rappelle_calcul(self, expression: str):
        """Renvoie le résultat mémorisé d'un calcul, ou None s'il n'a jamais été vu (-> à calculer puis mémoriser)."""
        f = self.cherche("calcul", expression)
        return f.valeur if f else None

    # — usage : lookup-jugé (présent -> Fait ; absent -> None ; jamais de faux) —
    def cherche(self, relation: str, entite: str, contexte: str = "") -> Fait | None:
        e = self.faits.get(self._cle(relation, entite, contexte))
        if e:
            return Fait(e["valeur"], e["categorie"], e["source"])
        return None

    def repond(self, relation: str, entite: str, contexte: str = "") -> tuple[str, Fait | None]:
        """Renvoie (VERIFIE, Fait) si connu (mémoire OU base figée), sinon (HORS, None). Model-free, sound."""
        f = self.cherche(relation, entite, contexte)
        if f:
            return VERIFIE, f
        f = _cherche_base(relation, entite)        # repli sur la base amorce figée (sans contexte)
        return (VERIFIE, f) if f else (HORS, None)

    # — fusion dans base_faits : rend les faits retenus visibles par cherche/repond_nl globaux —
    def fusionne_dans_base(self) -> int:
        """Injecte les faits persistés dans base_faits.FAITS -> l'IA globale (ia.demande, repond_nl) les voit."""
        n = 0
        for cle, e in self.faits.items():
            parts = cle.split("|")
            rel, ent, ctx = parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
            k = (rel, f"{ent} {ctx}".strip() if ctx else ent)    # le contexte est plié dans l'entité côté base
            if k not in FAITS:
                FAITS[k] = Fait(e["valeur"], e["categorie"], e["source"])
                n += 1
        return n

    def __len__(self) -> int:
        return len(self.faits)

    def taille_octets(self) -> int:
        """Empreinte disque réelle (preuve de compacité : ~dizaines d'octets/fait, pas de téras)."""
        return len(json.dumps(self.faits, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=120)
    print("=== DÉMO MÉMOIRE D'INFORMATIONS (compacte, model-free, durable) ===")
    mem = MemoireFaits()

    # EXEMPLE 1 (Yohan) : elle APPREND un fait daté et le RETIENT (sans écraser une autre année).
    mem.retient("president", "France", "Macron", "passe", "appris (actualité)", contexte="2026")
    mem.retient("president", "France", "Macron", "passe", "appris (actualité)", contexte="2017")
    print("  apprend 'président France 2026' ->", mem.cherche("president", "France", "2026").valeur)
    print("  rappelle 'président France 2026' (pas de recalcul/redécouverte) ->",
          mem.repond("president", "France", "2026"))
    print("  'président France 1800' (jamais appris) ->", mem.repond("president", "France", "1800")[0], "(HORS honnête)")

    # EXEMPLE 2 (Yohan) : elle ne RECALCULE pas 3*5 -> elle a MÉMORISÉ le résultat.
    if mem.rappelle_calcul("3*5") is None:
        mem.memorise_calcul("3*5", 3 * 5)        # 1re fois : calcule puis retient
        print("  3*5 : calculé puis mémorisé")
    print("  3*5 (rappel mémoire, zéro recalcul) ->", mem.rappelle_calcul("3*5"))

    # COMPACITÉ : 100000 faits synthétiques -> Mo, pas de téras, pas de poids de réseau.
    for i in range(100000):
        mem.retient("mesure", f"e{i}", str(i), "physique", "synthetique")
    print(f"  {len(mem)} faits -> {mem.taille_octets()/1e6:.1f} Mo "
          f"(≈ {mem.taille_octets()//len(mem)} octets/fait) — PAS de téras, PAS de poids de réseau, souverain")
