import unittest
import server

class APITests(unittest.TestCase):
    def setUp(self):
        self.client=server.app.test_client()
        self.ids=[]
    def tearDown(self):
        with server.database() as db:
            for mid in self.ids: db.execute('DELETE FROM matches WHERE id=%s',(mid,))
    def create(self,mode='hotseat'):
        response=self.client.post('/api/matches',json={'mode':mode})
        self.assertEqual(response.status_code,201)
        data=response.get_json(); self.ids.append(data['id'])
        return data
    def auth(self,token): return {'Authorization':'Bearer '+token}
    def test_persistence_hidden_hand_and_auth(self):
        m=self.create(); url='/api/matches/'+m['id']
        self.assertEqual(self.client.get(url).status_code,403)
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
        self.assertEqual(self.client.get(url,headers=self.auth(joined.get_json()['token'])).status_code,200)
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

if __name__=='__main__': unittest.main()
