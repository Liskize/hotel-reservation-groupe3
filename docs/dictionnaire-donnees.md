# Dictionnaire de données

## API REST de réservations hôtelières

**Projet :** Développement à base de composants et services web  
**Groupe :** Groupe 3 SIE  
**SGBD :** PostgreSQL 18  
**Responsable :** Rôle 1 — Base de données et Docker

---

## 1. Présentation

La base `hotel_reservation_db` permet de gérer les
hôtels, les clients et leurs réservations.

Elle comporte trois tables :

- hotels
- clients
- reservations

## 2. Table hotels

Cette table contient les établissements hôteliers.

| Colonne     | Type PostgreSQL | Contraintes           | Description            |
| ----------- | --------------- | --------------------- | ---------------------- |
| id          | INTEGER         | PK, identité          | Identifiant de l'hôtel |
| nom         | VARCHAR(150)    | NOT NULL              | Nom de l'hôtel         |
| ville       | VARCHAR(100)    | NOT NULL              | Ville                  |
| adresse     | VARCHAR(255)    | NOT NULL              | Adresse                |
| etoiles     | INTEGER         | NOT NULL, CHECK 0 à 5 | Classement             |
| nb_chambres | INTEGER         | NOT NULL, CHECK > 0   | Capacité en chambres   |

**Contrainte d'unicité :** (nom, ville).

## 3. Table clients

Cette table contient les informations des clients.

| Colonne   | Type PostgreSQL | Contraintes      | Description           |
| --------- | --------------- | ---------------- | --------------------- |
| id        | INTEGER         | PK, identité     | Identifiant du client |
| nom       | VARCHAR(100)    | NOT NULL         | Nom du client         |
| prenom    | VARCHAR(100)    | NOT NULL         | Prénom                |
| email     | VARCHAR(255)    | NOT NULL, UNIQUE | Adresse email         |
| telephone | VARCHAR(30)     | NOT NULL         | Numéro de téléphone   |

## 4. Table reservations

Cette table enregistre les réservations des clients.

| Colonne      | Type PostgreSQL | Contraintes                         | Description            |
| ------------ | --------------- | ----------------------------------- | ---------------------- |
| id           | INTEGER         | PK, identité                        | Identifiant            |
| client_id    | INTEGER         | NOT NULL, FK                        | Client concerné        |
| hotel_id     | INTEGER         | NOT NULL, FK                        | Hôtel concerné         |
| date_arrivee | DATE            | NOT NULL                            | Date d'arrivée         |
| date_depart  | DATE            | NOT NULL                            | Date de départ         |
| nb_personnes | INTEGER         | NOT NULL, CHECK > 0                 | Nombre de personnes    |
| statut       | VARCHAR(30)     | NOT NULL                            | État de la réservation |
| created_at   | TIMESTAMP       | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de création       |

Valeurs autorisées pour `statut` :

- EN_ATTENTE
- CONFIRMEE
- ANNULEE

Valeur par défaut : EN_ATTENTE.

Contraintes :

- date_depart > date_arrivee
- nb_personnes > 0
- UNIQUE(client_id, hotel_id, date_arrivee, date_depart)

## 5. Relations

### Client - Réservation

Un client peut effectuer plusieurs réservations.

Relation : clients (1) — (N) reservations

Clé étrangère :
reservations.client_id → clients.id

### Hôtel - Réservation

Un hôtel peut recevoir plusieurs réservations.

Relation : hotels (1) — (N) reservations

Clé étrangère :
reservations.hotel_id → hotels.id

Les deux relations utilisent ON DELETE RESTRICT.

## 6. Index

| Index                   | Colonne   | Utilité             |
| ----------------------- | --------- | ------------------- |
| idx_reservations_hotel  | hotel_id  | Filtrage par hôtel  |
| idx_reservations_client | client_id | Filtrage par client |
| idx_reservations_statut | statut    | Filtrage par statut |

## 7. Gestion des erreurs

L'API doit respecter le contrat commun du groupe.

Exemples :

- 200 : opération réussie
- 201 : ressource créée
- 204 : suppression réussie
- 400 : requête incorrecte
- 404 : ressource introuvable
- 409 : conflit ou doublon
- 422 : données invalides

Structure commune :

```json
{
  "error": "validation_error",
  "message": "date_depart doit être après date_arrivee",
  "details": {}
}
```

## 8. Données de démonstration

Le fichier database/seed.sql doit insérer au minimum :

- 3 hôtels
- 5 clients
- 10 réservations

Le fichier database/init.sql définit le schéma.

Les deux scripts sont exécutés automatiquement
lors de l'initialisation d'une base PostgreSQL
Docker neuve.

## 9. Recommandations pour les développeurs Flask

- Utiliser les noms des colonnes définis dans ce document.
- Respecter les contraintes d'unicité.
- Valider les dates avant insertion.
- Retourner HTTP 409 pour les doublons.
- Retourner HTTP 404 pour les identifiants inexistants.
- Utiliser les noms exacts des statuts.
- Ne pas créer de schéma SQL incompatible avec init.sql.

```

```
