import unittest
from copy import deepcopy
import bot
import rules

class BotTests(unittest.TestCase):
    def test_move_then_destroy_last_crystal(self):
        s=rules.new_game(1)
        s['units']=[rules.make_unit('crystal',0,0,2,'home'),
                    rules.make_unit('crystal',1,6,2,'enemy'),
                    rules.make_unit('ninja',0,2,2,'ninja')]
        s['units'][1]['hp']=400
        s['hands'][0]=[]; s['ap']=2
        original=deepcopy(s)
        after,actions,events=bot.play(s)
        self.assertEqual(after['winner'],0)
        self.assertEqual([a['type'] for a in actions],['move','attack'])
        self.assertEqual(s,original)
        replay=s
        for action in actions: replay=rules.apply(replay,action)
        self.assertEqual(after,replay)
        self.assertEqual(rules.end_turn(after),after)

    def test_opponent_hidden_cards_do_not_affect_plan(self):
        s=rules.new_game(17,practice=True); s['ap']=2
        other=deepcopy(s)
        other['hands'][1].reverse(); other['decks'][1].reverse()
        self.assertEqual(bot.play(s)[1],bot.play(other)[1])

    def test_revives_last_fallen_hero_before_expiration(self):
        s=rules.new_game(2)
        unit=rules.make_unit('knight',0,0,0,'fallen')
        unit.update(hp=0,ko_turn=1)
        s['units'].append(unit); s['turn']=3
        s['hands'][0]=['potion']; s['decks'][0]=[]; s['ap']=1
        after,actions,_=bot.play(s)
        self.assertEqual(actions,[dict(type='item',card=0,x=0,y=0)])
        self.assertIsNone(rules.end_turn(after)['winner'])

if __name__=='__main__': unittest.main()
