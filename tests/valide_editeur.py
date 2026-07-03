"""VALIDE editeur.py — ADVERSE, FAUX=0. Substrat de mutation de fichiers d'un dépôt.

Vérifie les 6 garanties de sûreté : confinement (évasion `..`/absolu/symlink), non-écrasement (cree/verrou optimiste),
édition exacte non ambiguë, atomicité (fichier intact après échec), aperçu sans effet, types. Utilise un dépôt
temporaire jetable + un dossier EXTÉRIEUR témoin (jamais touché)."""
import os
import shutil
import tempfile

import editeur as E

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


racine = tempfile.mkdtemp(prefix="depot_test_")
exterieur = tempfile.mkdtemp(prefix="hors_depot_")
try:
    secret = os.path.join(exterieur, "secret.txt")
    with open(secret, "w") as fh:
        fh.write("NE_PAS_TOUCHER")

    dep = E.Depot(racine)

    # ── création + round-trip ──
    dep.cree("src/a.txt", "bonjour\nmonde\n")
    contenu, emp = dep.lit("src/a.txt")
    check(contenu == "bonjour\nmonde\n", "cree->lit round-trip exact")
    check(emp == E.empreinte("bonjour\nmonde\n"), "empreinte cohérente")
    check(dep.existe("src/a.txt"), "existe() vrai après création")

    # ── NON-ÉCRASEMENT : cree sur existant refuse, contenu intact ──
    check(leve(dep.cree, "src/a.txt", "ECRASE"), "cree sur fichier existant -> ValueError")
    check(dep.lit("src/a.txt")[0] == "bonjour\nmonde\n", "contenu intact après cree refusé")

    # ── ÉDITION EXACTE ──
    dep.cree("src/b.txt", "x = 1\ny = 1\nz = 2\n")
    check(dep.edite("src/b.txt", "z = 2", "z = 3") == 1, "edite ancre unique -> 1")
    check(dep.lit("src/b.txt")[0] == "x = 1\ny = 1\nz = 3\n", "edite applique exactement")
    # ancre absente -> refus, fichier intact
    avant = dep.lit("src/b.txt")[0]
    check(leve(dep.edite, "src/b.txt", "INEXISTANT", "!"), "edite ancre absente -> ValueError")
    check(dep.lit("src/b.txt")[0] == avant, "fichier intact après ancre absente (atomicité)")
    # ancre ambiguë (2 occurrences « = 1 ») sans tous -> refus, intact
    check(leve(dep.edite, "src/b.txt", "= 1", "= 9"), "edite ancre ambiguë sans tous -> ValueError")
    check(dep.lit("src/b.txt")[0] == avant, "fichier intact après ancre ambiguë")
    # tous=True remplace toutes les occurrences
    n = dep.edite("src/b.txt", "= 1", "= 9", tous=True)
    check(n == 2 and dep.lit("src/b.txt")[0] == "x = 9\ny = 9\nz = 3\n", "edite tous=True remplace toutes")
    check(leve(dep.edite, "src/b.txt", "abc", "abc"), "edite ancien==nouveau -> ValueError")
    check(leve(dep.edite, "src/b.txt", "", "x"), "edite ancre vide -> ValueError")

    # ── VERROU OPTIMISTE (remplace/supprime) ──
    _, emp_b = dep.lit("src/b.txt")
    dep.remplace("src/b.txt", "neuf\n", empreinte_attendue=emp_b)
    check(dep.lit("src/b.txt")[0] == "neuf\n", "remplace avec bonne empreinte OK")
    # empreinte périmée -> refus, contenu intact
    check(leve(dep.remplace, "src/b.txt", "ECRASE\n", empreinte_attendue="deadbeef"), "remplace empreinte périmée -> ValueError")
    check(dep.lit("src/b.txt")[0] == "neuf\n", "contenu intact après remplace refusé")
    # empreinte_attendue=None sur fichier existant -> refus
    check(leve(dep.remplace, "src/b.txt", "X", empreinte_attendue=None), "remplace None sur existant -> ValueError")
    # empreinte_attendue=None sur absent -> crée
    dep.remplace("src/c.txt", "creee via remplace\n", empreinte_attendue=None)
    check(dep.lit("src/c.txt")[0] == "creee via remplace\n", "remplace None sur absent -> crée")
    # supprime : mauvaise empreinte refuse, bonne empreinte supprime
    _, emp_c = dep.lit("src/c.txt")
    check(leve(dep.supprime, "src/c.txt", empreinte_attendue="stale"), "supprime empreinte périmée -> ValueError")
    check(dep.existe("src/c.txt"), "fichier toujours là après suppression refusée")
    dep.supprime("src/c.txt", empreinte_attendue=emp_c)
    check(not dep.existe("src/c.txt"), "supprime avec bonne empreinte OK")

    # ── APERÇU SANS EFFET ──
    avant_a = dep.lit("src/a.txt")[0]
    diff = dep.previsualise_edition("src/a.txt", "monde", "terre")
    check("monde" in diff and "terre" in diff and diff.startswith("---"), "previsualise rend un diff unifié")
    check(dep.lit("src/a.txt")[0] == avant_a, "previsualise n'écrit RIEN (aucun effet)")

    # ── CONFINEMENT : évasion refusée, témoin extérieur intact ──
    check(leve(dep.cree, "../evasion.txt", "X"), "cree ../ hors dépôt -> ValueError")
    check(leve(dep.lit, "../../etc/passwd"), "lit remontée profonde -> ValueError")
    check(leve(dep.chemin_absolu, "/etc/passwd"), "chemin absolu -> ValueError")
    check(not os.path.exists(os.path.join(exterieur, "evasion.txt")), "aucun fichier créé hors dépôt")
    # évasion par SYMLINK : lien dans le dépôt pointant dehors
    os.symlink(exterieur, os.path.join(racine, "lien"))
    check(leve(dep.cree, "lien/piege.txt", "X"), "cree via symlink-dossier vers l'extérieur -> ValueError")
    check(not os.path.exists(os.path.join(exterieur, "piege.txt")), "symlink : rien écrit dehors")
    # symlink FICHIER vers le secret extérieur : remplace refusé, secret intact
    os.symlink(secret, os.path.join(racine, "vers_secret.txt"))
    check(leve(dep.remplace, "vers_secret.txt", "HACK", empreinte_attendue="x"), "remplace via symlink-fichier vers dehors -> ValueError")
    with open(secret) as fh:
        check(fh.read() == "NE_PAS_TOUCHER", "secret extérieur JAMAIS modifié")

    # ── TYPES / ABSTENTION ──
    check(leve(dep.cree, "t.txt", 123), "contenu non-str -> ValueError")
    check(leve(dep.cree, "", "x"), "chemin vide -> ValueError")
    check(leve(E.empreinte, 5), "empreinte(non-str) -> ValueError")
    check(leve(E.Depot, os.path.join(exterieur, "inexistant_xyz")), "Depot racine inexistante -> ValueError")

    # ── création profonde + liste ──
    dep.cree("deep/x/y/z.txt", "profond\n")
    lst = dep.liste("src")
    check(lst == ["src/a.txt", "src/b.txt"], f"liste triée d'un sous-dossier ({lst})")
    check("deep/x/y/z.txt" in dep.liste(), "création de dossiers profonds OK")

    # ── DURCISSEMENT (failles fermées par la passe adverse) ──
    # (13) ancre à AUTO-CHEVAUCHEMENT : « aa » dans « aaa » -> position ambiguë -> refus, fichier intact
    dep.cree("ov.txt", "aaa\n")
    check(leve(dep.edite, "ov.txt", "aa", "bb"), "ancre auto-chevauchante -> ValueError")
    check(dep.lit("ov.txt")[0] == "aaa\n", "fichier intact après ancre chevauchante")
    # (14/20) previsualise applique les MÊMES gardes qu'edite (ancien==nouveau, absente, ambiguë)
    check(leve(dep.previsualise_edition, "ov.txt", "x", "x"), "previsualise ancien==nouveau -> ValueError (⇔ edite)")
    check(leve(dep.previsualise_edition, "ov.txt", "ZZZ", "y"), "previsualise ancre absente -> ValueError")
    # (16/2) éditer/lire À TRAVERS un symlink interne est refusé (jamais d'action à côté du fichier)
    dep.cree("cible_reelle.txt", "REEL\n")
    os.symlink(os.path.join(racine, "cible_reelle.txt"), os.path.join(racine, "lien_interne.txt"))
    check(leve(dep.edite, "lien_interne.txt", "REEL", "PIRATE"), "edite via symlink interne -> ValueError")
    check(dep.lit("cible_reelle.txt")[0] == "REEL\n", "cible d'un symlink interne jamais modifiée")
    check(leve(dep.lit, "lien_interne.txt"), "lit via symlink -> ValueError (ne suit pas)")
    check(leve(dep.remplace, "lien_interne.txt", "X", empreinte_attendue="z"), "remplace via symlink -> ValueError")
    # (2) symlink CASSÉ vers l'extérieur (cible inexistante) : cree/lit refusent, rien dehors
    os.symlink(os.path.join(exterieur, "pas_encore.txt"), os.path.join(racine, "lien_casse.txt"))
    check(leve(dep.cree, "lien_casse.txt", "X"), "cree sur symlink cassé -> ValueError")
    check(not os.path.exists(os.path.join(exterieur, "pas_encore.txt")), "symlink cassé : rien créé dehors")
    # (7/19) PRÉSERVATION DES PERMISSIONS : un fichier exécutable le reste après edite.
    # (Sur un FS sans vrais bits Unix — drvfs/9p — le chmod ne « prend » pas : la préservation est alors sans objet.)
    dep.cree("script.sh", "echo v1\n")
    p_sh = os.path.join(racine, "script.sh")
    os.chmod(p_sh, 0o755)
    if (os.stat(p_sh).st_mode & 0o777) == 0o755:               # FS à perms Unix -> tester la préservation
        dep.edite("script.sh", "v1", "v2")
        check((os.stat(p_sh).st_mode & 0o777) == 0o755, "mode 0755 préservé après edite")
    else:                                                      # FS sans perms Unix -> vérifier au moins l'édition
        dep.edite("script.sh", "v1", "v2")
        check(dep.lit("script.sh")[0] == "echo v2\n", "edite OK (FS sans perms Unix : préservation sans objet)")
    # (15/18) fichier NON-TEXTE -> ValueError (abstention honnête, pas une autre exception)
    with open(os.path.join(racine, "bin.dat"), "wb") as fh:
        fh.write(b"\xff\xfe\x00\x01")
    check(leve(dep.lit, "bin.dat"), "lecture binaire -> ValueError")
    check(leve(dep.edite, "bin.dat", "a", "b"), "edite binaire -> ValueError")
    # (11) cree ET remplace(None) refusent TOUTE entrée existante (même non régulière)
    os.mkdir(os.path.join(racine, "un_dossier"))
    check(leve(dep.cree, "un_dossier", "X"), "cree sur dossier existant -> ValueError")
    check(leve(dep.remplace, "un_dossier", "X", empreinte_attendue=None), "remplace(None) sur dossier -> ValueError")
    # (21) liste sur non-dossier / inexistant -> ValueError, et confinement
    check(leve(dep.liste, "script.sh"), "liste sur un fichier -> ValueError")
    check(leve(dep.liste, "inexistant_dir"), "liste sur dossier inexistant -> ValueError")
    check(leve(dep.liste, "../"), "liste hors dépôt -> ValueError")

    # ── déterminisme ──
    check(E.empreinte("abc") == E.empreinte("abc"), "empreinte déterministe")

finally:
    shutil.rmtree(racine, ignore_errors=True)
    shutil.rmtree(exterieur, ignore_errors=True)

print(f"\n=== valide_editeur : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
