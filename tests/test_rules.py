import unittest
from copy import deepcopy
from rules import *

class RulesTests(unittest.TestCase):
    def setUp(self):
        self.s=new_game(17)
    def unit(self,kind,side,x,y):
        u=make_unit(kind,side,x,y,str(len(self.s['units'])))
        self.s['units'].append(u)
        return u
    def test_inventory(self):
        for p in (0,1):
            cards=self.s['hands'][p]+self.s['decks'][p]
            self.assertEqual(len(cards),28)
            self.assertEqual(cards.count('ninja'),1)
    def test_archer_melee_and_knight_armor(self):
        a=self.unit('archer',0,3,3); k=self.unit('knight',1,4,3)
        self.assertEqual(damage_amount(self.s,a,k),120)
        k['x']=5
        self.assertEqual(damage_amount(self.s,a,k),240)
    def test_ninja_sword_scroll(self):
        n=self.unit('ninja',0,3,3); a=self.unit('archer',1,4,3)
        n['gear']=['sword','scroll']
        self.assertEqual(damage_amount(self.s,n,a),1800)
        r=apply(self.s,dict(type='attack',unit=n['id'],x=4,y=3))
        self.assertNotIn('scroll',next(u for u in r['units'] if u['id']==n['id'])['gear'])
        self.assertIn('scroll',n['gear'])
    def test_invalid_atomic(self):
        original=deepcopy(self.s)
        with self.assertRaises(InvalidMove):
            apply(self.s,dict(type='move',unit='missing',x=4,y=3))
        self.assertEqual(self.s,original)
    def test_ap_enforced(self):
        u=self.unit('knight',0,3,3)
        for i in range(5):
            self.s=apply(self.s,dict(type='move',unit=u['id'],x=3,y=2 if i%2==0 else 3))
        with self.assertRaises(InvalidMove):
            apply(self.s,dict(type='move',unit=u['id'],x=3,y=3))
        self.assertEqual(end_turn(self.s)['ap'],5)
    def test_revive_and_stomp(self):
        c=self.unit('cleric',0,3,3); a=self.unit('archer',0,4,3)
        a['hp']=0; a['ko_turn']=0
        healed=apply(self.s,dict(type='heal',unit=c['id'],x=4,y=3))
        self.assertEqual(at(healed,4,3)['hp'],400)
        enemy=self.unit('knight',1,5,3); self.s['player']=1
        stomp=apply(self.s,dict(type='move',unit=enemy['id'],x=4,y=3))
        self.assertFalse(any(u['id']==a['id'] for u in stomp['units']))
    def test_chain_falloff(self):
        w=self.unit('wizard',0,3,2)
        for x,y in [(4,2),(4,3),(5,3)]: self.unit('archer',1,x,y)
        after=apply(self.s,dict(type='attack',unit=w['id'],x=4,y=2))
        self.assertEqual([e['amount'] for e in after['events'] if e['type']=='damage'],[200,150,100])
    def test_crystal_victory(self):
        self.s['units']=[u for u in self.s['units'] if not (u['owner']==1 and u['id']=='c11')]
        c=next(u for u in self.s['units'] if u['id']=='c10'); c['hp']=100
        a=self.unit('archer',0,5,1)
        self.assertEqual(apply(self.s,dict(type='attack',unit=a['id'],x=6,y=1))['winner'],0)
    def test_hidden_information(self):
        p=public_state(self.s,0)
        self.assertNotIn('hands',p); self.assertNotIn('decks',p)
        self.assertEqual(p['hand'],self.s['hands'][0])
    def test_duplicate_equipment(self):
        u=self.unit('archer',0,3,3); u['gear']=['sword']; self.s['hands'][0]=['sword']
        with self.assertRaises(InvalidMove): apply(self.s,dict(type='item',card=0,x=3,y=3))
    def test_inferno_only_removes_existing_corpses(self):
        a=self.unit('archer',1,4,2); a['hp']=100
        b=self.unit('knight',1,4,3); b['hp']=0
        self.s['hands'][0]=['inferno']
        after=apply(self.s,dict(type='item',card=0,x=4,y=2))
        self.assertEqual(at(after,4,2)['hp'],0); self.assertIsNone(at(after,4,3))
    def test_corpse_lifetime(self):
        a=self.unit('archer',1,4,2); a.update(hp=0,ko_turn=1)
        s=end_turn(self.s); self.assertIsNotNone(at(s,4,2))
        s=end_turn(s); self.assertIsNone(at(s,4,2))
    def test_swap_does_not_reveal_card_before_commit(self):
        self.s['hands'][0]=['inferno']*6
        after=apply(self.s,dict(type='swap_card',card=0))
        self.assertEqual(len(after['hands'][0]),5)
        self.assertEqual(len(end_turn(after)['hands'][0]),6)
    def test_blocked_los_and_friendly_passthrough(self):
        a=self.unit('archer',0,3,3); b=self.unit('knight',1,4,3); c=self.unit('cleric',1,5,3)
        self.assertFalse(line_clear(self.s,a,c)); b['owner']=0
        self.assertTrue(line_clear(self.s,a,c))

if __name__=='__main__': unittest.main()
