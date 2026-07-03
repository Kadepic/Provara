"""
CURIOSITÉ DIRIGÉE — diriger l'invention vers le trou, mesuré en appels-juge (le mur de l'EXPLORATION).

L'invention de base mute tous les atomes confirmés et SHUFFLE : l'ordre du bon atome est laissé au
hasard. Mesuré ailleurs (`mesure_vitesse`), l'association syntaxique (le « cerveau », le prédicteur)
ENTERRE le neuf. Quand le registre grandit (compounding), la bonne matière se noie -> le coût de
l'invention explose. Ici on DIRIGE : on réordonne les atomes-à-muter par la DISCORDE cerveau/cœur
(intuition de Yohan : « cerveau et cœur se contredisent et ça pousse à tenter »).

  - CERVEAU = `Predicteur.rang(source)` : syntaxique, précis sur le connu, FAIBLE sur la nouveauté.
  - CŒUR    = crédit partiel rendu par le JUGE sur les tests VISIBLES (combien d'asserts passent),
              CONSULTATIF, coûte une exécution -> seulement sur les top-N atomes du cerveau (Fork C).

La DISCORDE = un atome que le cerveau enterre mais que le cœur trouve CHAUD : on le mute EN PREMIER.

Ligne rouge (Fork A, tranchée) : le cœur lit le CRÉDIT du juge (réalité), JAMAIS le texte des asserts ;
il ne fait que RÉORDONNER (rien jeté) ; seul le HELD-OUT promeut -> au pire on perd des appels, jamais
un faux skill. La discorde dit OÙ chercher ; le juge seul dit QUOI garder.

A/B falsifiable (Fork D), sur deux domaines (chaîne + nombre) pour écarter le coup de chance :
  inverse_chaine = s[::-1]  (seul `copie` = s[:] porte un slice -> matière unique ; cœur 0.67)
  cube           = x**3     (seul `carre` = x*x est allongeable -> matière unique ; cœur 0.50)

Mesuré honnêtement : le coût du cœur est FIXE (borné top-N, Fork C), la recherche évitée CROÎT avec le
registre. Donc diriger paie quand la recherche est DURE — précisément le régime du compounding (registre
qui grandit). Sur une recherche triviale, profiler coûte plus que tenter. On le MONTRE par un balayage.

Critères de MORT :
  1. DISCORDE   : la bonne matière est CHAUDE au cœur (max strict) ALORS que le cerveau ne la met PAS
                  première -> les deux sens se contredisent vraiment (sinon : pas de signal à exploiter).
  2. RÉSOUT+GÉN : l'invention dirigée minte l'atome ET il GÉNÉRALISE (held-out) -> on ne se ment pas.
  3. ÉCRASE     : dirigé écrase le coût de RECHERCHE-candidats (brut, hors cœur) — le mécanisme marche.
  4. SCALING    : le cœur étant BORNÉ (top-N), le coût dirigé reste ~PLAT quand le registre grandit, là où
                  le non-dirigé CROÎT -> un CROISEMENT existe et, au registre réaliste (grand), dirigé gagne
                  en NET (cœur inclus). Si pas de croisement / pas de plateau, la brique MEURT.
"""

from __future__ import annotations

import ast
import statistics
import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import (TYPES_RICHES, GenerateurInvention, GenerateurInventionDirige)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# Compteur d'appels au juge : c'est LA métrique de l'A/B (le coût de la recherche).
_compte = {"n": 0}


def jc(code: str, tests: str):
    _compte["n"] += 1
    return juge(code, tests, LIM)


# --- Le cœur : crédit partiel via le juge (repris de mesure_sens, branché sur le compteur) -------
def _asserts_individuels(tests_src: str, entree: str) -> list[str]:
    tree = ast.parse(tests_src)
    check = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check"), None)
    if check is None:
        return []
    return [f"def check(c):\n    {ast.unparse(a)}\ncheck({entree})\n"
            for a in check.body if isinstance(a, ast.Assert)]


def _renomme(src: str, nom: str) -> str:
    """Renomme la fonction d'un atome vers le point d'entrée de T (pour la juger comme candidate)."""
    import re
    return re.sub(r"def\s+\w+\s*\(", f"def {nom}(", src, count=1)


def _coeur_de(tache: Tache):
    """Renvoie un callable src -> crédit partiel (asserts visibles passés / total) ; ce QU'ON injecte."""
    micro = _asserts_individuels(tache.tests, tache.point_entree)

    def coeur(src: str) -> float:
        if not micro:
            return 0.0
        cand = _renomme(src, tache.point_entree)
        return sum(1 for m in micro if jc(cand, m).passe) / len(micro)

    return coeur


def _t(fn, arg, tests, held):
    return Tache(id=f"cur/{fn}", point_entree=fn, prompt=f'def {fn}({arg}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# --- Substrat : un registre de plusieurs atomes confirmés ; UN SEUL est la bonne matière ---------
def _atome(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


# Pour inverse_chaine : seul `copie` (s[:]) a un SLICE -> seul lui peut donner s[::-1].
REG_CHAINE = [
    _atome("copie", "args[0][:]"),          # <- matière unique (slice) ; cœur chaud (identité : 2/3)
    _atome("carre", "args[0] * args[0]"),
    _atome("mul", "args[0] * args[1]"),
    _atome("incremente", "args[0] + 1"),
    _atome("trie", "sorted(args[0])"),
    _atome("premier", "args[0][0]"),        # décoy tiède (passe 'x') mais SANS slice -> mauvaise matière
    _atome("dernier", "args[0][-1]"),       # décoy tiède aussi
    _atome("double", "args[0] + args[0]"),
]
T_CHAINE = _t("inverse_chaine", "s",
              "def check(c):\n    assert c('abc') == 'cba'\n    assert c('') == ''\n    assert c('x') == 'x'\ncheck(inverse_chaine)",
              "def check(c):\n    assert c('hello') == 'olleh'\n    assert c('ab') == 'ba'\n    assert c('abcd') == 'dcba'\ncheck(inverse_chaine)")

# Pour cube : seul `carre` (x*x) est une chaîne de produits allongeable -> seul lui peut donner x**3.
REG_NOMBRE = [
    _atome("carre", "args[0] * args[0]"),   # <- matière unique ; cœur chaud (0² , 1² collent : 2/4)
    _atome("mul", "args[0] * args[1]"),
    _atome("incremente", "args[0] + 1"),
    _atome("add", "args[0] + args[1]"),
    _atome("double", "args[0] + args[0]"),
    _atome("max2", "args[0] if args[0] > args[1] else args[1]"),
    _atome("min2", "args[0] if args[0] < args[1] else args[1]"),
    _atome("trie", "sorted(args[0])"),
]
T_NOMBRE = _t("cube", "x",
              "def check(c):\n    assert c(2) == 8\n    assert c(3) == 27\n    assert c(0) == 0\n    assert c(1) == 1\ncheck(cube)",
              "def check(c):\n    assert c(4) == 64\n    assert c(5) == 125\n    assert c(-2) == -8\ncheck(cube)")

# Le cerveau apprend sur des succès NUMÉRIQUES (registre réaliste) -> il « connaît » le numérique
# et ENTERRE le slicing : c'est ce qui crée la discorde sur `copie`.
STORE_SEEDS = {
    "somme_carres": "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n",
    "compte_positifs": "def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n",
    "incremente_s": "def incremente_s(*args, **kwargs):\n    return args[0] + 1\n",
}
SEED_TESTS = {
    "somme_carres": "def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)",
    "compte_positifs": "def check(c):\n    assert c([1,-2,3]) == 2\ncheck(compte_positifs)",
    "incremente_s": "def check(c):\n    assert c(4) == 5\ncheck(incremente_s)",
}


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _mesure(gen, tache, n=400):
    """Renvoie (net, brut, sol). Pour le dirigé, propose() consomme le cœur AVANT la boucle :
    `brut` = recherche-candidats seule (le mécanisme), `net` = cœur INCLUS (honnête)."""
    _compte["n"] = 0
    cands = gen.propose(tache.prompt, n)
    overhead = _compte["n"]                               # cœur (0 pour le non-dirigé)
    sol = next((c for c in cands if jc(c, tache.tests).passe), None)
    net = _compte["n"]
    return net, net - overhead, sol


def _table_discorde(atomes, predicteur, coeur, source_attendue):
    """Affiche (cerveau, cœur) par atome et renvoie (discorde_ok, nom_le_plus_chaud)."""
    print(f"    {'atome':<12}{'cerveau(rang)':<16}{'cœur(crédit)'}")
    print("    " + "-" * 40)
    lignes = []
    for nom, src in atomes:
        r = predicteur.rang(src)
        c = coeur(src)
        lignes.append((nom, r, c))
        print(f"    {nom:<12}{r:<16}{c:.2f}")
    plus_chaud = max(lignes, key=lambda l: l[2])
    rang_min = min(l[1] for l in lignes)
    # DISCORDE : la bonne matière est la plus CHAUDE (strict) ET le cerveau ne la met PAS première.
    bonne = next(l for l in lignes if l[0] == source_attendue)
    chaud_unique = bonne[2] > max((l[2] for l in lignes if l[0] != source_attendue), default=-1)
    enterree = bonne[1] > rang_min
    return chaud_unique and enterree, plus_chaud[0]


def _pred_coeur(store_dir, nom_dom, tache):
    """Construit le cerveau (sur succès numériques) et le cœur (crédit partiel du juge sur T)."""
    store = Store(Path(store_dir) / f"{nom_dom}.jsonl")
    for fn, src in STORE_SEEDS.items():
        v = juge(src, SEED_TESTS[fn], LIM)
        assert v.passe, f"seed {fn}"
        store.ajoute(Tache(id=f"seed/{fn}", point_entree=fn, prompt="", tests=SEED_TESTS[fn]), src, v)
    return Predicteur(store, types=TYPES_RICHES), _coeur_de(tache)


def _domaine(nom_dom, atomes, tache, source_attendue, store_dir):
    print(f"\n=== {nom_dom} : T = {tache.point_entree} (matière attendue : {source_attendue}) ===")
    pred, coeur = _pred_coeur(store_dir, nom_dom, tache)

    discorde_ok, plus_chaud = _table_discorde(atomes, pred, coeur, source_attendue)
    _compte["n"] = 0   # la table a consommé des appels (cœur) : on repart à zéro pour l'A/B

    # NON-DIRIGÉ : moyenne sur plusieurs seeds (le shuffle est aléatoire).
    base_calls = []
    for s in range(5):
        net, _, sol = _mesure(GenerateurInvention(atomes, seed=s), tache)
        assert sol is not None, f"non-dirigé n'a pas minté {tache.point_entree} (seed {s})"
        base_calls.append(net)
    base_moy = statistics.mean(base_calls)

    # DIRIGÉ : déterministe ; brut = recherche seule, net = cœur (top-5) inclus.
    dir_net, dir_brut, dir_sol = _mesure(
        GenerateurInventionDirige(GenerateurInvention(atomes), pred, coeur, topn=5), tache)
    generalise = dir_sol is not None and juge(dir_sol, tache.tests_held_out, LIM).passe

    print(f"    minté (dirigé) -> {dir_sol.strip().splitlines()[-1].strip() if dir_sol else '—'}")
    print(f"    appels-juge : NON-DIRIGÉ moy={base_moy:.0f} | DIRIGÉ brut={dir_brut} (recherche), "
          f"net={dir_net} (cœur inclus)")

    res = []
    res.append(_check(f"DISCORDE ({nom_dom}) : '{source_attendue}' est la plus CHAUDE au cœur mais "
                      f"PAS première au cerveau — les deux sens se contredisent (le plus chaud = '{plus_chaud}')",
                      discorde_ok))
    res.append(_check(f"RÉSOUT+GÉNÉRALISE ({nom_dom}) : l'invention dirigée minte {tache.point_entree} "
                      f"et il passe le HELD-OUT (vrai atome, pas un fluke)", generalise))
    res.append(_check(f"ÉCRASE ({nom_dom}) : dirigé recherche en {dir_brut} appel(s) vs non-dirigé≈{base_moy:.0f} "
                      f"— le mécanisme vise juste (coût de recherche écrasé)", dir_brut < base_moy / 2))
    return res


# --- SCALING : le coût dirigé reste ~plat (cœur borné) quand le non-dirigé croît -----------------
def _distracteurs(k):
    """k atomes confirmés DISTRACTEURS : aucun n'a de chaîne `x*x` -> aucun ne peut donner x**3.
    Ils gonflent le registre (donc le coût du non-dirigé), sans fournir la matière de cube."""
    tmpls = ["args[0] - {K}", "args[0] // {K}", "args[0] % {K}"]
    return [_atome(f"d{i}", tmpls[i % 3].format(K=2 + i)) for i in range(k)]


def _scaling(store_dir):
    tache = T_NOMBRE
    print(f"\n=== SCALING : T = cube, registre qui grandit (matière unique = carre, enterrée) ===")
    pred, coeur = _pred_coeur(store_dir, "SCALING", tache)
    distract = _distracteurs(24)
    CARRE = _atome("carre", "args[0] * args[0]")
    INCR = _atome("incremente", "args[0] + 1")   # rang 0 (le cerveau le croit utile) : il enterre carre

    print(f"    {'taille':<10}{'non-dirigé(moy)':<18}{'dirigé net':<14}{'dirigé brut'}")
    print("    " + "-" * 52)
    lignes = []
    for taille in (4, 8, 12, 16, 20):
        # carre placé APRÈS incremente (rang 0) -> enterré par le cerveau, rattrapé par le cœur.
        atomes = [INCR, CARRE] + distract[:taille - 2]
        nd = statistics.mean(_mesure(GenerateurInvention(atomes, seed=s), tache)[0] for s in range(3))
        net, brut, sol = _mesure(
            GenerateurInventionDirige(GenerateurInvention(atomes), pred, coeur, topn=5), tache)
        assert sol is not None, f"dirigé n'a pas minté cube (taille {taille})"
        lignes.append((taille, nd, net, brut))
        print(f"    {taille:<10}{nd:<18.0f}{net:<14}{brut}")

    nd_croit = lignes[-1][1] > lignes[0][1] * 1.5          # le non-dirigé GRANDIT nettement
    nets = [l[2] for l in lignes]
    dir_plat = max(nets) - min(nets) <= 4                  # le dirigé reste ~PLAT (cœur borné)
    gagne_grand = lignes[-1][2] < lignes[-1][1]            # au plus grand registre, dirigé net < non-dirigé
    croisement = any(l[2] < l[1] for l in lignes) and any(l[2] >= l[1] for l in lignes)

    res = []
    res.append(_check(f"SCALING-PLATEAU : le coût dirigé reste ~plat ({min(nets)}..{max(nets)}) quand le "
                      f"non-dirigé croît ({lignes[0][1]:.0f}->{lignes[-1][1]:.0f}) — le cœur borné plafonne",
                      nd_croit and dir_plat))
    res.append(_check(f"SCALING-CROISEMENT : un croisement existe et au registre réaliste (grand) dirigé "
                      f"net={lignes[-1][2]} < non-dirigé≈{lignes[-1][1]:.0f} — diriger paie quand c'est dur",
                      gagne_grand and croisement))
    return res


def main() -> int:
    resultats = []
    with tempfile.TemporaryDirectory() as d:
        resultats += _domaine("CHAÎNE", REG_CHAINE, T_CHAINE, "copie", d)
        resultats += _domaine("NOMBRE", REG_NOMBRE, T_NOMBRE, "carre", d)
        resultats += _scaling(d)

    print()
    if all(resultats):
        print(f"CURIOSITÉ DIRIGÉE VALIDÉE — {len(resultats)}/{len(resultats)}. La DISCORDE cerveau/cœur "
              f"(intuition de Yohan) est un signal RÉEL et EXPLOITABLE : sur deux domaines, le cœur "
              f"behavioral désigne la bonne matière que le cerveau syntaxique enterre, et muter celle-là EN "
              f"PREMIER minte l'atome (généralisé) en ÉCRASANT le coût de recherche. Et le SCALING tranche "
              f"honnêtement : le cœur étant borné (top-N), le coût dirigé reste ~plat quand le registre "
              f"grandit alors que l'aveugle croît -> au registre réaliste (régime du compounding), diriger "
              f"paie en net. Rien jeté (réordonne), seul le held-out promeut : au pire on perd des appels, "
              f"jamais un faux skill. L'invention n'est plus aveugle ; elle vise le trou.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. C'est un RÉSULTAT : la discorde ne dirige pas "
          f"(encore) mieux que le hasard, ou le scaling ne tient pas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
