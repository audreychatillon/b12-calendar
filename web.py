from flask import Flask, render_template, request, redirect, send_file, abort, g
from datetime import date,timedelta, datetime
from calendar import monthrange
import locale
import os
from db import get_connection

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "C")

def format_date_short(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A %d")

def format_date_long(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A %d %B %Y")

months_fr = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

app = Flask(__name__)
app.jinja_env.globals.update(
    format_date_short=format_date_short,
    format_date_long=format_date_long
)

def get_status_by_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id, statut
        FROM presences
        WHERE evenement_id = %s
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    status_map = {}

    for row in rows:
        status_map[row["membre_id"]] = row["statut"]

    return status_map

def get_stats_by_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id, statut
        FROM presences
        WHERE evenement_id = %s
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    stats = {
        "present": 0,
        "absent": 0,
        "pending": 0
    }

    for row in rows:
        statut = row["statut"]
        print("DEBUG STATUT", statut)
        if statut in stats:
            stats[statut] += 1

    return stats


def get_status(event_id,statut):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT membre_id
        FROM presences
        WHERE evenement_id = %s AND statut = %s
    """, (event_id,statut))

    resultat = [row["membre_id"] for row in cursor.fetchall()]
    conn.close()
    return resultat

def get_events():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, date, heure, titre, type, lieu
        FROM evenements
        ORDER BY date
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_setlist_filename(event_date):
    filename = f"setlist_{event_date.replace('-', '')}.pdf"
    path = os.path.join(
        "static",
        "img",
        "setlists",
        filename
    )
    if os.path.exists(path):
        return filename
    return None

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"]
        heure = request.form["heure"]
        type_event = request.form["type"]
        titre = request.form["titre"]
        lieu = request.form["lieu"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evenements (date, heure, type, titre, lieu)
            VALUES (%s, %s, %s, %s, %s)
        """, (date, heure, type_event, titre, lieu))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        heure = request.form["heure"]
        type_event = request.form["type"]
        titre = request.form["titre"]
        lieu = request.form["lieu"]

        cursor.execute("""
            UPDATE evenements
            SET date = %s, heure = %s, type = %s, titre = %s, lieu = %s
            WHERE id = %s
        """, (date, heure, type_event, titre, lieu, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT date, heure, type, titre, lieu FROM evenements WHERE id = %s", (id,))
    event = cursor.fetchone()
    conn.close()

    return render_template("edit.html", event=event, id=id)

@app.route("/presence", methods=["POST"])
def presence():

    event_id = request.form["event_id"]
    membre_id = request.form["membre_id"]
    statut = request.form["statut"]

    if statut not in ["present", "absent", "pending"]:
        return "Statut invalide", 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO presences (membre_id, evenement_id, statut)
        VALUES (%s, %s, %s)
        ON CONFLICT(membre_id, evenement_id)
        DO UPDATE SET statut = excluded.statut
    """, (membre_id, event_id, statut))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/inscription")
def inscription():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nom, status FROM membres ORDER BY LOWER(nom)")
    membres = cursor.fetchall()

    conn.close()

    return render_template("choix_membre.html", membres=membres)

@app.route("/inscription/membre")
def inscription_membre():

    membre_id = request.args.get("membre_id")

    if not membre_id:
        return redirect("/inscription")

    return redirect(f"/inscription/membre/{membre_id}")

@app.route("/inscription/membre/<int:membre_id>")
def inscription_membre_detail(membre_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM membres WHERE id = %s", (membre_id,))
    membre = cursor.fetchone()

    today = date.today()

    cursor.execute("""
        SELECT id, date, heure, titre, type, lieu
        FROM evenements
        WHERE date >= %s
        ORDER BY date, heure
    """, (str(today),))

    events = cursor.fetchall()

    # récupérer les réponses existantes
    cursor.execute("""
        SELECT evenement_id, statut
        FROM presences
        WHERE membre_id = %s
    """, (membre_id,))

    presences = {row["evenement_id"]: row["statut"] for row in cursor.fetchall()}

    conn.close()

    return render_template(
        "inscription.html",
        membre=membre,
        events=events,
        presences=presences
    )

@app.route("/inscription", methods=["POST"])
def inscription_post():

    event_id = request.form["event_id"]
    membre_id = request.form["membre_id"]
    statut = request.form["statut"]

    if statut not in ["present", "absent", "pending"]:
        return "Statut invalide", 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO presences (membre_id, evenement_id, statut)
        VALUES (%s, %s, %s)
        ON CONFLICT(membre_id, evenement_id)
        DO UPDATE SET statut = excluded.statut
    """, (membre_id, event_id, statut))

    conn.commit()
    conn.close()

    return redirect(f"/inscription/membre/{membre_id}")

@app.route("/partitions")
def partitions():
    return render_template("partitions.html")



@app.route("/membres")
def membres():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM membres ORDER BY LOWER(nom)")
    membres = cursor.fetchall()

    conn.close()

    return render_template("membres.html", membres=membres)

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/admin/membres")
def admin_membres():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM membres
        ORDER BY LOWER(nom)
    """)

    membres = cursor.fetchall()

    conn.close()

    return render_template("admin_membres.html", membres=membres)

@app.route("/admin/membres/add", methods=["POST"])
def add_member():

    nom = request.form.get("nom","").strip()
    instruments = request.form.get("instruments","").strip()
    status = request.form.get("status","active").strip()

    if not nom:
        return redirect("/admin/membres")

    if status not in ["active", "guest", "former"]:
        status = "active"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO membres (nom, instruments, status)
        VALUES (%s, %s, %s)
    """, (nom, instruments, status))

    conn.commit()
    conn.close()

    return redirect("/admin/membres")

@app.route("/admin/membres/update/<int:id>", methods=["POST"])
def update_member(id):

    nom = request.form["nom"].strip()
    instruments = request.form["instruments"].strip()
    status = request.form["status"].strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE membres
        SET nom = %s, instruments = %s, status = %s
        WHERE id = %s
    """, (nom, instruments, status, id))

    conn.commit()
    conn.close()

    return redirect("/admin/membres")

@app.route("/admin/membres/delete/<int:id>", methods=["POST"])
def delete_member(id):

    conn = get_connection()
    cursor = conn.cursor()

    # On supprime d'abord les présences liées
    cursor.execute("DELETE FROM presences WHERE membre_id = %s", (id,))

    # Puis le membre
    cursor.execute("DELETE FROM membres WHERE id = %s", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/membres")

@app.route("/")
def index():
    filtre = request.args.get("filtre", "tout")
    mois = request.args.get("mois")
    today = date.today()
    if mois and "-" in mois:
        year, month = map(int, mois.split("-"))
    else:
        year, month = today.year, today.month
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT id, date, heure, titre, type, lieu
    FROM evenements
    WHERE date >= %s AND date <= %s
    """
    
    params = [str(start), str(end)]

    # filtre type
    if filtre == "repet":
        query += " AND type = %s"
        params.append("repet")

    elif filtre == "concert":
        query += " AND type = %s"
        params.append("concert")

    query += " ORDER BY date, heure"

    cursor.execute(query, params)
    events = cursor.fetchall()

    # statut par événement
    status_by_event = {}
    stats_by_event = {}
    # setlist par concert
    setlist_by_event = {}
    for event in events:
        event_id = event["id"]
        status_by_event[event_id] = get_status_by_event(event_id)
        stats_by_event[event["id"]] = get_stats_by_event(event["id"])
        setlist_by_event[event_id] = get_setlist_filename(event["date"])
    cursor.execute("SELECT id, nom, status FROM membres")
    membres = cursor.fetchall()

    next_event = None
    next_month_link = None 
    next_month_label = None
    cursor.execute("""
        SELECT date
        FROM evenements
        WHERE date > %s
        ORDER BY date ASC
        LIMIT 1
    """, (str(end),))
    
    next_event = cursor.fetchone()
    if next_event:
        d = datetime.strptime(next_event["date"], "%Y-%m-%d")
        next_month_label = f"{months_fr[d.month]} {d.year}"
        next_month_link = f"{d.year}-{d.month}"
    conn.close()
    
    return render_template(
        "index.html",
        events=events,
        membres=membres,
        status_by_event=status_by_event,
        stats_by_event=stats_by_event,
        setlist_by_event=setlist_by_event,
        filtre=filtre,
        year=year,
        month=month,
        months_fr=months_fr,
        mois=f"{year:04d}-{month:02d}",
        next_month_link=next_month_link,
        next_month_label=next_month_label
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
