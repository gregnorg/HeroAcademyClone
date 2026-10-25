"""A transparent, bounded greedy sparring partner; not an original-game feature."""
from rules import apply, legal_actions, stats, distance, UNITS

def evaluate(state, side):
    if state['winner'] is not None:
        return 1000000 if state['winner']==side else -1000000
    score=0
    for u in state['units']:
        sign=1 if u['owner']==side else -1
        if u['kind']=='crystal':
            score += sign*u['hp']*.7
        elif u['hp']>0:
            score += sign*(u['hp']*.6+350+len(u['gear'])*100)
            if sign==1:
                enemies=[v for v in state['units'] if v['owner']!=side and v['hp']>0]
                if enemies:
                    score -= min(distance(u,v) for v in enemies)*24
                if u['kind']=='cleric': score += 90
        else:
            score += sign*80
    return score

def play(state):
    side=state['player']; actions=[]; events=[]
    while state['ap']>0 and state['winner'] is None:
        candidates=[]
        for unit in state['units']:
            if unit['owner']==side and unit['hp']>0 and unit['kind']!='crystal':
                candidates.extend(legal_actions(state,unit_id=unit['id']))
        for i in range(len(state['hands'][side])):
            candidates.extend(legal_actions(state,card=i))
        best=None; bestscore=evaluate(state,side)
        for candidate in candidates:
            action=candidate['action']
            if action['type']=='swap_card': continue
            after=apply(state,action)
            score=evaluate(after,side)
            # Reserve consumables have value; prevent spending them without purpose.
            if action['type']=='item': score-=45
            if score>bestscore:
                best=(action,after); bestscore=score
        if best is None: break
        action,state=best; actions.append(action); events.extend(state['events'])
    return state,actions,events
