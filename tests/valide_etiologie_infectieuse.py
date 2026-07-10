"""Gate adverse pour `etiologie_infectieuse` : ancres NON CIRCULAIRES (faits médicaux établis
indépendants du code), soundness (abstention sur types/entrées illégales), déterminisme.

Chaque valeur attendue est un FAIT de microbiologie médicale écrit EN DUR, connu indépendamment du module.
"""
from __future__ import annotations

import etiologie_infectieuse as E

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
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def abstient(fn, *a):
    """Abstention au sens large : ValueError OU TypeError (mauvaise arité). Jamais un retour muet."""
    try:
        fn(*a)
        return False
    except (ValueError, TypeError):
        return True
    except Exception:
        return False


# ── ANCRES NON CIRCULAIRES (faits médicaux établis, écrits en dur) ───────────────────────────────────────────

# ANCRE DISCRIMINANTE : le paludisme est causé par un PARASITE (Plasmodium), PAS par un virus,
# et surtout PAS par le moustique (qui n'est que le VECTEUR).
check(E.type_agent("paludisme") == "parasite", "paludisme = parasite")
check(E.type_agent("paludisme") != "virus", "paludisme n'est PAS un virus")
check("Plasmodium" in E.agent("paludisme"), "agent paludisme = Plasmodium")
check("moustique" not in E.agent("paludisme").lower(), "agent paludisme n'est PAS le moustique")
check("Anophel" not in E.agent("paludisme"), "agent paludisme n'est pas Anopheles (= vecteur)")
# le moustique/vecteur apparaît dans la TRANSMISSION, pas dans l'agent
check("Anophel" in E.transmission("paludisme") or "moustique" in E.transmission("paludisme"),
      "vecteur Anopheles figure dans la transmission")

# ANCRE : ulcère gastroduodénal = Helicobacter pylori (bactérie), PAS le stress (Nobel 2005).
check("Helicobacter" in E.agent("ulcere gastroduodenal"), "ulcère = Helicobacter pylori")
check(E.type_agent("ulcere gastroduodenal") == "bactérie", "ulcère = bactérie")
check("stress" not in E.agent("ulcere gastroduodenal").lower(), "ulcère n'est PAS le stress")

# ANCRE : tuberculose = bactérie (bacille de Koch, Mycobacterium tuberculosis).
check(E.type_agent("tuberculose") == "bactérie", "tuberculose = bactérie")
check("Mycobacterium" in E.agent("tuberculose"), "tuberculose = Mycobacterium tuberculosis")

# ANCRE VACCIN (fait 2026) : le VIH n'a PAS de vaccin ; la rougeole en a un.
check(E.vaccin_existe("vih/sida") is False, "VIH : pas de vaccin (2026)")
check(E.vaccin_existe("rougeole") is True, "rougeole : vaccin existe (ROR)")

# ANCRE : Creutzfeldt-Jakob = PRION (ni virus ni bactérie).
check(E.type_agent("creutzfeldt-jakob") == "prion", "Creutzfeldt-Jakob = prion")
check(E.type_agent("creutzfeldt-jakob") != "virus", "Creutzfeldt-Jakob n'est PAS un virus")
check(E.type_agent("creutzfeldt-jakob") != "bactérie", "Creutzfeldt-Jakob n'est PAS une bactérie")

# ── Autres faits établis par maladie ─────────────────────────────────────────────────────────────────────────
check("Vibrio cholerae" == E.agent("cholera"), "choléra = Vibrio cholerae")
check(E.type_agent("cholera") == "bactérie", "choléra = bactérie")
check(E.type_agent("grippe") == "virus", "grippe = virus")
check(E.agent("covid-19") == "SARS-CoV-2", "COVID-19 = SARS-CoV-2")
check(E.type_agent("covid-19") == "virus", "COVID-19 = virus")
check(E.type_agent("vih/sida") == "virus", "VIH = virus")
check("Clostridium tetani" == E.agent("tetanos"), "tétanos = Clostridium tetani")
check(E.type_agent("tetanos") == "bactérie", "tétanos = bactérie")
check("Yersinia pestis" == E.agent("peste"), "peste = Yersinia pestis")
check("Salmonella" in E.agent("typhoide"), "typhoïde = Salmonella Typhi")
check("Bordetella pertussis" == E.agent("coqueluche"), "coqueluche = Bordetella pertussis")
check("Corynebacterium diphtheriae" == E.agent("diphterie"), "diphtérie = Corynebacterium diphtheriae")
check("Treponema pallidum" == E.agent("syphilis"), "syphilis = Treponema pallidum")
check("Borrelia burgdorferi" == E.agent("maladie de lyme"), "Lyme = Borrelia burgdorferi")
check(E.type_agent("maladie de lyme") == "bactérie", "Lyme = bactérie (spirochète)")
check("Toxoplasma gondii" == E.agent("toxoplasmose"), "toxoplasmose = Toxoplasma gondii")
check(E.type_agent("toxoplasmose") == "parasite", "toxoplasmose = parasite")
check("Candida albicans" == E.agent("candidose"), "candidose = Candida albicans")
check(E.type_agent("candidose") == "champignon", "candidose = champignon")
check("hépatite B" in E.agent("hepatite b"), "hépatite B = VHB")
check(E.vaccin_existe("hepatite b") is True, "hépatite B : vaccin existe")
check(E.type_agent("rage") == "virus", "rage = virus")
check("morsure" in E.transmission("rage"), "rage : transmission par morsure")

# ── Vecteurs vs agents (piège agent/vecteur au-delà du paludisme) ────────────────────────────────────────────
check("puce" in E.transmission("peste"), "peste : vecteur puce dans transmission")
check("Yersinia" in E.agent("peste") and "puce" not in E.agent("peste"), "peste : agent = bactérie, pas la puce")
check("tique" in E.transmission("maladie de lyme"), "Lyme : vecteur tique dans transmission")

# ── maladies_par_agent : recoupe le catalogue (second chemin) ────────────────────────────────────────────────
prions = E.maladies_par_agent("prion")
check(prions == ["creutzfeldt-jakob"], "un seul prion au catalogue")
champis = E.maladies_par_agent("champignon")
check(champis == ["candidose"], "un seul champignon au catalogue")
virus = E.maladies_par_agent("virus")
check("grippe" in virus and "covid-19" in virus and "rougeole" in virus, "virus contient grippe/covid/rougeole")
check("paludisme" not in virus, "paludisme absent des virus (parasite)")
check(E.maladies_par_agent("virus") == sorted(E.maladies_par_agent("virus")), "liste virus triée")
# la réunion des types couvre exactement tout le catalogue (partition)
union = []
for t in ("bactérie", "virus", "parasite", "champignon", "prion"):
    union += E.maladies_par_agent(t)
check(sorted(union) == E.catalogue(), "les types partitionnent le catalogue")

# ── catalogue : au moins 20 maladies, trié ───────────────────────────────────────────────────────────────────
cat = E.catalogue()
check(len(cat) >= 20, "au moins 20 maladies au catalogue")
check(cat == sorted(cat), "catalogue trié")
check(len(set(cat)) == len(cat), "catalogue sans doublon")

# ── ALIAS / normalisation ────────────────────────────────────────────────────────────────────────────────────
check(E.type_agent("malaria") == "parasite", "alias malaria -> paludisme")
check(E.agent("VIH") == "VIH", "alias VIH -> vih/sida")
check(E.type_agent("TUBERCULOSE") == "bactérie", "casse insensible")
check(E.type_agent("paludïsme".replace("ï", "i")) == "parasite", "normalisation basique")
check(E.agent("Ulcère gastroduodénal") == "Helicobacter pylori", "accents normalisés")

# ── SOUNDNESS : abstention structurelle ──────────────────────────────────────────────────────────────────────
# maladie NON infectieuse -> ValueError (diabète, cancer non viral, hypertension)
check(leve(E.agent, "diabete"), "diabète (non infectieux) -> ValueError")
check(leve(E.agent, "hypertension"), "hypertension (non infectieux) -> ValueError")
check(leve(E.type_agent, "cancer"), "cancer générique -> ValueError")
# maladie inventée -> ValueError
check(leve(E.agent, "morgellons_inventee"), "maladie inventée -> ValueError")
check(leve(E.agent, "xyzzy"), "nom bidon -> ValueError")
# types invalides
check(leve(E.agent, True), "bool -> ValueError (agent)")
check(leve(E.agent, 42), "int -> ValueError (agent)")
check(leve(E.agent, None), "None -> ValueError (agent)")
check(leve(E.agent, ""), "chaîne vide -> ValueError (agent)")
check(leve(E.agent, 1.5), "float -> ValueError (agent)")
check(abstient(E.type_agent, "grippe", "extra"), "mauvaise arité -> abstention (type_agent)")
check(leve(E.vaccin_existe, True), "bool -> ValueError (vaccin_existe)")
check(leve(E.transmission, "inexistante"), "maladie inconnue -> ValueError (transmission)")
# type d'agent inconnu / invalide pour maladies_par_agent
check(leve(E.maladies_par_agent, "algue"), "type inconnu -> ValueError")
check(leve(E.maladies_par_agent, True), "bool -> ValueError (maladies_par_agent)")
check(abstient(E.maladies_par_agent, "virus", "trop"), "mauvaise arité -> abstention (maladies_par_agent)")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────
check(E.agent("paludisme") == E.agent("paludisme"), "déterminisme agent")
check(E.catalogue() == E.catalogue(), "déterminisme catalogue")
check(E.maladies_par_agent("virus") == E.maladies_par_agent("virus"), "déterminisme maladies_par_agent")
check(E.vaccin_existe("vih/sida") == E.vaccin_existe("vih/sida"), "déterminisme vaccin_existe")


print(f"\n=== valide_etiologie_infectieuse : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
