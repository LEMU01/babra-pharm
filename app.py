from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "siri_nzito_sana"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres.ltfzabxpwnxkuiwyomjv:Lemu1234%23567@aws-0-eu-west-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def conn():
    return db.engine.raw_connection()

# ---------------- DATABASE INIT ----------------
with app.app_context():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dawa(
        id SERIAL PRIMARY KEY,
        jina TEXT,
        idadi INTEGER,
        bei INTEGER,
        tarehe TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mauzo(
        id SERIAL PRIMARY KEY,
        dawa_id INTEGER,
        idadi INTEGER,
        jumla INTEGER,
        tarehe TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watumiaji(
        id SERIAL PRIMARY KEY,
        jina TEXT UNIQUE,
        nywila TEXT
    )
    """)

    cur.execute("SELECT * FROM watumiaji WHERE jina=%s", ('admin',))
    if not cur.fetchone():
        cur.execute("INSERT INTO watumiaji (jina, nywila) VALUES (%s,%s)", ('admin','admin123'))

    c.commit()
    cur.close()
    c.close()

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        jina = request.form['jina']
        nywila = request.form['nywila']

        c = conn()
        cur = c.cursor()
        cur.execute("SELECT * FROM watumiaji WHERE jina=%s AND nywila=%s", (jina, nywila))
        user = cur.fetchone()
        cur.close()
        c.close()

        if user:
            session['user'] = jina
            return redirect(url_for('dashboard'))
        flash("Login failed", "danger")

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    c = conn()
    cur = c.cursor()

    if search:
        cur.execute("SELECT * FROM dawa WHERE jina ILIKE %s", ('%'+search+'%',))
    else:
        cur.execute("SELECT * FROM dawa ORDER BY id DESC")

    dawa = cur.fetchall()

    cur.execute("""
    SELECT m.id, d.jina, m.idadi, m.jumla, m.tarehe
    FROM mauzo m
    JOIN dawa d ON d.id = m.dawa_id
    ORDER BY m.id DESC
    """)

    mauzo = cur.fetchall()

    cur.close()
    c.close()

    return render_template('dashboard.html', dawa=dawa, mauzo=mauzo, search=search)

# ---------------- ADD MEDICINE ----------------
@app.route('/ongeza_dawa', methods=['POST'])
def ongeza_dawa():
    jina = request.form['jina']
    idadi = request.form['idadi']
    bei = request.form['bei']
    tarehe = request.form['tarehe']

    c = conn()
    cur = c.cursor()

    cur.execute(
        "INSERT INTO dawa(jina,idadi,bei,tarehe) VALUES (%s,%s,%s,%s)",
        (jina, idadi, bei, tarehe)
    )

    c.commit()
    cur.close()
    c.close()

    flash("Medicine added", "success")
    return redirect(url_for('dashboard'))

# ---------------- SELL ----------------
@app.route('/uza_dawa', methods=['POST'])
def uza_dawa():
    dawa_id = request.form['dawa_id']
    qty = int(request.form['idadi'])

    c = conn()
    cur = c.cursor()

    cur.execute("SELECT idadi,bei FROM dawa WHERE id=%s", (dawa_id,))
    d = cur.fetchone()

    if d and d[0] >= qty:
        left = d[0] - qty
        total = d[1] * qty

        cur.execute("UPDATE dawa SET idadi=%s WHERE id=%s", (left, dawa_id))

        cur.execute("""
        INSERT INTO mauzo(dawa_id,idadi,jumla,tarehe)
        VALUES (%s,%s,%s,%s)
        """, (dawa_id, qty, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        c.commit()
        flash("Sale successful", "success")
    else:
        flash("Not enough stock", "danger")

    cur.close()
    c.close()
    return redirect(url_for('dashboard'))

# ---------------- EDIT ----------------
@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    c = conn()
    cur = c.cursor()

    if request.method == 'POST':
        jina = request.form['jina']
        idadi = request.form['idadi']
        bei = request.form['bei']
        tarehe = request.form['tarehe']

        cur.execute("""
        UPDATE dawa SET jina=%s,idadi=%s,bei=%s,tarehe=%s
        WHERE id=%s
        """, (jina, idadi, bei, tarehe, id))

        c.commit()
        cur.close()
        c.close()

        flash("Updated", "success")
        return redirect(url_for('dashboard'))

    cur.execute("SELECT * FROM dawa WHERE id=%s", (id,))
    dawa = cur.fetchone()

    cur.close()
    c.close()

    return render_template("edit.html", dawa=dawa)

# ---------------- DELETE ----------------
@app.route('/futa/<int:id>')
def futa(id):
    c = conn()
    cur = c.cursor()

    cur.execute("DELETE FROM dawa WHERE id=%s", (id,))

    c.commit()
    cur.close()
    c.close()

    flash("Deleted", "success")
    return redirect(url_for('dashboard'))

# ---------------- REPORT ----------------
@app.route('/report')
def report():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    SELECT d.jina, m.idadi, m.jumla, m.tarehe
    FROM mauzo m
    JOIN dawa d ON d.id=m.dawa_id
    ORDER BY m.id DESC
    """)

    mauzo = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(jumla),0) FROM mauzo")
    jumla = cur.fetchone()[0]

    cur.close()
    c.close()

    return render_template("report.html", mauzo=mauzo, jumla_kuu=jumla)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=false)