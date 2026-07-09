# -*- coding: utf-8 -*-
"""
SÉQUENCEUR — l'EXÉCUTIF d'allocation (SPEC_TRONC_COMPREHENSION §11-§12, Phase 4).

Décide l'ORDRE d'essai des caps de la cascade conversationnelle, PAR ACTE de parole (§8), pour minimiser le
NOMBRE de caps évalués avant celui qui tranche. Ce nombre est la ressource rare ici (§15 : machinerie de
RARETÉ) : moins de caps essayés = moins de calcul = « mieux comprendre et moins de ressources sont la même
chose » (§3.1, théorème thermodynamique). La latence n'est pas le sujet (déjà quelques ms) — le calcul évité l'est.

POLITIQUE = PRIOR statique (familles sûres, ex-`_FAMILLES_ACTES`) ∪ APPRIS du journal de routage RÉEL
(`tronc_routage.jsonl`, écrit par `tronc.note_routage`). C'est le BANDIT CONTEXTUEL de §11 en version DISCRÈTE :
  • contexte  = l'acte classé (11 valeurs) — un LinUCB sur ce one-hot dégénère exactement en un bandit par acte ;
  • bras      = un cap de la cascade ;
  • récompense = le cap a RÉELLEMENT tranché (mesuré POST-HOC dans le journal — anti-Goodhart : on ne récompense
                 pas une propriété déclarée de la sortie, mais la conséquence réelle « ça a répondu ») ;
  • EXPLORATION = le FILET COMPLET de la cascade : tout cap non prioritaire est quand même essayé DERRIÈRE, donc
                 tout cap qui tranche est journalisé -> le signal se collecte tout seul, convergence SANS epsilon ;
  • EXPLOITATION = la politique rechargée met les caps gagnants d'un acte EN TÊTE.

SÛRETÉ FAUX=0 — INVARIANT (prouvé par `valide_sequenceur`) : réordonner ne CHANGE JAMAIS la réponse, seulement
l'ordre d'essai. Garanti par deux règles DURES :
  (1) l'ensemble des caps servis est IDENTIQUE (aucun retiré, le filet reste complet) ;
  (2) l'ordre RELATIF au sein du bloc remonté ET au sein du reste = TOUJOURS l'ordre historique de la cascade
      -> aucune paire de priorité VÉCUE (avis_critere avant avis, comparaison_nway avant comparaison,
      mesure_ambigue avant synonyme_tete…) n'est jamais inversée.
Seuls les actes DÉJÀ dans le prior sont réordonnés (quotidien/avis/créer/agir : détecteurs sûrs). Les actes
factuels/raisonnement gardent l'ordre historique — leurs collisions fines ne se réordonnent pas (biais
conservateur, même prudence que le prior de Phase 5). Le journal les COMPTE quand même (extension future sous banc).

COLD-START HONNÊTE : journal vide / acte hors prior -> ordre historique EXACT -> zéro régression garantie.
Stdlib pur, souverain. Chemin du journal partagé avec `tronc` (une seule source de vérité).
"""
from __future__ import annotations

import json
import os

# Confiance minimale de l'acte pour router (sous ce seuil, l'intention est trop incertaine -> ordre historique).
SEUIL_CONF = 0.8
# Nombre de succès RÉELS minimum pour qu'un cap devienne « appris » d'un acte (anti-bruit : une occurrence
# isolée ne fait pas une politique). Surchargeable pour les tests.
SUPPORT_MIN = 3

# ── PHASE 5 (§21 « retirer les caps ») — COUPE DU FILET, mesurée et réversible ──
# Confiance minimale de l'acte pour COUPER (plus dure que pour réordonner : couper retire des essais).
COUPE_CONF = 0.9
# Maturité : nombre minimal de décisions JOURNALISÉES pour l'acte (toutes dans la famille) avant de couper.
SUPPORT_COUPE = 25
# Passe d'AUDIT : 1 décision sur N garde le filet COMPLET même quand la coupe est mûre — l'exploration reste
# vivante ; un hit hors-famille à l'audit ré-ouvre le filet au prochain rechargement (auto-révocation).
AUDIT_TOUS = 8
_AUDIT_TICK: dict = {}        # {acte: nb de décisions éligibles à la coupe depuis le début du process}

# PRIOR : familles de caps sûres par acte (cold-start + périmètre d'apprentissage autorisé). Déplacé ici depuis
# repond.py — le séquenceur est LE propriétaire de la politique d'allocation. Carte FERMÉE.
PRIOR: dict = {
    "quotidien": ("quotidien", "site"),
    "demander_avis": ("avis_critere", "avis"),
    "creer": ("creer_ouvert", "invention_composite", "invention"),
    "agir": ("traduction",),
    # MESURÉE, jamais déclarée (Phase 5, 2026-07-09) : le journal réel comptait 74/74 décisions « calculer »
    # tranchées par conversion (l'arithmétique pure est déjà TRANCHÉE en amont par le juge AST du tronc —
    # ce qui atteint la cascade sous CALCULER, ce sont les conversions d'unités).
    "calculer": ("conversion",),
}

_CACHE_POLITIQUE = None       # {acte: {cap: nb_succès}} chargé du journal (cristallisé, §15) ; None = à charger


def _chemin_journal() -> str:
    """Le journal de routage — MÊME fichier que `tronc.note_routage` (source unique). Import paresseux pour
    éviter tout cycle ; repli direct sur la convention si tronc est indisponible."""
    try:
        import tronc
        return tronc._chemin_routage()
    except Exception:
        p = os.environ.get("TRONC_ROUTAGE_PATH")
        if p:
            return p
        base = os.environ.get("VERAX_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
        return os.path.join(base, "tronc_routage.jsonl")


def _charge_politique() -> dict:
    """Agrège le journal en {acte: {cap: nb_succès}} (cristallisé une fois par process). Robuste aux lignes
    corrompues ; journal absent -> {} (cold-start)."""
    global _CACHE_POLITIQUE
    if _CACHE_POLITIQUE is not None:
        return _CACHE_POLITIQUE
    counts: dict = {}
    try:
        with open(_chemin_journal(), encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    o = json.loads(ligne)
                except ValueError:
                    continue
                acte, cap = o.get("acte"), o.get("cap")
                if acte and cap:
                    counts.setdefault(acte, {})
                    counts[acte][cap] = counts[acte].get(cap, 0) + 1
    except OSError:
        pass
    _CACHE_POLITIQUE = counts
    return counts


def recharge() -> None:
    """Invalide le cache de politique (rechargée au prochain appel). L'apprentissage est ASYNCHRONE (§11 split
    avant/arrière-plan) : le signal du jour affecte la politique au prochain (re)chargement, pas en plein tour."""
    global _CACHE_POLITIQUE
    _CACHE_POLITIQUE = None


def prioritaires(acte: str) -> tuple:
    """Caps à privilégier pour `acte` = PRIOR de l'acte ∪ caps APPRIS (≥ SUPPORT_MIN succès réels), ou () si
    l'acte n'est pas dans le prior (biais conservateur : on n'invente pas de famille pour un acte factuel).
    L'ordre du tuple n'a AUCUNE importance (l'ordre servi reste toujours l'ordre historique — cf. `ordonne`)."""
    base = PRIOR.get(acte)
    if not base:
        return ()
    appris = tuple(cap for cap, n in _charge_politique().get(acte, {}).items() if n >= SUPPORT_MIN)
    return tuple(dict.fromkeys(base + appris))          # union en préservant l'apparition, sans doublon


def ordonne(acte: str, caps, confiance: float = 1.0):
    """Réordonne `caps` (liste de (nom, handler) dans l'ordre HISTORIQUE) : les caps prioritaires de `acte` sont
    remontés EN TÊTE, l'ordre relatif historique préservé PARTOUT (invariant de sûreté). Renvoie (ordre, set des
    noms prioritaires réellement présents). acte vide / confiance < seuil / acte hors prior -> (caps, set())."""
    caps = list(caps)
    if not acte or confiance < SEUIL_CONF:
        return caps, set()
    prio = set(prioritaires(acte))
    if not prio:
        return caps, set()
    tete = [c for c in caps if c[0] in prio]            # ordre historique conservé (filtre stable)
    reste = [c for c in caps if c[0] not in prio]       # idem
    presents = {c[0] for c in tete}
    return tete + reste, presents


def coupe(acte: str, confiance: float = 1.0) -> bool:
    """PHASE 5 (§21 « retirer les caps ») — True -> la cascade n'essaie QUE la famille de l'acte (le filet des
    ~60 autres caps n'est plus payé). Conditions DURES, toutes mesurées, jamais déclarées :
      • acte à famille FERMÉE (PRIOR) et confiance ≥ COUPE_CONF (couper exige plus que réordonner) ;
      • MATURITÉ prouvée par le journal RÉEL : ≥ SUPPORT_COUPE décisions pour cet acte, ZÉRO hors-famille ;
      • pas un tour d'AUDIT (1 sur AUDIT_TOUS garde le filet complet — l'exploration reste vivante ; un hit
        hors-famille à l'audit est journalisé et RÉVOQUE la coupe au prochain rechargement).
    FAUX=0 : couper n'invente rien — si la famille s'abstient, le pipeline continue (conjonction, web, moteur
    lourd, repli honnête), exactement comme quand la cascade complète s'abstient. Réversible par construction."""
    if not acte or acte not in PRIOR or confiance < COUPE_CONF:
        return False
    total, hors = _hors_actuels(acte)
    if hors or total < SUPPORT_COUPE:
        return False
    n = _AUDIT_TICK.get(acte, 0) + 1
    _AUDIT_TICK[acte] = n
    if n % AUDIT_TOUS == 0:
        return False                                    # tour d'audit : filet complet, le journal juge
    return True


def _hors_actuels(acte: str) -> tuple:
    """(total, hors) pour `acte` — « hors » = décisions dont le cap N'appartient PAS aux prioritaires ACTUELS
    (prior ∪ appris). Le flag `famille` du journal reflète le prior D'ALORS ; la maturité de la coupe se juge
    contre la famille COURANTE : une famille élargie HÉRITE de l'histoire de ses caps (74 décisions
    « calculer -> conversion » comptent le jour où conversion devient la famille de calculer), et un cap
    apprenti qui atteint le support rejoint la famille SANS invalider son passé."""
    counts = _charge_politique().get(acte, {})
    prio = set(prioritaires(acte))
    total = sum(counts.values())
    hors = sum(n for cap, n in counts.items() if cap not in prio)
    return total, hors


def etat_coupe() -> dict:
    """{acte du PRIOR: {total, hors, mure}} — l'état MESURÉ du retrait Phase 5 (pour le diagnostic)."""
    out = {}
    for acte in PRIOR:
        total, hors = _hors_actuels(acte)
        out[acte] = {"total": total, "hors": hors, "mure": bool(total >= SUPPORT_COUPE and not hors)}
    return out


def rapport() -> dict:
    """État de la politique APPRISE (pour le diagnostic) : par acte, les caps appris (≥ support) et leur nombre
    de succès réels. Mesuré depuis le journal, jamais déclaré."""
    pol = _charge_politique()
    out = {}
    for acte, caps in pol.items():
        forts = {cap: n for cap, n in caps.items() if n >= SUPPORT_MIN}
        if forts:
            out[acte] = dict(sorted(forts.items(), key=lambda kv: -kv[1]))
    return out


def couverture() -> tuple:
    """(décisions totales journalisées, décisions couvertes par le prior) — mesure grossière de l'utilité du
    routage. Une décision est « couverte » si son cap gagnant appartenait au prior de son acte."""
    pol = _charge_politique()
    total = couvert = 0
    for acte, caps in pol.items():
        base = set(PRIOR.get(acte, ()))
        for cap, n in caps.items():
            total += n
            if cap in base:
                couvert += n
    return total, couvert
