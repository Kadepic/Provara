"""
VALIDE versification_fr.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES : des vers CÉLÈBRES dont le compte syllabique est établi par la tradition
métrique, écrits en dur avec leur compte, et jamais recalculés par le module.
  • Verlaine, « Je fais souvent ce rêve étrange et pénétrant » — alexandrin (12). C'est l'ancre PIÈGE : une
    règle « -ent toujours muet » y compte 11 (elle avale le « -vent » de « souvent »), et une règle
    « -ent toujours sonore » compte 12 mais se trompe ailleurs. Seul le traitement AMBIGU s'en sort.
  • Hugo, « Demain, dès l'aube, à l'heure où blanchit la campagne » — alexandrin (12), avec deux élisions
    (« l'aube à », « l'heure où ») et un « e » muet final (« campagne »).
  • La Fontaine, « Maître Corbeau, sur un arbre perché » — décasyllabe (10).
  • « Un cheval blanc » — 4 (compté à la main).

ANCRE D'HONNÊTETÉ (la plus importante) : un vers contenant « lion », « hier » ou « nuage » doit rendre un
INTERVALLE, et `est_alexandrin` doit rendre 'indéterminé' quand 12 y est contenu sans être forcé. Un module
qui trancherait serait FAUX — la synérèse/diérèse n'est pas décidable orthographiquement.

SOUNDNESS : vers vide, non-str, bool, sans voyelle, mètre hors catalogue, césure d'un vers ambigu, rime sans
finale commune, quatrain de taille ≠ 4, schéma non reconnu -> ValueError. Déterminisme vérifié.
"""
import sys

import versification_fr as V

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


# ── 1) ANCRES EXTERNES : vers célèbres, comptes établis, écrits en dur ──
VERLAINE = "Je fais souvent ce rêve étrange et pénétrant"
HUGO = "Demain, dès l'aube, à l'heure où blanchit la campagne"
LAFONTAINE = "Maître Corbeau, sur un arbre perché"

check(V.compte_syllabes(VERLAINE) == (12, 12), "Verlaine : alexandrin CERTAIN de 12 syllabes")
check(V.compte_syllabes(HUGO) == (12, 12), "Hugo : alexandrin CERTAIN de 12 syllabes")
check(V.compte_syllabes(LAFONTAINE) == (10, 10), "La Fontaine : décasyllabe CERTAIN de 10 syllabes")
check(V.compte_syllabes("Un cheval blanc") == (4, 4), "« Un cheval blanc » = 4 (compté à la main)")

check(V.est_alexandrin(VERLAINE) is True, "Verlaine : est_alexandrin -> True")
check(V.est_alexandrin(HUGO) is True, "Hugo : est_alexandrin -> True")
check(V.est_alexandrin(LAFONTAINE) is False, "décasyllabe : est_alexandrin -> False")

# ── 2) L'ANCRE PIÈGE : « souvent » n'est PAS une désinence verbale ──
check(V.compte_syllabes("souvent")[0] == 2, "« souvent » : 2 syllabes, finale SONORE (pas de -ent muet)")
check(V.compte_syllabes("souvent") == (2, 2), "« souvent » : compte CERTAIN (liste _ENT_SONORE)")
check("souvent" in V._ENT_SONORE, "« souvent » figure dans la liste fermée des -ent non verbaux")
check(V.compte_syllabes("moment") == (2, 2), "« moment » : 2 syllabes, certain")
# a contrario, une forme verbale probable reste AMBIGUË : on ne devine pas la morphologie
mn, mx = V.compte_syllabes("chantent")
check(mn == 1 and mx == 2, "« chantent » : AMBIGU (1 si désinence verbale muette, 2 sinon)")
check(mn < mx, "le module ne devine pas si « chantent » est un verbe")

# ── 3) ÉLISION du « e » : certaine, jamais ambiguë ──
check(V.compte_syllabes("rose")[0] == 1, "« rose » en fin de vers : le e final est muet (1)")
check(V.compte_syllabes("rose") == (1, 1), "« rose » : compte certain")
check(V.compte_syllabes("roses") == (1, 1), "« roses » : -es final muet")
check(V.compte_syllabes("ce") == (1, 1), "« ce » : e unique, jamais élidé par cette règle")
check(V.compte_syllabes("je") == (1, 1), "« je » : e unique -> 1")
# « rêve étrange » : le e de « rêve » s'élide devant la voyelle de « étrange »
check(V.compte_syllabes("rêve étrange") == (3, 3), "élision devant voyelle : rê + é + tran = 3")
check(V.compte_syllabes("rêve blanc") == (3, 3), "sans élision : rê + ve + blanc = 3")

# ── 4) ANCRE D'HONNÊTETÉ : la diérèse n'est PAS tranchée ──
for mot in ("lion", "hier", "nuage", "viande", "jouer"):
    a, b = V.compte_syllabes(mot)
    check(a < b, f"« {mot} » : intervalle rendu (synérèse/diérèse indécidable)")
    check(b - a == 1, f"« {mot} » : exactement une ambiguïté")

# « ui » est monosyllabique en usage classique : PAS d'ambiguïté
check(V.compte_syllabes("nuit") == (1, 1), "« nuit » : ui monosyllabique, compte certain")
check(V.compte_syllabes("lui") == (1, 1), "« lui » : ui monosyllabique")

# un vers dont l'intervalle CONTIENT 12 sans le forcer -> 'indéterminé', jamais True ni False
ambigu = "Le lion rugit encore au fond du vieux jardin fier"
a, b = V.compte_syllabes(ambigu)
if a <= 12 <= b and a != b:
    check(V.est_alexandrin(ambigu) == "indéterminé", "12 dans l'intervalle sans y être forcé -> 'indéterminé'")
else:
    check(True, "(vers de contrôle non ambigu autour de 12 : cas non déclenché)")
check(V.est_alexandrin("Un cheval blanc") is False, "compte certain ≠ 12 -> False (pas 'indéterminé')")

# ── 5) MÈTRES ──
check(V.nom_metre(12) == "alexandrin", "12 -> alexandrin")
check(V.nom_metre(10) == "décasyllabe", "10 -> décasyllabe")
check(V.nom_metre(8) == "octosyllabe", "8 -> octosyllabe")
check(leve(V.nom_metre, 13), "13 syllabes -> ValueError (hors catalogue)")
check(leve(V.nom_metre, 12.0), "compte flottant -> ValueError")
check(leve(V.nom_metre, True), "bool -> ValueError")

# ── 6) HÉMISTICHES : coupe à la 6ᵉ syllabe d'un alexandrin CERTAIN ──
g, d = V.hemistiche(VERLAINE)
check(V.compte_syllabes(g)[0] >= 5, "hémistiche gauche non vide")
check(g and d and g != d, "deux hémistiches distincts")
check(leve(V.hemistiche, LAFONTAINE), "césure d'un décasyllabe -> ValueError (pas un alexandrin)")
check(leve(V.hemistiche, ambigu), "césure d'un vers ambigu -> ValueError (on ne coupe pas au hasard)")

# ── 7) RIMES ──
check(V.genre_rime("rose") == "féminine", "« rose » : rime féminine")
check(V.genre_rime("roses") == "féminine", "« roses » : rime féminine")
check(V.genre_rime("chantent") == "féminine", "« chantent » : rime féminine")
check(V.genre_rime("amour") == "masculine", "« amour » : rime masculine")
check(V.genre_rime("blanc") == "masculine", "« blanc » : rime masculine")
check(V.type_rime("flamme", "âme") == "suffisante", "flamme/âme : 2 lettres communes -> suffisante")
# jardin/matin ne partagent que « in » (2 lettres) : la rime est SUFFISANTE, pas riche.
check(V.type_rime("jardin", "matin") == "suffisante", "jardin/matin : 2 lettres communes -> suffisante")
check(V.type_rime("jardin", "gradin") == "riche", "jardin/gradin : « din » commun -> riche")
check(V.type_rime("beau", "eau") == "riche", "beau/eau -> riche")
check(leve(V.type_rime, "chien", "table"), "aucune finale commune -> ValueError (ce n'est pas une rime)")

check(V.schema_rimes(["le vent", "la dent", "le jour", "l'amour"]) == "AABB", "rimes plates AABB")
check(V.schema_rimes(["le vent", "le jour", "la dent", "l'amour"]) == "ABAB", "rimes croisées ABAB")
check(V.schema_rimes(["le vent", "le jour", "l'amour", "la dent"]) == "ABBA", "rimes embrassées ABBA")
check(leve(V.schema_rimes, ["a", "b", "c"]), "3 vers -> ValueError (quatrain requis)")
check(leve(V.schema_rimes, ["le chien", "la table", "le stylo", "la lampe"]), "aucun schéma -> ValueError")

# ── 8) SOUNDNESS ──
check(leve(V.compte_syllabes, ""), "vers vide -> ValueError")
check(leve(V.compte_syllabes, "   "), "vers blanc -> ValueError")
check(leve(V.compte_syllabes, 12), "entier -> ValueError")
check(leve(V.compte_syllabes, True), "bool -> ValueError")
check(leve(V.compte_syllabes, None), "None -> ValueError")
check(leve(V.compte_syllabes, "!!! ??? ..."), "vers sans voyelle -> ValueError")
check(leve(V.genre_rime, ""), "genre_rime('') -> ValueError")
check(leve(V.genre_rime, 3), "genre_rime(int) -> ValueError")
check(leve(V.est_alexandrin, ""), "est_alexandrin('') -> ValueError")

# ── 9) DÉTERMINISME ──
check(V.compte_syllabes(VERLAINE) == V.compte_syllabes(VERLAINE), "déterminisme du compte")
check(V.est_alexandrin(HUGO) == V.est_alexandrin(HUGO), "déterminisme d'est_alexandrin")
check(V.hemistiche(VERLAINE) == V.hemistiche(VERLAINE), "déterminisme de la césure")
check(V.schema_rimes(["le vent", "la dent", "le jour", "l'amour"])
      == V.schema_rimes(["le vent", "la dent", "le jour", "l'amour"]), "déterminisme du schéma")

# ── 10) COHÉRENCE : le minimum ne dépasse jamais le maximum ──
for v in (VERLAINE, HUGO, LAFONTAINE, "Un cheval blanc", ambigu, "Le lion et le rat"):
    a, b = V.compte_syllabes(v)
    check(1 <= a <= b, f"invariant min ≤ max pour « {v[:26]}… »")

print(f"\n=== valide_versification_fr : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
