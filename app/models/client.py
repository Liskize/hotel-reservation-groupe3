CLIENT_FIELDS = {
    "nom": {"type": "str"},
    "prenom": {"type": "str"},
    "email": {"type": "email"},
    "telephone": {"type": "str", "required": False, "max_len": 30},
}
