
-- ============================================
-- GROUPE 3 : DONNEES DE TEST
-- ============================================

-- 1. HOTELS
INSERT INTO hotels
    (nom, ville, adresse, etoiles, nb_chambres)
VALUES
    ('Hotel Splendid', 'Ouagadougou', 'Avenue Kwame Nkrumah', 4, 80),
    ('Hotel Sonia', 'Ouagadougou', 'Secteur 15', 3, 45),
    ('Hotel Sissiman', 'Bobo-Dioulasso', 'Quartier Sarfalao', 3, 60)
ON CONFLICT (nom, ville) DO NOTHING;

-- 2. CLIENTS
INSERT INTO clients
    (nom, prenom, email, telephone)
VALUES
    ('SANON', 'Cheick Hadou', 'cheicki@example.com', '70000001'),
    ('OUEDRAOGO', 'Judicël', 'judicael@example.com', '70000002'),
    ('SOME', 'Enock', 'enock@example.com', '70000003'),
    ('TEGA', 'Lareine', 'lareine@example.com', '70000004'),
    ('WEDRAOGO', 'Diane', 'diane@example.com', '70000005')
ON CONFLICT (email) DO NOTHING;

-- 3. RESERVATIONS
-- Les identifiants sont recherches via les emails
-- et les noms des hotels afin d'eviter de supposer
-- que les IDs generes commencent toujours a 1.

WITH donnees (
    email, hotel_nom, ville,
    date_arrivee, date_depart,
    nb_personnes, statut
) AS (
    VALUES
    ('cheicki@example.com', 'Hotel Splendid',
     'Ouagadougou', DATE '2026-11-01',
     DATE '2026-11-04', 2, 'CONFIRMEE'),

    ('judicael@example.com', 'Hotel Sonia',
     'Ouagadougou', DATE '2026-11-03',
     DATE '2026-11-06', 1, 'EN_ATTENTE'),

    ('enock@example.com', 'Hotel Sissiman',
     'Bobo-Dioulasso', DATE '2026-11-05',
     DATE '2026-11-08', 2, 'CONFIRMEE'),

    ('lareine@example.com', 'Hotel Splendid',
     'Ouagadougou', DATE '2026-11-08',
     DATE '2026-11-10', 1, 'ANNULEE'),

    ('diane@example.com', 'Hotel Sonia',
     'Ouagadougou', DATE '2026-11-10',
     DATE '2026-11-13', 3, 'CONFIRMEE'),

    ('cheicki@example.com', 'Hotel Sissiman',
     'Bobo-Dioulasso', DATE '2026-11-12',
     DATE '2026-11-15', 2, 'EN_ATTENTE'),

    ('judicael@example.com', 'Hotel Splendid',
     'Ouagadougou', DATE '2026-11-14',
     DATE '2026-11-17', 2, 'CONFIRMEE'),

    ('enock@example.com', 'Hotel Sonia',
     'Ouagadougou', DATE '2026-11-18',
     DATE '2026-11-21', 1, 'CONFIRMEE'),

    ('lareine@example.com', 'Hotel Sissiman',
     'Bobo-Dioulasso', DATE '2026-11-20',
     DATE '2026-11-23', 2, 'EN_ATTENTE'),

    ('diane@example.com', 'Hotel Splendid',
     'Ouagadougou', DATE '2026-11-25',
     DATE '2026-11-28', 2, 'CONFIRMEE')
)
INSERT INTO reservations (
    client_id, hotel_id,
    date_arrivee, date_depart,
    nb_personnes, statut
)
SELECT
    c.id,
    h.id,
    d.date_arrivee,
    d.date_depart,
    d.nb_personnes,
    d.statut
FROM donnees d
JOIN clients c ON c.email = d.email
JOIN hotels h
    ON h.nom = d.hotel_nom
    AND h.ville = d.ville
-- les identifiants suivent l'ordre chronologique des arrivees
ORDER BY d.date_arrivee
ON CONFLICT (
    client_id, hotel_id,
    date_arrivee, date_depart
) DO NOTHING;
