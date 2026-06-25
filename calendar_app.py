import sqlite3

DB = "b12.db"


def list_events():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, heure, titre, type, lieu
        FROM evenements
        ORDER BY date
    """)
    events = cursor.fetchall()
    print("\n📅 Planning B12\n :")

    if not events:
        print("Aucun événement")
        return

    for event in events:
        id_event, date, heure, titre, type_event, lieu = event

        if type_event == "repet":
            print(f"[id={id_event}]    {date} | {heure} |  repet  | {titre}")
        else:
            print(f"[id={id_event}]    {date} | {heure} | concert | {titre} - {lieu}")

        cursor.execute("""
            SELECT m.nom, p.statut
            FROM presences p
            JOIN membres m ON m.id = p.membre_id
            WHERE p.evenement_id = ?
        """, (id_event,))

        presences = cursor.fetchall()

        if presences:
            for nom, statut in presences:
                print(f"    {nom} → {statut}")
        else:
            print("    (aucune réponse)")

    conn.close()


def add_repetition():
    titre = input("Titre : ")
    date  = input("Date  (AAAA-MM-JJ) : ")
    heure = input("Heure (HH-MM) : ")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO evenements (titre, date, heure, type)
        VALUES (?, ?, ?, ?)
    """, (titre, date, heure, "repet"))

    conn.commit()
    conn.close()

    print("✔ Répétition enregistrée")

def add_concert():
    titre = input("Titre : ")
    date  = input("Date (AAAA-MM-JJ) : ")
    heure = input("Heure : ")
    lieu  = input("Lieu du concert : ")

    conn = sqlite3.connect("b12.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO evenements (titre, date, heure, type, lieu)
        VALUES (?, ?, ?, ?, ?)
    """, (titre, date, heure, "concert", lieu))

    conn.commit()
    conn.close()

    print("✔ Concert ajouté")


def edit_event():
    list_events()

    event_id = input("\nID de l'événement à modifier : ")

    print("\nLaisse vide pour ne pas modifier un champ\n")

    titre = input("Titre : ")
    date = input("Date (AAAA-MM-JJ) : ")
    heure = input("Heure : ")
    type_event = input("Type (concert/repet) : ")
    lieu = input("Lieu : ")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # on construit UPDATE dynamique
    fields = []
    values = []

    if titre:
        fields.append("titre = ?")
        values.append(titre)
    if date:
        fields.append("date = ?")
        values.append(date)
    if heure:
        fields.append("heure = ?")
        values.append(heure)
    if type_event:
        fields.append("type = ?")
        values.append(type_event)
    if lieu:
        fields.append("lieu = ?")
        values.append(lieu)

    values.append(event_id)

    sql = f"""
        UPDATE evenements
        SET {", ".join(fields)}
        WHERE id = ?
    """

    cursor.execute(sql, values)

    conn.commit()
    conn.close()

    print("✔ Événement modifié")


def add_presence():
    list_events()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # afficher événements
    cursor.execute("SELECT id, date, titre FROM evenements ORDER BY date")
    events = cursor.fetchall()

    print("\n📅 Événements :")
    for e in events:
        print(f"{e[0]} - {e[1]} - {e[2]}")

    event_id = input("\nID événement : ")

    # afficher membres
    cursor.execute("SELECT id, nom FROM membres")
    members = cursor.fetchall()

    print("\n👥 Membres :")
    for m in members:
        print(f"{m[0]} - {m[1]}")

    member_id = input("\nID membre : ")

    statut = input("Statut (present / absent / incertain) : ")

    cursor.execute("""
        INSERT OR REPLACE INTO presences (membre_id, evenement_id, statut)
        VALUES (?, ?, ?)
    """, (member_id, event_id, statut))

    conn.commit()
    conn.close()

    print("✔ Présence enregistrée")


def show_presence():
    event_id = input("ID événement : ")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.nom, p.statut
        FROM presences p
        JOIN membres m ON m.id = p.membre_id
        WHERE p.evenement_id = ?
    """, (event_id,))

    events = cursor.fetchall()

    print("\n📋 Présences :")

    if not events:
        print("Aucune réponse")
    else:
        for nom, statut in events:
            print(f"{nom} → {statut}")

    conn.close()


def menu():
    while True:
        print("\n===== B12 =====")
        print("1 - Voir les événements")
        print("2 - Ajouter une répétition")
        print("3 - Ajouter un concert")
        print("4 - Modifier un événement (repet ou concert)")
        print("5 - Ajouter présence")
        print("6 - Voir présences d’un événement")
        print("0 - Quitter")

        choix = input("\nChoix : ")

        if choix == "1":
            list_events()
        elif choix == "2":
            add_repetition()
        elif choix == "3":
            add_concert()
        elif choix == "4":
            edit_event()
        elif choix == "5":
            add_presence()
        elif choix == "6":
            show_presence()
        elif choix == "0":
            print("Au revoir")
            break
        else:
            print("Choix invalide")


if __name__ == "__main__":
    menu()
