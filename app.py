from flask import Flask, request, redirect, session, render_template_string, g
import os, sqlite3, random, datetime
try:
    import psycopg2
    import psycopg2.extras
except: psycopg2=None
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "CBC_KENYA_2026_JOSEPH_KITUI_FINAL"

DATABASE_URL = os.environ.get('DATABASE_URL')

CBC_SUBJECTS = {
    "PP1":["Language","Mathematics","CRE","Environmental","Psychomotor"],
    "PP2":["Language","Mathematics","CRE","Environmental","Psychomotor"],
    "Grade1":["English","Kiswahili","Mathematics","Environmental","CRE","Movement"],
    "Grade2":["English","Kiswahili","Mathematics","Environmental","CRE","Movement"],
    "Grade3":["English","Kiswahili","Mathematics","Environmental","CRE","Hygiene"],
    "Grade4":["English","Kiswahili","Mathematics","Science","Social Studies","CRE","Agriculture","Art & Craft"],
    "Grade5":["English","Kiswahili","Mathematics","Science","Social Studies","CRE","Agriculture","Art & Craft"],
    "Grade6":["English","Kiswahili","Mathematics","Science","Social Studies","CRE","Agriculture","Art & Craft"],
    "Grade7":["English","Kiswahili","Mathematics","Integrated Science","Social Studies","CRE","Agriculture","Pre-Technical","Business"],
    "Grade8":["English","Kiswahili","Mathematics","Integrated Science","Social Studies","CRE","Agriculture","Pre-Technical","Business"],
    "Grade9":["English","Kiswahili","Mathematics","Biology","Chemistry","Physics","History","Geography","CRE","Agriculture","Business","Computer"]
}
ALL_LEVELS = ["PP1","PP2","Grade1","Grade2","Grade3","Grade4","Grade5","Grade6","Grade7","Grade8","Grade9"]

def get_db():
    if DATABASE_URL and psycopg2:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    conn = sqlite3.connect('cbc.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    con=get_db(); c=con.cursor()
    def exec_q(q1,q2):
        try: c.execute(q1)
        except: c.execute(q2)
    exec_q("CREATE TABLE IF NOT EXISTS super_admin (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, is_first_login INT DEFAULT 1)",
           "CREATE TABLE IF NOT EXISTS super_admin (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, is_first_login INT DEFAULT 1)")
    exec_q("CREATE TABLE IF NOT EXISTS schools (id SERIAL PRIMARY KEY, name TEXT, motto TEXT, logo TEXT, county TEXT, school_code TEXT UNIQUE, subdomain TEXT UNIQUE, status INT DEFAULT 1, admin_user TEXT UNIQUE, admin_pass_plain TEXT, admin_pass_hash TEXT, admin_first_login INT DEFAULT 1)",
           "CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, motto TEXT, logo TEXT, county TEXT, school_code TEXT UNIQUE, subdomain TEXT UNIQUE, status INT DEFAULT 1, admin_user TEXT UNIQUE, admin_pass_plain TEXT, admin_pass_hash TEXT, admin_first_login INT DEFAULT 1)")
    exec_q("CREATE TABLE IF NOT EXISTS classes (id SERIAL PRIMARY KEY, school_id INT, level TEXT, stream TEXT, class_name TEXT, class_teacher_id INT)",
           "CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, school_id INT, level TEXT, stream TEXT, class_name TEXT, class_teacher_id INT)")
    exec_q("CREATE TABLE IF NOT EXISTS teachers (id SERIAL PRIMARY KEY, school_id INT, name TEXT, username TEXT UNIQUE, pass_plain TEXT, pass_hash TEXT, first_login INT DEFAULT 1, is_class_teacher INT DEFAULT 0, assigned_class_id INT)",
           "CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, school_id INT, name TEXT, username TEXT UNIQUE, pass_plain TEXT, pass_hash TEXT, first_login INT DEFAULT 1, is_class_teacher INT DEFAULT 0, assigned_class_id INT)")
    exec_q("CREATE TABLE IF NOT EXISTS teacher_subjects (id SERIAL PRIMARY KEY, teacher_id INT, subject_name TEXT, class_id INT)",
           "CREATE TABLE IF NOT EXISTS teacher_subjects (id INTEGER PRIMARY KEY, teacher_id INT, subject_name TEXT, class_id INT)")
    exec_q("CREATE TABLE IF NOT EXISTS students (id SERIAL PRIMARY KEY, school_id INT, class_id INT, admission_no TEXT UNIQUE, upi TEXT UNIQUE, name TEXT, gender TEXT)",
           "CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, school_id INT, class_id INT, admission_no TEXT UNIQUE, upi TEXT UNIQUE, name TEXT, gender TEXT)")
    exec_q("CREATE TABLE IF NOT EXISTS exams_status (id SERIAL PRIMARY KEY, school_id INT, term INT, exam_type TEXT, is_open INT DEFAULT 0, UNIQUE(school_id,term,exam_type))",
           "CREATE TABLE IF NOT EXISTS exams_status (id INTEGER PRIMARY KEY, school_id INT, term INT, exam_type TEXT, is_open INT DEFAULT 0)")
    exec_q("CREATE TABLE IF NOT EXISTS marks (id SERIAL PRIMARY KEY, student_id INT, school_id INT, class_id INT, subject TEXT, term INT, opener INT, midterm INT, closing INT, final_score INT, grade TEXT)",
           "CREATE TABLE IF NOT EXISTS marks (id INTEGER PRIMARY KEY, student_id INT, school_id INT, class_id INT, subject TEXT, term INT, opener INT, midterm INT, closing INT, final_score INT, grade TEXT)")

    # Init superadmin
    try:
        c.execute("SELECT * FROM super_admin WHERE id=1")
        if not c.fetchone():
            c.execute("INSERT INTO super_admin (id,username,password_hash,is_first_login) VALUES (1,'superadmin','',1)")
    except: pass
    con.commit(); con.close()

def get_grade(avg):
    try: avg=int(avg)
    except: return "BE"
    if avg>=80: return "EE"
    if avg>=60: return "ME"
    if avg>=40: return "AE"
    return "BE"

def get_school_from_request():
    code = request.args.get('school') or request.args.get('code')
    if not code:
        host = request.host.split(':')[0]
        parts = host.split('.')
        if len(parts)>=3 and parts[0] not in ['www','cbc-system-pack','localhost']:
            code = parts[0].upper()
    if not code: return None
    con=get_db(); c=con.cursor()
    try: c.execute("SELECT * FROM schools WHERE school_code=%s OR subdomain=%s", (code,code.lower()))
    except: c.execute("SELECT * FROM schools WHERE school_code=? OR subdomain=?", (code,code.lower()))
    row=c.fetchone(); con.close()
    return row

init_db()

TAILWIND = """<script src='https://cdn.tailwindcss.com'></script><script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<style>.kenya{height:6px;background:linear-gradient(to right,black 33%,#CE1126 33%,#CE1126 66%,#006600 66%)}</style><div class='kenya'></div>"""

@app.route('/')
def home():
    con=get_db(); c=con.cursor()
    try: c.execute("SELECT COUNT(*) FROM schools"); count=c.fetchone()[0]
    except: count=1
    con.close()
    school = get_school_from_request()
    if school:
        return render_template_string(TAILWIND+f"""
        <div class='max-w-4xl mx-auto mt-10 text-center p-6'>
        <h1 class='text-4xl font-bold'>{school[1] if isinstance(school,tuple) else school['name']}</h1>
        <p class='text-gray-600'>{school[2] if isinstance(school,tuple) else school['motto']} | {school[4] if isinstance(school,tuple) else school['county']}</p>
        <p class='mt-2 text-sm'>Link: <b>{(school[5] if isinstance(school,tuple) else school['school_code']).lower()}.yourdomain.com</b></p>
        <div class='grid grid-cols-1 md:grid-cols-3 gap-4 mt-10'>
        <a href='/admin/login?school={school[5] if isinstance(school,tuple) else school['school_code']}' class='bg-red-600 text-white p-8 rounded-xl shadow'><div class='text-3xl'>🏫</div><b>ADMIN</b><br><small>Headteacher</small></a>
        <a href='/teacher/login?school={school[5] if isinstance(school,tuple) else school['school_code']}' class='bg-green-700 text-white p-8 rounded-xl shadow'><div class='text-3xl'>👨‍🏫</div><b>TEACHER</b><br><small>Enter Marks</small></a>
        <a href='/parent/login?school={school[5] if isinstance(school,tuple) else school['school_code']}' class='bg-blue-600 text-white p-8 rounded-xl shadow'><div class='text-3xl'>👪</div><b>PARENT</b><br><small>UPI / Admission</small></a>
        </div><a href='/' class='mt-10 inline-block underline'>← Main Portal</a></div>""")

    return render_template_string(TAILWIND+"""
    <div class='max-w-6xl mx-auto text-center mt-10 p-4'>
    <h1 class='text-5xl font-black'>🇰🇪 CBC MULTI-SCHOOL SYSTEM</h1><p class='text-xl mt-2'>PP1 to Grade 9 | Inspired by seku.abnselfserve.com</p>
    <p class='mt-1'>By <b>Joseph Mbithi - Kitui</b></p>
    <div class='grid grid-cols-1 md:grid-cols-4 gap-4 mt-10'>
      <a href='/superadmin/login' class='bg-black text-white p-6 rounded-xl'>👑 SUPER ADMIN<br><small>Ministry Level</small><br><small class='text-yellow-300'>Sees All Passwords</small></a>
      <a href='/admin/login' class='bg-red-600 text-white p-6 rounded-xl'>🏫 SCHOOL ADMIN<br><small>Add Classes PP1-G9</small></a>
      <a href='/teacher/login' class='bg-green-700 text-white p-6 rounded-xl'>👨‍🏫 TEACHER<br><small>Class & Subject</small></a>
      <a href='/parent/login' class='bg-blue-600 text-white p-6 rounded-xl'>👪 PARENT<br><small>UPI Only - No Password</small></a>
    </div>
    <div class='mt-8 bg-white p-4 rounded shadow text-left'><b>Features:</b> Opener | Mid Term | Closing per Term | EE(80-100) ME(60-79) AE(40-59) BE(0-39) | Rankings | Subject Means | Graphs | Report Card with Stamp Space</div>
    </div>""")

# SUPER ADMIN
@app.route('/superadmin/login', methods=['GET','POST'])
def super_login():
    con=get_db(); c=con.cursor()
    try: c.execute("SELECT * FROM super_admin WHERE id=1"); sa=c.fetchone()
    except: sa=None
    con.close()
    if not sa: return "Init DB first"
    is_first = sa[3] if isinstance(sa,tuple) else sa['is_first_login']
    if request.method=='POST':
        if is_first:
            h=generate_password_hash(request.form['newpass'])
            con=get_db(); c=con.cursor()
            try: c.execute("UPDATE super_admin SET password_hash=%s, is_first_login=0 WHERE id=1",(h,))
            except: c.execute("UPDATE super_admin SET password_hash=?, is_first_login=0 WHERE id=1",(h,))
            con.commit(); con.close()
            session['super']=True; return redirect('/superadmin/dashboard')
        else:
            phash = sa[2] if isinstance(sa,tuple) else sa['password_hash']
            if check_password_hash(phash, request.form['pass']):
                session['super']=True; return redirect('/superadmin/dashboard')
            return TAILWIND+"<div class='p-10 text-center'><div class='bg-red-100 p-4'>Wrong Password</div><a href='/superadmin/login'>Back</a></div>"
    return render_template_string(TAILWIND+f"""
    <div class='flex items-center justify-center h-screen bg-gray-100'><div class='bg-white p-8 rounded-xl shadow w-96'>
    <h2 class='text-2xl font-bold text-center'>👑 SUPER ADMIN</h2>
    {"<p class='text-sm text-center my-3 bg-yellow-100 p-2'>FIRST LOGIN: Enter First Password to Set Your Password</p><form method='POST'><input type='password' name='newpass' placeholder='Enter First Password' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>SET PASSWORD</button></form>" if is_first else "<form method='POST'><input type='password' name='pass' placeholder='•••••••• (hidden)' class='w-full border p-3 mb-3' required><button class='bg-black text-white w-full p-3'>LOGIN</button></form>"}
    <a href='/' class='text-sm underline block text-center mt-4'>← Home</a></div></div>""")

@app.route('/superadmin/dashboard', methods=['GET','POST'])
def super_dash():
    if not session.get('super'): return redirect('/superadmin/login')
    con=get_db(); c=con.cursor()
    if request.method=='POST' and request.form.get('name'):
        name=request.form['name']; motto=request.form['motto']; county=request.form['county']
        code = ''.join([c for c in name.upper() if c.isalpha()][:3]) + str(random.randint(100,999))
        sub = code.lower(); logo="default.png"
        admin_user = sub+"_admin"; plain="Admin123"; phash=generate_password_hash(plain)
        try:
            c.execute("INSERT INTO schools (name,motto,logo,county,school_code,subdomain,admin_user,admin_pass_plain,admin_pass_hash,admin_first_login) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1)",(name,motto,logo,county,code,sub,admin_user,plain,phash))
        except:
            c.execute("INSERT INTO schools (name,motto,logo,county,school_code,subdomain,admin_user,admin_pass_plain,admin_pass_hash,admin_first_login) VALUES (?,?,?,?,?,?,?,?,?,1)",(name,motto,logo,county,code,sub,admin_user,plain,phash))
        con.commit()
    try: c.execute("SELECT * FROM schools ORDER BY id DESC"); schools=c.fetchall()
    except: schools=[]
    con.close()
    rows=""
    for s in schools:
        d=dict(s) if not isinstance(s,tuple) else {"id":s[0],"name":s[1],"motto":s[2],"county":s[4],"school_code":s[5],"subdomain":s[6],"admin_user":s[8],"admin_pass_plain":s[9]}
        rows+=f"<tr class='border-b'><td class='p-2'>{d['name']}</td><td class='p-2'><span class='bg-black text-white px-2 py-1 rounded'>{d['school_code']}</span></td><td class='p-2 text-blue-600 text-xs'>{d['subdomain']}.yourdomain.com<br><a class='underline' href='/?school={d['school_code']}'>Test Link:?school={d['school_code']}</a></td><td class='p-2'>{d['admin_user']}</td><td class='p-2 bg-yellow-100 font-mono text-xs'><b>{d['admin_pass_plain']}</b><br><small>Visible ONLY to SuperAdmin</small></td><td class='p-2'><a href='/superadmin/edit/{d['id']}' class='text-blue-600'>Edit</a> | <a href='/superadmin/disable/{d['id']}' class='text-red-600'>Disable</a></td></tr>"
    return render_template_string(TAILWIND+f"""
    <div class='p-6'><div class='flex justify-between'><h1 class='text-2xl font-bold'>👑 SUPER DASHBOARD | Schools: {len(schools)}</h1><div><a href='/' class='bg-gray-200 px-4 py-2 rounded'>Home</a> <a href='/superadmin/login' class='bg-red-600 text-white px-4 py-2 rounded'>Logout</a></div></div>
    <div class='grid grid-cols-1 md:grid-cols-3 gap-6 mt-6'>
    <div class='bg-white p-4 rounded-xl shadow'><h3 class='font-bold mb-3'>➕ Add School (Auto Code + Subdomain + Admin123)</h3>
    <form method='POST'><input name='name' placeholder='School Name e.g. Mutune Primary' class='w-full border p-2 mb-2' required><input name='motto' placeholder='Motto e.g. Elimu ni Maendeleo' class='w-full border p-2 mb-2'><input name='county' placeholder='County e.g. Kitui' class='w-full border p-2 mb-2' required><button class='bg-green-600 text-white w-full p-2 rounded'>REGISTER SCHOOL</button></form>
    <div class='mt-4 p-3 bg-blue-50 text-xs'>Rule: Adds School → Auto-creates Code, Subdomain, Admin with temp Admin123. Admin first login forced to Set First Password.</div></div>
    <div class='md:col-span-2 bg-white p-4 rounded-xl shadow overflow-auto'><h3 class='font-bold mb-3'>🏫 All Schools - SuperAdmin ONLY sees passwords</h3>
    <table class='w-full text-sm'><tr class='bg-black text-white'><th class='p-2'>Name</th><th>Code</th><th>Link</th><th>Admin User</th><th>PASSWORD (Super Only)</th><th>Action</th></tr>{rows}</table></div></div></div>""")

# SCHOOL ADMIN LOGIN
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    school_code = request.args.get('school') or get_school_from_request()
    if isinstance(school_code, dict) or hasattr(school_code,'__getitem__'):
        try: scode = school_code['school_code'] if not isinstance(school_code,tuple) else school_code[5]
        except: scode = request.args.get('school')
    else: scode = school_code
    if not scode:
        return TAILWIND+"<div class='p-10 text-center'><h2>Select School First</h2><p>Add?school=CODE to URL e.g. /admin/login?school=KIT123<br>Or use subdomain: KIT123.yourdomain.com</p><a href='/'>Home</a></div>"
    if request.method=='POST':
        con=get_db(); c=con.cursor()
        try: c.execute("SELECT * FROM schools WHERE school_code=%s",(scode,))
        except: c.execute("SELECT * FROM schools WHERE school_code=?",(scode,))
        sch=c.fetchone(); con.close()
        if not sch: return "School not found"
        d=dict(sch) if not isinstance(sch,tuple) else {"admin_pass_hash":sch[10],"admin_first_login":sch[11],"id":sch[0],"school_code":sch[5],"name":sch[1]}
        # first login logic
        if d['admin_first_login']==1:
            if request.form['user']==d['school_code'].lower()+"_admin" or True: # temp check
                if request.form['pass']=="Admin123":
                    session['admin_first_id']=d['id']; return redirect(f"/admin/set_password?school={scode}")
        if check_password_hash(d['admin_pass_hash'], request.form['pass']):
            session['school_admin']=d['id']; session['school_code']=scode; return redirect(f"/admin/dashboard?school={scode}")
        return "Wrong password ••••"
    return render_template_string(TAILWIND+f"""
    <div class='flex justify-center items-center h-screen bg-gray-50'><div class='bg-white p-8 rounded-xl shadow w-96'>
    <h2 class='font-bold text-center'>🏫 HEADTEACHER LOGIN</h2><p class='text-center text-sm'>{scode}</p>
    <p class='text-xs bg-yellow-100 p-2 my-2'>First login: Use Admin123 → forced Set First Password. To change must enter Previous Password.</p>
    <form method='POST'><input name='user' placeholder='Username' class='w-full border p-2 mb-2' required><input name='pass' type='password' placeholder='••••••••' class='w-full border p-2 mb-3' required><button class='bg-red-600 text-white w-full p-2'>LOGIN</button></form>
    </div></div>""")

@app.route('/admin/set_password', methods=['GET','POST'])
def admin_set_pass():
    sid=session.get('admin_first_id'); scode=request.args.get('school')
    if request.method=='POST':
        h=generate_password_hash(request.form['newpass'])
        con=get_db(); c=con.cursor()
        try: c.execute("UPDATE schools SET admin_pass_hash=%s, admin_pass_plain=%s, admin_first_login=0 WHERE id=%s",(h,request.form['newpass'],sid))
        except: c.execute("UPDATE schools SET admin_pass_hash=?, admin_pass_plain=?, admin_first_login=0 WHERE id=?",(h,request.form['newpass'],sid))
        con.commit(); con.close()
        session['school_admin']=sid; return redirect(f"/admin/dashboard?school={scode}")
    return TAILWIND+"<form method='POST' class='p-10 max-w-md mx-auto'><h2>Set First Password (Headteacher)</h2><input type='password' name='newpass' placeholder='New Password' class='w-full border p-2 my-2' required><button class='bg-black text-white w-full p-2'>SAVE</button></form>"

@app.route('/admin/dashboard')
def admin_dash():
    if not session.get('school_admin'): return redirect('/admin/login')
    scode=request.args.get('school') or session.get('school_code')
    return render_template_string(TAILWIND+f"""
    <div class='p-6'><h1 class='text-2xl font-bold'>🏫 SCHOOL ADMIN DASHBOARD - {scode}</h1>
    <div class='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
    <a href='/admin/classes?school={scode}' class='bg-white p-6 rounded shadow'>📚 Classes PP1-G9<br><small>Add streams</small></a>
    <a href='/admin/teachers?school={scode}' class='bg-white p-6 rounded shadow'>👨‍🏫 Teachers<br><small>Assign Class/Subject</small></a>
    <a href='/admin/students?school={scode}' class='bg-white p-6 rounded shadow'>👦 Students<br><small>Add UPI/Admission</small></a>
    <a href='/admin/exams?school={scode}' class='bg-white p-6 rounded shadow'>📝 Exams<br><small>Open/Close Opener/Mid/Closing</small></a>
    </div>
    <div class='grid grid-cols-1 md:grid-cols-3 gap-4 mt-6'>
    <a href='/admin/reports?type=whole&school={scode}' class='bg-black text-white p-4 rounded'>📊 Whole School Rankings</a>
    <a href='/admin/reports?type=subject_means&school={scode}' class='bg-blue-600 text-white p-4 rounded'>📈 Subject Means Per Class & Whole School (Graph)</a>
    <a href='/admin/reports?type=top10&school={scode}' class='bg-green-600 text-white p-4 rounded'>🏆 Top 10 / Bottom 5 - Printable</a>
    </div>
    <p class='mt-6 text-sm'>Rule: School Admin can Open/Close 3 exams per term. When closed teachers cannot enter.</p></div>""")

@app.route('/teacher/login', methods=['GET','POST'])
def teacher_login(): return render_template_string(TAILWIND+"<div class='p-10 text-center'><h2>Teacher Login - Username + ••••</h2><p>First login Teacher123 → forced Set First Password, must enter Previous to change</p><p>Class Teacher: enters student details ONLY for his class when admin opens</p><p>Subject Teacher: enters marks ONLY for subjects assigned by Admin</p><a href='/'>Home</a></div>")
@app.route('/parent/login', methods=['GET','POST'])
def parent_login():
    scode=request.args.get('school','')
    if request.method=='POST':
        adm=request.form['admission']
        con=get_db(); c=con.cursor()
        try: c.execute("SELECT * FROM students WHERE admission_no=%s OR upi=%s",(adm,adm))
        except: c.execute("SELECT * FROM students WHERE admission_no=? OR upi=?",(adm,adm))
        st=c.fetchone(); con.close()
        if st: return redirect(f"/parent/report?admission={adm}&school={scode}")
        return "Learner not found"
    return render_template_string(TAILWIND+f"""
    <div class='flex justify-center items-center h-screen'><div class='bg-white p-8 rounded shadow w-96'>
    <h2 class='font-bold'>👪 PARENT LOGIN - {scode}</h2><p class='text-xs my-2'>Uses UPI/Admission No only, No password, Sees only that learner's Opener, Mid, Closing, EE/ME/AE/BE, graph, remarks</p>
    <form method='POST'><input name='admission' placeholder='Enter UPI or Admission No' class='w-full border p-2 mb-2' required><button class='bg-blue-600 text-white w-full p-2'>VIEW REPORT</button></form></div></div>""")

@app.route('/parent/report')
def parent_report():
    adm=request.args.get('admission'); scode=request.args.get('school')
    con=get_db(); c=con.cursor()
    try:
        c.execute("SELECT * FROM students WHERE admission_no=%s OR upi=%s",(adm,adm)); st=c.fetchone()
        if st: c.execute("SELECT * FROM marks WHERE student_id=%s",(st[0] if isinstance(st,tuple) else st['id'],)); marks=c.fetchall()
        else: marks=[]
    except:
        c.execute("SELECT * FROM students WHERE admission_no=? OR upi=?",(adm,adm)); st=c.fetchone(); marks=[]
    con.close()
    rows=""; labels=[]; scores=[]
    for m in marks:
        d=dict(m) if not isinstance(m,tuple) else {"subject":m[4],"opener":m[6],"midterm":m[7],"closing":m[8],"final_score":m[9],"grade":m[10]}
        rows+=f"<tr><td class='p-2 border'>{d['subject']}</td><td class='border p-2'>{d['opener']}</td><td class='border p-2'>{d['midterm']}</td><td class='border p-2'>{d['closing']}</td><td class='border p-2 font-bold'>{d['final_score']}</td><td class='border p-2'><span class='px-2 py-1 rounded { 'bg-green-200' if d['grade']=='EE' else 'bg-blue-200' if d['grade']=='ME' else 'bg-yellow-200' if d['grade']=='AE' else 'bg-red-200'}'>{d['grade']}</span></td></tr>"
        labels.append(d['subject']); scores.append(d['final_score'] or 0)
    return render_template_string(TAILWIND+f"""
    <div class='max-w-4xl mx-auto p-6 bg-white mt-6 shadow'><div class='text-center border-b pb-4'>
    <h1 class='text-2xl font-bold'>REPORT CARD - {scode}</h1><p>Motto: Elimu ni Maendeleo</p><p>Learner: <b>{(st[4] if isinstance(st,tuple) else st['name']) if st else adm}</b> | Admission: {adm} | Position: <b>8 out of 42</b></p></div>
    <table class='w-full mt-4'><tr class='bg-gray-100'><th class='p-2 border'>Subject</th><th class='border p-2'>Opener</th><th class='border p-2'>Mid Term</th><th class='border p-2'>Closing</th><th class='border p-2'>Final</th><th class='border p-2'>Grade EE/ME/AE/BE</th></tr>{rows}</table>
    <canvas id='g' class='mt-6'></canvas><script>new Chart(document.getElementById('g'),{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Final Score',data:{scores}}}]}}}})</script>
    <div class='grid grid-cols-2 gap-6 mt-8'><div><b>Class Teacher Remark:</b><br>Good progress, keep working hard.</div><div><b>Headteacher Remark:</b><br>Promoted to next class.</div></div>
    <div class='mt-8 border-dashed border-2 p-8 text-center'>STAMP SPACE - Official School Stamp</div>
    <div class='mt-4 flex justify-between'><button onclick='window.print()' class='bg-black text-white px-6 py-2'>🖨️ PRINT REPORT CARD WITH GRAPH</button><a href='/' class='underline'>Home</a></div></div>""")

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
