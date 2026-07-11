"""
MÉMOIRE DE BRIQUES MULTI-ARGUMENT — la rétention self-improving pour les briques binaires/ternaires
(chantier FORGE, cap multi-arg). Pendant du mono `memoire_briques.MemoireBriques`, ARITÉ-CONSCIENT.

`forge_brique_multi` découvrait une invention binaire/ternaire mais ne la RETENAIT pas : chaque session la
re-dérivait, et une cible déjà apprise n'était jamais reconnue comme EXISTE_DEJA. Ce store comble ce manque
en préservant les MÊMES garanties que le mono (mandat « rien de non vérifié n'entre ; le disque n'est jamais
cru sur parole ») :
  • CONFIANCE ZÉRO AU DISQUE : chaque brique est RE-JUGÉE à `charge()` sur son spec, avec ses PROPRES params
    (arité), par exécution réelle en splat f(*args) — un fichier altéré part en QUARANTAINE, jamais injecté.
  • INNOCUITÉ AVANT EXÉCUTION (atome 7) : `expression_sure` juge la brique SÛRE avant tout appel (au chargement
    ET à l'admission) — une expr hostile n'est jamais exécutée.
  • ADMISSION GARDÉE : `retient()` exige nouveauté (dédup par arité), sûreté, reproduction du spec (splat), et
    spec sérialisable (aller-retour repr→literal_eval) — sinon refus compté.
  • SERVICE PAR ARITÉ : `existant(arite)` = registre de base de l'arité + briques apprises de CETTE arité —
    jamais de mélange d'arités (une expr binaire n'est pas servie à une cible ternaire).
"""
from __future__ import annotations

import datetime
import json
import os

from memoire_briques import VERSION, _normalise, _spec_vers_texte, _texte_vers_spec


class MemoireBriquesMulti:
    def __init__(self, chemin: str | None = None, bases: dict | None = None):
        self.chemin = chemin
        self.bases = {a: dict(r) for a, r in (bases or {}).items()}   # {arite: registre}
        self.appris: dict[str, dict] = {}
        self.quarantaine: list[dict] = []
        self.refus_admission = 0
        self._exprs: dict[int, set] = {}                             # arité -> exprs normalisées connues
        for a, r in self.bases.items():
            self._exprs.setdefault(a, set()).update(_normalise(e) for e in r.values())
        self.charge()

    def _quarantaine(self, nom, raison, brut) -> None:
        self.quarantaine.append({"nom": nom, "raison": raison, "brut": repr(brut)[:400]})

    def _reproduit(self, expr, params, paires) -> bool:
        import invention_multi as IMM
        return IMM._reproduit_multi(IMM._callable_multi(expr, "f", list(params)), paires)

    def charge(self) -> int:
        """Recharge le fichier ; chaque brique RE-JUGÉE (sûreté PUIS reproduction avec ses params) avant
        d'entrer. Tout ce qui ne se re-juge pas part en quarantaine — compté, tracé, jamais injecté."""
        self.appris.clear()
        self.quarantaine.clear()
        if not (self.chemin and os.path.exists(self.chemin)):
            return 0
        try:
            with open(self.chemin, encoding="utf-8") as f:
                brut = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            os.replace(self.chemin, self.chemin + ".corrompu")
            self._quarantaine("<fichier>", f"JSON illisible ({e.__class__.__name__}) — préservé en .corrompu", "")
            self._ecrit_quarantaine()
            return 0
        if not isinstance(brut, dict) or brut.get("version") != VERSION:
            self._quarantaine("<racine>", "format sans spec re-jugeable (version inconnue)", brut)
            self._ecrit_quarantaine()
            return 0
        import expression_sure as ES
        for nom, rec in sorted(brut.get("briques", {}).items()):
            if not isinstance(rec, dict) or not all(k in rec for k in ("expr", "params", "origine", "spec", "held")):
                self._quarantaine(nom, "enregistrement incomplet (champ manquant)", rec)
                continue
            params = rec["params"]
            if not (isinstance(params, list) and len(params) >= 2 and all(isinstance(p, str) for p in params)):
                self._quarantaine(nom, "params invalides (attendu une liste de ≥2 noms)", rec)
                continue
            try:
                paires = _texte_vers_spec(rec["spec"]) + _texte_vers_spec(rec["held"])
            except (ValueError, SyntaxError) as e:
                self._quarantaine(nom, f"spec irrelisible ({e.__class__.__name__})", rec)
                continue
            if not paires:
                self._quarantaine(nom, "spec vide : rien ne prouve la brique", rec)
                continue
            # INNOCUITÉ AVANT RE-JUGEMENT (atome 7).
            raison = ES.raison_danger(rec["expr"])
            if raison is not None:
                self._quarantaine(nom, f"expression non sûre ({raison})", rec)
                continue
            # RE-JUGEMENT : reproduit son spec ICI, avec ses params (splat).
            if not self._reproduit(rec["expr"], params, paires):
                self._quarantaine(nom, "ne reproduit plus son spec enregistré (expr/spec/params altérés)", rec)
                continue
            self.appris[nom] = rec
            self._exprs.setdefault(len(params), set()).add(_normalise(rec["expr"]))
        self._ecrit_quarantaine()
        return len(self.appris)

    def _ecrit_quarantaine(self) -> None:
        if not (self.chemin and self.quarantaine):
            return
        quand = datetime.date.today().isoformat()
        with open(self.chemin + ".quarantaine", "a", encoding="utf-8") as f:
            for q in self.quarantaine:
                f.write(json.dumps({"quand": quand, **q}, ensure_ascii=False) + "\n")

    def sauve(self) -> None:
        if not self.chemin:
            return
        tmp = self.chemin + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"version": VERSION, "briques": self.appris}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.chemin)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def connait(self, expr: str, arite: int) -> bool:
        return _normalise(expr) in self._exprs.get(arite, set())

    def retient(self, par: str, *, origine: str, params, exemples, held) -> bool:
        """Garde une brique multi-arg si (a) nouvelle pour son arité, (b) SÛRE (jugé AVANT exécution),
        (c) son expr reproduit exemples+held (splat), (d) son spec survit au disque. True ssi apprise ;
        tout refus est compté."""
        params = list(params)
        if not par or not origine or len(params) < 2:
            return False
        arite = len(params)
        n = _normalise(par)
        if n in self._exprs.get(arite, set()):
            return False                                # déjà connue : ni refus ni apprentissage
        import expression_sure as ES
        if not ES.est_sure(par):                        # INNOCUITÉ AVANT toute exécution
            self.refus_admission += 1
            return False
        exemples = [(tuple(a), o) for a, o in exemples]
        held = [(tuple(a), o) for a, o in (held or [])]
        toutes = exemples + held
        if not toutes or not self._reproduit(par, params, toutes):
            self.refus_admission += 1
            return False
        s_ex, s_held = _spec_vers_texte(exemples), _spec_vers_texte(held)
        if s_ex is None or s_held is None:
            self.refus_admission += 1                   # spec non sérialisable = injugeable demain = refusé
            return False
        nom = origine
        k = 2
        while nom in self.appris:
            nom = f"{origine}_{k}"
            k += 1
        self.appris[nom] = {"expr": par, "params": params, "origine": origine,
                            "quand": datetime.date.today().isoformat(),
                            "spec": s_ex, "held": s_held, "n_verifie": len(toutes)}
        self._exprs.setdefault(arite, set()).add(n)
        return True

    def existant(self, arite: int) -> dict:
        """Registre COMPLET pour une arité : base + briques apprises de CETTE arité (jamais d'autre arité)."""
        appris = {nom: rec["expr"] for nom, rec in self.appris.items() if len(rec["params"]) == arite}
        return {**self.bases.get(arite, {}), **appris}

    def provenance(self, nom: str) -> dict | None:
        rec = self.appris.get(nom)
        return dict(rec) if rec else None

    def __len__(self) -> int:
        return len(self.appris)
