"""VALIDE veille.py — accès web souverain, FAUX=0. OFFLINE (transport injecté, aucun réseau).

Vérifie : (1) récupération + dégradation gracieuse (toute erreur -> HORS, jamais d'exception/fabrication) ;
(2) typage RAPPORTÉ (toute info web = SUPPOSITION régime rapporté, jamais un fait) ; (3) INDÉPENDANCE (domaine
distinct ET contenu non recopié) ; (4) CORROBORATION -> FAIT SEULEMENT si >= minimum sources indépendantes ET
juge réel positif (jamais l'un sans l'autre) ; (5) approfondit rend des suppositions, jamais des faits."""
import atome as A
import veille as V

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def fake(url, timeout=15):
    return (200, b"contenu de test au sujet demande")


def fake_autre(url, timeout=15):
    return (200, b"un contenu totalement different sur le meme sujet")


def boom(url, timeout=15):
    raise OSError("pas de reseau")


def http404(url, timeout=15):
    return (404, b"not found")


def oversize(url, timeout=15):
    return (200, b"x" * (V._TAILLE_MAX + 10))


# ── 1) récupération + dégradation gracieuse ──
st, txt, meta = V.recupere("https://exemple.org/p", transport=fake)
check(st == V.OK and "test" in txt and meta["domaine"] == "exemple.org" and "empreinte" in meta, "recupere OK + méta")
check(V.recupere("ftp://x/y", transport=fake)[0] == V.HORS, "schéma non http(s) -> HORS")
check(V.recupere("", transport=fake)[0] == V.HORS, "URL vide -> HORS")
check(V.recupere(None, transport=fake)[0] == V.HORS, "URL None -> HORS")
check(V.recupere("https://x/y", transport=boom)[0] == V.HORS, "réseau KO -> HORS (gracieux)")
check(V.recupere("https://x/y", transport=http404)[0] == V.HORS, "HTTP 404 -> HORS")
check(V.recupere("https://x/y", transport=oversize)[0] == V.HORS, "réponse oversize -> HORS (bornée)")
check(V.recupere("https://www.a.org/x", transport=fake)[2]["domaine"] == "a.org", "domaine normalisé (www. retiré)")

# ── 2) typage RAPPORTÉ ──
r = V.rapporte("le pib de x est y", "https://source.org/a")
check(r.statut == A.SUPPOSITION and r.regime == A.RAPPORTE, "info web -> SUPPOSITION régime RAPPORTÉ")
check(0.0 < r.confiance < 1.0, "confiance rapportée dans ]0,1[")
check("source.org" in r.preuve or "source.org" in r.portee.condition, "provenance conservée")
check(leve(V.rapporte, "", "https://a.org"), "énoncé vide -> ValueError")

# ── 3) INDÉPENDANCE ──
T = V.Temoignage
tem = [T("https://a.org/1", "a.org", "X", "h1"),
       T("https://a.org/2", "a.org", "X", "h2"),   # même domaine -> non indépendant
       T("https://b.org/1", "b.org", "X", "h3"),
       T("https://c.org/1", "c.org", "X", "h3")]    # contenu recopié (h3) -> non indépendant
ind = V.independantes(tem)
check([t.domaine for t in ind] == ["a.org", "b.org"], f"indépendance : domaine unique + anti-recopie ({[t.domaine for t in ind]})")

# ── 4) CORROBORATION : FAIT seulement si (>= min indep) ET (juge réel positif) ──
juge_ok = lambda e, ts: A.Verdict("test-juge", True, "vérifié sur sources indépendantes")
juge_non = lambda e, ts: A.Verdict("test-juge", False, "non confirmé après vérification")
check(V.corrobore("X", tem).statut == A.SUPPOSITION, "corroboration sans juge -> reste SUPPOSITION")
check(V.corrobore("X", tem, minimum=2, juge=juge_ok).statut == A.FAIT, "2 indép + juge positif -> FAIT")
check(V.corrobore("X", tem, minimum=2, juge=juge_non).statut == A.SUPPOSITION, "juge négatif -> reste SUPPOSITION")
check(V.corrobore("X", [tem[0]], minimum=2, juge=juge_ok).statut == A.SUPPOSITION, "1 seule source + juge -> PAS un fait")
# 3 sources qui se recopient (même empreinte) ne comptent pas comme corroboration
recopies = [T("https://a.org/1", "a.org", "X", "hh"), T("https://b.org/1", "b.org", "X", "hh"),
            T("https://c.org/1", "c.org", "X", "hh")]
check(V.corrobore("X", recopies, minimum=2, juge=juge_ok).statut == A.SUPPOSITION,
      "sources qui se recopient (même contenu) -> PAS de corroboration -> pas un fait")
check(0.0 < V.corrobore("X", tem).confiance < 1.0, "confiance d'une corroboration non promue reste dans ]0,1[")

# ── 5) approfondit : suppositions, jamais des faits ; dégradation gracieuse ──
res = V.approfondit("sujet Z", urls=["https://a.org/x", "https://b.org/y"], transport=fake)
check(res["statut"] == V.OK and len(res["temoignages"]) == 2, "approfondit récupère les témoignages")
check(all(at.statut == A.SUPPOSITION and at.regime == A.RAPPORTE for at in res["atomes"]),
      "approfondit ne rend que des SUPPOSITIONS rapportées (jamais un fait)")
check(V.approfondit("sujet Z", urls=["https://a.org/x"], transport=boom)["statut"] == V.HORS,
      "approfondit sans réseau -> HORS (gracieux)")
check(V.approfondit("", urls=["https://a.org/x"], transport=fake)["statut"] == V.HORS, "sujet vide -> HORS")

# ── déterminisme ──
check(V.recupere("https://a.org/x", transport=fake)[2]["empreinte"] == V.recupere("https://a.org/x", transport=fake)[2]["empreinte"],
      "empreinte déterministe")

print(f"\n=== valide_veille : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
