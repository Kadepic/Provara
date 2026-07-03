"""VALIDE reseaux_ip.py — ADVERSE, FAUX=0. Réseau/broadcast/masque/hôtes CONNUS, appartenance au sous-réseau,
aller-retour IP↔entier + SOUNDNESS (adresse mal formée / CIDR invalide -> ValueError)."""
import reseaux_ip as R

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# CONVERSIONS (aller-retour)
check(R.ip_vers_entier("0.0.0.0") == 0 and R.ip_vers_entier("255.255.255.255") == 0xFFFFFFFF, "bornes IP")
check(R.ip_vers_entier("192.168.1.1") == 3232235777, "192.168.1.1 -> entier")
check(R.entier_vers_ip(3232235777) == "192.168.1.1", "entier -> IP (aller-retour)")
check(all(R.entier_vers_ip(R.ip_vers_entier(ip)) == ip for ip in ["10.0.0.1", "172.16.5.4", "8.8.8.8"]), "round-trip")

# RÉSEAU / BROADCAST / MASQUE
check(R.adresse_reseau("192.168.1.130", 24) == "192.168.1.0", "réseau /24")
check(R.adresse_broadcast("192.168.1.130", 24) == "192.168.1.255", "broadcast /24")
check(R.adresse_reseau("172.16.5.130", 26) == "172.16.5.128", "réseau /26")
check(R.adresse_broadcast("172.16.5.130", 26) == "172.16.5.191", "broadcast /26")
check(R.masque(24) == "255.255.255.0" and R.masque(26) == "255.255.255.192" and R.masque(8) == "255.0.0.0", "masques")
check(R.masque(0) == "0.0.0.0" and R.masque(32) == "255.255.255.255", "masques bornes")
check(R.adresse_reseau("10.1.2.3", 32) == "10.1.2.3", "/32 -> hôte unique")

# NOMBRE D'HÔTES
check(R.nombre_hotes(24) == 254 and R.nombre_hotes(30) == 2 and R.nombre_hotes(16) == 65534, "hôtes /24 /30 /16")
check(R.nombre_hotes(31) == 0 and R.nombre_hotes(32) == 0, "/31 /32 -> 0 hôte utilisable")
check(R.nombre_hotes(0) == 2 ** 32 - 2, "/0 -> tout l'espace")

# MÊME SOUS-RÉSEAU
check(R.meme_reseau("10.0.0.1", "10.0.0.254", 24) is True, ".1 et .254 dans /24")
check(R.meme_reseau("10.0.0.1", "10.0.1.1", 24) is False, ".0.1 et .1.1 hors /24")
check(R.meme_reseau("192.168.1.130", "192.168.1.190", 26) is True, "même /26")
check(R.meme_reseau("192.168.1.130", "192.168.1.60", 26) is False, "/26 frontière")

# SOUNDNESS
check(leve(R.ip_vers_entier, "192.168.1.256"), "octet 256 -> ValueError")
check(leve(R.ip_vers_entier, "10.0.0"), "3 octets -> ValueError")
check(leve(R.ip_vers_entier, "a.b.c.d"), "non numérique -> ValueError")
check(leve(R.masque, 33), "CIDR 33 -> ValueError")
check(leve(R.nombre_hotes, -1), "CIDR négatif -> ValueError")

# DÉTERMINISME
check(R.adresse_reseau("192.168.1.130", 24) == R.adresse_reseau("192.168.1.130", 24), "déterminisme")

print(f"\n=== valide_reseaux_ip : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
