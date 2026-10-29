HOTEL_FIELDS = {
    "nom": {"type": "str", "max_len": 150},
    "ville": {"type": "str", "max_len": 100},
    "adresse": {"type": "str", "max_len": 255},
    "etoiles": {"type": "int", "min": 0, "max": 5},
    "nb_chambres": {"type": "int", "min": 1},
}