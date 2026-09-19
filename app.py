from flask import Flask, render_template, request,redirect,session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "wandji-finance-secret"

def get_db():
    conn = sqlite3.connect("wandji_finance.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS revenus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            montant REAL NOT NULL,
            source TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def accueil():

    if "utilisateur_id" not in session:
        return redirect("/connexion")

    conn = get_db()

    depenses = conn.execute("""
    SELECT * FROM depenses
    WHERE utilisateur_id = ?
    ORDER BY date DESC
    """, (session["utilisateur_id"],)).fetchall()

    revenus = conn.execute("""
    SELECT * FROM revenus
    WHERE utilisateur_id = ?
    ORDER BY date DESC
    """, (session["utilisateur_id"],)).fetchall()

    total_depenses = conn.execute("""
    SELECT COALESCE(SUM(montant), 0) AS total
    FROM depenses
    WHERE utilisateur_id = ?
    """, (session["utilisateur_id"],)).fetchone()["total"]

    total_revenus = conn.execute("""
    SELECT COALESCE(SUM(montant), 0) AS total
    FROM revenus
    WHERE utilisateur_id = ?
    """, (session["utilisateur_id"],)).fetchone()["total"]

    solde = total_revenus - total_depenses

    transactions = []

    for depense in depenses:
        transactions.append({
            "type": "depense",
            "description": depense["description"],
            "categorie": depense["categorie"],
            "montant": depense["montant"],
            "date": depense["date"]
        })

    for revenu in revenus:
        transactions.append({
            "type": "revenu",
            "description": revenu["description"],
            "categorie": revenu["source"],
            "montant": revenu["montant"],
            "date": revenu["date"]
        })

    transactions.sort(key=lambda x: x["date"], reverse=True)

    conn.close()

    return render_template(
        "index.html",
        depenses=depenses,
        revenus=revenus,
        total_depenses=total_depenses,
        total_revenus=total_revenus,
        solde=solde,
        transactions=transactions
    )


@app.route("/ajouter-depense", methods=["GET", "POST"])
def ajouter_depense():

    if "utilisateur_id" not in session:
        return redirect("/connexion")

    if request.method == "POST":
        montant = request.form["montant"]
        categorie = request.form["categorie"]
        description = request.form["description"]
        date = request.form["date"]

        conn = get_db()

        conn.execute("""
            INSERT INTO depenses
            (montant, categorie, description, date, utilisateur_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            montant,
            categorie,
            description,
            date,
            session["utilisateur_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("ajouter_depenses.html")

@app.route("/ajouter-revenu", methods=["GET", "POST"])
def ajouter_revenu():

    if "utilisateur_id" not in session:
        return redirect("/connexion")
    
    if request.method == "POST":

        montant = request.form["montant"]
        source = request.form["source"]
        description = request.form["description"]
        date = request.form["date"]

        conn = get_db()

        conn.execute("""
        INSERT INTO revenus
        (montant, source, description, date, utilisateur_id)
        VALUES (?, ?, ?, ?, ?)
        """, (
        montant,
        source,
        description,
        date,
        session["utilisateur_id"]
        ))


        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("ajouter_revenus.html")

@app.route("/historique")
def historique():

    if "utilisateur_id" not in session:
        return redirect("/connexion")
    
    conn = get_db()

    depenses = conn.execute("""
        SELECT
            id,
            'depense' AS type,
            categorie AS categorie,
            description,
            montant,
            date
        FROM depenses
        WHERE utilisateur_id = ?
        """, (session["utilisateur_id"],)).fetchall()

    revenus = conn.execute("""
        SELECT
            id,
            'revenu' AS type,
            source AS categorie,
            description,
            montant,
            date
        FROM revenus
        WHERE utilisateur_id = ?
        """, (session["utilisateur_id"],)).fetchall()

    conn.close()

    transactions = list(depenses) + list(revenus)

    transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    return render_template(
        "historiques.html",
        transactions=transactions
    )

@app.route("/supprimer-depense/<int:id>")
def supprimer_depense(id):
    conn = get_db()

    conn.execute("""
        DELETE FROM depenses
        WHERE id = ?
        AND utilisateur_id = ?
    """, (id, session["utilisateur_id"]))

    conn.commit()
    conn.close()

    return redirect("/historique")

@app.route("/supprimer-revenu/<int:id>")
def supprimer_revenu(id):
    conn = get_db()

    conn.execute("""
        DELETE FROM revenus
        WHERE id = ?
        AND utilisateur_id = ?
    """, (id, session["utilisateur_id"]))

    conn.commit()
    conn.close()

    return redirect("/historique")

@app.route("/modifier-depense/<int:id>", methods=["GET", "POST"])
def modifier_depense(id):

    conn = get_db()

    depense = conn.execute(
    """
    SELECT * FROM depenses
    WHERE id = ?
    AND utilisateur_id = ?
    """,
    (id, session["utilisateur_id"])
    ).fetchone()

    if depense is None:
        conn.close()
        return "Dépense introuvable", 404

    if request.method == "POST":

        montant = request.form["montant"]
        categorie = request.form["categorie"]
        description = request.form["description"]
        date = request.form["date"]

        conn.execute("""
            UPDATE depenses
            SET montant = ?,
                categorie = ?,
                description = ?,
                date = ?
            WHERE id = ?
        """, (
            montant,
            categorie,
            description,
            date,
            session["utilisateur_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/historique")

    conn.close()

    return render_template(
        "modifier_depense.html",
        depense=depense
    )

@app.route("/modifier-revenu/<int:id>", methods=["GET", "POST"])
def modifier_revenu(id):

    conn = get_db()

    revenu = conn.execute(
    """
    SELECT * FROM revenus
    WHERE id = ?
    AND utilisateur_id = ?
    """,
    (id, session["utilisateur_id"])
    ).fetchone()

    if revenu is None:
        conn.close()
        return "Revenu introuvable", 404

    if request.method == "POST":

        montant = request.form["montant"]
        source = request.form["source"]
        description = request.form["description"]
        date = request.form["date"]

        conn.execute("""
            UPDATE revenus
            SET montant = ?,
                source = ?,
                description = ?,
                date = ?
            WHERE id = ?
        """, (
            montant,
            source,
            description,
            date,
            session["utilisateur_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/historique")

    conn.close()

    return render_template(
        "modifier_revenu.html",
        revenu=revenu
    )

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom = request.form["nom"]
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO utilisateurs (nom, email, mot_de_passe)
                VALUES (?, ?, ?)
            """, (nom, email, mot_de_passe_hash))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Cette adresse email existe déjà."

        conn.close()

        return redirect("/")

    return render_template("inscriptions.html")

@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        conn = get_db()

        utilisateur = conn.execute("""
            SELECT * FROM utilisateurs
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if utilisateur is None:
            return "Email ou mot de passe incorrect."

        if not check_password_hash(
            utilisateur["mot_de_passe"],
            mot_de_passe
        ):
            return "Email ou mot de passe incorrect."

        session["utilisateur_id"] = utilisateur["id"]
        session["nom_utilisateur"] = utilisateur["nom"]

        return redirect("/")

    return render_template("connexion.html")

@app.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect("/connexion")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)