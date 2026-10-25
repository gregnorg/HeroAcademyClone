"""Bounded turn planner for practice; uses the same rules as human players."""
from rules import apply, stats, distance, end_turn, InvalidMove, ITEMS

BEAM_WIDTH = 4

def evaluate(state, side):
    if state['winner'] is not None:
        return 1000000 if state['winner']==side else -1000000
    score=0
    enemies=[u for u in state['units'] if u['owner']!=side and u['hp']>0]
    for u in state['units']:
        sign=1 if u['owner']==side else -1
        if u['kind']=='crystal':
            score += sign*u['hp']*.7
        elif u['hp']>0:
            score += sign*(u['hp']*.6+350+len(u['gear'])*100)
            if u['kind']=='cleric': score += sign*150
            if sign==1 and enemies:
                score -= min(distance(u,v) for v in enemies)*24
        else:
            score += sign*80
    return score

def successors(state):
    """Generate plausible actions, with the engine enforcing every rule."""
    side=state['player']
    candidates=[]
    for unit in state['units']:
        if unit['owner']!=side or unit['hp']<=0 or unit['kind']=='crystal': continue
        st=stats(unit)
        for y in range(5):
            for x in range(9):
                d=abs(x-unit['x'])+abs(y-unit['y'])
                if not d: continue
                kinds=[]
                if d<=st['move']: kinds.append('move')
                if d<=st['reach']: kinds.append('attack')
                if unit['kind']=='cleric' and d<=2: kinds.append('heal')
                if unit['kind']=='ninja': kinds.append('teleport')
                candidates.extend(dict(type=t,unit=unit['id'],x=x,y=y) for t in kinds)
    seen_cards=set()
    for i,card in enumerate(state['hands'][side]):
        if card in seen_cards: continue
        seen_cards.add(card)
        for y in range(5):
            for x in range(9):
                candidates.append(dict(type='item' if card in ITEMS else 'deploy',card=i,x=x,y=y))
    for action in candidates:
        try: yield action,apply(state,action)
        except InvalidMove: pass

def position_key(state):
    # Excludes opponent hand/deck: neither search nor tie-breaking may use them.
    return (tuple((u['id'],u['x'],u['y'],u['hp'],tuple(u['gear'])) for u in state['units']),
            tuple(state['hands'][state['player']]))

def play(state):
    side=state['player']
    # Search whole plans, including early submission. Ending a turn can expire
    # corpses, so score that actual result rather than assuming revives are free.
    best=(evaluate(end_turn(state),side),state,[],[])
    beam=[(state,[],[],0)]
    visited={position_key(state)}
    for depth in range(state['ap']):
        expanded=[]
        for current,actions,events,cost in beam:
            if current['winner'] is not None: continue
            for action,after in successors(current):
                key=position_key(after)
                if key in visited: continue
                visited.add(key)
                spent=cost+(45 if action['type']=='item' else 0)
                plan=actions+[action]; log=events+after['events']
                score=evaluate(end_turn(after),side)-spent
                # Small per-action penalty prefers shorter equally good plans.
                value=score-len(plan)*.01
                if value>best[0]: best=(value,after,plan,log)
                expanded.append((evaluate(after,side)-spent,after,plan,log,spent))
        expanded.sort(key=lambda entry:entry[0],reverse=True)
        beam=[(s,a,e,c) for _,s,a,e,c in expanded[:BEAM_WIDTH]]
        if not beam or best[0]>900000: break
    return best[1],best[2],best[3]
