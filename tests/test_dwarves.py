import unittest
import rules as r
class DwarfTests(unittest.TestCase):
 def setUp(self): self.s=r.new_game(7,factions=['dwarves','council'])
 def unit(self,kind,owner,x,y,hp=None):
  u=r.make_unit(kind,owner,x,y,str(self.s['next_id']));self.s['next_id']+=1
  if hp is not None:u['hp']=hp
  self.s['units'].append(u);return u
 def test_inventory(self):
  self.assertEqual(len(self.s['hands'][0])+len(self.s['decks'][0]),28)
  self.assertEqual((self.s['hands'][0]+self.s['decks'][0]).count('annihilator'),1)
 def test_engineer_premium(self):
  a=self.unit('engineer',0,2,2);self.assertEqual(r.stats(a)['power'],340)
  a.update(x=4,y=0);self.assertEqual(r.stats(a)['physical'],28)
  a.update(y=4);self.assertEqual(r.dwarves.assault(self.s,0),420)
 def test_paladin_heals_both(self):
  a=self.unit('paladin',0,3,3,500);self.unit('gunner',0,4,3,200)
  s=r.apply(self.s,dict(type='heal',unit=a['id'],x=4,y=3))
  self.assertEqual(r.at(s,4,3)['hp'],600);self.assertEqual(r.at(s,3,3)['hp'],700)
 def test_barrier_blocks_one_hit_and_knockback(self):
  a=self.unit('engineer',0,3,3);self.unit('gunner',0,4,3);b=self.unit('knight',1,5,3)
  s=r.apply(self.s,dict(type='barrier',unit=a['id'],x=4,y=3));s['player']=1
  s=r.apply(s,dict(type='attack',unit=b['id'],x=4,y=3))
  self.assertEqual(r.at(s,4,3)['hp'],800);self.assertNotIn('barrier',r.at(s,4,3))
 def test_barrier_moves_and_dies_with_engineer(self):
  a=self.unit('engineer',0,3,3);self.unit('gunner',0,4,3);self.unit('paladin',0,3,4)
  s=r.apply(self.s,dict(type='barrier',unit=a['id'],x=4,y=3))
  s=r.apply(s,dict(type='barrier',unit=a['id'],x=3,y=4))
  self.assertNotIn('barrier',r.at(s,4,3))
  r.hurt(s,r.at(s,3,3),9999);self.assertNotIn('barrier',r.at(s,3,4))
 def test_grenade_ignores_blocker_and_splashes(self):
  a=self.unit('grenadier',0,3,2);self.unit('knight',1,4,2);self.unit('archer',1,5,2);self.unit('archer',1,5,3)
  s=r.apply(self.s,dict(type='attack',unit=a['id'],x=5,y=2))
  self.assertEqual(r.at(s,5,2)['hp'],600);self.assertEqual(r.at(s,5,3)['hp'],700)
 def test_brew_consumed_once(self):
  a=self.unit('gunner',0,3,3);self.s['hands'][0]=['brew'];b=self.unit('archer',1,5,3)
  s=r.apply(self.s,dict(type='item',card=0,x=3,y=3));s['player']=1
  s=r.apply(s,dict(type='attack',unit=b['id'],x=3,y=3));self.assertEqual(r.at(s,3,3)['hp'],650)
  s=r.apply(s,dict(type='attack',unit=b['id'],x=3,y=3));self.assertEqual(r.at(s,3,3)['hp'],350)
 def test_annihilator_break_and_push(self):
  a=self.unit('annihilator',0,3,2);self.unit('knight',1,5,2);self.unit('archer',1,5,3)
  s=r.apply(self.s,dict(type='attack',unit=a['id'],x=5,y=2))
  self.assertTrue(r.at(s,5,2)['armor_break']);self.assertEqual(r.stats(r.at(s,5,2))['physical'],-30)
  self.assertEqual(r.at(s,5,4)['hp'],740)
 def test_pulverizer_crystal_splash(self):
  self.unit('archer',1,6,2);self.s['hands'][0]=['pulverizer']
  s=r.apply(self.s,dict(type='item',card=0,x=6,y=1))
  self.assertEqual(r.at(s,6,1)['hp'],4000);self.assertEqual(r.at(s,6,2)['hp'],600)
if __name__=='__main__':unittest.main()
