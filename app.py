from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "siri_nzito_sana"

# URI yako ya Supabase tukiwa tumeiweka sawa
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.ltfzabxpwnxkuiwyomjv:Lemu1234#567@aws-0-eu-west-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tumeizungushia TRY/EXCEPT ili hata database ikigoma, APP ISIFE!
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f"DATABASE ERROR LAKINI APP INAWAKA: {e}")

@app.route('/')
def login():
    return "<h1>Chombo Kiko Hewani! Mfumo wa Babrah Pharmacy Unafanya Kazi!</h1>"

if __name__ == '__main__':
    # Hii inasaidia kupata PORT ya Render kiotomatiki
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)