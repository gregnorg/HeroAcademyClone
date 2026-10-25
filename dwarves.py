"""Dwarf launch-baseline abilities. Geometry uncertainties: docs/FIDELITY.md."""
KINDS=('paladin','gunner','grenadier','engineer','annihilator')

def register(r):
    for kind,name,hp,power,reach,armor,magic,damage,ability in [
        ('paladin','Paladin',1000,200,1,10,10,'physical','Heal an ally for twice power; heal herself for half that amount.'),
        ('gunner','Gunner',800,300,2,0,0,'physical','Full damage at melee range; half damage in a three-lane ranged spread.'),
        ('grenadier','Grenadier',800,200,3,0,0,'magical','Lobs explosive grenades over blockers. Half damage in melee.'),
        ('engineer','Engineer',800,200,1,0,0,'physical','Shield one ally or crystal within two squares. Enhanced premium squares.'),
        ('annihilator','Annihilator',650,300,3,0,0,'magical','Rocket splash pushes nearby enemies and weakens the target’s next physical defense.')]:
        r.UNITS[kind]=dict(name=name,hp=hp,power=power,move=2,reach=reach,physical=armor,magical=magic,damage=damage,ability=ability)
    r.ITEMS.update(brew=dict(name='Dwarven Brew',description='Heal 1000; +50 physical and magic resistance against the next hit. Cannot revive.'),
                   pulverizer=dict(name='The Pulverizer',description='500 physical damage. Hitting a crystal splashes nearby enemies. Launch baseline.'))
    deck={**{k:3 for k in KINDS[:-1]},'annihilator':1,'sword':3,'shield':3,'helm':3,'scroll':2,'brew':2,'pulverizer':2}
    r.FACTIONS['dwarves']=dict(name='Dwarves',deck=deck,squad=['paladin','gunner','engineer','grenadier','annihilator'])

def premium(unit,base):
    return base*(140 if unit['kind']=='engineer' else 120 if unit['kind'] in KINDS else 100)//100

def assault(state,side):
    import rules as r
    return sum(premium(u,300) for u in state['units'] if u['owner']==side and u['hp']>0 and r.tile(u)=='assault')

def hit(state,target,power,damage_type):
    import rules as r
    amount=max(0,int(power*(100-r.stats(target)[damage_type])/100))
    return r.hurt(state,target,amount,damage_type)

def push(state,u,dx,dy):
    import rules as r
    if u['kind']=='crystal' or u not in state['units']:return
    nx,ny=u['x']+dx,u['y']+dy
    if 0<=nx<9 and 0<=ny<5 and r.at(state,nx,ny) is None and r.TILES.get(f'{nx},{ny}')!=f'deploy{1-u["owner"]}':
        state['events'].append(dict(type='push',target=u['id'],from_x=u['x'],from_y=u['y'],x=nx,y=ny,label='Knocked back'))
        u.update(x=nx,y=ny)

def attack(state,source,target):
    import rules as r
    kind=source['kind']; x,y=target['x'],target['y']; d=r.distance(source,target)
    power=r.stats(source)['power']*(.5 if source.get('weakened') else 1)
    targets=[(target,1)]
    if kind=='gunner' and d>1:
        power*=.5
        dx=x-source['x'];dy=y-source['y']
        # First standing enemy in each flank lane; diagonal fan is provisional.
        for lane in (-1,1):
            points=[(source['x']+(1 if dx>0 else -1 if dx<0 else 0)*step+(lane if dy else 0),
                     source['y']+(1 if dy>0 else -1 if dy<0 else 0)*step+(lane if dx else 0)) for step in (1,2)]
            for px,py in points:
                u=r.at(state,px,py)
                if u and u['hp']>0:
                    if u['owner']!=source['owner'] and u is not target and all(v is not u for v,_ in targets): targets.append((u,1))
                    break
    elif kind in ('grenadier','annihilator'):
        if kind=='grenadier' and d==1:power*=.5
        else:
            for u in state['units']:
                dx,dy=abs(u['x']-x),abs(u['y']-y)
                if u is not target and u['owner']!=source['owner'] and u['hp']>0 and max(dx,dy)==1:
                    factor=(.25 if dx and dy else .5) if kind=='grenadier' else (.04 if dx and dy else .2)
                    targets.append((u,factor))
    state['events'].append(dict(type='attack',source=source['id'],target=target['id'],from_x=source['x'],from_y=source['y'],x=x,y=y,label=r.UNITS[kind]['name']+' attacked'))
    for u,factor in targets:
        shielded=bool(u.get('barrier'))
        raw=power*factor
        amount=max(0,int(raw*(100-r.stats(u)[r.UNITS[kind]['damage']])/100))
        if u['kind']=='crystal':amount+=assault(state,source['owner'])
        r.hurt(state,u,amount,r.UNITS[kind]['damage'])
        if kind=='annihilator' and u is not target and not shielded:
            push(state,u,(u['x']>x)-(u['x']<x),(u['y']>y)-(u['y']<y))
    if kind=='annihilator' and target in state['units']:target['armor_break']=True
    source.pop('weakened',None)
    if 'scroll' in source['gear']:source['gear'].remove('scroll')

def pulverize(state,target,side):
    import rules as r
    x,y=target['x'],target['y']; crystal=target['kind']=='crystal'
    raw=max(0,int(500*(100-r.stats(target)['physical'])/100))+(assault(state,side) if crystal else 0)
    splash=[u for u in state['units'] if u is not target and u['owner']!=side and u['hp']>0 and max(abs(u['x']-x),abs(u['y']-y))==1] if crystal else []
    r.hurt(state,target,raw,'physical')
    for u in splash:
        hit(state,u,raw*(.16 if u['x']!=x and u['y']!=y else .4),'physical')
    state['events'].append(dict(type='spell',x=x,y=y,label='The Pulverizer'))
