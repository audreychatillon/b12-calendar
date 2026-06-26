from flask import Flask, render_template, request, redirect, send_file, abort, g
from datetime import date,timedelta, datetime
import locale
import sqlite3
import os

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "C")


def format_date_fr(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%A %d %B %Y")

app = Flask(__name__)
app.jinja_env.globals.update(format_date_fr=format_date_fr)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "b12.db")
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evenements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        heure TEXT,
        titre TEXT,
        type TEXT,
        lieu TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presences (
        membre_id INTEGER,
        evenement_id INTEGER,
        statut TEXT,
        PRIMARY KEY (membre_id, evenement_id)
    )
    """)

    conn.commit()
    conn.close()
init_db()

def get_status_by_event(event_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id, statut
        FROM presences
        WHERE evenement_id = ?
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    status_map = {}

    for membre_id, statut in rows:
        status_map[membre_id] = statut

    return status_map

def get_stats_by_event(event_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id, statut
        FROM presences
        WHERE evenement_id = ?
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    stats = {
        "present": 0,
        "absent": 0,
        "nsp": 0
    }

    for membre_id, statut in rows:
        if statut in stats:
            stats[statut] += 1

    # les membres sans ligne = NSP
    cursor = sqlite3.connect(DB).cursor()
    cursor.execute("SELECT COUNT(*) FROM membres")
    total = cursor.fetchone()[0]

    stats["nsp"] = total - (stats["present"] + stats["absent"])

    return stats


def get_status(event_id,statut):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id
        FROM presences
        WHERE evenement_id = ? AND statut = ?
    """, (event_id,statut))

    resultat = [row[0] for row in cursor.fetchall()]
    conn.close()
    return resultat

def get_events():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, date, heure, titre, type, lieu
        FROM evenements
        ORDER BY date
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route("/download-db")
def download_db():
    return send_file("b12.db", as_attachment=True)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"]
        heure = request.form["heure"]
        type_event = request.form["type"]
        titre = request.form["titre"]
        lieu = request.form["lieu"]

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evenements (date, heure, type, titre, lieu)
            VALUES (?, ?, ?, ?, ?)
        """, (date, heure, type_event, titre, lieu))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        heure = request.form["heure"]
        type_event = request.form["type"]
        titre = request.form["titre"]
        lieu = request.form["lieu"]

        cursor.execute("""
            UPDATE evenements
            SET date = ?, heure = ?, type = ?, titre = ?, lieu = ?
            WHERE id = ?
        """, (date, heure, type_event, titre, lieu, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT date, heure, type, titre, lieu FROM evenements WHERE id = ?", (id,))
    event = cursor.fetchone()
    conn.close()

    return render_template("edit.html", event=event, id=id)

@app.route("/presence", methods=["POST"])
def presence():

    event_id = request.form["event_id"]
    membre_id = request.form["membre_id"]
    statut = request.form["statut"]

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO presences (membre_id, evenement_id, statut)
        VALUES (?, ?, ?)
        ON CONFLICT(membre_id, evenement_id)
        DO UPDATE SET statut = excluded.statut
    """, (membre_id, event_id, statut))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/inscription/<int:event_id>")
def inscription(event_id):

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM evenements WHERE id = ?", (event_id,))
    event = cursor.fetchone()

    cursor.execute("""
        SELECT id, nom
        FROM membres
        ORDER BY nom COLLATE NOCASE
    """)
    membres = cursor.fetchall()

    conn.close()

    return render_template("inscription.html", event=event, membres=membres)

@app.route("/inscription", methods=["POST"])
def inscription_post():
    print("🔥 POST INSCRIPTION REÇU")
    print(request.form)
    event_id = request.form["event_id"]
    membre_id = request.form["membre_id"]
    statut = request.form["statut"]

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO presences (membre_id, evenement_id, statut)
        VALUES (?, ?, ?)
        ON CONFLICT(membre_id, evenement_id)
        DO UPDATE SET statut = excluded.statut
    """, (membre_id, event_id, statut))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/")
def index():

    filtre = request.args.get("filtre", "tout")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT id, date, heure, titre, type, lieu FROM evenements WHERE 1=1"
    params = []

    today = date.today()

    # filtre type
    if filtre == "repet":
        query += " AND type = ?"
        params.append("repet")

    elif filtre == "concert":
        query += " AND type = ?"
        params.append("concert")

    # filtre temps
    elif filtre == "1m":
        query += " AND date >= ?"
        params.append(str(today))
        query += " AND date <= ?"
        params.append(str(today + timedelta(days=30)))

    elif filtre == "3m":
        query += " AND date <= ?"
        params.append(str(today + timedelta(days=90)))

    elif filtre == "6m":
        query += " AND date <= ?"
        params.append(str(today + timedelta(days=1580)))

    query += " ORDER BY date, heure"

    cursor.execute(query, params)
    events = cursor.fetchall()

    # statut par événement
    status_by_event = {}
    stats_by_event = {}
    for event in events:
        event_id = event["id"]
        status_by_event[event_id] = get_status_by_event(event_id)
        stats_by_event[event["id"]] = get_stats_by_event(event["id"])

    # membres AVEC ID (important)
    cursor.execute("SELECT id, nom FROM membres")
    membres = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        events=events,
        membres=membres,
        status_by_event=status_by_event,
        stats_by_event=stats_by_event,
        filtre=filtre
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
