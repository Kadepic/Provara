"""
INGESTION T7 — MESURES NUMÉRIQUES & TECHNIQUE -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline ensuite).

Ouvre le PATRON NUMÉRIQUE du lecteur (valeur + unité). Chaque relation = (classe, propriété) -> une valeur
littérale numérique exprimée DANS UNE UNITÉ CANONIQUE (le mètre pour les longueurs), avec :

  FAUX=0 NUMÉRIQUE (garde-fous cumulés) :
    (a) `float(v)` parsable, sinon REJET ;
    (b) UNITÉ EXPLICITE (psv:/wikibase:quantityUnit) lue puis CONVERTIE vers le mètre par un facteur EXACT
        (pied×0,3048, pouce×0,0254, cm×0,01, mm×0,001, km×1000). Unité hors de la table blanche -> IGNORÉE.
        => fini la fuite d'unité : un phare en pieds ou une statue en centimètres n'est plus lu comme des mètres.
    (c) FONCTIONNEL À TOLÉRANCE (par libellé) : on regroupe toutes les déclarations d'un même libellé, converties
        en mètres ; si elles s'ACCORDENT (étendue ≤ tol) -> une seule valeur émise (le mètre natif est préféré) ;
        si elles DÉSACCORDENT (homonymes « mont Blanc », mesures incompatibles) -> HORS. Jamais d'ambiguïté écrite.
    (d) PLAGE physique [vmin, vmax] (en mètres) : écarte les saisies aberrantes restantes.
    (e) ANCRES vérité-terrain dans valide_lecteur_t7.py (Everest≈8849 m, Burj Khalifa≈828 m…) — non circulaire.

Mode COMPTE (population) : valeur = un dénombrement sans unité ; pull `wdt:` direct + fonctionnel EXACT de publie
(plusieurs recensements => HORS). La fabrique catégorielle (licence = ensemble fermé) réutilise IQ.

Unité canonique portée par le NOM de relation + la SOURCE (le lecteur stocke un scalaire, comme `numero_atomique`).
Usage : python3 ingere_t7.py sonde   (inspecte sans écrire)   |   python3 ingere_t7.py   (ingère tout).
"""
from __future__ import annotations

import sys

import ingere_qlever as IQ

# Prefixes SPARQL supplémentaires pour atteindre les value-nodes (l'unité explicite) côté QLever.
_PREF_UNITE = (
    "PREFIX p: <http://www.wikidata.org/prop/>\n"
    "PREFIX psv: <http://www.wikidata.org/prop/statement/value/>\n"
    "PREFIX wikibase: <http://wikiba.se/ontology#>\n")

# Unité (QID Wikidata) -> facteur EXACT vers le mètre. Hors table -> déclaration ignorée (sound).
UNITES_METRE = {
    "Q11573": 1.0,        # mètre
    "Q3710": 0.3048,      # pied international (exact par définition)
    "Q218593": 0.0254,    # pouce (exact)
    "Q174728": 0.01,      # centimètre
    "Q174789": 0.001,     # millimètre
    "Q828224": 1000.0,    # kilomètre
}
# Unité d'AIRE (QID) -> facteur EXACT vers le km². Hors table -> déclaration ignorée (sound).
UNITES_KM2 = {
    "Q712226": 1.0,        # kilomètre carré
    "Q35852": 0.01,        # hectare (1 ha = 0,01 km²)
    "Q25343": 1e-6,        # mètre carré
    "Q2737347": 1e-4,      # décamètre carré (= 100 m²)
    "Q23892": 0.00404685642, # acre international (exact)
    "Q81292": 0.00404685642, # acre (QID alternatif, même facteur)
    "Q232291": 2.589988110336, # mille carré (exact)
}
# Unité de PUISSANCE (QID) -> facteur EXACT vers le mégawatt (MW). ⚠️ NE PAS inclure mégavolt-ampère (Q5409016) ni
# kVA (Q29924639) = puissance APPARENTE (≠ watt), ni m³/s (Q794261) = débit -> grandeurs différentes, ignorées (sound).
UNITES_MW = {
    "Q6982035": 1.0,       # mégawatt (natif)
    "Q3320608": 0.001,     # kilowatt
    "Q5879479": 1000.0,    # gigawatt
    "Q25236": 1e-6,        # watt
}
# Unité de MASSE (QID) -> facteur EXACT vers le kilogramme (kg).
UNITES_KG = {
    "Q11570": 1.0,         # kilogramme (natif)
    "Q191118": 1000.0,     # tonne
    "Q41803": 0.001,       # gramme
    "Q100995": 0.45359237, # livre (pound international, exact)
}
# Unité de DÉBIT (QID) -> m³/s. On ne garde que le m³/s natif (les autres unités de débit sont minoritaires/ambiguës).
UNITES_M3S = {
    "Q794261": 1.0,        # mètre cube par seconde (natif)
}
# Unité de VITESSE (QID) -> facteur EXACT vers le km/h. ⚠️ NE PAS inclure le nombre de Mach (Q160669) : pas de
# facteur fixe (dépend de l'altitude/température) -> ignoré (sound). Sur les véhicules (Q42889) le nœud DOMINE (navires).
UNITES_KMH = {
    "Q180154": 1.0,         # kilomètre par heure (natif)
    "Q128822": 1.852,       # nœud (1 NM/h = 1852 m/h, exact)
    "Q211256": 1.609344,    # mille par heure (mph, exact)
    "Q182429": 3.6,         # mètre par seconde
    "Q3674704": 3600.0,     # kilomètre par seconde
}
# Unité de FRÉQUENCE (QID) -> facteur EXACT vers le mégahertz (MHz). QID confirmés sur les stations de radio.
# ⚠️ Hors table -> ignoré (sound) : « chaîne de télévision », « modulation de fréquence », « tour par minute »
# (rotation ≠ fréquence d'onde), « femtomètre » (longueur mal saisie), QID-villes parasites. GHz non vérifié -> exclu.
UNITES_MHZ = {
    "Q732707": 1.0,         # mégahertz (natif)
    "Q2143992": 0.001,      # kilohertz
    "Q39369": 1e-6,         # hertz
}
# Unité de TENSION électrique (QID) -> facteur EXACT vers le kilovolt (kV). volt et kilovolt seulement (vérifiés).
UNITES_KV = {
    "Q2554092": 1.0,        # kilovolt (natif)
    "Q25250": 0.001,        # volt
}
# « Unité » de CAPACITÉ-PASSAGERS (compte de personnes). On ne garde QUE les unités-PERSONNES (toutes = 1 personne) ;
# ⚠️ exclus car quantités DIFFÉRENTES : « équivalent vingt pieds » (TEU, conteneurs), « voiture »/« automobile »
# (capacité de ferry en véhicules), et le générique « 1 » (Q199, ambigu : passagers ? voitures ? -> ignoré, sound).
UNITES_PASSAGERS = {
    "Q319604": 1.0,         # passager (natif)
    "Q5": 1.0,              # être humain
    "Q215627": 1.0,         # personne
}
# Unité d'AUTONOMIE/range (QID) -> facteur EXACT vers le mètre. Table DÉDIÉE (ne pas polluer UNITES_METRE avec NM/mile).
# ⚠️ Exclus = grandeurs DIFFÉRENTES : nœud (vitesse), jour (durée), km² (aire) -> hors table -> ignorés (sound).
UNITES_AUTONOMIE = {
    "Q11573": 1.0,          # mètre
    "Q828224": 1000.0,      # kilomètre
    "Q93318": 1852.0,       # mille nautique (exact)
    "Q253276": 1609.344,    # mille international (exact)
}
# Unité de VOLUME (QID) -> facteur EXACT vers le mètre cube. Natif = m³ (Q25517).
# ⚠️ Exclus = grandeurs DIFFÉRENTES présentes dans les données : mètre (Q11573, longueur), km² (Q712226, aire)
#    -> hors table -> ignorés (sound).
UNITES_VOLUME = {
    "Q25517": 1.0,                    # mètre cube
    "Q5195628": 1e6,                  # hectomètre cube (100 m)³
    "Q4243638": 1e9,                  # kilomètre cube
    "Q342590": 1233.48183754752,      # acre-pied (exact)
    "Q23925410": 0.00454609,          # gallon impérial (exact)
    "Q23925413": 0.003785411784,      # gallon US (exact)
    "Q53393659": 1000.0,              # mégalitre (10⁶ L)
    "Q53393664": 1e6,                 # gigalitre (10⁹ L)
    "Q11582": 0.001,                  # litre
    "Q1545979": 0.028316846592,       # pied cube (exact)
}
# Unité de TEMPS (QID) -> facteur EXACT vers la seconde. Natif = seconde (Q11574). « annum » = an julien 365,25 j.
UNITES_SECONDE = {
    "Q11574": 1.0,            # seconde
    "Q7727": 60.0,            # minute
    "Q25235": 3600.0,         # heure
    "Q573": 86400.0,          # jour
    "Q1092296": 31557600.0,   # annum (an julien = 365,25 × 86400)
    "Q723733": 1e-3,          # milliseconde
    "Q842015": 1e-6,          # microseconde
    "Q838801": 1e-9,          # nanoseconde
    "Q3902709": 1e-12,        # picoseconde
    "Q1777507": 1e-15,        # femtoseconde
    "Q2483628": 1e-18,        # attoseconde
    "Q2762458": 1e-24,        # yoctoseconde
}
# Unité de MASSE MOLÉCULAIRE -> dalton (Da = unité de masse atomique unifiée). Valeurs GARDÉES en Da (pas de
# conversion en kg : le dalton est l'unité naturelle de la masse moléculaire). Natif = dalton.
UNITES_DALTON = {
    "Q483261": 1.0,           # dalton
}
# Unité de MASSE VOLUMIQUE -> kg/m³. (g/cm³ et g/mL = ×1000 ; g/L = ×1, identité kg/m³.)
UNITES_DENSITE = {
    "Q844211": 1.0,           # kilogramme par mètre cube (natif)
    "Q13147228": 1000.0,      # gramme par centimètre cube
    "Q3308032": 1000.0,       # gramme par millilitre
    "Q834105": 1.0,           # gramme par litre (= kg/m³)
}
# Unité de PETITE MASSE -> gramme. Garde les valeurs en g (objets ~g : pièces/médailles) pour ancre discriminante.
UNITES_GRAMME = {
    "Q41803": 1.0,            # gramme (natif)
    "Q11570": 1000.0,         # kilogramme
    "Q191118": 1e6,           # tonne
}
# Unité de PETIT DIAMÈTRE -> millimètre. Garde les valeurs en mm (pas en m) pour que la tolérance d'ancre
# max(2,1%) du validateur reste DISCRIMINANTE sur les objets cm (pièces/médailles ~15-40 mm).
UNITES_MM = {
    "Q174789": 1.0,           # millimètre (natif)
    "Q174728": 10.0,          # centimètre
    "Q11573": 1000.0,         # mètre
    "Q218593": 25.4,          # pouce (exact)
}


# ============================================================================================
#  PULL UNITÉ-AWARE GÉNÉRIQUE : entité (classe) -> valeur convertie dans une unité CANONIQUE,
#  fonctionnel à tolérance par libellé (accord -> 1 valeur native-médiane ; désaccord -> HORS).
# ============================================================================================
def _pull_unite(relation, classe_qid, prop, unites, natif_qid, tol_abs, tol_rel, sous_classes=True):
    """Renvoie [(libellé, valeur_canonique_float, brut)] dédupliqué : un libellé n'apparaît qu'une fois, et seulement
    si toutes ses déclarations (converties via `unites`) s'accordent à tol = max(tol_abs, tol_rel·|médiane|). Le
    représentant = médiane des valeurs en unité NATIVE (`natif_qid`, conversion ×1) sinon médiane des converties."""
    chemin = "wdt:P31/wdt:P279*" if sous_classes else "wdt:P31"
    q = _PREF_UNITE + f"""SELECT ?eLabel ?amt ?unit WHERE {{
      ?e {chemin} wd:{classe_qid} ; p:{prop} ?st .
      ?st psv:{prop} ?vn . ?vn wikibase:quantityAmount ?amt ; wikibase:quantityUnit ?unit .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    par = {}    # libellé -> liste de (valeur_canonique, est_natif)
    for r in rows:
        e = IQ.val(r, "eLabel")
        amt = IQ.val(r, "amt")
        unit = IQ.val(r, "unit").rsplit("/", 1)[-1]
        if not e or not amt or IQ._est_qid(e):
            continue
        fac = unites.get(unit)
        if fac is None:
            continue
        try:
            x = float(amt) * fac
        except ValueError:
            continue
        par.setdefault(e, []).append((x, unit == natif_qid))
    out = []
    for e, vals in par.items():
        xs = [x for x, _nat in vals]
        med = sorted(xs)[len(xs) // 2]
        if max(xs) - min(xs) > max(tol_abs, tol_rel * abs(med)):
            continue                                # désaccord -> HORS (homonyme ou conflit d'unité)
        natifs = sorted(x for x, nat in vals if nat)
        pool = natifs if natifs else sorted(xs)
        x = pool[len(pool) // 2]
        out.append((e, x, _fmt(x)))
    return out


def _pull_metres(relation, classe_qid, prop, sous_classes=True):
    """LONGUEUR -> mètres (tol 0,5 m ou 0,5 %, natif = mètre)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_METRE, "Q11573", 0.5, 0.005, sous_classes)


def _pull_aire(relation, classe_qid, prop, sous_classes=True):
    """AIRE -> km² (tol relative 1 %, natif = km² ; pas de plancher absolu, valeurs sur 9 ordres de grandeur)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_KM2, "Q712226", 0.0, 0.01, sous_classes)


def _pull_puissance(relation, classe_qid, prop, sous_classes=True):
    """PUISSANCE -> mégawatt (tol relative 1 %, natif = MW ; W/kW/MW/GW seulement, pas la puissance apparente)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_MW, "Q6982035", 0.0, 0.01, sous_classes)


def _pull_masse(relation, classe_qid, prop, sous_classes=True):
    """MASSE -> kilogramme (tol 0,1 kg ou 1 %, natif = kg)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_KG, "Q11570", 0.1, 0.01, sous_classes)


def _pull_debit(relation, classe_qid, prop, sous_classes=True):
    """DÉBIT -> m³/s (tol relative 1 %, natif = m³/s ; autres unités de débit ignorées)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_M3S, "Q794261", 0.01, 0.01, sous_classes)


def _pull_vitesse(relation, classe_qid, prop, sous_classes=True):
    """VITESSE -> km/h (tol 0,5 km/h ou 1 %, natif = km/h ; nœud/mph/m·s⁻¹/km·s⁻¹ convertis, Mach ignoré)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_KMH, "Q180154", 0.5, 0.01, sous_classes)


def _pull_frequence(relation, classe_qid, prop, sous_classes=True):
    """FRÉQUENCE -> MHz (tol 0,05 MHz ou 0,1 %, natif = MHz ; kHz/Hz convertis ; homonymes désaccord -> HORS)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_MHZ, "Q732707", 0.05, 0.001, sous_classes)


def _pull_tension(relation, classe_qid, prop, sous_classes=True):
    """TENSION -> kV (tol 0,5 kV ou 1 %, natif = kV ; volt converti ; multi-tension/homonymes -> HORS)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_KV, "Q2554092", 0.5, 0.01, sous_classes)


def _pull_passagers(relation, classe_qid, prop, sous_classes=True):
    """CAPACITÉ-PASSAGERS -> compte de personnes (tol 2 ou 2 %, natif = passager ; unités non-personnes ignorées ;
    sources divergentes -> HORS). Seules les déclarations unit'ées en personnes comptent (jamais TEU/voitures/« 1 »)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_PASSAGERS, "Q319604", 2.0, 0.02, sous_classes)


def _pull_autonomie(relation, classe_qid, prop, sous_classes=True):
    """AUTONOMIE/range -> mètres (tol 100 m ou 2 %, natif = mètre ; km/NM/mile convertis ; nœud/jour/km² ignorés)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_AUTONOMIE, "Q11573", 100.0, 0.02, sous_classes)


def _pull_volume(relation, classe_qid, prop, sous_classes=True):
    """VOLUME -> mètre cube (tol relative 1 %, natif = m³ ; valeurs sur ~14 ordres de grandeur -> pas de plancher
    absolu, comme l'aire ; hm³/km³/acre-pied/gallons/L/pied³ convertis ; mètre & km² mal-typés ignorés = sound)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_VOLUME, "Q25517", 0.0, 0.01, sous_classes)


def _pull_temps(relation, classe_qid, prop, sous_classes=True):
    """TEMPS -> seconde (tol relative 1 %, natif = seconde ; an julien/jour/h/min/ms/µs/ns/ps/fs/as/ys convertis ;
    valeurs sur ~50 ordres de grandeur -> pas de plancher absolu, comme l'aire/le volume)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_SECONDE, "Q11574", 0.0, 0.01, sous_classes)


def _pull_densite(relation, classe_qid, prop, sous_classes=True):
    """MASSE VOLUMIQUE -> kg/m³ (tol relative 1 %, natif = kg/m³ ; g/cm³·g/mL convertis ×1000, g/L identité ;
    plusieurs T° -> désaccord HORS)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_DENSITE, "Q844211", 0.0, 0.01, sous_classes)


def _pull_gramme(relation, classe_qid, prop, sous_classes=True):
    """PETITE MASSE -> gramme (tol 0,05 g ou 1 %, natif = g ; kg/tonne convertis). Valeurs gardées en g pour rester
    sous une ancre discriminante (objets g-scale : pièces de monnaie, médailles)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_GRAMME, "Q41803", 0.05, 0.01, sous_classes)


def _pull_mm(relation, classe_qid, prop, sous_classes=True):
    """PETIT DIAMÈTRE -> millimètre (tol 0,5 mm ou 1 %, natif = mm ; cm/m/pouce convertis). Valeurs gardées en mm
    pour rester sous une ancre discriminante (objets cm-scale : pièces de monnaie, médailles)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_MM, "Q174789", 0.5, 0.01, sous_classes)


# Unité de TEMPÉRATURE -> Kelvin par conversion AFFINE : K = amt·a + b (≠ multiplicatif). Facteurs EXACTS.
_UNITES_KELVIN = {
    "Q11579": (1.0, 0.0),                 # kelvin
    "Q25267": (1.0, 273.15),              # degré Celsius
    "Q42289": (5.0 / 9.0, 255.3722222222222),  # degré Fahrenheit : K = F·5/9 + (273.15 − 32·5/9)
}


def _pull_temperature(relation, classe_qid, prop, sous_classes=True):
    """TEMPÉRATURE -> kelvin (conversion AFFINE °C/°F→K ; tol 1 K ou 0,5 % ; multi-source/polymorphes désaccord→HORS).
    Valeurs gardées en K (toujours positives → plage simple). Unités hors table ignorées = sound."""
    chemin = "wdt:P31/wdt:P279*" if sous_classes else "wdt:P31"
    q = _PREF_UNITE + f"""SELECT ?eLabel ?amt ?unit WHERE {{
      ?e {chemin} wd:{classe_qid} ; p:{prop} ?st .
      ?st psv:{prop} ?vn . ?vn wikibase:quantityAmount ?amt ; wikibase:quantityUnit ?unit .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    par = {}
    for r in rows:
        e = IQ.val(r, "eLabel"); amt = IQ.val(r, "amt"); unit = IQ.val(r, "unit").rsplit("/", 1)[-1]
        if not e or not amt or IQ._est_qid(e):
            continue
        conv = _UNITES_KELVIN.get(unit)
        if conv is None:
            continue
        try:
            x = float(amt) * conv[0] + conv[1]
        except ValueError:
            continue
        par.setdefault(e, []).append(x)
    out = []
    for e, xs in par.items():
        med = sorted(xs)[len(xs) // 2]
        if max(xs) - min(xs) > max(1.0, 0.005 * abs(med)):
            continue
        out.append((e, med, _fmt(med)))
    return out


def _pull_dalton(relation, classe_qid, prop, sous_classes=True):
    """MASSE MOLÉCULAIRE -> dalton (tol relative 1 %, natif = dalton ; valeurs gardées en Da ; monoisotopique/moyenne
    s'accordent à 1 %). Autres unités de masse (kg/g) ignorées = sound (on ne veut que la masse moléculaire en Da)."""
    return _pull_unite(relation, classe_qid, prop, UNITES_DALTON, "Q483261", 0.0, 0.01, sous_classes)


def _pull_compte(relation, classe_qid, prop, sous_classes=True):
    """Mode COMPTE (population…) : valeur = dénombrement sans unité. wdt: direct ; le fonctionnel EXACT de publie
    écarte les entités à plusieurs valeurs (plusieurs recensements -> HORS)."""
    chemin = "wdt:P31/wdt:P279*" if sous_classes else "wdt:P31"
    q = f"""SELECT ?eLabel ?v WHERE {{
      ?e {chemin} wd:{classe_qid} ; wdt:{prop} ?v .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    out = []
    for r in rows:
        e = IQ.val(r, "eLabel")
        v = IQ.val(r, "v")
        if not e or not v or IQ._est_qid(e):
            continue
        try:
            f = float(v)
        except ValueError:
            continue
        out.append((e, f, v))
    return out


def _fmt(f: float) -> str:
    """Forme propre : entier sans « .0 », sinon décimal compact (repr nettoie les artefacts binaires courants)."""
    if f == int(f):
        return str(int(f))
    return repr(round(f, 4))


def ingere_numerique(relation, classe_qid, prop, source, vmin, vmax,
                     categorie="physique", sous_classes=True, mode="unite"):
    """Ingère une relation NUMÉRIQUE bornée. mode='unite' -> conversion en mètres ; mode='compte' -> dénombrement.
    PLAGE [vmin, vmax] = garde-fou final (HORS hors-plage). Renvoie les stats publie()."""
    pull = {"unite": _pull_metres, "compte": _pull_compte, "aire": _pull_aire, "puissance": _pull_puissance, "masse": _pull_masse, "debit": _pull_debit, "vitesse": _pull_vitesse, "frequence": _pull_frequence, "tension": _pull_tension, "passagers": _pull_passagers, "autonomie": _pull_autonomie, "volume": _pull_volume, "temps": _pull_temps, "dalton": _pull_dalton, "mm": _pull_mm, "temperature": _pull_temperature, "gramme": _pull_gramme, "densite": _pull_densite}[mode]
    triples = pull(relation, classe_qid, prop, sous_classes=sous_classes)
    paires, hors_plage = [], 0
    for e, f, _brut in triples:
        if vmin <= f <= vmax:
            paires.append((e, _fmt(f)))
        else:
            hors_plage += 1
    print(f"== {relation} ({prop}, classe {classe_qid}, {mode}) : {len(triples)} entités, "
          f"plage[{vmin},{vmax}] -> {len(paires)} gardés, {hors_plage} hors-plage(HORS) ==")
    return IQ.publie(relation, categorie, source, paires)


# ============================================================================================
#  RELATIONS T7 — (relation, classe, prop, source, vmin, vmax, categorie, mode)
#  unite : valeur convertie en MÈTRES (unité explicite lue). compte : dénombrement sans unité.
# ============================================================================================
_SRC = "Wikidata/QLever — {p} (unité lue puis convertie en mètres ; pied/pouce/cm exacts)"
NUMERIQUES = [
    # --- géométrie physique (mètres, unité-aware) ---
    ("altitude_montagne",   "Q8502",   "P2044", _SRC.format(p="altitude P2044"),  -500, 9000, "physique", "unite"),
    ("hauteur_gratte_ciel", "Q11303",  "P2048", _SRC.format(p="hauteur P2048"),    30, 1000,  "physique", "unite"),
    ("hauteur_barrage",     "Q12323",  "P2048", _SRC.format(p="hauteur P2048"),    1, 350,    "physique", "unite"),
    ("hauteur_tour",        "Q12518",  "P2048", _SRC.format(p="hauteur P2048"),    10, 1000,  "physique", "unite"),
    ("profondeur_lac",      "Q23397",  "P4511", _SRC.format(p="profondeur P4511"), 1, 2000,   "physique", "unite"),
    ("hauteur_phare",       "Q39715",  "P2048", _SRC.format(p="hauteur P2048"),    1, 160,    "physique", "unite"),
    ("hauteur_statue",      "Q179700", "P2048", _SRC.format(p="hauteur P2048"),    1, 250,    "physique", "unite"),
    ("longueur_navire",     "Q11446",  "P2043", _SRC.format(p="longueur P2043"),   3, 460,    "physique", "unite"),
    # --- lot 3 (mètres, unité-aware) ---
    ("altitude_aeroport",   "Q1248784", "P2044", _SRC.format(p="altitude P2044"), -500, 5000, "physique", "unite"),
    ("altitude_ville",      "Q515",    "P2044", _SRC.format(p="altitude P2044"),  -500, 5500, "physique", "unite"),
    # --- lot 4 : longueurs KM-CAPABLES (débloquées par l'unité-aware ; statements PORTANT une unité) ---
    ("longueur_fleuve",     "Q4022",   "P2043", _SRC.format(p="longueur P2043"),  1, 7_000_000, "physique", "unite"),
    ("longueur_pont",       "Q12280",  "P2043", _SRC.format(p="longueur P2043"),  1, 200_000,   "physique", "unite"),
    ("hauteur_cascade",     "Q34038",  "P2048", _SRC.format(p="hauteur P2048"),   1, 1000,      "physique", "unite"),
    # --- lot 5 : patron AIRE (km², unité-aware ; km²/ha/m²/acre lus puis convertis) ---
    ("superficie_ile",      "Q23442",  "P2046", "Wikidata/QLever — superficie P2046 (unité lue puis convertie en "
     "km² ; km²/ha/m²/acre exacts)", 0, 2_200_000, "physique", "aire"),
    # --- lot 6 : extensions AIRE (km²) + glacier (m) ---
    ("superficie_parc_national", "Q46169", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 1_000_000, "physique", "aire"),
    ("superficie_desert",   "Q8514",   "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 10_000_000, "physique", "aire"),
    ("superficie_reserve_naturelle", "Q179049", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 1_000_000, "physique", "aire"),
    # superficie de lac (ex-« différé sans-unité » : la plupart des lacs ONT désormais une unité km² explicite)
    ("superficie_lac",      "Q23397",  "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0.001, 400_000, "physique", "aire"),
    ("superficie_reservoir", "Q131681", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0.001, 20_000, "physique", "aire"),
    ("superficie_baie",     "Q39594",  "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0.001, 3_000_000, "physique", "aire"),
    ("superficie_etang",    "Q3253281", "P2046", "Wikidata/QLever — superficie P2046 (→ km² ; unité-explicite seulement)", 0.001, 2_000, "physique", "aire"),
    ("masse_navire",        "Q11446",  "P2067", "Wikidata/QLever — masse/déplacement P2067 (unité lue → kg ; tonne/livre exacts ; ton/long-ton ambigus ignorés)", 100, 1e9, "physique", "masse"),
    # vitesse_navire : ship-specific (Q11446) — superset vitesse_max_vehicule (Q42889) rate des navires (lacunes P279*) ; relation conservée pour couverture maximale (overlap toléré, cf hauteur_structure)
    ("vitesse_navire",      "Q11446",  "P2052", "Wikidata/QLever — vitesse max P2052 (nœud→km/h ; multi-source→HORS)", 1, 120, "physique", "vitesse"),
    # vitesse_train : matériel roulant ferroviaire (Q811704) — SUPERSET propre des locos (Q19832486⊂Q811704, pas de lacune P279*) + EMUs/TGV/Shinkansen/ICE. Remplace l'ex-vitesse_locomotive.
    ("vitesse_train",       "Q811704", "P2052", "Wikidata/QLever — vitesse max (de conception) P2052 (→ km/h)", 1, 700, "physique", "vitesse"),
    ("nombre_travees",      "Q12280",  "P1314", "Wikidata/QLever — nombre de travées P1314 (dénombrement)", 1, 15000, "physique", "compte"),
    ("hauteur_pyramide",    "Q12516",  "P2048", _SRC.format(p="hauteur P2048"), 1, 160, "physique", "unite"),
    # patron DENSITÉ (nouveau, →kg/m³) : masse volumique d'entité chimique
    ("densite_chimie",      "Q113145171", "P2054", "Wikidata/QLever — masse volumique P2054 (→ kg/m³)", 1, 30000, "physique", "densite"),
    # patron TEMPÉRATURE (nouveau, →K affine) : point de fusion d'entité chimique
    ("point_fusion_chimie", "Q113145171", "P2101", "Wikidata/QLever — point de fusion P2101 (°C/°F→K affine)", 50, 6000, "physique", "temperature"),
    ("point_ebullition_chimie", "Q113145171", "P2102", "Wikidata/QLever — point d'ébullition P2102 (°C/°F→K affine)", 50, 6000, "physique", "temperature"),
    ("point_eclair_chimie", "Q113145171", "P2128", "Wikidata/QLever — point d'éclair P2128 (°C/°F→K affine)", 100, 700, "physique", "temperature"),
    # pKa : constante d'acidité (sans dimension) — mode compte (lit le float, dedup EXACT → polyprotiques/multi-source HORS)
    ("pKa_chimie",          "Q113145171", "P1117", "Wikidata/QLever — constante d'acidité pKa P1117 (sans dimension)", -15, 60, "physique", "compte"),
    # patron MM (nouveau) : diamètre de pièce de monnaie (gardé en mm)
    ("diametre_piece_monnaie", "Q113813711", "P2386", "Wikidata/QLever — diamètre P2386 (en mm)", 1, 200, "physique", "mm"),
    ("masse_piece_monnaie", "Q113813711", "P2067", "Wikidata/QLever — masse P2067 (en g)", 0.1, 2000, "physique", "gramme"),
    # patron DALTON (nouveau) : masse moléculaire d'entité chimique (gardée en Da)
    ("masse_moleculaire",   "Q113145171", "P2067", "Wikidata/QLever — masse moléculaire P2067 (en dalton)", 1, 1e7, "physique", "dalton"),
    # DIMENSIONS d'œuvres (mesure numérique, coordonné T5) : hauteur/largeur de tableaux (cm→m)
    ("hauteur_peinture",    "Q3305213", "P2048", _SRC.format(p="hauteur P2048"), 0.01, 25, "physique", "unite"),
    ("largeur_peinture",    "Q3305213", "P2049", _SRC.format(p="largeur P2049"), 0.01, 30, "physique", "unite"),
    ("hauteur_sculpture",   "Q860861",  "P2048", _SRC.format(p="hauteur P2048"), 0.01, 200, "physique", "unite"),
    ("hauteur_dessin",      "Q93184",   "P2048", _SRC.format(p="hauteur P2048"), 0.01, 5, "physique", "unite"),
    ("largeur_dessin",      "Q93184",   "P2049", _SRC.format(p="largeur P2049"), 0.01, 5, "physique", "unite"),
    ("hauteur_estampe",     "Q11835431", "P2048", _SRC.format(p="hauteur P2048"), 0.01, 5, "physique", "unite"),
    ("largeur_estampe",     "Q11835431", "P2049", _SRC.format(p="largeur P2049"), 0.01, 5, "physique", "unite"),
    ("hauteur_aquarelle",   "Q18761202", "P2048", _SRC.format(p="hauteur P2048"), 0.01, 5, "physique", "unite"),
    ("largeur_aquarelle",   "Q18761202", "P2049", _SRC.format(p="largeur P2049"), 0.01, 5, "physique", "unite"),
    # superset cours d'eau (Q355304 ⊃ fleuve Q4022) : capte ruisseaux/rivières/canaux en + des fleuves
    ("longueur_cours_eau",  "Q355304", "P2043", _SRC.format(p="longueur P2043"), 1, 7_000_000, "physique", "unite"),
    # patron TEMPS (nouveau, →s) : demi-vie d'isotope
    ("demi_vie_isotope",    "Q25276",  "P2114", "Wikidata/QLever — demi-vie P2114 (unité de temps lue puis convertie en secondes ; an julien/jour/h/min/sous-multiples exacts)", 0, 1e40, "physique", "temps"),
    ("longueur_glacier",    "Q35666",  "P2043", _SRC.format(p="longueur P2043"), 1, 600_000, "physique", "unite"),
    # --- lot 7 : NOUVEAUX PATRONS — puissance (→ MW) et masse (→ kg) ---
    ("puissance_centrale_hydro", "Q15911738", "P2109", "Wikidata/QLever — puissance installée P2109 (→ MW ; hydro hors Q159719, lacune P279*)", 0.1, 30000, "physique", "puissance"),
    ("puissance_centrale_solaire", "Q1003207", "P2109", "Wikidata/QLever — puissance installée P2109 (→ MW ; solaire PV)", 0.1, 5000, "physique", "puissance"),
    ("puissance_parc_eolien", "Q50687555", "P2109", "Wikidata/QLever — puissance installée P2109 (→ MW ; parc éolien terrestre)", 0.1, 3000, "physique", "puissance"),
    ("puissance_centrale_charbon", "Q6558431", "P2109", "Wikidata/QLever — puissance installée P2109 (→ MW ; centrale au charbon)", 1, 8000, "physique", "puissance"),
    ("puissance_centrale",  "Q159719", "P2109", "Wikidata/QLever — puissance installée P2109 (→ MW ; W/kW/MW/GW"
     "convertis exacts ; puissance apparente kVA/MVA exclue)", 0, 30_000, "physique", "puissance"),
    ("masse_vehicule_spatial", "Q40218", "P2067", "Wikidata/QLever — masse P2067 (→ kg ; kg/t/g/livre exacts)",
     0, 500_000, "physique", "masse"),
    # --- lot 8 : diamètre de cratère (→ m), débit de fleuve (→ m³/s), capacité de stade (compte) ---
    ("diametre_cratere",    "Q55818",  "P2386", _SRC.format(p="diamètre P2386"), 1, 3_000_000, "physique", "unite"),
    ("debit_fleuve",        "Q4022",   "P2225", "Wikidata/QLever — débit P2225 (→ m³/s)", 0, 300_000, "physique", "debit"),
    ("capacite_stade",      "Q483110", "P1083", "Wikidata/QLever — capacité maximale P1083 (places ; dénombrement)",
     0, 300_000, "physique", "compte"),
    # --- lot 9 : hauteur de pont (→ m), superficie d'aire protégée (→ km²), nombre d'étages (compte) ---
    ("hauteur_pont",        "Q12280",  "P2048", _SRC.format(p="hauteur P2048"), 1, 400, "physique", "unite"),
    ("superficie_aire_protegee", "Q473972", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 3_000_000, "physique", "aire"),
    ("nombre_etages",       "Q41176",  "P1101", "Wikidata/QLever — nombre d'étages P1101 (dénombrement ; bâtiment, superset ⊃ gratte-ciel)", 1, 200, "physique", "compte"),
    # --- lot 10 : ÉLARGISSEMENT DE CLASSES sur le patron longueur (→ m) ---
    ("altitude_lac",        "Q23397",  "P2044", _SRC.format(p="altitude P2044"), -500, 6000, "physique", "unite"),
    ("hauteur_immeuble",    "Q41176",  "P2048", _SRC.format(p="hauteur P2048"), 1, 1000, "physique", "unite"),
    ("hauteur_volcan",      "Q8072",   "P2044", _SRC.format(p="altitude P2044"), -500, 9000, "physique", "unite"),
    ("hauteur_arbre",       "Q10884",  "P2048", _SRC.format(p="hauteur P2048"), 1, 130, "physique", "unite"),
    # --- lot 11 : encore des classes physiques distinctes (longueur→m, aire→km²) ---
    ("altitude_col",        "Q133056", "P2044", _SRC.format(p="altitude P2044"), -500, 9000, "physique", "unite"),
    ("hauteur_colline",     "Q54050",  "P2044", _SRC.format(p="altitude P2044"), -500, 9000, "physique", "unite"),
    ("superficie_foret",    "Q4421",   "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 3_000_000, "physique", "aire"),
    ("superficie_glacier",  "Q35666",  "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 3_000_000, "physique", "aire"),
    # --- lot 12 : sommets (m), capacité de salle (compte), aire d'aéroport (km²) ---
    ("altitude_sommet",     "Q207326", "P2044", _SRC.format(p="altitude P2044"), -500, 9000, "physique", "unite"),
    ("capacite_salle",      "Q24354",  "P1083", "Wikidata/QLever — capacité P1083 (places ; dénombrement)", 1, 100_000, "physique", "compte"),
    ("capacite_eglise",     "Q16970",  "P1083", "Wikidata/QLever — capacité P1083 (places ; église, hors Q24354)", 1, 100_000, "physique", "compte"),
    ("superficie_aeroport", "Q1248784", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 1000, "physique", "aire"),
    # --- lot 13 : altitude des localités (Q486972, superset de ville, ~133k) + travée de pont (P2787, span) ---
    ("altitude_localite",   "Q486972", "P2044", _SRC.format(p="altitude P2044"), -500, 6000, "physique", "unite"),
    ("travee_pont",         "Q12280",  "P2787", _SRC.format(p="travée principale P2787"), 1, 4000, "physique", "unite"),
    # --- lot 14 : mesures numériques sur la classe gare Q55488 (annoncé à T11 ; numérique ≠ leur catégoriel) ---
    ("altitude_gare",       "Q55488",  "P2044", _SRC.format(p="altitude P2044"), -500, 6000, "physique", "unite"),
    ("nombre_quais_gare",   "Q55488",  "P1103", "Wikidata/QLever — nombre de voies à quai P1103 (dénombrement)", 1, 100, "physique", "compte"),
    # --- lot 15 : structures de loisir (montagnes russes, →m) ---
    ("hauteur_montagnes_russes", "Q204832", "P2048", _SRC.format(p="hauteur P2048"), 1, 200, "physique", "unite"),
    ("longueur_montagnes_russes", "Q204832", "P2043", _SRC.format(p="longueur P2043"), 1, 3000, "physique", "unite"),
    # --- lot 16 : hauteur de structure (Q811979 = superset le plus large des structures, →m) ---
    ("hauteur_structure",   "Q811979", "P2048", _SRC.format(p="hauteur P2048"), 1, 1000, "physique", "unite"),
    # --- lot 17 : largeur (nouvelle dimension, →m) + effectif scolaire (compte) ---
    ("largeur_navire",      "Q11446",  "P2049", _SRC.format(p="largeur P2049"), 1, 80, "physique", "unite"),
    ("largeur_pont",        "Q12280",  "P2049", _SRC.format(p="largeur P2049"), 1, 100, "physique", "unite"),
    ("hauteur_eglise",      "Q16970",  "P2048", _SRC.format(p="hauteur P2048"), 5, 180, "physique", "unite"),
    # patron VOLUME (nouveau, ->m³) : capacité de réservoir/lac de barrage
    ("capacite_reservoir",  "Q131681", "P2234", _SRC.format(p="capacité/volume P2234"), 1, 2e11, "physique", "volume"),
    ("volume_lac",          "Q23397",  "P2234", _SRC.format(p="capacité/volume P2234"), 1, 1e17, "physique", "volume"),
    # grottes (unité-aware : seules les déclarations à unité explicite ; nombres nus DIFFÉRÉS = sound)
    ("largeur_route",       "Q34442",  "P2049", _SRC.format(p="largeur P2049"), 1, 300, "physique", "unite"),
    ("diametre_telescope",  "Q4213",   "P2386", _SRC.format(p="diamètre P2386"), 0.1, 45, "physique", "unite"),
    ("longueur_grotte",     "Q35509",  "P2043", _SRC.format(p="longueur P2043"), 1, 1e6, "physique", "unite"),
    ("profondeur_grotte",   "Q35509",  "P4511", _SRC.format(p="profondeur P4511"), 1, 2500, "physique", "unite"),
    ("nombre_eleves",       "Q3914",   "P2196", "Wikidata/QLever — nombre d'élèves/étudiants P2196 (dénombrement)", 1, 200_000, "physique", "compte"),
    # nombre de cylindres (P1100) : compte borné [1,48], multi-classe (moteurs/locomotives/autos/marins) -> snapshot
    # _raw/nombre_cylindres.json class-free pré-construit, _pull_compte le relit offline (classe Q44167 = doc). multi -> HORS.
    ("nombre_cylindres",    "Q44167",  "P1100", "Wikidata/QLever — nombre de cylindres P1100 (dénombrement ; snapshot class-free)", 1, 48, "physique", "compte"),
    # tonnage brut (P1093) : nombre SANS unité (jauge brute des navires) ; plage [1,600000] exclut les navires de guerre
    # à 0 (mesurés en déplacement, pas en GT). snapshot _raw/tonnage_brut.json class-free, multi -> HORS.
    ("tonnage_brut",        "Q11446",  "P1093", "Wikidata/QLever — tonnage brut P1093 (jauge ; dénombrement ; snapshot class-free)", 1, 600_000, "physique", "compte"),
    # longueur de ligne ferroviaire (P2043, UNITÉ-AWARE → m) : orphelin transport T11 ; unités explicites km/m/pied
    # converties (mille/verste/li hors UNITES_METRE -> ignorés = sound) ; snapshot psv: pré-construit ; multi/désaccord -> HORS.
    ("longueur_ligne_ferroviaire", "Q728937", "P2043", "Wikidata/QLever — longueur P2043 d'une ligne ferroviaire (→ m)", 100, 10_000_000, "physique", "unite"),
    # longueur de route (P2043, UNITÉ-AWARE → m) : orphelin transport T11 (≠ pays_route de T1) ; km/m/pied convertis,
    # mille hors table -> ignoré=sound ; snapshot psv: ; multi/désaccord -> HORS. ~12000 faits.
    ("longueur_route",      "Q34442",  "P2043", "Wikidata/QLever — longueur P2043 d'une route (→ m)", 10, 30_000_000, "physique", "unite"),
    # longueur tunnel/canal (P2043, UNITÉ-AWARE → m) : le « différé unité-nue » était OBSOLÈTE — unités explicites
    # (mètre dominant + km/pied) ; orphelins T11 (≠ pays_/exploitant_ existants) ; snapshot psv: ; multi/désaccord -> HORS.
    ("longueur_tunnel",     "Q44377",  "P2043", "Wikidata/QLever — longueur P2043 d'un tunnel (→ m)", 10, 200_000, "physique", "unite"),
    ("longueur_canal",      "Q12284",  "P2043", "Wikidata/QLever — longueur P2043 d'un canal (→ m)", 10, 2_000_000, "physique", "unite"),
    # longueur sentier (P2043, UNITÉ-AWARE → m) : sentiers de randonnée Q628179 (classe propre, vérifiée non-polluée) ;
    # ⚠️ piste_cyclable Q1311670 REJETÉE = closure P279* polluée par des voies FERRÉES (non-sound). snapshot psv:.
    ("longueur_sentier",    "Q628179", "P2043", "Wikidata/QLever — longueur P2043 d'un sentier de randonnée (→ m)", 10, 20_000_000, "physique", "unite"),
    # longueur aqueduc (P2043, UNITÉ-AWARE → m) : aqueducs/tunnels d'eau Q474 ; classe propre ; snapshot psv:.
    ("longueur_aqueduc",    "Q474",    "P2043", "Wikidata/QLever — longueur P2043 d'un aqueduc (→ m)", 10, 500_000, "physique", "unite"),
    # tirant d'eau d'un navire (P2262, UNITÉ-AWARE → m) : orphelin T11 ; mètre/pied ; snapshot psv: ; multi/désaccord -> HORS.
    ("tirant_eau_navire",   "Q11446",  "P2262", "Wikidata/QLever — tirant d'eau P2262 d'un navire (→ m)", 0.2, 40, "physique", "unite"),
    # plus longue travée d'un pont (P2787, UNITÉ-AWARE → m) : mesure d'ingénierie ; mètre/pied ; snapshot psv: ; multi -> HORS.
    ("plus_longue_travee_pont", "Q12280", "P2787", "Wikidata/QLever — plus longue travée P2787 d'un pont (→ m)", 1, 5000, "physique", "unite"),
    # longueur de crête d'un barrage (P2043 sur Q12323, UNITÉ-AWARE → m ; ≠ hauteur_barrage) ; ancres Hoover 379/Trois-Gorges 2335.
    ("longueur_crete_barrage", "Q12323", "P2043", "Wikidata/QLever — longueur de crête P2043 d'un barrage (→ m)", 5, 20000, "physique", "unite"),
    # --- lot 18 : superficie des localités (Q486972, P2046 unité-portée ≠ superficie_lac nu ; ~79k) ---
    ("superficie_localite", "Q486972", "P2046", "Wikidata/QLever — superficie P2046 (→ km²)", 0, 200_000, "physique", "aire"),
    # --- lot 19 : nombre de lits d'hôpital (compte) ---
    ("nombre_lits_hopital", "Q16917",  "P6801", "Wikidata/QLever — nombre de lits P6801 (dénombrement)", 1, 20_000, "physique", "compte"),
    # --- lot 20 : hauteur du plan focal d'un phare (P2923, mesure de navigation ≠ hauteur de tour) ---
    ("hauteur_focale_phare", "Q39715", "P2923", _SRC.format(p="hauteur focale P2923"), 1, 500, "physique", "unite"),
    # DIFFÉRÉ longueur_tunnel/canal (Q44377/Q12284 P2043) + superficie_lac (Q23397 P2046) : statements SANS unité
    # (nombres nus) -> indissociable m/km -> FAUX possible. L'unité-aware n'aide pas sans unité explicite.
    # DIFFÉRÉ envergure_avion/longueur_avion (Q11436 P2050/P2043) : n~100, ancres fr introuvables, et A320
    # « longueur » P2043 = 35,75 ≈ envergure 35,8 -> confusion length/wingspan possible dans Wikidata. Doute -> HORS.
    # --- lot 3 (compte sans unité) ---
    ("population_ville",    "Q515",    "P1082", "Wikidata/QLever — population P1082 (rang préféré/truthy ; "
     "dénombrement, valeur datée pouvant évoluer)", 0, 40_000_000, "physique", "compte"),
    # --- lot 21 : nombre de locuteurs d'une langue (compte ; veine orpheline ex-T9, couloir fermé) ---
    # P1098 multi-valué (L1/total/recensements) -> fonctionnel par libellé : langue à 1 seule valeur gardée,
    # multi-valeur (français, allemand…) -> HORS. Plage [1, 2e9] exclut les 0 (langues éteintes) et le bruit.
    ("nombre_locuteurs_langue", "Q34770", "P1098", "Wikidata/QLever — nombre de locuteurs P1098 (dénombrement, "
     "valeur datée ; multi-valeur->HORS)", 1, 2_000_000_000, "physique", "compte"),
    # --- lot 22 : vitesse maximale d'un véhicule (km/h ; nouveau patron VITESSE, orpheline ex-T11) ---
    # P2052 unité-aware : nœud/mph/m·s⁻¹/km·s⁻¹ -> km/h (facteurs exacts) ; Mach ignoré (pas de facteur fixe).
    ("vitesse_max_vehicule", "Q42889", "P2052", "Wikidata/QLever — vitesse maximale P2052 (unité lue puis "
     "convertie en km/h ; nœud/mph exacts)", 1, 12_000, "physique", "vitesse"),
    # --- lot 23 : masse d'un véhicule (kg ; _pull_masse existant, orpheline ex-T11) ---
    # P2067 unité-aware kg/tonne/gramme/livre ; tonneau(jauge)/m³(volume)/port-en-lourd(capacité) hors table->ignorés.
    # Souvent multi-valeur (à vide/en charge/déplacement) -> fonctionnel à tolérance -> HORS (sound).
    ("masse_vehicule", "Q42889", "P2067", "Wikidata/QLever — masse P2067 (unité lue puis convertie en kg ; "
     "tonne exacte)", 1, 1_000_000_000, "physique", "masse"),
    # --- lot 24 : fréquence d'émission d'une station de radio (MHz ; NOUVEAU patron FRÉQUENCE) ---
    # P2144 unité-aware MHz/kHz/Hz->MHz ; homonymes (mêmes noms, fréquences ≠) -> désaccord -> HORS (sound).
    # Plage [0.01, 2000] MHz couvre AM(~0.5)/FM(87.5-108)/DAB(~230) ; parasites hors-table->ignorés.
    ("frequence_station_radio", "Q14350", "P2144", "Wikidata/QLever — fréquence P2144 (unité lue puis convertie "
     "en MHz ; kHz/Hz exacts)", 0.01, 300, "physique", "frequence"),
    # --- lot 25 : tension nominale d'un poste électrique (kV ; NOUVEAU patron TENSION) ---
    # P2436 unité-aware volt/kilovolt->kV ; poste multi-tension (plusieurs niveaux) -> désaccord -> HORS (sound).
    # Plage [0.1, 1200] kV couvre distribution(~0.4)/transport(63-400)/UHV(~1100).
    ("tension_poste_electrique", "Q174814", "P2436", "Wikidata/QLever — tension nominale P2436 (unité lue puis "
     "convertie en kV ; volt exact)", 0.1, 1200, "physique", "tension"),
    # --- lot 26 : capacité en passagers d'un navire (compte de personnes ; unité-filtré passagers) ---
    # P1083 capacité : on ne garde QUE les unités-personnes (passager/être humain/personne) ; TEU/voitures/« 1 »->ignorés.
    ("capacite_passagers_navire", "Q11446", "P1083", "Wikidata/QLever — capacité P1083 filtrée unités-personnes "
     "(passagers ; TEU/voitures exclus)", 1, 10_000, "physique", "passagers"),
    # --- lot 27 : autonomie/distance franchissable d'un véhicule (mètres ; patron AUTONOMIE dédié) ---
    # P2073 range : NM/km/mile/m -> mètres ; nœud(vitesse)/jour(durée)/km²(aire) exclus. Plage [100 m, 100 000 km].
    ("autonomie_vehicule", "Q42889", "P2073", "Wikidata/QLever — autonomie P2073 (unité lue puis convertie en "
     "mètres ; mille nautique/km exacts)", 100, 100_000_000, "physique", "autonomie"),
    # --- lot 28 : nombre total d'exemplaires produits d'un modèle de véhicule (compte) ---
    # P1092 « quantité produite » : total de production (borné, fait historique) ; multi-source -> HORS (compte fonctionnel).
    ("nombre_produit_auto",  "Q3231690", "P1092", "Wikidata/QLever — quantité produite P1092 (modèle d'auto ; hors Q42889, lacune P279*)", 1, 100_000_000, "physique", "compte"),
    ("nombre_produit_navire", "Q559026", "P1092", "Wikidata/QLever — quantité produite P1092 (classe de navire ; hors Q42889)", 1, 10_000, "physique", "compte"),
    ("nombre_produit_vehicule", "Q42889", "P1092", "Wikidata/QLever — quantité produite P1092 (dénombrement "
     "total d'exemplaires)", 1, 200_000_000, "physique", "compte"),
]

# Catégorielles techniques (ensemble fermé) : réutilisent la fabrique générique de IQ.
CATEGORIELLES = [
    ("licence_logiciel", "Q7397", "P275", "Wikidata/QLever — licence (P275) d'un logiciel", "convention"),
    # --- sous-sujet TECHNIQUE-LOGICIEL : langage de programmation (P277) ; multi-langage -> HORS (fonctionnel) ---
    ("langage_programmation_logiciel", "Q7397", "P277",
     "Wikidata/QLever — langage de programmation (P277) d'un logiciel", "convention"),
    # systeme d'exploitation (P306) : OBJET CONTRAINT à être un OS réel (snapshot pré-filtré P31/P279* Q9135) ->
    # exclut « multiplateforme » (attribut de portabilité, PAS un OS) = FAUX évité ; multi-OS -> HORS (fonctionnel).
    ("systeme_exploitation_logiciel", "Q7397", "P306",
     "Wikidata/QLever — système d'exploitation (P306, objet contraint à un OS Q9135) d'un logiciel", "convention"),
    # --- format de fichier (Q235557, artefact technique ≠ œuvre) : valeurs LITTÉRALES, snapshot pré-construit avec
    #     la clé vLabel = le littéral (MIME/extension) -> réutilise _ingere_x_vers_entite offline. multi -> HORS. ---
    ("type_mime_format", "Q235557", "P1163",
     "Wikidata/QLever — type MIME (P1163) d'un format de fichier", "convention"),
    # extension de fichier (P1195) : valeur LITTÉRALE (ex. png, json) -> snapshot pré-construit avec clé vLabel = le
    # littéral -> _ingere_x_vers_entite lit offline. multi-extension -> HORS (fonctionnel). FAUX=0.
    ("extension_format", "Q235557", "P1195",
     "Wikidata/QLever — extension de fichier (P1195) d'un format de fichier", "convention"),
    # --- écartement des rails (P1064, valeur = TYPE d'écartement = entité réelle ; orphelin transport T11 fermé) :
    #     classe_qid=None (P1064 = rail-spécifique, sans ambiguïté) ; snapshot _raw/ecartement_rails.json pré-construit ;
    #     multi-écartement (lignes à voie mixte) -> HORS (fonctionnel). ~10500 faits. ---
    ("ecartement_rails", None, "P1064",
     "Wikidata/QLever — écartement des rails (P1064) d'une infrastructure ferroviaire", "convention"),
    # --- propulsé par (P516, valeur = TYPE de propulsion = entité : moteur à allumage commandé/Diesel/électrique…) ;
    #     orphelin transport T11 ; classe_qid=None ; snapshot _raw/propulse_par.json ; multi-config -> HORS. ~5800 faits. ---
    ("propulse_par", None, "P516",
     "Wikidata/QLever — propulsé par (P516) le type de propulsion d'un véhicule", "convention"),
    # --- source d'énergie (P618, valeur = type d'énergie : solaire/éolien/hydraulique/charbon/gazole/Li-ion…) ;
    #     centrales + dispositifs (T7-technique) ; classe_qid=None ; snapshot _raw/source_energie.json ; multi -> HORS. ---
    ("source_energie", None, "P618",
     "Wikidata/QLever — source d'énergie (P618) d'une centrale ou d'un dispositif", "convention"),
]


def ingere_tout():
    for rel, cls, prop, src, lo, hi, cat, mode in NUMERIQUES:
        ingere_numerique(rel, cls, prop, src, lo, hi, categorie=cat, mode=mode)
    for rel, cls, prop, src, cat in CATEGORIELLES:
        IQ._ingere_x_vers_entite(rel, prop, cat, src, classe_qid=cls)


def sonde():
    """Inspecte chaque veine SANS écrire dans le lecteur : compte, étendue, échantillon -> juger plage/densité."""
    for rel, cls, prop, _src, lo, hi, _cat, mode in NUMERIQUES:
        pull = {"unite": _pull_metres, "compte": _pull_compte, "aire": _pull_aire, "puissance": _pull_puissance, "masse": _pull_masse, "debit": _pull_debit, "vitesse": _pull_vitesse, "frequence": _pull_frequence, "tension": _pull_tension, "passagers": _pull_passagers, "autonomie": _pull_autonomie, "volume": _pull_volume, "temps": _pull_temps, "dalton": _pull_dalton, "mm": _pull_mm, "temperature": _pull_temperature, "gramme": _pull_gramme, "densite": _pull_densite}[mode]
        triples = pull(rel, cls, prop)
        if not triples:
            print(f"  [{rel:20s}] 0 valeur (classe/prop vide ?)")
            continue
        vals = sorted(f for _e, f, _b in triples)
        dans = sum(1 for v in vals if lo <= v <= hi)
        ech = triples[:3]
        print(f"  [{rel:20s}] {mode:6s} n={len(triples):6d}  min={vals[0]:.1f}  max={vals[-1]:.1f}  "
              f"med={vals[len(vals)//2]:.1f}  dans[{lo},{hi}]={dans}  ex={[(e, _fmt(f)) for e, f, _b in ech]}")


def ingere_une(relation):
    """Ingest CHIRURGICAL d'une seule relation (évite de re-traiter les 50 autres)."""
    for rel, cls, prop, src, lo, hi, cat, mode in NUMERIQUES:
        if rel == relation:
            return ingere_numerique(rel, cls, prop, src, lo, hi, categorie=cat, mode=mode)
    for rel, cls, prop, src, cat in CATEGORIELLES:
        if rel == relation:
            return IQ._ingere_x_vers_entite(rel, prop, cat, src, classe_qid=cls)
    raise SystemExit(f"relation inconnue: {relation}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sonde":
        sonde()
    elif len(sys.argv) > 2 and sys.argv[1] == "one":
        # plusieurs relations -> ingérées dans LE MÊME process (un seul import lecteur amorti). Ordre = args.
        for _rel in sys.argv[2:]:
            ingere_une(_rel)
    else:
        ingere_tout()
