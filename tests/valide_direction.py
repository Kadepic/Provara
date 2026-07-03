"""
Validation de la DIRECTION — la compréhension qui DIRIGE la boucle vivante.

Point 2 du plan. Jusqu'ici la boucle BRASSE : elle juge les candidats dans un ordre
aveugle jusqu'à tomber sur un qui passe. Ici la compréhension DIRIGE : le `Predicteur`
réordonne les candidats (`GenerateurDirige`) pour juger d'abord les prédits-utiles.
On ne JETTE rien (réordonner ≠ filtrer) -> la couverture reste identique ; on économise
seulement des APPELS AU JUGE (la partie chère). « Diriger au lieu de brasser », chiffré.

Mise en scène : tâche cible = max_carres -> max(x * x for x in args[0]). Le store connaît
deux succès sur D'AUTRES tâches : somme_carres (sum + « x * x ») et max_plus_un (max + « x + 1 »).
Le générateur de base propose un FLUX MIXTE pour max_carres : du garbage, un piège
prédit-utile-mais-FAUX (sum(x*x...) — bonne brique, mauvaise tâche), et la vraie solution
(max(x*x...)), placée TARD. On exige :

  1. COUVERTURE ÉGALE : les trois approches trouvent la MÊME solution (rien n'est jeté).
  2. DIRIGER ÉCONOMISE : le dirigé-RICHE atteint le succès en bien MOINS d'appels au juge.
  3. LA RICHESSE EST LE LEVIER : le dirigé-CONDITIONS ne fait pas mieux que l'aveugle
     (il ne reconnaît pas « x * x » -> ne sait pas remonter la vraie solution). C'est le
     vocabulaire du point 1 qui rend la direction utile.
  4. MÉMOIRE COURTE : après que le juge a réfuté le piège, la passe SUIVANTE l'évite
     (rétrogradé, pas jeté) -> coût encore plus bas. La direction s'affine par l'erreur.
  5. HONNÊTETÉ : seul le juge promeut (on re-confirme le succès) ; la mémoire courte vit
     en RAM, jamais dans le store.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from generateur import TYPES_CONDITIONS, TYPES_RICHES, GenerateurDirige
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(id, fn, tests):
    return Tache(id=id, point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# Deux succès sur d'AUTRES tâches -> la mémoire LONGUE du prédicteur riche.
A = _t("seed/somme_carres", "somme_carres",
       "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\ncheck(somme_carres)")
A_SOL = "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n"
B = _t("seed/max_plus_un", "max_plus_un",
       "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([0]) == 1\ncheck(max_plus_un)")
B_SOL = "def max_plus_un(*args, **kwargs):\n    return max(x + 1 for x in args[0])\n"

# Tâche cible (absente du store).
CIBLE = _t("cible/max_carres", "max_carres",
           "def check(c):\n    assert c([1,2,3]) == 9\n    assert c([-3,2]) == 9\n    assert c([4]) == 16\ncheck(max_carres)")


def _c(body):
    return f"def max_carres(*args, **kwargs):\n    return {body}\n"


# Flux MIXTE pour max_carres : garbage + piège prédit-utile-mais-faux + vraie solution (tard).
POOL = [
    _c("None"),                            # garbage (prédit non)
    _c("0"),                               # garbage
    _c("args[0]"),                         # garbage
    _c("len(args[0])"),                    # garbage
    _c("sum(x * x for x in args[0])"),     # PIÈGE : prédit-utile (riche) mais FAUX pour max_carres
    _c("[]"),                              # garbage
    _c("max(args[0])"),                    # faux (et prédit non : sens inconnu)
    _c("min(x * x for x in args[0])"),     # faux (prédit non : squelette/sens pas connus ensemble)
    _c("max(x * x for x in args[0])"),     # VRAIE solution (prédit-utile riche), placée TARD
    _c("True"),                            # garbage
]
IDX_VRAI = 8


class _Banc:
    """Générateur de base à ordre FIXE (pour une mesure déterministe et lisible)."""
    def __init__(self, pool):
        self._pool = list(pool)

    def propose(self, prompt: str, n: int) -> list[str]:
        return self._pool[:n]


class Compteur:
    """Enveloppe le juge pour COMPTER les appels (la ressource chère)."""
    def __init__(self):
        self.n = 0

    def juge(self, code, tests, limites=LIM):
        self.n += 1
        return juge(code, tests, limites)


def resoudre(generateur, tache, n, compteur, predicteur=None):
    """Juge les candidats DANS L'ORDRE proposé, s'arrête au 1er succès (la « boucle
    vivante » en mode résolution). Compte les appels au juge. Si un prédicteur est
    fourni, un échec nourrit sa mémoire COURTE (sans rien graver de durable)."""
    for code in generateur.propose(tache.prompt, n):
        v = compteur.juge(code, tache.tests)
        if v.passe:
            return code
        if predicteur is not None:
            predicteur.note_echec(code)
    return None


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    n = len(POOL)

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for tache, sol in [(A, A_SOL), (B, B_SOL)]:
            v = juge(sol, tache.tests, LIM)
            assert v.passe, f"pré-condition : {tache.id}"
            store.ajoute(tache, sol, v)
        taille_store_avant = len(store)

        base = _Banc(POOL)
        pred_cond = Predicteur(store, types=TYPES_CONDITIONS)
        pred_riche = Predicteur(store, types=TYPES_RICHES)

        # --- Non-dirigé (aveugle) : ordre brut du flux ---
        c0 = Compteur()
        sol0 = resoudre(base, CIBLE, n, c0)

        # --- Dirigé par prédicteur CONDITIONS (vocabulaire pauvre) ---
        c1 = Compteur()
        sol1 = resoudre(GenerateurDirige(base, pred_cond), CIBLE, n, c1, pred_cond)

        # --- Dirigé par prédicteur RICHE, passe 1 (mémoire courte vide) ---
        c2 = Compteur()
        sol2 = resoudre(GenerateurDirige(base, pred_riche), CIBLE, n, c2, pred_riche)
        # --- Dirigé RICHE, passe 2 (le piège réfuté est désormais en mémoire courte) ---
        c3 = Compteur()
        sol3 = resoudre(GenerateurDirige(base, pred_riche), CIBLE, n, c3, pred_riche)

        print(f"Flux de {n} candidats pour max_carres (vraie solution en position {IDX_VRAI + 1}).")
        print("Appels au juge pour atteindre le 1er succès :\n")
        print(f"    non-dirigé (aveugle)        -> {c0.n}")
        print(f"    dirigé / vocabulaire pauvre -> {c1.n}")
        print(f"    dirigé / vocabulaire riche  -> {c2.n}   (passe 1)")
        print(f"    dirigé / riche, passe 2     -> {c3.n}   (le piège réfuté est évité)\n")

        bonne = POOL[IDX_VRAI]
        toutes_trouvent_la_bonne = sol0 == sol1 == sol2 == sol3 == bonne
        # 1. Couverture égale : les quatre runs trouvent la MÊME (vraie) solution.
        resultats.append(_check("couverture égale : les 4 trouvent la même solution (rien n'est jeté)",
                                toutes_trouvent_la_bonne))
        # 2. Diriger économise (riche ≪ aveugle).
        resultats.append(_check(f"diriger (riche) économise des appels au juge ({c2.n} ≪ {c0.n})",
                                c2.n < c0.n))
        # 3. La richesse est le levier : conditions seules ne font pas mieux que l'aveugle.
        resultats.append(_check(f"vocabulaire pauvre ne dirige PAS (={c0.n} comme l'aveugle) ; riche, oui ({c2.n})",
                                c1.n == c0.n and c2.n < c1.n))
        # 4. Mémoire courte : la passe suivante évite le piège -> coût plus bas.
        resultats.append(_check(f"mémoire courte : passe 2 < passe 1 ({c3.n} < {c2.n}) — la direction s'affine par l'erreur",
                                c3.n < c2.n))
        # 5. Honnêteté : la direction n'a rien gravé (store inchangé) ; le succès est re-confirmé par le juge.
        store_intact = len(store) == taille_store_avant
        succes_reconfirme = juge(bonne, CIBLE.tests, LIM).passe
        memoire_courte_en_ram = bool(pred_riche._echecs_courts) and \
            not any(s.solution in pred_riche._echecs_courts for s in store)
        resultats.append(_check("honnêteté : store intact (direction ne grave rien) + succès re-confirmé par le juge + mémoire courte en RAM",
                                store_intact and succes_reconfirme and memoire_courte_en_ram))

    print()
    if all(resultats):
        print(f"DIRECTION VALIDÉE — {len(resultats)}/{len(resultats)}. La compréhension DIRIGE la boucle : "
              f"à couverture égale, on appelle le juge bien moins souvent ; c'est le vocabulaire riche (pt 1) "
              f"qui rend la direction utile ; et la mémoire courte affine le tir au fil des erreurs — sans rien figer.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
