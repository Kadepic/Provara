"""
VALIDE conjugaison.py — ADVERSARIAL. Ancres de conjugaison CONNUES (mécanisme réglé : 1er groupe -er, 2e groupe
-ir/-issant) + SOUNDNESS (irrégulier / 3e groupe / -ir incertain / particularité orthographique / personne hors
1..6 / temps non géré / type invalide -> ValueError, jamais une forme fausse) + DÉTERMINISME.

Aucune des formes émises ici n'est « re-dérivée » par le module : ce sont des conjugaisons de référence connues.
"""
import conjugaison as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def abst(fn, *a, **k):
    """True ssi l'appel ABSTIENT proprement (ValueError) — toute autre issue = échec de soundness."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — 1er groupe `parler` (présent complet, personnes 1..6) ──
check(M.conjugue("parler", 1, "present") == "parle", "parler/je -> parle")
check(M.conjugue("parler", 2, "present") == "parles", "parler/tu -> parles")
check(M.conjugue("parler", 3, "present") == "parle", "parler/il -> parle")
check(M.conjugue("parler", 4, "present") == "parlons", "parler/nous -> parlons")
check(M.conjugue("parler", 5, "present") == "parlez", "parler/vous -> parlez")
check(M.conjugue("parler", 6, "present") == "parlent", "parler/ils -> parlent")

# ── 2) ANCRES — autres 1er groupe réguliers (held-out, jamais cités dans le module) ──
check(M.conjugue("donner", 1, "present") == "donne", "donner/je -> donne")
check(M.conjugue("donner", 4, "present") == "donnons", "donner/nous -> donnons")
check(M.conjugue("aimer", 1, "present") == "aime", "aimer/je -> aime")
check(M.conjugue("aimer", 6, "present") == "aiment", "aimer/ils -> aiment")
check(M.conjugue("jouer", 4, "present") == "jouons", "jouer/nous -> jouons")
check(M.conjugue("chanter", 5, "present") == "chantez", "chanter/vous -> chantez")
check(M.conjugue("travailler", 3, "present") == "travaille", "travailler/il -> travaille")
check(M.conjugue("créer", 1, "present") == "crée", "créer/je -> crée (radical en voyelle, pas de changement)")
check(M.conjugue("étudier", 4, "present") == "étudions", "étudier/nous -> étudions")

# ── 3) ANCRES — 2e groupe `finir` et autres (présent en -iss-) ──
check(M.conjugue("finir", 1, "present") == "finis", "finir/je -> finis")
check(M.conjugue("finir", 3, "present") == "finit", "finir/il -> finit")
check(M.conjugue("finir", 4, "present") == "finissons", "finir/nous -> finissons")
check(M.conjugue("finir", 5, "present") == "finissez", "finir/vous -> finissez")
check(M.conjugue("finir", 6, "present") == "finissent", "finir/ils -> finissent")
check(M.conjugue("choisir", 4, "present") == "choisissons", "choisir/nous -> choisissons")
check(M.conjugue("grandir", 1, "present") == "grandis", "grandir/je -> grandis")
check(M.conjugue("réfléchir", 6, "present") == "réfléchissent", "réfléchir/ils -> réfléchissent")

# ── 4) groupe() — classification établie ──
check(M.groupe("parler") == 1, "groupe(parler)=1")
check(M.groupe("donner") == 1, "groupe(donner)=1")
check(M.groupe("manger") == 1, "groupe(manger)=1 (1er groupe, même si conjugue abstient)")
check(M.groupe("finir") == 2, "groupe(finir)=2")
check(M.groupe("choisir") == 2, "groupe(choisir)=2")
check(M.groupe("aller") == 3, "groupe(aller)=3 (seul -er irrégulier)")
check(M.groupe("être") == 3, "groupe(être)=3")
check(M.groupe("avoir") == 3, "groupe(avoir)=3")
check(M.groupe("voir") == 3, "groupe(voir)=3 (-oir)")
check(M.groupe("vendre") == 3, "groupe(vendre)=3 (-re)")
check(M.groupe("prendre") == 3, "groupe(prendre)=3")
check(M.groupe("partir") == 3, "groupe(partir)=3 (-ir 3e groupe)")
check(M.groupe("courir") == 3, "groupe(courir)=3")
check(M.groupe("PARLER") == 1, "groupe insensible à la casse")
check(M.groupe("  finir  ") == 2, "groupe insensible aux espaces")

# ── 5) terminaisons_present() — jeux réguliers ──
check(M.terminaisons_present(1) == ("e", "es", "e", "ons", "ez", "ent"), "terminaisons 1er groupe")
check(M.terminaisons_present(2) == ("is", "is", "it", "issons", "issez", "issent"), "terminaisons 2e groupe")
check(M.terminaisons_present("1er") == M.TERMINAISONS_1ER, "terminaisons accepte '1er'")
check(M.terminaisons_present("2e") == M.TERMINAISONS_2E, "terminaisons accepte '2e'")
check(M.terminaisons_present(M.groupe("finir")) == M.TERMINAISONS_2E, "compose groupe()->terminaisons_present()")

# ── 6) SOUNDNESS — irréguliers / 3e groupe : ABSTENTION ──
check(abst(M.conjugue, "être", 1, "present"), "être -> abstention (irrégulier)")
check(abst(M.conjugue, "avoir", 3, "present"), "avoir -> abstention (irrégulier)")
check(abst(M.conjugue, "aller", 1, "present"), "aller -> abstention (-er irrégulier)")
check(abst(M.conjugue, "faire", 4, "present"), "faire -> abstention (3e groupe)")
check(abst(M.conjugue, "prendre", 1, "present"), "prendre -> abstention (3e groupe)")
check(abst(M.conjugue, "partir", 1, "present"), "partir -> abstention (-ir 3e groupe)")
check(abst(M.conjugue, "venir", 4, "present"), "venir -> abstention (-ir 3e groupe)")
check(abst(M.conjugue, "vendre", 1, "present"), "vendre -> abstention (-re 3e groupe)")

# ── 7) SOUNDNESS — -ir hors catalogue (groupe incertain) : ABSTENTION ──
check(abst(M.groupe, "moisir"), "moisir -> abstention (-ir hors catalogue, incertain)")
check(abst(M.conjugue, "moisir", 1, "present"), "conjugue(moisir) -> abstention (groupe incertain)")
check(abst(M.groupe, "haïr"), "haïr -> abstention (tréma, hors catalogue)")

# ── 8) SOUNDNESS — 1er groupe à particularité orthographique : ABSTENTION (pas de forme à risque) ──
check(abst(M.conjugue, "manger", 4, "present"), "manger -> abstention (-ger)")
check(abst(M.conjugue, "commencer", 4, "present"), "commencer -> abstention (-cer)")
check(abst(M.conjugue, "nettoyer", 1, "present"), "nettoyer -> abstention (-yer)")
check(abst(M.conjugue, "appeler", 1, "present"), "appeler -> abstention (-eler)")
check(abst(M.conjugue, "acheter", 1, "present"), "acheter -> abstention (-eter)")
check(abst(M.conjugue, "jeter", 6, "present"), "jeter -> abstention (-eter)")
check(abst(M.conjugue, "lever", 1, "present"), "lever -> abstention (e+consonne)")
check(abst(M.conjugue, "céder", 1, "present"), "céder -> abstention (é+consonne)")
check(abst(M.conjugue, "préférer", 4, "present"), "préférer -> abstention (é+consonne)")
check(abst(M.conjugue, "semer", 1, "present"), "semer -> abstention (e+consonne)")

# ── 9) SOUNDNESS — personne hors 1..6, types invalides ──
check(abst(M.conjugue, "parler", 0, "present"), "personne 0 -> abstention")
check(abst(M.conjugue, "parler", 7, "present"), "personne 7 -> abstention")
check(abst(M.conjugue, "parler", -1, "present"), "personne -1 -> abstention")
check(abst(M.conjugue, "parler", True, "present"), "personne booléenne -> abstention")
check(abst(M.conjugue, "parler", 1.0, "present"), "personne float -> abstention")
check(abst(M.conjugue, "parler", "1", "present"), "personne str -> abstention")
check(abst(M.conjugue, 123, 1, "present"), "infinitif non-str -> abstention")
check(abst(M.conjugue, "", 1, "present"), "infinitif vide -> abstention")
check(abst(M.groupe, None), "groupe(None) -> abstention")
check(abst(M.groupe, "xyz"), "groupe(non-verbe) -> abstention")

# ── 10) SOUNDNESS — temps non géré (présent seulement) ──
check(abst(M.conjugue, "parler", 1, "futur"), "temps futur -> abstention")
check(abst(M.conjugue, "parler", 4, "imparfait"), "temps imparfait -> abstention")
check(abst(M.conjugue, "finir", 1, "passe-simple"), "temps passé simple -> abstention")
check(abst(M.terminaisons_present, 3), "terminaisons_present(3) -> abstention (pas de jeu régulier)")
check(abst(M.terminaisons_present, 9), "terminaisons_present(9) -> abstention")
check(abst(M.terminaisons_present, "3e"), "terminaisons_present('3e') -> abstention")

# ── 11) DÉTERMINISME — appels répétés identiques ──
check(all(M.conjugue("parler", p, "present") == M.conjugue("parler", p, "present") for p in range(1, 7)),
      "conjugue déterministe")
check(M.groupe("finir") == M.groupe("finir") == 2, "groupe déterministe")
check(M.terminaisons_present(1) == M.terminaisons_present(1), "terminaisons déterministes")

# ── 12) ACCEPTE 'présent' accentué (équivalent au présent) ──
check(M.conjugue("parler", 1, "présent") == "parle", "temps 'présent' accentué accepté")

print(f"\n=== valide_conjugaison : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
