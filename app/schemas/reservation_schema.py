from datetime import datetime

STATUTS = {"EN_ATTENTE", "CONFIRMEE", "ANNULEE"}
STATUT_DEFAUT = "EN_ATTENTE"
MAX_INT = 2147483647  # INTEGER PostgreSQL
REQUIRED = ["client_id", "hotel_id", "date_arrivee", "date_depart", "nb_personnes"]


class ValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def _positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 < value <= MAX_INT


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def validate_reservation(data):
    """Valide le corps JSON et renvoie un dict nettoyé, sinon lève ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError("Corps JSON invalide")

    missing = [f for f in REQUIRED if data.get(f) in (None, "")]
    if missing:
        raise ValidationError("Champs obligatoires manquants", {"missing": missing})

    details = {}
    for f in ("client_id", "hotel_id", "nb_personnes"):
        if not _positive_int(data[f]):
            details[f] = f"entier entre 1 et {MAX_INT} attendu"

    dates = {}
    for f in ("date_arrivee", "date_depart"):
        try:
            dates[f] = _parse_date(data[f])
        except (TypeError, ValueError):
            details[f] = "date invalide, format attendu YYYY-MM-DD"

    statut = data.get("statut")
    if statut is None or statut == "":
        statut = STATUT_DEFAUT
    # une liste ou un objet ferait planter le test d'appartenance (TypeError)
    if not isinstance(statut, str) or statut.strip().upper() not in STATUTS:
        details["statut"] = f"valeur attendue parmi {sorted(STATUTS)}"
    else:
        statut = statut.strip().upper()

    if details:
        raise ValidationError("Données invalides", details)

    if dates["date_depart"] <= dates["date_arrivee"]:
        raise ValidationError("date_depart doit être après date_arrivee")

    return {
        "client_id": data["client_id"],
        "hotel_id": data["hotel_id"],
        "date_arrivee": dates["date_arrivee"],
        "date_depart": dates["date_depart"],
        "nb_personnes": data["nb_personnes"],
        "statut": statut,
    }