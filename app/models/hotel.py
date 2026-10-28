HOTEL_FIELDS = {
    "nom": {"type": "str"},
    "ville": {"type": "str"},
    "adresse": {"type": "str", "required": False},
    "etoiles": {"type": "int", "min": 1, "max": 5},
    "nb_chambres": {"type": "int", "min": 1},
}
