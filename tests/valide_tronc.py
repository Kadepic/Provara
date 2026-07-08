# -*- coding: utf-8 -*-
"""Gate TRONC DE COMPRÉHENSION — Phase 1 (SPEC_TRONC_COMPREHENSION §7-§10) : `tronc.acte()` classe l'intention
dans la carte FERMÉE des 11 actes, extrait entités/relation/régime, tient l'ambiguïté en PARALLÈLE (G2), ne
tranche JAMAIS sans juge réel (G1/G7), et le REPLI HONNÊTE (G6) remplace le garbage : « voici ce que j'ai
compris + ce que je sais faire ». Ce banc EST la spec du comportement (règle d'or : on casse les caps si les
bancs passent — pas l'inverse)."""
import os
import sys
import tempfile

os.environ["TRONC_ROUTAGE_PATH"] = os.path.join(tempfile.mkdtemp(), "routage.jsonl")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import tronc as T  # noqa: E402

_ok = [0]
_ko = [0]


def check(cond, label):
    if cond:
        _ok[0] += 1
    else:
        _ko[0] += 1
        print("  FAIL:", label)


def meilleur(q, ctx=None):
    return T.acte(q, ctx).meilleur()


# ————————————————— (1) LA CARTE FERMÉE : chaque acte est reconnu par le CŒUR explicite —————————————————
check(meilleur("quelle est la capitale de la France ?").intention == T.INTERROGER_FAIT,
      "« capitale de la France » -> INTERROGER_FAIT")
check(meilleur("qui a écrit 1984 ?").intention == T.INTERROGER_FAIT, "« qui a écrit 1984 » -> INTERROGER_FAIT")
check(meilleur("combien font 2+2 ?").intention == T.CALCULER, "« combien font 2+2 » -> CALCULER")
check(meilleur("quelle différence entre un fleuve et une rivière ?").intention == T.RAISONNER,
      "« différence entre X et Y » -> RAISONNER")
check(meilleur("que penses-tu des voitures électriques ?").intention == T.DEMANDER_AVIS,
      "« que penses-tu de X » -> DEMANDER_AVIS")
check(meilleur("le meilleur entre la mer et la montagne ?").intention == T.DEMANDER_AVIS,
      "« le meilleur entre X et Y » -> DEMANDER_AVIS")
check(meilleur("aide-moi à inventer un objet pour la cuisine").intention == T.CREER,
      "« aide-moi à inventer » -> CRÉER")
check(meilleur("que sais-tu faire ?").intention == T.META, "« que sais-tu faire » -> MÉTA")
check(meilleur("bonjour").intention == T.SOCIAL, "« bonjour » -> SOCIAL")
check(meilleur("merci beaucoup, bonne journée !").intention == T.SOCIAL, "« merci bonne journée » -> SOCIAL")
check(meilleur("je suis perdu").intention == T.EXPRIMER_ETAT, "« je suis perdu » -> EXPRIMER_ÉTAT")
check(meilleur("quel temps fait-il à Toulouse ?").intention == T.QUOTIDIEN, "météo -> QUOTIDIEN")
check(meilleur("quelle heure est-il ?").intention == T.QUOTIDIEN, "heure -> QUOTIDIEN")
check(meilleur("regarde yohanfauck.fr").intention == T.QUOTIDIEN, "site nommé -> QUOTIDIEN (_cap_site)")
check(meilleur("traduis bonjour en espagnol").intention == T.AGIR, "« traduis » -> AGIR")
check(meilleur("oublie tout ce que je t'ai dit").intention == T.AGIR, "« oublie » (RGPD) -> AGIR")
check(meilleur("des trucs et des machins").intention == T.INCONNU, "garbage -> INCONNU (jamais deviné)")
check(len(T.ACTES) == 11, "la carte est FERMÉE : exactement 11 actes")
f_vide = T.acte("")
check(f_vide.candidats == () and f_vide.est_inconnu(), "signal vide -> faisceau vide, inconnu (no-op sûr)")

# ————————————————— (2) EXTRACTION : entités/relation UNE fois, régime du gardien de bornage —————————————————
m = meilleur("quelle est la capitale de la France ?")
check(m.relation == "capitale" and m.entites == ("france",), "extraction R de E : relation=capitale, entité=france")
check(m.regime == "borne", "régime attaché depuis classifieur_bornage (borné)")
m = meilleur("quelle différence entre un fleuve et une rivière ?")
check(m.entites == ("fleuve", "riviere"), "« entre X et Y » -> DEUX entités extraites")
m = meilleur("quel est le plus beau pays du monde ?")
check(m.regime == "non_borne", "subjectif -> régime non-borné (le gardien route, jamais dupliqué)")
m = meilleur("il est mort quand ?", {"anaphore": "Napoléon Ier"})
check(m.intention == T.INTERROGER_FAIT and m.entites == ("Napoléon Ier",),
      "anaphore du contexte résolue : « il est mort quand ? » -> entité = dernier sujet")

# ————————————————— (3) G1/G7 : TRANCHÉ exige un JUGE réel ; tout le reste est recette/supposition —————————————————
m = meilleur("combien font 2+2 ?")
check(m.statut == T.TRANCHE and m.reponse == "4", "calcul évalué -> TRANCHÉ, valeur exacte 4")
check("AST" in m.ancrage, "le TRANCHÉ est ANCRÉ (juge arithmétique AST, provenance déclarée)")
m = meilleur("combien font 2 + 2 fois 3 ?")
check(m.statut != T.TRANCHE, "« 2 + 2 fois 3 » (op verbale) -> JAMAIS tranché (fragment refusé, faille fermée)")
for q in ("quelle est la capitale de la France ?", "que penses-tu des voitures électriques ?",
          "je suis perdu", "bonjour"):
    for c in T.acte(q).candidats:
        check(c.statut != T.TRANCHE, "G1 : « %s » -> aucun candidat TRANCHÉ sans juge" % q[:30])
        if c.statut == T.NON_TRANCHE:
            check(c.reponse.startswith("faculté :"), "NON-TRANCHÉ porte une RECETTE (faculté), pas une valeur")

# ————————————————— (4) G2 : ambiguïté réelle -> candidats PARALLÈLES, jamais un choisi en silence —————————————————
f = T.acte("combien font 2+2 ?")
check(len(f.candidats) >= 2, "« combien font 2+2 » -> ≥2 candidats (calcul + fait), tenus en parallèle")
check(f.candidats[0].confiance >= f.candidats[1].confiance, "candidats ORDONNÉS par confiance (calibrée, pas devinée)")
f = T.acte("quelle différence entre un fleuve et une rivière ?")
check(len(f.candidats) >= 2, "comparaison -> RAISONNER + INTERROGER_FAIT en parallèle (G2)")
check(all(c.signal_discriminant for c in f.candidats), "chaque candidat porte son signal discriminant (§10)")
check(all(c.provenance for c in f.candidats), "chaque candidat porte sa provenance (lignée complète)")

# ————————————————— (5) PÉRIPHÉRIE gzip-kNN (U13) : PROPOSE (confiance bornée), jamais n'affirme —————————————————
m = meilleur("t'aurais pas un truc sur les fractions")
check(m.intention != T.INCONNU and m.confiance <= 0.45,
      "hors-motifs mais voisin d'exemples -> PROPOSITION gzip-kNN à confiance bornée (≤ 0,45)")
check("périphérie" in m.provenance, "la proposition est TRACÉE comme périphérie (propose -> l'humain vérifie)")
for q in ("des trucs et des machins", "des machins chouettes par la", "xyzzy blorp gnak"):
    check(meilleur(q).intention == T.INCONNU, "« %s » -> INCONNU honnête (voisinage trop lointain)" % q)

# ————————————————— (6) G6 : le REPLI HONNÊTE — « voici ce que j'ai compris + ce que je sais faire » —————————————————
r = T.repli("t'aurais pas un truc sur les fractions")
check(r.startswith(T._PFX_REPLI), "repli -> préfixe stable (classification positive de la porte unique)")
check("hypothèse" in r and "?" in r, "repli -> hypothèse TYPÉE (G7) + vraie question (porte, pas mur)")
check("sais faire" in r, "repli -> montre ce que Provara SAIT FAIRE (la brique anti « il comprend rien »)")
r = T.repli("des trucs et des machins")
check(r.startswith(T._PFX_REPLI) and "?" in r, "repli INCONNU total -> honnête + question, jamais muet")
check("capitale de l'Espagne" in r, "repli INCONNU -> liste les FAMILLES réelles (invitation concrète)")
for q in ("des trucs et des machins", "t'aurais pas un truc sur les fractions"):
    rr = T.repli(q)
    check("vouliez-vous dire" not in rr.lower(), "G5 : le repli ne fait JAMAIS de fausse correction ortho")
    check("d'après" not in rr.lower() and "http" not in rr.lower(),
          "G4 : le repli ne sert JAMAIS une recherche web du texte littéral")

# ————————————————— (7) ATTUNEMENT (§13) : état SUPPOSÉ, jamais ressenti ni jugé —————————————————
a = T.attunement("je suis perdu")
check(a is not None and a.startswith("Il se peut que"), "état exprimé -> attunement en SUPPOSITION")
check("je ne le ressens pas" in a, "anti-anthropomorphisme : jamais « je ressens » sans l'aveu machine")
check(T.attunement("quelle est la capitale de la France ?") is None, "pas d'état -> None (l'appelant continue)")
check(T.attunement("mon plat préféré est la ratatouille") is None,
      "une préférence n'est PAS un état exprimé -> None (le mémo garde sa voie)")

# ————————————————— (8) LE COMPOSITEUR (§10) — le coup CALCULÉ sur la forme du faisceau, jamais un choix —————————————————
def _cand(rel, rep, ok=True):
    return T.Candidat(intention=T.INTERROGER_FAIT, relation=rel, statut=T.TRANCHE if ok else T.NON_TRANCHE,
                      reponse=rep if ok else "", ancrage="lookup vérifié (lecteur)" if ok else "non ancré",
                      confiance=0.9 if ok else 0.0)


r = T.compose(T.Faisceau((_cand("superficie", "Superficie de la France : 551 695 km²."),
                          _cand("population", "Population de la France : 68 720 337 habitants."))), terme="taille")
check("Superficie de la France" in r and "Population de la France" in r,
      "divergence -> TOUTES les branches vérifiées servies conditionnellement (§10.2)")
check("peut vouloir dire plusieurs choses" in r and "Précise" in r,
      "divergence -> le certain + les lectures + l'INVITATION (une porte, pas un mur)")
r = T.compose(T.Faisceau((_cand("hauteur", "Hauteur de tour Eiffel : 330 m."),
                          _cand("superficie", "", ok=False), _cand("population", "", ok=False))), terme="taille")
check(r.startswith("Hauteur de tour Eiffel : 330 m.") and "superficie ou population" in r,
      "lecture unique servable -> mener avec le fait, SIGNALER les autres lectures (jamais en silence)")
r = T.compose(T.Faisceau((_cand("a", "X : 42."), _cand("b", "X : 42."))), terme="t")
check(r.startswith("X : 42.") and "concordent" in r,
      "convergence -> tronc commun servi + ambiguïté signalée non porteuse (§10.2, 1er cas)")
check(T.compose(T.Faisceau((_cand("a", "", ok=False), _cand("b", "", ok=False)))) is None,
      "aucune branche servie -> None (l'appelant garde sa cascade, jamais un texte vide)")
r = T.compose(T.Faisceau(tuple(_cand("r%d" % i, "R%d : %d." % (i, i)) for i in range(5))), terme="t")
check(r is not None and "trop de choses" in r and "R0 : 0." not in r,
      "trop de branches -> lister les lectures et laisser choisir (§10.2, dernier cas)")
check(set(T.RELATIONS_AMBIGUES) == {"taille", "grandeur", "dimension"},
      "carte FERMÉE des têtes de mesure ambiguës (s'étend par décision, jamais par dérive)")

# ————————————————— (9) CÂBLAGE repond : « taille de X » composée sur l'échantillon embarqué —————————————————
_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LECTEUR_DATASETS_DIR", os.path.join(_RACINE, "datasets", "lecteur"))
sys.path.insert(0, os.path.join(_RACINE, "interface"))
import repond as R  # noqa: E402

r = R._cap_mesure_ambigue("quelle est la taille de la France ?")
check(r is not None and "Superficie de la France" in r and "Population de la France" in r,
      "« taille de la France » -> COMPOSÉ superficie + population (fini le collapse silencieux sur superficie)")
check(r is not None and "Hauteur" not in r,
      "garde homonyme : jamais « Hauteur de France » (le paquebot) pour un PAYS — FAUX réel vécu 2026-07-07")
check(R._cap_mesure_ambigue("quelle est la hauteur de la tour Eiffel ?") is None,
      "tête NON ambiguë (« hauteur ») -> None (cascade existante inchangée)")
check(R._cap_mesure_ambigue("bonjour comment vas-tu ?") is None, "hors périmètre -> None (aucun détournement)")
# ROUTAGE PAR ACTE (Phase 5, retrait progressif) : la carte des familles est FERMÉE et cohérente avec les actes.
check(set(R._FAMILLES_ACTES) <= set(T.ACTES), "familles routées ⊆ carte des 11 actes (jamais un acte inventé)")
check(all(isinstance(v, tuple) and v for v in R._FAMILLES_ACTES.values()),
      "chaque famille routée est un tuple non vide de caps nommés")
check("interroger_fait" not in R._FAMILLES_ACTES and "raisonner" not in R._FAMILLES_ACTES,
      "les actes factuels/raisonnement NE sont PAS routés (détecteurs de caps plus fins que l'acte)")
# REGISTRE DU ROUTAGE (§16) : chaque décision tranchée est journalisée, l'erreur (hors-famille) MESURÉE, ET le
# COÛT de calcul (position du cap gagnant = profondeur de sonde) = le « − coût » de l'utilité §12 rendu observable.
check(T.stats_routage() == (0, 0, 0.0), "journal vierge -> (0, 0, 0.0), jamais une exception")
T.note_routage("quotidien", "quotidien", True, position=0)
T.note_routage("demander_avis", "definition", False, position=6)
_tot, _hors, _prof = T.stats_routage()
check((_tot, _hors) == (2, 1), "registre du routage : 2 décisions, 1 hors-famille (signal du séquenceur §11)")
check(_prof == 3.0, "profondeur de sonde moyenne mesurée = (0+6)/2 = 3.0 (coût de calcul post-hoc, §12)")

# ————————————————— (10) CÂBLAGE assistant_nl : l'indécidable sert le repli intent-aware —————————————————
os.environ.pop("IA_WEB", None)
import assistant_nl as A  # noqa: E402
A._TRANSPORT = None
r = A.apres_hors("t'aurais pas un truc sur les fractions", "c-tronc")
check(r is not None and r.statut == A.CLARIFICATION and r.texte.startswith(T._PFX_REPLI),
      "indécidable AVEC hypothèse -> repli honnête du tronc (CLARIFICATION intent-aware)")
check(r is not None and bool(r.attente), "repli du tronc -> attente déclarée (état conversationnel propre)")
A.oublie_etat("c-tronc2"); A._INDECIS.pop("c-tronc2", None)
r = A.apres_hors("des trucs et des machins", "c-tronc2")
check(r is not None and r.statut == A.CLARIFICATION,
      "indécidable SANS hypothèse -> clarification générique conservée (aucune régression)")
# ANAPHORE CÂBLÉE (§7 contexte) : le dernier sujet du pipeline nourrit le faisceau du repli.
R._DERNIER_SUJET["c-anaph"] = "la tour Eiffel"
A.oublie_etat("c-anaph"); A._INDECIS.pop("c-anaph", None)
r = A.apres_hors("il est genial non ?", "c-anaph")
check(r is not None and r.statut == A.CLARIFICATION and "la tour Eiffel" in r.texte and "AVIS" in r.texte,
      "« il est génial non ? » -> hypothèse AVIS à propos du DERNIER SUJET (anaphore du contexte, §7)")
R._DERNIER_SUJET.pop("c-anaph", None)

print("valide_tronc :", _ok[0], "OK,", _ko[0], "KO")
sys.exit(1 if _ko[0] else 0)
