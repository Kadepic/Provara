"""MICROPROCESSEURS — portes logiques et ALU, FAUX=0 (mission formule/concept 2026-06-29).

Portes logiques élémentaires (ET/OU/NON/NON-ET/NON-OU/OU-X), additionneur complet (1 bit), unité arithmétique et
logique (ALU) sur entiers non signés de n bits avec indicateurs (zéro, retenue, débordement signé). Mécanisme EXACT
(arithmétique binaire). Abstention STRUCTURELLE : opération inconnue, opérandes hors plage -> ValueError.

Couvre le sujet borné « Microprocesseurs » (volet logique/ALU, calculable).
Vérifié en adverse par `valide_microprocesseurs.py` (tables de vérité, additionneur, ALU avec flags).
"""
from __future__ import annotations


def porte(type_porte: str, a: int, b: int = 0) -> int:
    """Porte logique sur des bits (0/1). Types : 'et','ou','non','non-et','non-ou','ou-x','ou-x-non'."""
    for v in (a, b):
        if v not in (0, 1):
            raise ValueError("entrées binaires (0/1) requises")
    if type_porte == "non":
        return 1 - a
    if type_porte == "et":
        return a & b
    if type_porte == "ou":
        return a | b
    if type_porte == "ou-x":
        return a ^ b
    if type_porte == "non-et":
        return 1 - (a & b)
    if type_porte == "non-ou":
        return 1 - (a | b)
    if type_porte == "ou-x-non":
        return 1 - (a ^ b)
    raise ValueError(f"porte inconnue : {type_porte!r}")


def additionneur_complet(a: int, b: int, retenue_entrante: int = 0) -> tuple[int, int]:
    """Additionneur complet 1 bit : renvoie (somme, retenue_sortante). a,b,retenue ∈ {0,1}."""
    for v in (a, b, retenue_entrante):
        if v not in (0, 1):
            raise ValueError("bits (0/1) requis")
    total = a + b + retenue_entrante
    return (total & 1, total >> 1)


def alu(operation: str, a: int, b: int, bits: int = 8) -> dict:
    """ALU sur entiers NON signés de `bits` bits. operation ∈ {'add','sub','and','or','xor','not'}.
    Renvoie {resultat, zero, retenue, debordement}. Le résultat est tronqué à `bits` bits ; les flags sont calculés."""
    if not isinstance(bits, int) or isinstance(bits, bool) or bits <= 0:
        raise ValueError("bits > 0 requis")
    masque = (1 << bits) - 1
    for v in (a, b):
        if not isinstance(v, int) or isinstance(v, bool) or not (0 <= v <= masque):
            raise ValueError(f"opérande ∈ [0, 2^{bits}) requis")
    retenue = 0
    debordement = False
    if operation == "add":
        brut = a + b
        res = brut & masque
        retenue = 1 if brut > masque else 0
        sa, sb, sr = (a >> (bits - 1)) & 1, (b >> (bits - 1)) & 1, (res >> (bits - 1)) & 1
        debordement = (sa == sb) and (sr != sa)        # débordement signé
    elif operation == "sub":
        brut = a - b
        res = brut & masque
        retenue = 1 if a < b else 0                     # emprunt
        sa, sb, sr = (a >> (bits - 1)) & 1, (b >> (bits - 1)) & 1, (res >> (bits - 1)) & 1
        debordement = (sa != sb) and (sr != sa)
    elif operation == "and":
        res = a & b
    elif operation == "or":
        res = a | b
    elif operation == "xor":
        res = a ^ b
    elif operation == "not":
        res = (~a) & masque
    else:
        raise ValueError(f"opération ALU inconnue : {operation!r}")
    return {"resultat": res, "zero": int(res == 0), "retenue": retenue, "debordement": debordement}


if __name__ == "__main__":
    print("ET(1,1)/OU(0,0)/XOR(1,0)/NON(1) :", porte("et", 1, 1), porte("ou", 0, 0), porte("ou-x", 1, 0), porte("non", 1))
    print("NAND(1,1) :", porte("non-et", 1, 1))
    print("add complet 1+1+0 :", additionneur_complet(1, 1, 0), "| 1+1+1 :", additionneur_complet(1, 1, 1))
    print("ALU add 200+100 / 8 bits :", alu("add", 200, 100, 8))
    print("ALU add 100+28 / 8 bits :", alu("add", 100, 28, 8))
    print("ALU sub 50-50 :", alu("sub", 50, 50, 8))
    print("ALU and 0xF0 & 0x0F :", alu("and", 0xF0, 0x0F, 8))
