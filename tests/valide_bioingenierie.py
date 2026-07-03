"""
VALIDE bioingenierie.py — held-out ADVERSE. Cinétique de Michaelis-Menten :
exactitude des cas connus + propriétés du modèle (Km, saturation, S=0) + soundness (domaine -> ValueError)
+ déterminisme. Aucun de ces cas adverses n'est dans le __main__ du module.
"""
import bioingenierie as B

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
    """Vrai si fn(*a) lève ValueError (abstention)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


TOL = 1e-9

# 1) CAS de la spécification — EXACTS.
check(abs(B.vitesse(10, 2, 2) - 5.0) < TOL, "v(10,2,2)=5 (=Vmax/2 car S=Km)")
check(abs(B.vitesse(10, 2, 6) - 7.5) < TOL, "v(10,2,6)=7.5")
check(B.vitesse(10, 2, 0) == 0.0, "v à S=0 -> 0")

# 2) PROPRIÉTÉS du modèle.
# à S=Km, v=Vmax/2 (held-out : autres paramètres).
check(abs(B.vitesse(40, 5, 5) - 20.0) < TOL, "S=Km -> Vmax/2 (40,5,5)=20")
check(abs(B.vitesse(7, 0.3, 0.3) - 3.5) < TOL, "S=Km -> Vmax/2 (7,0.3,0.3)=3.5")
# à S >> Km, v -> Vmax (saturation).
v_sat = B.vitesse(10, 2, 2_000_000)
check(v_sat < 10.0 and abs(v_sat - 10.0) < 1e-4, "S>>Km -> v->Vmax (sous saturation, jamais dépassé)")
check(B.vitesse(10, 2, 1e12) < 10.0, "v < Vmax strict pour tout S fini")
# monotonie croissante en S.
check(B.vitesse(10, 2, 1) < B.vitesse(10, 2, 2) < B.vitesse(10, 2, 4), "v croît avec S")
# valeur de référence calculée à la main : v(10,2,3)=10*3/5=6.0
check(abs(B.vitesse(10, 2, 3) - 6.0) < TOL, "v(10,2,3)=6.0 (10*3/5)")
# v(20,4,4)=20*4/8=10.0
check(abs(B.vitesse(20, 4, 4) - 10.0) < TOL, "v(20,4,4)=10.0 (=Vmax/2)")

# 3) km_vitesse_demi — toujours Vmax/2, cohérent avec vitesse(.,.,Km).
check(abs(B.km_vitesse_demi(10, 2) - 5.0) < TOL, "km_vitesse_demi(10,2)=5.0")
check(abs(B.km_vitesse_demi(13.4, 7.7) - 6.7) < TOL, "km_vitesse_demi(13.4,7.7)=6.7 (held-out)")
check(B.km_vitesse_demi(10, 2) == B.vitesse(10, 2, 2), "km_vitesse_demi == vitesse(.,.,Km)")

# 4) efficacite_catalytique = kcat/Km.
check(abs(B.efficacite_catalytique(100, 2) - 50.0) < TOL, "eff(100,2)=50")
check(abs(B.efficacite_catalytique(1e7, 1e-4) - 1e11) < 1.0, "eff(1e7,1e-4)=1e11 (diffusion-limit)")
check(abs(B.efficacite_catalytique(3, 1.5) - 2.0) < TOL, "eff(3,1.5)=2.0")

# 5) SOUNDNESS — domaine physique -> ValueError (jamais un nombre absurde).
check(leve(B.vitesse, 0, 2, 2), "Vmax=0 -> ValueError")
check(leve(B.vitesse, -1, 2, 2), "Vmax<0 -> ValueError")
check(leve(B.vitesse, 10, 0, 2), "Km=0 -> ValueError")
check(leve(B.vitesse, 10, -2, 2), "Km<0 -> ValueError")
check(leve(B.vitesse, 10, 2, -1), "S<0 -> ValueError")
check(leve(B.km_vitesse_demi, 0, 2), "km_demi Vmax=0 -> ValueError")
check(leve(B.km_vitesse_demi, 10, 0), "km_demi Km=0 -> ValueError")
check(leve(B.efficacite_catalytique, 0, 2), "eff kcat=0 -> ValueError")
check(leve(B.efficacite_catalytique, 100, 0), "eff Km=0 -> ValueError")
check(leve(B.efficacite_catalytique, 100, -1), "eff Km<0 -> ValueError")

# 6) NON numérique / booléen -> ValueError (pas de réponse inventée).
check(leve(B.vitesse, "10", 2, 2), "Vmax str -> ValueError")
check(leve(B.vitesse, 10, None, 2), "Km None -> ValueError")
check(leve(B.vitesse, 10, 2, True), "S booléen -> ValueError")
check(leve(B.efficacite_catalytique, None, 2), "kcat None -> ValueError")

# 7) DÉTERMINISME.
check(B.vitesse(10, 2, 6) == B.vitesse(10, 2, 6), "déterministe vitesse")
check(B.efficacite_catalytique(100, 2) == B.efficacite_catalytique(100, 2), "déterministe efficacite")

print(f"\n=== valide_bioingenierie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
