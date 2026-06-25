import sqlite3

DB = "b12.db"


def get_conn():
    return sqlite3.connect(DB)


def list_members():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nom FROM membres")
    rows = cursor.fetchall()

    print("\n📋 Membres :")
    for r in rows:
        print(f"{r[0]} - {r[1]}")

    conn.close()


def add_member():
    name = input("Nom du membre : ")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO membres (nom) VALUES (?)", (name,))
    conn.commit()
    conn.close()

    print("✔ Ajouté")


def delete_member():
    member_id = input("ID à supprimer : ")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM membres WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()

    print("✔ Supprimé")

def modify_name():
    list_members()

    member_id = input("ID à modifier : ")
    nom = input("Nouveau nom : ")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE membres SET nom = ? WHERE id = ?",
        (nom, member_id)
    )

    conn.commit()
    conn.close()

    print("✔ Membre modifié")


def menu():
    while True:
        print("\n🎸 Gestion groupe")
        print("1 - Lister membres")
        print("2 - Ajouter membre")
        print("3 - Supprimer membre")
        print("4 - Modifier nom")
        print("0 - Quitter")

        choice = input("Choix : ")

        if choice == "1":
            list_members()
        elif choice == "2":
            add_member()
        elif choice == "3":
            delete_member()
        elif choice == "4":
            modify_name()
        elif choice == "0":
            break
        else:
            print("Choix invalide")


if __name__ == "__main__":
    menu()
