"""VALIDE braille.py — bijection + round-trip + FAUX=0 (domaine explicite, abstention hors table).

Oracle : la table des 26 lettres est bijective (26 combinaisons distinctes) ; le bit Unicode d'un point i est 1<<(i-1)
(re-dérivé) ; texte<->braille round-trip. Négatifs : caractère hors alphabet, combinaison inconnue -> ValueError.
"""
import braille as B

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


LETTRES = "abcdefghijklmnopqrstuvwxyz"

# ── 1) Bijection : 26 lettres -> 26 combinaisons distinctes -> 26 caractères Unicode distincts ──
points = [B.lettre_vers_points(c) for c in LETTRES]
check(len(set(points)) == 26, "26 combinaisons de points distinctes")
unis = [B.lettre_vers_unicode(c) for c in LETTRES]
check(len(set(unis)) == 26, "26 caractères Unicode distincts")

# ── 2) Ancres canoniques (valeurs connues de la convention) ──
check(B.lettre_vers_points("a") == (1,), "a = point 1")
check(B.lettre_vers_points("b") == (1, 2), "b = points 1,2")
check(B.lettre_vers_points("z") == (1, 3, 5, 6), "z = points 1,3,5,6")
check(B.lettre_vers_points("w") == (2, 4, 5, 6), "w = points 2,4,5,6 (exception historique)")
check(B.lettre_vers_unicode("a") == "⠁", "a -> U+2801 (bit du point 1)")
check(B.lettre_vers_unicode(" ") == "⠀", "espace -> cellule vide U+2800")

# ── 3) k–t = a–j + point 3 ; u–z = a–j + points 3,6 (sauf w) — structure re-dérivée ──
def sans(pts, retire):
    return tuple(p for p in pts if p not in retire)
struct_kt = all(3 in B.lettre_vers_points(kt) and sans(B.lettre_vers_points(kt), {3}) == B.lettre_vers_points(aj)
                for kt, aj in zip("klmnopqrst", "abcdefghij"))
check(struct_kt, "k–t = a–j + point 3")
struct_uz = all({3, 6} <= set(B.lettre_vers_points(uz)) and sans(B.lettre_vers_points(uz), {3, 6}) == B.lettre_vers_points(aj)
                for uz, aj in zip("uvxyz", "abcde"))   # w exclu (exception)
check(struct_uz, "u,v,x,y,z = a,b,c,d,e + points 3,6")

# ── 4) Round-trip texte ──
for txt in ("bonjour le monde", "abcdefghijklmnopqrstuvwxyz", "verax"):
    br = B.texte_vers_braille(txt)
    check(B.braille_vers_texte(br) == txt, f"round-trip texte : {txt!r}")
# inverse point->lettre et unicode->lettre cohérents
check(all(B.points_vers_lettre(B.lettre_vers_points(c)) == c for c in LETTRES), "points_vers_lettre inverse")
check(all(B.unicode_vers_lettre(B.lettre_vers_unicode(c)) == c for c in LETTRES), "unicode_vers_lettre inverse")

# ── 5) Rendu ascii ──
check(B.cellule_ascii("a").startswith("●·"), "cellule_ascii(a) : point 1 allumé")

# ── 6) FAUX=0 : hors domaine -> ValueError (jamais deviné) ──
check(leve(B.lettre_vers_points, "é"), "lettre accentuée -> ValueError")
check(leve(B.lettre_vers_points, "5"), "chiffre -> ValueError")
check(leve(B.lettre_vers_points, "!"), "ponctuation -> ValueError")
check(leve(B.lettre_vers_points, "ab"), "plusieurs caractères -> ValueError")
check(leve(B.texte_vers_braille, "coût 5€"), "texte avec caractère hors domaine -> ValueError")
check(leve(B.unicode_vers_lettre, "A"), "caractère hors bloc Braille -> ValueError")
check(leve(B.points_vers_lettre, (1, 2, 3, 4, 5, 6)), "combinaison sans lettre -> ValueError")
check(leve(B.braille_vers_texte, "⣿"), "cellule Braille sans lettre conventionnée -> ValueError")

print(f"\n=== valide_braille : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
