from flask import Flask, request, redirect, session, render_template_string
import os
try:
    import psycopg2
    import psycopg2.extras
except:
    psycopg2 = None
import sqlite3

app = Flask(__name__)
app.secret_key = "final2026"

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL and psycopg2:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('cbc.db')

def init_db():
    con = get_db()
    c = con.cursor()
    try:
        c.execute('CREATE TABLE IF NOT EXISTS schools (id SERIAL PRIMARY KEY, name TEXT, code TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)')
        c.execute("INSERT INTO schools (id,name,code,admin_user,admin_pass) VALUES (1,'SUPER','SUPER','superadmin','admin123') ON CONFLICT (id) DO NOTHING")
    except:
        c.execute('CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)')
        c.execute("INSERT OR IGNORE INTO schools (id,name,code,admin_user,admin_pass) VALUES (1,'SUPER','SUPER','superadmin','admin123')")
    con.commit()
    con.close()

init_db()

# HOME PAGE - Fixes your Not Found
@app.route('/')
def home():
    return render_template_string("""
    <h1>🎉 CBC SYSTEM - KENYA LIVE</h1>
    <p>System by Joseph - Kitui</p>
    <a href='/superadmin'><button>SUPER ADMIN LOGIN</button></a><br><br>
    <a href='/admin'>Headteacher Login</a> | 
    <a href='/teacher'>Teacher Login</a> | 
    <a href='/parent'>Parent Login</a>
    <p>Link: https://cbc-system-pack.onrender.com</p>
    """)

@app.route('/superadmin', methods=['GET','POST'])
def superadmin():
    if request.method == 'POST':
        if request.form['user']=='superadmin' and request.form['pass']=='admin123':
            session['super']=True
            return redirect('/superadmin/dashboard')
    return """
    <h2>SuperAdmin Login</h2>
    <form method='POST'>
    User: <input name='user'><br>
    Pass: <input name='pass' type='password'><br>
    <button>Login</button>
    </form>
    """

@app.route('/superadmin/dashboard')
def super_dash():
    if not session.get('super'): return redirect('/superadmin')
    con=get_db(); c=con.cursor()
    c.execute("SELECT * FROM schools")
    schools=c.fetchall()
    con.close()
    return f"<h1>SUPER DASHBOARD - Schools: {len(schools)}</h1><p>{schools}</p><a href='/'>Home</a>"

@app.route('/admin')
def admin_page(): return "<h1>Headteacher Login Page - Coming</h1><a href='/'>Home</a>"
@app.route('/teacher')
def teacher_page(): return "<h1>Teacher Login Page - Coming</h1><a href='/'>Home</a>"
@app.route('/parent')
def parent_page(): return "<h1>Parent Login Page - Coming</h1><a href='/'>Home</a>"

if __name__=='__main__':
    app.run()
