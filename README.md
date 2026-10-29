# API REST de réservations hôtelières : Groupe 3 (SIE)

Projet « Développement à base de composants et services web » 2026.
Une API REST (Flask + PostgreSQL) gère des hôtels, des clients et des réservations. Un flux Apache NiFi l'alimente à partir d'un fichier CSV brut.

```
CSV brut  →  Apache NiFi (nettoyage, validation, recherche des ids)  →  PostgreSQL  →  API Flask (REST)  →  Postman / curl
```

## Équipe

| # | Rôle | Membre |
|---|---|---|
| 1 | Chef de projet, base de données, Docker | SANON Cheick Hadou (Liskize) |
| 2 | API : socle, hôtels, clients | WEDRAOGO Relwende |
| 3 | API : réservations | TEGA Lareine |
| 4 | NiFi | OUEDRAOGO Pégué Judicaël |
| 5 | Tests, documentation, présentation | SOME Enock |

## Sommaire

1. [Architecture](#architecture)
2. [Prérequis](#prérequis)
3. [Installation avec Docker (recommandée)](#installation-avec-docker-recommandée)
4. [Installation manuelle de l'API](#installation-manuelle-de-lapi)
5. [Utiliser l'API](#utiliser-lapi)
6. [Lancer les tests](#lancer-les-tests)
7. [Flux NiFi](#flux-nifi)
8. [Scénario de démonstration](#scénario-de-démonstration)
9. [Problèmes fréquents](#problèmes-fréquents)
10. [Limites connues](#limites-connues)

## Architecture

| Composant | Technologie | Conteneur | Port sur l'hôte |
|---|---|---|---|
| Base de données | PostgreSQL 18 | `hotel_groupe3_db` | 5433 |
| API | Flask 3 + gunicorn (Python 3.12) | `hotel_groupe3_api` | 5000 |
| Flux de données | Apache NiFi 2.7.2 | `hotel_groupe3_nifi` | 8443 (HTTPS) |

Tous les ports sont liés à `127.0.0.1` : ils ne sont accessibles que depuis la machine elle-même.

```
app/            code de l'API
  __init__.py     création de l'application Flask (create_app)
  config.py       lecture du .env
  db.py           connexion PostgreSQL (une par requête)
  errors.py       format d'erreur commun et codes HTTP
  crud.py         CRUD générique (hôtels, clients) : validation, pagination
  routes/         health, hotels, clients, reservations
  models/         champs des hôtels et clients, requêtes SQL des réservations
  schemas/        validation d'une réservation
database/       init.sql (tables, contraintes) et seed.sql (données de test)
nifi/           flux exporté (flow.json), CSV source, driver JDBC, README
docs/           contrat OpenAPI, dictionnaire de données, NiFi, scénario de bout en bout
postman/        collection et environnement Postman
presentation/   PowerPoint
tests/          tests pytest
```

Le modèle de données (3 tables, contraintes, relations) est décrit dans [docs/dictionnaire-donnees.md](docs/dictionnaire-donnees.md).

## Prérequis

- Git
- Docker Desktop (Windows, macOS) ou Docker Engine (Linux) avec Docker Compose v2 : `docker compose version` doit répondre
- 4 Go de RAM libres si NiFi est lancé
- Pour l'installation manuelle et pour pytest : Python 3.12
- Pour les tests Postman : Postman (application) ou Newman

## Installation avec Docker (recommandée)

**1. Récupérer le projet et créer le fichier `.env`**

```bash
git clone https://github.com/Liskize/hotel-reservation-groupe3.git
cd hotel-reservation-groupe3
cp .env.example .env
```

Sous Windows (PowerShell), remplacer `cp` par `Copy-Item .env.example .env`.

Ouvrir `.env` et changer les deux mots de passe :

- `POSTGRES_PASSWORD` : mot de passe de la base ;
- `NIFI_PASSWORD` : **12 caractères minimum**, sinon NiFi ignore les identifiants et en génère d'autres.

**2. Démarrer la base et l'API**

```bash
docker compose --profile application up -d --build db api
```

La première fois, la construction de l'image prend une à deux minutes. Au premier démarrage, PostgreSQL exécute `database/init.sql` puis `database/seed.sql` : la base contient alors **3 hôtels, 5 clients et 10 réservations**.

**3. Vérifier**

```bash
curl http://127.0.0.1:5000/api/v1/health
# {"database":"up","status":"ok"}

curl "http://127.0.0.1:5000/api/v1/reservations?per_page=2"
# {"data":[...2 réservations...],"page":1,"per_page":2,"total":10}
```

On peut aussi ouvrir http://127.0.0.1:5000/api/v1/hotels dans un navigateur.

**4. Arrêter**

```bash
docker compose --profile application down       # arrête, garde les données
docker compose --profile application down -v    # arrête et efface la base (repart du seed)
```

## Installation manuelle de l'API

Pour développer sans reconstruire l'image. Il faut une base PostgreSQL : le plus simple est de lancer uniquement le conteneur `db`.

```bash
docker compose up -d db
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python run.py                      # http://127.0.0.1:5000 (mode debug)
```

L'API lit le même `.env` : `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` (5433) et `POSTGRES_HOST` (par défaut `localhost`). Si le conteneur `api` tourne déjà sur le port 5000, l'arrêter d'abord (`docker compose stop api`).

Pour utiliser une base PostgreSQL déjà installée sur la machine : créer la base, exécuter `database/init.sql` puis `database/seed.sql` avec `psql`, et adapter les variables `POSTGRES_*` du `.env`.

## Utiliser l'API

Préfixe : `/api/v1`. Contrat complet : [docs/openapi.yaml](docs/openapi.yaml) (à ouvrir dans https://editor.swagger.io : *File > Import file*).

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | État de l'API et de la base |
| GET, POST | `/hotels` | Liste paginée, création |
| GET, PUT, DELETE | `/hotels/{id}` | Lecture, modification, suppression |
| GET, POST | `/clients` | Liste paginée, création |
| GET, PUT, DELETE | `/clients/{id}` | Lecture, modification, suppression |
| GET, POST | `/reservations` | Liste paginée et filtrée, création |
| GET, PUT, DELETE | `/reservations/{id}` | Lecture, modification, suppression |

`PUT` remplace la ressource entière : tous les champs obligatoires doivent être envoyés.

**Pagination** : `?page=1&per_page=10` (10 par défaut ; au-delà de 100, la valeur est ramenée à 100).
Réponse : `{"data": [...], "page": 1, "per_page": 10, "total": 10}`.

**Filtres sur `/reservations`** : `hotel_id`, `client_id`, `statut` (`EN_ATTENTE`, `CONFIRMEE`, `ANNULEE`), `date_debut` (arrivée ≥ cette date) et `date_fin` (départ ≤ cette date), au format `AAAA-MM-JJ`. Ils se combinent :

```bash
curl "http://127.0.0.1:5000/api/v1/reservations?hotel_id=1&statut=CONFIRMEE&date_debut=2026-11-01&date_fin=2026-11-30"
```

**Créer une réservation** (`statut` est facultatif, `EN_ATTENTE` par défaut) :

```bash
curl -X POST http://127.0.0.1:5000/api/v1/reservations \
  -H "Content-Type: application/json" \
  -d '{"client_id":1,"hotel_id":1,"date_arrivee":"2035-05-01","date_depart":"2035-05-03","nb_personnes":2}'
```

Sous PowerShell, utiliser `curl.exe` et échapper les guillemets, ou plus simplement `Invoke-RestMethod` :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/v1/reservations -ContentType "application/json" `
  -Body '{"client_id":1,"hotel_id":1,"date_arrivee":"2035-05-01","date_depart":"2035-05-03","nb_personnes":2}'
```

### Codes d'erreur

Toutes les erreurs ont le même format :

```json
{"error": "validation_error", "message": "date_depart doit être après date_arrivee", "details": {}}
```

| Code | `error` | Cas |
|---|---|---|
| 400 | `bad_request` | Corps JSON absent ou invalide, `page` ou filtre mal formé |
| 404 | `not_found` | Identifiant inexistant (ou client / hôtel référencé par une réservation inexistant) |
| 409 | `conflict` | Réservation en double, email client déjà utilisé, hôtel (nom + ville) déjà existant, suppression d'un hôtel ou d'un client qui a des réservations (voir le [bug connu](#limites-connues)) |
| 422 | `validation_error` | Champ obligatoire manquant, date invalide, `date_depart` ≤ `date_arrivee`, `nb_personnes` ≤ 0, statut inconnu, email invalide, `etoiles` hors de 0 à 5 |
| 503 | `database_unavailable` | Base injoignable |

Pour une réservation, les contrôles sont faits dans cet ordre : 400, puis 422, puis 404 (client, hôtel), puis 409 (doublon).
Un **doublon** est une réservation avec les mêmes `client_id`, `hotel_id`, `date_arrivee` et `date_depart` (contrainte `uq_reservation`).

## Lancer les tests

### Tests automatisés (pytest)

**40 tests** : 8 tests unitaires de validation (sans base) et 32 tests sur la vraie API avec la vraie base PostgreSQL. Ces derniers sont ignorés (*skipped*) si la base est injoignable. Les tests créent leurs propres données et les suppriment.

```bash
docker compose up -d db              # la base doit tourner
pip install -r requirements.txt      # dans le .venv, voir l'installation manuelle
pytest -v
```

Résultat attendu : `39 passed, 1 xfailed`. Le test marqué `xfail` correspond au [bug connu](#limites-connues) de la suppression d'un hôtel lié ; il passera automatiquement (`XPASS`) une fois le bug corrigé.

| Fichier | Ce qui est testé |
|---|---|
| `tests/test_reservation_schema.py` | Validation d'une réservation : statut par défaut, dates, champs manquants, `nb_personnes` |
| `tests/test_reservations.py` | CRUD réservations, doublon 409, 404, 422, 400, pagination, filtres |
| `tests/test_hotels_clients.py` | Santé, CRUD hôtels et clients, unicité (409), validation (422), suppression d'un hôtel lié (409), format d'erreur |

### Tests Postman

1. Dans Postman : *Import*, puis choisir les deux fichiers du dossier `postman/` :
   - `hotel-reservation-api.postman_collection.json` (la collection) ;
   - `hotel-reservation-local.postman_environment.json` (l'environnement, `baseUrl = http://127.0.0.1:5000/api/v1`).
2. Sélectionner l'environnement « Hotel Reservation - local » en haut à droite.
3. Clic droit sur la collection, *Run collection*, puis *Run*.

Résultat attendu : **50 requêtes, 102 assertions**. Tant que le [bug connu](#limites-connues) n'est pas corrigé, les 4 assertions des deux requêtes « Supprimer l'hôtel utilisé (409) » et « Supprimer le client utilisé (409) » échouent (l'API répond 500) ; toutes les autres passent. La collection crée son propre hôtel, client et réservation, puis les supprime : on peut la relancer autant de fois que nécessaire.

| Dossier | Contenu |
|---|---|
| 1. Santé | `GET /health` |
| 2. Hôtels | CRUD, liste paginée, doublon nom + ville (409), champs manquants et 6 étoiles (422), 404 |
| 3. Clients | CRUD, liste paginée, email en double (409), email invalide (422), 404 |
| 4. Réservations : cas normaux | Création, lecture, pagination (page 1, page 2, plafond 100), filtres `hotel_id`, `client_id`, `statut`, période |
| 5. Réservations : erreurs | Doublon (409), dates incohérentes, champs manquants, `nb_personnes = 0`, date mal formée, statut inconnu (422), client / hôtel / réservation inexistants (404), corps non JSON et paramètres invalides (400) |
| 6. Suppressions et nettoyage | Suppression d'un hôtel ou client lié (409), suppression (204), relecture (404), nettoyage |

Sans Postman, la même collection se lance en ligne de commande avec Newman (Node.js ou Docker) :

```bash
npx newman run postman/hotel-reservation-api.postman_collection.json
# ou, sans Node.js :
docker run --rm -v "$(pwd)/postman:/etc/newman" postman/newman:6-alpine \
  run hotel-reservation-api.postman_collection.json --env-var baseUrl=http://host.docker.internal:5000/api/v1
```

## Flux NiFi

Le flux lit `nifi/data/reservations_brutes.csv` (8 lignes, dont des cas invalides), convertit les dates `jj/mm/aaaa` en `aaaa-mm-jj`, écarte les lignes invalides, retrouve `client_id` (par email) et `hotel_id` (par nom), puis insère les réservations valides dans PostgreSQL.

```bash
docker compose up -d db nifi
docker compose logs -f nifi      # attendre « NiFi has started » (1 à 2 minutes), puis Ctrl+C
```

Interface : https://localhost:8443/nifi (certificat auto-signé à accepter ; identifiants `NIFI_USERNAME` et `NIFI_PASSWORD` du `.env`).

Import du flux, saisie du mot de passe de la base et exécution pas à pas : [nifi/README.md](nifi/README.md). Explications détaillées, schéma et résultats attendus : [docs/nifi.md](docs/nifi.md).

Résultat attendu : **3 réservations insérées sur 8 lignes**. Les 5 autres sont écartées : départ avant arrivée, email vide, 0 personne, hôtel inconnu, doublon.

## Scénario de démonstration

Le scénario complet, commande par commande, est dans [docs/scenario-e2e.md](docs/scenario-e2e.md). En résumé :

1. Démarrer tout : `docker compose --profile application up -d --build`.
2. Compter les réservations : **10** (données du seed).
   ```bash
   docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "select count(*) from reservations;"
   ```
3. Dans NiFi, importer `nifi/flow.json` et lancer le flux sur le CSV.
4. Compter de nouveau : **13**. Les 5 lignes invalides ont été écartées.
5. Consulter dans l'API : `GET /api/v1/reservations?page=2` : les 3 nouvelles réservations apparaissent en fin de liste.
6. Dans Postman : créer, modifier et supprimer une réservation, puis déclencher une erreur 422 et un doublon 409.

## Variables d'environnement

| Variable | Rôle | Valeur dans `.env.example` |
|---|---|---|
| `POSTGRES_DB` | Nom de la base | `hotel_reservation_db` |
| `POSTGRES_USER` | Utilisateur | `hotel_app` |
| `POSTGRES_PASSWORD` | Mot de passe (à changer) | `change_this_db_password` |
| `POSTGRES_PORT` | Port de la base sur l'hôte | `5433` |
| `POSTGRES_HOST` | Hôte de la base, pour l'API hors Docker (facultatif) | `localhost` par défaut |
| `FLASK_PORT` | Port de l'API sur l'hôte | `5000` |
| `NIFI_PORT` | Port HTTPS de NiFi | `8443` |
| `NIFI_USERNAME` / `NIFI_PASSWORD` | Connexion à NiFi (12 caractères minimum) | `admin` / à changer |

Dans Docker, l'API reçoit `DATABASE_URL`, construite par `docker-compose.yml` à partir de ces variables. Le fichier `.env` ne doit jamais être commité (il est dans `.gitignore`).

## Problèmes fréquents

| Symptôme | Solution |
|---|---|
| `failed to connect to the docker API` | Docker Desktop n'est pas lancé : le démarrer et attendre qu'il soit prêt |
| `port is already allocated` | Un autre programme utilise le port : changer `POSTGRES_PORT`, `FLASK_PORT` ou `NIFI_PORT` dans `.env` |
| La base est vide ou les tables n'existent pas | `init.sql` et `seed.sql` ne s'exécutent qu'à la création du volume : `docker compose --profile application down -v`, puis relancer |
| `password authentication failed` après un changement de mot de passe | Même cause : le volume garde l'ancien mot de passe. `down -v` puis relancer |
| `{"error": "database_unavailable"}` (503) | La base ne tourne pas ou les variables `POSTGRES_*` du `.env` ne correspondent pas |
| Tests pytest très lents sous Windows (près d'une minute) | `localhost` est d'abord résolu en IPv6 : ajouter `POSTGRES_HOST=127.0.0.1` dans `.env` |
| Tous les tests d'API sont *skipped* | La base n'est pas joignable : `docker compose up -d db` |
| NiFi ne répond pas | Attendre 2 minutes, vérifier `docker compose logs nifi` et la RAM disponible |
| Impossible de se connecter à NiFi | `NIFI_PASSWORD` fait moins de 12 caractères |
| `postgresql.jar` absent | `curl -L -o nifi/drivers/postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.7.4.jar` |
| Fedora / SELinux : `Permission denied` | Les volumes utilisent déjà l'option `:z` ; vérifier qu'elle n'a pas été retirée |

## Limites connues

- **Bug connu (à corriger dans `app/errors.py`)** : supprimer un hôtel ou un client qui a des réservations renvoie `500 internal_error` au lieu de `409 conflict`. Avec `ON DELETE RESTRICT` (voir `init.sql`), PostgreSQL lève `RestrictViolation`, alors que le gestionnaire d'erreurs n'intercepte que `ForeignKeyViolation`. La suppression est bien refusée (aucune donnée perdue), seul le code HTTP est faux. Détecté par `tests/test_hotels_clients.py` et la collection Postman.
- Le flux NiFi est lancé manuellement (« Run Once ») et n'écrit pas encore les lignes rejetées dans `nifi/data/rejets/` : elles sont abandonnées dans NiFi.
- La disponibilité des chambres n'est pas contrôlée : seule une réservation strictement identique (même client, hôtel et dates) est refusée.
- L'API n'a pas d'authentification.
- Le mot de passe de la base doit être ressaisi dans NiFi après chaque import du flux (NiFi n'exporte jamais les valeurs sensibles).

## Documentation

| Document | Contenu |
|---|---|
| [docs/openapi.yaml](docs/openapi.yaml) | Contrat OpenAPI 3 de l'API |
| [docs/dictionnaire-donnees.md](docs/dictionnaire-donnees.md) | Tables, colonnes, contraintes, relations |
| [docs/nifi.md](docs/nifi.md) | Flux NiFi détaillé |
| [docs/scenario-e2e.md](docs/scenario-e2e.md) | Démonstration de bout en bout |
| [presentation/](presentation/) | Support de soutenance |
