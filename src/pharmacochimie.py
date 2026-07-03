"""pharmacochimie.py — Règle de cinq de Lipinski (druglikeness). FAUX=0.

Mécanisme EXACT et établi (Lipinski et al., Adv. Drug Deliv. Rev. 1997) : une molécule
candidate-médicament administrée par voie orale a une absorption/perméation médiocre
quand PLUS D'UNE des règles suivantes est violée (« règle de cinq ») :
  - masse molaire   MM ≤ 500 Da
  - lipophilie      logP ≤ 5
  - donneurs de H        ≤ 5
  - accepteurs de H      ≤ 10
On compte donc les violations (comparaison de seuils exacte, déterministe) :
  - respecte_lipinski  = True ssi 0 violation (les 4 critères satisfaits)
  - est_drug_like      = True ssi ≤ 1 violation (tolérance pratique de la règle)
  - nombre_violations  = nombre de critères dépassés (0..4)
  - indice_lipinski    = verdict détaillé (par critère + synthèse)

SOUNDNESS : entrées non numériques / non finies -> ValueError ;
masse molaire ≤ 0 -> ValueError ; donneurs/accepteurs négatifs -> ValueError.
(logP PEUT être négatif — molécules très polaires, ex. caféine logP≈-0.07 — donc non rejeté.)
"""
import math

# Seuils canoniques de la règle de cinq (valeurs établies, sources : Lipinski 1997).
SEUIL_MASSE = 500.0      # Da
SEUIL_LOGP = 5.0
SEUIL_DONNEURS = 5
SEUIL_ACCEPTEURS = 10


def _nombre_fini(x, nom):
    """Vérifie que x est un nombre réel fini (rejette bool, str, NaN, inf)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre, reçu {type(x).__name__}")
    if not math.isfinite(x):
        raise ValueError(f"{nom} doit être fini, reçu {x}")
    return float(x)


def _valide_entrees(masse_molaire, logP, donneurs_H, accepteurs_H):
    """Valide et normalise les 4 descripteurs ; lève ValueError si invalide."""
    mm = _nombre_fini(masse_molaire, "masse_molaire")
    lp = _nombre_fini(logP, "logP")
    dh = _nombre_fini(donneurs_H, "donneurs_H")
    ah = _nombre_fini(accepteurs_H, "accepteurs_H")
    if mm <= 0:
        raise ValueError("masse_molaire doit être > 0")
    if dh < 0:
        raise ValueError("donneurs_H ne peut être négatif")
    if ah < 0:
        raise ValueError("accepteurs_H ne peut être négatif")
    return mm, lp, dh, ah


def nombre_violations(masse_molaire, logP, donneurs_H, accepteurs_H):
    """Nombre de critères de Lipinski dépassés (0..4). Violation ssi STRICTEMENT au-dessus du seuil."""
    mm, lp, dh, ah = _valide_entrees(masse_molaire, logP, donneurs_H, accepteurs_H)
    v = 0
    if mm > SEUIL_MASSE:
        v += 1
    if lp > SEUIL_LOGP:
        v += 1
    if dh > SEUIL_DONNEURS:
        v += 1
    if ah > SEUIL_ACCEPTEURS:
        v += 1
    return v


def respecte_lipinski(masse_molaire, logP, donneurs_H, accepteurs_H):
    """True ssi les 4 critères sont satisfaits (0 violation)."""
    return nombre_violations(masse_molaire, logP, donneurs_H, accepteurs_H) == 0


def est_drug_like(masse_molaire, logP, donneurs_H, accepteurs_H):
    """True ssi ≤ 1 violation (tolérance pratique de la règle de cinq)."""
    return nombre_violations(masse_molaire, logP, donneurs_H, accepteurs_H) <= 1


def indice_lipinski(masse_molaire, logP, donneurs_H, accepteurs_H):
    """Verdict détaillé par critère + synthèse. Dict déterministe.

    Clés : masse_ok, logP_ok, donneurs_ok, accepteurs_ok (bool par critère),
    n_violations (int 0..4), n_satisfaits (int 0..4),
    respecte (0 violation), drug_like (≤1 violation)."""
    mm, lp, dh, ah = _valide_entrees(masse_molaire, logP, donneurs_H, accepteurs_H)
    masse_ok = mm <= SEUIL_MASSE
    logP_ok = lp <= SEUIL_LOGP
    donneurs_ok = dh <= SEUIL_DONNEURS
    accepteurs_ok = ah <= SEUIL_ACCEPTEURS
    n = (not masse_ok) + (not logP_ok) + (not donneurs_ok) + (not accepteurs_ok)
    return {
        "masse_ok": masse_ok,
        "logP_ok": logP_ok,
        "donneurs_ok": donneurs_ok,
        "accepteurs_ok": accepteurs_ok,
        "n_violations": n,
        "n_satisfaits": 4 - n,
        "respecte": n == 0,
        "drug_like": n <= 1,
    }
