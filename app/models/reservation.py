from app.db import get_db

TABLES = {"clients", "hotels"}


def _serialize(row):
    """Dates en texte ISO (YYYY-MM-DD), sinon Flask les rend au format HTTP."""
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()}


def exists(table, row_id):
    if table not in TABLES:
        raise ValueError("table inconnue")
    cur = get_db().cursor()
    cur.execute(f"SELECT 1 FROM {table} WHERE id = %s", (row_id,))
    return cur.fetchone() is not None


def get_by_id(res_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM reservations WHERE id = %s", (res_id,))
    row = cur.fetchone()
    return _serialize(row) if row else None


def find_duplicate(data, exclude_id=None):
    sql = """SELECT 1 FROM reservations
             WHERE client_id = %s AND hotel_id = %s
               AND date_arrivee = %s AND date_depart = %s"""
    params = [data["client_id"], data["hotel_id"], data["date_arrivee"], data["date_depart"]]
    if exclude_id is not None:
        sql += " AND id <> %s"
        params.append(exclude_id)
    cur = get_db().cursor()
    cur.execute(sql, params)
    return cur.fetchone() is not None


def list_reservations(page, per_page, hotel_id=None, client_id=None,
                      statut=None, date_debut=None, date_fin=None):
    where, params = [], []
    if hotel_id is not None:
        where.append("hotel_id = %s")
        params.append(hotel_id)
    if client_id is not None:
        where.append("client_id = %s")
        params.append(client_id)
    if statut:
        where.append("statut = %s")
        params.append(statut)
    if date_debut:
        where.append("date_arrivee >= %s")
        params.append(date_debut)
    if date_fin:
        where.append("date_depart <= %s")
        params.append(date_fin)
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    cur = get_db().cursor()
    cur.execute(f"SELECT COUNT(*) AS total FROM reservations {clause}", params)
    total = cur.fetchone()["total"]
    cur.execute(
        f"SELECT * FROM reservations {clause} ORDER BY id LIMIT %s OFFSET %s",
        params + [per_page, (page - 1) * per_page],
    )
    return [_serialize(r) for r in cur.fetchall()], total


def create(data):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """INSERT INTO reservations
               (client_id, hotel_id, date_arrivee, date_depart, nb_personnes, statut)
           VALUES (%(client_id)s, %(hotel_id)s, %(date_arrivee)s, %(date_depart)s,
                   %(nb_personnes)s, %(statut)s)
           RETURNING *""",
        data,
    )
    row = cur.fetchone()
    db.commit()
    return _serialize(row)


def update(res_id, data):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """UPDATE reservations
           SET client_id = %(client_id)s, hotel_id = %(hotel_id)s,
               date_arrivee = %(date_arrivee)s, date_depart = %(date_depart)s,
               nb_personnes = %(nb_personnes)s, statut = %(statut)s
           WHERE id = %(id)s
           RETURNING *""",
        {**data, "id": res_id},
    )
    row = cur.fetchone()
    db.commit()
    return _serialize(row)


def delete(res_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM reservations WHERE id = %s", (res_id,))
    db.commit()