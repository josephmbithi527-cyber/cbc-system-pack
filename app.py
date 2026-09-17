from flask import Flask, request, redirect, session, render_template_string
import os, random
try:
    import psycopg2
    import psycopg2.extras
except:
    psycopg2=None

app = Flask(__name__)
app.secret_key = "joseph_final_2026"

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL and psycopg2:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    import sqlite3
    conn = sqlite3.connect('cbc.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    con=get_db(); c=con.cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS super_admin (id SERIAL PRIMARY KEY, username TEXT, password TEXT, first INT DEFAULT 1)")
        c.execute("SELECT * FROM super_admin WHERE id=1")
        if not c.fetchone():
            c.execute("INSERT INTO super_admin (id,username,password,first) VALUES (1,'superadmin','',1)")
        c.execute("CREATE TABLE IF NOT EXISTS schools (id SERIAL PRIMARY KEY, name TEXT, motto TEXT, county TEXT, code TEXT UNIQUE, sub TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)")
        con.commit()
    except Exception as e:
        print(e)
    con.close()

init_db()

@app.route('/')
def home():
    return """
    <div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
    <div style='text-align:center;margin-top:50px;font-family:sans-serif'>
    <h1>🇰🇪 CBC MULTI-SCHOOL SYSTEM</h1><p>By Joseph Kitui</p>
    <br><a href='/superadmin/login' style='background:black;color:white;padding:15px 30px;text-decoration:none;border-radius:8px'>👑 SUPER ADMIN LOGIN</a>
    <br><br><br><p>Live: cbc-system-pack.onrender.com</p></div>
    """

@app.route('/superadmin/login', methods=['GET','POST'])
def s_login():
    con=get_db(); c=con.cursor()
    c.execute("SELECT * FROM super_admin WHERE id=1")
    sa=c.fetchone()
    con.close()

    first = sa['first'] if isinstance(sa, dict) else sa[3] if sa else 1

    if request.method=='POST':
        pwd = request.form.get('newpass') or request.form.get('pass')
        if not pwd:
            return "Please enter password <a href='/superadmin/login'>Back</a>"

        con=get_db(); c=con.cursor()
        try:
            # SUPER SIMPLE: Save as plain text to avoid hash crash, but input is hidden ••••
            if first==1:
                if DATABASE_URL:
                    c.execute("UPDATE super_admin SET password=%s, first=0 WHERE id=1", (pwd,))
                else:
                    c.execute("UPDATE super_admin SET password=?, first=0 WHERE id=1", (pwd,))
                con.commit()
                con.close()
                session['super']=True
                return redirect('/superadmin/dashboard')
            else:
                # Check password
                saved = sa['password'] if isinstance(sa, dict) else sa[2]
                if pwd==saved:
                    con.close()
                    session['super']=True
                    return redirect('/superadmin/dashboard')
                else:
                    con.close()
                    return f"Wrong password. Saved is {saved} but you typed {pwd}. <a href='/superadmin/login'>Back</a>"
        except Exception as e:
            con.close()
            return f"Error: {e} <a href='/superadmin/login'>Back</a>"

    if first==1:
        return """
        <div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
        <div style='max-width:350px;margin:80px auto;font-family:sans-serif;background:white;padding:30px;box-shadow:0 0 10px #ccc;border-radius:10px;text-align:center'>
        <h2>👑 SUPER ADMIN</h2><p style='background:#fff3cd;padding:8px;font-size:13px'>FIRST LOGIN: Enter First Password</p>
        <form method='POST'><input name='newpass' type='password' placeholder='Enter First Password' style='width:100%;padding:12px;margin:10px 0;border:1px solid #ccc' required>
        <button style='width:100%;padding:12px;background:black;color:white'>SET PASSWORD</button></form></div>
        """
    else:
        return """
        <div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
        <div style='max-width:350px;margin:80px auto;font-family:sans-serif;background:white;padding:30px;box-shadow:0 0 10px #ccc;border-radius:10px;text-align:center'>
        <h2>👑 SUPER ADMIN LOGIN</h2>
        <form method='POST'><input name='pass' type='password' placeholder='••••••••' style='width:100%;padding:12px;margin:10px 0;border:1px solid #ccc' required>
        <button style='width:100%;padding:12px;background:black;color:white'>LOGIN</button></form></div>
        """

@app.route('/superadmin/dashboard', methods=['GET','POST'])
def s_dash():
    if not session.get('super'):
        return redirect('/superadmin/login')
    con=get_db(); c=con.cursor()
    if request.method=='POST':
        name=request.form.get('name','').strip()
        if name:
            county=request.form.get('county','Kitui')
            motto=request.form.get('motto','')
            code=''.join([x for x in name.upper() if x.isalpha()][:3])+str(random.randint(100,999))
            sub=code.lower()
            admin_user=sub+"_admin"
            try:
                if DATABASE_URL:
                    c.execute("INSERT INTO schools (name,motto,county,code,sub,admin_user,admin_pass) VALUES (%s,%s,%s,%s,%s,%s,%s)", (name,motto,county,code,sub,admin_user,"Admin123"))
                else:
                    c.execute("INSERT INTO schools (name,motto,county,code,sub,admin_user,admin_pass) VALUES (?,?,?,?,?,?,?)", (name,motto,county,code,sub,admin_user,"Admin123"))
                con.commit()
            except Exception as e:
                print(e)
    c.execute("SELECT * FROM schools ORDER BY id DESC")
    schools=c.fetchall()
    con.close()
    rows=""
    for s in schools:
        d=dict(s)
        rows+=f"<tr><td style='padding:8px;border:1px solid #ddd'>{d['name']}</td><td style='padding:8px;border:1px solid #ddd'><b>{d['code']}</b></td><td style='padding:8px;border:1px solid #ddd'>{d['sub']}.yourdomain.com<br><a href='/?school={d['code']}'>?school={d['code']}</a></td><td style='padding:8px;border:1px solid #ddd'>{d['admin_user']}</td><td style='padding:8px;border:1px solid #ddd;background:yellow'>{d['admin_pass']}</td></tr>"
    return f"""
    <div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>
    <div style='padding:20px;font-family:sans-serif'>
    <h2>👑 SUPER DASHBOARD - Total Schools: {len(schools)}</h2>
    <div style='display:flex;gap:20px;margin-top:20px'>
    <div style='width:300px;background:white;padding:15px;box-shadow:0 0 5px #ccc'><h3>➕ Add School</h3>
    <form method='POST'><input name='name' placeholder='School Name e.g. Mutune Primary' style='width:100%;padding:8px;margin:5px 0' required>
    <input name='motto' placeholder='Motto' style='width:100%;padding:8px;margin:5px 0'><input name='county' placeholder='County e.g. Kitui' style='width:100%;padding:8px;margin:5px 0' required>
    <button style='width:100%;padding:10px;background:green;color:white'>REGISTER SCHOOL</button></form></div>
    <div style='flex:1;background:white;padding:15px;box-shadow:0 0 5px #ccc;overflow:auto'><h3>🏫 All Schools - Only SuperAdmin Sees Passwords</h3>
    <table style='width:100%;border-collapse:collapse;margin-top:10px'><tr style='background:black;color:white'><th style='padding:8px'>Name</th><th>Code</th><th>Link</th><th>Admin</th><th>Password</th></tr>
    {rows if rows else "<tr><td colspan=5 style='padding:20px;text-align:center'>No schools yet - Add one!</td></tr>"}</table></div></div>
    <br><a href='/'>Home</a> | <a href='/superadmin/login'>Logout</a></div>
    """

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
