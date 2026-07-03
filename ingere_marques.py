"""
INGESTION ÉCONOMIE — marque -> pays d'origine (auto / tech / luxe)  -> datasets/lecteur/*.jsonl (OFFLINE).

SOURCE : connaissance économique de référence. Faits STABLES et CERTAINS = PAYS D'ORIGINE de la marque
(indépendant du propriétaire actuel, qui peut changer : Jaguar=origine RU même si Tata, Volvo=origine
Suède même si Geely). FAUX=0 : on garde les origines NON CONTESTÉES. Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_AUTO = {
    "France": ["renault", "peugeot", "citroën", "bugatti", "ds"],
    "Allemagne": ["volkswagen", "bmw", "mercedes", "audi", "porsche", "opel"],
    "Italie": ["ferrari", "fiat", "lamborghini", "maserati", "alfa romeo"],
    "Japon": ["toyota", "honda", "nissan", "mazda", "subaru", "mitsubishi", "suzuki"],
    "États-Unis": ["ford", "chevrolet", "tesla", "cadillac", "jeep"],
    "Corée du Sud": ["hyundai", "kia"],
    "Suède": ["volvo"],
    "Royaume-Uni": ["jaguar", "land rover", "bentley", "rolls-royce", "mini", "aston martin"],
    "République tchèque": ["skoda"],
    "Espagne": ["seat"],
}
_TECH = {
    "États-Unis": ["apple", "microsoft", "google", "intel", "ibm", "dell", "hp", "nvidia", "amd", "oracle"],
    "Corée du Sud": ["samsung", "lg"],
    "Japon": ["sony", "nintendo", "panasonic", "toshiba", "canon", "nikon"],
    "Finlande": ["nokia"],
    "Suède": ["ericsson", "spotify"],
    "Allemagne": ["siemens", "sap", "bosch"],
    "Pays-Bas": ["philips", "asml"],
    "Chine": ["lenovo", "huawei", "xiaomi", "alibaba", "tencent"],
    "Taïwan": ["acer", "asus", "tsmc"],
}
_LUXE = {
    "France": ["louis vuitton", "chanel", "hermès", "dior", "cartier", "yves saint laurent"],
    "Italie": ["gucci", "prada", "versace", "armani", "dolce & gabbana", "fendi", "bulgari"],
    "Suisse": ["rolex", "patek philippe", "omega"],
    "Royaume-Uni": ["burberry"],
    "États-Unis": ["tiffany"],
}

def _paires(d):
    return [(m, pays) for pays, marques in d.items() for m in marques]

def ingere():
    print("== MARQUES -> PAYS (auto / tech / luxe) ==")
    publie("pays_marque_auto", "convention", "économie de référence (marque auto -> pays d'origine)", _paires(_AUTO))
    publie("pays_marque_tech", "convention", "économie de référence (marque tech -> pays d'origine)", _paires(_TECH))
    publie("pays_marque_luxe", "convention", "économie de référence (marque de luxe -> pays d'origine)", _paires(_LUXE))

if __name__ == "__main__":
    ingere()
