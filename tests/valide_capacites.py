"""VALIDE capacites.py — manifeste de capacités formule/concept. Held-out ADVERSE, FAUX=0.

Deux niveaux :
  1) Le manifeste est LIVE : verifie_tout() -> toutes les preuves passent (sinon manifeste menteur).
  2) ORACLE INDÉPENDANT (non auto-certifiant) : on re-dérive des ANCRES CONNUES directement contre les modules
     sous-jacents et on exige l'accord — garantit que « couvert » reflète un calcul JUSTE, pas un proof qui
     renverrait True à vide. + contrôles NÉGATIFS : un sujet hors-registre n'est JAMAIS couvert (pas de faux positif).
"""
import capacites as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def proche(a, b, rel=1e-3, abs_=1e-9):
    try:
        return abs(float(a) - float(b)) <= rel * abs(float(b)) + abs_
    except Exception:
        return False


# ── 1) MANIFESTE LIVE : toutes les preuves passent ──
n_ok, n_ko, echecs = C.verifie_tout()
check(n_ko == 0, f"manifeste live : {n_ok}/{n_ok + n_ko} (échecs: {echecs})")
check(n_ok == 303, f"303 sujets au registre (vu {n_ok})")  # 2026-07-08 : +22 preuves façade ia.py (lots 1-17, excellence atomique)

# ── 2) ORACLE INDÉPENDANT — re-dérive les ancres contre les modules (anti auto-certification) ──
import bayes as B
st, p, _ = B.posterior(0.5, [(0.9, 0.1, True)])
check(st == B.ESTIMATION and proche(p, 0.9), "oracle bayes : prior 0.5 × LR 9 -> postérieure 0.9")
check(B.posterior(1.0, [(0.9, 0.1, True)])[0] == B.ABSTENTION, "oracle bayes : prior dégénéré -> abstention")

import regression_robuste as rr
b, a = rr.ols([0, 1, 2, 3, 4], [1, 4, 7, 10, 13])      # y = 3x + 1
check(proche(b, 1.0) and proche(a, 3.0), "oracle régression : y=3x+1 -> (intercept 1, pente 3)")

import importance_sampling as isz
check(proche(isz.ess([2, 2, 2]), 3.0), "oracle ESS : poids égaux -> ESS = n = 3")
check(proche(isz.ess([5, 0, 0]), 1.0), "oracle ESS : un poids domine -> ESS = 1")

import physique as P
g = P.calcule("gravite_surface", {"M": 5.972e24, "r": 6.371e6})
check(g[0] == P.VERIFIE and proche(g[1], 9.81, rel=2e-3), "oracle physique : gravité Terre ≈ 9.81 m/s²")
check(P.calcule("ph", {"concentration_H": 1e-3})[1] == 3.0, "oracle physique : pH([H+]=1e-3) = 3")
check(P.calcule("gravite_surface", {"M": -1, "r": 1})[0] == P.HORS, "oracle physique : M<0 -> HORS")

import jeux_zero_somme as jzs
# point-selle indépendant : maximin = max(min(4,5),min(6,7)) = 6 ; minimax = min(max(4,6),max(5,7)) = 6
st2, info2 = jzs.analyse([[4, 5], [6, 7]], iters=3000)
check(st2 == jzs.JEU and proche(info2["valeur"], 6.0, rel=2e-2), "oracle jeux : point-selle [[4,5],[6,7]] -> valeur 6")

import deduction as D
m = D.MoteurDeduction()
for x, y in [("a", "b"), ("b", "c"), ("c", "d")]:
    m.ajoute_fait("p", x, y)
m.ajoute_regle(("anc", "X", "Y"), [("p", "X", "Y")], "b")
m.ajoute_regle(("anc", "X", "Z"), [("p", "X", "Y"), ("anc", "Y", "Z")], "t")
check(m.interroge("anc", "a", "d")[0] == "verifie", "oracle déduction : fermeture transitive a->d")
check(m.interroge("anc", "d", "a")[0] == "hors", "oracle déduction : pas d'invention d->a (soundness)")

import coherence_physique as cp
check(cp.juge_dispositif({"type": "moteur_thermique", "rendement": 0.70,
                          "t_chaud_K": 800, "t_froid_K": 300})[0] == cp.VIOLE,
      "oracle cohérence : rendement 0.70 > Carnot 0.625 -> VIOLE")

import maths_discretes as MD
check(MD.catalan(7) == 429 and MD.fibonacci(10) == 55, "oracle maths_discretes : Catalan(7)=429, Fib(10)=55")
check(MD.composantes_connexes(4, [(0, 1), (2, 3)]) == 2, "oracle maths_discretes : 2 composantes connexes")
check(MD.dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3) == 2, "oracle maths_discretes : Dijkstra = 2")
check(MD.aire_triangle_x2((0, 0), (4, 0), (0, 3)) == 12, "oracle maths_discretes : aire triangle ×2 = 12")
check(MD.eval_rpn(["2", "3", "+", "4", "*"]) == 20, "oracle maths_discretes : RPN (2 3 + 4 *) = 20")
try:
    MD.fibonacci(-1); _soundMD = False
except ValueError:
    _soundMD = True
check(_soundMD, "oracle maths_discretes : fibonacci(-1) -> ValueError (soundness)")
import audit_code as AC
check(AC.audite("def f(a,b):\n    return a+b", "python")[0] == AC.RAS, "oracle audit_code : code propre -> RAS (pas de faux positif)")
import algebre_calcul as AL
from fractions import Fraction as _Fr
check(AL.equation_lineaire(2, -6) == ("unique", _Fr(3)), "oracle algèbre : 2x-6=0 -> x=3")
check(AL.equation_quadratique(1, -5, 6) == ("deux_rationnelles", [_Fr(2), _Fr(3)]), "oracle algèbre : (x-2)(x-3) -> {2,3}")
check(AL.equation_quadratique(1, 0, -2)[0] == "deux_irrationnelles", "oracle algèbre : x²-2 -> irrationnel (pas de fausse décimale)")
check(AL.evalue_polynome([6, -5, 1], 2) == _Fr(0), "oracle algèbre : 2 racine de x²-5x+6 (évaluation exacte)")
import arithmetique_modulaire as AM
check(AM.exp_modulaire(7,128,13)==pow(7,128,13) and AM.est_premier(561) is False, "oracle crypto : exp mod = pow, Carmichael 561 démasqué")
g,x,y=AM.euclide_etendu(240,46)
check(240*x+46*y==g==2, "oracle crypto : Bézout 240,46 vérifié")
import information_calcul as IC
check(abs(IC.entropie([0.25, 0.25, 0.25, 0.25]) - 2.0) < 1e-9, "oracle info : entropie 4 issues = 2 bits")
import algebre_boole as BL
check(BL.est_tautologie("((a -> b) & (b -> c)) -> (a -> c)") and not BL.est_tautologie("a | b"),
      "oracle Boole : syllogisme hypothétique tautologie, a|b non")
import automates as AUT
_m3 = {"etats": {0, 1, 2}, "alphabet": {"0", "1"},
       "transitions": {(r, b): (2 * r + int(b)) % 3 for r in (0, 1, 2) for b in ("0", "1")},
       "initial": 0, "acceptants": {0}}
check(AUT.accepte(_m3, "1100") == (int("1100", 2) % 3 == 0), "oracle automate : DFA multiples de 3 vs arithmétique")
import turing as TUR
_incr = {"blanc": "_", "initial": "d", "acceptants": {"f"},
         "transitions": {("d", "0"): ("d", "0", "R"), ("d", "1"): ("d", "1", "R"), ("d", "_"): ("r", "_", "L"),
                         ("r", "0"): ("f", "1", "L"), ("r", "1"): ("r", "0", "L"), ("r", "_"): ("f", "1", "L")}}
check(TUR.execute(_incr, "1011", 1000)[1] == bin(int("1011", 2) + 1)[2:], "oracle Turing : incrément = +1 binaire")
import groupes as GRP
check(GRP.ordre_permutation((1, 0, 3, 4, 2)) == 6 and GRP.signature_permutation((1, 2, 0)) == 1,
      "oracle groupes : ordre ppcm(2,3)=6, signature 3-cycle = +1")
import stoechiometrie as STO, chimie as _CH
_c = STO.equilibre(["C2H6", "O2"], ["CO2", "H2O"])
_bil = {}
for j,f in enumerate(["C2H6","O2","CO2","H2O"]):
    _,_comp=_CH.composition(f); _sg=1 if j<2 else -1
    for _el,_k in _comp.items(): _bil[_el]=_bil.get(_el,0)+_sg*_c[j]*_k
check(_c==[2,7,4,6] and all(v==0 for v in _bil.values()), "oracle stoechiometrie : combustion C2H6 equilibree + conservation")
import trigonometrie as TRG
check(TRG.hypotenuse(3,4)==5.0 and TRG.sin_deg(30)==0.5, "oracle trigo : hypotenuse 3-4-5, sin30=0.5")
import calcul_infinitesimal as CIN
from fractions import Fraction as _F2
check(CIN.integrale_definie([0,0,1],0,3)==_F2(9) and CIN.limite_rationnelle_en([-1,0,1],[-1,1],1)==_F2(2),
      "oracle calcul : integrale x^2=9, limite (x2-1)/(x-1)=2")
import series_calcul as SER
check(SER.somme_geometrique_infinie(1,_F2(1,2))==_F2(2) and SER.somme_arithmetique(1,1,100)==_F2(5050),
      "oracle series : geometrique=2, Gauss=5050")
import mecanique as MEC, math as _m
check(MEC.force_frottement(0.5,100)==50.0 and abs(MEC.periode_ressort(1,1)-2*_m.pi)<1e-4,
      "oracle mecanique : frottement=50, T(1,1)=2pi")
check(abs(MEC.poussee_archimede(1000,1)-9806.65)<1e-1, "oracle mecanique : Archimede 1m3 eau = poids 1000kg")
import chimie_quantitative as CQU
check(abs(CQU.enthalpie_reaction([-393.5,2*-285.8],[-74.8,0])-(-890.3))<1e-2 and abs(CQU.potentiel_cellule(0.34,-0.76)-1.10)<1e-4,
      "oracle chimie quant : combustion CH4=-890.3, Daniell=1.10V")
import electronique as ELC, statique as STA
check(ELC.resistance_serie([10,20,30])==60.0 and abs(ELC.resistance_parallele([2,3,6])-1.0)<1e-6 and ELC.diviseur_tension(12,1000,2000)==8.0,
      "oracle electronique : serie=60, parallele=1, diviseur=8V")
_rg,_rd=STA.reactions_appui(100,1,4)
check(_rg==75.0 and _rd==25.0 and abs(_rg+_rd-100)<1e-9 and STA.force_levier(100,1,4)==25.0,
      "oracle statique : reactions 75/25 (conservation), levier 25N")
import robotique as ROB, controle as CTL
_x,_y=ROB.cinematique_directe_2r(2,1,90,-90)
check(abs(_x-1.0)<1e-4 and abs(_y-2.0)<1e-4, "oracle robotique : 2R(2,1,90,-90) = (1,2)")
check(CTL.est_stable([1,6,11,6]) is True and CTL.est_stable([1,1,1,6]) is False, "oracle controle : (s+1)(s+2)(s+3) stable, s3+s2+s+6 instable")
import equilibre_chimique as EQU, hydraulique as HYD
check(EQU.quotient_reaction([(2,2)],[(1,1),(1,3)])==4.0 and EQU.sens_evolution(4,10)=="direct", "oracle equilibre : Q=4, Q<K->direct")
check(HYD.nombre_reynolds(1000,1,0.1,0.001)==100000.0 and HYD.vitesse_continuite(2,1,0.5)==4.0, "oracle hydraulique : Re=1e5, continuite v2=4")
import reseaux_ip as RIP, architecture as ARC
check(RIP.adresse_reseau("192.168.1.130",24)=="192.168.1.0" and RIP.nombre_hotes(24)==254, "oracle reseaux : reseau .0, 254 hotes")
check(ARC.complement_a_deux(-1,8)==255 and ARC.depuis_complement_a_deux(255,8)==-1, "oracle archi : c2(-1,8)=255 aller-retour")
import bases_donnees as BDD, theorie_reseaux as TRX
check(len(BDD.jointure([{"id":1,"n":"a"}],[{"id":1,"s":9}],"id"))==1 and BDD.agregat([{"s":40},{"s":60}],"s","avg")==50.0,
      "oracle BD : jointure + agregat avg=50")
check(TRX.densite(3,[(0,1),(1,2),(2,0)])==1.0 and abs(TRX.densite(4,[(0,1),(0,2),(0,3)])-0.5)<1e-9, "oracle reseaux : densite triangle=1, etoile=0.5")
import telecom as TLC, reseaux_neurones as NRN
check(TLC.capacite_shannon(3000,7)==9000.0 and TLC.gain_db(100,1)==20.0, "oracle telecom : Shannon 9000 b/s, gain 20 dB")
check(NRN.neurone([1,1],[1,1],-1.5)==1 and NRN.neurone([1,0],[1,1],-1.5)==0, "oracle NN : perceptron ET(1,1)=1, ET(1,0)=0")
import blockchain as BCH, etats_matiere as ETM
_gg=BCH.cree_bloc(0,"g","0"); _bb=BCH.cree_bloc(1,"t",_gg["hash"])
check(BCH.chaine_valide([_gg,_bb]) is True and BCH.chaine_valide([_gg,dict(_bb,donnees="x")]) is False, "oracle blockchain : chaine valide vs falsifiee")
check(ETM.etat_physique(25,0,100)=="liquide" and ETM.celsius_vers_fahrenheit(100)==212.0, "oracle etats : eau 25C liquide, 100C=212F")
import cryptographie_appliquee as KAP, microprocesseurs as MPR
check(KAP.chiffre_vigenere("ATTACKATDAWN","LEMON")=="LXFOPVEFRNHR" and KAP.dechiffre_vigenere("LXFOPVEFRNHR","LEMON")=="ATTACKATDAWN",
      "oracle crypto appli : Vigenere LEMON canonique aller-retour")
_a=MPR.alu("add",100,28,8)
check(_a["debordement"] is True and _a["retenue"]==0, "oracle micro : 100+28 debordement signe sans retenue")
import cloud_distribue as CLD, big_data as BGD
check(CLD.quorum_coherent(3,2,2) is True and CLD.quorum_coherent(3,1,1) is False and CLD.cap_choix(True,"coherence")=="CP",
      "oracle cloud : quorum R+W>N, CAP CP")
check(BGD.compte_mots(["a a b"])=={"a":2,"b":1}, "oracle big_data : word-count {a:2,b:1}")
import web as WEB, geometrie_projective as GPR
from fractions import Fraction as _F3
check(WEB.specificite("#nav .item a")==(1,1,1) and WEB.balises_equilibrees("<div><p></div></p>") is False, "oracle web : specificite (1,1,1), imbrication croisee invalide")
_pp=[0,1,3,7]; _im=[GPR.homographie(x,2,1,1,3) for x in _pp]
check(GPR.birapport(*_pp)==GPR.birapport(*_im) and GPR.birapport(0,1,2,3)==_F3(4,3), "oracle projective : birapport invariant par homographie")
import geotechnique as GTC, genie_chimique as GCH
check(GTC.contrainte_effective(90,20)==70.0 and abs(GTC.coefficient_poussee_active(30)-1/3)<1e-4, "oracle geotech : Terzaghi 70, Ka(30)=1/3")
check(abs(GCH.conversion_cstr_ordre1(0.5,4)-2/3)<1e-4 and GCH.conversion_pfr_ordre1(0.5,4)>GCH.conversion_cstr_ordre1(0.5,4), "oracle genie chim : CSTR=2/3, PFR>CSTR")

# ── 3) CONTRÔLES NÉGATIFS — aucun faux positif ──
for absent in ["Satellites, sondes", "Faisabilité d'une synthèse donnée", "Cyberattaques (analyse)", "Capacités/limites d'une IA donnée",
               "", "xyz-inconnu", "Vols habités (histoire)"]:    # tous hors-registre (réellement pas encore couverts)
    check(C.couvert(absent) is False, f"contrôle négatif : '{absent[:30]}' non couvert")
check(C.couvert(None) is False, "contrôle négatif : None -> non couvert")
check(C.preuve_de("Satellites, sondes") is None, "preuve_de d'un absent -> None")
check(isinstance(C.preuve_de("Radioactivité"), str), "preuve_de d'un couvert -> description")

# ── 4) DÉTERMINISME ──
check(C.couvert("Statistique bayésienne") == C.couvert("Statistique bayésienne"), "déterminisme")
check(len(C.sujets_couverts()) == 303, "sujets_couverts() = 303")

print(f"\n=== valide_capacites : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
