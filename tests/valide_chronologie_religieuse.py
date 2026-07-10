"""VALIDE chronologie_religieuse.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (faits historiques universellement établis, écrits EN DUR, PAS recalculés
par le module) :
  • concile de Nicée = 325 (premier concile œcuménique).
  • Hégire = 622 (an 1 du calendrier islamique lunaire).
  • grand schisme d'Orient = 1054.
  • 95 thèses de Luther = 1517.
  • Vatican II = 1962-1965.
  • loi française de séparation des Églises et de l'État = 1905.
  • édit de Milan = 313 ; Chalcédoine = 451 ; prise de Jérusalem = 1099 ; concile de Trente = 1545-1563 ;
    édit de Nantes = 1598 / révocation = 1685 ; Vatican I = 1869-1870.

ANCRES D'ABSTENTION CAPITALES :
  • date('naissance de Jésus') -> ValueError (fait CONTESTÉ) ; dater à l'an 1 serait FAUX.
  • datation_contestee('naissance de Jésus') -> fourchette (−6, −4), raison citant Hérode † −4 / pas d'an 0 /
    25 décembre liturgique.
  • Bouddha : deux chronologies CONCURRENTES -> consensus == False.
  • datation_contestee('concile de Nicée') -> ValueError (événement daté avec certitude).
  • événement inventé -> ValueError.

SOUNDNESS : type invalide (bool/int/None/str vide), hors catalogue, croisement des deux régimes -> ValueError.
DÉTERMINISME : double appel identique.
"""
import chronologie_religieuse as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ══ 1) ÉVÉNEMENTS DATÉS — année certaine confrontée à l'ancre EN DUR ══
check(C.date("concile de Nicée") == 325, "Nicée = 325")
check(C.date("premier concile de Nicée") == 325, "premier concile de Nicée = 325 (alias)")
check(C.date("Hégire") == 622, "Hégire = 622")
check(C.date("grand schisme d'Orient") == 1054, "grand schisme = 1054")
check(C.date("schisme de 1054") == 1054, "schisme (alias) = 1054")
check(C.date("95 thèses") == 1517, "95 thèses = 1517")
check(C.date("95 thèses de Luther") == 1517, "95 thèses de Luther = 1517 (alias)")
check(C.date("loi de séparation des Églises et de l'État") == 1905, "séparation = 1905")
check(C.date("loi de 1905") == 1905, "loi de 1905 (alias) = 1905")
check(C.date("édit de Milan") == 313, "édit de Milan = 313")
check(C.date("concile de Chalcédoine") == 451, "Chalcédoine = 451")
check(C.date("prise de Jérusalem") == 1099, "prise de Jérusalem = 1099")
check(C.date("édit de Nantes") == 1598, "édit de Nantes = 1598")
check(C.date("révocation de l'édit de Nantes") == 1685, "révocation édit de Nantes = 1685")
check(C.date("édit de Fontainebleau") == 1685, "édit de Fontainebleau (alias) = 1685")

# ══ 2) ÉVÉNEMENTS PLURIANNUELS -> (debut, fin) ══
check(C.date("Vatican II") == (1962, 1965), "Vatican II = (1962, 1965)")
check(C.date("concile Vatican II") == (1962, 1965), "concile Vatican II = (1962,1965) (alias)")
check(C.date("concile de Trente") == (1545, 1563), "Trente = (1545, 1563)")
check(C.date("Vatican I") == (1869, 1870), "Vatican I = (1869, 1870)")

# ══ 3) SOURCE présente et non vide, et cohérente ══
check(isinstance(C.source("Hégire"), str) and "622" in C.source("Hégire"), "source Hégire mentionne 622")
check(isinstance(C.source("concile de Nicée"), str) and len(C.source("concile de Nicée")) > 10,
      "source Nicée non vide")
check(isinstance(C.enonce("édit de Nantes"), str) and len(C.enonce("édit de Nantes")) > 5,
      "énoncé édit de Nantes non vide")

# ══ 4) ABSTENTION CAPITALE — naissance de Jésus : date() refuse, datation_contestee() encadre ══
check(leve(C.date, "naissance de Jésus"), "date('naissance de Jésus') -> ValueError (contesté)")
check(leve(C.date, "naissance du Christ"), "date('naissance du Christ') -> ValueError (alias contesté)")
check(leve(C.source, "naissance de Jésus"), "source('naissance de Jésus') -> ValueError")
dc_jesus = C.datation_contestee("naissance de Jésus")
check(dc_jesus["fourchette"] == (-6, -4), "datation_contestee('naissance de Jésus') fourchette = (-6, -4)")
check(dc_jesus["consensus"] is True, "naissance de Jésus : consensus sur la fourchette = True")
# La raison DOIT citer les trois motifs historiques (ancres textuelles non circulaires)
_raison_j = dc_jesus["raison"].lower()
check("herode" in _raison_j or "hérode" in _raison_j or "-4" in _raison_j or "−" in _raison_j,
      "raison Jésus cite Hérode / -4")
check("an 0" in _raison_j or "an zero" in _raison_j, "raison Jésus : pas d'an 0")
check("25 decembre" in _raison_j or "liturgique" in _raison_j, "raison Jésus : 25 décembre liturgique")

# ══ 5) BOUDDHA — deux chronologies concurrentes -> consensus False ══
dc_b = C.datation_contestee("vie du Bouddha")
check(dc_b["consensus"] is False, "Bouddha : consensus = False (chronologies concurrentes)")
check(dc_b["fourchette"][0] < dc_b["fourchette"][1], "Bouddha : fourchette (min < max)")
check(dc_b["fourchette"][0] < 0 and dc_b["fourchette"][1] < 0, "Bouddha : entièrement av. J.-C.")
check(leve(C.date, "vie du Bouddha"), "date('vie du Bouddha') -> ValueError (contesté)")

# ══ 6) AUTRES FAITS CONTESTÉS ══
check(C.datation_contestee("Pentateuque")["fourchette"] == (-900, -400), "Pentateuque = (-900, -400)")
check(C.datation_contestee("Pentateuque")["consensus"] is False, "Pentateuque consensus False")
z = C.datation_contestee("Zoroastre")
check(z["fourchette"][1] - z["fourchette"][0] >= 1000, "Zoroastre : fourchette > un millénaire")
check(z["consensus"] is False, "Zoroastre consensus False")
check(C.datation_contestee("Védas")["fourchette"] == (-1500, -500), "Védas = (-1500, -500)")
check(leve(C.date, "Védas"), "date('Védas') -> ValueError (contesté)")

# ══ 7) CROISEMENT DES DEUX RÉGIMES (abstention structurelle) ══
check(leve(C.datation_contestee, "concile de Nicée"), "datation_contestee('concile de Nicée') -> ValueError")
check(leve(C.datation_contestee, "Hégire"), "datation_contestee('Hégire') -> ValueError (daté)")
check(leve(C.datation_contestee, "Vatican II"), "datation_contestee('Vatican II') -> ValueError (daté)")
check(leve(C.date, "naissance du Bouddha"), "date d'un contesté -> ValueError (bis)")

# ══ 8) HORS CATALOGUE + TYPES INVALIDES -> ValueError ══
check(leve(C.date, "concile de Machin"), "événement inventé -> ValueError")
check(leve(C.date, "réforme grégorienne du calendrier"), "événement hors catalogue -> ValueError")
check(leve(C.datation_contestee, "naissance de Napoléon"), "fait inventé -> ValueError")
check(leve(C.date, ""), "chaîne vide -> ValueError")
check(leve(C.date, "   "), "chaîne blanche -> ValueError")
check(leve(C.date, True), "bool -> ValueError")
check(leve(C.date, 325), "int -> ValueError")
check(leve(C.date, None), "None -> ValueError")
check(leve(C.datation_contestee, False), "datation_contestee(bool) -> ValueError")

# ══ 9) CALENDRIERS RELIGIEUX ══
cal = C.calendriers_religieux()
check(set(cal) == {"ere_chretienne", "hegire", "calendrier_hebraique"}, "3 calendriers présents")
check(cal["ere_chretienne"]["an_zero"] is False, "ère chrétienne : PAS d'an 0")
check(cal["hegire"]["type"] == "lunaire", "Hégire : calendrier lunaire")
check("622" in cal["hegire"]["origine"], "Hégire : origine 622")
check(cal["calendrier_hebraique"]["type"] == "luni-solaire", "hébraïque : luni-solaire")
# Immutabilité : muter la copie ne doit pas contaminer le prochain appel
cal["ere_chretienne"]["an_zero"] = True
check(C.calendriers_religieux()["ere_chretienne"]["an_zero"] is False, "calendriers : copie neuve (immuable)")

# ══ 10) INDEX PAR SIÈCLE (ancres : siècle calculé À LA MAIN, indépendant du module) ══
# 325 -> IVᵉ s. ; 622 -> VIIᵉ s. ; 1517 -> XVIᵉ s. ; 1905 & 1962 -> XXᵉ s. ; 1054 & 1099 -> XIᵉ s.
check("nicee_1" in C.evenements_par_siecle(4), "Nicée dans le IVᵉ siècle")
check("hegire" in C.evenements_par_siecle(7), "Hégire dans le VIIᵉ siècle")
check("theses_luther" in C.evenements_par_siecle(16), "95 thèses dans le XVIᵉ siècle")
check(set(C.evenements_par_siecle(11)) == {"schisme_orient", "prise_jerusalem_croises"},
      "XIᵉ siècle : schisme (1054) + prise de Jérusalem (1099)")
check("separation_eglises_etat" in C.evenements_par_siecle(20)
      and "vatican_ii" in C.evenements_par_siecle(20), "XXᵉ siècle : séparation 1905 + Vatican II 1962")
check(C.evenements_par_siecle(1) == (), "Iᵉ siècle : aucun événement (tuple vide)")
check(leve(C.evenements_par_siecle, 0), "siècle 0 -> ValueError")
check(leve(C.evenements_par_siecle, -4), "siècle négatif -> ValueError")
check(leve(C.evenements_par_siecle, True), "siècle bool -> ValueError")
check(leve(C.evenements_par_siecle, "IV"), "siècle str -> ValueError")

# ══ 11) CATALOGUE / faits_contestes ══
cat = C.catalogue()
check(len(cat) == 13, "catalogue : 13 événements datés")
check("vatican_ii" in cat and "edit_milan" in cat, "catalogue contient Vatican II et édit de Milan")
check(cat == tuple(sorted(cat)), "catalogue trié")
fc = C.faits_contestes()
check(set(fc) == {"naissance_jesus", "bouddha", "pentateuque", "zoroastre", "vedas"},
      "faits_contestes : 5 faits")
# Aucun recoupement entre les deux régimes
check(set(cat).isdisjoint(set(fc)), "datés et contestés disjoints")

# ══ 12) DÉTERMINISME ══
check(C.date("Hégire") == C.date("Hégire"), "déterminisme date")
check(C.datation_contestee("naissance de Jésus") == C.datation_contestee("naissance de Jésus"),
      "déterminisme datation_contestee")
check(C.evenements_par_siecle(11) == C.evenements_par_siecle(11), "déterminisme evenements_par_siecle")

print(f"\n=== valide_chronologie_religieuse : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
