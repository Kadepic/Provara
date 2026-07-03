"""RÉSEAUX IP — calcul de sous-réseaux IPv4, FAUX=0 (mission formule/concept 2026-06-29).

Adresse de réseau, adresse de diffusion (broadcast), masque, nombre d'hôtes, appartenance à un même sous-réseau,
à partir d'une adresse IPv4 et d'un préfixe CIDR. Mécanisme EXACT (arithmétique binaire 32 bits). Abstention
STRUCTURELLE : adresse mal formée (octet ∉ 0..255, format invalide) ou CIDR ∉ 0..32 -> ValueError.

Couvre le sujet borné « Réseaux (protocoles TCP/IP…) » (volet adressage, calculable).
Vérifié en adverse par `valide_reseaux_ip.py` (réseau/broadcast/hôtes connus, même sous-réseau).
"""
from __future__ import annotations


def ip_vers_entier(ip: str) -> int:
    """Convertit « a.b.c.d » en entier 32 bits. ValueError si format invalide ou octet hors 0..255."""
    if not isinstance(ip, str):
        raise ValueError("adresse IP (chaîne) attendue")
    parties = ip.strip().split(".")
    if len(parties) != 4:
        raise ValueError(f"adresse IPv4 invalide : {ip!r}")
    n = 0
    for p in parties:
        if not p.isdigit():
            raise ValueError(f"octet non numérique : {p!r}")
        o = int(p)
        if not (0 <= o <= 255):
            raise ValueError(f"octet hors 0..255 : {o}")
        n = (n << 8) | o
    return n


def entier_vers_ip(n: int) -> str:
    """Convertit un entier 32 bits en « a.b.c.d »."""
    if not isinstance(n, int) or isinstance(n, bool) or not (0 <= n <= 0xFFFFFFFF):
        raise ValueError("entier 32 bits (0..2³²−1) attendu")
    return ".".join(str((n >> (8 * i)) & 0xFF) for i in (3, 2, 1, 0))


def _valide_cidr(cidr):
    if not isinstance(cidr, int) or isinstance(cidr, bool) or not (0 <= cidr <= 32):
        raise ValueError("préfixe CIDR ∈ 0..32 requis")


def masque_entier(cidr: int) -> int:
    _valide_cidr(cidr)
    return (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF if cidr else 0


def masque(cidr: int) -> str:
    """Masque de sous-réseau en notation décimale pointée (ex. /24 -> 255.255.255.0)."""
    return entier_vers_ip(masque_entier(cidr))


def adresse_reseau(ip: str, cidr: int) -> str:
    """Adresse de réseau = IP ET masque."""
    return entier_vers_ip(ip_vers_entier(ip) & masque_entier(cidr))


def adresse_broadcast(ip: str, cidr: int) -> str:
    """Adresse de diffusion = réseau OU complément du masque."""
    n = ip_vers_entier(ip) & masque_entier(cidr)
    return entier_vers_ip(n | (~masque_entier(cidr) & 0xFFFFFFFF))


def nombre_hotes(cidr: int) -> int:
    """Nombre d'adresses d'hôtes utilisables = 2^(32−cidr) − 2 (réseau + broadcast exclus). /31 et /32 -> 0."""
    _valide_cidr(cidr)
    total = 2 ** (32 - cidr)
    return max(total - 2, 0)


def meme_reseau(ip1: str, ip2: str, cidr: int) -> bool:
    """Les deux adresses sont-elles dans le même sous-réseau (même adresse de réseau) ?"""
    m = masque_entier(cidr)
    return (ip_vers_entier(ip1) & m) == (ip_vers_entier(ip2) & m)


if __name__ == "__main__":
    print("réseau 192.168.1.130/24 :", adresse_reseau("192.168.1.130", 24))
    print("broadcast /24 :", adresse_broadcast("192.168.1.130", 24))
    print("masque /24 :", masque(24), "| /26 :", masque(26))
    print("hôtes /24 :", nombre_hotes(24), "| /30 :", nombre_hotes(30), "| /16 :", nombre_hotes(16))
    print("même réseau .1 et .254 /24 :", meme_reseau("10.0.0.1", "10.0.0.254", 24))
    print("même réseau .1 et 10.0.1.1 /24 :", meme_reseau("10.0.0.1", "10.0.1.1", 24))
    print("réseau 172.16.5.130/26 :", adresse_reseau("172.16.5.130", 26), "broadcast :", adresse_broadcast("172.16.5.130", 26))
