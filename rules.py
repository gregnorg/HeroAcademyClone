"""Independent rules engine. All actions are deterministic; see docs/FIDELITY.md."""
from copy import deepcopy
import random

VERSION = 'council-2012-reconstruction-v1'
UNITS = {
    'knight': dict(name='Knight', hp=1200, power=200, move=2, reach=1, physical=20, magical=0, damage='physical', ability='Pushes its target back one square.'),
    'archer': dict(name='Archer', hp=800, power=300, move=2, reach=3, physical=0, magical=0, damage='physical', ability='Half damage at melee range.'),
    'wizard': dict(name='Wizard', hp=800, power=200, move=2, reach=2, physical=0, magical=0, damage='magical', ability='Lightning chains to two nearby enemies at 75% and 50% power.'),
    'cleric': dict(name='Cleric', hp=800, power=200, move=2, reach=2, physical=0, magical=0, damage='magical', ability='Heals allies for 600; revives for 400. Power increases healing.'),
    'ninja': dict(name='Ninja', hp=800, power=200, move=3, reach=2, physical=0, magical=0, damage='physical', ability='Double melee damage. Swap with any standing ally.'),
    'crystal': dict(name='Crystal', hp=4500, power=0, move=0, reach=0, physical=0, magical=0, damage='physical', ability='Destroy every enemy crystal to win.'),
}
ITEMS = {
    'sword': dict(name='Runemetal', description='+50% base power. One per unit.'),
    'shield': dict(name='Dragonscale', description='+20 percentage points physical resistance.'),
    'helm': dict(name='Shining Helm', description='+20 percentage points magic resistance; +10% base health.'),
    'scroll': dict(name='Supercharge', description='Triples power for the next attack or heal.'),
    'potion': dict(name='Revive Potion', description='Heal 1000 HP or revive with 100 HP.'),
    'inferno': dict(name='Inferno', description='350 magic damage to enemies in a 3×3 area. Removes existing enemy corpses.'),
}
DECK = {**{k: 3 for k in ('knight', 'archer', 'wizard', 'cleric')}, 'ninja': 1, 'sword': 3, 'shield': 3, 'helm': 3, 'scroll': 2, 'potion': 2, 'inferno': 2}
# Launch-era Dark Elf baseline; uncertain interactions are listed in the ledger.
DARK_UNITS = ('void_monk','impaler','priestess','necromancer','wraith','phantom')
for kind, name, hp, power, move, reach, physical, magical, damage, ability in [
    ('void_monk','Void Monk',800,200,2,1,20,20,'physical','Strikes enemies beside and behind the target. Life leech.'),
    ('impaler','Impaler',800,300,2,2,0,0,'physical','Pulls the target one square closer. Life leech.'),
    ('necromancer','Necromancer',800,200,2,3,0,0,'magical','Raise a Phantom from a corpse within three squares. Life leech.'),
    ('priestess','Priestess',800,200,2,2,0,0,'magical','Heal 400 or revive 100 within three squares. Attacks weaken the next enemy attack.'),
    ('wraith','Wraith',650,250,3,1,0,10,'magical','Consume adjacent corpses: +150 health and +50 power, up to three times. Deploy on corpses.'),
    ('phantom','Phantom',200,100,3,1,0,10,'magical','Summoned spirit. Cannot equip items; disappears when defeated.')]:
    UNITS[kind]=dict(name=name,hp=hp,power=power,move=move,reach=reach,physical=physical,magical=magical,damage=damage,ability=ability)
ITEMS.update(
    soulstone=dict(name='Soulstone',description='+10% base health; doubles life leech.'),
    mana_vial=dict(name='Mana Vial',description='Heal a standing ally for 1000 and add 50 maximum health.'),
    soul_harvest=dict(name='Soul Harvest',description='100 magic damage in a 3×3 area; distribute stolen life to all friendly heroes, including fallen ones. Formula provisional.'))
DARK_DECK={**{k:3 for k in ('void_monk','impaler','necromancer','priestess')},'wraith':1,
           'sword':3,'soulstone':3,'helm':3,'scroll':2,'mana_vial':2,'soul_harvest':2}
FACTIONS={
    'council':dict(name='Council',deck=DECK,squad=['knight','archer','cleric','wizard','ninja']),
    'dark_elves':dict(name='Dark Elves',deck=DARK_DECK,squad=['void_monk','impaler','priestess','necromancer','wraith'])}

# Zero-based coordinates, from the annotated map in Justesen (2015).
TILES = {'0,0': 'deploy0', '0,4': 'deploy0', '8,0': 'deploy1', '8,4': 'deploy1',
         '4,0': 'defense', '4,4': 'assault', '2,2': 'power', '6,2': 'power'}

class InvalidMove(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise InvalidMove(message)

def distance(a, b):
    return abs(a['x'] - b['x']) + abs(a['y'] - b['y'])

def tile(unit):
    return TILES.get(f"{unit['x']},{unit['y']}", 'plain')

def make_unit(kind, owner, x, y, uid):
    return dict(id=uid, kind=kind, owner=owner, x=x, y=y, hp=UNITS[kind]['hp'], gear=[])

def stats(unit):
    base = dict(UNITS[unit['kind']])
    gear = unit['gear']
    base['hp'] += (base['hp']//10) * sum(g in gear for g in ('helm','soulstone'))
    base['hp'] += unit.get('bonus_hp',0)+150*unit.get('souls',0)
    base['power'] += 50*unit.get('souls',0)
    base['power'] = int(base['power'] * (1.5 if 'sword' in gear else 1))
    if tile(unit) == 'power':
        base['power'] += 100
    if 'scroll' in gear:
        base['power'] *= 3
    base['physical'] += (20 if 'shield' in gear else 0) + (20 if tile(unit) == 'defense' else 0)
    base['magical'] += 20 if 'helm' in gear else 0
    return base

def at(state, x, y):
    return next((u for u in state['units'] if u['x'] == x and u['y'] == y), None)

def new_game(seed=None, practice=False, factions=None):
    factions=['council','council'] if factions is None else factions
    require(isinstance(factions,list) and len(factions)==2 and all(isinstance(f,str) and f in FACTIONS for f in factions), 'Choose two supported factions.')
    rng = random.Random(seed)
    decks, hands = [], []
    for faction in factions:
        deck = [k for k, n in FACTIONS[faction]['deck'].items() for _ in range(n)]
        rng.shuffle(deck)
        # Avoid an unplayable opening. Exact original opening draw constraints remain unverified.
        if not any(k in UNITS for k in deck[-6:]):
            index = next(i for i, k in enumerate(deck) if k in UNITS)
            deck[index], deck[-1] = deck[-1], deck[index]
        hands.append([deck.pop() for _ in range(6)])
        decks.append(deck)
    units = [make_unit('crystal', side, x, y, f'c{side}{i}')
             for side, coords in enumerate([[(2,1),(1,3)],[(6,1),(7,3)]])
             for i, (x,y) in enumerate(coords)]
    state = dict(version=VERSION, turn=1, player=0, ap=5, units=units, hands=hands, decks=decks,
                 pending_swaps=[[],[]], next_id=1, winner=None, events=[], practice=practice, factions=list(factions))
    if practice:
        for side in range(2):
            for kind, (x,y) in zip(FACTIONS[factions[side]]['squad'],[(2,0),(2,3),(1,2),(3,2),(1,4)]):
                # Deal from that side's real inventory rather than conjuring extra units.
                source = hands[side] if kind in hands[side] else decks[side]
                source.remove(kind)
                units.append(make_unit(kind, side, x if side == 0 else 8-x, y, str(state['next_id'])))
                state['next_id'] += 1
            refill(state, side)
    return state

def refill(state, side):
    while len(state['hands'][side]) < 6 and state['decks'][side]:
        state['hands'][side].append(state['decks'][side].pop())

def line_clear(state, source, target):
    # Center-to-center ray; exact corner tie behavior is documented as provisional.
    dx, dy = target['x'] - source['x'], target['y'] - source['y']
    steps = max(abs(dx), abs(dy)) * 4
    for i in range(1, steps):
        x = int(source['x'] + .5 + dx * i / steps)
        y = int(source['y'] + .5 + dy * i / steps)
        if (x,y) in [(source['x'],source['y']), (target['x'],target['y'])]:
            continue
        blocker = at(state,x,y)
        if blocker and blocker['hp'] > 0 and blocker['owner'] != source['owner']:
            return False
    return True

def damage_amount(state, source, target, multiplier=1):
    power = stats(source)['power']
    if source.get('weakened'): power //= 2
    d = distance(source, target)
    if source['kind'] == 'archer' and d == 1:
        power //= 2
    if source['kind'] == 'ninja' and d == 1:
        power *= 2
    power = int(power * multiplier)
    if target['kind'] == 'crystal':
        power += 300 * sum(u['owner'] == source['owner'] and u['hp'] > 0 and tile(u) == 'assault' for u in state['units'])
    return int(power * (100 - stats(target)[UNITS[source['kind']]['damage']]) / 100)

def hurt(state, target, amount):
    target['hp'] = max(0, target['hp'] - amount)
    state['events'].append(dict(type='damage', target=target['id'], x=target['x'], y=target['y'], amount=amount))
    if target['hp'] == 0:
        if target['kind'] in ('crystal','phantom'):
            state['units'].remove(target)
        else:
            target['ko_turn'] = state['turn']

def check_winner(state):
    for side in (0,1):
        crystals = any(u['owner'] == side and u['kind'] == 'crystal' for u in state['units'])
        reserves = any(k in UNITS for k in state['hands'][side] + state['decks'][side] + state['pending_swaps'][side])
        soldiers = any(u['owner'] == side and u['kind'] != 'crystal' for u in state['units'])
        if not crystals or not (reserves or soldiers):
            state['winner'] = 1-side
            return

def apply(state, action):
    """Return a new state or raise. Invalid inputs cannot partially mutate a match."""
    require(isinstance(action, dict), 'Expected an action object.')
    result = deepcopy(state)
    result['events'] = []
    require(result['winner'] is None, 'This match is finished.')
    require(result['ap'] > 0, 'Submit your turn to continue.')
    kind = action.get('type')
    side = result['player']
    if kind == 'swap_card':
        card_index = action.get('card')
        require(type(card_index) is int and 0 <= card_index < len(result['hands'][side]), 'Choose a card.')
        require(bool(result['decks'][side]), 'No reserve cards left to exchange.')
        card = result['hands'][side].pop(card_index)
        result['pending_swaps'][side].append(card)
        result['events'].append(dict(type='swap_card', label='Returned a card to reserves'))
    elif kind in ('deploy','item'):
        card_index = action.get('card')
        require(type(card_index) is int and 0 <= card_index < len(result['hands'][side]), 'Choose a card.')
        card = result['hands'][side][card_index]
        x,y = action.get('x'),action.get('y')
        require(type(x) is int and type(y) is int and 0 <= x < 9 and 0 <= y < 5, 'Choose a board square.')
        target = at(result,x,y)
        if kind == 'deploy':
            require(card in UNITS and card != 'crystal', 'Choose a unit card.')
            corpse=card=='wraith' and target is not None and target['hp']==0
            require(corpse or TILES.get(f'{x},{y}') == f'deploy{side}', 'Deploy on your glowing corner squares, or a corpse for a Wraith.')
            require(target is None or corpse, 'That deployment square is occupied.')
            if corpse: result['units'].remove(target)
            unit = make_unit(card,side,x,y,str(result['next_id']))
            result['next_id'] += 1
            if corpse: unit.update(souls=1,hp=800)
            result['units'].append(unit)
            result['events'].append(dict(type='deploy', target=unit['id'], x=x,y=y,label=f'Deployed {UNITS[card]["name"]}'))
        else:
            require(card in ITEMS, 'Choose an item card.')
            if card == 'soul_harvest':
                drained=0
                for u in list(result['units']):
                    if u['owner']!=side and u['hp']>0 and abs(u['x']-x)<=1 and abs(u['y']-y)<=1:
                        damage=int(100*(100-stats(u)['magical'])/100)
                        if u['kind']=='crystal': damage+=300*sum(v['owner']==side and v['hp']>0 and tile(v)=='assault' for v in result['units'])
                        drained+=min(u['hp'],damage); hurt(result,u,damage)
                allies=[u for u in result['units'] if u['owner']==side and u['kind']!='crystal']
                gain=int(drained/(3+len(allies))/5+.5)*5
                for u in allies:
                    if gain:
                        u['bonus_hp']=u.get('bonus_hp',0)+gain; u['hp']+=gain; u.pop('ko_turn',None)
                result['events'].append(dict(type='spell',x=x,y=y,label=f'Soul Harvest: +{gain} health per ally'))
            elif card == 'inferno':
                targets = [u for u in result['units'] if u['owner'] != side and abs(u['x']-x)<=1 and abs(u['y']-y)<=1]
                for u in targets:
                    if u['hp'] == 0:
                        result['units'].remove(u)
                    else:
                        bonus = 300 * sum(v['owner']==side and v['hp']>0 and tile(v)=='assault' for v in result['units']) if u['kind']=='crystal' else 0
                        hurt(result,u,int(350*(100-stats(u)['magical'])/100)+bonus)
                result['events'].append(dict(type='spell',x=x,y=y,label='Inferno'))
            else:
                require(target and target['owner']==side and target['kind']!='crystal', 'Choose one of your units.')
                require(target['kind']!='phantom', 'Phantoms cannot use equipment or potions.')
                if card == 'mana_vial':
                    require(target['hp']>0,'Mana Vials cannot revive.')
                    target['bonus_hp']=target.get('bonus_hp',0)+50
                    target['hp']=min(stats(target)['hp'],target['hp']+1000)
                elif card == 'potion':
                    require(target['hp'] < stats(target)['hp'], 'Already at full health.')
                    target['hp'] = min(stats(target)['hp'], target['hp']+1000) if target['hp'] else 100
                    target.pop('ko_turn',None)
                else:
                    require(target['hp']>0, 'Revive this unit before equipping it.')
                    require(card not in target['gear'], 'This unit already has that equipment.')
                    oldmax = stats(target)['hp']
                    target['gear'].append(card)
                    target['hp'] += stats(target)['hp']-oldmax
                result['events'].append(dict(type='heal' if card in ('potion','mana_vial') else 'equip', target=target['id'],x=x,y=y,label=ITEMS[card]['name']))
        result['hands'][side].pop(card_index)
    elif kind in ('move','attack','heal','teleport','raise','consume'):
        source = next((u for u in result['units'] if u['id']==action.get('unit')),None)
        require(source and source['owner']==side and source['hp']>0 and source['kind']!='crystal', 'Select one of your standing units.')
        x,y = action.get('x'), action.get('y')
        require(type(x) is int and type(y) is int and 0<=x<9 and 0<=y<5, 'Choose a board square.')
        target = at(result,x,y)
        destination = dict(x=x,y=y)
        d = distance(source,destination)
        require(d>0, 'Choose another square.')
        if kind in ('raise','consume'):
            require(target and target['hp']==0 and target['kind']!='crystal','Choose a fallen hero.')
            if kind=='raise':
                require(source['kind']=='necromancer' and d<=3,'Necromancers raise corpses within three squares.')
                result['units'].remove(target)
                phantom=make_unit('phantom',side,x,y,str(result['next_id'])); result['next_id']+=1
                result['units'].append(phantom)
                label='Raised a Phantom'
            else:
                require(source['kind']=='wraith' and d<=1,'Wraiths consume adjacent corpses.')
                result['units'].remove(target)
                if source.get('souls',0)<3:
                    source['souls']=source.get('souls',0)+1; source['hp']+=150
                label='Consumed a soul'
            result['events'].append(dict(type=kind,x=x,y=y,label=label))
        elif kind == 'move':
            require(d<=stats(source)['move'], 'Beyond movement range.')
            require(TILES.get(f'{x},{y}') != f'deploy{1-side}', 'Enemy deployment squares are protected.')
            require(target is None or target['hp']==0, 'That square is occupied.')
            if target:
                result['units'].remove(target)
                result['events'].append(dict(type='stomp',target=target['id'],x=x,y=y,label='Stomped a fallen unit'))
            result['events'].append(dict(type='move',target=source['id'],from_x=source['x'],from_y=source['y'],x=x,y=y,label=f'Moved {UNITS[source["kind"]]["name"]}'))
            source.update(x=x,y=y)
        elif kind == 'teleport':
            require(source['kind']=='ninja' and target and target['owner']==side and target['hp']>0 and target['kind']!='crystal', 'Ninjas swap with standing allies.')
            target['x'],target['y'] = source['x'],source['y']
            source.update(x=x,y=y)
            result['events'].append(dict(type='teleport',target=source['id'],x=x,y=y,label='Ninja swapped positions'))
        elif kind == 'heal':
            require(source['kind'] in ('cleric','priestess') and target and target['owner']==side and target['kind']!='crystal', 'Clerics heal other friendly units.')
            require(d<=(3 if source['kind']=='priestess' else 2), 'Beyond healing range.')
            require(target['hp']<stats(target)['hp'], 'Already at full health.')
            amount = int(stats(source)['power'] * ((2 if target['hp'] else .5) if source['kind']=='priestess' else (3 if target['hp'] else 2)))
            target['hp'] = min(stats(target)['hp'],target['hp']+amount)
            target.pop('ko_turn',None)
            if 'scroll' in source['gear']:
                source['gear'].remove('scroll')
            result['events'].append(dict(type='heal',target=target['id'],x=x,y=y,amount=amount,label=f'Healed {UNITS[target["kind"]]["name"]}'))
        else:
            require(target and target['owner']!=side and target['hp']>0, 'Attack a standing enemy. Move onto a fallen enemy to stomp it.')
            require(d<=stats(source)['reach'], 'Beyond attack range.')
            require(line_clear(result,source,target), 'An enemy blocks line of sight.')
            result['events'].append(dict(type='attack',source=source['id'],target=target['id'],from_x=source['x'],from_y=source['y'],x=x,y=y,label=f'{UNITS[source["kind"]]["name"]} attacked'))
            chain = [target]
            if source['kind']=='wizard':
                for _ in range(2):
                    previous = chain[-1]
                    choices = [u for u in result['units'] if u['owner']!=side and u['hp']>0 and u not in chain and max(abs(u['x']-previous['x']),abs(u['y']-previous['y']))==1]
                    if not choices:
                        break
                    # Reproducible provisional tie-break; exposed in fidelity notes.
                    chain.append(min(choices,key=lambda u:(distance(previous,u),u['y'],u['x'])))
            if source['kind']=='void_monk':
                dx,dy=target['x']-source['x'],target['y']-source['y']
                squares={(target['x']-dy,target['y']+dx),(target['x']+dy,target['y']-dx),(target['x']+dx,target['y']+dy)}
                chain += [u for u in result['units'] if u['owner']!=side and u['hp']>0 and (u['x'],u['y']) in squares]
            stolen=0
            for i,u in enumerate(chain):
                amount=damage_amount(result,source,u,[1,.75,.5][i] if source['kind']=='wizard' else 1)
                stolen+=min(u['hp'],amount); hurt(result,u,amount)
            if source['kind'] in DARK_UNITS:
                amount=min(stats(source)['hp']-source['hp'],stolen*(2 if 'soulstone' in source['gear'] else 1)//3)
                source['hp']+=amount
                if amount: result['events'].append(dict(type='heal',target=source['id'],x=source['x'],y=source['y'],amount=amount,label='Life leech'))
            source.pop('weakened',None)
            if source['kind']=='priestess' and target in result['units'] and target['kind']!='crystal': target['weakened']=True
            if source['kind']=='impaler' and target in result['units'] and target['kind']!='crystal' and d>1:
                dx=source['x']-target['x']; dy=source['y']-target['y']
                nx=target['x']+(1 if dx>0 else -1 if dx<0 else 0)
                ny=target['y']+(1 if dy>0 else -1 if dy<0 else 0)
                if at(result,nx,ny) is None and TILES.get(f'{nx},{ny}')!=f'deploy{side}': target.update(x=nx,y=ny)
            if 'scroll' in source['gear']:
                source['gear'].remove('scroll')
            if source['kind']=='knight' and target in result['units'] and target['kind']!='crystal':
                nx,ny = target['x']+(target['x']-source['x']),target['y']+(target['y']-source['y'])
                if 0<=nx<9 and 0<=ny<5 and at(result,nx,ny) is None and TILES.get(f'{nx},{ny}') != f'deploy{side}':
                    target.update(x=nx,y=ny)
    else:
        raise InvalidMove('Unknown action.')
    result['ap'] -= 1
    check_winner(result)
    return result

def end_turn(state):
    result = deepcopy(state)
    if result['winner'] is not None:
        return result
    side = result['player']
    # A fallen unit survives through its owner's next chance to revive it.
    result['units'] = [u for u in result['units'] if not (u['owner']==side and u['hp']==0 and u.get('ko_turn',result['turn']) < result['turn'])]
    refill(result,side)
    result['decks'][side] = result['pending_swaps'][side] + result['decks'][side]
    result['pending_swaps'][side] = []
    result['player'] = 1-side
    result['turn'] += 1
    result['ap'] = 5
    result['events'] = []
    check_winner(result)
    return result

def legal_actions(state, unit_id=None, card=None):
    actions=[]
    candidates=[]
    if unit_id is not None:
        candidates=[dict(type=t,unit=unit_id,x=x,y=y) for t in ('move','attack','heal','teleport','raise','consume') for y in range(5) for x in range(9)]
    elif card is not None:
        candidates=[dict(type=t,card=card,x=x,y=y) for t in ('deploy','item') for y in range(5) for x in range(9)]
        candidates.append(dict(type='swap_card',card=card))
    for action in candidates:
        try:
            after=apply(state,action)
            actions.append(dict(action=action,events=after['events']))
        except InvalidMove:
            continue
    return actions

def public_state(state, side):
    result=deepcopy(state)
    result['remaining']=[len(state['hands'][p])+len(state['decks'][p])+len(state['pending_swaps'][p]) for p in (0,1)]
    result['hand']=result['hands'][side] if side in (0,1) else []
    for key in ('hands','decks','pending_swaps','next_id'):
        result.pop(key,None)
    for u in result['units']:
        u['stats']=stats(u)
    return result
