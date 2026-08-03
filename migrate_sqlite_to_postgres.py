import sqlite3
import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def migrate_table(sqlite_cursor, postgres_cursor, table, columns):
    sqlite_cursor.execute(
        f"SELECT {', '.join(columns)} FROM {table}"
    )

    rows = sqlite_cursor.fetchall()

    placeholders = ", ".join(["%s"] * len(columns))

    query = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({placeholders})
    """

    for row in rows:
        postgres_cursor.execute(query, row)

    print(f"{table}: {len(rows)} lignes migrées")


sqlite_conn = sqlite3.connect("b12.db")
sqlite_cursor = sqlite_conn.cursor()

postgres_conn = psycopg.connect(DATABASE_URL)
postgres_cursor = postgres_conn.cursor()


try:
    migrate_table(
        sqlite_cursor,
        postgres_cursor,
        "membres",
        ["id", "nom", "instruments", "status"]
    )

    migrate_table(
        sqlite_cursor,
        postgres_cursor,
        "evenements",
        ["id", "date", "heure", "titre", "type", "lieu"]
    )

    migrate_table(
        sqlite_cursor,
        postgres_cursor,
        "presences",
        ["membre_id", "evenement_id", "statut"]
    )

    postgres_conn.commit()

    print("Migration terminée avec succès !")

except Exception as e:
    postgres_conn.rollback()
    print("Erreur :", e)

finally:
    sqlite_conn.close()
    postgres_conn.close()
