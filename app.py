from flask import Flask, request, redirect, session, render_template_string
import os, random
try:
    import psycopg2
    import psycopg2.extras
except: psycopg2=None
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "CBC_KENYA_FINAL_2026"

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL and psycopg2:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    import sqlite3
    conn = sqlite3.connect('cbc.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    con=get_db(); c=con.cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS super_admin (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, is_first_login INT DEFAULT 1)")
        c.execute("CREATE TABLE IF NOT EXISTS schools (id SERIAL PRIMARY KEY, name TEXT, motto TEXT, logo TEXT, county TEXT, school_code TEXT UNIQUE, subdomain TEXT UNIQUE, status INT DEFAULT 1, admin_user TEXT UNIQUE, admin_pass_plain TEXT, admin_pass_hash TEXT, admin_first_login INT DEFAULT 1)")
        c.execute("SELECT * FROM super_admin WHERE id=1")
        if not c.fetchone():
            c.execute("INSERT INTO super_admin (id,username,password_hash,is_first_login) VALUES (1,'superadmin','',1)")
        con.commit()
    except Exception as e:
        print("Init error", e)
        try:
            c.execute("CREATE TABLE IF NOT EXISTS super_admin (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, is_first_login INT DEFAULT 1)")
            c.execute("CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, motto TEXT, logo TEXT, county TEXT, school_code TEXT UNIQUE, subdomain TEXT UNIQUE, status INT DEFAULT 1, admin_user TEXT UNIQUE, admin_pass_plain TEXT, admin_pass_hash TEXT, admin_first_login INT DEFAULT 1)")
            c.execute("SELECT * FROM super_admin WHERE id=1")
            if not c.fetchone():
                c.execute("INSERT INTO super_admin (id,username,password_hash,is_first_login) VALUES (1,'superadmin','',1)")
            con.commit()
        except Exception as e2:
            print(e2)
    con.close()

init_db()
TAILWIND = """<script src='https://cdn.tailwindcss.com'></script><div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>"""

@app.route('/')
def home():
    return render_template_string(TAILWIND+"""
    <div class='max-w-4xl mx-auto text-center mt-12 p-6'>
    <h1 class='text-4xl font-black'>🇰🇪 CBC MULTI-SCHOOL SYSTEM</h1>
    <p>PP1 to Grade 9 | By Joseph - Kitui</p>
    <div class='grid grid-cols-2 gap-4 mt-10'>
    <a href='/superadmin/login' class='bg-black text-white p-6 rounded-xl'>👑 SUPER ADMIN</a>
    <a href='/superadmin/dashboard' class='bg-green-600 text-white p-6 rounded-xl'>📊 GO TO DASHBOARD DIRECT</a>
    </div>
    <p class='mt-6 text-sm'>Live: cbc-system-pack.onrender.com | Status: LIVE</p></div>""")

@app.route('/superadmin/login', methods=['GET','POST'])
def super_login():
    con=get_db(); c=con.cursor()
    c.execute("SELECT * FROM super_admin WHERE id=1"); sa=c.fetchone(); con.close()
    is_first = sa['is_first_login'] if isinstance(sa, dict) else sa[3]
    if request.method=='POST':
        if is_first==1:
            h=generate_password_hash(request.form['newpass'])
            con=get_db(); c=con.cursor()
            c.execute("UPDATE super_admin SET password_hash=%s, is_first_login=0 WHERE id=1" % f"'{h}'" if not DATABASE_URL else "UPDATE super_admin SET password_hash=%s, is_first_login=0 WHERE id=1", (h,) if DATABASE_URL and psycopg2 else ())
            if not DATABASE_URL:
                con2=get_db(); c2=con2.cursor()
                try: c2.execute("UPDATE super_admin SET password_hash=?, is_first_login=0 WHERE id=1",(h,))
                except: c2.execute(f"UPDATE super_admin SET password_hash='{h}', is_first_login=0 WHERE id=1")
                con2.commit(); con2.close()
            else:
                con.commit(); con.close()
            session['super']=True; return redirect('/superadmin/dashboard')
        else:
            phash = sa['password_hash'] if isinstance(sa, dict) else sa[2]
            if check_password_hash(phash, request.form['pass']):
                session['super']=True; return redirect('/superadmin/dashboard')
            return "Wrong password"
    return render_template_string(TAILWIND+f"""
    <div class='flex justify-center items-center h-screen bg-gray-100'><div class='bg-white p-8 rounded shadow w-96'>
    <h2 class='font-bold text-center text-xl'>👑 SUPER ADMIN</h2>
    {"<form method='POST' class='mt-4'><p class='bg-yellow-100 p-2 text-sm mb-2'>FIRST LOGIN: Enter First Password</p><input name='newpass' type='password' placeholder='Enter First Password' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>SET PASSWORD</button></form>" if is_first==1 else "<form method='POST' class='mt-4'><input name='pass' type='password' placeholder='••••••••' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>LOGIN</button></form>"}
    </div></div>""")

@app.route('/superadmin/dashboard', methods=['GET','POST'])
def super_dash():
    if not session.get('super'):
        return redirect('/superadmin/login')
    con=get_db(); c=con.cursor()
    if request.method=='POST':
        try:
            name=request.form.get('name','').strip()
            if name:
                motto=request.form.get('motto',''); county=request.form.get('county','Kitui')
                code=''.join([x for x in name.upper() if x.isalpha()][:3])+str(random.randint(100,999))
                sub=code.lower(); admin_user=sub+"_admin"; plain="Admin123"; phash=generate_password_hash(plain)
                if DATABASE_URL and psycopg2:
                    c.execute("INSERT INTO schools (name,motto,logo,county,school_code,subdomain,admin_user,admin_pass_plain,admin_pass_hash,admin_first_login) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1)",(name,motto,'default.png',county,code,sub,admin_user,plain,phash))
                else:
                    c.execute("INSERT INTO schools (name,motto,logo,county,school_code,subdomain,admin_user,admin_pass_plain,admin_pass_hash,admin_first_login) VALUES (?,?,?,?,?,?,?,?,?,1)",(name,motto,'default.png',county,code,sub,admin_user,plain,phash))
                con.commit()
        except Exception as e:
            print("Add school error:", e)
    try:
        c.execute("SELECT * FROM schools ORDER BY id DESC")
        schools=c.fetchall()
    except: schools=[]
    con.close()
    rows=""
    for s in schools:
        try:
            d=dict(s) if not isinstance(s, tuple) else {"id":s[0],"name":s[1],"motto":s[2],"county":s[4],"school_code":s[5],"subdomain":s[6],"admin_user":s[8],"admin_pass_plain":s[9]}
            rows+=f"<tr class='border-b'><td class='p-2'>{d.get('name','')}</td><td class='p-2'><b>{d.get('school_code','')}</b></td><td class='p-2 text-xs text-blue-600'>{d.get('subdomain','')}.yourdomain.com<br><a class='underline' href='/?school={d.get('school_code','')}'>?school={d.get('school_code','')}</a></td><td class='p-2'>{d.get('admin_user','')}</td><td class='p-2 bg-yellow-100'>{d.get('admin_pass_plain','')}</td><td class='p-2'>{d.get('county','')}</td></tr>"
        except: pass
    return render_template_string(TAILWIND+f"""
    <div class='p-4'><h1 class='text-2xl font-bold'>👑 SUPER DASHBOARD - Total: {len(schools)}</h1>
    <div class='grid grid-cols-1 md:grid-cols-3 gap-4 mt-6'>
    <div class='bg-white p-4 rounded shadow'><h3 class='font-bold'>➕ Add School</h3>
    <form method='POST'><input name='name' placeholder='School Name' class='w-full border p-2 mb-2' required><input name='motto' placeholder='Motto' class='w-full border p-2 mb-2'><input name='county' placeholder='County' class='w-full border p-2 mb-2' required><button class='bg-green-600 text-white w-full p-2'>REGISTER</button></form></div>
    <div class='md:col-span-2 bg-white p-4 rounded shadow overflow-auto'><table class='w-full text-sm'><tr class='bg-black text-white'><th class='p-2'>Name</th><th>Code</th><th>Link</th><th>Admin</th><th>Password (Super Only)</th><th>County</th></tr>{rows if rows else "<tr><td colspan=6 class='p-4 text-center'>No schools - Add first school now!</td></tr>"}</table></div></div>
    <a href='/' class='mt-6 inline-block underline'>Home</a></div>""")

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
