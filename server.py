import hashlib
import os
import secrets
import uuid
from contextlib import contextmanager

import psycopg
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException

import rules
import bot
import accounts

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MAX_CONTENT_LENGTH']=32768

@contextmanager
def database():
    with psycopg.connect(host=os.environ['PGHOST'], dbname=os.environ['PGDATABASE'],
                         user=os.environ['PGUSER'], password=os.environ['PGPASSWORD'],
                         connect_timeout=5, row_factory=dict_row) as connection:
        yield connection

def initialize():
    with database() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS matches (
            id UUID PRIMARY KEY, mode TEXT NOT NULL, state JSONB NOT NULL,
            revision INTEGER NOT NULL DEFAULT 0,
            invite TEXT, joined BOOLEAN NOT NULL DEFAULT FALSE,
            history JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now())''')
        accounts.schema(db)
        # Retire capabilities permanently; preserve historical match states.
        db.execute('ALTER TABLE matches DROP COLUMN IF EXISTS token0, DROP COLUMN IF EXISTS token1')
        db.execute('UPDATE matches SET invite=NULL WHERE NOT EXISTS (SELECT 1 FROM match_players p WHERE p.match_id=matches.id)')

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict):
        raise rules.InvalidMove('Expected a JSON object.')
    return value

def get_match(db, mid, lock=False):
    try: uuid.UUID(mid)
    except (ValueError,TypeError): raise HTTPExceptionWithCode(404,'Match not found.')
    row=db.execute('SELECT * FROM matches WHERE id=%s'+(' FOR UPDATE' if lock else ''),(mid,)).fetchone()
    if not row: raise HTTPExceptionWithCode(404,'Match not found.')
    if g.get('user'):
        owned=db.execute('SELECT side FROM match_players WHERE match_id=%s AND account_id=%s ORDER BY side',(mid,g.user['id'])).fetchall()
        wanted=request.headers.get('X-Player-Side')
        side=next((r['side'] for r in owned if wanted is None or str(r['side'])==wanted),None)
        if side is not None:return row,side
    raise HTTPExceptionWithCode(403 if g.get('user') else 401,'Log in with an account that owns this match.')

class HTTPExceptionWithCode(Exception):
    def __init__(self,code,message): self.code=code; self.message=message

@app.errorhandler(HTTPExceptionWithCode)
def custom_error(error): return jsonify(error=error.message),error.code

@app.errorhandler(rules.InvalidMove)
def invalid(error): return jsonify(error=str(error)),400

@app.errorhandler(psycopg.Error)
def db_error(error):
    app.logger.error('Database operation failed: %s',type(error).__name__)
    return jsonify(error='Database unavailable. Your last submitted turn remains saved; please retry.'),503

@app.errorhandler(HTTPException)
def http_error(error): return jsonify(error=error.description),error.code

@app.after_request
def headers(response):
    response.headers['Cache-Control']='no-store' if request.path.startswith('/api/') else 'no-cache'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    return response

@app.get('/')
def index(): return app.send_static_file('index.html')

@app.get('/api/health')
def health():
    with database() as db: db.execute('SELECT 1')
    return jsonify(app='online',database='connected')

@app.get('/api/rules')
def rulebook():
    return jsonify(version=rules.VERSION,units=rules.UNITS,items=rules.ITEMS,deck=rules.DECK,factions=rules.FACTIONS,tiles=rules.TILES)

@app.post('/api/matches')
def create_match():
    if not g.user:raise HTTPExceptionWithCode(401,'Log in to start a battle.')
    data=body(); mode=data.get('mode','practice')
    rules.require(mode in ('practice','hotseat','friend'),'Choose a supported game mode.')
    mid=str(uuid.uuid4()); invite=secrets.token_urlsafe(24)
    state=rules.new_game(secrets.randbits(64),practice=mode=='practice',factions=data.get('factions'))
    with database() as db:
        db.execute('INSERT INTO matches (id,mode,state,invite,joined) VALUES (%s,%s,%s,%s,%s)',
                   (mid,mode,Jsonb(state),digest(invite) if mode=='friend' else None,mode!='friend'))
        for side in ([0,1] if mode=='hotseat' else [0]):db.execute('INSERT INTO match_players VALUES (%s,%s,%s)',(mid,side,g.user['id']))
    result=dict(id=mid,mode=mode,account=True,side=0)
    if mode=='friend': result['invite']=invite
    return jsonify(result),201

@app.post('/api/matches/<mid>/join')
def join_match(mid):
    if not g.user:raise HTTPExceptionWithCode(401,'Log in to join a battle.')
    data=body(); invitation=data.get('invite','')
    rules.require(isinstance(invitation,str),'Invalid invitation.')
    try: uuid.UUID(mid)
    except ValueError: raise HTTPExceptionWithCode(404,'Match not found.')
    with database() as db:
        row=db.execute('SELECT * FROM matches WHERE id=%s FOR UPDATE',(mid,)).fetchone()
        if not row or not row['invite'] or not secrets.compare_digest(digest(invitation),row['invite']):
            raise HTTPExceptionWithCode(403,'This invitation is invalid or has already been claimed.')
        db.execute('UPDATE matches SET joined=TRUE,invite=NULL WHERE id=%s',(mid,))
        db.execute('INSERT INTO match_players VALUES (%s,1,%s)',(mid,g.user['id']))
    return jsonify(id=mid,mode='friend',account=True,side=1)

def envelope(row,side,state=None):
    return dict(id=str(row['id']),mode=row['mode'],revision=row['revision'],side=side,joined=row['joined'],
                state=rules.public_state(state or row['state'],side),
                history=[{**{k:v for k,v in h.items() if k not in ('before','frames')}, 'replay_available': bool(h.get('frames'))} for h in row['history'][-20:]])

@app.get('/api/matches/<mid>')
def read_match(mid):
    with database() as db:
        row,side=get_match(db,mid)
    return jsonify(envelope(row,side))

@app.post('/api/matches/<mid>/invite')
def renew_invite(mid):
    with database() as db:
        row,side=get_match(db,mid,True)
        rules.require(side==0 and row['mode']=='friend' and not row['joined'],'No pending invitation for this side.')
        invitation=secrets.token_urlsafe(24)
        db.execute('UPDATE matches SET invite=%s WHERE id=%s',(digest(invitation),mid))
    return jsonify(invite=invitation)

def replay(row,side,data):
    if type(data.get('revision')) is not int or data['revision']!=row['revision']:
        raise HTTPExceptionWithCode(409,'A newer turn is saved. Refresh the match before playing.')
    state=row['state']
    rules.require(state['winner'] is None,'This match is finished.')
    rules.require(state['player']==side,"It is your opponent's turn.")
    actions=data.get('actions',[])
    rules.require(isinstance(actions,list) and len(actions)<=5,'A turn has at most five actions.')
    events=[]
    frames=[rules.public_state(state,None)]
    for action in actions:
        state=rules.apply(state,action); events.extend(state['events'])
        frames.append(rules.public_state(state,None))
    return state,events,frames

@app.post('/api/matches/<mid>/preview')
def preview(mid):
    data=body()
    with database() as db: row,side=get_match(db,mid)
    state,events,frames=replay(row,side,data)
    result=envelope(row,side,state)
    selection=data.get('selection')
    if isinstance(selection,dict):
        unit=selection.get('unit'); card=selection.get('card')
        rules.require(unit is None or isinstance(unit,str),'Invalid unit selection.')
        rules.require(card is None or type(card) is int,'Invalid card selection.')
        result['legal']=rules.legal_actions(state,unit_id=unit,card=card)
    result['events']=events
    return jsonify(result)

@app.post('/api/matches/<mid>/submit')
def submit(mid):
    data=body()
    with database() as db:
        row,side=get_match(db,mid,True)
        rules.require(row['joined'],'Wait for your friend to join before submitting.')
        state,events,frames=replay(row,side,data)
        history=row['history']
        history.append(dict(turn=state['turn'],player=side,events=events,frames=frames,before=rules.public_state(row['state'],None)))
        state=rules.end_turn(state)
        if row['mode']=='practice' and state['winner'] is None:
            bot_start=state
            before=rules.public_state(state,None)
            state,actions,events=bot.play(state)
            frames=[before]
            for action in actions:
                bot_start=rules.apply(bot_start,action)
                frames.append(rules.public_state(bot_start,None))
            history.append(dict(turn=state['turn'],player=1,events=events,frames=frames,before=before))
            state=rules.end_turn(state)
        revision=row['revision']+1
        db.execute('UPDATE matches SET state=%s,history=%s,revision=%s,updated_at=now() WHERE id=%s',
                   (Jsonb(state),Jsonb(history),revision,mid))
        row.update(state=state,history=history,revision=revision)
    return jsonify(envelope(row,side))


@app.get('/api/matches/<mid>/replay/<int:turn>')
def replay_turn(mid,turn):
    with database() as db: row,side=get_match(db,mid)
    entry=next((h for h in row['history'] if h['turn']==turn),None)
    if not entry or not entry.get('frames'): raise HTTPExceptionWithCode(404,'No replay is available for this turn.')
    return jsonify(turn=turn,player=entry['player'],frames=entry['frames'])

@app.post('/api/matches/<mid>/resign')
def resign(mid):
    data=body()
    with database() as db:
        row,side=get_match(db,mid,True)
        if data.get('revision')!=row['revision']: raise HTTPExceptionWithCode(409,'Refresh before resigning.')
        rules.require(row['state']['winner'] is None,'This match is already finished.')
        row['state']['winner']=1-side; row['revision']+=1
        db.execute('UPDATE matches SET state=%s,revision=%s,updated_at=now() WHERE id=%s',(Jsonb(row['state']),row['revision'],mid))
    return jsonify(envelope(row,side))

accounts.install(app,database,HTTPExceptionWithCode)

if __name__=='__main__': initialize()
