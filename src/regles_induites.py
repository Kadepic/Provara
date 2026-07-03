"""
PONT INDUCTION → DÉDUCTION — les règles VALIDÉES par induction_horn deviennent des clauses Datalog (2026-07-02).

POURQUOI : `induction_horn.py` PRODUIT des règles structurelles validées mais rien ne les consommait ;
`deduction.py` (Datalog) CONSOMME des règles mais rien ne les produisait. Ce pont ferme la boucle
apprentissage→raisonnement : la machine apprend une régularité, la valide contre des exemples, puis RAISONNE avec.

FAUX=0 — la ligne rouge du pont (durcie par attaque adversariale exécutée, 2026-07-02) :
  • Seules les règles VALIDÉES (consistantes AU POINT FIXE, support>0, réfutables = négatifs fournis) entrent au
    Datalog. Les rejetées et les non_refutables n'entrent JAMAIS (monde ouvert : pas de négatifs -> pas d'adoption).
    Un re-branchement DÉBRANCHE d'abord les règles induites précédentes de la relation (pas de règle fantôme).
  • Un fait dont la dérivation DÉPEND d'une règle induite est INCERTAIN (une généralisation), jamais « verifie ».
    La certitude exige une justification 100 % base + règles certaines (marche ITÉRATIVE de la provenance).
  • Les négatifs déclarés sont PERSISTÉS comme gardes : un fait déclaré faux est servi 'refute' pour toujours,
    même si une généralisation induite le dérive après de nouveaux faits ; s'il devient certain-dérivable c'est
    une contradiction réelle -> ValueError (jamais arbitrée en silence).
  • Noms réservés gardés : 'base' (sentinel de provenance, refusé à la racine par deduction) et 'induit:*'
    (refusé pour une règle certaine) — la contamination ne peut pas être maquillée par une collision de nom.
  • Conservateur : si la justification ENREGISTRÉE passe par une règle induite, le fait est dit incertain même
    s'il existait un autre chemin certain (sous-revendiquer = sûr ; l'inverse serait un FAUX+).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import deduction
import induction_horn

VERIFIE = "verifie"
INCERTAIN = "incertain"
REFUTE = "refute"          # fait DÉCLARÉ faux par les exemples négatifs — jamais servi comme dérivable
HORS = "hors"
PREFIXE_INDUIT = "induit:"


def clauses_datalog(type_regle: str, rel: str) -> list:
    """Clauses Datalog (tete, corps) équivalentes à une règle structurelle d'induction_horn sur `rel`."""
    if type_regle == induction_horn.TRANSITIVITE:
        return [((rel, "X", "Z"), [(rel, "X", "Y"), (rel, "Y", "Z")])]
    if type_regle == induction_horn.SYMETRIE:
        return [((rel, "Y", "X"), [(rel, "X", "Y")])]
    if type_regle == induction_horn.REFLEXIVITE:
        # R(x,x) pour tout x apparaissant à GAUCHE ou à DROITE (même sémantique que induction_horn.derive)
        return [((rel, "X", "X"), [(rel, "X", "Y")]),
                ((rel, "Y", "Y"), [(rel, "X", "Y")])]
    raise ValueError(f"règle inconnue : {type_regle}")


class MoteurInduit:
    """MoteurDeduction dont une partie des règles est INDUITE : `statut()` distingue verifie/incertain/hors.
    Le Datalog sous-jacent reste sound ; l'étiquette INCERTAIN empêche de servir une généralisation comme un fait."""

    def __init__(self):
        self.moteur = deduction.MoteurDeduction()
        self.induites: set[str] = set()          # noms des règles venues de l'induction
        self.negatifs: dict[str, set] = {}       # rel -> couples DÉCLARÉS faux (gardes PERSISTANTES, cf. statut)

    # — construction (invalide la matérialisation à chaque mutation) —
    def ajoute_fait(self, rel, x, y, source="donné"):
        if (x, y) in self.negatifs.get(rel, ()):
            raise ValueError(f"contradiction : ({rel!r}, {x!r}, {y!r}) a été déclaré NÉGATIF (exemple faux)")
        self.moteur.ajoute_fait(rel, x, y, source)

    def ajoute_regle_certaine(self, tete, corps, nom=""):
        """Règle écrite/vérifiée PAR AILLEURS : ses dérivations restent VERIFIE. Le nom 'base' (sentinel de
        provenance) est refusé à la racine par deduction ; le préfixe des règles induites l'est ici (une règle
        se déclarant 'induit:…' fausserait le suivi de contamination dans l'autre sens — sous-revendication).
        ⚠ convention deduction : un terme Capitalisé est une VARIABLE — pas de constante majuscule dans une règle."""
        if str(nom).startswith(PREFIXE_INDUIT):
            raise ValueError(f"préfixe de nom réservé aux règles induites : {PREFIXE_INDUIT!r}")
        self.moteur.ajoute_regle(tete, corps, nom)

    def branche_relation(self, rel: str, negatifs) -> dict:
        """Induit les règles structurelles sur les faits de base de `rel` (positifs) contre `negatifs` (couples),
        n'ajoute au Datalog QUE les validées (nommées 'induit:<rel>:<type>'). Les règles 'induit:<rel>:*' d'un
        branchement PRÉCÉDENT sont d'abord DÉBRANCHÉES (idempotent ; une règle réfutée par de nouveaux négatifs
        ne survit pas en fantôme). Les négatifs sont PERSISTÉS comme gardes : un fait déclaré faux est servi
        'refute' même si une généralisation le dérive plus tard. Renvoie le rapport d'induction."""
        prefixe = f"{PREFIXE_INDUIT}{rel}:"
        self.moteur.regles = [r for r in self.moteur.regles if not r.nom.startswith(prefixe)]
        self.induites = {n for n in self.induites if not n.startswith(prefixe)}
        positifs = {(x, y) for (r, x, y) in self.moteur.base if r == rel}
        rapport = induction_horn.induit(positifs, negatifs)   # valide la FORME + pos∩neg + point fixe
        self.negatifs.setdefault(rel, set()).update(induction_horn._couples(negatifs, "negatifs"))
        for (t, _support, _nouveaux) in rapport["validees"]:
            for i, (tete, corps) in enumerate(clauses_datalog(t, rel)):
                nom = f"{prefixe}{t}" + (f":{i}" if i else "")
                self.moteur.ajoute_regle(tete, corps, nom)
                self.induites.add(nom)
        self.moteur.faits = set()
        return rapport

    # — certitude : marche ITÉRATIVE de la provenance enregistrée (récursif = RecursionError vers ~500 de
    #   profondeur, attaque 2026-07-02 ; la provenance est acyclique par construction — supports antérieurs) —
    def _certain(self, triplet) -> bool:
        """True ssi la justification ENREGISTRÉE de `triplet` n'utilise que base + règles certaines."""
        pile, vus = [triplet], set()
        while pile:
            t = pile.pop()
            if t in vus:
                continue
            vus.add(t)
            j = self.moteur.prov.get(t)
            if not j:
                return False
            nom, reste = j[0][0], j[0][1]
            if nom == "base":
                continue
            if nom in self.induites:
                return False
            pile.extend(reste)
        return True

    # — interrogation étiquetée —
    def statut(self, rel, x, y):
        """('verifie'|'incertain'|'refute'|'hors', provenance). incertain = dérivable mais dépend d'une règle
        induite ; refute = DÉCLARÉ faux (garde persistante — prime toute généralisation, jamais « dérivable »).
        Un fait à la fois certain-dérivable ET déclaré faux = contradiction réelle -> ValueError (jamais arbitré
        en silence)."""
        declare_faux = (x, y) in self.negatifs.get(rel, ())
        etat, prov = self.moteur.interroge(rel, x, y)
        if etat == "hors":
            return (REFUTE, None) if declare_faux else (HORS, None)
        certain = self._certain((rel, x, y))
        if declare_faux:
            if certain:
                raise ValueError(f"contradiction : ({rel!r}, {x!r}, {y!r}) certain-dérivable ET déclaré négatif")
            return REFUTE, None                   # une généralisation induite ne bat jamais un négatif déclaré
        return (VERIFIE if certain else INCERTAIN), prov

    def reponses(self, rel, x):
        """Tous les y dérivables pour (rel, x, ?) avec leur ÉTIQUETTE — une généralisation induite n'est jamais
        fondue dans les faits vérifiés, un négatif déclaré est marqué 'refute'. Trié (déterministe)."""
        if not self.moteur.faits:
            self.moteur.materialise()
        neg = self.negatifs.get(rel, ())
        out = []
        for (fr, fx, fy) in sorted(self.moteur.faits):
            if fr == rel and fx == x:
                certain = self._certain((fr, fx, fy))
                if (fx, fy) in neg:
                    if certain:
                        raise ValueError(f"contradiction : ({rel!r}, {fx!r}, {fy!r}) certain-dérivable ET déclaré négatif")
                    out.append((fy, REFUTE))
                else:
                    out.append((fy, VERIFIE if certain else INCERTAIN))
        return out

    def explique(self, rel, x, y):
        return self.moteur.explique(rel, x, y)

    def retracte(self, rel, x, y):
        """Rétraction TMS du moteur sous-jacent (re-matérialisation sound)."""
        self.moteur.retracte(rel, x, y)


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=60)
    print("=== DÉMO : la boucle apprendre→valider→raisonner (induction branchée au Datalog) ===")
    m = MoteurInduit()
    for a, b in [("alice", "bob"), ("bob", "carol"), ("alice", "carol"), ("carol", "dan")]:
        m.ajoute_fait("ancetre", a, b, "généalogie")
    r = m.branche_relation("ancetre", negatifs={("bob", "alice")})
    print("  règles validées :", [t for t, _s, _n in r["validees"]], "| rejetées :", [t for t, _e in r["rejetees"]])
    print("  alice ancêtre de bob ? ->", m.statut("ancetre", "alice", "bob")[0], "(fait de base)")
    print("  alice ancêtre de dan ? ->", m.statut("ancetre", "alice", "dan")[0], "(généralisation induite)")
    print("  bob ancêtre d'alice ? ->", m.statut("ancetre", "bob", "alice")[0],
          "(négatif déclaré = garde persistante ; la symétrie rejetée n'a rien dérivé)")
