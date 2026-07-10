"""
VALIDE calendriers.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs tabulées, PAS recalculées par les fonctions testées) :
  • JDN(1er janvier 2000 grégorien) = 2451545 — époque astronomique J2000, universellement tabulée.
  • JDN(1er janvier 1970 grégorien) = 2440588 — époque Unix, tabulée partout.
  • Réforme grégorienne : le 4 octobre 1582 (julien, JDN 2299160) et le 15 octobre 1582 (grégorien,
    JDN 2299161) sont des jours CONSÉCUTIFS de l'histoire — ancre historique forte. Le 4 oct 1582 était
    un JEUDI, le 15 oct 1582 un VENDREDI (fait historique documenté).
  • 1 Muharram 1 AH (hijri tabulaire, époque civile) = JDN 1948440 = vendredi 16 juillet 622 JULIEN
    (Explanatory Supplement). Cycle tabulaire de 30 ans = 10631 jours = 30·354 + 11 (constante documentée).
  • Bissextiles discriminantes : 2000 OUI / 1900 NON en grégorien (règle des 400) ; 1900 OUI en julien
    (la règle naïve /4 échouerait sur 1900 grégorien).
  • Jours de semaine connus : 1 jan 2000 = SAMEDI ; 1 jan 1970 = JEUDI (faits documentés).
  • Écart julien->grégorien : 10 jours en 1582, 13 en 1900 et 2000, 14 en 2100 (valeurs classiques) ;
    second chemin de code indépendant dans la gate : ecart = c - c//4 - 2 avec c = annee//100 (dérive
    de 3 jours par 400 ans, calcul à la main).
  • BOUCLE FERMÉE : jdn_vers_x(x_vers_jdn(date)) == date pour 2000 dates balayées 1600-2400 (grégorien),
    plus balayages julien et hijri ; et continuité JDN jour par jour sur des années charnières.

SOUNDNESS : 30 février, mois 13, jour 0, 29 fév non bissextile, année 0, bool/float/str/NaN/inf,
JDN hors domaine, fuseau régional, heure hors bornes -> ValueError. heure_ete -> ValueError TOUJOURS.
"""
import math

import calendriers as C

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


# ── 1) ANCRES JDN TABULÉES (grégorien) ──
check(C.gregorien_vers_jdn(2000, 1, 1) == 2451545, "JDN(2000-01-01 grég) = 2451545 (J2000)")
check(C.gregorien_vers_jdn(1970, 1, 1) == 2440588, "JDN(1970-01-01 grég) = 2440588 (époque Unix)")
check(C.jdn_vers_gregorien(2451545) == (2000, 1, 1), "JDN 2451545 -> 2000-01-01 grég")
check(C.jdn_vers_gregorien(2440588) == (1970, 1, 1), "JDN 2440588 -> 1970-01-01 grég")

# ── 2) ANCRE HISTORIQUE : réforme de 1582, jours consécutifs ──
jdn_dernier_julien = C.julien_vers_jdn(1582, 10, 4)
jdn_premier_gregorien = C.gregorien_vers_jdn(1582, 10, 15)
check(jdn_dernier_julien == 2299160, "JDN(4 oct 1582 julien) = 2299160 (tabulé)")
check(jdn_premier_gregorien == 2299161, "JDN(15 oct 1582 grég) = 2299161 (tabulé)")
check(jdn_premier_gregorien - jdn_dernier_julien == 1, "4 oct 1582 (julien) et 15 oct 1582 (grég) CONSÉCUTIFS")
check(C.jdn_vers_julien(2299160) == (1582, 10, 4), "JDN 2299160 -> 4 oct 1582 julien")
check(C.jdn_vers_gregorien(2299161) == (1582, 10, 15), "JDN 2299161 -> 15 oct 1582 grég")

# ── 3) ANCRE JULIEN <-> GRÉGORIEN sur une même date nominale ──
# 1 juin 1582 : julien = grégorien + 10 jours de JDN (l'écart de la réforme)
check(C.julien_vers_jdn(1582, 6, 1) - C.gregorien_vers_jdn(1582, 6, 1) == 10,
      "1 juin 1582 : JDN julien - JDN grég = 10")

# ── 4) BISSEXTILES DISCRIMINANTES (la règle naïve /4 échouerait) ──
check(C.est_bissextile_gregorien(2000) is True, "2000 bissextile grég (divisible 400)")
check(C.est_bissextile_gregorien(1900) is False, "1900 NON bissextile grég (siècle non /400)")
check(C.est_bissextile_gregorien(2100) is False, "2100 NON bissextile grég")
check(C.est_bissextile_gregorien(1600) is True, "1600 bissextile grég")
check(C.est_bissextile_gregorien(2024) is True, "2024 bissextile grég")
check(C.est_bissextile_gregorien(2023) is False, "2023 NON bissextile grég")
check(C.est_bissextile_julien(1900) is True, "1900 EST bissextile julien (règle /4)")
check(C.est_bissextile_julien(2100) is True, "2100 bissextile julien")
check(C.est_bissextile_julien(2023) is False, "2023 NON bissextile julien")
# Conséquence sur les dates : 29 fév 2000 grég OK, 29 fév 1900 grég REFUSÉ, 29 fév 1900 julien OK
check(C.gregorien_vers_jdn(2000, 2, 29) == 2451545 + 59, "29 fév 2000 grég = JDN 2451604 (59 j après le 1 jan)")
check(leve(C.gregorien_vers_jdn, 1900, 2, 29), "29 fév 1900 grég -> ValueError (non bissextile)")
check(C.julien_vers_jdn(1900, 2, 29) == C.julien_vers_jdn(1900, 3, 1) - 1, "29 fév 1900 julien existe")

# ── 5) JOUR DE LA SEMAINE (faits historiques documentés) ──
check(C.jour_semaine(2451545) == "samedi", "1 jan 2000 = SAMEDI")
check(C.jour_semaine(2440588) == "jeudi", "1 jan 1970 = JEUDI")
check(C.jour_semaine(2299160) == "jeudi", "4 oct 1582 (julien) = JEUDI (historique)")
check(C.jour_semaine(2299161) == "vendredi", "15 oct 1582 (grég) = VENDREDI (historique)")
check(C.jour_semaine(1948440) == "vendredi", "1 Muharram 1 AH = VENDREDI (époque civile)")
check(C.jour_semaine(2440588 + 7) == "jeudi", "période 7 : +7 jours = même jour de semaine")

# ── 6) HIJRI TABULAIRE : époque + constantes de cycle documentées ──
check(C.hijri_vers_jdn(1, 1, 1) == 1948440, "1 Muharram 1 AH -> JDN 1948440 (époque civile tabulée)")
check(C.jdn_vers_hijri(1948440) == (1, 1, 1), "JDN 1948440 -> 1/1/1 AH")
check(C.julien_vers_jdn(622, 7, 16) == 1948440, "16 juillet 622 JULIEN = époque hijri (Explanatory Suppl.)")
# Cycle de 30 ans = 10631 jours (constante documentée : 30*354 + 11 abondantes = 10620 + 11)
check(C.hijri_vers_jdn(31, 1, 1) - C.hijri_vers_jdn(1, 1, 1) == 10631, "cycle 30 ans hijri = 10631 jours")
# Années 1 (commune) et 2 (abondante) : longueurs 354 / 355 (intercalation type II documentée)
check(C.hijri_vers_jdn(2, 1, 1) - C.hijri_vers_jdn(1, 1, 1) == 354, "an 1 AH commun = 354 jours")
check(C.hijri_vers_jdn(3, 1, 1) - C.hijri_vers_jdn(2, 1, 1) == 355, "an 2 AH abondant = 355 jours")
# Ensemble complet des abondantes du cycle {2,5,7,10,13,16,18,21,24,26,29} (écrit EN DUR, documenté)
abondantes_calc = tuple(a for a in range(1, 31) if C.est_abondante_hijri(a))
check(abondantes_calc == (2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29),
      "abondantes du cycle = {2,5,7,10,13,16,18,21,24,26,29}")
# Mois : Muharram 30 j, Safar 29 j (alternance documentée) ; Dhou al-hijja 30 j si abondante
check(C.hijri_vers_jdn(1, 2, 1) - C.hijri_vers_jdn(1, 1, 1) == 30, "Muharram = 30 jours")
check(C.hijri_vers_jdn(1, 3, 1) - C.hijri_vers_jdn(1, 2, 1) == 29, "Safar = 29 jours")
check(C.hijri_vers_jdn(2, 12, 30) == C.hijri_vers_jdn(3, 1, 1) - 1, "Dhou al-hijja an 2 (abondant) a 30 j")
check(leve(C.hijri_vers_jdn, 1, 12, 30), "30 Dhou al-hijja an 1 (commun) -> ValueError")

# ── 7) BOUCLE FERMÉE grégorien : 2000 dates balayées 1600-2400 ──
rates = 0
for i in range(2000):
    a = 1600 + (i * 801) // 2000          # couvre 1600..2400
    m = 1 + (i * 7) % 12
    j = 1 + (i * 11) % 28                 # 1..28 : valide dans tout mois
    if C.jdn_vers_gregorien(C.gregorien_vers_jdn(a, m, j)) != (a, m, j):
        rates += 1
check(rates == 0, f"boucle fermée grég 2000 dates 1600-2400 ({rates} ratés)")

# ── 8) BOUCLE FERMÉE julien et hijri (balayages) ──
rates = 0
for i in range(500):
    a = 100 + (i * 1900) // 500
    m = 1 + (i * 5) % 12
    j = 1 + (i * 13) % 28
    if C.jdn_vers_julien(C.julien_vers_jdn(a, m, j)) != (a, m, j):
        rates += 1
check(rates == 0, f"boucle fermée julien 500 dates ({rates} ratés)")
rates = 0
for i in range(500):
    a = 1 + (i * 1500) // 500
    m = 1 + (i * 5) % 12
    j = 1 + (i * 13) % 29                 # 1..29 mais jours pairs>29 impossibles : rester <= 29
    j = min(j, 29 if m % 2 == 0 else 30)
    if C.jdn_vers_hijri(C.hijri_vers_jdn(a, m, j)) != (a, m, j):
        rates += 1
check(rates == 0, f"boucle fermée hijri 500 dates ({rates} ratés)")

# ── 9) CONTINUITÉ : le JDN croît de 1 jour par jour sur des années charnières ──
rates = 0
for annee in (1900, 2000):                # non-bissextile ET bissextile grégoriennes
    prec = C.gregorien_vers_jdn(annee, 1, 1)
    for m in range(1, 13):
        for j in range(1, 32):
            if (annee, m, j) == (annee, 1, 1):
                continue
            try:
                cur = C.gregorien_vers_jdn(annee, m, j)
            except ValueError:
                continue                  # jour inexistant (31 avril, 29-30 fév...)
            if cur != prec + 1:
                rates += 1
            prec = cur
check(rates == 0, f"continuité JDN jour par jour 1900+2000 grég ({rates} ruptures)")
# nb de jours des années : 1900 grég = 365, 2000 grég = 366 (calcul à la main)
check(C.gregorien_vers_jdn(1901, 1, 1) - C.gregorien_vers_jdn(1900, 1, 1) == 365, "1900 grég = 365 jours")
check(C.gregorien_vers_jdn(2001, 1, 1) - C.gregorien_vers_jdn(2000, 1, 1) == 366, "2000 grég = 366 jours")
check(C.julien_vers_jdn(1901, 1, 1) - C.julien_vers_jdn(1900, 1, 1) == 366, "1900 julien = 366 jours")

# ── 10) ÉCART JULIEN/GRÉGORIEN : ancres classiques + second chemin de code ──
check(C.ecart_julien_gregorien(1582) == 10, "écart 1582 = 10 jours (réforme)")
check(C.ecart_julien_gregorien(1900) == 13, "écart 1900 = 13 jours")
check(C.ecart_julien_gregorien(2000) == 13, "écart 2000 = 13 jours")
check(C.ecart_julien_gregorien(2100) == 14, "écart 2100 = 14 jours")
check(C.ecart_julien_gregorien(1700) == 11, "écart 1700 = 11 jours (Grande-Bretagne 1752 : 11 j)")
# Second chemin INDÉPENDANT : dérive séculaire c - c//4 - 2 (3 jours par 400 ans, calcul à la main)
rates = 0
for annee in range(300, 2500, 37):
    c = annee // 100
    if C.ecart_julien_gregorien(annee) != c - c // 4 - 2:
        rates += 1
check(rates == 0, f"écart == c - c//4 - 2 sur 300-2500 ({rates} ratés)")

# ── 11) FUSEAUX À OFFSET FIXE ──
check(C.decalage_utc("UTC") == 0, "UTC = 0 min")
check(C.decalage_utc("UTC+1") == 60, "UTC+1 = +60 min")
check(C.decalage_utc("UTC-12") == -720, "UTC-12 = -720 min")
check(C.decalage_utc("UTC+14") == 840, "UTC+14 = +840 min")
check(C.decalage_utc("UTC+5:30") == 330, "UTC+5:30 = +330 min (5*60+30, calcul à la main)")
check(C.decalage_utc("UTC+5:45") == 345, "UTC+5:45 = +345 min")
check(C.decalage_utc("UTC-9:30") == -570, "UTC-9:30 = -570 min")
# heure_locale : 12:00 UTC en UTC+1 -> 13:00 même jour (720+60=780)
check(C.heure_locale(720, 60) == (780, 0), "12:00 UTC + UTC+1 = 13:00 même jour")
# 23:30 UTC en UTC+1 -> 00:30 LENDEMAIN (1410+60=1470 -> 30, report +1)
check(C.heure_locale(1410, 60) == (30, 1), "23:30 UTC + UTC+1 = 00:30 lendemain")
# 00:15 UTC en UTC-5 -> 19:15 la VEILLE (15-300=-285 -> 1155, report -1)
check(C.heure_locale(15, -300) == (1155, -1), "00:15 UTC + UTC-5 = 19:15 veille")
# 12:00 UTC en UTC+14 -> 02:00 lendemain (720+840=1560 -> 120, +1)
check(C.heure_locale(720, 840) == (120, 1), "12:00 UTC + UTC+14 = 02:00 lendemain")
check(C.heure_locale(0, 0) == (0, 0), "minuit UTC + UTC = minuit même jour")

# ── 12) ABSTENTION CAPITALE : heure d'été TOUJOURS refusée ──
check(leve(C.heure_ete), "heure_ete() -> ValueError")
check(leve(C.heure_ete, "Europe/Paris", 2026, 7, 10), "heure_ete(zone, date) -> ValueError")
check(leve(C.heure_ete, 720, 60), "heure_ete(minutes, offset) -> ValueError")

# ── 13) SOUNDNESS — dates invalides ──
check(leve(C.gregorien_vers_jdn, 2000, 2, 30), "30 février -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, 13, 1), "mois 13 -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, 0, 1), "mois 0 -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, 1, 0), "jour 0 -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, 1, 32), "32 janvier -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, 4, 31), "31 avril -> ValueError")
check(leve(C.julien_vers_jdn, 1901, 2, 29), "29 fév 1901 julien -> ValueError")
check(leve(C.hijri_vers_jdn, 1, 13, 1), "mois hijri 13 -> ValueError")
check(leve(C.hijri_vers_jdn, 1, 2, 30), "30 Safar (29 j) -> ValueError")
check(leve(C.gregorien_vers_jdn, 0, 1, 1), "année 0 -> ValueError (domaine [1,9999])")
check(leve(C.gregorien_vers_jdn, 10000, 1, 1), "année 10000 -> ValueError")
check(leve(C.hijri_vers_jdn, 0, 1, 1), "année hijri 0 -> ValueError")

# ── 14) SOUNDNESS — types (bool / float / str / NaN / inf) ──
check(leve(C.gregorien_vers_jdn, True, 1, 1), "année bool -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000, True, 1), "mois bool -> ValueError")
check(leve(C.gregorien_vers_jdn, 2000.0, 1, 1), "année float -> ValueError")
check(leve(C.gregorien_vers_jdn, "2000", 1, 1), "année str -> ValueError")
check(leve(C.gregorien_vers_jdn, float("nan"), 1, 1), "année NaN -> ValueError")
check(leve(C.gregorien_vers_jdn, float("inf"), 1, 1), "année inf -> ValueError")
check(leve(C.jdn_vers_gregorien, 2451545.0), "jdn float -> ValueError")
check(leve(C.jdn_vers_gregorien, True), "jdn bool -> ValueError")
check(leve(C.jour_semaine, "2451545"), "jour_semaine str -> ValueError")
check(leve(C.jour_semaine, -1), "jour_semaine jdn négatif -> ValueError")
check(leve(C.est_bissextile_gregorien, True), "bissextile bool -> ValueError")
check(leve(C.est_bissextile_julien, 2000.0), "bissextile float -> ValueError")
check(leve(C.ecart_julien_gregorien, math.nan), "écart NaN -> ValueError")

# ── 15) SOUNDNESS — JDN hors domaine inversible ──
check(leve(C.jdn_vers_gregorien, 0), "jdn 0 -> ValueError (avant l'an 1)")
check(leve(C.jdn_vers_gregorien, 10_000_000), "jdn énorme -> ValueError (après 9999)")
check(leve(C.jdn_vers_julien, 1721423), "jdn < 1/1/1 julien -> ValueError")
check(leve(C.jdn_vers_hijri, 1948439), "jdn < époque hijri -> ValueError")

# ── 16) SOUNDNESS — fuseaux / heures ──
check(leve(C.decalage_utc, "CET"), "fuseau régional CET -> ValueError (DST ambigu)")
check(leve(C.decalage_utc, "EST"), "fuseau régional EST -> ValueError")
check(leve(C.decalage_utc, "UTC+15"), "UTC+15 inexistant -> ValueError")
check(leve(C.decalage_utc, 60), "fuseau non-str -> ValueError")
check(leve(C.heure_locale, 1440, 0), "heure_utc=1440 -> ValueError (hors [0,1439])")
check(leve(C.heure_locale, -1, 0), "heure_utc<0 -> ValueError")
check(leve(C.heure_locale, 720, 7), "décalage non multiple de 15 -> ValueError")
check(leve(C.heure_locale, 720, 900), "décalage > +840 -> ValueError")
check(leve(C.heure_locale, 720.0, 60), "heure float -> ValueError")
check(leve(C.heure_locale, True, 60), "heure bool -> ValueError")

# ── 17) DÉTERMINISME ──
check(C.gregorien_vers_jdn(2000, 1, 1) == C.gregorien_vers_jdn(2000, 1, 1), "déterminisme grégorien")
check(C.jdn_vers_hijri(2459437) == C.jdn_vers_hijri(2459437), "déterminisme hijri inverse")
check(C.jour_semaine(2451545) == C.jour_semaine(2451545), "déterminisme jour_semaine")
check(C.heure_locale(1410, 60) == C.heure_locale(1410, 60), "déterminisme heure_locale")

print(f"\n=== valide_calendriers : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
