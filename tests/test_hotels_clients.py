import uuid

import pytest

from app import create_app

HOTELS = "/api/v1/hotels"
CLIENTS = "/api/v1/clients"


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="module", autouse=True)
def base_disponible(app):
    if app.test_client().get("/api/v1/health").status_code != 200:
        pytest.skip("Base PostgreSQL non disponible")


@pytest.fixture
def hotel(client):
    r = client.post(HOTELS, json={"nom": f"Hotel Test {uuid.uuid4().hex[:8]}", "ville": "Koudougou",
                                  "adresse": "Rue test", "etoiles": 3, "nb_chambres": 20})
    assert r.status_code == 201
    h = r.get_json()
    yield h
    client.delete(f"{HOTELS}/{h['id']}")


@pytest.fixture
def client_cree(client):
    r = client.post(CLIENTS, json={"nom": "TEST", "prenom": "Pytest",
                                   "email": f"pytest{uuid.uuid4().hex[:8]}@example.com",
                                   "telephone": "70000098"})
    assert r.status_code == 201
    c = r.get_json()
    yield c
    client.delete(f"{CLIENTS}/{c['id']}")


def test_health(client):
    assert client.get("/api/v1/health").get_json() == {"status": "ok", "database": "up"}


def test_route_inconnue_404_format_commun(client):
    r = client.get("/api/v1/inexistant")
    assert r.status_code == 404
    assert set(r.get_json()) == {"error", "message", "details"}


# --- Hôtels ---

def test_liste_hotels_paginee(client):
    body = client.get(f"{HOTELS}?page=1&per_page=2").get_json()
    assert body["page"] == 1 and body["per_page"] == 2
    assert len(body["data"]) <= 2
    assert isinstance(body["total"], int)


def test_per_page_plafonne_a_100(client):
    assert client.get(f"{HOTELS}?per_page=500").get_json()["per_page"] == 100


def test_lecture_hotel(client, hotel):
    r = client.get(f"{HOTELS}/{hotel['id']}")
    assert r.status_code == 200
    assert r.get_json()["nom"] == hotel["nom"]


def test_modification_hotel(client, hotel):
    r = client.put(f"{HOTELS}/{hotel['id']}", json={**hotel, "etoiles": 5})
    assert r.status_code == 200
    assert r.get_json()["etoiles"] == 5


def test_hotel_doublon_nom_ville_409(client, hotel):
    r = client.post(HOTELS, json={k: v for k, v in hotel.items() if k != "id"})
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"


def test_hotel_champ_manquant_422(client):
    r = client.post(HOTELS, json={"nom": "Incomplet"})
    assert r.status_code == 422
    assert "ville" in r.get_json()["details"]


def test_hotel_etoiles_hors_bornes_422(client):
    r = client.post(HOTELS, json={"nom": "X", "ville": "Y", "adresse": "Z",
                                  "etoiles": 6, "nb_chambres": 10})
    assert r.status_code == 422
    assert "etoiles" in r.get_json()["details"]


def test_hotel_inexistant_404(client):
    r = client.get(f"{HOTELS}/999999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"


@pytest.mark.xfail(reason="Bug connu : ON DELETE RESTRICT lève RestrictViolation, non gérée par "
                          "app/errors.py (500 au lieu de 409)", strict=False)
def test_suppression_hotel_lie_409(client, hotel, client_cree):
    res = client.post("/api/v1/reservations", json={
        "client_id": client_cree["id"], "hotel_id": hotel["id"],
        "date_arrivee": "2037-03-01", "date_depart": "2037-03-04", "nb_personnes": 1}).get_json()
    try:
        r = client.delete(f"{HOTELS}/{hotel['id']}")
        assert r.status_code == 409
    finally:
        client.delete(f"/api/v1/reservations/{res['id']}")


def test_suppression_hotel_204(client, hotel):
    assert client.delete(f"{HOTELS}/{hotel['id']}").status_code == 204
    assert client.get(f"{HOTELS}/{hotel['id']}").status_code == 404


# --- Clients ---

def test_lecture_client(client, client_cree):
    r = client.get(f"{CLIENTS}/{client_cree['id']}")
    assert r.status_code == 200
    assert r.get_json()["email"] == client_cree["email"]


def test_modification_client(client, client_cree):
    r = client.put(f"{CLIENTS}/{client_cree['id']}", json={**client_cree, "telephone": "76000000"})
    assert r.status_code == 200
    assert r.get_json()["telephone"] == "76000000"


def test_client_email_doublon_409(client, client_cree):
    r = client.post(CLIENTS, json={k: v for k, v in client_cree.items() if k != "id"})
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"


def test_client_email_invalide_422(client):
    r = client.post(CLIENTS, json={"nom": "A", "prenom": "B", "email": "pas-un-email",
                                   "telephone": "70000000"})
    assert r.status_code == 422
    assert r.get_json()["details"]["email"] == "email invalide"


def test_client_inexistant_put_404(client):
    r = client.put(f"{CLIENTS}/999999", json={"nom": "A", "prenom": "B",
                                              "email": "a@example.com", "telephone": "1"})
    assert r.status_code == 404


def test_client_corps_non_json_400(client):
    r = client.post(CLIENTS, data="pas du json", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["error"] == "bad_request"
