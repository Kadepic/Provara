"""VALIDATION falsification.py (Vague 6). FAUX=0 : contre-exemple réel ; aucun trouvé -> 'non réfutée' (pas 'prouvée')."""
from __future__ import annotations
from falsification import refute, corrobore, resiste

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Hypothèse VRAIE sur l'espace : « tout entier de 0..99 au carré est >= 0 » -> pas de contre-exemple
check("hypothèse vraie : aucun contre-exemple (None)", refute(lambda x: x * x >= 0, range(100)) is None)
check("resiste() = True sur hypothèse vraie", resiste(lambda x: x * x >= 0, range(100)))

# Hypothèse FAUSSE : « tout entier est < 50 » -> contre-exemple = 50 (le premier)
ce = refute(lambda x: x < 50, range(100))
check("hypothèse fausse : contre-exemple trouvé", ce is not None)
check("contre-exemple = 50 (premier violant)", ce == 50)
check("le contre-exemple VIOLE réellement l'hypothèse", not (ce < 50))

# corrobore() est honnête : 'non réfutée', pas 'prouvée'
nr, ce2 = corrobore(lambda x: x % 2 == 0, [0, 2, 4, 6])
check("corrobore : non réfutée sur l'espace testé", nr and ce2 is None)
nr2, ce3 = corrobore(lambda x: x % 2 == 0, [0, 2, 3, 4])
check("corrobore : réfutée -> renvoie le contre-exemple (3)", not nr2 and ce3 == 3)

# Une hypothèse qui PLANTE sur un cas est réfutée par ce cas
check("hypothèse qui lève une exception -> réfutée par ce cas",
      refute(lambda x: 1 / x > 0, [1, 2, 0, 3]) == 0)

# Popper : ne jamais confondre corroboration et preuve (documenté) — resiste borné par l'espace
check("resiste ne teste QUE l'espace fourni (portée finie honnête)",
      resiste(lambda x: x < 1000, range(10)) and not resiste(lambda x: x < 1000, range(2000)))

print(f"\n=== valide_falsification : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
