"""VALIDE web.py — ADVERSE, FAUX=0. Imbrication HTML (correcte/incorrecte, void, auto-fermant), spécificité CSS
connue + comparaison + SOUNDNESS (entrée non textuelle -> ValueError)."""
import web as W

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# IMBRICATION HTML
check(W.balises_equilibrees("<div><p>x</p></div>") is True, "imbrication correcte")
check(W.balises_equilibrees("<div><p></div></p>") is False, "imbrication croisée -> invalide")
check(W.balises_equilibrees("<div><p></div>") is False, "balise non fermée -> invalide")
check(W.balises_equilibrees("</p>") is False, "fermeture sans ouverture -> invalide")
check(W.balises_equilibrees("<div><br><img src=x></div>") is True, "éléments void (br/img) sans fermeture -> OK")
check(W.balises_equilibrees("<div><input/></div>") is True, "auto-fermant -> OK")
check(W.balises_equilibrees("") is True, "vide -> équilibré")
check(W.balises_equilibrees("<DIV><P></p></div>") is True, "insensible à la casse")
check(W.balises_equilibrees("<ul><li>a</li><li>b</li></ul>") is True, "liste correcte")

# SPÉCIFICITÉ CSS
check(W.specificite("#id") == (1, 0, 0), "#id -> (1,0,0)")
check(W.specificite(".classe") == (0, 1, 0), ".classe -> (0,1,0)")
check(W.specificite("div") == (0, 0, 1), "élément -> (0,0,1)")
check(W.specificite("#nav .item a") == (1, 1, 1), "#nav .item a -> (1,1,1)")
check(W.specificite("ul li.active") == (0, 1, 2), "ul li.active -> (0,1,2)")
check(W.specificite("a:hover") == (0, 1, 1), "pseudo-classe compte comme classe")
check(W.specificite("input[type=text]") == (0, 1, 1), "attribut compte comme classe")
check(W.specificite(".a.b.c") == (0, 3, 0), "3 classes")

# COMPARAISON (cascade)
check(W.compare_specificite("#x", ".a.b.c") == 1, "un id l'emporte sur 3 classes")
check(W.compare_specificite(".a", "div span") == 1, "une classe l'emporte sur 2 éléments")
check(W.compare_specificite("div", "div") == 0, "égalité")
check(W.compare_specificite("p", ".x") == -1, "élément < classe")

# SOUNDNESS
check(leve(W.balises_equilibrees, 123), "HTML non-chaîne -> ValueError")
check(leve(W.specificite, ""), "sélecteur vide -> ValueError")

# DÉTERMINISME
check(W.specificite("#nav .item a") == W.specificite("#nav .item a"), "déterminisme")

print(f"\n=== valide_web : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
