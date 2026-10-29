import pytest
from app.schemas.reservation_schema import validate_reservation, ValidationError

BASE = {"client_id": 1, "hotel_id": 1, "date_arrivee": "2026-11-01",
        "date_depart": "2026-11-05", "nb_personnes": 2}


def test_cas_normal_statut_par_defaut():
    assert validate_reservation(BASE)["statut"] == "EN_ATTENTE"


def test_statut_minuscule_normalise():
    assert validate_reservation({**BASE, "statut": "confirmee"})["statut"] == "CONFIRMEE"


def test_statut_invalide():
    with pytest.raises(ValidationError):
        validate_reservation({**BASE, "statut": "PAYEE"})


def test_depart_avant_arrivee():
    with pytest.raises(ValidationError):
        validate_reservation({**BASE, "date_depart": "2026-10-30"})


def test_depart_egal_arrivee():
    with pytest.raises(ValidationError):
        validate_reservation({**BASE, "date_depart": "2026-11-01"})


def test_date_invalide():
    with pytest.raises(ValidationError):
        validate_reservation({**BASE, "date_arrivee": "pas-une-date"})


def test_champ_manquant():
    bad = {k: v for k, v in BASE.items() if k != "hotel_id"}
    with pytest.raises(ValidationError):
        validate_reservation(bad)


def test_nb_personnes_nul():
    with pytest.raises(ValidationError):
        validate_reservation({**BASE, "nb_personnes": 0})


def test_identifiant_hors_limites():
    with pytest.raises(ValidationError) as e:
        validate_reservation({**BASE, "hotel_id": 2**31})
    assert "hotel_id" in e.value.details


@pytest.mark.parametrize("statut", [["CONFIRMEE"], {}, 1])
def test_statut_mauvais_type(statut):
    with pytest.raises(ValidationError) as e:
        validate_reservation({**BASE, "statut": statut})
    assert "statut" in e.value.details