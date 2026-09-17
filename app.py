from flask import Flask, request, redirect, session
import os, random

app = Flask(__name__)
app.secret_key = "joseph_kitui_final_2026"

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL:
        try:
            import psycopg2, psycopg2.extras
            return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        except: pass
    import sqlite3
    conn = sqlite3.connect('/tmp/cbc.db')
    conn.row_factory = sqlite3.Row
    return conn

def run_query(c, query, params):
    # Auto tries Postgres then SQLite
    try:
        c.execute(query, params)
    except:
        # Convert %s to? for SQLite
        q = query.replace('%s','?')
        c.execute(q, params)

def init_db():
    con=get_db(); c=con.cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS super_admin (id INTEGER PRIMARY KEY, username TEXT, password TEXT, first INTEGER DEFAULT 1)")
        c.execute("CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, motto TEXT, county TEXT, code TEXT UNIQUE, sub TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)")
        run_query(c, "SELECT * FROM super_admin WHERE id=%s", (1,))
        row = c.fetchone()
        if not row:
            run_query(c, "INSERT INTO super_admin (id,username,password,first) VALUES (%s,%s,%s,%s)", (1,'superadmin','',1))
        con.commit()
    except Exception as e:
        print("Init error:", e)
    con.close()

init_db()

@app.route('/')
def home():
    return """<div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
    <div style='text-align:center;margin-top:60px;font-family:sans-serif'><h1>🇰🇪 CBC SYSTEM - LIVE</h1><p>By Joseph Kitui</p>
    <br><a href='/superadmin/login' style='background:black;color:white;padding:15px 30px;text-decoration:none;border-radius:8px'>👑 SUPER ADMIN</a></div>"""

@app.route('/superadmin/login', methods=['GET','POST'])
def s_login():
    con=get_db(); c=con.cursor()
    try:
        run_query(c, "SELECT * FROM super_admin WHERE id=%s", (1,))
        sa=c.fetchone()
    except: sa=None
    con.close()
    if not sa:
        first=1
    else:
        try: first=sa['first']
        except: first=sa[3]

    if request.method=='POST':
        pwd = (request.form.get('newpass') or request.form.get('pass') or '').strip()
        if not pwd:
            return "<p>Enter password</p><a href='/superadmin/login'>Back</a>"
        con=get_db(); c=con.cursor()
        try:
            if first==1:
                run_query(c, "UPDATE super_admin SET password=%s, first=0 WHERE id=%s", (pwd,1))
                con.commit()
                con.close()
                session['super']=True
                return redirect('/superadmin/dashboard')
            else:
                saved = sa['password'] if isinstance(sa, dict) or hasattr(sa,'keys') else sa[2]
                if pwd==saved:
                    con.close()
                    session['super']=True
                    return redirect('/superadmin/dashboard')
                con.close()
                return f"Wrong password. <a href='/superadmin/login'>Back</a>"
        except Exception as e:
            con.close()
            return f"DB Error: {e} <a href='/superadmin/login'>Back</a>"

    if first==1:
        return """<div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
        <div style='max-width:350px;margin:80px auto;font-family:sans-serif;background:white;padding:30px;box-shadow:0 0 10px #ccc;border-radius:10px;text-align:center'>
        <h2>👑 SUPER ADMIN</h2><p style='background:#fff3cd;padding:8px;font-size:13px'>FIRST LOGIN: Enter First Password</p>
        <form method='POST'><input name='newpass' type='password' placeholder='Enter First Password' style='width:100%;padding:12px;margin:10px 0;border:1px solid #ccc' required>
        <button style='width:100%;padding:12px;background:black;color:white'>SET PASSWORD</button></form></div>"""
    else:
        return """<div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
        <div style='max-width:350px;margin:80px auto;font-family:sans-serif;background:white;padding:30px;box-shadow:0 0 10px #ccc;border-radius:10px;text-align:center'>
        <h2>👑 SUPER ADMIN LOGIN</h2><form method='POST'>
        <input name='pass' type='password' placeholder='••••••••' style='width:100%;padding:12px;margin:10px 0;border:1px solid #ccc' required>
        <button style='width:100%;padding:12px;background:black;color:white'>LOGIN</button></form></div>"""

@app.route('/superadmin/dashboard', methods=['GET','POST'])
def s_dash():
    if not session.get('super'): return redirect('/superadmin/login')
    con=get_db(); c=con.cursor()
    if request.method=='POST':
        name=(request.form.get('name') or '').strip()
        if name:
            county=request.form.get('county','Kitui'); motto=request.form.get('motto','')
            code=''.join([x for x in name.upper() if x.isalpha()][:3])+str(random.randint(100,999))
            sub=code.lower(); admin_user=sub+"_admin"
            try:
                run_query(c, "INSERT INTO schools (name,motto,county,code,sub,admin_user,admin_pass) VALUES (%s,%s,%s,%s,%s,%s,%s)", (name,motto,county,code,sub,admin_user,"Admin123"))
                con.commit()
            except Exception as e:
                print("Insert error:", e)
    try:
        c.execute("SELECT * FROM schools ORDER BY id DESC")
        schools=c.fetchall()
    except: schools=[]
    con.close()
    rows=""
    for s in schools:
        try:
            d=dict(s)
            rows+=f"<tr><td style='padding:8px;border:1px solid #ddd'>{d.get('name','')}</td><td style='padding:8px;border:1px solid #ddd'><b>{d.get('code','')}</b></td><td style='padding:8px;border:1px solid #ddd'>{d.get('sub','')}.yourdomain.com<br><a href='/?school={d.get('code','')}'>?school={d.get('code','')}</a></td><td style='padding:8px;border:1px solid #ddd'>{d.get('admin_user','')}</td><td style='padding:8px;border:1px solid #ddd;background:yellow'><b>{d.get('admin_pass','')}</b></td></tr>"
        except: pass
    return f"""<div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
    <div style='padding:20px;font-family:sans-serif'><h2>👑 SUPER DASHBOARD - {len(schools)} Schools</h2>
    <div style='display:flex;gap:20px;margin-top:20px;flex-wrap:wrap'>
    <div style='width:300px;background:white;padding:15px;box-shadow:0 0 5px #ccc'><h3>➕ Add School</h3>
    <form method='POST'><input name='name' placeholder='School Name' style='width:100%;padding:8px;margin:5px 0' required>
    <input name='motto' placeholder='Motto' style='width:100%;padding:8px;margin:5px 0'><input name='county' placeholder='County' style='width:100%;padding:8px;margin:5px 0' required>
    <button style='width:100%;padding:10px;background:green;color:white'>REGISTER</button></form></div>
    <div style='flex:1;background:white;padding:15px;box-shadow:0 0 5px #ccc'><table style='width:100%;border-collapse:collapse'><tr style='background:black;color:white'><th style='padding:8px'>Name</th><th>Code</th><th>Link</th><th>Admin</th><th>Pass (Super Only)</th></tr>
    {rows if rows else "<tr><td colspan=5 style='padding:20px;text-align:center'>No schools - Add now!</td></tr>"}</table></div></div>
    <br><a href='/'>Home</a></div>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
