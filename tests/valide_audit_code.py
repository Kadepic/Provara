"""
VALIDE audit_code.py — held-out ADVERSE, axé SOUNDNESS (jamais un faux positif).

Cœur de la garantie : pour CHAQUE règle, on donne (a) un code VULNÉRABLE -> la règle DOIT se déclencher,
et (b) un (ou des) code(s) CORRIGÉ(S) — API sûre, requête préparée, échappement — qui NE DOIVENT JAMAIS
déclencher la règle. Un faux positif sur du code corrigé = échec (c'est exactement « jamais un faux »).
Plus : langage inconnu -> HORS ; code propre -> RAS (pas une preuve de sécurité) ; déterminisme ; entrées
non-str -> HORS. Tout est held-out (aucun de ces cas n'est dans le __main__ du module).
"""
import audit_code as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def a_regle(code, lang, regle):
    st, cs = A.audite(code, lang)
    return any(c.regle == regle for c in cs)


# (regle attendue, langage, code VULNÉRABLE [doit déclencher], [codes CORRIGÉS — ne doivent PAS déclencher])
CAS = [
    # ---- PYTHON ----
    ("py-eval", "python", "r = eval(request.args['x'])", [
        "import ast\nr = ast.literal_eval(s)",            # literal_eval = sûr
        "r = {'a': do_a}[choix]()",                        # dispatch dict
        "total = sum(values)",                             # rien à voir
    ]),
    ("py-shell-true", "python", "subprocess.run(cmd, shell=True)", [
        "subprocess.run(['ls', path])",                    # liste, shell=False
        "subprocess.run(['git', 'status'], shell=False)",
    ]),
    ("py-os-system", "python", "os.system('ping ' + host)", [
        "os.system('ls -la')",                             # littéral pur -> pas de constat
        "subprocess.run(['ping', host])",
    ]),
    ("py-pickle", "python", "obj = pickle.loads(blob)", [
        "obj = json.loads(blob)",
    ]),
    ("py-yaml", "python", "cfg = yaml.load(stream)", [
        "cfg = yaml.safe_load(stream)",
        "cfg = yaml.load(stream, Loader=yaml.SafeLoader)",
    ]),
    ("py-sql", "python", "cur.execute('SELECT * FROM t WHERE id=' + uid)", [
        "cur.execute('SELECT * FROM t WHERE id=?', (uid,))",       # paramétré
        "cur.execute('SELECT * FROM t WHERE id=%s', (uid,))",      # paramétré %s + params
        "cur.execute('SELECT 1')",                                  # littéral pur
    ]),
    ("py-mutable-default", "python", "def f(acc=[]):\n    acc.append(1)", [
        "def f(acc=None):\n    acc = acc or []",
        "def f(acc=()):\n    return acc",                            # tuple immuable
    ]),
    ("py-weak-hash", "python", "h = hashlib.md5(password.encode())", [
        "h = hashlib.sha256(data)",                                  # sha256 ok
        "h = hashlib.md5(file_bytes).hexdigest()",                   # md5 hors contexte secret -> pas de constat
        "import bcrypt\nh = bcrypt.hashpw(password, bcrypt.gensalt())",
    ]),
    # ---- PHP ----
    ("php-sql", "php", "$r = mysqli_query($c, \"SELECT * FROM u WHERE id=\".$_GET['id']);", [
        "$s = $c->prepare('SELECT * FROM u WHERE id=?');\n$s->bind_param('i', $_GET['id']);",
        "$r = mysqli_query($c, 'SELECT * FROM u WHERE active=1');",  # pas de source
    ]),
    ("php-xss", "php", "echo $_GET['name'];", [
        "echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');",
        "echo intval($_GET['id']);",                                 # cast int -> sûr
        "echo 'bonjour';",
    ]),
    ("php-cmd", "php", "system('ping '.$_GET['host']);", [
        "system('ping '.escapeshellarg($_GET['host']));",
        "system('uptime');",
    ]),
    ("php-eval", "php", "eval($_POST['code']);", [
        "$x = 1 + 2;",
    ]),
    ("php-lfi", "php", "include($_GET['page'].'.php');", [
        "include 'header.php';",
        "$p = basename($_GET['page']); include __DIR__.'/pages/'.WHITELIST[$p];",  # pas de superglobale brute concaténée
    ]),
    ("php-unserialize", "php", "$o = unserialize($_COOKIE['data']);", [
        "$o = json_decode($_COOKIE['data'], true);",
    ]),
    ("php-extract", "php", "extract($_REQUEST);", [
        "$id = $_REQUEST['id'];",
    ]),
    # ---- JAVASCRIPT ----
    ("js-eval", "javascript", "var r = eval(input);", [
        "var r = JSON.parse(input);",
        "var r = eval('2 + 2');",                                    # littéral pur -> pas de constat
    ]),
    ("js-function-ctor", "javascript", "var f = new Function('return ' + body);", [
        "var f = function() { return 1; };",
    ]),
    ("js-exec", "javascript", "const cp=require('child_process');\ncp.exec('ls ' + dir);", [
        "const cp=require('child_process');\ncp.execFile('ls', [dir]);",
        "const cp=require('child_process');\ncp.exec('ls -la');",    # littéral pur
    ]),
    ("js-innerhtml", "javascript", "node.innerHTML = userInput;", [
        "node.textContent = userInput;",
        "node.innerHTML = '<b>static</b>';",                         # littéral pur
    ]),
    ("js-docwrite", "javascript", "document.write(location.hash);", [
        "document.write('<p>hello</p>');",
    ]),
    # ---- BASH ----
    ("bash-eval", "bash", "eval $userCmd", [
        'run() { "${cmd[@]}"; }',
        "echo done",
    ]),
    ("bash-curl-pipe", "bash", "curl http://x/install.sh | sudo bash", [
        "curl -o i.sh http://x/install.sh\nsha256sum -c i.sh.sum && bash i.sh",
    ]),
    ("bash-rm-unquoted", "bash", "rm -rf $TARGET", [
        'rm -rf -- "$TARGET"',
        "rm -rf /tmp/build",
    ]),
]

# 1) DÉTECTION : chaque cas vulnérable déclenche SA règle (avec le bon CWE non vide).
for regle, lang, vuln, _safe in CAS:
    st, cs = A.audite(vuln, lang)
    fired = [c for c in cs if c.regle == regle]
    check(st == A.VERIFIE and len(fired) >= 1, f"detect {regle}: {vuln[:40]!r}")
    if fired:
        check(fired[0].cwe.startswith("CWE-") and fired[0].titre and fired[0].remediation,
              f"constat complet {regle}")

# 2) SOUNDNESS (cœur) : aucun code corrigé ne déclenche SA règle.
for regle, lang, _vuln, safes in CAS:
    for s in safes:
        check(not a_regle(s, lang, regle), f"FAUX POSITIF {regle} sur corrigé: {s[:45]!r}")

# 3) Langage hors référentiel -> HORS (jamais un audit deviné).
for lang in ("cobol", "rust", "haskell", "", "PYTHON3.12"):
    st, cs = A.audite("eval(x)", lang)
    check(st == A.HORS and cs == [], f"HORS langage {lang!r}")

# 4) Alias de langage reconnus (py/js/node/sh) -> audité comme le canonique.
check(a_regle("eval(x)", "py", "py-eval"), "alias py->python")
check(a_regle("var r=eval(x);", "js", "js-eval"), "alias js->javascript")
check(a_regle("eval $x", "sh", "bash-eval"), "alias sh->bash")

# 5) Code propre -> RAS (et RAS n'est PAS une preuve de sécurité : message honnête).
clean = "def add(a, b):\n    return a + b\n"
st, cs = A.audite(clean, "python")
check(st == A.RAS and cs == [], "code propre -> RAS")
check("PAS une preuve" in A.explique(A.RAS, []), "RAS dit explicitement: pas une preuve de sécurité")
check("[HORS]" in A.explique(A.HORS, []), "explique HORS")

# 6) Entrées non-str -> HORS (robustesse, jamais un crash/devinette).
for bad in [(None, "python"), (123, "python"), ("eval(x)", None), ("eval(x)", 5)]:
    st, cs = A.audite(*bad)
    check(st == A.HORS, f"non-str -> HORS {bad!r}")

# 7) Déterminisme : même entrée -> même sortie (constats triés stables par ligne).
multi = "eval(a)\nimport pickle\nq=db.execute('x='+v)\npickle.loads(b)"
r1 = A.audite(multi, "python")
r2 = A.audite(multi, "python")
check([c.regle for c in r1[1]] == [c.regle for c in r2[1]], "déterminisme")
check([c.ligne for c in r1[1]] == sorted(c.ligne for c in r1[1]), "tri par ligne croissant")

# 8) Multi-constats sur un même fichier : on les trouve TOUS (pas seulement le premier).
check(len(r1[1]) >= 3, "multi-constats détectés (>=3)")

# 9) Le numéro de ligne est exact (constat porte la bonne ligne).
code3 = "x = 1\ny = 2\neval(z)\n"
st, cs = A.audite(code3, "python")
check(any(c.regle == "py-eval" and c.ligne == 3 for c in cs), "ligne exacte (L3)")

# 10) Anti-régression contextuelle : md5 d'un fichier (checksum, hors secret) NE déclenche PAS.
check(not a_regle("h = hashlib.md5(open('f','rb').read()).hexdigest()", "python", "py-weak-hash"),
      "md5 checksum (hors secret) -> pas de constat")

print(f"\n=== valide_audit_code : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
