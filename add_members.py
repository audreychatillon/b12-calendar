import sqlite3

conn = sqlite3.connect("b12.db")
cursor = conn.cursor()

membres = ["Gilles", "Emmanuel", "Arnaud", "Thierry", "Bertrand", "Adrien", "Hugues", "Alexandre", "Flute", "Sylvie", "Hervé", "Audrey", "Marc", "Arthur"]

for nom in membres:
    cursor.execute("INSERT INTO membres (nom) VALUES (?)", (nom,))

conn.commit()
conn.close()

print("Membres ajoutés")
