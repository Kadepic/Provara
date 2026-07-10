"""
VALIDE familles_langues.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (linguistique comparée, consensus — connues INDÉPENDAMMENT du code testé) :
  • parente('français') contient 'roman' et se TERMINE par 'indo-européen'.
  • parente('anglais') contient 'germanique' et 'indo-européen'.
  • ancetre_commun('français','espagnol') = 'roman'   (tous deux romans, mais gallo-roman vs ibéro-roman).
  • ancetre_commun('français','anglais') = 'indo-européen'.
  • ancetre_commun('français','arabe') -> ValueError  (indo-européen vs afro-asiatique : ANCRE FORTE).
  • apparentees('hindi','anglais') = True   (tous deux indo-européens — contre-intuitif, ancre pédagogique).
  • apparentees('hongrois','français') = False  (ouralien vs indo-européen malgré la proximité géographique).
  • est_isolat('basque') = True ; famille('basque') = 'isolat' ; ancetre_commun('basque','espagnol') -> ValueError.
  • famille('turc') = 'turcique' et NON 'altaïque' (regroupement contesté).

SOUNDNESS : bool, None, str vide, nombre, mauvaise arité, langue inconnue -> ValueError.
DÉTERMINISME : double appel identique.
"""
import familles_langues as F

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


# ══ 1) ANCRE : parente('français') — chaîne exacte du contrat ════════════════════════════════════════════════════
p_fr = F.parente("français")
check(p_fr == ("français", "langue d'oïl", "gallo-roman", "roman", "italique", "indo-européen"),
      f"parente(français) = chaîne exacte, obtenu {p_fr}")
check("roman" in p_fr, "parente(français) contient 'roman'")
check(p_fr[-1] == "indo-européen", "parente(français) se termine par 'indo-européen'")
check(p_fr[0] == "français", "parente(français) commence par la langue elle-même")

# ══ 2) ANCRE : parente('anglais') contient 'germanique' et 'indo-européen' ════════════════════════════════════════
p_en = F.parente("anglais")
check("germanique" in p_en, f"parente(anglais) contient 'germanique', obtenu {p_en}")
check("indo-européen" in p_en, "parente(anglais) contient 'indo-européen'")
check(p_en[-1] == "indo-européen", "parente(anglais) se termine par 'indo-européen'")

# ══ 3) ANCRE FORTE : ancêtres communs ════════════════════════════════════════════════════════════════════════════
# français & espagnol : romans mais sous-branches différentes (gallo-roman vs ibéro-roman) -> commun = 'roman'
check(F.ancetre_commun("français", "espagnol") == "roman",
      f"ancetre_commun(français,espagnol)='roman', obtenu {F.ancetre_commun('français','espagnol')}")
# symétrie
check(F.ancetre_commun("espagnol", "français") == "roman", "ancetre_commun symétrique (roman)")
# français & anglais : romans vs germaniques -> commun = 'indo-européen'
check(F.ancetre_commun("français", "anglais") == "indo-européen",
      "ancetre_commun(français,anglais)='indo-européen'")
# hindi & persan : indo-aryen vs iranien -> commun = 'indo-iranien' (les deux sous-branches indo-iraniennes)
check(F.ancetre_commun("hindi", "persan") == "indo-iranien",
      f"ancetre_commun(hindi,persan)='indo-iranien', obtenu {F.ancetre_commun('hindi','persan')}")
# espagnol & portugais : tous deux ibéro-romans -> commun = 'ibéro-roman'
check(F.ancetre_commun("espagnol", "portugais") == "ibéro-roman",
      "ancetre_commun(espagnol,portugais)='ibéro-roman'")
# russe & polonais : slave oriental vs occidental -> commun = 'slave'
check(F.ancetre_commun("russe", "polonais") == "slave", "ancetre_commun(russe,polonais)='slave'")
# une langue avec elle-même -> elle-même (nœud le plus profond)
check(F.ancetre_commun("français", "français") == "français", "ancetre_commun(français,français)='français'")

# ══ 4) ANCRE FORTE : ABSENCE de parenté = ValueError (pas un échec) ═══════════════════════════════════════════════
check(leve(F.ancetre_commun, "français", "arabe"),
      "ancetre_commun(français,arabe) -> ValueError (indo-européen vs afro-asiatique)")
check(leve(F.ancetre_commun, "basque", "espagnol"),
      "ancetre_commun(basque,espagnol) -> ValueError (isolat vs indo-européen)")
check(leve(F.ancetre_commun, "basque", "sumérien"),
      "ancetre_commun(basque,sumérien) -> ValueError (deux isolats DISTINCTS, pas de pseudo-nœud partagé)")
check(leve(F.ancetre_commun, "japonais", "coréen"),
      "ancetre_commun(japonais,coréen) -> ValueError (japonique vs coréanique, altaïque contesté)")
check(leve(F.ancetre_commun, "turc", "hongrois"),
      "ancetre_commun(turc,hongrois) -> ValueError (turcique vs ouralien)")
check(leve(F.ancetre_commun, "mandarin", "tamoul"),
      "ancetre_commun(mandarin,tamoul) -> ValueError (sino-tibétain vs dravidien)")

# ══ 5) ANCRE : apparentees ═══════════════════════════════════════════════════════════════════════════════════════
check(F.apparentees("hindi", "anglais") is True,
      "apparentees(hindi,anglais)=True (tous deux indo-européens)")
check(F.apparentees("hongrois", "français") is False,
      "apparentees(hongrois,français)=False (ouralien vs indo-européen)")
check(F.apparentees("arabe", "hébreu") is True, "apparentees(arabe,hébreu)=True (tous deux sémitiques)")
check(F.apparentees("finnois", "estonien") is True, "apparentees(finnois,estonien)=True (finniques)")
check(F.apparentees("finnois", "hongrois") is True, "apparentees(finnois,hongrois)=True (ouraliens)")
check(F.apparentees("turc", "azéri") is True, "apparentees(turc,azéri)=True (turciques)")
check(F.apparentees("basque", "français") is False, "apparentees(basque,français)=False (isolat)")
check(F.apparentees("basque", "sumérien") is False,
      "apparentees(basque,sumérien)=False (deux isolats distincts)")
check(F.apparentees("japonais", "coréen") is False,
      "apparentees(japonais,coréen)=False (altaïque non prouvé)")

# ══ 6) ANCRE : familles ══════════════════════════════════════════════════════════════════════════════════════════
check(F.famille("français") == "indo-européen", "famille(français)='indo-européen'")
check(F.famille("anglais") == "indo-européen", "famille(anglais)='indo-européen'")
check(F.famille("arabe") == "afro-asiatique", "famille(arabe)='afro-asiatique'")
check(F.famille("hébreu") == "afro-asiatique", "famille(hébreu)='afro-asiatique'")
check(F.famille("hongrois") == "ouralien", "famille(hongrois)='ouralien'")
check(F.famille("finnois") == "ouralien", "famille(finnois)='ouralien'")
check(F.famille("mandarin") == "sino-tibétain", "famille(mandarin)='sino-tibétain'")
check(F.famille("tibétain") == "sino-tibétain", "famille(tibétain)='sino-tibétain'")
check(F.famille("tamoul") == "dravidien", "famille(tamoul)='dravidien'")
check(F.famille("indonésien") == "austronésien", "famille(indonésien)='austronésien'")
check(F.famille("malgache") == "austronésien", "famille(malgache)='austronésien' (Madagascar, austronésien!)")
check(F.famille("swahili") == "niger-congo", "famille(swahili)='niger-congo'")
check(F.famille("japonais") == "japonique", "famille(japonais)='japonique'")
check(F.famille("coréen") == "coréanique", "famille(coréen)='coréanique'")
# ANCRE : turcique et NON altaïque
check(F.famille("turc") == "turcique", "famille(turc)='turcique' (PAS altaïque)")
check(F.famille("turc") != "altaïque", "famille(turc) != 'altaïque' (regroupement contesté)")

# ══ 7) ANCRE : isolats ═══════════════════════════════════════════════════════════════════════════════════════════
check(F.est_isolat("basque") is True, "est_isolat(basque)=True")
check(F.famille("basque") == "isolat", "famille(basque)='isolat'")
check(F.est_isolat("sumérien") is True, "est_isolat(sumérien)=True")
check(F.famille("sumérien") == "isolat", "famille(sumérien)='isolat'")
check(F.est_isolat("aïnou") is True, "est_isolat(aïnou)=True")
# ANCRE FAUX=0 (correctif) : japonais et ryukyu se PARTAGENT la famille japonique -> AUCUN n'est un isolat.
# Le japonais a un apparenté prouvé (les langues ryūkyū) : Japonic est une FAMILLE, pas un isolat
# (Glottolog/Ethnologue : Japanese-Ryukyuan). Un prédicat 'isolat' True ici serait un faux positif.
check(F.est_isolat("japonais") is False,
      "est_isolat(japonais)=False (a un apparenté prouvé : les langues ryūkyū — Japonic est une famille)")
check(F.est_isolat("ryukyu") is False,
      "est_isolat(ryukyu)=False (apparenté au japonais dans la famille japonique)")
# COHÉRENCE INTERNE : est_isolat contredit apparentees serait un bug -> on prouve la NON-contradiction.
check(F.apparentees("japonais", "ryukyu") is True,
      "apparentees(japonais,ryukyu)=True (même famille japonique)")
check(F.ancetre_commun("japonais", "ryukyu") == "japonique",
      "ancetre_commun(japonais,ryukyu)='japonique'")
check(not (F.est_isolat("japonais") and F.apparentees("japonais", "ryukyu")),
      "NON-contradiction : est_isolat(x) implique aucun apparenté (japonais/ryukyu)")
check(F.est_isolat("coréen") is True, "est_isolat(coréen)=True (seul membre de coréanique — selon l'école)")
check(F.est_isolat("français") is False, "est_isolat(français)=False")
check(F.est_isolat("arabe") is False, "est_isolat(arabe)=False")
# un isolat vrai n'a EN EFFET aucun apparenté autre que lui-même dans le catalogue (contrôle structurel)
for _iso in ("basque", "sumérien", "aïnou", "coréen"):
    _autres = [n for n in F.catalogue() if n != _iso and F.apparentees(_iso, n)
               and n not in F.parente(_iso)]
    check(_autres == [], f"est_isolat({_iso})=True cohérent : aucun apparenté hors lignée (obtenu {_autres})")
check(F.parente("basque") == ("basque",), "parente(basque)=('basque',) — un isolat n'a pas d'ascendance")

# ══ 8) NORMALISATION accent-insensible (mais toujours FAUX=0 sur l'inconnu) ═══════════════════════════════════════
check(F.famille("Francais") == "indo-européen", "normalisation accents/casse : 'Francais' -> français")
check(F.famille("ARABE") == "afro-asiatique", "normalisation casse : 'ARABE'")
check(F.famille("  turc  ") == "turcique", "normalisation espaces")

# ══ 9) SOUNDNESS — abstention structurelle ═══════════════════════════════════════════════════════════════════════
check(leve(F.parente, "klingon"), "langue inventée -> ValueError")
check(leve(F.parente, "atlante"), "langue inconnue -> ValueError")
check(leve(F.famille, "elfique"), "famille(inconnue) -> ValueError")
check(leve(F.est_isolat, "quenya"), "est_isolat(inconnue) -> ValueError")
check(leve(F.apparentees, "français", "klingon"), "apparentees avec inconnue -> ValueError")
check(leve(F.ancetre_commun, "klingon", "français"), "ancetre_commun avec inconnue -> ValueError")
check(leve(F.parente, ""), "chaîne vide -> ValueError")
check(leve(F.parente, "   "), "espaces seuls -> ValueError")
check(leve(F.parente, True), "bool -> ValueError")
check(leve(F.parente, False), "bool False -> ValueError")
check(leve(F.parente, None), "None -> ValueError")
check(leve(F.parente, 42), "entier -> ValueError")
check(leve(F.parente, 3.14), "flottant -> ValueError")
check(leve(F.parente, ["français"]), "liste -> ValueError")
check(leve(F.famille, b"francais"), "bytes -> ValueError")

# ══ 10) DÉTERMINISME ═════════════════════════════════════════════════════════════════════════════════════════════
check(F.parente("français") == F.parente("français"), "déterminisme parente")
check(F.ancetre_commun("hindi", "persan") == F.ancetre_commun("hindi", "persan"), "déterminisme ancetre_commun")
check(F.famille("turc") == F.famille("turc"), "déterminisme famille")

# ══ 11) COHÉRENCE STRUCTURELLE du catalogue (arbre bien formé, ≥ 40 langues) ═════════════════════════════════════
cat = F.catalogue()
check(len(cat) >= 40, f"catalogue >= 40 nœuds (obtenu {len(cat)})")
# toute chaîne remonte à une racine reconnue (famille réelle ou isolat), sans lever
bien_forme = True
for noeud in cat:
    try:
        ch = F.parente(noeud)
        r = ch[-1]
        if r not in F.familles() and r not in ("basque", "sumérien", "aïnou"):
            bien_forme = False
    except Exception:
        bien_forme = False
check(bien_forme, "toute chaîne du catalogue remonte à une racine reconnue")
# apparentees est réflexif et symétrique sur un échantillon
ech = ("français", "anglais", "arabe", "turc", "basque", "japonais", "mandarin", "hindi")
refl = all(F.apparentees(x, x) for x in ech)
sym = all(F.apparentees(a, b) == F.apparentees(b, a) for a in ech for b in ech)
check(refl, "apparentees réflexif")
check(sym, "apparentees symétrique")

print(f"\n=== valide_familles_langues : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
