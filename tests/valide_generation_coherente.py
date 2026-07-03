"""GÉNÉRATION COHÉRENTE — l'IA produit des phrases complètes TOTALEMENT cohérentes (grammaire + sémantique + ré-analyse).
COHÉRENTE : phrases bien formées et livrées. SÉMANTIQUE : sujet incompatible avec le verbe -> REFUSÉ. RÉ-ANALYSE :
génération ∘ compréhension = identité. HELD-OUT : sens jamais vu -> phrase cohérente produite."""
from __future__ import annotations

from generation_coherente import Ecrivain


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    ec = Ecrivain()
    r = []

    p1, c1, _ = ec.ecris("chat", "manger", "souris")
    p2, c2, _ = ec.ecris("chien", "chasser", "chat")
    r.append(_check(f"COHÉRENTE : « {p1} » et « {p2} » produites et cohérentes",
                    c1 and p1 == "le chat mange la souris" and c2 and p2 == "le chien chasse le chat"))

    pv, cv, raison = ec.ecris("voiture", "manger", "souris")
    r.append(_check(f"SÉMANTIQUE : « voiture manger » REFUSÉ ({raison})", not cv and pv is None))

    # RÉ-ANALYSE : la phrase cohérente se relit en son sens (sinon ecris() l'aurait rejetée).
    p3, c3, _ = ec.ecris("lion", "voir", "souris")
    r.append(_check(f"RÉ-ANALYSE : « {p3} » cohérente (génération ∘ compréhension = identité)",
                    c3 and p3 == "le lion voit la souris"))

    # HELD-OUT : sens jamais vu en démo.
    ph, ch, _ = ec.ecris("tigre", "chasser", "chien")
    r.append(_check(f"HELD-OUT : « {ph} » (sens neuf) cohérente", ch and ph == "le tigre chasse le chien"))

    # FUSION (sans brique superflue) : adjectif accordé + négation, cohérence ré-analysée.
    pa, ca, _ = ec.ecris_riche("chat", "manger", "souris", adjectif="petit")
    r.append(_check(f"FUSION adjectif : « {pa} »", ca and pa == "le petit chat mange la souris"))

    pf, cf, _ = ec.ecris_riche("souris", "voir", "chat", adjectif="petit")
    r.append(_check(f"FUSION accord féminin : « {pf} » (petit→petite)", cf and pf == "la petite souris voit le chat"))

    pn, cn, _ = ec.ecris_riche("chat", "manger", "souris", negatif=True)
    r.append(_check(f"FUSION négation : « {pn} »", cn and pn == "le chat ne mange pas la souris"))

    pc, cc, _ = ec.ecris_riche("chien", "chasser", "chat", adjectif="grand", negatif=True)
    r.append(_check(f"FUSION adjectif+négation : « {pc} »", cc and pc == "le grand chien ne chasse pas le chat"))

    pp, cp, _ = ec.ecris_pluriel("chat", "manger", "souris")
    r.append(_check(f"FUSION pluriel : « {pp} » (noms + verbe accordés)", cp and pp == "les chats mangent les souris"))

    pl, cl, _ = ec.ecris_pluriel("lion", "chasser", "chien")
    r.append(_check(f"FUSION pluriel held-out : « {pl} »", cl and pl == "les lions chassent les chiens"))

    pq, cq, _ = ec.demande("chat", "manger", "souris")
    r.append(_check(f"FUSION interrogative : « {pq} »", cq and pq == "le chat mange-t-il la souris ?"))

    pd, cd, _ = ec.raconte("chat", "manger", "souris", "chanter")
    r.append(_check(f"FUSION discours (coréférence) : « {pd} »",
                    cd and pd == "le chat mange la souris. il chante."))

    # cohérence du discours : pronom AMBIGU (objet de même genre que le sujet) -> REFUSÉ.
    pamb, camb, _ = ec.raconte("chat", "chasser", "chien", "chanter")
    r.append(_check("DISCOURS HONNÊTE : « chat … chien. il … » REFUSÉ (coréférence ambiguë, 2 masculins)",
                    not camb and pamb is None))

    print()
    print(f"GÉNÉRATION COHÉRENTE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
