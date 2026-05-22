from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "siri_nzito_sana"

# URI yetu thabiti ya Supabase inayotumia dereva wa pg8000
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres.ltfzabxpwnxkuiwyomjv:Lemu1234#567@aws-0-eu-west-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def unganisha_db():
    return db.engine.raw_connection()

# Kutengeneza meza kwenye Supabase zikiwa hazipo
with app.app_context():
    try:
        conn = unganisha_db()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS dwa (
                            id SERIAL PRIMARY KEY, 
                            jina TEXT, 
                            idadi INTEGER, 
                            bei INTEGER, 
                            tarehe TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS mauzo (
                            id SERIAL PRIMARY KEY, 
                            dawa_id INTEGER, 
                            idadi INTEGER, 
                            jumla INTEGER, 
                            tarehe TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS watumiaji (
                            id SERIAL PRIMARY KEY, 
                            jina TEXT UNIQUE, 
                            nywila TEXT)''')
        
        # Kuongeza akaunti ya kwanza ya admin kama haipo
        cursor.execute("SELECT * FROM watumiaji WHERE jina = %s", ('admin',))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO watumiaji (jina, nywila) VALUES (%s, %s)", ('admin', 'admin123'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Initialization Error: {e}")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        jina = request.form['jina']
        nywila = request.form['nywila']
        
        try:
            conn = unganisha_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watumiaji WHERE jina = %s AND nywila = %s", (jina, nywila))
            mtumiaji = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if mtumiaji:
                session['mtumiaji'] = jina
                return redirect(url_for('dashboard'))
            else:
                flash("Jina au nywila si sahihi!", "danger")
                return redirect(url_for('login'))
        except Exception as e:
            flash("Imeshindwa kuunganisha kanizadata!", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'mtumiaji' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = unganisha_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dwa")
        dawa_zote = cursor.fetchall()
        
        cursor.execute("SELECT m.id, d.jina, m.idadi, m.jumla, m.tarehe FROM mauzo m JOIN dwa d ON m.dawa_id = d.id")
        mauzo_yote = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('dashboard.html', dwa=dawa_zote, mauzo=mauzo_yote)
    except Exception as e:
        return f"Ushonaji wa data umefeli: {e}"

@app.route('/ongeza_dawa', methods=['POST'])
def ongeza_dawa():
    if 'mtumiaji' not in session:
        return redirect(url_for('login'))
        
    jina = request.form['jina']
    idadi = int(request.form['idadi'])
    bei = int(request.form['bei'])
    tarehe = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = unganisha_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO dwa (jina, idadi, bei, tarehe) VALUES (%s, %s, %s, %s)", (jina, idadi, bei, tarehe))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Dawa imeongezwa kikamilifu!", "success")
    return redirect(url_for('dashboard'))

@app.route('/uza_dawa', methods=['POST'])
def uza_dawa():
    if 'mtumiaji' not in session:
        return redirect(url_for('login'))
        
    dawa_id = int(request.form['dawa_id'])
    idadi_ya_kuza = int(request.form['idadi'])
    tarehe = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = unganisha_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT idadi, bei FROM dwa WHERE id = %s", (dawa_id,))
    dawa = cursor.fetchone()
    
    if dawa and dawa[0] >= idadi_ya_kuza:
        idadi_baki = dawa[0] - idadi_ya_kuza
        jumla_bei = dawa[1] * idadi_ya_kuza
        
        cursor.execute("UPDATE dwa SET idadi = %s WHERE id = %s", (idadi_baki, dawa_id))
        cursor.execute("INSERT INTO mauzo (dawa_id, idadi, jumla, tarehe) VALUES (%s, %s, %s, %s)", (dawa_id, idadi_ya_kuza, jumla_bei, tarehe))
        conn.commit()
        flash("Mauzo yamefanyika kikamilifu!", "success")
    else:
        flash("Idadi ya dawa haitoshi stoki!", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

# HII NDIO NJIA YA 'report' ILIYOKUWA INATAFUTWA NA DASHBOARD YAKO KUTOKANA NA ERROR
@app.route('/report')
def report():
    if 'mtumiaji' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('mtumiaji', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=False)