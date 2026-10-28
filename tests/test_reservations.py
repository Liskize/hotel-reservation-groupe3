import pytest

from app import create_app

URL = "/api/v1/reservations"


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def ids(app):
    c = app.test_client()
    r_client = c.get("/api/v1/clients?per_page=1")
    r_hotel = c.get("/api/v1/hotels?per_page=1")
    if r_client.status_code != 200 or r_hotel.status_code != 200:
        pytest.skip("Base PostgreSQL non disponible")
    clients, hotels = r_client.get_json()["data"], r_hotel.get_json()["data"]
    if not clients or not hotels:
        pytest.skip("Base vide : seed.sql non chargé")
    return clients[0]["id"], hotels[0]["id"]


@pytest.fixture
def payload(ids):
    client_id, hotel_id = ids
    return {"client_id": client_id, "hotel_id": hotel_id,
            "date_arrivee": "2035-01-10", "date_depart": "2035-01-15",
            "nb_personnes": 2}


@pytest.fixture
def created(client, payload):
    r = client.post(URL, json=payload)
    assert r.status_code == 201
    res = r.get_json()
    yield res
    client.delete(f"{URL}/{res['id']}")


def test_creation_normale(created):
    assert created["statut"] == "EN_ATTENTE"
    assert created["date_arrivee"] == "2035-01-10"


def test_date_invalide_422(client, payload):
    r = client.post(URL, json={**payload, "date_depart": "2034-12-01"})
    assert r.status_code == 422
    assert r.get_json()["error"] == "validation_error"


def test_doublon_409(client, payload, created):
    r = client.post(URL, json=payload)
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"


def test_identifiant_inexistant_404(client):
    r = client.get(f"{URL}/999999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"


def test_client_inexistant_404(client, payload):
    r = client.post(URL, json={**payload, "client_id": 999999})
    assert r.status_code == 404


def test_hotel_inexistant_404(client, payload):
    r = client.post(URL, json={**payload, "hotel_id": 999999})
    assert r.status_code == 404


def test_json_absent_400(client):
    r = client.post(URL, data="pas du json", content_type="text/plain")
    assert r.status_code == 400


def test_lecture_par_id(client, created):
    r = client.get(f"{URL}/{created['id']}")
    assert r.status_code == 200
    assert r.get_json()["id"] == created["id"]


def test_modification(client, payload, created):
    r = client.put(f"{URL}/{created['id']}", json={**payload, "statut": "CONFIRMEE"})
    assert r.status_code == 200
    assert r.get_json()["statut"] == "CONFIRMEE"


def test_modification_inexistante_404(client, payload):
    assert client.put(f"{URL}/999999", json=payload).status_code == 404


def test_pagination_et_filtre_hotel(client, ids, created):
    _, hotel_id = ids
    r = client.get(f"{URL}?hotel_id={hotel_id}&per_page=2&page=1")
    body = r.get_json()
    assert r.status_code == 200
    assert body["per_page"] == 2
    assert len(body["data"]) <= 2
    assert all(i["hotel_id"] == hotel_id for i in body["data"])


def test_page_invalide_400(client):
    assert client.get(f"{URL}?page=abc").status_code == 400


def test_statut_filtre_invalide_400(client):
    assert client.get(f"{URL}?statut=PAYEE").status_code == 400


def test_suppression_204(client, payload):
    res = client.post(URL, json={**payload, "date_arrivee": "2036-02-01",
                                 "date_depart": "2036-02-03"}).get_json()
    assert client.delete(f"{URL}/{res['id']}").status_code == 204
    assert client.get(f"{URL}/{res['id']}").status_code == 404