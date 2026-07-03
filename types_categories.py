"""FONDATIONS ALTERNATIVES (théorie des catégories, types) — deux mécanismes EXACTS, déterministes, FAUX=0
(formule/concept 2026-06-29).

(1) TYPAGE du LAMBDA-CALCUL SIMPLEMENT TYPÉ (à la Church, abstractions annotées).
    type_de(terme, contexte) -> chaîne de type canonique, ou ValueError si le terme est mal typé / mal formé.
    Règles de dérivation EXACTES :
      - variable :   Γ(x) = T              => x : T            (sinon ValueError : variable libre)
      - application : f : A->B   et  x : A  => (f x) : B        (sinon ValueError : non-fonction / argument incompatible)
      - abstraction : Γ,x:A ⊢ corps : B     => (λx:A. corps) : A->B
    Les types sont écrits avec « -> » associatif À DROITE : « A->B->C » = « A->(B->C) ».

(2) LOIS DE CATÉGORIE sur les morphismes d'une catégorie LIBRE (morphisme = chemin de flèches).
    compose(g, f) défini ssi dom(g) = cod(f) ; la composition est la concaténation des chemins (g après f).
    identite(X) = morphisme neutre (chemin vide) sur l'objet X.
    verifie_identite(f)            : id(cod f) ∘ f = f  ET  f ∘ id(dom f) = f          (THÉORÈME, toujours vrai)
    verifie_associativite(h,g,f)   : (h ∘ g) ∘ f = h ∘ (g ∘ f)                          (THÉORÈME, toujours vrai)
    Abstention STRUCTURELLE : composition incompatible / morphisme mal formé -> ValueError.

Couvre le sujet borné « Fondations alternatives (théorie des catégories, types) ».
Vérifié en adverse par `valide_types_categories.py`.
"""
from __future__ import annotations

from collections import namedtuple


# ─────────────────────────────────────────────────────────────────────────────
#  (1)  TYPES & LAMBDA-CALCUL SIMPLEMENT TYPÉ
# ─────────────────────────────────────────────────────────────────────────────
#  Type interne :  atomique = str  |  fonction = ('->', gauche, droite)
#  Terme interne :  ('var', nom)  |  ('app', f, x)  |  ('lam', nom, type_str, corps)

def _tokenize_type(s):
    if not isinstance(s, str):
        raise ValueError("type : chaîne attendue")
    toks = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            toks.append(c)
            i += 1
            continue
        if c == "-":
            if i + 1 < n and s[i + 1] == ">":
                toks.append("->")
                i += 2
                continue
            raise ValueError("type : '-' isolé")
        if c.isalpha():
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            toks.append(s[i:j])
            i = j
            continue
        raise ValueError(f"type : caractère invalide {c!r}")
    return toks


def _p_atom(toks, pos):
    if pos[0] >= len(toks):
        raise ValueError("type : atome attendu")
    tok = toks[pos[0]]
    if tok == "(":
        pos[0] += 1
        inner = _p_arrow(toks, pos)
        if pos[0] >= len(toks) or toks[pos[0]] != ")":
            raise ValueError("type : parenthèse non fermée")
        pos[0] += 1
        return inner
    if tok in (")", "->"):
        raise ValueError("type : jeton inattendu")
    if not tok[0].isalpha():
        raise ValueError("type : identifiant invalide")
    pos[0] += 1
    return tok


def _p_arrow(toks, pos):
    left = _p_atom(toks, pos)
    if pos[0] < len(toks) and toks[pos[0]] == "->":
        pos[0] += 1
        right = _p_arrow(toks, pos)          # associatif à droite
        return ("->", left, right)
    return left


def _parse_type(s):
    """Chaîne -> type interne (str atomique ou ('->', g, d)). ValueError si mal formé."""
    toks = _tokenize_type(s)
    if not toks:
        raise ValueError("type vide")
    pos = [0]
    res = _p_arrow(toks, pos)
    if pos[0] != len(toks):
        raise ValueError("type : jetons résiduels")
    return res


def _to_str(t):
    """Type interne -> chaîne canonique (parenthésage minimal, '->' associatif à droite)."""
    if isinstance(t, str):
        return t
    g, d = t[1], t[2]
    gs = _to_str(g)
    if isinstance(g, tuple):          # une flèche à gauche d'une flèche : parenthèses obligatoires
        gs = "(" + gs + ")"
    return gs + "->" + _to_str(d)


def parse_type(s):
    """Normalise une chaîne de type en sa forme canonique. ValueError si mal formé."""
    return _to_str(_parse_type(s))


# --- constructeurs de termes (lisibilité) ---
def var(nom):
    return ("var", nom)


def app(f, x):
    return ("app", f, x)


def lam(nom, type_str, corps):
    return ("lam", nom, type_str, corps)


def _infer(t, ctx):
    """Infère le type interne du terme t dans le contexte ctx {nom: type_interne}. ValueError si mal typé."""
    if not (isinstance(t, tuple) and len(t) >= 1 and isinstance(t[0], str)):
        raise ValueError("terme mal formé")
    tag = t[0]

    if tag == "var":
        if len(t) != 2 or not isinstance(t[1], str):
            raise ValueError("var mal formée")
        nom = t[1]
        if nom not in ctx:
            raise ValueError(f"variable libre : {nom}")
        return ctx[nom]

    if tag == "app":
        if len(t) != 3:
            raise ValueError("application mal formée")
        tf = _infer(t[1], ctx)
        tx = _infer(t[2], ctx)
        if not (isinstance(tf, tuple) and tf[0] == "->"):
            raise ValueError("application : la tête n'est pas une fonction")
        if tf[1] != tx:
            raise ValueError("application : type d'argument incompatible")
        return tf[2]

    if tag == "lam":
        if len(t) != 4 or not isinstance(t[1], str):
            raise ValueError("abstraction mal formée")
        a = _parse_type(t[2])
        ctx2 = dict(ctx)
        ctx2[t[1]] = a
        b = _infer(t[3], ctx2)
        return ("->", a, b)

    raise ValueError(f"constructeur de terme inconnu : {tag}")


def type_de(terme, contexte=None):
    """Type (chaîne canonique) du terme dans le contexte donné ; ValueError si mal typé ou mal formé."""
    if contexte is None:
        contexte = {}
    if not isinstance(contexte, dict):
        raise ValueError("contexte : dict attendu")
    ctx = {}
    for k, v in contexte.items():
        if not isinstance(k, str):
            raise ValueError("contexte : clés str attendues")
        ctx[k] = _parse_type(v)
    return _to_str(_infer(terme, ctx))


def bien_type(terme, contexte=None):
    """True ssi le terme est typable (jamais de ValueError propagée)."""
    try:
        type_de(terme, contexte)
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  (2)  CATÉGORIE LIBRE : MORPHISMES & LOIS
# ─────────────────────────────────────────────────────────────────────────────
#  Un morphisme = (dom, cod, fleches) où fleches est le chemin de générateurs
#  dans l'ORDRE d'application (du domaine vers le codomaine). Chemin vide = identité.

Morphisme = namedtuple("Morphisme", ["dom", "cod", "fleches"])


def _obj_valide(o):
    return isinstance(o, str) and o != ""


def morphisme(nom, dom, cod):
    """Morphisme générateur nom : dom -> cod."""
    if not (isinstance(nom, str) and nom != ""):
        raise ValueError("morphisme : nom non vide attendu")
    if not (_obj_valide(dom) and _obj_valide(cod)):
        raise ValueError("morphisme : objets (dom, cod) non vides attendus")
    return Morphisme(dom, cod, (nom,))


def identite(objet):
    """Morphisme identité id(objet) : objet -> objet (chemin vide)."""
    if not _obj_valide(objet):
        raise ValueError("identite : objet non vide attendu")
    return Morphisme(objet, objet, ())


def _est_morphisme(m):
    return isinstance(m, Morphisme) and _obj_valide(m.dom) and _obj_valide(m.cod) and isinstance(m.fleches, tuple)


def compose(g, f):
    """g ∘ f : composition (g APRÈS f). Définie ssi dom(g) = cod(f). ValueError sinon."""
    if not (_est_morphisme(g) and _est_morphisme(f)):
        raise ValueError("compose : deux morphismes attendus")
    if g.dom != f.cod:
        raise ValueError(f"compose : domaines incompatibles (dom g={g.dom} ≠ cod f={f.cod})")
    return Morphisme(f.dom, g.cod, f.fleches + g.fleches)


def verifie_identite(f):
    """Vérifie la loi d'identité : id(cod f) ∘ f = f  ET  f ∘ id(dom f) = f. ValueError si f mal formé."""
    if not _est_morphisme(f):
        raise ValueError("verifie_identite : morphisme attendu")
    gauche = compose(identite(f.cod), f)
    droite = compose(f, identite(f.dom))
    return gauche == f and droite == f


def verifie_associativite(h, g, f):
    """Vérifie l'associativité : (h ∘ g) ∘ f = h ∘ (g ∘ f). ValueError si non composables / mal formés."""
    if not (_est_morphisme(h) and _est_morphisme(g) and _est_morphisme(f)):
        raise ValueError("verifie_associativite : trois morphismes attendus")
    if g.dom != f.cod or h.dom != g.cod:
        raise ValueError("verifie_associativite : morphismes non composables")
    gauche = compose(compose(h, g), f)
    droite = compose(h, compose(g, f))
    return gauche == droite
