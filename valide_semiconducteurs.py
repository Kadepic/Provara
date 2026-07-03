"""
VALIDE semiconducteurs.py — held-out ADVERSE.

Exactitude ancrée sur des valeurs EXTERNES connues, NON recalculées par l'expression du module :
  • la « règle des 1240 » du physicien : λ(nm) ≈ 1239.84 / Eg(eV)  (constante hc≈1239.84 eV·nm mémorisée
    indépendamment) -> contrôle croisé de longueur_onde_seuil sans réutiliser h·c/(Eg·e) ;
  • seuils tabulés connus : Si≈1107 nm, GaAs≈873 nm, diamant (Eg≈5.47 eV)≈225-227 nm (UV) ;
  • table de valence : groupe III -> accepteur/type P, groupe V -> donneur/type N.
SOUNDNESS : Eg ≤ 0 / non numérique / dopant inconnu / hôte Si / non-str -> ValueError (jamais un faux).
Aucun de ces cas n'est codé en dur dans semiconducteurs.py.
"""
import semiconducteurs as S

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRE EXTERNE INDÉPENDANTE : règle hc ≈ 1239.84 eV·nm ─────────────────────────────────────────────────────
HC_EV_NM = 1239.841984  # h·c/e en eV·nm — valeur de référence mémorisée (PAS l'expression du module)


def proche(a, b, rel):
    return abs(a - b) <= rel * abs(b)


for Eg in (0.67, 1.12, 1.42, 2.26, 3.4, 5.47):
    ref_nm = HC_EV_NM / Eg                      # référence indépendante
    check(proche(S.longueur_onde_seuil_nm(Eg), ref_nm, 1e-4),
          f"λ(Eg={Eg}) cohérente avec règle 1240 ({ref_nm:.2f} nm)")

# ── 2) SEUILS TABULÉS CONNUS (valeurs publiées, tol 1%) ──────────────────────────────────────────────────────────
check(proche(S.longueur_onde_seuil_nm(1.12), 1107.0, 0.01), "Si Eg=1.12 -> ≈1107 nm")
check(proche(S.longueur_onde_seuil(1.12), 1.107e-6, 0.01), "Si Eg=1.12 -> ≈1.107e-6 m")
check(proche(S.longueur_onde_seuil_nm(1.42), 873.0, 0.01), "GaAs Eg=1.42 -> ≈873 nm")
check(proche(S.longueur_onde_seuil(1.42), 873.0e-9, 0.01), "GaAs Eg=1.42 -> ≈8.73e-7 m")
check(proche(S.longueur_onde_seuil_nm(5.47), 226.0, 0.01), "diamant Eg=5.47 -> ≈226 nm (UV)")

# ── 3) COHÉRENCE INTERNE m <-> nm (×1e9) ─────────────────────────────────────────────────────────────────────────
check(proche(S.longueur_onde_seuil(1.12) * 1e9, S.longueur_onde_seuil_nm(1.12), 1e-9), "m·1e9 == nm")

# ── 4) MONOTONIE physique : gap ↑  =>  λ_seuil ↓ ─────────────────────────────────────────────────────────────────
check(S.longueur_onde_seuil(0.7) > S.longueur_onde_seuil(1.1) > S.longueur_onde_seuil(3.0),
      "λ_seuil strictement décroissante en Eg")

# ── 5) CONVERSION eV -> J (ancre : 1 eV = charge élémentaire exacte) ──────────────────────────────────────────────
check(proche(S.energie_gap_eV_vers_joule(1.0), 1.602176634e-19, 1e-12), "1 eV = 1.602176634e-19 J")
check(proche(S.energie_gap_eV_vers_joule(2.0), 2 * 1.602176634e-19, 1e-12), "2 eV = 2·e J (linéarité)")

# ── 6) DOPAGE — table de valence ─────────────────────────────────────────────────────────────────────────────────
check(S.type_dopage("P") == "accepteur/type P", "lettre P -> accepteur/type P")
check(S.type_dopage("N") == "donneur/type N", "lettre N -> donneur/type N")
check(S.type_dopage("B") == "accepteur/type P", "bore (III) -> accepteur/type P")
check(S.type_dopage("Al") == "accepteur/type P", "aluminium (III) -> accepteur/type P")
check(S.type_dopage("Ga") == "accepteur/type P", "gallium (III) -> accepteur/type P")
check(S.type_dopage("As") == "donneur/type N", "arsenic (V) -> donneur/type N")
check(S.type_dopage("Sb") == "donneur/type N", "antimoine (V) -> donneur/type N")
check(S.type_dopage(" As ") == "donneur/type N", "trim toléré")

# ── 7) SOUNDNESS — abstention stricte (jamais un faux) ───────────────────────────────────────────────────────────
check(leve(S.longueur_onde_seuil, 0), "Eg=0 -> ValueError")
check(leve(S.longueur_onde_seuil, -1.1), "Eg<0 -> ValueError")
check(leve(S.longueur_onde_seuil, "1.12"), "Eg non numérique -> ValueError")
check(leve(S.longueur_onde_seuil, True), "Eg bool -> ValueError")
check(leve(S.longueur_onde_seuil_nm, 0), "λ_nm Eg=0 -> ValueError")
check(leve(S.energie_gap_eV_vers_joule, 0), "conv Eg=0 -> ValueError")
check(leve(S.energie_gap_eV_vers_joule, -3), "conv Eg<0 -> ValueError")
check(leve(S.type_dopage, "Si"), "hôte Si -> ValueError (pas un dopant)")
check(leve(S.type_dopage, "Ge"), "hôte Ge -> ValueError")
check(leve(S.type_dopage, "Xx"), "dopant inconnu -> ValueError")
check(leve(S.type_dopage, "C"), "carbone non listé -> ValueError")
check(leve(S.type_dopage, 15), "non-str -> ValueError")
check(leve(S.type_dopage, None), "None -> ValueError")

# ── 8) DÉTERMINISME ──────────────────────────────────────────────────────────────────────────────────────────────
check(S.longueur_onde_seuil(1.12) == S.longueur_onde_seuil(1.12), "déterminisme λ")
check(S.type_dopage("As") == S.type_dopage("As"), "déterminisme dopage")

print(f"\n=== valide_semiconducteurs : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
