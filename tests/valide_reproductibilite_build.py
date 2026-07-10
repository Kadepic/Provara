"""
VALIDE reproductibilite_build.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par le code testé) :
  • SHA-256 de la chaîne VIDE (constante universelle, FIPS 180-4, vérifiable partout) :
        e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  • SHA-256 de 'abc' (vecteur de test officiel NIST) :
        ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
    Ces deux constantes sont écrites EN DUR ci-dessous : elles jugent `empreinte` de l'extérieur.
  • INDÉPENDANCE À L'ORDRE (ancre forte) : le même arbre créé en insérant les fichiers dans DEUX ordres
    différents doit donner la MÊME empreinte_arbre (c'est la définition du déterminisme visé).
  • SOURCE_DATE_EPOCH est LE remède standardisé de l'horodatage embarqué (reproducible-builds.org) :
    on exige sa mention littérale dans remede('horodatage').
  • Un octet changé -> empreinte différente ; arbres identiques -> même empreinte.

SOUNDNESS : chemin inexistant, dossier vide, fichier vs dossier croisés, bool/int/float/None/bytes/'',
cause inconnue -> ValueError. DÉTERMINISME : chaque fonction appelée deux fois -> égalité.
LIENS SYMBOLIQUES (contre-exemples de l'audit adverse) : arbre {a:'X', b:'X'} vs {b:'X', a=lien->b}
N'EST PAS identique bit-à-bit (types d'inode différents) -> le module doit S'ABSTENIR (ValueError),
jamais rendre reproductible=True ; lien ABSOLU vers un fichier HORS de l'arbre -> ValueError (sinon
l'empreinte dépendrait d'octets étrangers à l'arbre) ; lien cassé, lien de dossier, FIFO, argument
lui-même symlink -> ValueError.
La gate n'écrit RIEN hors de son répertoire temporaire (tempfile).
"""
import os
import shutil
import tempfile

import reproductibilite_build as B

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


# Constantes universelles, écrites EN DUR (NIST/FIPS 180-4) — indépendantes du code testé.
SHA256_VIDE = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SHA256_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

racine = tempfile.mkdtemp(prefix="valide_repro_")


def ecrit(dossier, rel, contenu: bytes):
    chemin = os.path.join(dossier, *rel.split("/"))
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(contenu)
    return chemin


try:
    # ── 1) ANCRE EXTERNE : SHA-256 de fichiers au contenu connu ──
    f_vide = ecrit(racine, "vide.txt", b"")
    f_abc = ecrit(racine, "abc.txt", b"abc")
    check(B.empreinte(f_vide) == SHA256_VIDE, "empreinte(fichier vide) = constante NIST chaîne vide")
    check(B.empreinte(f_abc) == SHA256_ABC, "empreinte(fichier 'abc') = constante NIST 'abc'")
    check(len(B.empreinte(f_abc)) == 64, "empreinte = 64 hexadécimaux")

    # ── 2) ARBRES IDENTIQUES -> MÊME empreinte ; un octet changé -> DIFFÉRENTE ──
    arbre1 = os.path.join(racine, "arbre1")
    arbre2 = os.path.join(racine, "arbre2")
    for arbre in (arbre1, arbre2):
        ecrit(arbre, "lib/module.py", b"print('ok')\n")
        ecrit(arbre, "app.bin", b"\x00\x01\x02")
        ecrit(arbre, "README", b"doc")
    e1 = B.empreinte_arbre(arbre1)
    e2 = B.empreinte_arbre(arbre2)
    check(e1 == e2, "arbres identiques -> même empreinte")
    check(len(e1) == 64, "empreinte_arbre = 64 hexadécimaux")
    # un SEUL octet changé
    ecrit(arbre2, "app.bin", b"\x00\x01\x03")
    check(B.empreinte_arbre(arbre2) != e1, "un octet changé -> empreinte différente")
    # un fichier AJOUTÉ change aussi l'empreinte
    arbre3 = os.path.join(racine, "arbre3")
    ecrit(arbre3, "lib/module.py", b"print('ok')\n")
    ecrit(arbre3, "app.bin", b"\x00\x01\x02")
    ecrit(arbre3, "README", b"doc")
    ecrit(arbre3, "extra.txt", b"x")
    check(B.empreinte_arbre(arbre3) != e1, "fichier ajouté -> empreinte différente")
    # même CONTENU sous un AUTRE chemin -> différente (le chemin fait partie du build)
    arbre4 = os.path.join(racine, "arbre4")
    ecrit(arbre4, "lib/renomme.py", b"print('ok')\n")
    ecrit(arbre4, "app.bin", b"\x00\x01\x02")
    ecrit(arbre4, "README", b"doc")
    check(B.empreinte_arbre(arbre4) != e1, "fichier renommé -> empreinte différente")

    # ── 3) ANCRE FORTE : INDÉPENDANCE À L'ORDRE D'INSERTION ──
    ordre_a = os.path.join(racine, "ordre_a")
    ordre_b = os.path.join(racine, "ordre_b")
    ecrit(ordre_a, "zeta.txt", b"Z")          # a : zeta d'abord, alpha ensuite
    ecrit(ordre_a, "sub/alpha.txt", b"A")
    ecrit(ordre_a, "milieu.txt", b"M")
    ecrit(ordre_b, "milieu.txt", b"M")        # b : ordre d'insertion inversé/permuté
    ecrit(ordre_b, "sub/alpha.txt", b"A")
    ecrit(ordre_b, "zeta.txt", b"Z")
    check(B.empreinte_arbre(ordre_a) == B.empreinte_arbre(ordre_b),
          "ordre d'insertion différent -> MÊME empreinte (indépendance à l'ordre du FS)")

    # ── 4) identiques ──
    check(B.identiques(f_abc, ecrit(racine, "abc2.txt", b"abc")) is True, "fichiers même contenu -> True")
    check(B.identiques(f_abc, f_vide) is False, "fichiers contenus distincts -> False")
    check(B.identiques(arbre1, arbre1) is True, "dossier vs lui-même -> True")
    check(B.identiques(ordre_a, ordre_b) is True, "arbres égaux (ordres d'insertion ≠) -> True")
    check(B.identiques(arbre1, arbre2) is False, "arbres différents -> False")

    # ── 5) diff_arbres ──
    da = os.path.join(racine, "diff_a")
    db = os.path.join(racine, "diff_b")
    ecrit(da, "commun.txt", b"pareil")
    ecrit(da, "change.txt", b"v1")
    ecrit(da, "seul_a.txt", b"a")
    ecrit(db, "commun.txt", b"pareil")
    ecrit(db, "change.txt", b"v2")
    ecrit(db, "seul_b.txt", b"b")
    seulement_a, seulement_b, differents = B.diff_arbres(da, db)
    check(seulement_a == ["seul_a.txt"], "diff: seulement_a exact")
    check(seulement_b == ["seul_b.txt"], "diff: seulement_b exact")
    check(differents == ["change.txt"], "diff: differents exact")
    s0, s1, d0 = B.diff_arbres(arbre1, arbre1)
    check(s0 == [] and s1 == [] and d0 == [], "diff arbre vs lui-même : trois listes vides")

    # ── 6) CATALOGUE des causes (faits documentés) ──
    causes = B.causes_connues()
    check(isinstance(causes, tuple) and len(causes) == 8, "catalogue : tuple de 8 causes")
    check(causes == tuple(sorted(causes)), "catalogue trié (sortie stable)")
    for c in ("horodatage", "chemin_de_build_absolu", "ordre_parcours_fs", "graine_aleatoire",
              "parallelisme_non_ordonne", "variables_environnement", "numero_de_build",
              "adresses_memoire_aslr"):
        check(c in causes, f"cause au catalogue : {c}")
    # ANCRE : SOURCE_DATE_EPOCH = remède standardisé de l'horodatage (reproducible-builds.org)
    check("SOURCE_DATE_EPOCH" in B.remede("horodatage"), "remede(horodatage) mentionne SOURCE_DATE_EPOCH")
    check("tri" in B.remede("ordre_parcours_fs"), "remede(ordre_parcours_fs) : trier explicitement")
    for c in causes:
        check(isinstance(B.remede(c), str) and len(B.remede(c)) > 0, f"remede({c}) non vide")

    # ── 7) verifie_reproductible ──
    v_ok = B.verifie_reproductible(ordre_a, ordre_b)
    check(v_ok["reproductible"] is True, "builds identiques -> reproductible True")
    check(v_ok["fichiers_differents"] == [], "builds identiques -> aucun fichier différent")
    check(v_ok["causes_suspectes"] == [], "builds identiques -> aucune cause suspecte")
    # builds différents : un .pyc qui diffère + un fichier d'un seul côté
    b1 = os.path.join(racine, "build1")
    b2 = os.path.join(racine, "build2")
    ecrit(b1, "pkg/mod.pyc", b"\x01")
    ecrit(b1, "commun.txt", b"x")
    ecrit(b2, "pkg/mod.pyc", b"\x02")
    ecrit(b2, "commun.txt", b"x")
    ecrit(b2, "build.log", b"run 42")
    v_ko = B.verifie_reproductible(b1, b2)
    check(v_ko["reproductible"] is False, "builds différents -> reproductible False")
    check("pkg/mod.pyc" in v_ko["fichiers_differents"], "le .pyc différent est listé")
    check("seulement_build2:build.log" in v_ko["fichiers_differents"],
          "fichier d'un seul côté listé (marqué seulement_build2:)")
    check(any("horodatage" in h for h in v_ko["causes_suspectes"]),
          "hypothèse horodatage inférée (.pyc/log)")
    check(all(h.startswith("hypothese:") for h in v_ko["causes_suspectes"]),
          "TOUTE cause suspecte est marquée 'hypothese:' (jamais un fait)")
    # verdict FAIT vs HYPOTHÈSE : la clause reproductible/differents ne dépend pas des heuristiques
    check(set(v_ko.keys()) == {"reproductible", "fichiers_differents", "causes_suspectes"},
          "structure exacte du verdict")

    # ── 8) SOUNDNESS — chemins inexistants / dossier vide ──
    fantome = os.path.join(racine, "n_existe_pas")
    check(leve(B.empreinte, fantome), "empreinte(chemin inexistant) -> ValueError")
    check(leve(B.empreinte_arbre, fantome), "empreinte_arbre(chemin inexistant) -> ValueError")
    check(leve(B.identiques, f_abc, fantome), "identiques(_, inexistant) -> ValueError")
    check(leve(B.diff_arbres, fantome, arbre1), "diff_arbres(inexistant, _) -> ValueError")
    check(leve(B.verifie_reproductible, fantome, arbre1), "verifie(inexistant, _) -> ValueError")
    vide = os.path.join(racine, "dossier_vide")
    os.makedirs(vide, exist_ok=True)
    check(leve(B.empreinte_arbre, vide), "empreinte_arbre(dossier vide) -> ValueError")
    check(leve(B.verifie_reproductible, vide, arbre1), "verifie(dossier vide, _) -> ValueError")
    check(leve(B.verifie_reproductible, arbre1, vide), "verifie(_, dossier vide) -> ValueError")

    # ── 9) SOUNDNESS — fichier vs dossier croisés ──
    check(leve(B.empreinte, arbre1), "empreinte(dossier) -> ValueError")
    check(leve(B.empreinte_arbre, f_abc), "empreinte_arbre(fichier) -> ValueError")
    check(leve(B.identiques, f_abc, arbre1), "identiques(fichier, dossier) -> ValueError")
    check(leve(B.diff_arbres, f_abc, arbre1), "diff_arbres(fichier, _) -> ValueError")
    check(leve(B.verifie_reproductible, arbre1, f_abc), "verifie(_, fichier) -> ValueError")

    # ── 10) SOUNDNESS — types invalides ──
    check(leve(B.empreinte, True), "empreinte(bool) -> ValueError")
    check(leve(B.empreinte, 3), "empreinte(int) -> ValueError")
    check(leve(B.empreinte, 3.14), "empreinte(float) -> ValueError")
    check(leve(B.empreinte, None), "empreinte(None) -> ValueError")
    check(leve(B.empreinte, b"/tmp"), "empreinte(bytes) -> ValueError")
    check(leve(B.empreinte, ""), "empreinte(chaîne vide) -> ValueError")
    check(leve(B.empreinte_arbre, False), "empreinte_arbre(bool) -> ValueError")
    check(leve(B.identiques, True, f_abc), "identiques(bool, _) -> ValueError")
    check(leve(B.remede, "cause_inventee"), "remede(cause inconnue) -> ValueError")
    check(leve(B.remede, True), "remede(bool) -> ValueError")
    check(leve(B.remede, 0), "remede(int) -> ValueError")

    # ── 11) DÉTERMINISME — deux appels, même résultat ──
    check(B.empreinte(f_abc) == B.empreinte(f_abc), "déterminisme empreinte")
    check(B.empreinte_arbre(arbre1) == B.empreinte_arbre(arbre1), "déterminisme empreinte_arbre")
    check(B.diff_arbres(da, db) == B.diff_arbres(da, db), "déterminisme diff_arbres")
    check(B.verifie_reproductible(b1, b2) == B.verifie_reproductible(b1, b2),
          "déterminisme verifie_reproductible")
    check(B.causes_connues() == B.causes_connues(), "déterminisme causes_connues")

    # ── 12) LIENS SYMBOLIQUES & INODES NON RÉGULIERS -> ABSTENTION (contre-exemples de l'audit) ──
    # Contre-exemple 1 de l'audit : s1={a:'X', b:'X'} (deux fichiers réguliers) vs s2={b:'X', a=lien->b}.
    # Les contenus LUS coïncident mais les arbres ne sont PAS identiques bit-à-bit (types d'inode
    # différents ; un tar des deux diffère). Verdict True serait un FAUX POSITIF : on exige ValueError.
    s1 = os.path.join(racine, "sym1")
    s2 = os.path.join(racine, "sym2")
    ecrit(s1, "a", b"X")
    ecrit(s1, "b", b"X")
    ecrit(s2, "b", b"X")
    os.symlink("b", os.path.join(s2, "a"))  # lien relatif interne a -> b
    check(leve(B.verifie_reproductible, s1, s2), "verifie(régulier, arbre avec symlink) -> ValueError")
    check(leve(B.verifie_reproductible, s2, s1), "verifie(arbre avec symlink, régulier) -> ValueError")
    check(leve(B.identiques, s1, s2), "identiques(régulier, arbre avec symlink) -> ValueError")
    check(leve(B.diff_arbres, s1, s2), "diff_arbres(_, arbre avec symlink) -> ValueError")
    check(leve(B.empreinte_arbre, s2), "empreinte_arbre(arbre avec symlink interne) -> ValueError")
    check(len(B.empreinte_arbre(s1)) == 64, "l'arbre 100% régulier reste hachable, lui")
    # Contre-exemple 2 de l'audit : lien ABSOLU vers un fichier HORS de l'arbre. Sans abstention,
    # modifier la cible externe changerait l'empreinte sans qu'aucun octet DE L'ARBRE n'ait changé.
    externe = ecrit(racine, "externe.txt", b"contenu externe v1")
    s3 = os.path.join(racine, "sym3")
    ecrit(s3, "reel.txt", b"r")
    os.symlink(externe, os.path.join(s3, "lien.txt"))  # lien ABSOLU, cible hors de s3
    check(leve(B.empreinte_arbre, s3), "empreinte_arbre(arbre avec lien ABSOLU externe) -> ValueError")
    check(leve(B.verifie_reproductible, s3, s1), "verifie(arbre avec lien externe, _) -> ValueError")
    check(leve(B.identiques, s3, s1), "identiques(arbre avec lien externe, _) -> ValueError")
    # lien CASSÉ (cible inexistante) : refusé aussi, pas exclu en silence
    s4 = os.path.join(racine, "sym4")
    ecrit(s4, "reel.txt", b"r")
    os.symlink(os.path.join(racine, "cible_disparue"), os.path.join(s4, "casse"))
    check(leve(B.empreinte_arbre, s4), "empreinte_arbre(arbre avec lien cassé) -> ValueError")
    # lien vers un DOSSIER dans l'arbre (os.walk le range dans dirs, non descendu) : refusé
    s5 = os.path.join(racine, "sym5")
    ecrit(s5, "sub/reel.txt", b"r")
    os.symlink(os.path.join(s5, "sub"), os.path.join(s5, "lien_dossier"))
    check(leve(B.empreinte_arbre, s5), "empreinte_arbre(arbre avec symlink de dossier) -> ValueError")
    # l'ARGUMENT lui-même est un symlink : fichier puis dossier
    lien_f = os.path.join(racine, "lien_vers_abc.txt")
    os.symlink(f_abc, lien_f)
    check(leve(B.empreinte, lien_f), "empreinte(symlink vers fichier) -> ValueError")
    check(leve(B.identiques, f_abc, lien_f), "identiques(fichier régulier, symlink) -> ValueError")
    lien_d = os.path.join(racine, "lien_vers_arbre1")
    os.symlink(arbre1, lien_d)
    check(leve(B.empreinte_arbre, lien_d), "empreinte_arbre(symlink vers dossier) -> ValueError")
    check(leve(B.diff_arbres, lien_d, arbre1), "diff_arbres(symlink vers dossier, _) -> ValueError")
    # FIFO (inode non régulier, POSIX) dans l'arbre : refusé, pas exclu en silence
    s6 = os.path.join(racine, "sym6")
    ecrit(s6, "reel.txt", b"r")
    os.mkfifo(os.path.join(s6, "tube"))
    check(leve(B.empreinte_arbre, s6), "empreinte_arbre(arbre avec FIFO) -> ValueError")
    check(leve(B.verifie_reproductible, s1, s6), "verifie(_, arbre avec FIFO) -> ValueError")
finally:
    shutil.rmtree(racine, ignore_errors=True)

print(f"\n=== valide_reproductibilite_build : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
