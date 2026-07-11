"""
VALIDATION — MÉMOIRE DE BRIQUES MULTI-ARGUMENT (memoire_briques_multi) : self-improving binaire/ternaire.

forge_brique_multi découvrait une invention binaire/ternaire mais ne la RETENAIT pas. Ce store comble le
manque en préservant les garanties du mono (confiance zéro au disque, innocuité avant exécution, admission
gardée), ARITÉ-CONSCIENT.

Prouve : (1) SELF-IMPROVING via ia.forge_brique_multi — 1er passage invente+retient, 2e reconnaît EXISTE_DEJA
(recall, plus de re-dérivation) ; (2) CONFIANCE ZÉRO AU DISQUE — une brique altérée sur disque est RE-JUGÉE et
part en QUARANTAINE, jamais injectée ; (3) INNOCUITÉ — une expr hostile altérée en fichier est refusée AVANT
exécution (effet de bord jamais déclenché) ; (4) ADMISSION GARDÉE — retient() refuse une expr non sûre / qui
ne reproduit pas / au spec non sérialisable (refus compté) ; (5) SÉPARATION D'ARITÉ — une brique binaire n'est
JAMAIS servie à une cible ternaire ; (6) IDEMPOTENCE — re-retenir la même brique -> False (déjà connue).
"""
from __future__ import annotations

import json
import os
import tempfile

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import invention_multi as IM
from memoire_briques import VERSION, _spec_vers_texte
from memoire_briques_multi import MemoireBriquesMulti

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def P(f, pairs):
    return [((a, b), f(a, b)) for a, b in pairs]


PAIRS = [(3, 5), (7, 2), (4, 4), (9, 1), (2, 8), (6, 3)]
BASES = {2: IM.EXISTANT_BINAIRE, 3: IM.EXISTANT_TERNAIRE}


# ── (1) SELF-IMPROVING via ia.forge_brique_multi ─────────────────────────────────────────────────────────
ia._BRIQUES_MULTI = MemoireBriquesMulti(bases=BASES)     # store frais (pas de persistance disque)
ps = P(lambda a, b: a * a + b * b, PAIRS)
r1 = ia.forge_brique_multi("sc", ps[:4], ps[4:])
check("self-improving : 1er passage -> INVENTION retenue", r1["statut"] == IM.INVENTION and r1["appris"] is True)
r2 = ia.forge_brique_multi("sc_bis", ps[:4], ps[4:])
check("self-improving : 2e passage -> EXISTE_DEJA (reconnu, plus re-dérivé)",
      r2["statut"] == IM.EXISTE_DEJA and r2["appris"] is False)
ia._BRIQUES_MULTI = None                                  # ne pas fuir l'état vers d'autres tests

# ── (2)+(3) CONFIANCE ZÉRO AU DISQUE + INNOCUITÉ ─────────────────────────────────────────────────────────
d = tempfile.mkdtemp(prefix="bm_")
ch = os.path.join(d, "bm.json")
poc = os.path.join(tempfile.gettempdir(), "bm_poc.txt")
if os.path.exists(poc):
    os.remove(poc)
mem = MemoireBriquesMulti(chemin=ch, bases={2: IM.EXISTANT_BINAIRE})
check("retient : une invention binaire est admise", mem.retient(
    "a * a + b * b", origine="sc", params=["a", "b"], exemples=[((3, 5), 34), ((7, 2), 53)], held=[((4, 4), 32)]))
mem.sauve()
check("service : la brique retenue est servie pour son arité", "a * a + b * b" in mem.existant(2).values())
# altère l'expr sur disque en une expr HOSTILE qui reproduirait le spec
raw = json.load(open(ch, encoding="utf-8"))
list(raw["briques"].values())[0]["expr"] = f"(open({poc!r}, 'w').write('h'), a + b)[1]"
json.dump(raw, open(ch, "w", encoding="utf-8"))
mem2 = MemoireBriquesMulti(chemin=ch, bases={2: IM.EXISTANT_BINAIRE})
check("confiance zéro : la brique altérée hostile part en QUARANTAINE (0 apprise)",
      len(mem2) == 0 and any("non sûre" in q["raison"] for q in mem2.quarantaine))
check("innocuité : l'effet de bord n'a PAS été déclenché au chargement", not os.path.exists(poc))

# ── (4) ADMISSION GARDÉE ─────────────────────────────────────────────────────────────────────────────────
m = MemoireBriquesMulti(bases={2: IM.EXISTANT_BINAIRE})
poc2 = os.path.join(tempfile.gettempdir(), "bm_poc2.txt")
if os.path.exists(poc2):
    os.remove(poc2)
avant = m.refus_admission
check("admission : expr hostile REFUSÉE (avant exécution)", m.retient(
    f"(open({poc2!r}, 'w').write('h'), a + b)[1]", origine="mal", params=["a", "b"],
    exemples=[((1, 2), 3)], held=[((4, 5), 9)]) is False)
check("admission : l'effet de bord de l'expr refusée n'a PAS eu lieu", not os.path.exists(poc2))
# expr HORS registre (pas dédupliquée) et qui NE reproduit pas -> vrai refus compté
check("admission : expr hors registre qui NE reproduit pas est refusée",
      m.retient("a * a + b", origine="faux", params=["a", "b"], exemples=[((3, 5), 34)], held=[]) is False)
check("admission : les refus sont comptés", m.refus_admission >= avant + 2)

# ── (5) SÉPARATION D'ARITÉ ───────────────────────────────────────────────────────────────────────────────
ma = MemoireBriquesMulti(bases=BASES)
ma.retient("a * a + b * b", origine="sc2", params=["a", "b"], exemples=[((3, 5), 34)], held=[((7, 2), 53)])
check("séparation : la brique binaire est servie à l'arité 2", "a * a + b * b" in ma.existant(2).values())
check("séparation : la brique binaire n'est JAMAIS servie à l'arité 3", "a * a + b * b" not in ma.existant(3).values())

# ── (6) IDEMPOTENCE ──────────────────────────────────────────────────────────────────────────────────────
check("idempotence : re-retenir la même brique -> False (déjà connue)",
      ma.retient("a * a + b * b", origine="sc3", params=["a", "b"], exemples=[((3, 5), 34)], held=[((7, 2), 53)]) is False)

# ── (7) ARGS STRUCTURÉS (palier structurel, atome 24) ───────────────────────────────────────────────────
# Une brique à arguments STRUCTURÉS (dicts à clés str) survit au cycle complet retient -> sauve -> charge
# RE-JUGÉ (confiance zéro) ; un spec à clés ENTIÈRES (que JSON mangerait en str) est REFUSÉ à l'admission —
# « son spec survit au disque » mord réellement, jamais un spec injugeable demain.
with tempfile.TemporaryDirectory() as _d7:
    _c7 = os.path.join(_d7, "briques_multi.json")
    m7 = MemoireBriquesMulti(chemin=_c7, bases={2: IM.EXISTANT_BINAIRE})
    _ex7 = [((dict(a), dict(b)), {k: v for k, v in a.items() if k not in b})
            for a, b in [({"a": 1, "b": 2}, {"b": 9}), ({"x": 5}, {"y": 1}), ({"m": 4, "n": 6}, {"n": 0})]]
    check("args structurés : brique dict×dict (clés str) RETENUE",
          m7.retient("{_k: _v for _k, _v in a.items() if _k not in b}", origine="soustraction_dict",
                     params=["a", "b"], exemples=_ex7[:2], held=_ex7[2:]) is True)
    _ex7i = [((dict(a), dict(b)), {k: v for k, v in a.items() if k not in b})
             for a, b in [({1: 10, 2: 20}, {2: 0}), ({3: 5}, {4: 1}), ({5: 4, 6: 6}, {6: 0})]]
    check("args structurés : spec à clés ENTIÈRES refusé honnêtement (ne survivrait pas au disque)",
          m7.retient("{_k: _v for _k, _v in a.items() if _k not in b}", origine="soustraction_dict_int",
                     params=["a", "b"], exemples=_ex7i[:2], held=_ex7i[2:]) is False)
    m7.sauve()
    m7b = MemoireBriquesMulti(chemin=_c7, bases={2: IM.EXISTANT_BINAIRE})
    check("args structurés : la brique survit à sauve -> charge RE-JUGÉ et est servie",
          "soustraction_dict" in m7b.existant(2) and not m7b.quarantaine)

print(f"\n== VALIDE_MEMOIRE_MULTI : {ok}/{total} ==")
assert ok == total
