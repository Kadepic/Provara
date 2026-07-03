"""
GÉNÉRATION MULTI-LANGAGE (2026-06-17, choix Yohan « génération multi-langage ») — l'IA n'écrit plus seulement du
Python : elle ÉCRIT une solution dans un AUTRE langage (JS/Perl/Bash) et la fait VÉRIFIER par le juge polyglotte.

Module SÉPARÉ (vertical+modulaire) : ne touche pas l'orchestrateur Python. Famille BORNÉE et HONNÊTE = opérations
BINAIRES SCALAIRES (arithmétique + bit-à-bit + max/min), rendues dans la syntaxe de chaque langage. Le juge tranche
par l'exemple. Étendre = plus de familles par-langage (lourd) ou le modèle (fork) — `demande_lang` rend HORS, jamais
du faux, hors de sa famille.
"""

from __future__ import annotations

import dataclasses
import re

from executeur import EXECUTEURS
from juge import Limites, juge

LIM = Limites(temps_s=5, cpu_s=4, memoire_mo=4096)   # généreux (V8 réserve de la mémoire virtuelle)


class GenerateurPolyglotte:
    """Famille bornée d'opérations binaires scalaires `f(a, b)`, rendue dans le langage cible (JS/Perl/Bash)."""

    # Corps de la famille : {a}/{b} = accès aux 2 arguments dans CE langage.
    FAMILLES = {
        "javascript": ["{a} + {b}", "{a} - {b}", "{a} * {b}", "{a} % {b}",
                       "{a} & {b}", "{a} | {b}", "{a} ^ {b}", "Math.max({a},{b})", "Math.min({a},{b})"],
        "perl": ["{a} + {b}", "{a} - {b}", "{a} * {b}", "{a} % {b}",
                 "{a} & {b}", "{a} | {b}", "{a} ^ {b}", "({a} > {b} ? {a} : {b})", "({a} < {b} ? {a} : {b})"],
        "bash": ["$(( {a} + {b} ))", "$(( {a} - {b} ))", "$(( {a} * {b} ))", "$(( {a} % {b} ))",
                 "$(( {a} & {b} ))", "$(( {a} | {b} ))", "$(( {a} ^ {b} ))",
                 "$(( {a} > {b} ? {a} : {b} ))", "$(( {a} < {b} ? {a} : {b} ))"],
    }
    ACCES = {"javascript": ("a", "b"), "perl": ("$_[0]", "$_[1]"), "bash": ("$1", "$2")}
    WRAP = {
        "javascript": "function {g}(a, b) {{ return {corps}; }}",
        "perl": "sub {g} {{ return {corps}; }}",
        "bash": "{g}() {{ echo {corps}; }}",
    }

    def __init__(self, langage: str, seed: int = 0):
        self._langage = langage
        self._seed = seed

    def propose(self, point_entree: str) -> list[str]:
        a, b = self.ACCES[self._langage]
        wrap = self.WRAP[self._langage]
        return [wrap.format(g=point_entree, corps=corps.format(a=a, b=b)) for corps in self.FAMILLES[self._langage]]


def _tests_lang(g: str, langage: str, exemples) -> str:
    """Construit les tests dans la syntaxe du langage à partir des exemples [(a, b, attendu)]."""
    if langage == "javascript":
        lignes = ["const assert=require('assert');"]
        lignes += [f"assert.strictEqual({g}({a},{b}), {exp});" for a, b, exp in exemples]
        return "\n".join(lignes)
    if langage == "perl":
        return "\n".join(f'die "AssertionError\\n" unless {g}({a},{b})=={exp};' for a, b, exp in exemples)
    if langage == "bash":
        return "\n".join(f'[ "$({g} {a} {b})" = "{exp}" ] || {{ echo AssertionError >&2; exit 1; }}'
                         for a, b, exp in exemples)
    raise ValueError(langage)


@dataclasses.dataclass
class ReponseLang:
    ok: bool
    code: str | None
    langage: str
    generalise: bool

    def __str__(self) -> str:
        if not self.ok:
            return f"<HORS ({self.langage}) — aucun code vérifié>"
        g = "généralise" if self.generalise else "visibles seulement"
        return f"<RÉSOLU en {self.langage} ({g})>\n{self.code}"


def demande_lang(point_entree: str, exemples, langage: str, exemples_held=None) -> ReponseLang:
    """DEMANDE de code dans `langage` (JS/Perl/Bash). `exemples`/`exemples_held` = [(a, b, attendu), ...] (binaire
    scalaire). Rend la 1ʳᵉ solution du langage qui passe les exemples (et le held-out s'il est donné), ou HORS."""
    gen = GenerateurPolyglotte(langage)
    ex = EXECUTEURS[langage]
    vis = _tests_lang(point_entree, langage, exemples)
    held = _tests_lang(point_entree, langage, exemples_held) if exemples_held else ""
    for code in gen.propose(point_entree):
        if juge(code, vis, LIM, executeur=ex).passe and (not held or juge(code, held, LIM, executeur=ex).passe):
            return ReponseLang(True, code, langage, bool(held))
    return ReponseLang(False, None, langage, False)


if __name__ == "__main__":
    import shutil
    print("=== DÉMO — l'IA écrit du code dans plusieurs langages (vérifié par l'exemple) ===\n")
    runtime = {"javascript": "node", "perl": "perl", "bash": "bash"}
    for lang in ("javascript", "perl", "bash"):
        if not shutil.which(runtime[lang]):
            print(f"# {lang}: runtime absent -> sauté\n")
            continue
        # addition
        r = demande_lang("add", [(2, 3, 5), (10, 1, 11)], lang, [(0, 0, 0), (7, 8, 15)])
        print(f"# {lang} — add :\n{r}\n")
        # XOR binaire
        r = demande_lang("bit_xor", [(5, 3, 6), (12, 10, 6)], lang, [(7, 1, 6), (255, 128, 127)])
        print(f"# {lang} — bit_xor :\n{r}\n")
