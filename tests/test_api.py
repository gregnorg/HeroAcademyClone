import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
import server

class APITests(unittest.TestCase):
    def setUp(self):
        self.client=server.app.test_client()
        self.ids=[]
        self.name='test_'+uuid.uuid4().hex[:16]
        r=self.client.post('/api/account/register',json=dict(username=self.name,email=self.name+'@example.test',password='test password long'),headers={'X-Requested-With':'CrystalTactics'},environ_overrides={'REMOTE_ADDR':self.name})
        self.assertEqual(r.status_code,201,r.get_json())
        self.csrf=r.get_json()['csrf'];self.uid=r.get_json()['user']['id']
        self.client.environ_base['HTTP_X_CSRF_TOKEN']=self.csrf
    def tearDown(self):
        with server.database() as db:
            for mid in self.ids: db.execute('DELETE FROM matches WHERE id=%s',(mid,))
            db.execute('DELETE FROM accounts WHERE id=%s',(self.uid,))
            db.execute('DELETE FROM auth_limits WHERE key IN (%s,%s)',(server.accounts.hashed('ip:'+self.name),server.accounts.hashed('name:'+self.name)))
    def create(self,mode='hotseat'):
        response=self.client.post('/api/matches',json={'mode':mode})
        self.assertEqual(response.status_code,201)
        data=response.get_json(); self.ids.append(data['id'])
        data.update(token='0',other_token='1')
        return data
    def auth(self,token): return {'X-Player-Side':token,'X-CSRF-Token':self.csrf}
    def test_persistence_hidden_hand_and_auth(self):
        m=self.create(); url='/api/matches/'+m['id']
        self.assertEqual(server.app.test_client().get(url).status_code,401)
        data=self.client.get(url,headers=self.auth(m['token'])).get_json()
        self.assertNotIn('decks',data['state']); self.assertNotIn('hands',data['state'])
        self.assertEqual(len(data['state']['hand']),6)
        self.assertEqual(self.client.get(url,headers=self.auth(m['other_token'])).get_json()['side'],1)
    def test_preview_undo_and_revision(self):
        m=self.create(); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        state=self.client.get(url,headers=h).get_json()['state']
        index=next(i for i,k in enumerate(state['hand']) if k in server.rules.UNITS)
        action={'type':'deploy','card':index,'x':0,'y':0}
        data={'revision':0,'actions':[action]}
        preview=self.client.post(url+'/preview',headers=h,json=data)
        self.assertEqual(preview.status_code,200)
        self.assertEqual(preview.get_json()['state']['ap'],4)
        self.assertEqual(self.client.get(url,headers=h).get_json()['state']['ap'],5)
        self.assertEqual(self.client.post(url+'/submit',headers=h,json=data).status_code,200)
        self.assertEqual(self.client.post(url+'/submit',headers=h,json=data).status_code,409)
        state=self.client.get(url,headers=h).get_json()['state']
        self.assertEqual(state['player'],1)
        self.assertEqual(self.client.post(url+'/preview',headers=h,json={'revision':1,'actions':[]}).status_code,400)
    def test_invite_claimed_once(self):
        m=self.create('friend'); url='/api/matches/'+m['id']
        self.assertEqual(self.client.post(url+'/submit',headers=self.auth(m['token']),json={'revision':0,'actions':[]}).status_code,400)
        self.assertEqual(self.client.post(url+'/join',json={'invite':'bad'}).status_code,403)
        joined=self.client.post(url+'/join',json={'invite':m['invite']})
        self.assertEqual(joined.status_code,200)
        self.assertEqual(self.client.post(url+'/join',json={'invite':m['invite']}).status_code,403)
        self.assertEqual(self.client.get(url,headers=self.auth('1')).status_code,200)
    def test_replay_never_leaks_hands(self):
        m=self.create(); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        state=self.client.get(url,headers=h).get_json()['state']
        index=next(i for i,k in enumerate(state['hand']) if k in server.rules.UNITS)
        self.client.post(url+'/submit',headers=h,json={'revision':0,'actions':[{'type':'deploy','card':index,'x':0,'y':0}]})
        replay=self.client.get(url+'/replay/1',headers=h)
        self.assertEqual(replay.status_code,200)
        frames=replay.get_json()['frames']
        self.assertEqual(len(frames),2)
        self.assertEqual(len(frames[1]['units']),len(frames[0]['units'])+1)
        for frame in replay.get_json()['frames']:
            self.assertEqual(frame['hand'],[])
            self.assertNotIn('hands',frame); self.assertNotIn('decks',frame)
        self.assertEqual(server.app.test_client().get(url+'/replay/1').status_code,401)
        self.assertEqual(self.client.get(url+'/replay/999',headers=h).status_code,404)
    def test_simultaneous_submission_commits_once(self):
        m=self.create(); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        def submit(_):
            with server.app.test_client() as client:
                client.set_cookie(server.accounts.COOKIE,self.client.get_cookie(server.accounts.COOKIE).value)
                return client.post(url+'/submit',headers=h,json={'revision':0,'actions':[]}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(submit,range(2))),[200,409])
        saved=self.client.get(url,headers=h).get_json()
        self.assertEqual(saved['revision'],1)
        self.assertEqual(len(saved['history']),1)
    def test_malformed_action_rejected(self):
        m=self.create(); url='/api/matches/'+m['id']+'/preview'; h=self.auth(m['token'])
        for action in [None,{}, {'type':'deploy','card':True,'x':0,'y':0}, {'type':'teleport','unit':{},'x':0,'y':0}]:
            self.assertEqual(self.client.post(url,headers=h,json={'revision':0,'actions':[action]}).status_code,400)
    def test_resignation_final(self):
        m=self.create(); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        result=self.client.post(url+'/resign',headers=h,json={'revision':0})
        self.assertEqual(result.get_json()['state']['winner'],1)
        self.assertEqual(self.client.post(url+'/submit',headers=h,json={'revision':1,'actions':[]}).status_code,400)
    def test_practice_bot_returns_turn(self):
        m=self.create('practice'); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        result=self.client.post(url+'/submit',headers=h,json={'revision':0,'actions':[]})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.get_json()['state']['player'],0)
        self.assertEqual(result.get_json()['state']['turn'],3)
        self.assertEqual(len(result.get_json()['history']),2)
    def test_winning_plan_commits_without_an_extra_turn(self):
        m=self.create('practice'); url='/api/matches/'+m['id']; h=self.auth(m['token'])
        state=server.rules.new_game(1)
        state['units']=[server.rules.make_unit('crystal',0,0,2,'home'),
                        server.rules.make_unit('crystal',1,6,2,'enemy'),
                        server.rules.make_unit('ninja',0,5,2,'ninja')]
        state['units'][1]['hp']=100
        with server.database() as db:
            db.execute('UPDATE matches SET state=%s WHERE id=%s',(server.Jsonb(state),m['id']))
        result=self.client.post(url+'/submit',headers=h,json={'revision':0,'actions':[
            {'type':'attack','unit':'ninja','x':6,'y':2}]}).get_json()
        self.assertEqual(result['state']['winner'],0)
        self.assertEqual(result['state']['turn'],1)
        self.assertEqual(len(result['history']),1)
        self.assertEqual(self.client.get(url,headers=h).get_json()['state'],result['state'])
    def test_dark_elf_match_and_bot(self):
        response=self.client.post('/api/matches',json={'mode':'practice','factions':['council','dark_elves']})
        self.assertEqual(response.status_code,201)
        m=response.get_json();m['token']='0';self.ids.append(m['id'])
        url='/api/matches/'+m['id'];h=self.auth(m['token'])
        result=self.client.post(url+'/submit',headers=h,json={'revision':0,'actions':[]})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.get_json()['state']['factions'],['council','dark_elves'])
        self.assertEqual(result.get_json()['state']['player'],0)
        for factions in [[],['council'],['fake','council'],[{},'council']]:
            self.assertEqual(self.client.post('/api/matches',json={'factions':factions}).status_code,400)
    def test_dwarves_and_saved_barrier(self):
        response=self.client.post('/api/matches',json={'mode':'practice','factions':['dwarves','dark_elves']})
        self.assertEqual(response.status_code,201)
        m=response.get_json();m['token']='0';self.ids.append(m['id'])
        url='/api/matches/'+m['id'];h=self.auth(m['token'])
        state=self.client.get(url,headers=h).get_json()['state']
        engineer=next(u for u in state['units'] if u['kind']=='engineer')
        action=dict(type='barrier',unit=engineer['id'],x=2,y=1)
        preview=self.client.post(url+'/preview',headers=h,json={'revision':0,'actions':[action]}).get_json()
        self.assertTrue(next(u for u in preview['state']['units'] if u['id']=='c00')['barrier'])
        result=self.client.post(url+'/submit',headers=h,json={'revision':0,'actions':[action]})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.get_json()['state']['factions'],['dwarves','dark_elves'])
        self.assertEqual(self.client.get(url,headers=h).get_json()['state'],result.get_json()['state'])

if __name__=='__main__': unittest.main()
