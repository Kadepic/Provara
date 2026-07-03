"""
VALIDE logistique.py — held-out ADVERSE. Gestion des stocks : EOQ (formule de
Wilson), point de commande, stock de sécurité, coût total des stocks.
Ancres CONNUES recalculées à la main et NON circulaires (calculées sans appeler
le module), soundness (entrées <= 0 / non numériques -> ValueError) + déterminisme.
"""
import math
import logistique as L

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# 1) EOQ — formule de Wilson. Cas de la spéc : EOQ(D=1000,S=50,H=2)=sqrt(50000).
# sqrt(2*1000*50/2) = sqrt(100000/2) = sqrt(50000) = 223.6067977...
check(abs(L.quantite_economique_commande(1000, 50, 2) - math.sqrt(50000)) < 1e-5,
      "EOQ(1000,50,2) = sqrt(50000) ~ 223.6068")
check(abs(L.quantite_economique_commande(1000, 50, 2) - 223.606798) < 1e-6,
      "EOQ(1000,50,2) arrondi 6 décimales = 223.606798")
check(abs(L.eoq(1000, 50, 2) - L.quantite_economique_commande(1000, 50, 2)) < 1e-12,
      "alias eoq == quantite_economique_commande")

# EOQ(D=2400,S=12,H=0.3) : sqrt(2*2400*12/0.3) = sqrt(57600/0.3) = sqrt(192000)
# = 438.1780460...  (cas manuel indépendant)
check(abs(L.quantite_economique_commande(2400, 12, 0.3) - math.sqrt(192000)) < 1e-5,
      "EOQ(2400,12,0.3) = sqrt(192000) ~ 438.178")

# EOQ(D=1200,S=8,H=0.3) : sqrt(2*1200*8/0.3) = sqrt(19200/0.3) = sqrt(64000)
# = 252.982212...
check(abs(L.quantite_economique_commande(1200, 8, 0.3) - 252.982213) < 1e-6,
      "EOQ(1200,8,0.3) = sqrt(64000) ~ 252.982213")

# carré parfait pour ancre exacte : sqrt(2*D*S/H)=400 si 2*D*S/H=160000.
# D=400,S=200,H=1 -> 2*400*200/1=160000 -> EOQ=400 exactement.
check(L.quantite_economique_commande(400, 200, 1) == 400.0,
      "EOQ(400,200,1) = 400 (carré parfait)")

# 2) POINT DE COMMANDE — demande * délai. reorder = demande·délai.
check(L.point_commande(20, 5) == 100.0, "ROP(20/j, 5j) = 100")
check(L.point_commande(150, 10) == 1500.0, "ROP(150/j, 10j) = 1500")
check(L.point_commande(7.5, 4) == 30.0, "ROP(7.5/j, 4j) = 30")

# 3) STOCK DE SÉCURITÉ — z*sigma*sqrt(L). Défaut z=1.65.
# 1.65 * 10 * sqrt(4) = 1.65*10*2 = 33.0
check(abs(L.stock_securite(10, 4) - 33.0) < 1e-9, "SS(sigma=10,L=4,z=1.65)=33.0")
# 1.65 * 20 * sqrt(9) = 1.65*20*3 = 99.0
check(abs(L.stock_securite(20, 9) - 99.0) < 1e-9, "SS(sigma=20,L=9,z=1.65)=99.0")
# z=2.33 (99 %): 2.33 * 20 * sqrt(9) = 2.33*20*3 = 139.8
check(abs(L.stock_securite(20, 9, z=2.33) - 139.8) < 1e-9, "SS(sigma=20,L=9,z=2.33)=139.8")
# z=1.96 (97.5 %): 1.96 * 5 * sqrt(16) = 1.96*5*4 = 39.2
check(abs(L.stock_securite(5, 16, z=1.96) - 39.2) < 1e-9, "SS(sigma=5,L=16,z=1.96)=39.2")
# L non carré : 1.65*10*sqrt(2)=23.334524...
check(abs(L.stock_securite(10, 2) - 1.65 * 10 * math.sqrt(2)) < 1e-5,
      "SS(sigma=10,L=2,z=1.65)=1.65*10*sqrt(2)")

# 4) COÛT TOTAL DES STOCKS — (D/Q)*S + (Q/2)*H.
# Q=500 : (1000/500)*50 + (500/2)*2 = 2*50 + 250*2 = 100 + 500 = 600
check(abs(L.cout_total_stock(1000, 50, 2, 500) - 600.0) < 1e-9,
      "TC(D=1000,S=50,H=2,Q=500)=600")
# Q=100 : (1000/100)*50 + (100/2)*2 = 10*50 + 50*2 = 500 + 100 = 600
check(abs(L.cout_total_stock(1000, 50, 2, 100) - 600.0) < 1e-9,
      "TC(...,Q=100)=600")
# Q=200 : (1000/200)*50 + (200/2)*2 = 5*50 + 100*2 = 250 + 200 = 450
check(abs(L.cout_total_stock(1000, 50, 2, 200) - 450.0) < 1e-9,
      "TC(...,Q=200)=450")
# minimum au point Q=EOQ=sqrt(50000) : TC = sqrt(2*D*S*H) = sqrt(2*1000*50*2)
# = sqrt(200000) = 447.2135955...
eoq = math.sqrt(50000)
check(abs(L.cout_total_stock(1000, 50, 2, eoq) - math.sqrt(200000)) < 1e-4,
      "TC au point EOQ = sqrt(200000) ~ 447.2136 (minimum)")
# le minimum est bien <= aux coûts non optimaux ci-dessus
check(L.cout_total_stock(1000, 50, 2, eoq) < L.cout_total_stock(1000, 50, 2, 500),
      "TC(EOQ) < TC(Q=500) (optimalité)")
check(L.cout_total_stock(1000, 50, 2, eoq) < L.cout_total_stock(1000, 50, 2, 100),
      "TC(EOQ) < TC(Q=100) (optimalité)")

# 5) SOUNDNESS — entrées <= 0 -> ValueError (abstention, jamais un faux).
check(leve(L.quantite_economique_commande, 0, 50, 2), "EOQ D=0 -> ValueError")
check(leve(L.quantite_economique_commande, 1000, 0, 2), "EOQ S=0 -> ValueError")
check(leve(L.quantite_economique_commande, 1000, 50, 0), "EOQ H=0 (div/0 évitée) -> ValueError")
check(leve(L.quantite_economique_commande, -1000, 50, 2), "EOQ D<0 -> ValueError")
check(leve(L.quantite_economique_commande, 1000, -50, 2), "EOQ S<0 -> ValueError")
check(leve(L.quantite_economique_commande, 1000, 50, -2), "EOQ H<0 -> ValueError")
check(leve(L.point_commande, 0, 5), "ROP demande=0 -> ValueError")
check(leve(L.point_commande, 20, 0), "ROP délai=0 -> ValueError")
check(leve(L.point_commande, -20, 5), "ROP demande<0 -> ValueError")
check(leve(L.point_commande, 20, -5), "ROP délai<0 -> ValueError")
check(leve(L.stock_securite, 0, 4), "SS sigma=0 -> ValueError")
check(leve(L.stock_securite, 10, 0), "SS L=0 -> ValueError")
check(leve(L.stock_securite, 10, 4, z=0), "SS z=0 -> ValueError")
check(leve(L.stock_securite, 10, 4, z=-1.65), "SS z<0 -> ValueError")
check(leve(L.stock_securite, -10, 4), "SS sigma<0 -> ValueError")
check(leve(L.cout_total_stock, 1000, 50, 2, 0), "TC Q=0 (div/0 évitée) -> ValueError")
check(leve(L.cout_total_stock, 0, 50, 2, 500), "TC D=0 -> ValueError")
check(leve(L.cout_total_stock, 1000, 50, 0, 500), "TC H=0 -> ValueError")
check(leve(L.cout_total_stock, 1000, 50, 2, -500), "TC Q<0 -> ValueError")

# 6) SOUNDNESS — entrées non numériques / NaN / inf -> ValueError.
check(leve(L.quantite_economique_commande, "1000", 50, 2), "EOQ D str -> ValueError")
check(leve(L.quantite_economique_commande, None, 50, 2), "EOQ D None -> ValueError")
check(leve(L.quantite_economique_commande, True, 50, 2), "EOQ D bool -> ValueError")
check(leve(L.quantite_economique_commande, float("nan"), 50, 2), "EOQ D NaN -> ValueError")
check(leve(L.quantite_economique_commande, float("inf"), 50, 2), "EOQ D inf -> ValueError")
check(leve(L.point_commande, "20", 5), "ROP demande str -> ValueError")
check(leve(L.stock_securite, 10, 4, z="haut"), "SS z str -> ValueError")
check(leve(L.stock_securite, float("nan"), 4), "SS sigma NaN -> ValueError")
check(leve(L.cout_total_stock, 1000, 50, 2, float("inf")), "TC Q inf -> ValueError")

# 7) DÉTERMINISME — entrées pures -> sorties stables.
check(L.quantite_economique_commande(1000, 50, 2) == L.quantite_economique_commande(1000, 50, 2),
      "déterminisme EOQ")
check(L.point_commande(20, 5) == L.point_commande(20, 5), "déterminisme ROP")
check(L.stock_securite(10, 4) == L.stock_securite(10, 4), "déterminisme SS")
check(L.cout_total_stock(1000, 50, 2, 500) == L.cout_total_stock(1000, 50, 2, 500),
      "déterminisme TC")

print(f"\n=== valide_logistique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
