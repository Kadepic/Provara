"""
MOTEUR DE RÈGLES NORMATIVES — le domaine « règles posées par une autorité », entièrement BORNÉ
(cf. [[project-ia-domaines-realite]], cat 4 CONVENTION élargie). Réponse à Yohan : la loi, les
règles métier, les procédures, l'hygiène (HACCP), les normes… sont TOUTES le même type d'objet —
une RÈGLE POSÉE, datée, de portée définie. On ne les code pas une par une : on bâtit UN moteur
générique, et l'IA APPREND un domaine en INGÉRANT son RÉFÉRENTIEL (ses règles vérifiées + sources).

Ce qui est BORNÉ ici (sound, « sûr avant rapide ») :
  • LA LETTRE de la règle : « que dit l'article/la clause X ? » -> lookup EXACT, daté, scopé.
  • L'APPLICATION d'une règle à PRÉDICAT EXPLICITE (seuil/condition) à un cas non ambigu :
    « température 8 °C vs seuil ≤ 4 °C -> NON CONFORME » = un prédicat déterministe tranche.
Ce qui N'EST PAS borné (-> ABSTENTION, jamais un faux ; relève de la Phase 2 non-bornée) :
  • l'INTERPRÉTATION, la qualification fine, les conflits exigeant un arbitrage, la prédiction
    d'une décision. Une règle SANS prédicat propre -> on rend sa lettre, on n'affirme pas la conformité.

GARANTIES (structurelles) :
  - une règle absente du référentiel n'est JAMAIS inventée (lookup -> None) ;
  - DATÉ : une règle abrogée (ou pas encore en vigueur) à la date de référence n'est pas appliquée ;
  - SCOPÉ : même identifiant sous deux portées (FR vs UE vs entreprise) ne se mélange pas ;
  - un champ manquant du cas -> ABSTENTION (on ne devine pas) ;
  - HIÉRARCHIE des normes : `prevaut` rend la règle de rang supérieur (UE/constitution > loi >
    règlement > norme sectorielle > règle interne), avec le caveat de COMPÉTENCE explicite.

NB honnêteté : les contenus de l'amorce sont des formulations FIDÈLES de dispositions stables et
connues, SOURCÉES et DATÉES ; pour un usage qui engage, re-vérifier le texte exact et la version en
vigueur sur la source officielle (Légifrance, EUR-Lex…). La GARANTIE porte sur le MÉCANISME ; le
contenu est une donnée apprise, sous la responsabilité de l'autorité/source citée. Ceci n'est pas un
conseil juridique.
"""
from __future__ import annotations

import dataclasses

# Date de référence par défaut (déterministe ; on la passe explicitement pour dater un jugement).
AUJOURDHUI = "2026-06-22"

# Statuts d'application d'une règle à un cas.
CONFORME = "conforme"
NON_CONFORME = "non_conforme"
ABSTENTION = "abstention"   # interprétation requise / pas de prédicat propre / donnée manquante

# Opérateurs déclaratifs autorisés pour un prédicat (DONNÉE, pas de code exécuté -> sûr & sérialisable).
_OPS = {
    "<=": lambda v, s: v <= s, "<": lambda v, s: v < s,
    ">=": lambda v, s: v >= s, ">": lambda v, s: v > s,
    "==": lambda v, s: v == s, "!=": lambda v, s: v != s,
}


@dataclasses.dataclass(frozen=True)
class Regle:
    """Une règle posée. `predicat` = condition de conformité DÉCLARATIVE, ou None si la règle relève
    de l'interprétation (lookup seul). Formes de prédicat :
      ("<=", "temperature", 4)            -> conforme ssi cas["temperature"] <= 4
      ("plage", "ph", 4.6, 7.0)           -> conforme ssi 4.6 <= cas["ph"] <= 7.0
    """
    ref: str                 # référentiel + source (ex. "Légifrance — Code civil", "EUR-Lex 32016R0679")
    domaine: str             # domaine lisible (ex. "droit civil FR", "hygiène alimentaire")
    scope: str               # portée d'application (ex. "FR", "UE", "ACME", "secteur alimentaire")
    ident: str               # identifiant dans le référentiel (article/clause/section)
    contenu: str             # formulation fidèle, sourcée
    depuis: str              # entrée en vigueur (ISO "YYYY-MM-DD")
    rang: int                # hiérarchie des normes (plus petit = supérieur)
    jusqua: str | None = None        # fin de validité / abrogation (ISO) ou None si toujours en vigueur
    predicat: tuple | None = None     # condition de conformité déclarative, ou None (interprétation)

    def en_vigueur(self, date: str = AUJOURDHUI) -> bool:
        """Vraie ssi `date` ∈ [depuis, jusqua) — comparaison lexicographique sûre sur dates ISO."""
        return self.depuis <= date and (self.jusqua is None or date < self.jusqua)


@dataclasses.dataclass
class Referentiel:
    """Un corpus NOMMÉ de règles d'une autorité. L'IA « apprend » un domaine en ingérant un Référentiel.
    Clé interne = (scope, ident) -> Regle. Ingestion vérifiée : pas de doublon de clé silencieux."""
    nom: str
    autorite: str
    regles: dict = dataclasses.field(default_factory=dict)

    def apprend(self, regles) -> "Referentiel":
        """INGÈRE des règles (apprentissage d'un domaine). Retourne self (chaînable). Rejette un
        conflit de clé contradictoire (même (scope, ident), contenu différent) -> sûr, pas d'écrasement."""
        for r in regles:
            cle = (r.scope, r.ident)
            ancienne = self.regles.get(cle)
            if ancienne is not None and ancienne.contenu != r.contenu and ancienne.depuis == r.depuis:
                raise ValueError(f"conflit de règle sur {cle} dans {self.nom} (même date, contenu divergent)")
            self.regles[cle] = r
        return self

    def cherche(self, scope: str, ident: str, date: str = AUJOURDHUI) -> Regle | None:
        """Lookup EXACT, scopé + daté. Présent ET en vigueur à `date` -> Regle ; sinon None (jamais inventé)."""
        r = self.regles.get((scope, ident))
        return r if (r is not None and r.en_vigueur(date)) else None


def evalue_predicat(predicat: tuple | None, cas: dict):
    """Évalue un prédicat déclaratif sur un cas. Renvoie True/False, ou None si NON DÉCIDABLE
    (pas de prédicat, opérateur inconnu, ou champ requis absent -> on ne devine pas)."""
    if not predicat:
        return None
    op = predicat[0]
    if op == "plage":
        _, champ, lo, hi = predicat
        if champ not in cas:
            return None
        return lo <= cas[champ] <= hi
    fn = _OPS.get(op)
    if fn is None:
        return None
    _, champ, seuil = predicat
    if champ not in cas:
        return None
    return fn(cas[champ], seuil)


@dataclasses.dataclass(frozen=True)
class Jugement:
    statut: str
    regle: Regle | None = None
    justification: str = ""

    def __str__(self) -> str:
        base = f"[{self.statut.upper()}]"
        if self.regle is not None:
            base += f" {self.regle.ident} ({self.regle.domaine})"
        return f"{base} — {self.justification}" if self.justification else base


def applique(regle: Regle, cas: dict, date: str = AUJOURDHUI) -> Jugement:
    """Applique une règle à un cas concret. CONFORME / NON_CONFORME UNIQUEMENT si la règle a un
    prédicat propre ET que le cas fournit les champs requis. Sinon ABSTENTION (jamais de fausse
    conformité). Une règle non en vigueur à `date` -> ABSTENTION (datée)."""
    if not regle.en_vigueur(date):
        return Jugement(ABSTENTION, regle, "règle non en vigueur à cette date (datée)")
    res = evalue_predicat(regle.predicat, cas)
    if res is None:
        if regle.predicat is None:
            return Jugement(ABSTENTION, regle,
                            "règle d'interprétation (pas de prédicat déterministe) : je rends sa lettre, "
                            "je n'affirme pas la conformité — ceci n'est pas un avis juridique")
        return Jugement(ABSTENTION, regle, "donnée manquante dans le cas : je ne devine pas")
    return Jugement(CONFORME if res else NON_CONFORME, regle,
                    "le cas satisfait la règle" if res else "le cas viole la règle (prédicat explicite)")


APPRIS = "appris"
AMBIGU = "ambigu"
HORS = "hors"


def _est_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _candidats(tous) -> list:
    """Prédicats déclaratifs candidats, dérivés des champs/valeurs observés. Seuils numériques = valeurs
    observées + points milieux (les seules frontières que les exemples peuvent justifier)."""
    champs: set = set()
    for cas, _ in tous:
        champs |= set(cas.keys())
    cands = []
    for champ in sorted(champs, key=str):
        if any(champ not in cas for cas, _ in tous):
            continue   # champ absent de certains cas -> pas un prédicat total fiable
        vals = [cas[champ] for cas, _ in tous]
        if all(_est_num(v) for v in vals):
            distinct = sorted(set(vals))
            seuils = set(distinct)
            for i in range(len(distinct) - 1):
                seuils.add((distinct[i] + distinct[i + 1]) / 2)
            seuils = sorted(seuils)
            for s in seuils:
                for op in ("<=", "<", ">=", ">"):
                    cands.append((op, champ, s))
            # PLAGE (a <= champ <= b) : émise SEULEMENT si la zone VRAIE est encadrée par des FAUX des DEUX
            # côtés (vraie règle d'intervalle). Sinon un seuil one-sided resterait ambigu avec une plage
            # [min_observé, seuil] spurieuse. Garde la soundness ET ajoute l'apprentissage des intervalles.
            vrais = [cas[champ] for cas, lab in tous if lab and _est_num(cas.get(champ))]
            faux = [cas[champ] for cas, lab in tous if not lab and _est_num(cas.get(champ))]
            if vrais and faux and min(faux) < min(vrais) and max(faux) > max(vrais):
                for i in range(len(seuils)):
                    for j in range(i, len(seuils)):
                        cands.append(("plage", champ, seuils[i], seuils[j]))
        else:
            for s in sorted(set(vals), key=repr):
                for op in ("==", "!="):
                    cands.append((op, champ, s))
    return cands


def _probes(tous) -> list:
    """Cas-sondes pour tester si deux prédicats valides ont le MÊME comportement (sinon : sous-déterminé).
    Base = fusion des cas observés ; on fait varier chaque champ numérique autour des valeurs observées."""
    base: dict = {}
    for cas, _ in tous:
        base.update(cas)
    sondes = [dict(cas) for cas, _ in tous]
    champs = set(base)
    for champ in champs:
        vals = [cas[champ] for cas, _ in tous if champ in cas]
        if not (vals and all(_est_num(v) for v in vals)):
            continue
        distinct = sorted(set(vals))
        extra = set(distinct) | {distinct[0] - 1, distinct[-1] + 1}
        if all(float(v).is_integer() for v in vals):
            # champ ENTIER : on sonde à la granularité 1 (deux seuils équivalents sur les entiers sont
            # jugés identiques) -> une frontière entière CERNÉE est apprenable ; un trou reste ambigu.
            for v in range(int(distinct[0]) - 1, int(distinct[-1]) + 2):
                extra.add(v)
        else:
            # champ CONTINU : on sonde aussi les mi-points -> un seuil réel exige une frontière serrée.
            for i in range(len(distinct) - 1):
                extra.add((distinct[i] + distinct[i + 1]) / 2)
        for v in sorted(extra):
            s = dict(base)
            s[champ] = v
            sondes.append(s)
    return sondes


def apprend_predicat(exemples, exemples_held=None):
    """L'IA APPREND/CRÉE la règle à partir de CAS ÉTIQUETÉS (cas:dict, conforme:bool) quand le texte
    n'est pas donné. Renvoie (statut, predicat|None) :
      • (APPRIS, predicat)  — UN comportement unique reproduit exemples+held (vérifié) ;
      • (AMBIGU, None)      — plusieurs prédicats DISTINCTS reproduisent (seuil sous-déterminé : il faut
                              des exemples qui cernent la frontière) -> on n'invente pas (anti-hallucination) ;
      • (HORS, None)        — aucun prédicat seuil/égalité simple ne reproduit (concept hors de cette famille).
    SOUNDNESS : on ne renvoie jamais un prédicat qui se trompe sur un exemple étiqueté ; l'ambiguïté
    s'abstient (cf. principe « pas de fausse précision » de [[project-ia-staging-nonborne]])."""
    tous = list(exemples) + list(exemples_held or [])
    if not tous:
        return (HORS, None)
    # un candidat est VALIDE ssi il reproduit EXACTEMENT toutes les étiquettes (None != bool -> exclu).
    valides = [c for c in _candidats(tous)
               if all(evalue_predicat(c, cas) == bool(label) for cas, label in tous)]
    if not valides:
        return (HORS, None)
    sondes = _probes(tous)
    ref = valides[0]
    ref_sig = [evalue_predicat(ref, s) for s in sondes]
    for c in valides[1:]:
        if [evalue_predicat(c, s) for s in sondes] != ref_sig:
            return (AMBIGU, None)   # deux prédicats valides divergent sur une sonde -> sous-déterminé
    # comportement unique : on renvoie le candidat le plus simple (op canonique, seuil déterministe)
    ordre = {"<=": 0, ">=": 1, "<": 2, ">": 3, "==": 0, "!=": 1}
    return (APPRIS, min(valides, key=lambda c: (ordre.get(c[0], 9), repr(c[2]), c[1])))


def prevaut(r1: Regle, r2: Regle) -> Regle:
    """Hiérarchie des normes : rend la règle de RANG supérieur (plus petit `rang`). À rang égal,
    la plus récente. ATTENTION : la primauté (ex. droit de l'UE sur le droit national) ne s'applique
    que DANS LE DOMAINE DE COMPÉTENCE — ce helper donne l'ordre formel, pas une qualification de
    compétence (qui, elle, relève de l'interprétation -> hors borne)."""
    if r1.rang != r2.rang:
        return r1 if r1.rang < r2.rang else r2
    return r1 if r1.depuis >= r2.depuis else r2


# ===========================================================================================
#  AMORCE MULTI-DOMAINES — chaque Référentiel est un domaine APPRIS (prouve la généricité).
#  « Les faire tous » = ingérer autant de référentiels que besoin, même mécanisme. Petit mais sourcé.
# ===========================================================================================

# Rangs (hiérarchie des normes, ordre formel) :
R_UE = 1            # droit de l'Union (dans son domaine de compétence)
R_LOI = 2           # loi nationale
R_REGLEMENT = 3     # règlement / arrêté
R_NORME = 4         # norme sectorielle / référentiel d'hygiène
R_INTERNE = 5       # règle interne d'organisation

DROIT_FR = Referentiel("Droit français", "Légifrance").apprend([
    Regle("Légifrance — Code civil", "droit civil FR", "FR", "Code civil art. 414",
          "La majorité est fixée à dix-huit ans accomplis.", "1974-07-05", R_LOI,
          predicat=(">=", "age", 18)),
    Regle("Légifrance — Code de la route", "sécurité routière FR", "FR", "Code de la route R413-3",
          "En agglomération, la vitesse est limitée à 50 km/h.", "1990-12-01", R_REGLEMENT,
          predicat=("<=", "vitesse", 50)),
    Regle("Légifrance — Code civil", "droit civil FR", "FR", "Code civil art. 9",
          "Chacun a droit au respect de sa vie privée.", "1970-07-17", R_LOI,
          predicat=None),   # interprétation -> ABSTENTION sur la conformité
])

DROIT_UE = Referentiel("Droit de l'Union", "EUR-Lex").apprend([
    Regle("EUR-Lex 32016R0679 (RGPD)", "protection des données UE", "UE", "RGPD art. 5",
          "Les données à caractère personnel sont traitées de manière licite, loyale et transparente, "
          "pour des finalités déterminées, et limitées à ce qui est nécessaire (minimisation).",
          "2018-05-25", R_UE, predicat=None),   # principes -> interprétation
])

HYGIENE = Referentiel("Hygiène alimentaire", "Règl. (CE) 852/2004 + plan HACCP").apprend([
    Regle("Règl. (CE) 852/2004 / HACCP", "hygiène alimentaire", "secteur alimentaire", "Conservation réfrigérée",
          "Les denrées très périssables doivent être conservées au froid (≤ +4 °C).", "2006-01-01", R_NORME,
          predicat=("<=", "temperature", 4)),
])

# Règle métier / procédure interne (référentiel PRIVÉ appris au même titre).
INTERNE_ACME = Referentiel("Politique interne ACME", "ACME (interne v3)").apprend([
    Regle("ACME — politique commerciale v3", "règle métier RH/commerce", "ACME", "Remise fidélité",
          "Remise fidélité accordée à partir de 12 mois d'ancienneté client.", "2025-01-01", R_INTERNE,
          predicat=(">=", "anciennete_mois", 12)),
    Regle("ACME — procédure sécurité chantier v2", "procédure sécurité", "ACME", "Port du casque",
          "Le port du casque est obligatoire sur le chantier.", "2024-06-01", R_INTERNE,
          predicat=("==", "casque_porte", True)),
])

# « Ce que l'IA a appris » = l'ensemble des référentiels ingérés.
BASE = [DROIT_FR, DROIT_UE, HYGIENE, INTERNE_ACME]


def cherche_partout(scope: str, ident: str, base=None, date: str = AUJOURDHUI) -> Regle | None:
    """Cherche une règle dans tous les référentiels appris (premier match scopé + daté)."""
    for ref in (BASE if base is None else base):
        r = ref.cherche(scope, ident, date)
        if r is not None:
            return r
    return None


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== MOTEUR DE RÈGLES NORMATIVES — domaines appris, jugés sound ===\n")
    print(f"Référentiels appris : {', '.join(r.nom for r in BASE)}\n")

    demos = [
        (cherche_partout("secteur alimentaire", "Conservation réfrigérée"), {"temperature": 3}),
        (cherche_partout("secteur alimentaire", "Conservation réfrigérée"), {"temperature": 8}),
        (cherche_partout("FR", "Code civil art. 414"), {"age": 20}),
        (cherche_partout("FR", "Code civil art. 414"), {"age": 16}),
        (cherche_partout("FR", "Code de la route R413-3"), {"vitesse": 70}),
        (cherche_partout("ACME", "Remise fidélité"), {"anciennete_mois": 18}),
        (cherche_partout("FR", "Code civil art. 9"), {"quoi": "vie privée"}),   # interprétation -> ABSTENTION
        (cherche_partout("UE", "RGPD art. 5"), {}),                              # interprétation -> ABSTENTION
    ]
    for regle, cas in demos:
        if regle is None:
            print("  [INTROUVABLE] (règle absente du référentiel — non inventée)")
            continue
        print(f"  {applique(regle, cas)}\n      « {regle.contenu} »  (source : {regle.ref}, depuis {regle.depuis})")

    print("\nHiérarchie : RGPD (UE) vs Remise fidélité (interne ACME) ->",
          prevaut(cherche_partout("UE", "RGPD art. 5"), cherche_partout("ACME", "Remise fidélité")).ident,
          "(prévaut, dans son domaine de compétence)")
