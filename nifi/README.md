# Flux NiFi : chargement des réservations

## Rôle
Lire `nifi/data/reservations_brutes.csv`, normaliser les dates, valider les
lignes, retrouver les identifiants du client et de l'hôtel, puis charger la
table `reservations` de PostgreSQL.

## Prérequis
- Docker et Docker Compose
- Driver PostgreSQL : `nifi/drivers/postgresql.jar`. S'il est absent, le télécharger :

      curl -L -o nifi/drivers/postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.7.4.jar

- Sur Fedora (SELinux), les volumes du `docker-compose.yml` utilisent l'option `:z`.

## Lancer

    docker compose up -d db nifi

Interface : https://localhost:8443/nifi (identifiants : `NIFI_USERNAME` et
`NIFI_PASSWORD` du fichier `.env`, mot de passe de 12 caractères minimum).
NiFi met 1 à 2 minutes à démarrer.

## Importer le flux
1. Glisser l'icône « Process Group » sur le canvas.
2. Utiliser l'icône de téléversement à côté du nom, puis choisir `nifi/flow.json`.
3. Ouvrir le groupe, puis ses « Controller Services » : saisir le mot de passe
   de la base dans `DBCPConnectionPool` (il n'est pas exporté), puis activer
   les services (DBCPConnectionPool, CSVReader, JsonTreeReader,
   JsonRecordSetWriter, ClientLookup, HotelLookup).

## Chaîne de traitement
GetFile → UpdateAttribute → ReplaceText → QueryRecord → SplitRecord →
LookupRecord (client_id) → LookupRecord (hotel_id) → PutDatabaseRecord

| Étape | Rôle |
|---|---|
| GetFile | Lit le CSV (le fichier source est conservé) |
| ReplaceText | Convertit les dates `jj/mm/aaaa` en `aaaa-mm-jj` |
| QueryRecord | Sépare `valides` et `rejetes` (email, dates, nb_personnes, statut) |
| SplitRecord | Un FlowFile par réservation |
| LookupRecord x2 | Retrouve `client_id` (par email) et `hotel_id` (par nom) |
| PutDatabaseRecord | Insère dans `reservations` (statement type INSERT) |

## Exécution
Pour la démonstration, lancer chaque processor avec « Run Once », dans l'ordre
de la chaîne, en vérifiant le compteur « Queued » de chaque connexion.

## Résultat attendu avec le CSV fourni
Sur 8 lignes : 3 insérées (cheicki, enock, lareine). Écartées : départ avant
arrivée, email vide, 0 personne (QueryRecord), hôtel inconnu (LookupRecord
`unmatched`), doublon (refusé par la contrainte `uq_reservation`).

Vérification :

    docker compose exec db psql -U hotel_app -d hotel_reservation_db -c "select count(*) from reservations;"

Attendu : 13 (10 du seed + 3).

## Limites connues
- Les lignes rejetées ne sont pas enregistrées dans un fichier : leurs
  relations sont terminées dans NiFi.
- Le flux se lance manuellement (Run Once) pour la démonstration.
