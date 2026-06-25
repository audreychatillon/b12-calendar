import sqlite3

DB_NAME = "b12.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS membres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS evenements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    date  TEXT NOT NULL,
    heure TEXT ,
    type  TEXT NOT NULL,
    lieu  TEXT 
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS presences (
    membre_id INTEGER,
    evenement_id INTEGER,
    statut TEXT NOT NULL,
    PRIMARY KEY (membre_id, evenement_id)
)
""")

conn.commit()
conn.close()

print("Base initialisée ✔")
