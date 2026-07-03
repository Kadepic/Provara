"""
VALIDATION du MOTEUR DE DÉCOUVERTE D'INVENTIONS (moteur_invention.py).

Cœur = la SOUNDNESS de la prétention « INVENTION » :
  - INVENTION n'est rendu que pour une réalisation UNIQUE sous le spec, VÉRIFIÉE sur le held-out,
    NOUVELLE vs l'existant -> et son code, exécuté, reproduit RÉELLEMENT le held-out.
  - Un spec FAIBLE (coïncidences concurrentes) -> AMBIGU, JAMAIS une fausse invention.
  - Une cible déjà couverte -> EXISTE_DEJA. Une cible non réalisable -> BRIQUE_MANQUANTE. Contradiction -> INCOHERENT.
"""
from __future__ import annotations

from garde_ressources import borne
import moteur_invention as M

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def reproduit(par, paires):
    f = M._callable(par, "f")
    return M._reproduit(f, paires)


# 1) EXISTE DÉJÀ
v = M.examine_cible("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)])
check("somme -> EXISTE_DEJA (somme)", v.statut == M.EXISTE_DEJA and v.proche_de == "somme")

# 2) INVENTION amplitude (max-min) + le code rend RÉELLEMENT le held-out.
held_amp = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]
v = M.examine_cible("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)], held_amp)
check("amplitude -> INVENTION", v.statut == M.INVENTION)
check("amplitude : le code fourni reproduit le held-out", reproduit(v.par, held_amp))
check("amplitude : comportement = max-min", reproduit(v.par, [([1, 9, 3], 8), ([4, 4], 0), ([0, 100], 100)]))

# 3) INVENTION somme_carres + vérif held.
held_sc = [([5], 25), ([0, 4], 16), ([1, 1], 2)]
v = M.examine_cible("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], held_sc)
check("somme_carres -> INVENTION", v.statut == M.INVENTION)
check("somme_carres : le code fourni reproduit le held-out", reproduit(v.par, held_sc))

# 4) SOUNDNESS ANTI-COÏNCIDENCE : spec FAIBLE -> AMBIGU, jamais une fausse invention.
v = M.examine_cible("amp_faible", "x", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9)])
check("amplitude FAIBLE -> AMBIGU (pas de fausse invention)", v.statut == M.AMBIGU and v.statut != M.INVENTION)
check("AMBIGU porte une sonde discriminante", v.sonde is not None)
v = M.examine_cible("deux", "x", [([9, 8, 7], 8), ([1, 2, 3], 2)], [([5, 6, 7], 6)])
check("deuxième-élément FAIBLE -> AMBIGU", v.statut == M.AMBIGU)

# 5) FRONTIÈRE QUI SE DÉPLACE. `rle` (run-length ENCODE) est devenu une CAPACITÉ le 2026-06-24 (nuit : etend_vocabulaire
#    a acquis le GROUPBY -> [[valeur, compte], …]). Remplace produit_cumulatif (capacité 2026-06-23) ; comme lui,
#    « le plafond monte, le benchmark de frontière se déplace ». Le NOUVEAU benchmark = rle-DECODE (l'inverse :
#    [[v, c], …] -> liste plate ; double boucle/expansion hors vocab borné).
v = M.examine_cible("rle", "x", [([1, 1, 2, 3, 3, 3], [[1, 2], [2, 1], [3, 3]]), ([5, 5, 5, 2], [[5, 3], [2, 1]])],
                    [([7, 8, 8], [[7, 1], [8, 2]]), ([4, 4], [[4, 2]])])
check("rle (encode) -> INVENTION (capacité acquise via groupby)", v.statut == M.INVENTION and reproduit(v.par, [([7, 8, 8], [[7, 1], [8, 2]]), ([4, 4], [[4, 2]])]))
#    MISE À JOUR 2026-06-24 (après-nuit) : rle-DECODE est devenu une CAPACITÉ (etend_vocabulaire a acquis l'EXPANSION
#    [[v, c], …] -> liste plate par double boucle). La frontière se DÉPLACE de nouveau vers le FLATTEN RÉCURSIF
#    profondeur arbitraire ([1, [2, [3, 4]], 5] -> [1, 2, 3, 4, 5] : récursion vraie, hors vocab borné par compréhension).
v = M.examine_cible("rle_decode", "x", [([[5, 3], [2, 1]], [5, 5, 5, 2]), ([[7, 1], [8, 2]], [7, 8, 8])],
                    [([[1, 2], [3, 1]], [1, 1, 3]), ([[4, 2]], [4, 4])])
check("rle-decode -> INVENTION (capacité acquise via expansion)", v.statut == M.INVENTION and reproduit(v.par, [([[1, 2], [3, 1]], [1, 1, 3]), ([[4, 2]], [4, 4])]))
#    MISE À JOUR 2026-06-24 (après-midi, 2e franchissement) : le FLATTEN RÉCURSIF est devenu une CAPACITÉ — le
#    vocabulaire a acquis la RÉCURSION par auto-application (1er atome récursif : `(lambda _g: _g(_g, x))(…)`).
#    La frontière se DÉPLACE vers le DEEP-REVERSE (renverser une liste imbriquée à TOUS les niveaux : récursion
#    STRUCTURELLE qui reconstruit l'imbrication, hors du combinateur flatten ; sortie structurée -> zéro coïncidence).
v = M.examine_cible("flatten_rec", "x", [([1, [2, [3, 4]], 5], [1, 2, 3, 4, 5]), ([[1, 2], [3, [4]]], [1, 2, 3, 4])],
                    [([1, [2, [3, [4, 5]]]], [1, 2, 3, 4, 5]), ([[[1]], 2], [1, 2])])
check("flatten récursif -> INVENTION (récursion par auto-application acquise)", v.statut == M.INVENTION and reproduit(v.par, [([1, [2, [3, [4, 5]]]], [1, 2, 3, 4, 5]), ([[[1]], 2], [1, 2])]))
v = M.examine_cible("deep_reverse", "x", [([1, [2, 3], 4], [4, [3, 2], 1]), ([[1, 2], [3, 4]], [[4, 3], [2, 1]])],
                    [([1, [2, [3, 4]]], [[[4, 3], 2], 1]), ([5, [6, 7], 8, 9], [9, 8, [7, 6], 5])])
check("deep-reverse -> BRIQUE_MANQUANTE (nouvelle frontière)", v.statut == M.BRIQUE_MANQUANTE)

# 6) INCOHÉRENT
v = M.examine_cible("absurde", "x", [([1, 2], 5)], [([1, 2], 9)])
check("absurde -> INCOHERENT", v.statut == M.INCOHERENT)

# 6bis) REGISTRE EXISTANT ÉLARGI — chaque capacité est EXÉCUTABLE, et le registre reste « propre de
#       coïncidences » : AUCUNE capacité seule ne reproduit les frontières connues (médiane, 2e-élément)
#       sur leurs exemples — sinon elle masquerait de vraies frontières (cf. sum//len retiré, coïncidence).
front_mediane = [([3, 1, 2], 2), ([5, 1, 9], 5), ([10, 0, 5], 5), ([2, 8, 4], 4)]
front_deux = [([9, 8, 7], 8), ([1, 2, 3], 2), ([5, 6, 7], 6)]
toutes_exec = all(M._callable(expr, capa) is not None for capa, expr in M.EXISTANT.items())
check(f"EXISTANT élargi ({len(M.EXISTANT)} capacités) : toutes exécutables", toutes_exec)
propre = not any(reproduit(expr, front_mediane) or reproduit(expr, front_deux) for expr in M.EXISTANT.values())
check("EXISTANT propre de coïncidences (aucune capacité ne masque médiane / 2e-élément)", propre)

# 7) INVARIANT GLOBAL : sur tout le batch, TOUTE invention rend un code qui reproduit son held-out
#    (aucune invention fausse n'est jamais émise).
batch = [
    ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], held_sc),
    ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)], held_amp),
    ("amp_faible", "x", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9)]),
    ("rle", "x", [([1, 1, 2, 3, 3, 3], [[1, 2], [2, 1], [3, 3]]), ([5, 5, 5, 2], [[5, 3], [2, 1]])],
     [([7, 8, 8], [[7, 1], [8, 2]]), ([4, 4], [[4, 2]])]),
]
inv_sound = True
for nom, sig, ex, held in batch:
    v = M.examine_cible(nom, sig, ex, held)
    if v.statut == M.INVENTION and not reproduit(v.par, held):
        inv_sound = False
check("INVARIANT : toute INVENTION reproduit son held-out (jamais de faux)", inv_sound)

# 8) ROBUSTESSE CROSS-DOMAINE (2026-06-23) — le moteur EXAMINE sans crash hors listes-d'entiers
#    (chaînes / dict / matrices) et n'émet JAMAIS de faux INVENTION sur du trivial/déjà-existant.
#    Régression visée : `sondes_auto` plantait sur les matrices (e+1 sur une ligne-liste ; tuple-de-listes
#    non hashable). Fix type-safe -> sondes arithmétiques réservées au numérique + dédup par repr.
v = M.examine_cible("chaine_renverse", "x", [("abc", "cba"), ("ko", "ok")], [("salut", "tulas"), ("a", "a")])
check("chaîne renverse -> EXISTE_DEJA (pas de faux invention)", v.statut == M.EXISTE_DEJA)
v = M.examine_cible("chaine_majuscule", "x", [("abc", "ABC")], [("salut", "SALUT"), ("xy", "XY")])
check("chaîne majuscule -> EXISTE_DEJA", v.statut == M.EXISTE_DEJA)
v = M.examine_cible("mat_transpose", "x", [([[1, 2], [3, 4]], [[1, 3], [2, 4]])],
                    [([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]])])
check("matrice transpose : EXAMINÉE sans crash (TypeError éliminé)",
      v.statut in (M.INVENTION, M.EXISTE_DEJA, M.BRIQUE_MANQUANTE, M.AMBIGU))
check("matrice transpose : aucune fausse invention (si INVENTION -> reproduit le held)",
      v.statut != M.INVENTION or reproduit(v.par, [([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]])]))

# 9) REGISTRE EXISTANT ÉLARGI AUX MATRICES/DICT (2026-06-23) — cibles matricielles/dict désormais RECONNUES
#    comme « ce qui existe » (EXISTE_DEJA), base de nouveauté posée pour ces domaines.
v = M.examine_cible("mat_somme_lignes", "x", [([[1, 2], [3, 4]], [3, 7])],
                    [([[5, 5], [1, 1], [2, 3]], [10, 2, 5])])
check("matrice somme_lignes -> EXISTE_DEJA (registre matriciel)",
      v.statut == M.EXISTE_DEJA and v.proche_de == "matrice_somme_lignes")
v = M.examine_cible("mat_transposee2", "x", [([[1, 2], [3, 4]], [[1, 3], [2, 4]])],
                    [([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]])])
check("matrice transposée -> EXISTE_DEJA (registre matriciel)", v.statut == M.EXISTE_DEJA)
v = M.examine_cible("dict_vals", "x", [({"a": 1, "b": 2}, [1, 2])], [({"x": 5}, [5]), ({"p": 3, "q": 4}, [3, 4])])
check("dict valeurs -> EXISTE_DEJA (registre dict)",
      v.statut == M.EXISTE_DEJA and v.proche_de == "dict_valeurs")
# COLLISION-CHECK : les nouvelles ops matrice/dict ne reproduisent AUCUNE frontière 1-D (elles erreur dessus).
nouvelles = ["matrice_transposee", "matrice_somme_lignes", "matrice_somme_colonnes", "matrice_diagonale",
             "matrice_aplatie", "dict_valeurs", "dict_cles", "dict_paires_triees"]
propre_neuf = not any(reproduit(M.EXISTANT[c], front_mediane) or reproduit(M.EXISTANT[c], front_deux)
                      for c in nouvelles)
check("ops matrice/dict propres (aucune ne masque une cible 1-D)", propre_neuf)

# 10) INVENTIONS MATRICIELLES (2026-06-23) — le moteur TROUVE de vraies recombinaisons matricielles
#     (pas seulement EXISTE_DEJA) : trace = sum∘diagonale, grand_total = sum∘aplatie, max_par_ligne.
#     Soundness préservée : chaque INVENTION reproduit son held-out ; un spec faible -> AMBIGU, jamais un faux.
held_trace = [([[5, 6, 7], [8, 9, 0], [1, 2, 3]], 17), ([[10, 1], [1, 10]], 20), ([[1, 9], [9, 4]], 5)]
v = M.examine_cible("trace", "x", [([[1, 2], [3, 4]], 5), ([[2, 0], [0, 3]], 5)], held_trace)
check("trace -> INVENTION (sum de la diagonale)", v.statut == M.INVENTION)
check("trace : le code fourni reproduit le held-out", reproduit(v.par, held_trace))
held_gt = [([[1, 1, 1], [2, 2, 2]], 9), ([[10, 0], [0, 5]], 15)]
v = M.examine_cible("grand_total", "x", [([[1, 2], [3, 4]], 10), ([[5, 5], [0, 0]], 10)], held_gt)
check("grand_total -> INVENTION (somme de tous les éléments)", v.statut == M.INVENTION)
check("grand_total : le code fourni reproduit le held-out", reproduit(v.par, held_gt))
held_mpl = [([[0, 5, 2], [7, 1, 3]], [5, 7]), ([[6, 6], [1, 2]], [6, 2])]
v = M.examine_cible("max_par_ligne", "x", [([[1, 2], [4, 3]], [2, 4]), ([[9, 1], [2, 8]], [9, 8])], held_mpl)
check("max_par_ligne -> INVENTION", v.statut == M.INVENTION)
check("max_par_ligne : le code fourni reproduit le held-out", reproduit(v.par, held_mpl))
# SOUNDNESS : spec faible (max satisfait aussi par max-de-diagonale) -> AMBIGU, jamais une fausse invention.
v = M.examine_cible("max_glob_faible", "x", [([[1, 2], [3, 4]], 4), ([[9, 1], [2, 3]], 9)],
                    [([[0, 5, 2], [1, 8, 3]], 8), ([[7, 7], [7, 7]], 7)])
check("max_global FAIBLE -> AMBIGU (sound, pas de fausse invention)", v.statut == M.AMBIGU)

# 11) INVENTIONS DICT (2026-06-23) — recombinaisons sur mapping : somme_valeurs = sum∘values,
#     max_valeur = max∘values, cle_du_max = argmax (max(x, key=x.get)). Soundness : reproduit le held-out.
held_sv = [({"p": 3, "q": 4, "r": 1}, 8), ({"z": 9}, 9)]
v = M.examine_cible("somme_valeurs", "x", [({"a": 1, "b": 2}, 3), ({"x": 5, "y": 5}, 10)], held_sv)
check("somme_valeurs -> INVENTION (sum des valeurs)", v.statut == M.INVENTION)
check("somme_valeurs : le code fourni reproduit le held-out", reproduit(v.par, held_sv))
held_cdm = [({"p": 3, "q": 4, "r": 1}, "q"), ({"z": 9, "w": 2}, "z")]
v = M.examine_cible("cle_du_max", "x", [({"a": 1, "b": 7}, "b"), ({"x": 5, "y": 2}, "x")], held_cdm)
check("cle_du_max -> INVENTION (argmax sur dict)", v.statut == M.INVENTION)
check("cle_du_max : le code fourni reproduit le held-out", reproduit(v.par, held_cdm))

# 12) INVENTIONS CHAÎNES-COMPOSITIONS (2026-06-23) — recombinaisons sur mots/caractères : initiales = join∘
#     first∘split, mot_le_plus_long = argmax-len∘split, inverse_par_mot, compte_voyelles. + GARDE SOUNDNESS :
#     une cible chaîne ne doit JAMAIS être faussement EXISTE_DEJA=somme (bug 1-tuple des sondes, corrigé).
held_ini = [("vive la france", "vlf"), ("a b c d", "abcd")]
v = M.examine_cible("initiales", "x", [("nous allons bien", "nab"), ("bonjour le monde", "blm")], held_ini)
check("initiales -> INVENTION (pas un faux EXISTE_DEJA=somme)", v.statut == M.INVENTION)
check("initiales : le code fourni reproduit le held-out", reproduit(v.par, held_ini))
held_mpl = [("ok extraordinaire fin", "extraordinaire"), ("a bb ccc", "ccc")]
v = M.examine_cible("mot_le_plus_long", "x", [("le chat dort", "chat"), ("un grand jardin", "jardin")], held_mpl)
check("mot_le_plus_long -> INVENTION", v.statut == M.INVENTION)
check("mot_le_plus_long : reproduit le held-out", reproduit(v.par, held_mpl))
held_cv = [("brrr", 0), ("aurore", 4)]
v = M.examine_cible("compte_voyelles", "x", [("banane", 3), ("ciel", 2)], held_cv)
check("compte_voyelles -> INVENTION", v.statut == M.INVENTION)
check("compte_voyelles : reproduit le held-out", reproduit(v.par, held_cv))

# 13) COMPLÉTIONS DE FRONTIÈRE (2026-06-23, sonde de frontière) — recombinaisons naturelles comblées :
#     agrégat FILTRÉ (somme des pairs), anti-diagonale, produit de diagonale (prod), dernières lettres, longueur
#     totale des mots. Tous INVENTION + reproduisent leur held-out (sound).
held = [([0, 1, 2], 2), ([4, 4], 8)]
v = M.examine_cible("somme_pairs", "x", [([1, 2, 3, 4], 6), ([2, 5], 2)], held)
check("somme des pairs (agrégat filtré) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [3, 5, 7])]
v = M.examine_cible("antidiagonale", "x", [([[1, 2], [3, 4]], [2, 3])], held)
check("anti-diagonale -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([[2, 1], [1, 5]], 10), ([[3, 0], [0, 3]], 9)]
v = M.examine_cible("produit_diagonale", "x", [([[2, 0], [0, 3]], 6), ([[1, 5], [5, 4]], 4)], held)
check("produit de diagonale (prod) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [("vive la france", "eae"), ("ab cd", "bd")]
v = M.examine_cible("dernieres_lettres", "x", [("nous allons bien", "ssn"), ("bonjour le monde", "ree")], held)
check("dernières lettres de chaque mot -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [("xx yy zz", 6), ("mot", 3)]
v = M.examine_cible("longueur_totale_mots", "x", [("le chat", 6), ("a bb", 3)], held)
check("longueur totale des mots -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 14) COMPOSITION DE 2e NIVEAU — LISTE-OP∘map (2026-06-23) : transformer chaque élément PUIS réordonner.
#     carres_tries = sorted∘map(carré), carres_renverses = map(carré)[::-1] (données DISCRIMINANTES : entrées
#     NON triées -> distingue reverse de sort-desc, sinon AMBIGU). Comble le gap 2e niveau de façon additive+sound.
held = [([4, 1, 3], [1, 9, 16]), ([6, 0], [0, 36])]
v = M.examine_cible("carres_tries", "x", [([3, 1, 2], [1, 4, 9]), ([2, 5], [4, 25])], held)
check("carrés triés (sorted∘map) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, 2, 3], [9, 4, 1]), ([5, 2], [4, 25])]
v = M.examine_cible("carres_renverses", "x", [([3, 1, 2], [4, 1, 9]), ([2, 3, 1], [1, 9, 4])], held)
check("carrés renversés (map[::-1]) -> INVENTION (données discriminantes)",
      v.statut == M.INVENTION and reproduit(v.par, held))

# 15) NOUVELLES FAMILLES DE RAISONNEMENT (2026-06-23, sonde de familles) : fenêtre (somme par paires),
#     map-mots→liste (longueurs des mots), amplitude par ligne (matrice), filtre-liste (positifs seulement).
held = [([5, 5, 5], [10, 10]), ([2, 8], [10])]
v = M.examine_cible("paires_sommes", "x", [([1, 2, 3], [3, 5]), ([4, 0, 1], [4, 1])], held)
check("somme par paires consécutives -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [("xx yyy", [2, 3]), ("mot", [3])]
v = M.examine_cible("longueurs_mots", "x", [("le chat dort", [2, 4, 4]), ("a bb", [1, 2])], held)
check("longueurs des mots (map→liste) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([[0, 9], [4, 1], [7, 7]], [9, 3, 0])]
v = M.examine_cible("amplitude_par_ligne", "x", [([[1, 5, 2], [3, 3, 3]], [4, 0])], held)
check("amplitude par ligne (matrice) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([-2, -1], []), ([3, -3, 1], [3, 1])]
v = M.examine_cible("positifs_seulement", "x", [([-1, 2, -3, 4], [2, 4]), ([0, 5], [5])], held)
check("filtre-liste (positifs seulement) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 16) RAISONNEMENT POSITIONNEL (indices) + CROSS-DOMAINE string→dict (2026-06-23, sonde cross-domaine) :
#     freq_mots (fréquence de mots), indices des positifs, dict(enumerate), somme pondérée par l'indice.
held = [("y y", {"y": 2}), ("p q p", {"p": 2, "q": 1})]
v = M.examine_cible("freq_mots", "x", [("a a b", {"a": 2, "b": 1}), ("x", {"x": 1})], held)
check("fréquence des mots (string→dict) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([0, -1, 2], [2]), ([1, 1], [0, 1])]
v = M.examine_cible("indices_positifs", "x", [([-1, 3, -2, 4], [1, 3]), ([5, 0], [0])], held)
check("indices des positifs (positionnel) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([7, 8, 9], {0: 7, 1: 8, 2: 9}), ([3], {0: 3})]
v = M.examine_cible("dict_par_index", "x", [([10, 20], {0: 10, 1: 20}), ([5], {0: 5})], held)
check("dict indexé par position (enumerate) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, 0, 1], 2), ([2, 2, 2], 6)]
v = M.examine_cible("somme_ponderee_index", "x", [([10, 20, 30], 80), ([5, 5], 5)], held)
check("somme pondérée par l'indice -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 17) TÂCHES RÉELLES (corpus réel 2026-06-23) — capacités d'un vrai assistant : élément-vs-agrégat
#     (normaliser, %), tri indexé (top-N, médiane avec données DISCRIMINANTES len 5), chiffres d'un entier,
#     prédicat palindrome, arithmétique 2-champs (progression %).
held = [([5, 2, 8], [3, 0, 6]), ([0, 4], [0, 4])]
v = M.examine_cible("normaliser_min", "x", [([3, 1, 5], [2, 0, 4]), ([10, 10], [0, 0])], held)
check("normaliser par le min (élément-vs-agrégat) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, 3], [25, 75]), ([5], [100])]
v = M.examine_cible("pourcentage_du_total", "x", [([1, 1, 2], [25, 25, 50]), ([2, 2], [50, 50])], held)
check("pourcentage du total -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
# TRI INDEXÉ activé (choix Yohan) : top-N et médiane sont des CAPACITÉS. Médiane avec données DISCRIMINANTES
# len 5 (sinon coïncide avec 2e-max).
held = [([1, 2, 3, 4], [4, 3]), ([7, 7, 1], [7, 7])]
v = M.examine_cible("top_2", "x", [([3, 1, 5, 2], [5, 3]), ([9, 0, 4], [9, 4])], held)
check("top 2 (tri indexé) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
# La frontière a BOUGÉ : médiane n'est plus BRIQUE_MANQUANTE (l'engine sait l'exprimer via le tri-indexé).
# Le verdict exact peut être AMBIGU (plusieurs index de tri coïncident sur peu d'exemples = spec sous-déterminé,
# refus de committer = sound) ; ce qui compte = ce n'est PLUS une frontière.
v = M.examine_cible("mediane", "x", [([5, 1, 4, 2, 3], 3), ([9, 0, 7, 1, 2], 2)], [([3, 1, 2, 5, 4], 3), ([10, 0, 5, 1, 2], 2)])
check("médiane n'est plus une frontière (tri-indexé activé)", v.statut != M.BRIQUE_MANQUANTE)
held = [(999, 27), (5, 5), (100, 1)]
v = M.examine_cible("somme_chiffres", "x", [(123, 6), (40, 4)], held)
check("somme des chiffres (entier) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [("ressasser", True), ("abc", False)]
v = M.examine_cible("est_palindrome", "x", [("kayak", True), ("bonjour", False)], held)
check("palindrome (prédicat) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([5, 5], 100), ([0, 8], 0)]
v = M.examine_cible("progression_pct", "x", [([3, 10], 30), ([1, 4], 25)], held)
check("progression % ([fait, total]) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 18) FAMILLES (2) — map conditionnel (abs, ReLU), scan (running max), comptage relationnel (montées, données
#     DISCRIMINANTES vs somme-pairs), dédup en ordre (sonde familles 2, 2026-06-23).
held = [([4, -4], [4, 4]), ([-2], [2])]
v = M.examine_cible("abs_chaque", "x", [([-3, 2, -1], [3, 2, 1]), ([0, -5], [0, 5])], held)
check("abs de chaque (map) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([0, -1, 3], [0, 0, 3]), ([-2, 2], [0, 2])]
# DÉTERMINANT (nuit 2026-06-24) : [2,-1,3]->[2,0,3] (positifs en positions NON triées-par-abs). Sans lui, l'ajout de
# la primitive `relu` ouvre le concurrent `relu(sorted(x,key=abs))` qui réordonne et coïncide sur les autres données
# -> AMBIGU honnête. On détermine l'ORDRE D'ORIGINE. (Moteur plus riche, FAUX=0 préservé.)
v = M.examine_cible("clamp_positif", "x", [([-3, 2, -1], [0, 2, 0]), ([5, -5], [5, 0]), ([2, -1, 3], [2, 0, 3])], held)
check("ReLU (map conditionnel) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([2, 2, 1], [2, 2, 2]), ([0, 9], [0, 9])]
v = M.examine_cible("running_max", "x", [([1, 3, 2, 5], [1, 3, 3, 5]), ([4, 1], [4, 4])], held)
check("running max (scan) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, 2, 3], 2), ([9, 9, 1], 0)]   # discriminant : montées ≠ somme-pairs
v = M.examine_cible("compte_montees", "x", [([1, 5, 2, 4], 2), ([7, 1, 3], 1)], held)
check("nombre de montées (comptage relationnel) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([3, 1, 3, 2], [3, 1, 2]), ([4], [4])]
v = M.examine_cible("uniques_ordre", "x", [([1, 2, 1, 3], [1, 2, 3]), ([5, 5, 5], [5])], held)
check("uniques en ordre (dédup) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 19) FAMILLES (3) — casse (swapcase) ; booléens d'agrégat (doublons, tous-égaux : données DISCRIMINANTES vs
#     palindrome/coïncidences bool) ; découpe (paires glissantes, chunks). (sonde familles 3, 2026-06-23)
held = [("XyZ", "xYz"), ("a", "A")]
v = M.examine_cible("swapcase", "x", [("Hello", "hELLO"), ("aBc", "AbC")], held)
check("swapcase (casse) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([5, 5], True), ([1, 2, 3], False), ([7, 1], False)]
v = M.examine_cible("a_des_doublons", "x", [([1, 2, 2], True), ([1, 3], False), ([2, 2], True)], held)
check("a des doublons (bool, anti-coïncidence) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([5], True), ([1, 3], False), ([2, 2, 2], True)]
# NB : exemple discriminant [3, 2, 1]->False AJOUTÉ (2026-06-23) — sans lui, « tous égaux » est sous-déterminé
# (indistinguable de « non-croissant » : x[i] >= x[i+1], désormais au vocabulaire) -> l'engine répondait AMBIGU
# à juste titre. Avec l'exemple, seul len(set(x)) == 1 survit -> INVENTION. (tests = entraînement : on détermine la cible.)
v = M.examine_cible("tous_egaux", "x", [([3, 3, 3], True), ([1, 2, 1], False), ([5, 5], True), ([3, 2, 1], False)], held)
check("tous égaux (bool, discriminé du non-croissant) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([7, 8, 9, 0], [[7, 8], [8, 9], [9, 0]])]
v = M.examine_cible("paires_glissantes", "x", [([1, 2, 3], [[1, 2], [2, 3]]), ([4, 5], [[4, 5]])], held)
check("paires glissantes (découpe) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, 2, 3], [[1, 2], [3]]), ([9], [[9]])]
v = M.examine_cible("chunks_2", "x", [([1, 2, 3, 4], [[1, 2], [3, 4]]), ([5, 6], [[5, 6]])], held)
check("chunks de 2 (découpe) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 20) COMPOSITION 3-ÉTAPES (filtrer + transformer + agréger) — `etend_composition_filtree` (sonde dure 2026-06-23).
held = [([6, 1], 36), ([3, 3], 0), ([0, 2, 4], 20)]
v = M.examine_cible("somme_carres_pairs", "x", [([1, 2, 3, 4], 20), ([2, 5], 4)], held)
check("somme des carrés des pairs (3 étapes) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([2, 4], 1), ([1, 1, 7], 7)]
v = M.examine_cible("produit_impairs", "x", [([1, 2, 3], 3), ([3, 5], 15)], held)
check("produit des impairs (filtre+agrégat) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([2, 3], [4]), ([1, 1], [])]
# DÉTERMINANT (ajout nuit 2026-06-24) : exemple [4,2,3]->[16,4] où les carrés-pairs NE SONT PAS déjà triés.
# Sans lui, le spec est sous-déterminé (tous les exemples ont des evens déjà croissants) : la composition
# profonde (etend_composition_generale prof=2) propose AUSSI `sorted(pairs(carres(x)))` qui reproduit les
# données mais diverge sur l'ordre -> AMBIGU honnête (FAUX=0). Le moteur est devenu plus discriminant ; on
# DÉTERMINE le spec pour cibler l'ordre-d'origine. (Cf. feedback-resolution-coincidence-froid : held-out durci.)
v = M.examine_cible("carres_pairs", "x", [([1, 2, 3, 4], [4, 16]), ([5, 6], [36]), ([4, 2, 3], [16, 4])], held)
check("carrés des pairs (map filtré) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 21) MÉCANISME GÉNÉRATIF (2026-06-23, choix Yohan) — le moteur COMPOSE ses propres primitives g(f(x)) sans
#     schéma hardcodé : sorted∘abs_each, sum∘unique. Sound (gardes d'examine_cible inchangées). produit_cumulatif
#     reste BRIQUE_MANQUANTE (la frontière n'est pas franchie par cette composition bornée).
held = [([-5, 2], [2, 5]), ([0, -3], [0, 3])]
# DÉTERMINANT (nuit 2026-06-24) : [-2,2,1]->[1,2,2] avec |valeurs| RÉPÉTÉES. Sans lui, la composition profonde
# propose AUSSI `list(dict.fromkeys(sorted(abs)))` (dédup) qui reproduit les données sans doublon d'absolus ->
# AMBIGU honnête. On détermine « garder les doublons ». (Moteur plus discriminant, FAUX=0 préservé.)
v = M.examine_cible("abs_puis_trie", "x", [([-3, 1, -2], [1, 2, 3]), ([4, -1], [1, 4]), ([-2, 2, 1], [1, 2, 2])], held)
check("composition générative sorted∘abs -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([5, 5, 5], 5), ([1, 2, 3], 6)]
v = M.examine_cible("somme_uniques", "x", [([1, 1, 2], 3), ([3, 3], 3)], held)
check("composition générative sum∘unique -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 22) CONTRÔLE DE FLUX — arrêt anticipé (takewhile/early-stop), la frontière de contrôle (2026-06-23).
held = [([2, 0, -3, 9], 2), ([5, 5], 10)]
v = M.examine_cible("somme_jusqua_negatif", "x", [([1, 0, 2, -1, 5], 3), ([4, 4], 8), ([3, -9, 2], 3)], held)
check("somme jusqu'au 1er négatif (arrêt anticipé) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([1, -1, 1], [1]), ([7, 8, -3], [7, 8])]
v = M.examine_cible("prefixe_positif", "x", [([3, 1, -2, 9], [3, 1]), ([4, 5], [4, 5])], held)
check("préfixe positif (takewhile) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))

# 23) AUTO-SYNTHÈSE DE PRIMITIVES (2026-06-23) — l'engine SYNTHÉTISE une primitive en cherchant la constante dans
#     les données (seuil, pas, offset) ; reality-guarded (held-out) -> jamais de faux (le piège aléatoire reste
#     BRIQUE_MANQUANTE). Le cap de l'auto-évolution.
held = [([9, 7], 9), ([8, 8], 16)]
v = M.examine_cible("sum_gt_7", "x", [([10, 5, 12, 3], 22), ([8, 7], 8), ([1, 2], 0)], held)
check("auto-synthèse SEUIL (somme des >7) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([7, 1, 1, 8, 1, 1, 9], 24)]
v = M.examine_cible("stride_3", "x", [([1, 9, 9, 2, 9, 9, 3], 6), ([5, 0, 0, 4], 9)], held)
check("auto-synthèse PAS/STRIDE (range(0,len,3)) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
held = [([4, 4], [9, 9])]
v = M.examine_cible("plus_5", "x", [([1, 2, 3], [6, 7, 8]), ([0, 10], [5, 15])], held)
check("auto-synthèse OFFSET (map +5) -> INVENTION", v.statut == M.INVENTION and reproduit(v.par, held))
# SOUNDNESS : un piège sans fonction simple ne doit JAMAIS être synthétisé faux -> BRIQUE_MANQUANTE.
v = M.examine_cible("aleatoire_piege", "x", [([1, 2, 3], 7), ([4, 5], 2)], [([0, 0], 9), ([1, 1], 4)])
check("auto-synthèse SOUND : piège aléatoire -> BRIQUE_MANQUANTE (pas de faux)", v.statut == M.BRIQUE_MANQUANTE)

# 24) SOUNDNESS — fausse équivalence par sondes faibles (bug somme_uniques, débusqué par le test 100 passes) :
#     exemples SANS doublon (sum==sum_uniques) + held AVEC doublon -> le moteur NE DOIT PAS renvoyer EXISTE_DEJA=sum
#     (qui rate le held) ; il doit donner une INVENTION qui reproduit RÉELLEMENT le held.
held = [([1, -3, 1], -2), ([8, 3, 6], 17), ([2, 6, -4], 4)]
v = M.examine_cible("somme_uniques_piege", "x", [([-6, 11, 8], 13), ([6, 4, 5], 15), ([4, 2, 1], 7)], held)
check("pas de fausse équivalence (somme_uniques) : le par renvoyé reproduit le held",
      v.statut in (M.INVENTION, M.EXISTE_DEJA) and reproduit(v.par, held))

print(f"\nINVENTION_GAP VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
