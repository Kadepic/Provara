"""
MÉMOIRE DE BRIQUES PERSISTANTE v2 — « l'IA apprend ET RETIENT », sous CONFIANCE ZÉRO AU DISQUE
(chantier FORGE 2026-07-12, atome 1 — cf. `_REPRISE_FORGE_BRIQUES.md`).

Chaînon entre `examine_cible` (qui accepte un registre `existant` étendu) et les sessions : chaque
INVENTION vérifiée est GARDÉE sur disque et RÉINJECTÉE au démarrage — une cible déjà apprise redevient
EXISTE_DEJA au lieu d'être re-dérivée. Sortie de PREMIÈRE CLASSE (mandat Yohan) : la brique porte son
spec, son origine et sa date — tout est servable à l'utilisateur et re-jugeable par la machine.

LES DEUX LEÇONS QUI ONT DICTÉ LA v2 (mêmes défauts que « le cache ne signait pas la clé ») :
  • v1 CROYAIT LE DISQUE : `charge()` injectait le JSON tel quel dans `existant` — un fichier altéré
    faisait EXÉCUTER (exec au probing) et SERVIR (EXISTE_DEJA) des expressions jamais jugées. v2 RE-JUGE
    chaque brique sur SON spec enregistré À CHAQUE CHARGEMENT : la réalité re-juge à chaque session, le
    disque n'est jamais cru sur parole. Échec, champ manquant, format inconnu → QUARANTAINE (comptée,
    tracée dans `<chemin>.quarantaine`, JAMAIS injectée, jamais silencieuse).
  • v1 NE STOCKAIT QUE nom→expr : sans spec ni provenance, une brique n'était NI re-jugeable NI servable
    (noms opaques `appris_N`). v2 stocke {expr, origine, quand, spec, held} — le spec voyage AVEC la
    brique (repr/ast.literal_eval : les tuples survivent au disque, JSON les aplatirait en listes et le
    re-jugement mentirait).

ADMISSION GARDÉE À L'INTÉRIEUR : `retient()` exige que l'expr reproduise exemples+held (exécution réelle)
ET que le spec fasse l'aller-retour repr→literal_eval (sinon la brique serait injugeable à la prochaine
session : refusée MAINTENANT, comptée). Les appelants ne peuvent plus oublier la garde.

SOUNDNESS INCHANGÉE EN AVAL : EXISTE_DEJA exige toujours que la brique reproduise les données de la
NOUVELLE cible (`_reproduit` dans examine_cible) — la mémoire accélère, elle ne décide jamais seule.
"""
from __future__ import annotations

import ast
import datetime
import json
import os

VERSION = 2


def _normalise(expr: str) -> str:
    """Normalise une expr pour la dé-duplication (la même idée à espaces près = une seule brique)."""
    return "\n".join(l.rstrip() for l in expr.strip().splitlines())


def _spec_vers_texte(paires) -> str | None:
    """repr des paires si (et seulement si) l'aller-retour literal_eval est EXACT — sinon None : un spec
    qui ne survit pas au disque rendrait la brique injugeable à la prochaine session."""
    paires = list(paires)
    texte = repr(paires)
    try:
        return texte if ast.literal_eval(texte) == paires else None
    except (ValueError, SyntaxError):
        return None


def _texte_vers_spec(texte):
    """Relit un spec depuis le disque. literal_eval SEULEMENT (jamais eval) : des données, pas du code."""
    paires = ast.literal_eval(texte)
    if not isinstance(paires, list) or not all(isinstance(p, tuple) and len(p) == 2 for p in paires):
        raise ValueError("spec relu : attendu une liste de paires (entrée, sortie)")
    return paires


class MemoireBriques:
    """Bibliothèque PERSISTANTE de briques vérifiées, re-jugées au chargement. Réinjectable dans
    `examine_cible(existant=...)`. `self.quarantaine` = ce qui a été refusé au chargement (raison dite) ;
    `self.refus_admission` = ce que `retient()` a refusé (rien de non-vérifié n'entre, jamais)."""

    def __init__(self, chemin: str | None = None, base: dict | None = None):
        self.chemin = chemin
        self.base = dict(base) if base else {}     # registre de départ (EXISTANT), jamais réécrit sur disque
        self.appris: dict[str, dict] = {}          # nom parlant -> enregistrement complet (persisté)
        self.quarantaine: list[dict] = []          # refusés au CHARGEMENT (raison dite, tracés sur disque)
        self.refus_admission = 0                   # refusés par retient() (non reproduits / spec non sérialisable)
        self._exprs: set[str] = set()              # exprs normalisées connues (base + apprises) pour dé-dup
        for e in self.base.values():
            self._exprs.add(_normalise(e))
        self.charge()

    # ── persistance : CHARGEMENT SOUS RE-JUGEMENT (confiance zéro au disque) ──────────────────────────
    def _quarantaine(self, nom, raison, brut) -> None:
        self.quarantaine.append({"nom": nom, "raison": raison, "brut": repr(brut)[:400]})

    def charge(self) -> int:
        """Recharge le fichier : chaque brique est RE-JUGÉE sur son spec enregistré avant d'entrer.
        Tout ce qui ne se re-juge pas (format v1 sans spec, champ manquant, expr qui ne reproduit plus,
        version inconnue, JSON corrompu) part en quarantaine — compté, tracé, jamais injecté."""
        self.appris.clear()
        self.quarantaine.clear()
        if not (self.chemin and os.path.exists(self.chemin)):
            return 0
        try:
            with open(self.chemin, encoding="utf-8") as f:
                brut = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # fichier illisible : PRÉSERVER la pièce (jamais détruire), repartir vide, le DIRE.
            os.replace(self.chemin, self.chemin + ".corrompu")
            self._quarantaine("<fichier>", f"JSON illisible ({e.__class__.__name__}) — préservé en .corrompu", "")
            self._ecrit_quarantaine()
            return 0
        if not isinstance(brut, dict) or brut.get("version") != VERSION:
            # format v1 (nom->expr, sans spec : non re-jugeable) ou version inconnue : tout en quarantaine.
            entrees = brut.items() if isinstance(brut, dict) else [("<racine>", brut)]
            for nom, val in entrees:
                if nom == "version":
                    continue
                self._quarantaine(nom, "format sans spec re-jugeable (v1 ou version inconnue) — "
                                       "la brique sera re-dérivée et re-retenue au format v2", val)
            self._ecrit_quarantaine()
            return 0
        import moteur_invention as MI
        for nom, rec in sorted(brut.get("briques", {}).items()):
            if not isinstance(rec, dict) or not all(k in rec for k in ("expr", "origine", "spec", "held")):
                self._quarantaine(nom, "enregistrement incomplet (champ manquant)", rec)
                continue
            try:
                paires = _texte_vers_spec(rec["spec"]) + _texte_vers_spec(rec["held"])
            except (ValueError, SyntaxError) as e:
                self._quarantaine(nom, f"spec irrelisible ({e.__class__.__name__})", rec)
                continue
            if not paires:
                self._quarantaine(nom, "spec vide : rien ne prouve la brique", rec)
                continue
            # LE RE-JUGEMENT : l'expr doit reproduire, ICI et MAINTENANT, le spec qui l'a prouvée.
            if not MI._reproduit(MI._callable(rec["expr"], "f"), paires):
                self._quarantaine(nom, "ne reproduit plus son spec enregistré (expr ou spec altérés)", rec)
                continue
            self.appris[nom] = rec
            self._exprs.add(_normalise(rec["expr"]))
        self._ecrit_quarantaine()
        return len(self.appris)

    def _ecrit_quarantaine(self) -> None:
        """Trace APPEND-ONLY des refus de chargement (une ligne JSON par refus, datée) — l'évidence ne
        s'écrase jamais. Rien à écrire = rien de créé."""
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
            if os.path.exists(tmp):                 # échec avant replace : pas de résidu (leçon .tmp du cache)
                os.remove(tmp)

    # ── apprentissage : ADMISSION GARDÉE (rien de non-vérifié n'entre) ─────────────────────────────────
    def connait(self, expr: str) -> bool:
        return _normalise(expr) in self._exprs

    def retient(self, par: str, *, origine: str, exemples, held) -> bool:
        """Garde une brique si (a) nouvelle (dé-dup), (b) son expr REPRODUIT exemples+held (exécution
        réelle, ICI — l'appelant ne peut pas oublier la garde), (c) son spec survit à l'aller-retour
        disque. Nom PARLANT dérivé de l'origine (collision → suffixe numérique, rien d'écrasé).
        True ssi la brique vient d'être apprise ; tout refus est compté (`refus_admission`)."""
        if not par or not origine:
            return False
        n = _normalise(par)
        if n in self._exprs:
            return False                            # déjà connue : ni refus ni apprentissage
        exemples, held = list(exemples), list(held or [])
        import moteur_invention as MI
        if not (exemples or held) or not MI._reproduit(MI._callable(par, "f"), exemples + held):
            self.refus_admission += 1               # jamais un faux en mémoire, même demandé poliment
            return False
        s_ex, s_held = _spec_vers_texte(exemples), _spec_vers_texte(held)
        if s_ex is None or s_held is None:
            self.refus_admission += 1               # spec non sérialisable = injugeable demain = refusé aujourd'hui
            return False
        nom = origine
        k = 2
        while nom in self.appris:                   # collision de nom : on n'écrase JAMAIS une brique prouvée
            nom = f"{origine}_{k}"
            k += 1
        self.appris[nom] = {"expr": par, "origine": origine, "quand": datetime.date.today().isoformat(),
                            "spec": s_ex, "held": s_held, "n_verifie": len(exemples) + len(held)}
        self._exprs.add(n)
        return True

    # ── usage ──────────────────────────────────────────────────────────────────────────────────────────
    def existant(self) -> dict:
        """Le registre COMPLET à passer à examine_cible(existant=...) : base + tout ce qui a été appris
        (chaque brique apprise a été vérifiée à l'admission ET re-jugée au chargement)."""
        return {**self.base, **{nom: rec["expr"] for nom, rec in self.appris.items()}}

    def provenance(self, nom: str) -> dict | None:
        """L'enregistrement COMPLET d'une brique apprise (expr, origine, quand, spec, held, n_verifie) —
        la sortie de première classe : tout ce que l'utilisateur est en droit de demander."""
        rec = self.appris.get(nom)
        return dict(rec) if rec else None

    def __len__(self) -> int:
        return len(self.appris)


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=300)
    import moteur_invention as MI

    print("=== DÉMO MÉMOIRE v2 : apprendre -> retenir -> RE-JUGER au chargement -> réutiliser ===")
    mem = MemoireBriques(base=MI.EXISTANT)
    ex = [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)]
    held = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)]
    v1 = MI.examine_cible("amplitude", "x", ex, held, existant=mem.existant())
    print(f"  1er passage : {v1.statut}  (par={v1.par})")
    if v1.statut == MI.INVENTION:
        mem.retient(v1.par, origine="amplitude", exemples=ex, held=held)
    v2 = MI.examine_cible("amplitude_bis", "x", ex, held, existant=mem.existant())
    print(f"  2e passage (après rétention) : {v2.statut}  (par={v2.par})")
    print(f"  briques apprises : {len(mem)} | provenance('amplitude') = {mem.provenance('amplitude')}")
    ok = v1.statut == MI.INVENTION and v2.statut == MI.EXISTE_DEJA
    print("  RETENTION+RÉUTILISATION :", "✅ INVENTION -> EXISTE_DEJA" if ok else "❌")
