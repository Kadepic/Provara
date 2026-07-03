"""
VALIDATION du MOTEUR DE RÈGLES NORMATIVES (regle.py).

Cœur = la SOUNDNESS du jugement par règle posée + la CAPACITÉ D'APPRENDRE un domaine par ingestion :
  - une règle absente n'est jamais inventée ; scoping et dating exacts ;
  - conformité émise UNIQUEMENT via un prédicat propre sur un cas complet, sinon ABSTENTION
    (interprétation, donnée manquante, règle non en vigueur) -> jamais une fausse conformité ;
  - hiérarchie des normes formelle ; déterminisme ;
  - on APPREND un référentiel INÉDIT à chaud et on l'interroge correctement aussitôt.
"""
from __future__ import annotations

from garde_ressources import borne
import regle as R

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# 1) LOOKUP scopé : présent -> Regle ; absent -> None (jamais inventé)
check("lookup présent (hygiène, conservation réfrigérée)",
      R.cherche_partout("secteur alimentaire", "Conservation réfrigérée") is not None)
check("lookup absent -> None (règle non inventée)",
      R.cherche_partout("FR", "Article inexistant 999") is None)

# 2) SCOPING : même type de question sous deux portées ne se mélange pas
check("scoping : un ident FR n'est pas trouvé sous la portée UE",
      R.cherche_partout("UE", "Code civil art. 414") is None
      and R.cherche_partout("FR", "Code civil art. 414") is not None)

# 3) CONFORMITÉ par prédicat explicite (cas non ambigu)
temp = R.cherche_partout("secteur alimentaire", "Conservation réfrigérée")
check("température 3 °C -> CONFORME", R.applique(temp, {"temperature": 3}).statut == R.CONFORME)
check("température 8 °C -> NON_CONFORME", R.applique(temp, {"temperature": 8}).statut == R.NON_CONFORME)
maj = R.cherche_partout("FR", "Code civil art. 414")
check("âge 20 -> CONFORME (majeur)", R.applique(maj, {"age": 20}).statut == R.CONFORME)
check("âge 16 -> NON_CONFORME", R.applique(maj, {"age": 16}).statut == R.NON_CONFORME)
casque = R.cherche_partout("ACME", "Port du casque")
check("casque porté=True -> CONFORME", R.applique(casque, {"casque_porte": True}).statut == R.CONFORME)
check("casque porté=False -> NON_CONFORME", R.applique(casque, {"casque_porte": False}).statut == R.NON_CONFORME)

# 4) ABSTENTION (jamais de fausse conformité) : donnée manquante / interprétation
check("champ manquant -> ABSTENTION (on ne devine pas)",
      R.applique(temp, {"autre": 1}).statut == R.ABSTENTION)
vp = R.cherche_partout("FR", "Code civil art. 9")   # vie privée : pas de prédicat -> interprétation
check("règle d'interprétation (vie privée) -> ABSTENTION", R.applique(vp, {"x": 1}).statut == R.ABSTENTION)
rgpd = R.cherche_partout("UE", "RGPD art. 5")
check("RGPD art.5 (principes) -> ABSTENTION sur conformité", R.applique(rgpd, {}).statut == R.ABSTENTION)

# 5) DATING : une règle hors de sa fenêtre de validité n'est pas appliquée
abrogee = R.Regle("ref", "test", "TEST", "X", "contenu", "2000-01-01", R.R_LOI,
                  jusqua="2010-01-01", predicat=(">=", "v", 0))
check("règle abrogée non en vigueur aujourd'hui", not abrogee.en_vigueur("2026-06-22"))
check("règle abrogée -> ABSTENTION (datée)", R.applique(abrogee, {"v": 5}).statut == R.ABSTENTION)
check("règle en vigueur à une date dans sa fenêtre", abrogee.en_vigueur("2005-06-01"))
future = R.Regle("ref", "test", "TEST", "Y", "c", "2030-01-01", R.R_LOI, predicat=(">=", "v", 0))
check("règle pas encore en vigueur -> non appliquée", not future.en_vigueur("2026-06-22"))

# 6) HIÉRARCHIE des normes : la règle de rang supérieur prévaut
check("hiérarchie : UE prévaut sur règle interne", R.prevaut(rgpd, casque).rang == R.R_UE)
check("hiérarchie : loi prévaut sur règlement", R.prevaut(maj, temp).ident == maj.ident)

# 7) MULTI-DOMAINES : la base couvre plusieurs domaines distincts (généricité = « les faire tous »)
domaines = {r.domaine for ref in R.BASE for r in ref.regles.values()}
check(f"couverture multi-domaines ({len(domaines)} domaines distincts ≥ 4)", len(domaines) >= 4)

# 8) APPRENTISSAGE À CHAUD d'un domaine INÉDIT (jamais vu) -> interrogeable aussitôt, sound
#    (ex. seuil de bruit sur lieu de travail — référentiel fictif, démontre la CAPACITÉ d'apprendre)
nouveau = R.Referentiel("Référentiel inédit", "autorité test").apprend([
    R.Regle("réf. test", "santé au travail", "FR", "Seuil de bruit",
            "Le niveau d'exposition au bruit ne doit pas dépasser 87 dB(A).", "2006-02-15", R.R_REGLEMENT,
            predicat=("<=", "bruit_dba", 87)),
])
seuil = nouveau.cherche("FR", "Seuil de bruit")
check("domaine inédit appris : règle retrouvée", seuil is not None)
check("domaine inédit : 90 dB(A) -> NON_CONFORME", R.applique(seuil, {"bruit_dba": 90}).statut == R.NON_CONFORME)
check("domaine inédit : 80 dB(A) -> CONFORME", R.applique(seuil, {"bruit_dba": 80}).statut == R.CONFORME)
check("domaine inédit : règle inconnue dans ce référentiel -> None",
      nouveau.cherche("FR", "Autre seuil") is None)

# 9) INGESTION SÛRE : un conflit de règle contradictoire (même clé+date, contenu divergent) est REJETÉ
conflit_leve = False
try:
    R.Referentiel("x", "y").apprend([
        R.Regle("a", "d", "S", "I", "contenu A", "2020-01-01", R.R_LOI),
        R.Regle("a", "d", "S", "I", "contenu B", "2020-01-01", R.R_LOI),
    ])
except ValueError:
    conflit_leve = True
check("ingestion : conflit contradictoire rejeté (pas d'écrasement silencieux)", conflit_leve)

# 10) DÉTERMINISME
check("déterministe", R.applique(temp, {"temperature": 3}).statut == R.applique(temp, {"temperature": 3}).statut)

# 10bis) APPRENDRE/CRÉER une règle À PARTIR D'EXEMPLES étiquetés (cas, conforme) — sans le texte.
# (A) cas booléen net -> APPRIS, prédicat correct
st, pred = R.apprend_predicat([({"casque_porte": True}, True), ({"casque_porte": False}, False)])
check("apprend (booléen net) -> APPRIS", st == R.APPRIS)
check("prédicat appris classe un cas neuf correctement",
      pred is not None and R.evalue_predicat(pred, {"casque_porte": False}) is False)
# (B) numérique avec frontière ENTIÈRE cernée (2 conforme, 3 non) -> APPRIS, cohérent avec les exemples
exs = [({"t": 1}, True), ({"t": 2}, True), ({"t": 3}, False), ({"t": 9}, False)]
st, pred = R.apprend_predicat(exs)
check("apprend (numérique, frontière entière cernée) -> APPRIS", st == R.APPRIS)
check("prédicat numérique appris reproduit tous les exemples",
      all(R.evalue_predicat(pred, c) == lab for c, lab in exs))
# (C) ANTI-HALLUCINATION : exemples trop lâches (seuil non cerné) -> AMBIGU, pas d'invention de seuil
st, pred = R.apprend_predicat([({"t": 3}, True), ({"t": 8}, False)])
check("apprend (seuil sous-déterminé) -> AMBIGU (pas de fausse précision)", st == R.AMBIGU and pred is None)
# (C2) PLAGE (intervalle a<=x<=b) appris depuis des cas étiquetés à bornes SERRÉES (zone vraie encadrée de faux).
st, pred = R.apprend_predicat(
    [({"t": 3}, True), ({"t": 4}, True), ({"t": 5}, True), ({"t": 6}, True),
     ({"t": 2}, False), ({"t": 7}, False), ({"t": 0}, False), ({"t": 9}, False)],
    [({"t": 5}, True), ({"t": 8}, False)])
check("apprend une PLAGE (intervalle) depuis cas étiquetés serrés",
      st == R.APPRIS and pred[0] == "plage" and R.evalue_predicat(pred, {"t": 4}) and not R.evalue_predicat(pred, {"t": 8}))
# plage sous-déterminée (bornes non cernées) -> AMBIGU (pas de fausses bornes)
st, _ = R.apprend_predicat([({"t": 5}, True), ({"t": 1}, False), ({"t": 11}, False)])
check("plage sous-déterminée -> AMBIGU (pas de fausses bornes)", st in (R.AMBIGU, R.HORS))
# (D) hors famille seuil/égalité (labels non monotones sur 1 champ) -> HORS honnête
st, pred = R.apprend_predicat([({"a": 1}, True), ({"a": 2}, False), ({"a": 3}, True)])
check("apprend (hors famille seuil) -> HORS", st == R.HORS and pred is None)
# (E) SOUNDNESS : un prédicat APPRIS ne se trompe sur AUCUN exemple étiqueté
st, pred = R.apprend_predicat(exs)
check("INVARIANT : prédicat appris correct sur 100% des exemples étiquetés",
      st == R.APPRIS and all(R.evalue_predicat(pred, c) == lab for c, lab in exs))
# (F) INTÉGRATION : on coud le prédicat appris dans une Regle et on juge un cas neuf
appr = R.Regle("appris des données", "santé au travail", "FR", "Seuil appris",
               "règle dont le seuil a été appris à partir de cas observés", "2020-01-01", R.R_REGLEMENT,
               predicat=pred)
check("règle à prédicat APPRIS juge un cas neuf (CONFORME/NON_CONFORME)",
      R.applique(appr, {"t": 1}).statut in (R.CONFORME, R.NON_CONFORME))

# 11) INVARIANT GLOBAL : sur toute la base, jamais CONFORME/NON_CONFORME sans prédicat propre.
inv = True
for ref in R.BASE:
    for r in ref.regles.values():
        j = R.applique(r, {})   # cas vide
        if r.predicat is None and j.statut in (R.CONFORME, R.NON_CONFORME):
            inv = False
check("INVARIANT : aucune conformité affirmée sans prédicat explicite (jamais de faux)", inv)

print(f"\nREGLE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
