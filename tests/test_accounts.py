import unittest
import uuid
import server

class AccountTests(unittest.TestCase):
 def setUp(self):
  self.name='auth_'+uuid.uuid4().hex[:16];self.email=self.name+'@example.test'
  self.client=server.app.test_client();self.client.environ_base['REMOTE_ADDR']=self.name
  self.headers={'X-Requested-With':'CrystalTactics'};self.ids=[]
 def tearDown(self):
  with server.database() as db:
   for mid in self.ids:db.execute('DELETE FROM matches WHERE id=%s',(mid,))
   db.execute('DELETE FROM accounts WHERE username=%s',(self.name,))
   for prefix,value in [('ip:',self.name),('name:',self.name),('name:',self.email)]:db.execute('DELETE FROM auth_limits WHERE key=%s',(server.accounts.hashed(prefix+value),))
 def register(self):
  r=self.client.post('/api/account/register',json=dict(username=self.name,email=self.email,password='long test password'),headers=self.headers)
  self.assertEqual(r.status_code,201,r.get_json());self.headers['X-CSRF-Token']=r.json['csrf'];return r
 def test_credentials_sessions_and_email_login(self):
  r=self.register();self.assertEqual(r.json['user']['email'],self.email)
  cookie=self.client.get_cookie(server.accounts.COOKIE);self.assertTrue(cookie.http_only);self.assertEqual(cookie.same_site,'Strict')
  with server.database() as db:
   row=db.execute('SELECT password_hash FROM accounts WHERE username=%s',(self.name,)).fetchone()
   self.assertNotEqual(row['password_hash'],'long test password')
  self.assertEqual(self.client.post('/api/account/logout',json={}).status_code,403)
  self.assertEqual(self.client.post('/api/account/logout',json={},headers=self.headers).status_code,200)
  self.assertIsNone(self.client.get('/api/account/session').json['user'])
  self.client.set_cookie(server.accounts.COOKIE,cookie.value)
  self.assertIsNone(self.client.get('/api/account/session').json['user'])
  for password,status in [('wrong password long',401),('long test password',200)]:
   r=self.client.post('/api/account/login',json=dict(username=self.email.upper(),password=password),headers=self.headers)
   self.assertEqual(r.status_code,status,r.json)
 def test_account_ownership_no_capabilities(self):
  self.register();r=self.client.post('/api/matches',json={'mode':'hotseat'},headers=self.headers)
  self.assertEqual(r.status_code,201);mid=r.json['id'];self.ids.append(mid);url='/api/matches/'+mid
  self.assertNotIn('token',r.json)
  outsider=server.app.test_client()
  self.assertEqual(outsider.get(url,headers={'Authorization':'Bearer old-key'}).status_code,401)
  self.assertEqual(outsider.post('/api/matches',json={}).status_code,401)
  self.assertEqual(self.client.post('/api/account/claim',json={},headers=self.headers).status_code,405)
  with server.database() as db:
   db.execute('DELETE FROM match_players WHERE match_id=%s AND side=1',(mid,))
  self.assertEqual(self.client.get(url,headers={'X-Player-Side':'1'}).status_code,403)
  with server.database() as db:
   db.execute('INSERT INTO match_players VALUES (%s,1,%s)',(mid,self.client.get('/api/account/session').json['user']['id']))
  self.assertEqual(len(self.client.get('/api/account/matches').json['matches']),2)
  self.assertEqual(self.client.get(url,headers={'X-Player-Side':'1'}).json['side'],1)
  self.assertEqual(self.client.post(url+'/submit',json={'revision':0},headers={**self.headers,'Origin':'https://evil.example'}).status_code,403)
  with server.database() as db:
   columns=db.execute("SELECT column_name FROM information_schema.columns WHERE table_name='matches'").fetchall()
   self.assertFalse({'token0','token1'} & {r['column_name'] for r in columns})
 def test_validation_and_duplicate_email(self):
  r=self.client.post('/api/account/register',json=dict(username=self.name,email='bad',password='long test password'),headers=self.headers)
  self.assertEqual(r.status_code,400)
  self.register()
  r=self.client.post('/api/account/register',json=dict(username=self.name+'x',email=self.email.upper(),password='long test password'),headers=self.headers)
  self.assertEqual(r.status_code,409)
  with server.database() as db:db.execute('DELETE FROM auth_limits WHERE key=%s',(server.accounts.hashed('name:'+self.name+'x'),))
 def test_rate_limit(self):
  for i in range(11):
   r=self.client.post('/api/account/login',json=dict(username=self.name,password='wrong password long'),headers=self.headers)
  self.assertEqual(r.status_code,429)

if __name__=='__main__':unittest.main()
