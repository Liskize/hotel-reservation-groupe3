# Scénario de démonstration de bout en bout

Ce scénario montre toute la chaîne du projet, dans l'ordre où les données circulent :

```text
1. Dépôt du CSV  →  2. Passage dans NiFi  →  3. Consultation dans l'API  →  4. Tests dans Postman
```

Durée : environ 10 minutes, en comptant le démarrage de NiFi (à lancer avant la soutenance).
Les commandes sont à exécuter à la racine du dépôt. Sous Windows, utiliser Git Bash ou adapter (`curl.exe`, `Invoke-RestMethod`).

---

## 0. Préparation (avant la démonstration)

```bash
cp .env.example .env                                  # puis changer POSTGRES_PASSWORD et NIFI_PASSWORD (12 car. min)
docker compose --profile application down -v          # repartir d'une base vierge
docker compose --profile application up -d --build    # base + API + NiFi
docker compose logs -f nifi                           # attendre « NiFi has started », puis Ctrl+C
```

| Vérification | Commande | Attendu |
|---|---|---|
| API et base | `curl http://127.0.0.1:5000/api/v1/health` | `{"status":"ok","database":"up"}` |
| NiFi | ouvrir https://localhost:8443/nifi | page de connexion NiFi |
| Postman | importer `postman/*.json`, choisir l'environnement « Hotel Reservation - local » | collection visible |

Préparer aussi le flux dans NiFi (une seule fois, voir [nifi/README.md](../nifi/README.md)) : importer `nifi/flow.json` dans un Process Group, saisir le mot de passe de la base dans `DBCPConnectionPool`, activer les 6 Controller Services. **Ne lancer aucun processor.**

---

## 1. Dépôt du CSV de réservations brutes

**Ce qu'on dit** : « Un partenaire nous envoie un export CSV de réservations. Il est sale : formats de date différents, champs vides, incohérences, doublons. »

```bash
cat nifi/data/reservations_brutes.csv
```

Le dossier `nifi/data/` est monté dans le conteneur NiFi (`/opt/nifi/shared/data`) : déposer un fichier dans ce dossier suffit pour que NiFi le voie.

| # | Ligne | Problème | Ce que doit faire NiFi |
|---|---|---|---|
| 1 | cheicki, Hotel Splendid, 2026-11-10 → 2026-11-14 | aucun | **insérer** |
| 2 | enock, Hotel Sonia, 15/11/2026 → 18/11/2026 | dates `jj/mm/aaaa` | convertir, puis **insérer** |
| 3 | lareine, Hotel Sissiman, 2026-12-01 → 2026-12-05 | aucun | **insérer** |
| 4 | diane, Hotel Splendid, 2026-12-10 → 2026-12-08 | départ avant arrivée | rejeter |
| 5 | *(email vide)*, Hotel Sonia | champ obligatoire vide | rejeter |
| 6 | judicael, Hotel Inconnu | hôtel absent de la base | rejeter |
| 7 | cheicki, Hotel Splendid, 2026-11-10 → 2026-11-14 | doublon exact de la ligne 1 | rejeter (contrainte `uq_reservation`) |
| 8 | enock, Hotel Sonia, `nb_personnes` = 0 | valeur invalide | rejeter |

État de la base **avant** :

```bash
docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "select count(*) from reservations;"
```

Attendu : **10** (les données de `database/seed.sql`).

---

## 2. Passage dans NiFi

**Ce qu'on dit** : « NiFi est notre ETL : il extrait le CSV, le transforme et le charge dans PostgreSQL. Chaque réservation est traitée séparément, donc une ligne invalide ne bloque pas les autres. »

Dans https://localhost:8443/nifi, ouvrir le groupe `reservations-hotel` et lancer chaque processor avec **clic droit > Run Once**, dans l'ordre, en montrant le compteur *Queued* des flèches :

| Processor | Rôle | Compteur attendu après exécution |
|---|---|---|
| GetFile | lit le CSV | 1 FlowFile |
| UpdateAttribute | point de passage | 1 FlowFile |
| ReplaceText | `15/11/2026` → `2026-11-15` | 1 FlowFile |
| QueryRecord | sépare `valides` / `rejetes` (email, dates, nb_personnes, statut) | lignes 4, 5 et 8 rejetées |
| SplitRecord | une réservation par FlowFile | **5** FlowFiles |
| Chercher client_id | email → `client_id` | **5** `matched` |
| Chercher hotel_id | nom → `hotel_id` | **4** `matched` (« Hotel Inconnu » écarté) |
| PutDatabaseRecord | `INSERT` dans `reservations` | 3 insérées, le doublon est refusé par la base |

Après SplitRecord, plusieurs FlowFiles attendent : refaire *Run Once* jusqu'à vider la file, ou *Start*, attendre 5 secondes, puis *Stop*. Ne pas laisser GetFile en marche : il relirait le fichier toutes les 30 secondes.

État de la base **après** :

```bash
docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "select count(*) from reservations;"
```

Attendu : **13** (10 + 3). Bilan : 8 lignes, 3 chargées, 5 écartées.

**Point à souligner** : relancer le flux ne change rien (le compte reste à 13), car la contrainte d'unicité de la base refuse les doublons. Le chargement est **idempotent**.

---

## 3. Consultation dans l'API

**Ce qu'on dit** : « Les réservations chargées par NiFi sont immédiatement disponibles dans l'API REST, avec pagination et filtres. »

```bash
# Liste paginée : total = 13, les 3 nouvelles sont sur la page 2
curl "http://127.0.0.1:5000/api/v1/reservations?page=2"

# Filtre par période : les réservations de décembre (dont celle de lareine chargée par NiFi)
curl "http://127.0.0.1:5000/api/v1/reservations?date_debut=2026-12-01&date_fin=2026-12-31"

# Filtres combinés : réservations confirmées d'un hôtel
curl "http://127.0.0.1:5000/api/v1/reservations?hotel_id=1&statut=CONFIRMEE"
```

Pour la ligne 2 du CSV, montrer que la date `15/11/2026` est bien arrivée sous la forme `"date_arrivee": "2026-11-15"`.

Requête SQL pour montrer les 3 lignes chargées avec l'email et le nom de l'hôtel :

```bash
docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "select r.id, c.email, h.nom, r.date_arrivee, r.date_depart, r.statut from reservations r join clients c on c.id = r.client_id join hotels h on h.id = r.hotel_id where r.id > 10 order by r.id;"
```

---

## 4. Tests dans Postman

**Ce qu'on dit** : « L'API applique les mêmes règles que NiFi, et renvoie toujours une erreur au même format. »

### 4.1 Démonstration manuelle (requêtes de la collection)

| Étape | Requête dans la collection | Attendu |
|---|---|---|
| Créer | 2. Hôtels > Créer un hôtel ; 3. Clients > Créer un client ; 4. Réservations > Créer une réservation | `201`, `statut = EN_ATTENTE` |
| Lire | 4 > Lire la réservation | `200` |
| Modifier | 4 > Modifier la réservation | `200`, `statut = CONFIRMEE` |
| Erreur 422 | 5 > Départ avant arrivée | `422`, `"error": "validation_error"`, `"message": "date_depart doit être après date_arrivee"` |
| Doublon 409 | 5 > Doublon | `409`, `"error": "conflict"` |
| Erreur 404 | 5 > Client inexistant | `404`, `"error": "not_found"` |
| Supprimer | 6 > Supprimer la réservation | `204`, puis la relecture renvoie `404` |

Les requêtes de création enregistrent les identifiants (`hotelId`, `clientId`, `resId`) dans les variables de la collection : les requêtes suivantes les réutilisent sans rien recopier.

### 4.2 Exécution complète (Runner)

Clic droit sur la collection > *Run collection* > *Run*.
Attendu : **50 requêtes, 102 assertions, toutes réussies** (dont la suppression d'un hôtel ou client lié, refusée en 409). La collection supprime à la fin tout ce qu'elle a créé.

### 4.3 Tests automatisés

```bash
pytest -v
```

Attendu : **52 passed**.

---

## Rejouer la démonstration

Supprimer uniquement les 3 réservations chargées par NiFi :

```bash
docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "delete from reservations where id > 10;"
```

Ou repartir de zéro (base vierge, seed rechargé) :

```bash
docker compose --profile application down -v
docker compose --profile application up -d --build
```

Après un `down -v`, il faut ressaisir le mot de passe de la base dans le `DBCPConnectionPool` de NiFi si le conteneur NiFi a été recréé.

## En cas de problème pendant la démonstration

| Symptôme | Réaction |
|---|---|
| L'API renvoie `503 database_unavailable` | `docker compose ps` : la base doit être *healthy* |
| NiFi : `DBCPConnectionPool` invalide | Le mot de passe de la base n'a pas été saisi, ou le service n'est pas activé |
| Le compte reste à 10 après le flux | Vérifier les files *Queued* : un processor n'a pas été lancé, ou les FlowFiles attendent encore |
| Le compte reste à 13 quand on relance le flux | Normal : les lignes sont déjà en base, les doublons sont refusés (voir « Rejouer ») |
| Postman : erreur de connexion | Vérifier la variable `baseUrl` et que l'environnement « Hotel Reservation - local » est sélectionné |
