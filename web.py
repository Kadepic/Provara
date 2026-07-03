"""WEB (HTML/CSS/standards) — vérifications STRUCTURELLES exactes, FAUX=0 (mission formule/concept 2026-06-29).

Bon parenthésage des balises HTML (imbrication correcte, en tenant compte des éléments auto-fermants void), calcul
de la SPÉCIFICITÉ CSS d'un sélecteur (triplet id, classe, élément — règle de la cascade) et comparaison de deux
sélecteurs. Mécanisme EXACT et déterministe. Abstention STRUCTURELLE : entrée non textuelle -> ValueError.

Couvre le sujet borné « Web (HTML/CSS/standards) ».
Vérifié en adverse par `valide_web.py` (imbrication correcte/incorrecte, spécificité connue).
"""
from __future__ import annotations

import re

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_BALISE = re.compile(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)[^>]*?(/?)\s*>")


def balises_equilibrees(html: str) -> bool:
    """True ssi les balises HTML sont correctement imbriquées (pile LIFO). Les éléments void (<br>, <img>…) et les
    balises auto-fermantes (<x/>) ne nécessitent pas de fermeture. Insensible à la casse des noms de balises."""
    if not isinstance(html, str):
        raise ValueError("HTML (chaîne) attendu")
    pile = []
    for m in _BALISE.finditer(html):
        fermante, nom, autoferme = m.group(1), m.group(2).lower(), m.group(3)
        if fermante:
            if not pile or pile.pop() != nom:
                return False
        elif autoferme or nom in _VOID:
            continue                          # pas d'empilement
        else:
            pile.append(nom)
    return not pile


def specificite(selecteur: str) -> tuple[int, int, int]:
    """Spécificité CSS d'un sélecteur simple = (nb #id, nb .classe|[attr]|:pseudo-classe, nb éléments|::pseudo-élément).
    Ex. '#nav .item a' -> (1, 1, 1). Les '*' et combinateurs ne comptent pas."""
    if not isinstance(selecteur, str) or not selecteur.strip():
        raise ValueError("sélecteur (chaîne non vide) attendu")
    s = selecteur
    ids = len(re.findall(r"#[\w-]+", s))
    classes = len(re.findall(r"\.[\w-]+", s)) + len(re.findall(r"\[[^\]]+\]", s)) + len(re.findall(r"(?<!:):[\w-]+", s))
    # éléments : mots nus (pas précédés de # . : et pas un '*')
    sans = re.sub(r"[#.][\w-]+|\[[^\]]+\]|::?[\w-]+", " ", s)
    elements = len(re.findall(r"\b[a-zA-Z][\w-]*\b", sans))
    return (ids, classes, elements)


def compare_specificite(sel1: str, sel2: str) -> int:
    """Compare deux sélecteurs : +1 si sel1 l'emporte (plus spécifique), −1 si sel2, 0 si égalité (cascade : le
    dernier déclaré gagnerait — non décidé ici)."""
    a, b = specificite(sel1), specificite(sel2)
    return (a > b) - (a < b)


if __name__ == "__main__":
    print("équilibré <div><p>x</p></div> :", balises_equilibrees("<div><p>x</p></div>"))
    print("mal imbriqué <div><p></div></p> :", balises_equilibrees("<div><p></div></p>"))
    print("void <div><br><img></div> :", balises_equilibrees("<div><br><img></div>"))
    print("non fermé <div><p></div> :", balises_equilibrees("<div><p></div>"))
    print("spécificité '#nav .item a' :", specificite("#nav .item a"))
    print("spécificité 'ul li.active' :", specificite("ul li.active"))
    print("compare '#x' vs '.a.b.c' :", compare_specificite("#x", ".a.b.c"))
