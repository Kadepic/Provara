"""
VALIDE anatomie_systemes.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (faits anatomiques connus INDÉPENDAMMENT du module, écrits EN DUR ci-dessous) :
  • 206 os chez l'ADULTE — PAS chez le nouveau-né (~270, qui fusionnent) : ancre PIÈGE. Un module rendant
    206 pour le nouveau-né serait FAUX → on exige l'abstention sur toute demande pédiatrique.
  • Le cœur a 4 cavités (2 oreillettes + 2 ventricules).
  • 12 paires de nerfs crâniens (I à XII).
  • 33 vertèbres au total, dont 7 cervicales (répartition 7+12+5+5+4 = 33).
  • 24 côtes = 12 paires.
  • ANCRE DISCRIMINANTE FORTE : l'ARTÈRE PULMONAIRE transporte du sang DÉSOXYGÉNÉ (seule artère à le faire),
    les VEINES PULMONAIRES du sang OXYGÉNÉ. Un module disant « les artères sont oxygénées » serait FAUX.
  • Le foie appartient au système DIGESTIF ; les reins au système URINAIRE ; la rate au LYMPHATIQUE/immunitaire.
  • est_normal('frequence_cardiaque', 72) → True ; 40 → False.
  • Un organe inventé → ValueError.

SOUNDNESS : hors catalogue, pédiatrique, types (bool/str/NaN/inf), mauvaise arité → ValueError.
"""
import anatomie_systemes as A

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) LES 11 SYSTÈMES ──
sys_noms = A.liste_systemes()
check(len(sys_noms) == 11, "exactement 11 systèmes")
# noms attendus EN DUR (référentiel classique)
attendus = {"cardiovasculaire", "respiratoire", "digestif", "nerveux", "musculaire", "squelettique",
            "tégumentaire", "endocrinien", "lymphatique/immunitaire", "urinaire", "reproducteur"}
check(set(sys_noms) == attendus, "les 11 noms canoniques correspondent")

d = A.systeme("digestif")
check(isinstance(d["organes"], list) and "foie" in d["organes"], "système digestif contient le foie")
check("estomac" in d["organes"] and "intestin grêle" in d["organes"], "digestif contient estomac + grêle")
check(A.systeme("urinaire")["organes"].count("reins") == 1, "système urinaire contient les reins")
# copie défensive : muter la sortie ne corrompt pas le catalogue
d["organes"].append("XXX")
check("XXX" not in A.systeme("digestif")["organes"], "systeme() renvoie une copie défensive")
# alias
check(A.systeme("circulatoire")["nom"] == "cardiovasculaire", "alias circulatoire → cardiovasculaire")
check(A.systeme("immunitaire")["nom"] == "lymphatique/immunitaire", "alias immunitaire → lymphatique")

# ── 2) ORGANES → SYSTÈMES (ancres d'appartenance non circulaires) ──
check(A.organe("foie")["systeme"] == "digestif", "foie → digestif (ANCRE)")
check(A.organe("reins")["systeme"] == "urinaire", "reins → urinaire (ANCRE)")
check(A.organe("rate")["systeme"] == "lymphatique/immunitaire", "rate → lymphatique/immunitaire (ANCRE)")
check(A.organe("cœur")["systeme"] == "cardiovasculaire", "cœur → cardiovasculaire")
check(A.organe("poumons")["systeme"] == "respiratoire", "poumons → respiratoire")
check(A.organe("cerveau")["systeme"] == "nerveux", "cerveau → nerveux")
check(A.organe("thyroïde")["systeme"] == "endocrinien", "thyroïde → endocrinien")
check(A.organe("peau")["systeme"] == "tégumentaire", "peau → tégumentaire")
check(A.organe("vessie")["systeme"] == "urinaire", "vessie → urinaire")
check(A.organe("œsophage")["systeme"] == "digestif", "œsophage → digestif")
# accents optionnels + alias
check(A.organe("thyroide")["systeme"] == "endocrinien", "sans accent : thyroide → endocrinien")
check(A.organe("oesophage")["nom"] == "œsophage", "oesophage → œsophage (translit)")
check(A.organe("rein")["nom"] == "reins", "alias rein → reins")
check(A.organe("colon")["nom"] == "gros intestin", "alias colon → gros intestin")
# chaque organe expose les 4 champs
o = A.organe("estomac")
check(set(o.keys()) == {"nom", "systeme", "fonction", "localisation"}, "organe expose 4 champs")
check(isinstance(o["fonction"], str) and isinstance(o["localisation"], str), "champs texte non vides")
# les 16 organes minimum du catalogue existent
for nm in ["cœur", "poumons", "foie", "reins", "estomac", "intestin grêle", "gros intestin", "cerveau",
           "moelle épinière", "pancréas", "rate", "vessie", "thyroïde", "œsophage", "diaphragme", "peau"]:
    check(A.organe(nm)["nom"] == nm, f"organe présent : {nm}")

# ── 3) CHIFFRES ANATOMIQUES ÉTABLIS (ancres EN DUR) ──
check(A.chiffre_anatomique("os_adulte") == 206, "206 os chez l'adulte (ANCRE)")
check(A.chiffre_anatomique("cavites_cardiaques") == 4, "4 cavités cardiaques (ANCRE)")
check(A.chiffre_anatomique("oreillettes") == 2 and A.chiffre_anatomique("ventricules") == 2,
      "2 oreillettes + 2 ventricules")
check(A.chiffre_anatomique("paires_nerfs_craniens") == 12, "12 paires de nerfs crâniens (ANCRE)")
check(A.chiffre_anatomique("vertebres") == 33, "33 vertèbres (ANCRE)")
check(A.chiffre_anatomique("cotes") == 24, "24 côtes (ANCRE)")
check(A.chiffre_anatomique("paires_cotes") == 12, "12 paires de côtes")
check(A.chiffre_anatomique("reins") == 2, "2 reins")
check(A.chiffre_anatomique("foie") == 1, "1 foie")
# alias
check(A.chiffre_anatomique("os") == 206, "alias 'os' → 206")
check(A.chiffre_anatomique("nerfs craniens") == 12, "alias 'nerfs craniens' → 12")

# ── 3bis) ANCRE PIÈGE : nouveau-né ≠ 206 (le module DOIT s'abstenir, jamais rendre 206) ──
check(leve(A.chiffre_anatomique, "os_nouveau_ne"), "os nouveau-né → ValueError (pas 206) — ANCRE PIÈGE")
check(leve(A.chiffre_anatomique, "os_bebe"), "os bébé → ValueError (pédiatrique)")
check(leve(A.chiffre_anatomique, "os_enfant"), "os enfant → ValueError (pédiatrique)")

# ── 3ter) RÉPARTITION DES VERTÈBRES (somme = 33, 7 cervicales) ──
v = A.vertebres()
check(v["total"] == 33, "vertèbres total = 33")
check(v["cervicales"] == 7, "7 vertèbres cervicales (ANCRE)")
check(v["thoraciques"] == 12 and v["lombaires"] == 5, "12 thoraciques + 5 lombaires")
check(v["sacrees"] == 5 and v["coccygiennes"] == 4, "5 sacrées + 4 coccygiennes (fusionnées)")
# la somme des parties = total (cohérence non circulaire : 7+12+5+5+4 calculé à la main)
check(v["cervicales"] + v["thoraciques"] + v["lombaires"] + v["sacrees"] + v["coccygiennes"] == 33,
      "7+12+5+5+4 = 33 (somme des parties)")
check(7 + 12 + 5 + 5 + 4 == v["total"], "somme calculée main = total")

# ── 4) PHYSIOLOGIE — INTERVALLES (jamais scalaire) ──
lo, hi, u = A.valeur_normale("frequence_cardiaque")
check((lo, hi, u) == (60.0, 100.0, "bpm"), "FC normale = 60-100 bpm")
check(A.valeur_normale("pression_systolique") == (90.0, 120.0, "mmHg"), "PAS = 90-120 mmHg")
check(A.valeur_normale("frequence_respiratoire") == (12.0, 20.0, "/min"), "FR = 12-20 /min")
check(A.valeur_normale("temperature") == (36.1, 37.2, "°C"), "T° = 36.1-37.2 °C")
check(A.valeur_normale("debit_cardiaque") == (4.0, 8.0, "L/min"), "DC = 4-8 L/min")
# c'est bien un intervalle (min < max)
for p in A.liste_parametres():
    lp, hp, _ = A.valeur_normale(p)
    check(lp < hp, f"intervalle strict min<max pour {p}")

# ── 4bis) est_normal — ancres 72 True, 40 False ──
check(A.est_normal("frequence_cardiaque", 72) is True, "est_normal(FC, 72) = True (ANCRE)")
check(A.est_normal("frequence_cardiaque", 40) is False, "est_normal(FC, 40) = False (ANCRE)")
check(A.est_normal("frequence_cardiaque", 60) is True, "est_normal(FC, 60) = True (borne basse incluse)")
check(A.est_normal("frequence_cardiaque", 100) is True, "est_normal(FC, 100) = True (borne haute incluse)")
check(A.est_normal("frequence_cardiaque", 101) is False, "est_normal(FC, 101) = False")
check(A.est_normal("temperature", 37.0) is True, "est_normal(T°, 37.0) = True")
check(A.est_normal("temperature", 40.0) is False, "est_normal(T°, 40.0) = False (fièvre)")
check(A.est_normal("pouls", 72) is True, "alias pouls → FC")

# ── 5) CIRCULATION SANGUINE — trajet exact (ancre écrite EN DUR) ──
attendu_trajet = (
    "oreillette droite", "ventricule droit", "artère pulmonaire", "poumons",
    "veines pulmonaires", "oreillette gauche", "ventricule gauche", "aorte",
)
check(A.circulation_sanguine() == attendu_trajet, "trajet du sang exact (8 étapes)")
check(A.circulation_sanguine()[0] == "oreillette droite", "départ = oreillette droite")
check(A.circulation_sanguine()[-1] == "aorte", "arrivée = aorte")
# poumons entre artère pulmonaire et veines pulmonaires
t = A.circulation_sanguine()
check(t.index("artère pulmonaire") < t.index("poumons") < t.index("veines pulmonaires"),
      "ordre : artère pulmonaire → poumons → veines pulmonaires")

# ── 5bis) OXYGÉNATION — ANCRE DISCRIMINANTE FORTE ──
check(A.oxygenation("artère pulmonaire") == "désoxygéné",
      "artère pulmonaire = DÉSOXYGÉNÉ (ANCRE forte, contre-intuitif)")
check(A.oxygenation("veines pulmonaires") == "oxygéné",
      "veines pulmonaires = OXYGÉNÉ (ANCRE forte)")
check(A.oxygenation("aorte") == "oxygéné", "aorte = oxygéné")
check(A.oxygenation("veine cave") == "désoxygéné", "veine cave = désoxygéné")
# la discrimination : artère pulmonaire et aorte diffèrent (sinon règle naïve)
check(A.oxygenation("artère pulmonaire") != A.oxygenation("aorte"),
      "artère pulmonaire ≠ aorte en oxygénation (piège déjoué)")

# ── 6) SOUNDNESS — hors catalogue / organe inventé ──
check(leve(A.organe, "phlogistique"), "organe inventé → ValueError (ANCRE)")
check(leve(A.organe, "rate de dragon"), "organe fantaisiste → ValueError")
check(leve(A.systeme, "psychique"), "système inexistant → ValueError")
check(leve(A.chiffre_anatomique, "nombre de dents en or"), "compte inconnu → ValueError")
check(leve(A.valeur_normale, "taux de bonheur"), "paramètre inconnu → ValueError")
check(leve(A.est_normal, "taux de bonheur", 5), "est_normal param inconnu → ValueError")
check(leve(A.oxygenation, "canal lymphatique"), "vaisseau hors catalogue → ValueError")

# ── 7) SOUNDNESS — types invalides ──
check(leve(A.organe, True), "organe(bool) → ValueError")
check(leve(A.organe, 42), "organe(int) → ValueError")
check(leve(A.organe, None), "organe(None) → ValueError")
check(leve(A.systeme, ["digestif"]), "systeme(list) → ValueError")
check(leve(A.est_normal, "frequence_cardiaque", True), "est_normal valeur bool → ValueError")
check(leve(A.est_normal, "frequence_cardiaque", "72"), "est_normal valeur str → ValueError")
check(leve(A.est_normal, "frequence_cardiaque", float("nan")), "est_normal valeur NaN → ValueError")
check(leve(A.est_normal, "frequence_cardiaque", float("inf")), "est_normal valeur inf → ValueError")
check(leve(A.est_normal, "frequence_cardiaque", float("-inf")), "est_normal valeur -inf → ValueError")

# ── 8) DÉTERMINISME ──
check(A.organe("foie") == A.organe("foie"), "déterminisme organe")
check(A.circulation_sanguine() == A.circulation_sanguine(), "déterminisme circulation")
check(A.valeur_normale("temperature") == A.valeur_normale("temperature"), "déterminisme valeur_normale")
check(A.est_normal("frequence_cardiaque", 72) == A.est_normal("frequence_cardiaque", 72),
      "déterminisme est_normal")
check(A.vertebres() == A.vertebres(), "déterminisme vertèbres")

print(f"\n=== valide_anatomie_systemes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
