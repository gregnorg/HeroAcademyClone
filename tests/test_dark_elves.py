import unittest
import rules as r

class DarkElfTests(unittest.TestCase):
    def setUp(self): self.s=r.new_game(7,factions=['dark_elves','council'])
    def unit(self,kind,side,x,y,hp=None):
        u=r.make_unit(kind,side,x,y,str(self.s['next_id'])); self.s['next_id']+=1
        if hp is not None: u['hp']=hp
        self.s['units'].append(u); return u
    def test_inventory_and_practice(self):
        cards=self.s['hands'][0]+self.s['decks'][0]
        self.assertEqual(len(cards),28); self.assertEqual(cards.count('wraith'),1)
        self.assertNotIn('knight',cards)
        s=r.new_game(7,True,['dark_elves','dark_elves'])
        for side in (0,1):
            self.assertEqual(sum(u['owner']==side and u['kind']!='crystal' for u in s['units']),5)
            self.assertEqual(len(s['hands'][side])+len(s['decks'][side]),23)
    def test_life_leech_and_pull(self):
        a=self.unit('impaler',0,3,3,400); self.unit('knight',1,5,3)
        s=r.apply(self.s,dict(type='attack',unit=a['id'],x=5,y=3))
        self.assertEqual(r.at(s,4,3)['hp'],960)
        self.assertEqual(r.at(s,3,3)['hp'],480)
    def test_priestess_debuff_consumed_on_attack(self):
        a=self.unit('priestess',0,3,3); b=self.unit('archer',1,5,3)
        s=r.apply(self.s,dict(type='attack',unit=a['id'],x=5,y=3));s['player']=1
        s=r.apply(s,dict(type='attack',unit=b['id'],x=3,y=3))
        self.assertEqual(r.at(s,3,3)['hp'],650)
        self.assertNotIn('weakened',r.at(s,5,3))
    def test_priestess_long_range_revive(self):
        a=self.unit('priestess',0,3,3);self.unit('impaler',0,6,3,0)
        s=r.apply(self.s,dict(type='heal',unit=a['id'],x=6,y=3))
        self.assertEqual(r.at(s,6,3)['hp'],100)
    def test_raise_and_phantom_death(self):
        a=self.unit('necromancer',0,3,3);self.unit('archer',1,4,3,0)
        s=r.apply(self.s,dict(type='raise',unit=a['id'],x=4,y=3))
        phantom=r.at(s,4,3);self.assertEqual(phantom['kind'],'phantom')
        s['hands'][0]=['sword']
        with self.assertRaises(r.InvalidMove):r.apply(s,dict(type='item',card=0,x=4,y=3))
        r.hurt(s,phantom,200);self.assertIsNone(r.at(s,4,3))
    def test_wraith_growth_cap(self):
        a=self.unit('wraith',0,4,2)
        for x,y in [(3,2),(5,2),(4,1),(4,3)]:self.unit('knight',1,x,y,0)
        s=self.s
        for x,y in [(3,2),(5,2),(4,1),(4,3)]:s=r.apply(s,dict(type='consume',unit=a['id'],x=x,y=y))
        w=r.at(s,4,2);self.assertEqual(w['souls'],3)
        self.assertEqual(r.stats(w)['hp'],1100);self.assertEqual(r.stats(w)['power'],400)
    def test_corpse_deployment_and_mana(self):
        self.unit('archer',1,4,2,0);self.s['hands'][0]=['wraith','mana_vial']
        s=r.apply(self.s,dict(type='deploy',card=0,x=4,y=2))
        self.assertEqual(r.at(s,4,2)['souls'],1)
        s=r.apply(s,dict(type='item',card=0,x=4,y=2))
        self.assertEqual(r.stats(r.at(s,4,2))['hp'],850)
    def test_harvest_revives_distant_allies(self):
        self.unit('impaler',0,0,1,0);self.unit('knight',1,4,2)
        self.s['hands'][0]=['soul_harvest']
        s=r.apply(self.s,dict(type='item',card=0,x=4,y=2))
        self.assertEqual(r.at(s,0,1)['hp'],25)
        self.assertEqual(r.stats(r.at(s,0,1))['hp'],825)
    def test_void_monk_splash(self):
        a=self.unit('void_monk',0,3,2)
        for x,y in [(4,2),(4,3),(5,2)]: self.unit('archer',1,x,y)
        s=r.apply(self.s,dict(type='attack',unit=a['id'],x=4,y=2))
        self.assertEqual([e['amount'] for e in s['events'] if e['type']=='damage'],[200,200,200])

if __name__=='__main__':unittest.main()
