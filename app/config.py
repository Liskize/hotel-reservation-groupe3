def _database_url():
    """DATABASE_URL si fournie, sinon construite depuis les variables POSTGRES_*."""
    url = os.getenv("DATABASE_URL")
    if url:
        # psycopg2 n'accepte pas le préfixe SQLAlchemy "postgresql+psycopg2://"
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return "postgresql://{u}:{p}@{h}:{port}/{db}".format(
        u=os.getenv("POSTGRES_USER", "postgres"),
        p=os.getenv("POSTGRES_PASSWORD", "postgres"),
        h=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        db=os.getenv("POSTGRES_DB", "hotel_reservation_db"),
    )
