"""Database-backed accounts and revocable, HttpOnly browser sessions."""
import re
import secrets
import hashlib
import os
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

bp=Blueprint('accounts',__name__)
COOKIE='academy_session'
DUMMY=generate_password_hash('unusable-random-placeholder',method='pbkdf2:sha256:600000')

def hashed(value):return hashlib.sha256(value.encode()).hexdigest()

def schema(db):
 db.execute('''CREATE TABLE IF NOT EXISTS accounts (
 id UUID PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now())''')
 db.execute('ALTER TABLE accounts ADD COLUMN IF NOT EXISTS email TEXT')
 db.execute('CREATE UNIQUE INDEX IF NOT EXISTS accounts_email_unique ON accounts(lower(email))')
 db.execute('''CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 expires_at TIMESTAMPTZ NOT NULL)''')
 db.execute('''CREATE TABLE IF NOT EXISTS match_players (
 match_id UUID REFERENCES matches(id) ON DELETE CASCADE, side INTEGER CHECK(side IN (0,1)),
 account_id UUID REFERENCES accounts(id) ON DELETE CASCADE, PRIMARY KEY(match_id,side))''')
 db.execute('''CREATE TABLE IF NOT EXISTS auth_limits (
 key TEXT PRIMARY KEY, attempts INTEGER NOT NULL, reset_at TIMESTAMPTZ NOT NULL)''')

def install(app,database,error):
 import uuid
 def user_required():
  if not g.user:raise error(401,'Log in to continue.')
  return g.user
 def throttle(name):
  keys=['ip:'+(request.remote_addr or 'unknown'),'name:'+name]
  with database() as db:
   counts=[]
   for key in keys:
    row=db.execute('''INSERT INTO auth_limits VALUES (%s,1,now()+interval '15 minutes')
     ON CONFLICT(key) DO UPDATE SET attempts=CASE WHEN auth_limits.reset_at<now() THEN 1 ELSE auth_limits.attempts+1 END,
     reset_at=CASE WHEN auth_limits.reset_at<now() THEN now()+interval '15 minutes' ELSE auth_limits.reset_at END
     RETURNING attempts''',(hashed(key),)).fetchone()
    counts.append(row['attempts'])
  if counts[0]>50 or counts[1]>10:raise error(429,'Too many attempts. Try again in 15 minutes.')
 def issue(user):
  token=secrets.token_urlsafe(32)
  with database() as db:
   db.execute('DELETE FROM sessions WHERE expires_at<now() OR token_hash=%s',(hashed(request.cookies.get(COOKIE,'')),))
   db.execute("INSERT INTO sessions VALUES (%s,%s,now()+interval '7 days')",(hashed(token),user['id']))
  response=jsonify(user=dict(id=str(user['id']),username=user['username'],email=user['email']),csrf=hashed('csrf:'+token))
  response.set_cookie(COOKIE,token,httponly=True,samesite='Strict',secure=os.getenv('COOKIE_SECURE','0')=='1',max_age=604800,path='/')
  return response
 @app.before_request
 def authenticate():
  g.user=None
  if not request.path.startswith('/api/'):return
  token=request.cookies.get(COOKIE,'')
  if token:
   with database() as db:
    g.user=db.execute('''SELECT a.id,a.username,a.email FROM sessions s JOIN accounts a ON a.id=s.account_id
     WHERE s.token_hash=%s AND s.expires_at>now()''',(hashed(token),)).fetchone()
  if request.method in ('POST','PUT','PATCH','DELETE'):
   origin=request.headers.get('Origin')
   if origin and origin!=request.host_url.rstrip('/'):raise error(403,'Cross-origin requests are not allowed.')
   if request.headers.get('Sec-Fetch-Site')=='cross-site':raise error(403,'Cross-site requests are not allowed.')
   if g.user and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),hashed('csrf:'+token)):
    raise error(403,'Session verification failed. Reload the page.')
 @bp.get('/session')
 def session():
  return jsonify(user=dict(id=str(g.user['id']),username=g.user['username'],email=g.user['email']) if g.user else None,
                 csrf=hashed('csrf:'+request.cookies[COOKIE]) if g.user else None)
 def credentials():
  if request.headers.get('X-Requested-With')!='CrystalTactics':raise error(403,'Use the account form to sign in.')
  data=request.get_json(silent=True) or {}
  if not isinstance(data,dict):raise error(400,'Expected account details.')
  name=data.get('username','');password=data.get('password','')
  if not isinstance(name,str) or not isinstance(password,str):raise error(400,'Enter a username and password.')
  name=name.strip().lower()
  if request.path.endswith('/register') and not re.fullmatch('[a-z0-9_]{3,24}',name):raise error(400,'Username: 3–24 letters, numbers or underscores.')
  if not 12<=len(password)<=128:raise error(400,'Use a password with 12–128 characters.')
  if not 3<=len(name)<=254:raise error(400,'Enter your username or email.')
  throttle(name)
  return name,password
 @bp.post('/register')
 def register():
  name,password=credentials()
  email=request.get_json().get('email','')
  if not isinstance(email,str):raise error(400,'Enter a valid email address.')
  email=email.strip().lower()
  if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise error(400,'Enter a valid email address.')
  password_hash=generate_password_hash(password,method='pbkdf2:sha256:600000')
  with database() as db:
   user=db.execute('INSERT INTO accounts(id,username,email,password_hash) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id,username,email',
                   (str(uuid.uuid4()),name,email,password_hash)).fetchone()
  if not user:raise error(409,'That username or email is unavailable.')
  return issue(user),201
 @bp.post('/login')
 def login():
  name,password=credentials()
  with database() as db:user=db.execute('SELECT * FROM accounts WHERE username=%s OR email=%s',(name,name)).fetchone()
  valid=check_password_hash(user['password_hash'] if user else DUMMY,password)
  if not user or not valid:raise error(401,'Incorrect username/email or password.')
  return issue(user)
 @bp.post('/logout')
 def logout():
  with database() as db:db.execute('DELETE FROM sessions WHERE token_hash=%s',(hashed(request.cookies.get(COOKIE,'')),))
  response=jsonify(ok=True);response.delete_cookie(COOKIE,path='/');return response
 @bp.get('/matches')
 def matches():
  user=user_required()
  with database() as db:
   rows=db.execute('''SELECT m.id,m.mode,m.state,m.created_at,p.side FROM match_players p JOIN matches m ON m.id=p.match_id
    WHERE p.account_id=%s ORDER BY m.updated_at DESC,p.side''',(user['id'],)).fetchall()
  return jsonify(matches=[dict(id=str(r['id']),mode=r['mode'],side=r['side'],account=True,
   factions=r['state'].get('factions',['council','council']),created=r['created_at'].isoformat(),
   result='Turn '+str(r['state']['turn']) if r['state']['winner'] is None else 'Battle complete') for r in rows])
 app.register_blueprint(bp,url_prefix='/api/account')
