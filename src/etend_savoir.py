"""
ETEND_SAVOIR — auto-extension du savoir par FERMETURE TRANSITIVE depuis kaikki (§6.2 b/c, 2026-06-18).

Réalise l'idée « frontière » de bootstrap_savoir à l'échelle du VRAI dictionnaire : on part de graines, on télécharge
leurs définitions, on en extrait le genus, puis on télécharge la FRONTIÈRE (genus cités mais pas encore définis), et
on itère — borné en rounds/mots. Résultat : un graphe is-a CONNECTÉ construit SEUL depuis kaikki, sur lequel
relation-lexicale raisonne en profondeur (chat -> … -> animal), tout dérivé des définitions officielles.

`telecharge_fn` est injectable -> la LOGIQUE de fermeture est testée hors réseau (valide_etend_savoir), le CLI utilise
le vrai réseau (ingere_kaikki.telecharge).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from charge_lexique import _cycle, coherence
from comprehension import Predicteur
from compounding import resoudre
from convertit_kaikki import aretes_isa, convertit
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def frontiere(lex: dict):
    """Genus CITÉS (hyper) mais pas encore ENTRÉES = ce qu'il faut chercher ensuite pour creuser la taxonomie."""
    hypers = {d["hyper"] for d in lex.values() if d.get("hyper")}
    return sorted(h for h in hypers if h not in lex)


def acyclise(lex: dict):
    """Garantit un graphe is-a ACYCLIQUE (une taxonomie est un DAG). De vraies définitions circulaires
    (action<->opération…) créent des cycles -> on retire l'arête qui les ferme. Renvoie (lex_dag, arêtes_coupées)."""
    lex = {m: dict(d) for m, d in lex.items()}
    coupes = []
    while True:
        cyc = _cycle(lex)
        if not cyc:
            break
        noeud = cyc[-2]                       # son hyper ferme le cycle (-> cyc[-1])
        coupes.append((noeud, lex[noeud]["hyper"]))
        lex[noeud]["hyper"] = None
    return lex, coupes


def etend(graines, rounds=4, max_mots=600, telecharge_fn=None):
    """Fermeture transitive bornée depuis kaikki. Renvoie (lexique_connecté, trace_par_round)."""
    if telecharge_fn is None:
        from ingere_kaikki import telecharge as telecharge_fn
    lignes, vus, trace = [], set(), []
    a_chercher = list(dict.fromkeys(graines))
    for _ in range(rounds):
        a_chercher = [m for m in a_chercher if m not in vus][: max(0, max_mots - len(vus))]
        if not a_chercher:
            break
        vus.update(a_chercher)
        lignes += telecharge_fn(a_chercher)
        lex = convertit(lignes)
        trace.append((len(a_chercher), len(lex)))
        a_chercher = frontiere(lex)
    lex, _ = acyclise(convertit(lignes))      # taxonomie = DAG garanti
    return lex, trace


def chaine(mot, edges):
    """Remonte la chaîne is-a complète (garde anti-cycle)."""
    suiv = dict(edges)
    out, cur, vus = [mot], mot, {mot}
    while cur in suiv and suiv[cur] not in vus:
        cur = suiv[cur]
        out.append(cur)
        vus.add(cur)
    return out


def raisonneur(edges):
    """Récupère est_un de l'orchestrateur VIVANT (relation-lexicale) appliqué au graphe is-a fourni."""
    st = Store(Path(tempfile.mkdtemp()) / "s.jsonl")
    orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), relation_lexicale=True)
    # On épingle la variante DIRIGÉE (transitive mais orientée) : a->c vrai MAIS c->a faux -> exclut l'atteignabilité
    # non dirigée (sinon « animal est une sorte de chat » serait vrai).
    t = Tache(id="es/est_un", point_entree="est_un", prompt='def est_un(e,x,y):\n    """..."""',
              tests=("def check(c):\n    assert c([('a','b'),('b','c')],'a','c') == True\n"
                     "    assert c([('a','b'),('b','c')],'c','a') == False\ncheck(est_un)"), tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    return lambda x, y: ns["est_un"](edges, x.lower(), y.lower())


def main(argv) -> int:
    from charge_lexique import ecris
    graines = [m.strip() for m in (argv[0] if argv else "chat,paris,lyon,rose").split(",")]
    rounds = int(argv[1]) if len(argv) > 1 else 4
    max_mots = int(argv[2]) if len(argv) > 2 else 300
    lex, trace = etend(graines, rounds=rounds, max_mots=max_mots)
    edges = aretes_isa(lex)
    h = coherence(lex)
    n_syn = sum(len(d.get("syn") or []) for d in lex.values())
    n_ant = sum(len(d.get("ant") or []) for d in lex.values())
    if lex:
        ecris(lex, "datasets/lexique_kaikki.jsonl")
    print(f"Fermeture transitive : {h['entrees']} entrées (is-a={len(edges)}, syn={n_syn}, ant={n_ant}), "
          f"acyclique={h['acyclique']}, frontière restante={len(frontiere(lex))}")
    print(f"Trace (demandés→total par round) : {trace}")
    print("\nChaînes is-a AUTO-CONSTRUITES (depuis kaikki) :")
    for m in graines[:8]:
        if m in lex:
            print(f"    {m} : {' -> '.join(chaine(m, edges))}")
    if edges:
        eu = raisonneur(edges)
        print("\nRaisonnement PROFOND (la réalité juge) :")
        for x, y in [(graines[0], "animal"), (graines[0], "chose"), (graines[0], graines[0])]:
            print(f"  « {x} est-il un(e) {y} ? » -> {'oui' if eu(x, y) else 'non'}")
    print(f"\n-> Exporté datasets/lexique_kaikki.jsonl ({h['entrees']} entrées). Lexique massif persistant prêt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
