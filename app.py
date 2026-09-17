from flask import Flask, render_template, request, redirect, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = "final2026"
os.makedirs('static/logos', exist_ok=True)

def init_db():
    con=sqlite3.connect('cbc.db')
    c=con.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)')
    c.execute("INSERT OR IGNORE INTO schools (id,name,code,admin_user,admin_pass) VALUES (1,'SUPER','SUPER','superadmin','super123')")
    con.commit(); con.close()
init_db()

@app.route('/')
def home():
    return "<h1>CBC SYSTEM WORKING</h1><p><a href='/superadmin'>/superadmin</a> | <a href='/admin'>/admin</a> | <a href='/teacher'>/teacher</a> | <a href='/parent'>/parent</a></p>"

@app.route('/superadmin')
def superadmin():
    return render_template('superadmin_login.html')

@app.route('/superadmin/dashboard')
def super_dash():
    return "<h1>SUPER ADMIN DASHBOARD - SEE ALL PASSWORDS</h1><p>Working!</p><a href='/'>Home</a>"

@app.route('/admin')
def admin():
    return render_template('admin_dashboard.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher_dashboard.html')

@app.route('/parent')
def parent():
    return render_template('parent_login.html')

@app.route('/report')
def report():
    return render_template('report_card.html')

if __name__=='__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)