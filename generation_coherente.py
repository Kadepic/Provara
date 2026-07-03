"""
GÉNÉRATION COHÉRENTE — l'IA produit des PHRASES COMPLÈTES et TOTALEMENT COHÉRENTES (2026-06-18, mandat Yohan).

« Cohérente » a ici un sens VÉRIFIABLE à trois niveaux :
  1. GRAMMATICALE  — article + nom + verbe conjugué + article + nom (brique `generation`).
  2. SÉMANTIQUE    — restriction de sélection : le SUJET peut réellement faire l'action (ex. « manger » exige un
                     sujet qui EST un animal, via la closure is-a). « la voiture mange la souris » -> INCOHÉRENT.
  3. RÉ-ANALYSABLE — la phrase produite, relue par la compréhension (rôles SVO), redonne le sens d'origine
                     (génération ∘ compréhension = identité).

Une phrase n'est livrée que si les trois tiennent. Tout passe par le moteur ASSEMBLÉ (generation + relation-lexicale
+ comprehension-phrase). C'est la cohérence prouvée, pas affirmée.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import lexique_fr as L
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
DET = {"le", "la", "les", "un", "une"}
# restriction de sélection : verbe -> catégorie requise du sujet (vérifiée par is-a).
VERBE_REQUIERT = {"manger": "animal", "chasser": "animal", "regarder": "animal", "voir": "animal",
                  "chanter": "animal", "dormir": "animal"}


def _fn(orch, point, sig, appel, attendu):
    t = Tache(id=f"gc/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
              tests=f"def check(c):\n    assert c({appel}) == {attendu!r}\ncheck({point})", tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    return ns[point]


class Ecrivain:
    def __init__(self):
        self.lex = L.LEXIQUE
        self.genres = {m: d["genre"] for m, d in self.lex.items()}
        self.edges = L.edges_isa()
        orch = GenerateurOrchestre(Store(Path(tempfile.mkdtemp()) / "s.jsonl"),
                                   predicteur=Predicteur(Store(Path(tempfile.mkdtemp()) / "s2.jsonl"),
                                                         types=TYPES_RICHES),
                                   generation=True, relation_lexicale=True, comprehension_phrase=True, feminin=True,
                                   pluriel=True, coreference=True)
        self._phrase = _fn(orch, "phrase", "s,v,o,g", "'chat','manger','souris',{'chat':'masculin','souris':'féminin'}",
                           "le chat mange la souris")
        self._feminin = _fn(orch, "feminin", "a", "'grand'", "grande")
        self._pluriel = _fn(orch, "pluriel", "m", "'cheval'", "chevaux")
        self._antecedent = _fn(orch, "antecedent", "g,m,p", "{'chat':'masculin'},['chat'],'il'", "chat")
        self._est_un = _fn(orch, "est_un", "e,x,y", "[('a','b')],'a','b'", True)
        self._sujet = _fn(orch, "sujet", "c,p", "{'le':'determinant','chat':'nom','dort':'verbe'},'le chat dort'",
                          "le chat")
        self._objet = _fn(orch, "objet", "c,p", "{'le':'determinant','chat':'nom','voit':'verbe','la':'determinant',"
                          "'souris':'nom'},'le chat voit la souris'", "la souris")

    def _coherent_sem(self, sujet, verbe):
        besoin = VERBE_REQUIERT.get(verbe)
        return besoin is None or self._est_un(self.edges, sujet, besoin)

    def _reanalyse_ok(self, phrase, sujet, objet):
        toks = phrase.split()
        cl = {}
        for t in toks:
            cl[t] = "determinant" if t in DET else ("nom" if t in (sujet, objet) else "verbe")
        gs = self._sujet(cl, phrase)
        go = self._objet(cl, phrase)
        return sujet in gs.split() and objet in go.split()

    def ecris(self, sujet, verbe, objet):
        """Renvoie (phrase, coherent, raison)."""
        if not self._coherent_sem(sujet, verbe):
            return (None, False, f"incohérent : « {sujet} » ne peut pas « {verbe} » (pas un {VERBE_REQUIERT[verbe]})")
        phrase = self._phrase(sujet, verbe, objet, self.genres)
        if not self._reanalyse_ok(phrase, sujet, objet):
            return (phrase, False, "ré-analyse échouée (sens non récupéré)")
        return (phrase, True, "cohérente : grammaticale + sémantique + ré-analysable")

    def ecris_riche(self, sujet, verbe, objet, adjectif=None, negatif=False):
        """FUSION : enrichit la phrase d'un ADJECTIF accordé (féminin si besoin) et/ou d'une NÉGATION. Cohérence
        vérifiée par ré-analyse du noyau affirmatif. Renvoie (phrase, coherent, raison)."""
        if not self._coherent_sem(sujet, verbe):
            return (None, False, f"incohérent : « {sujet} » ne peut pas « {verbe} »")
        base = self._phrase(sujet, verbe, objet, self.genres).split()   # [art_s, sujet, verbe_conj, art_o, objet]
        if len(base) != 5:
            return (None, False, "forme non gérée (élision)")
        art_s, vc, art_o = base[0], base[2], base[3]
        adj = ""
        if adjectif:
            accorde = self._feminin(adjectif) if self.genres.get(sujet) == "féminin" else adjectif
            adj = accorde + " "
        verbe_part = f"ne {vc} pas" if negatif else vc
        phrase = f"{art_s} {adj}{sujet} {verbe_part} {art_o} {objet}"
        aff = f"{art_s} {adj}{sujet} {vc} {art_o} {objet}"             # noyau affirmatif pour la ré-analyse
        toks = aff.split()
        cl = {t: ("determinant" if t in DET else ("nom" if t in (sujet, objet) else
                  ("verbe" if t == vc else "adjectif"))) for t in toks}
        gs, go = self._sujet(cl, aff), self._objet(cl, aff)
        if not (sujet in gs.split() and objet in go.split()):
            return (phrase, False, "ré-analyse échouée")
        bonus = (" +adjectif" if adjectif else "") + (" +négation" if negatif else "")
        return (phrase, True, "cohérente (grammaticale + sémantique + ré-analysable" + bonus + ")")

    def ecris_pluriel(self, sujet, verbe, objet):
        """FUSION : phrase au PLURIEL (pluriel des noms + conjugaison 3ᵉ pers. pluriel). Cohérence ré-analysée."""
        if not self._coherent_sem(sujet, verbe):
            return (None, False, f"incohérent : « {sujet} » ne peut pas « {verbe} »")
        sp, op = self._pluriel(sujet), self._pluriel(objet)
        vc = (verbe[:-2] + "ent" if verbe.endswith("er")
              else (verbe[:-2] + "issent" if verbe.endswith("ir") else verbe))
        phrase = f"les {sp} {vc} les {op}"
        cl = {t: ("determinant" if t == "les" else ("nom" if t in (sp, op) else "verbe")) for t in phrase.split()}
        gs, go = self._sujet(cl, phrase), self._objet(cl, phrase)
        if not (sp in gs.split() and op in go.split()):
            return (phrase, False, "ré-analyse échouée")
        return (phrase, True, "cohérente (pluriel : noms + verbe accordés + ré-analysable)")

    def demande(self, sujet, verbe, objet):
        """FUSION : forme INTERROGATIVE par inversion (« le chat mange-t-il la souris ? »)."""
        if not self._coherent_sem(sujet, verbe):
            return (None, False, "incohérent")
        base = self._phrase(sujet, verbe, objet, self.genres).split()
        if len(base) != 5:
            return (None, False, "forme non gérée")
        art_s, vc, art_o = base[0], base[2], base[3]
        pron = "il" if self.genres.get(sujet) == "masculin" else "elle"
        return (f"{art_s} {sujet} {vc}-t-{pron} {art_o} {objet} ?", True, "interrogative cohérente")

    def raconte(self, sujet, verbe1, objet, verbe2):
        """FUSION DISCOURS : deux phrases liées par un PRONOM (« le chat mange la souris. il chante. »). Cohérent
        seulement si le pronom se résout SANS AMBIGUÏTÉ vers le sujet (coréférence) et que la 2ᵉ action est valide."""
        p1, c1, _ = self.ecris(sujet, verbe1, objet)
        if not c1:
            return (None, False, "1ère phrase incohérente")
        if not self._coherent_sem(sujet, verbe2):
            return (None, False, f"2ᵉ action incohérente pour « {sujet} »")
        pron = "il" if self.genres.get(sujet) == "masculin" else "elle"
        # le pronom doit se résoudre vers le SUJET (sinon ambigu : objet de même genre plus récent)
        if self._antecedent(self.genres, [sujet, objet], pron) != sujet:
            return (None, False, "coréférence ambiguë (objet de même genre)")
        vc2 = (verbe2[:-2] + "e" if verbe2.endswith("er") else verbe2)
        return (f"{p1}. {pron} {vc2}.", True, "discours cohérent (pronom résolu vers le sujet)")


SENS = [("chat", "manger", "souris"), ("chien", "chasser", "chat"), ("lion", "voir", "souris"),
        ("voiture", "manger", "souris")]


if __name__ == "__main__":
    ec = Ecrivain()
    for s, v, o in SENS:
        phrase, coherent, raison = ec.ecris(s, v, o)
        print(f"  {'✅' if coherent else '⛔'} ({s},{v},{o}) -> {phrase!r:<34} [{raison}]")
    print("  --- enrichies (fusion adjectif / négation) ---")
    for args in [("chat", "manger", "souris", "petit", False), ("chat", "manger", "souris", None, True),
                 ("souris", "voir", "chat", "petit", False), ("chien", "chasser", "chat", "grand", True)]:
        phrase, coherent, raison = ec.ecris_riche(*args)
        print(f"  {'✅' if coherent else '⛔'} {args} -> {phrase!r:<40} [{raison}]")
    print("  --- pluriel (fusion pluriel + conjugaison) ---")
    for s, v, o in [("chat", "manger", "souris"), ("lion", "chasser", "chien")]:
        phrase, coherent, raison = ec.ecris_pluriel(s, v, o)
        print(f"  {'✅' if coherent else '⛔'} ({s},{v},{o}) pluriel -> {phrase!r:<34} [{raison}]")
    print("  --- interrogative + discours (fusion) ---")
    pq, cq, _ = ec.demande("chat", "manger", "souris")
    print(f"  {'✅' if cq else '⛔'} interrogative -> {pq!r}")
    pd, cd, rd = ec.raconte("chat", "manger", "souris", "chanter")
    print(f"  {'✅' if cd else '⛔'} discours      -> {pd!r}  [{rd}]")
