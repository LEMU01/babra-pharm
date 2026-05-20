from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "siri_nzito_sana" 

# 1. Kuunganisha Database (Marekebisho: INTEGER badala ya REAL)
def unganisha_db():
    conn = sqlite3.connect('pharmacy.db')
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    # Tumetumia INTEGER kwenye bei ili kuzuia desimali (.0)
    cursor.execute('''CREATE TABLE IF NOT EXISTS dawa (id INTEGER PRIMARY KEY AUTOINCREMENT, jina TEXT NOT NULL, idadi INTEGER NOT NULL, bei INTEGER NOT NULL, tarehe_kuisha TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS mauzo (id INTEGER PRIMARY KEY AUTOINCREMENT, jina_dawa TEXT NOT NULL, idadi_iliyouzwa INTEGER NOT NULL, jumla_pesa INTEGER NOT NULL, tarehe TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS watumiaji (id INTEGER PRIMARY KEY AUTOINCREMENT, jina TEXT UNIQUE NOT NULL, nywila TEXT NOT NULL)''')
    cursor.execute("INSERT OR IGNORE INTO watumiaji (jina, nywila) VALUES ('admin', 'admin123')")
    conn.commit()
    return conn

# 2. Ukurasa wa Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        jina = request.form['jina']
        nywila = request.form['nywila']
        conn = unganisha_db()
        mtumiaji = conn.execute("SELECT * FROM watumiaji WHERE jina=? AND nywila=?", (jina, nywila)).fetchone()
        if mtumiaji:
            session['loggedin'] = True
            session['jina'] = jina
            return redirect(url_for('dashboard'))
        else:
            flash("Jina au Nywila si sahihi!", "danger")
    return render_template('login.html')


    return redirect(url_for('dashboard'))
# 3. Ukurasa Mkuu (Dashboard)


@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    
    # Chukua neno la kutafuta kama lipo
    search_query = request.args.get('search', '')
    
    conn = unganisha_db()
    if search_query:
        # Tafuta dawa inayofanana na neno lililoandikwa
        hoja = "SELECT * FROM dawa WHERE jina LIKE ? ORDER BY id DESC"
        dawa_zote = conn.execute(hoja, ('%' + search_query + '%',)).fetchall()
    else:
        # Kama hakuna search, onyesha zote kama kawaida
        dawa_zote = conn.execute("SELECT * FROM dawa ORDER BY id DESC").fetchall()
    
    return render_template('dashboard.html', dawa=dawa_zote, search_query=search_query, leo=datetime.now().date())

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = unganisha_db()
    dawa = conn.execute("SELECT * FROM dawa WHERE id=?", (id,)).fetchone()

    if request.method == 'POST':
        jina = request.form['jina']
        idadi = request.form['idadi']
        bei = request.form['bei']
        tarehe = request.form['tarehe']

        conn.execute("""
            UPDATE dawa 
            SET jina=?, idadi=?, bei=?, tarehe_kuisha=? 
            WHERE id=?
        """, (jina, idadi, bei, tarehe, id))

        conn.commit()
        return redirect(url_for('dashboard'))

    return render_template("edit.html", dawa=dawa)

# 4. Kuongeza Dawa (Marekebisho: request.form['bei'])
@app.route('/ongeza', methods=['POST'])
def ongeza():
    if request.method == 'POST':
        jina = request.form['jina']
        idadi = int(request.form['idadi'])
        # REKEBISHO: Hapa sasa inasoma 'bei' kutoka kwenye form
        bei = int(float(request.form['bei'])) 
        tarehe = request.form['tarehe']
        
        conn = unganisha_db()
        conn.execute("INSERT INTO dawa (jina, idadi, bei, tarehe_kuisha) VALUES (?, ?, ?, ?)", 
                     (jina, idadi, bei, tarehe))
        conn.commit()
        flash(f"Dawa '{jina}' imeongezwa kikamilifu!", "success")
        return redirect(url_for('dashboard'))

# 5. Kuuza Dawa
@app.route('/uza/<int:id>', methods=['POST'])
def uza(id):
    idadi_kuuza = int(request.form['idadi_kuuza'])
    conn = unganisha_db()
    dawa = conn.execute("SELECT * FROM dawa WHERE id=?", (id,)).fetchone()
    
    if dawa and dawa['idadi'] >= idadi_kuuza and idadi_kuuza > 0:
        idadi_mpya = dawa['idadi'] - idadi_kuuza
        jumla_pesa = idadi_kuuza * dawa['bei']
        tarehe_leo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute("UPDATE dawa SET idadi=? WHERE id=?", (idadi_mpya, id))
        conn.execute("INSERT INTO mauzo (jina_dawa, idadi_iliyouzwa, jumla_pesa, tarehe) VALUES (?, ?, ?, ?)", (dawa['jina'], idadi_kuuza, jumla_pesa, tarehe_leo))
        conn.commit()
        flash(f"Mauzo yamefanikiwa! Umepokea TZS {int(jumla_pesa)}", "success")
    else:
        flash("Idadi haitoshi stoo au umeweka namba isiyo sahihi!", "danger")
    return redirect(url_for('dashboard'))

# 6. Kufuta Dawa
@app.route('/futa/<int:id>')
def futa(id):
    conn = unganisha_db()
    conn.execute("DELETE FROM dawa WHERE id=?", (id,))
    conn.commit()
    flash("Dawa imefutwa kwenye mfumo!", "warning")
    return redirect(url_for('dashboard'))

# 7. Ripoti ya Mauzo
@app.route('/report')
def report():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    conn = unganisha_db()
    mauzo = conn.execute("SELECT * FROM mauzo ORDER BY id DESC").fetchall()
    jumla_kuu = sum([m['jumla_pesa'] for m in mauzo])
    return render_template('report.html', mauzo=mauzo, jumla_kuu=int(jumla_kuu))

# 8. Ku-Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 9. Futa Mauzo Yote
@app.route('/futa_mauzo_yote', methods=['POST'])
def futa_mauzo_yote():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    
    password_ya_kufuta = request.form.get('password_futa')
    ADMIN_PASSWORD = "futa2024" 

    if password_ya_kufuta == ADMIN_PASSWORD:
        conn = unganisha_db()
        conn.execute("DELETE FROM mauzo")
        conn.commit()
        flash("Historia yote ya mauzo imefutwa kikamilifu!", "success")
    else:
        flash("Password ya kufuta si sahihi! Kitendo kimesitishwa.", "danger")
        
    return redirect(url_for('report'))

if __name__ == '__main__':
    app.run(debug=False)