from flask import Flask, request, redirect, session, render_template_string, g
import os, random, datetime

app = Flask(__name__)
app.secret_key = "CBC_KENYA_FULL_PACK_JOSEPH_2026_FINAL"

DATABASE_URL = os.environ.get('DATABASE_URL')

# --- DATABASE HELPER (Works for Postgres & SQLite on Render) ---
def get_db():
    if DATABASE_URL:
        try:
            import psycopg2, psycopg2.extras
            return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        except: pass
    import sqlite3
    path = '/tmp/cbc_full.db' if os.path.exists('/tmp') else 'cbc_full.db'
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def run(c, q, p=()):
    try: c.execute(q, p)
    except:
        try: c.execute(q.replace('%s','?'), p)
        except Exception as e: print("SQL Error:", e, q)

def init_db():
    con=get_db(); c=con.cursor()
    try:
        # SUPER ADMIN
        c.execute("CREATE TABLE IF NOT EXISTS super_admin (id INTEGER PRIMARY KEY, username TEXT, password TEXT, first INTEGER DEFAULT 1)")
        # SCHOOLS
        c.execute("CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, motto TEXT, county TEXT, code TEXT UNIQUE, sub TEXT UNIQUE, admin_user TEXT, admin_pass TEXT, logo TEXT DEFAULT 'default.png')")
        # USERS (School Admins, Teachers)
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, school_code TEXT, username TEXT UNIQUE, password TEXT, role TEXT, fullname TEXT, first INTEGER DEFAULT 1)")
        # CLASSES - CBC: PP1,PP2,Grade1-9
        c.execute("CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, school_code TEXT, name TEXT, teacher TEXT)")
        # LEARNERS
        c.execute("CREATE TABLE IF NOT EXISTS learners (id INTEGER PRIMARY KEY, school_code TEXT, admission_no TEXT, fullname TEXT, class_name TEXT, gender TEXT, parent_phone TEXT, upi TEXT)")
        # CBC ASSESSMENTS
        c.execute("CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, school_code TEXT, learner_id INTEGER, subject TEXT, term TEXT, score TEXT, remarks TEXT, date TEXT)")

        run(c, "SELECT * FROM super_admin WHERE id=%s", (1,))
        if not c.fetchone():
            run(c, "INSERT INTO super_admin (id,username,password,first) VALUES (%s,%s,%s,%s)", (1,'superadmin','',1))
        con.commit()
    except Exception as e: print("Init error", e)
    con.close()

init_db()

# --- KENYA FLAG + TAILWIND ---
STYLE = """<script src='https://cdn.tailwindcss.com'></script>
<div style='height:6px;background:linear-gradient(to right,black 33%,red 33%,red 66%,green 66%)'></div>"""

CBC_CLASSES = ["PP1","PP2","Grade 1","Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7","Grade 8","Grade 9"]
CBC_SUBJECTS = ["Mathematics","English","Kiswahili","Science & Technology","Social Studies","CRE","Agriculture","Music","Art & Craft","PE"]

def get_school_from_request():
    # Only use ?school=CODE - Don't read Render domain
    code = request.args.get('school') or request.args.get('code') or ''
    return code.strip().upper()

# ================= HOME - FIXED =================
@app.route('/')
def home():
    scode = get_school_from_request()
    if scode:
        return school_home(scode)
    # Show MAIN landing page, not school error
    schools = get_all_schools()
    scount = len(schools)
    return render_template_string(STYLE+f"""
    <div class='max-w-5xl mx-auto text-center mt-10 p-6 font-sans'>
    <h1 class='text-4xl font-black'>🇰🇪 CBC MULTI-SCHOOL SYSTEM</h1>
    <p class='text-gray-600 mt-2'>PP1 - Grade 9 | One Link Per School | By Joseph - Kitui | {scount} Schools Live</p>
    <div class='grid grid-cols-1 md:grid-cols-3 gap-4 mt-10'>
      <a href='/superadmin/login' class='bg-black text-white p-6 rounded-xl shadow'>👑 SUPER ADMIN<br><span class='text-xs'>Add Schools & See Passwords (••••)</span></a>
      <div class='bg-green-600 text-white p-6 rounded-xl shadow'>🏫 YOUR SCHOOLS<br><span class='text-xs'>Use ?school=CODE<br>KIM917, KAB861 Live</span></div>
      <div class='bg-blue-600 text-white p-6 rounded-xl shadow'>🔗 TEST LINK<br><span class='text-xs'>cbc-system-pack.onrender.com/?school=KIM917</span></div>
    </div>
    <div class='mt-10 bg-white p-4 rounded shadow text-left'>
      <h3 class='font-bold'>📚 How to Open a School:</h3>
      <p class='text-sm mt-2'>1. Super Admin adds school → Code KIM917<br>2. Open: <b>https://cbc-system-pack.onrender.com/?school=KIM917</b><br>3. Click School Admin Login → User: kim917_admin / Admin123 → Set new password ••••<br>4. Dashboard → Add Learners PP1-G9</p>
    </div>
    <p class='mt-8 text-xs'>Live: cbc-system-pack.onrender.com | Main domain fixed!</p>
    </div>""")
def get_all_schools():
    con=get_db(); c=con.cursor()
    try: c.execute("SELECT * FROM schools ORDER BY id DESC"); rows=c.fetchall()
    except: rows=[]
    con.close(); return rows

def school_home(code):
    con=get_db(); c=con.cursor()
    run(c,"SELECT * FROM schools WHERE code=%s",(code,))
    sch=c.fetchone(); con.close()
    if not sch: return f"<h3>School {code} not found. Contact Super Admin.</h3><a href='/'>Home</a>"
    d=dict(sch); name=d.get('name',''); motto=d.get('motto',''); county=d.get('county','')
    return render_template_string(STYLE+f"""
    <div class='max-w-5xl mx-auto p-6 font-sans'>
    <div class='flex justify-between items-center bg-white p-4 rounded shadow'>
      <div><h1 class='text-2xl font-black'>{name}</h1><p class='text-sm text-gray-600'>{motto} | {county} | CODE: {code}</p></div>
      <div class='text-right'><span class='bg-black text-white px-3 py-1 rounded text-xs'>{code}.yourdomain.com</span></div>
    </div>
    <div class='grid grid-cols-2 md:grid-cols-4 gap-4 mt-8'>
      <a href='/school/{code}/login' class='bg-black text-white p-6 rounded-xl text-center'>🔐 School Admin Login</a>
      <a href='/school/{code}/teachers' class='bg-blue-600 text-white p-6 rounded-xl text-center'>👨‍🏫 Teachers Portal</a>
      <a href='/school/{code}/learners' class='bg-green-600 text-white p-6 rounded-xl text-center'>🎓 Learners (PP1-G9)</a>
      <a href='/school/{code}/assessments' class='bg-orange-600 text-white p-6 rounded-xl text-center'>📊 CBC Assessments</a>
    </div>
    <p class='mt-6'><a href='/' class='underline'>← Back to Main</a></p></div>""")

# ================= SUPER ADMIN =================
@app.route('/superadmin/login', methods=['GET','POST'])
def s_login():
    con=get_db(); c=con.cursor()
    run(c,"SELECT * FROM super_admin WHERE id=%s",(1,)); sa=c.fetchone(); con.close()
    first = sa['first'] if sa and 'first' in sa.keys() else (sa[3] if sa else 1)
    if request.method=='POST':
        pwd=(request.form.get('newpass') or request.form.get('pass') or '').strip()
        if not pwd: return "Enter password <a href='/superadmin/login'>Back</a>"
        con=get_db(); c=con.cursor()
        if first==1:
            run(c,"UPDATE super_admin SET password=%s, first=0 WHERE id=%s",(pwd,1)); con.commit(); con.close(); session['super']=True; return redirect('/superadmin/dashboard')
        else:
            saved = sa['password'] if 'password' in sa.keys() else sa[2]
            con.close()
            if pwd==saved: session['super']=True; return redirect('/superadmin/dashboard')
            return "Wrong password <a href='/superadmin/login'>Back</a>"
    form = f"<form method='POST'><input name='newpass' type='password' placeholder='Enter First Password' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>SET PASSWORD</button></form>" if first==1 else f"<form method='POST'><input name='pass' type='password' placeholder='••••••••' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>LOGIN</button></form>"
    return render_template_string(STYLE+f"<div class='max-w-sm mx-auto mt-20 bg-white p-8 rounded shadow text-center'><h2 class='font-bold text-xl'>👑 SUPER ADMIN</h2><p class='bg-yellow-100 text-xs p-2 mt-2'>{'FIRST LOGIN' if first==1 else 'Login with •••• hidden'}</p><div class='mt-4'>{form}</div></div>")

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
            run(c,"INSERT INTO schools (name,motto,county,code,sub,admin_user,admin_pass) VALUES (%s,%s,%s,%s,%s,%s,%s)",(name,motto,county,code,sub,admin_user,"Admin123"))
            con.commit()
            # Create classes for this school
            for cl in CBC_CLASSES:
                run(c,"INSERT INTO classes (school_code,name,teacher) VALUES (%s,%s,%s)",(code,cl,""))
            con.commit()
    c.execute("SELECT * FROM schools ORDER BY id DESC"); schools=c.fetchall(); con.close()
    rows="".join([f"<tr><td class='p-2 border'>{dict(s).get('name')}</td><td class='p-2 border'><b>{dict(s).get('code')}</b></td><td class='p-2 border text-xs text-blue-600'><a href='/?school={dict(s).get('code')}' class='underline'>/?school={dict(s).get('code')}</a><br>{dict(s).get('sub')}.yourdomain.com</td><td class='p-2 border'>{dict(s).get('admin_user')}</td><td class='p-2 border bg-yellow-200'><b>{dict(s).get('admin_pass')}</b></td><td class='p-2 border'><a href='/school/{dict(s).get('code')}/login' class='bg-black text-white px-2 py-1 rounded text-xs'>Login</a></td></tr>" for s in schools])
    return render_template_string(STYLE+f"""
    <div class='p-4 font-sans'><h1 class='text-2xl font-bold'>👑 SUPER DASHBOARD - {len(schools)} Schools | INSTRUCTION: Only Super Sees Passwords</h1>
    <div class='flex gap-4 mt-4 flex-wrap'>
      <div class='w-80 bg-white p-4 rounded shadow'><h3 class='font-bold'>➕ Add School (TEMPLATE)</h3>
      <p class='text-xs text-gray-500 mb-2'>Fill: Name, Motto, County. Code auto = 3 letters + 3 digits. Admin auto = code_admin / Admin123 hidden ••••</p>
      <form method='POST'><input name='name' placeholder='e.g. KIMUUNI PRIMARY SCHOOL' class='w-full border p-2 mb-2' required><input name='motto' placeholder='Elimu ni Ufunguo' class='w-full border p-2 mb-2'><input name='county' placeholder='Kitui' class='w-full border p-2 mb-2' required><button class='bg-green-600 text-white w-full p-2 rounded'>REGISTER SCHOOL</button></form></div>
      <div class='flex-1 bg-white p-4 rounded shadow overflow-auto'><table class='w-full text-sm border'><tr class='bg-black text-white'><th class='p-2'>Name</th><th>Code</th><th>Link</th><th>Admin</th><th>Pass (Super Only)</th><th>Action</th></tr>{rows or "<tr><td colspan=6 class='p-4 text-center'>No schools yet</td></tr>"}</table></div>
    </div><br><a href='/' class='underline'>Home</a> | <a href='/superadmin/login'>Logout</a></div>""")

# ================= SCHOOL ADMIN LOGIN =================
@app.route('/school/<code>/login', methods=['GET','POST'])
def school_login(code):
    code=code.upper()
    con=get_db(); c=con.cursor()
    run(c,"SELECT * FROM schools WHERE code=%s",(code,)); sch=c.fetchone()
    if not sch: con.close(); return "School not found"
    schd=dict(sch)
    # Check first login
    first = 1 if schd.get('admin_pass')=="Admin123" else 0
    if request.method=='POST':
        pwd=(request.form.get('newpass') or request.form.get('pass') or '').strip()
        if first==1:
            run(c,"UPDATE schools SET admin_pass=%s WHERE code=%s",(pwd,code)); con.commit(); con.close(); session[f'school_{code}']=True; return redirect(f'/school/{code}/dashboard')
        else:
            if pwd==schd.get('admin_pass'): con.close(); session[f'school_{code}']=True; return redirect(f'/school/{code}/dashboard')
            con.close(); return "Wrong password <a href=''>Back</a>"
    con.close()
    form = f"<p class='bg-yellow-100 p-2 text-xs mb-2'>FIRST LOGIN: Change default Admin123. Password hidden ••••</p><form method='POST'><input name='newpass' type='password' placeholder='New Password ••••' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>SET PASSWORD</button></form>" if first==1 else f"<form method='POST'><input name='pass' type='password' placeholder='••••••••' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>LOGIN AS {schd.get('admin_user')}</button></form>"
    return render_template_string(STYLE+f"<div class='max-w-sm mx-auto mt-16 bg-white p-8 rounded shadow'><h2 class='font-bold text-center'>{schd.get('name')}<br><span class='text-xs'>{code} Admin</span></h2><div class='mt-4'>{form}</div><a href='/?school={code}' class='text-xs underline'>← School Home</a></div>")

@app.route('/school/<code>/dashboard')
def school_dash(code):
    code=code.upper()
    if not session.get(f'school_{code}'): return redirect(f'/school/{code}/login')
    con=get_db(); c=con.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM learners WHERE school_code=%s".replace('%s','?') if not DATABASE_URL else "SELECT COUNT(*) as cnt FROM learners WHERE school_code=%s", (code,))
    try: learners=c.fetchone(); lcnt=learners['cnt'] if isinstance(learners, dict) else learners[0]
    except: lcnt=0
    con.close()
    return render_template_string(STYLE+f"""
    <div class='p-6 font-sans max-w-5xl mx-auto'>
    <h1 class='text-2xl font-bold'>🏫 {code} DASHBOARD</h1>
    <p class='text-sm'>Learners: {lcnt} | Classes: {len(CBC_CLASSES)} (PP1-G9)</p>
    <div class='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
      <a href='/school/{code}/learners/add' class='bg-blue-600 text-white p-5 rounded text-center'>➕ Add Learner<br><span class='text-xs'>Admission, UPI, Class</span></a>
      <a href='/school/{code}/learners' class='bg-green-600 text-white p-5 rounded text-center'>🎓 View Learners<br><span class='text-xs'>PP1 to Grade 9</span></a>
      <a href='/school/{code}/teachers/add' class='bg-purple-600 text-white p-5 rounded text-center'>👨‍🏫 Add Teacher</a>
      <a href='/school/{code}/assessments' class='bg-orange-600 text-white p-5 rounded text-center'>📊 CBC Assessments</a>
    </div>
    <div class='mt-8 bg-white p-4 rounded shadow'><h3 class='font-bold'>CBC CLASSES TEMPLATE</h3><p class='text-xs'>System auto-created: {", ".join(CBC_CLASSES)}</p><p class='text-xs mt-2'>INSTRUCTIONS: 1. Add Learners with Admission No. 2. Assign Class 3. Add Assessments (Exceeding, Meeting, Approaching, Below)</p></div>
    <br><a href='/?school={code}' class='underline'>School Home</a></div>""")

# ADD LEARNER
@app.route('/school/<code>/learners/add', methods=['GET','POST'])
def add_learner(code):
    code=code.upper()
    if not session.get(f'school_{code}'): return redirect(f'/school/{code}/login')
    if request.method=='POST':
        con=get_db(); c=con.cursor()
        adm=request.form.get('admission'); name=request.form.get('fullname'); cl=request.form.get('class_name'); gender=request.form.get('gender'); phone=request.form.get('phone'); upi=request.form.get('upi')
        run(c,"INSERT INTO learners (school_code,admission_no,fullname,class_name,gender,parent_phone,upi) VALUES (%s,%s,%s,%s,%s,%s,%s)",(code,adm,name,cl,gender,phone,upi)); con.commit(); con.close()
        return redirect(f'/school/{code}/learners')
    opts="".join([f"<option>{x}</option>" for x in CBC_CLASSES])
    return render_template_string(STYLE+f"""
    <div class='max-w-lg mx-auto mt-8 bg-white p-6 rounded shadow font-sans'><h2 class='font-bold'>Add Learner - {code}</h2>
    <form method='POST' class='mt-4'>
      <input name='admission' placeholder='Admission No e.g. KIM001' class='w-full border p-2 mb-2' required>
      <input name='fullname' placeholder='Full Name' class='w-full border p-2 mb-2' required>
      <select name='class_name' class='w-full border p-2 mb-2' required>{opts}</select>
      <select name='gender' class='w-full border p-2 mb-2'><option>Male</option><option>Female</option></select>
      <input name='upi' placeholder='UPI (NEMIS)' class='w-full border p-2 mb-2'>
      <input name='phone' placeholder='Parent Phone' class='w-full border p-2 mb-2'>
      <button class='bg-green-600 text-white w-full p-3'>SAVE LEARNER</button>
    </form><br><a href='/school/{code}/dashboard' class='underline text-sm'>← Dashboard</a></div>""")

@app.route('/school/<code>/learners')
def view_learners(code):
    code=code.upper()
    if not session.get(f'school_{code}'): return redirect(f'/school/{code}/login')
    con=get_db(); c=con.cursor(); c.execute("SELECT * FROM learners WHERE school_code=%s ORDER BY class_name".replace('%s','?') if not DATABASE_URL else "SELECT * FROM learners WHERE school_code=%s ORDER BY class_name",(code,)); rows=c.fetchall(); con.close()
    tr="".join([f"<tr><td class='p-2 border'>{dict(r).get('admission_no')}</td><td class='p-2 border'>{dict(r).get('fullname')}</td><td class='p-2 border'>{dict(r).get('class_name')}</td><td class='p-2 border'>{dict(r).get('gender')}</td><td class='p-2 border'>{dict(r).get('upi')}</td></tr>" for r in rows])
    return render_template_string(STYLE+f"<div class='p-4 font-sans'><h2 class='font-bold'>{code} Learners - {len(rows)}</h2><table class='w-full mt-4 border text-sm'><tr class='bg-black text-white'><th class='p-2'>Adm No</th><th>Name</th><th>Class</th><th>Gender</th><th>UPI</th></tr>{tr or '<tr><td colspan=5 class=text-center p-4>No learners yet</td></tr>'}</table><br><a href='/school/{code}/dashboard' class='underline'>← Dashboard</a></div>")

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
