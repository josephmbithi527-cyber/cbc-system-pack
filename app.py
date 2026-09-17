from flask import Flask, render_template, request, redirect, session
import os
try:
    import psycopg2
except:
    psycopg2 = None
import sqlite3

app = Flask(__name__)
app.secret_key = "final2026"
os.makedirs('static/logos', exist_ok=True)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL and psycopg2:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect('cbc.db')
        return conn

def init_db():
    con = get_db()
    c = con.cursor()
    # Works for both SQLite and Postgres
    try:
        c.execute('CREATE TABLE IF NOT EXISTS schools (id SERIAL PRIMARY KEY, name TEXT, code TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)')
    except:
        c.execute('CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, admin_user TEXT, admin_pass TEXT)')
    
    try:
        c.execute("INSERT INTO schools (id,name,code,admin_user,admin_pass) VALUES (1,'SUPER','SUPER','superadmin','admin123') ON CONFLICT (id) DO NOTHING")
    except:
        c.execute("INSERT OR IGNORE INTO schools (id,name,code,admin_user,admin_pass) VALUES (1,'SUPER','SUPER','superadmin','admin123')")
    con.commit(); con.close()

init_db()
