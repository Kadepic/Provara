"""
VALIDE musique_gammes.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT des formules testées) :
  • A4 = 440 Hz EXACTEMENT (norme ISO 16, diapason de concert) ; A5 = 880 Hz (l'octave DOUBLE la fréquence,
    fait acoustique antérieur à toute formule) ; A3 = 220 Hz.
  • Table de fréquences du piano (valeurs tabulées universelles, ±0.001 Hz) : C4 ≈ 261.6256 Hz,
    E4 ≈ 329.6276, G4 ≈ 391.9954, A#4 ≈ 466.1638, B3 ≈ 246.9417, C-1 ≈ 8.1758 Hz.
  • Demi-ton tempéré = 2^(1/12) ≈ 1.059463094 (constante tabulée).
  • Quinte juste = 3/2 EXACT (Pythagore) ; quarte 4/3 ; tierce majeure 5/4 ; octave 2/1 (Fractions).
  • Quinte tempérée 2^(7/12) ≈ 1.498307077 ; écart quinte tempérée−juste = 700 − 701.955 ≈ −1.955 cents
    (calcul à la main : 1200·log2(1.5) = 1200·0.5849625007 = 701.9550009).
  • COMMA PYTHAGORICIEN : (3/2)^12/2^7 = 531441/524288 (= 3^12/2^19, arithmétique entière recalculée ICI
    par un SECOND chemin en Fraction) ≈ 23.460 cents.
  • Gammes sur les TOUCHES BLANCHES (fait classique : les 7 modes grecs = rotations de C majeur) :
    C majeur = C D E F G A B ; D dorien, E phrygien, F lydien, G mixolydien, A éolien, B locrien = les
    mêmes 7 notes blanches. Armures classiques : G majeur -> F# (1 dièse), F majeur -> Bb (1 bémol),
    Bb majeur -> Bb Eb (2 bémols). A mineur harmonique -> G# (sensible haussée).
  • Accords classiques : do majeur = C E G (0,4,7) ; la mineur = A C E ; si diminué = B D F ;
    sol 7e de dominante = G B D F.

SOUNDNESS : note invalide, octave hors [-1,9], système non nommé/inconnu, mode/qualité/intervalle hors
catalogue, intonation juste ambiguë (triton, 7e mineure), bool/str/NaN/inf/rapport ≤ 0 -> ValueError.
"""
import math
from fractions import Fraction

import musique_gammes as M

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


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


T = "tempere_12"

# ── 1) ANCRE ISO 16 : A4 = 440 Hz EXACT ; octaves = ×2 (fait acoustique) ──
check(M.frequence("A", 4, T) == 440.0, "A4 = 440 Hz exact (ISO 16)")
check(M.frequence("A", 5, T) == 880.0, "A5 = 880 Hz (octave = ×2)")
check(M.frequence("A", 3, T) == 220.0, "A3 = 220 Hz (octave = /2)")

# ── 2) ANCRES : table de fréquences tabulée (±0.001 Hz) ──
check(proche(M.frequence("C", 4, T), 261.6256, tol=1e-3), "C4 ≈ 261.6256 Hz (do central, tabulé)")
check(proche(M.frequence("C", 5, T), 523.2511, tol=1e-3), "C5 ≈ 523.2511 Hz (tabulé)")
check(proche(M.frequence("E", 4, T), 329.6276, tol=1e-3), "E4 ≈ 329.6276 Hz (tabulé)")
check(proche(M.frequence("G", 4, T), 391.9954, tol=1e-3), "G4 ≈ 391.9954 Hz (tabulé)")
check(proche(M.frequence("A#", 4, T), 466.1638, tol=1e-3), "A#4 ≈ 466.1638 Hz (tabulé)")
check(proche(M.frequence("Bb", 4, T), 466.1638, tol=1e-3), "Bb4 = A#4 (enharmonie tempérée)")
check(proche(M.frequence("C", -1, T), 8.1758, tol=1e-3), "C-1 ≈ 8.1758 Hz (plus basse note MIDI, tabulé)")
# demi-ton tempéré = 2^(1/12) ≈ 1.059463094 (constante tabulée)
check(proche(M.frequence("A#", 4, T) / M.frequence("A", 4, T), 1.059463094, tol=1e-6),
      "rapport d'un demi-ton = 2^(1/12) ≈ 1.059463094")
# l'octave s'attache à la lettre : B#3 sonne C4 ; Cb4 sonne B3 (≈ 246.9417 Hz tabulé)
check(proche(M.frequence("B#", 3, T), 261.6256, tol=1e-3), "B#3 = C4 (épellation : octave suit la lettre)")
check(proche(M.frequence("Cb", 4, T), 246.9417, tol=1e-3), "Cb4 = B3 ≈ 246.9417 Hz (tabulé)")

# ── 3) INTERVALLES : demi-tons et noms ──
check(M.intervalle_demi_tons("C", "G") == 7, "C->G = 7 demi-tons (quinte)")
check(M.intervalle_demi_tons("C", "C") == 0, "C->C = 0 (unisson)")
check(M.intervalle_demi_tons("C", "E") == 4, "C->E = 4 (tierce majeure)")
check(M.intervalle_demi_tons("E", "C") == 8, "E->C ascendant = 8 (sixte mineure)")
check(M.intervalle_demi_tons("A", "C") == 3, "A->C = 3 (tierce mineure)")
check(M.intervalle_demi_tons("F#", "Gb") == 0, "F# et Gb : même classe de hauteur tempérée")
check(M.nom_intervalle(0) == "unisson", "0 = unisson")
check(M.nom_intervalle(1) == "seconde mineure", "1 = seconde mineure")
check(M.nom_intervalle(4) == "tierce majeure", "4 = tierce majeure")
check(M.nom_intervalle(5) == "quarte juste", "5 = quarte juste")
check(M.nom_intervalle(7) == "quinte juste", "7 = quinte juste")
check(M.nom_intervalle(12) == "octave", "12 = octave")
check(M.demi_tons_intervalle("quinte_juste") == 7, "quinte_juste = 7 demi-tons")

# ── 4) GAMMES : ancre do majeur + armures classiques + modes = touches blanches ──
check(M.intervalles_gamme("majeur") == (2, 2, 1, 2, 2, 2, 1), "patron majeur = 2,2,1,2,2,2,1")
check(M.intervalles_gamme("mineur_naturel") == (2, 1, 2, 2, 1, 2, 2), "patron mineur naturel = 2,1,2,2,1,2,2")
check(M.gamme("C", "majeur") == ["C", "D", "E", "F", "G", "A", "B"], "do majeur = C D E F G A B (ancre)")
check(M.gamme("G", "majeur") == ["G", "A", "B", "C", "D", "E", "F#"], "sol majeur = 1 dièse (F#)")
check(M.gamme("F", "majeur") == ["F", "G", "A", "Bb", "C", "D", "E"], "fa majeur = 1 bémol (Bb)")
check(M.gamme("Bb", "majeur") == ["Bb", "C", "D", "Eb", "F", "G", "A"], "sib majeur = 2 bémols (Bb, Eb)")
check(M.gamme("A", "mineur_naturel") == ["A", "B", "C", "D", "E", "F", "G"], "la mineur naturel = blanches")
check(M.gamme("A", "mineur_harmonique") == ["A", "B", "C", "D", "E", "F", "G#"],
      "la mineur harmonique = sensible G#")
check(M.gamme("D", "dorien") == ["D", "E", "F", "G", "A", "B", "C"], "ré dorien = touches blanches")
check(M.gamme("E", "phrygien") == ["E", "F", "G", "A", "B", "C", "D"], "mi phrygien = touches blanches")
check(M.gamme("F", "lydien") == ["F", "G", "A", "B", "C", "D", "E"], "fa lydien = touches blanches")
check(M.gamme("G", "mixolydien") == ["G", "A", "B", "C", "D", "E", "F"], "sol mixolydien = touches blanches")
check(M.gamme("B", "locrien") == ["B", "C", "D", "E", "F", "G", "A"], "si locrien = touches blanches")
check(M.gamme("C", "ionien") == M.gamme("C", "majeur"), "ionien = majeur")
check(M.gamme("A", "eolien") == M.gamme("A", "mineur_naturel"), "éolien = mineur naturel")
check(M.gamme("C", "pentatonique") == ["C", "D", "E", "G", "A"], "do pentatonique majeure = C D E G A")

# ── 5) ACCORDS : ancres classiques ──
check(M.intervalles_accord("majeur") == (0, 4, 7), "accord majeur = 0,4,7 (ancre)")
check(M.intervalles_accord("mineur") == (0, 3, 7), "accord mineur = 0,3,7")
check(M.intervalles_accord("septieme_dominante") == (0, 4, 7, 10), "7e de dominante = 0,4,7,10")
check(M.accord("C", "majeur") == ["C", "E", "G"], "do majeur = C E G (ancre)")
check(M.accord("A", "mineur") == ["A", "C", "E"], "la mineur = A C E")
check(M.accord("B", "diminue") == ["B", "D", "F"], "si diminué = B D F")
check(M.accord("C", "augmente") == ["C", "E", "G#"], "do augmenté = C E G#")
check(M.accord("G", "septieme_dominante") == ["G", "B", "D", "F"], "G7 = G B D F")
check(M.accord("D", "majeur") == ["D", "F#", "A"], "ré majeur = D F# A")

# ── 6) INTONATION JUSTE : Fractions EXACTES (ancres pythagoriciennes/5-limite) ──
q = M.rapport_juste("quinte_juste")
check(isinstance(q, Fraction) and q == Fraction(3, 2), "quinte juste = 3/2 EXACT (Fraction)")
check(M.rapport_juste("quarte_juste") == Fraction(4, 3), "quarte juste = 4/3 EXACT")
check(M.rapport_juste("tierce_majeure") == Fraction(5, 4), "tierce majeure = 5/4 EXACT")
check(M.rapport_juste("tierce_mineure") == Fraction(6, 5), "tierce mineure = 6/5 EXACT")
check(M.rapport_juste("octave") == Fraction(2, 1), "octave = 2/1 EXACT")
check(M.rapport_juste("unisson") == Fraction(1, 1), "unisson = 1/1 EXACT")
check(M.rapport_intervalle("quinte_juste", "juste") == Fraction(3, 2), "rapport_intervalle juste nommé = 3/2")

# ── 7) COMPARAISON tempéré/juste : le point théorique ──
# quinte tempérée = 2^(7/12) ≈ 1.498307077 (tabulé)
check(proche(M.rapport_intervalle("quinte_juste", T), 1.498307077, tol=1e-6),
      "quinte tempérée = 2^(7/12) ≈ 1.498307077")
# écart quinte : 700 − 701.9550009 = −1.9550009 cents (calcul à la main dans l'en-tête)
check(proche(M.ecart_cents(2.0 ** (7.0 / 12.0), Fraction(3, 2)), -1.955, tol=1e-3),
      "écart quinte tempérée−juste ≈ −1.955 cents")
check(proche(M.ecart_tempere_juste("quinte_juste"), -1.955, tol=1e-3),
      "ecart_tempere_juste(quinte) ≈ −1.955 cents")
# la quinte tempérée vaut 700 cents au-dessus de l'unisson : 1200·log2(2^(7/12)) = 700 exactement
check(proche(M.ecart_cents(2.0 ** (7.0 / 12.0), 1), 700.0, tol=1e-6), "quinte tempérée = 700 cents")
# tierce majeure : 400 − 386.3137 = +13.686 cents (valeur classique du 'syntonic' écart tempéré)
check(proche(M.ecart_tempere_juste("tierce_majeure"), 13.686, tol=1e-3),
      "écart tierce majeure ≈ +13.686 cents")
# l'octave tempérée est PURE : écart nul
check(M.ecart_tempere_juste("octave") == 0.0, "octave tempérée = octave juste (écart 0)")

# ── 8) COMMA PYTHAGORICIEN : second chemin arithmétique EXACT ──
comma = M.comma_pythagoricien()
check(isinstance(comma, Fraction) and comma == Fraction(531441, 524288),
      "comma = 531441/524288 EXACT (ancre remarquable 3^12/2^19)")
# SECOND chemin : douze quintes 3/2 empilées, redescendues de 7 octaves (arithmétique entière ICI)
douze_quintes = Fraction(3, 2) ** 12          # 531441/4096
sept_octaves = Fraction(2, 1) ** 7            # 128
check(comma == douze_quintes / sept_octaves, "comma = (3/2)^12 / 2^7 (recalcul indépendant en Fraction)")
check(douze_quintes / sept_octaves != 1, "FAIT : 12 quintes justes ≠ 7 octaves (le cycle ne boucle pas)")
check(proche(float(comma), 1.013643265, tol=1e-6), "comma ≈ 1.013643265 (tabulé)")
check(proche(M.comma_pythagoricien_cents(), 23.460, tol=1e-3), "comma ≈ 23.460 cents (tabulé)")
check(proche(M.ecart_cents(comma, 1), M.comma_pythagoricien_cents(), tol=1e-6),
      "cohérence : ecart_cents(comma, 1) = comma en cents")

# ── 9) SOUNDNESS — notes ──
check(leve(M.frequence, "H", 4, T), "note H -> ValueError")
check(leve(M.frequence, "X#", 4, T), "note X# -> ValueError")
check(leve(M.frequence, "C###", 4, T), "triple dièse -> ValueError")
check(leve(M.frequence, "c", 4, T), "minuscule -> ValueError")
check(leve(M.frequence, "", 4, T), "note vide -> ValueError")
check(leve(M.frequence, 60, 4, T), "note non-str -> ValueError")
check(leve(M.intervalle_demi_tons, "C", "H"), "intervalle note invalide -> ValueError")
check(leve(M.gamme, "H", "majeur"), "gamme tonique invalide -> ValueError")
check(leve(M.accord, "Do", "majeur"), "accord tonique 'Do' (non catalogue) -> ValueError")

# ── 10) SOUNDNESS — octave hors [-1, 9] / non entier ──
check(leve(M.frequence, "A", -2, T), "octave -2 -> ValueError")
check(leve(M.frequence, "A", 10, T), "octave 10 -> ValueError")
check(leve(M.frequence, "A", 4.0, T), "octave flottant -> ValueError")
check(leve(M.frequence, "A", True, T), "octave bool -> ValueError")
check(leve(M.frequence, "A", "4", T), "octave str -> ValueError")

# ── 11) SOUNDNESS — SYSTÈME toujours nommé, jamais implicite ──
try:
    M.frequence("A", 4)          # système absent -> TypeError (arité) : jamais de défaut implicite
    check(False, "frequence sans système ne doit pas répondre")
except TypeError:
    check(True, "frequence sans système -> TypeError (le système est OBLIGATOIRE)")
except ValueError:
    check(True, "frequence sans système -> refus")
check(leve(M.frequence, "A", 4, "pythagoricien"), "système inconnu -> ValueError")
check(leve(M.frequence, "A", 4, ""), "système vide -> ValueError")
check(leve(M.frequence, "A", 4, "juste"), "fréquence en intonation juste -> ValueError (pas de référence absolue)")
check(leve(M.rapport_intervalle, "quinte_juste", "tempere_53"), "rapport système inconnu -> ValueError")

# ── 12) SOUNDNESS — catalogues (mode, qualité, intervalle) ──
check(leve(M.gamme, "C", "blues"), "mode hors catalogue -> ValueError")
check(leve(M.gamme, "C", 3), "mode non-str -> ValueError")
check(leve(M.accord, "C", "sus4"), "qualité hors catalogue -> ValueError")
check(leve(M.nom_intervalle, 13), "13 demi-tons -> ValueError (hors catalogue)")
check(leve(M.nom_intervalle, -1), "-1 demi-ton -> ValueError")
check(leve(M.nom_intervalle, True), "demi-tons bool -> ValueError")
check(leve(M.nom_intervalle, 7.0), "demi-tons flottant -> ValueError")
check(leve(M.demi_tons_intervalle, "neuvieme"), "intervalle inconnu -> ValueError")
check(leve(M.rapport_juste, "triton"), "triton juste AMBIGU -> ValueError (abstention)")
check(leve(M.rapport_juste, "septieme_mineure"), "7e mineure juste AMBIGUË -> ValueError (abstention)")
check(leve(M.rapport_juste, 7), "rapport_juste non-str -> ValueError")

# ── 13) SOUNDNESS — ecart_cents (types, domaine) ──
check(leve(M.ecart_cents, 0.0, 1.5), "rapport 0 -> ValueError")
check(leve(M.ecart_cents, -1.5, 1.5), "rapport négatif -> ValueError")
check(leve(M.ecart_cents, 1.5, 0), "rapport juste 0 -> ValueError")
check(leve(M.ecart_cents, float("nan"), 1.5), "NaN -> ValueError")
check(leve(M.ecart_cents, float("inf"), 1.5), "inf -> ValueError")
check(leve(M.ecart_cents, 1.5, float("-inf")), "-inf -> ValueError")
check(leve(M.ecart_cents, True, 1.5), "bool -> ValueError")
check(leve(M.ecart_cents, "1.5", 1.5), "str -> ValueError")

# ── 14) DÉTERMINISME ──
check(M.frequence("C", 4, T) == M.frequence("C", 4, T), "déterminisme fréquence")
check(M.gamme("G", "majeur") == M.gamme("G", "majeur"), "déterminisme gamme")
check(M.accord("G", "septieme_dominante") == M.accord("G", "septieme_dominante"), "déterminisme accord")
check(M.ecart_tempere_juste("quinte_juste") == M.ecart_tempere_juste("quinte_juste"), "déterminisme cents")
check(M.comma_pythagoricien() == M.comma_pythagoricien(), "déterminisme comma")

print(f"\n=== valide_musique_gammes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
