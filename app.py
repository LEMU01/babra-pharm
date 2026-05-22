from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "siri_nzito_sana"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres.ltfzabxpwnxkuiwyomjv:Lemu1234%23567@aws-0-eu-west-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def unganisha_db():
    return db.engine.raw_connection()

with app.app_context():
    conn = unganisha_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dwa (
        id SERIAL PRIMARY KEY,
        jina TEXT,
        idadi INTEGER,
        bei INTEGER,
        tarehe TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mauzo (
        id SERIAL PRIMARY KEY,
        dawa_id INTEGER,
        idadi INTEGER,
        jumla INTEGER,
        tarehe TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watumiaji (
        id SERIAL PRIMARY KEY,
        jina TEXT UNIQUE,
        nywila TEXT
    )
    ''')

    cursor.execute("SELECT * FROM watumiaji WHERE jina=%s", ('admin',))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO watumiaji (jina, nywila) VALUES (%s,%s)",
            ('admin', 'admin123')
        )

    conn.commit()
    cursor.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        jina = request.form['jina']
        nywila = request.form['nywila']

        conn = unganisha_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM watumiaji WHERE jina=%s AND nywila=%s",
            (jina, nywila)
        )

        mtumiaji = cursor.fetchone()

        cursor.close()
        conn.close()

        if mtumiaji:
            session['mtumiaji'] = jina
            return redirect(url_for('dashboard'))

        flash("Username au password sio sahihi", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    if 'mtumiaji' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    conn = unganisha_db()
    cursor = conn.cursor()

    if search:
        cursor.execute(
            "SELECT * FROM dwa WHERE LOWER(jina) LIKE LOWER(%s)",
            ('%' + search + '%',)
        )
    else:
        cursor.execute("SELECT * FROM dwa ORDER BY id DESC")

    dawa_zote = cursor.fetchall()

    cursor.execute("""
    SELECT m.id, d.jina, m.idadi, m.jumla, m.tarehe
    FROM mauzo m
    JOIN dwa d ON m.dawa_id = d.id
    ORDER BY m.id DESC
    """)

    mauzo_yote = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        dwa=dawa_zote,
        mauzo=mauzo_yote,
        search_query=search
    )

@app.route('/ongeza_dawa', methods=['POST'])
def ongeza_dawa():

    if 'mtumiaji' not in session:
        return redirect(url_for('login'))

    jina = request.form['jina']
    idadi = request.form['idadi']
    bei = request.form['bei']
    tarehe = request.form['tarehe']

    conn = unganisha_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO dwa (jina, idadi, bei, tarehe) VALUES (%s,%s,%s,%s)",
        (jina, idadi, bei, tarehe)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Medicine added successfully", "success")

    return redirect(url_for('dashboard'))

@app.route('/uza_dawa', methods=['POST'])
def uza_dawa():

    dawa_id = request.form['dawa_id']
    idadi = int(request.form['idadi'])

    conn = unganisha_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT idadi, bei FROM dwa WHERE id=%s",
        (dawa_id,)
    )

    dawa = cursor.fetchone()

    if dawa and dawa[0] >= idadi:

        mpya = dawa[0] - idadi
        jumla = dawa[1] * idadi

        cursor.execute(
            "UPDATE dwa SET idadi=%s WHERE id=%s",
            (mpya, dawa_id)
        )

        cursor.execute(
            "INSERT INTO mauzo (dawa_id,idadi,jumla,tarehe) VALUES (%s,%s,%s,%s)",
            (
                dawa_id,
                idadi,
                jumla,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )

        conn.commit()

        flash("Sale completed", "success")

    else:
        flash("Stock haitoshi", "danger")

    cursor.close()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    conn = unganisha_db()
    cursor = conn.cursor()

    if request.method == 'POST':

        jina = request.form['jina']
        idadi = request.form['idadi']
        bei = request.form['bei']
        tarehe = request.form['tarehe']

        cursor.execute("""
        UPDATE dwa
        SET jina=%s, idadi=%s, bei=%s, tarehe=%s
        WHERE id=%s
        """, (jina, idadi, bei, tarehe, id))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Medicine updated", "success")

        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM dwa WHERE id=%s", (id,))
    dawa = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('edit.html', dawa=dawa)

@app.route('/futa/<int:id>')
def futa(id):

    conn = unganisha_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM dwa WHERE id=%s", (id,))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Medicine deleted", "success")

    return redirect(url_for('dashboard'))

@app.route('/report')
def report():

    conn = unganisha_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT d.jina, m.idadi, m.jumla, m.tarehe
    FROM mauzo m
    JOIN dwa d ON m.dawa_id=d.id
    ORDER BY m.id DESC
    """)

    mauzo = cursor.fetchall()

    cursor.execute("SELECT COALESCE(SUM(jumla),0) FROM mauzo")
    jumla_kuu = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'report.html',
        mauzo=mauzo,
        jumla_kuu=jumla_kuu
    )

@app.route('/logout')
def logout():

    session.pop('mtumiaji', None)

    return redirect(url_for('login'))

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port, debug=False)