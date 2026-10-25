import {portrait} from './art.js';
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let rulebook, current=null, view=null, actions=[], selected=null, legal=[], busy=false, selectionEpoch=0, sound=false;
let saves=[];
try{saves=JSON.parse(localStorage.getItem('ct.matches')||'[]');if(!Array.isArray(saves))saves=[];}catch{saves=[];}
let audioContext;
function tone(kind='move'){
 if(!sound)return;
 try{audioContext??=new (window.AudioContext||window.webkitAudioContext)();audioContext.resume();const t=audioContext.currentTime;const o=audioContext.createOscillator(),g=audioContext.createGain();o.connect(g);g.connect(audioContext.destination);o.type=kind==='attack'?'triangle':'sine';o.frequency.setValueAtTime(kind==='attack'?180:kind==='heal'?660:440,t);o.frequency.exponentialRampToValueAtTime(kind==='attack'?70:880,t+.15);g.gain.setValueAtTime(.055,t);g.gain.exponentialRampToValueAtTime(.001,t+.22);o.start();o.stop(t+.23);}catch{}
}
function persist(){try{localStorage.setItem('ct.matches',JSON.stringify(saves));}catch{toast('Browser storage is unavailable. Keep your player link to return to this match.');}}
function saveMatch(m){const previous=saves.find(x=>x.id===m.id);if(previous)Object.assign(previous,m);else saves.unshift({...m,created:new Date().toISOString()});persist();return saves.find(x=>x.id===m.id);}
function saveDraft(){if(!current||!view)return;try{localStorage.setItem(`ct.draft.${current.id}.${view.side}`,JSON.stringify({revision:view.revision,actions}));}catch{}}
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,4500);}
function modal(html){$('#modal-content').innerHTML=html;if(!$('#modal').open)$('#modal').showModal();}
$('#close-modal').onclick=()=>$('#modal').close();
$('#modal').addEventListener('click',e=>{if(e.target===$('#modal'))$('#modal').close();});
async function api(path,{method='GET',body,token=current?.token}={}){
 const response=await fetch('/api'+path,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(token?{Authorization:'Bearer '+token}:{})},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(90000)});
 const data=await response.json();if(!response.ok){const error=new Error(data.error||'Request failed.');error.status=response.status;throw error;}return data;
}
function lock(value){busy=value;document.body.classList.toggle('busy',value);if(view){renderControls();for(const card of document.querySelectorAll('#hand button'))card.disabled=value||!canPlay();}}
function team(side){return side===0?'Azure':'Crimson';}
function canPlay(){return view && (view.state.winner===null || actions.length>0) && view.side===view.state.player;}
function canAct(){return canPlay() && view.state.winner===null && view.state.ap>0 && !busy;}
function unitAt(x,y){return view.state.units.find(u=>u.x===x&&u.y===y);}
function name(kind){return rulebook.units[kind]?.name||rulebook.items[kind]?.name||kind;}
function draftKey(){return `ct.draft.${current.id}.${view.side}`;}
async function lobby(){selectionEpoch++;current=null;view=null;actions=[];selected=null;legal=[];$('#game').hidden=true;$('#lobby').hidden=false;history.replaceState(null,'',location.pathname);await renderMatches();}
async function renderMatches(){
 const host=$('#matches');host.innerHTML='';
 if(!saves.length){host.innerHTML='<div class="empty">Your academy awaits. Start a practice battle, or share a device for a friendly duel.</div>';return;}
 for(const save of saves){const button=document.createElement('button');button.className='match-card';button.innerHTML=portrait('knight',save.side||0)+`<div><strong>${save.mode==='practice'?'Practice battle':save.mode==='hotseat'?'Pass & play':'Friendly duel'}</strong><span>${save.result||'Continue your battle'} · ${new Date(save.created||Date.now()).toLocaleDateString()}</span></div>`;button.onclick=()=>openMatch(save);host.append(button);}
}
async function create(mode){
 if(busy)return;lock(true);
 try{const m=await api('/matches',{method:'POST',body:{mode},token:null});await openMatch(saveMatch(m));if(mode==='friend')showInvite();}
 catch(e){toast(e.message);}finally{lock(false);}
}
async function openMatch(save){
 if(busy&&current)return;
 lock(true);current=save;selected=null;legal=[];actions=[];
 try{view=await api(`/matches/${save.id}`);save.side=view.side;save.mode=view.mode;
 $('#lobby').hidden=true;$('#game').hidden=false;history.replaceState(null,'',`#match=${save.id}`);
 try{const draft=JSON.parse(localStorage.getItem(draftKey())||'null');if(draft&&draft.revision===view.revision&&canPlay()&&Array.isArray(draft.actions)&&draft.actions.length){const restored=await api(`/matches/${save.id}/preview`,{method:'POST',body:{revision:view.revision,actions:draft.actions}});actions=draft.actions;view=restored;toast('Your unsubmitted turn was restored.');}}catch{toast('Saved draft could not be restored; the submitted match is unchanged.');}
 render();persist();
 if(current.mode==='hotseat'&&view.state.player!==view.side&&view.state.winner===null)offerHandoff();
 }catch(e){toast(e.message);await lobby();}finally{lock(false);}
}
function render(){renderBoard();renderHand();renderControls();renderInspector();renderJournal();}
function renderBoard(){
 const board=$('#board');const old=new Map([...board.querySelectorAll('.unit')].map(el=>[el.dataset.id,el.getBoundingClientRect()]));board.innerHTML='';
 for(let y=0;y<5;y++)for(let x=0;x<9;x++){
 const type=rulebook.tiles[`${x},${y}`]||'plain',unit=unitAt(x,y),entry=legal.find(l=>l.action.x===x&&l.action.y===y);
 const cell=document.createElement('button');cell.className=`tile ${(x+y)%2?'alternate':''} ${type} ${unit?'owner'+unit.owner:''}`;cell.dataset.x=x;cell.dataset.y=y;
 const symbols={deploy0:'❯',deploy1:'❮',power:'⚔',defense:'⛨',assault:'◆'};
 cell.innerHTML=`<span class="tile-symbol">${symbols[type]||''}</span><span class="tile-coordinate">${String.fromCharCode(65+x)}${y+1}</span>`;
 if(unit){cell.innerHTML+=`<div class="unit ${unit.hp===0?'ko':'idle'} ${unit.kind}" data-id="${esc(unit.id)}">${portrait(unit.kind,unit.owner,unit.gear)}</div><span class="hp-text">${unit.hp===0?'KO':unit.hp}</span><span class="hp-bar"><i style="width:${Math.max(0,Math.min(100,unit.hp/unit.stats.hp*100))}%"></i></span><span class="equipment">${unit.gear.map(g=>({sword:'⚔',shield:'⛨',helm:'◉',scroll:'ϟ'}[g]||'')).join('')}</span>`;}
 if(entry){cell.classList.add('legal','legal-'+entry.action.type);const damage=entry.events.filter(e=>e.type==='damage').reduce((sum,e)=>sum+e.amount,0);cell.title=`${entry.action.type}${damage?' · '+damage+' total damage':''}`;cell.onmouseenter=cell.onfocus=()=>{if(damage)$('#hint').textContent=entry.events.filter(e=>e.type==='damage').map(e=>`${name(view.state.units.find(u=>u.id===e.target)?.kind||'target')}: −${e.amount} HP`).join(' · ');};}
 if(selected?.unit&&unit?.id===selected.unit)cell.classList.add('selected');
 cell.setAttribute('aria-label',`${String.fromCharCode(65+x)}${y+1}, ${type}${unit?`, ${team(unit.owner)} ${name(unit.kind)}, ${unit.hp} health`:''}${entry?`, ${entry.action.type}`:''}`);
 cell.onclick=()=>clickTile(x,y);board.append(cell);
 }
 if(!matchMedia('(prefers-reduced-motion: reduce)').matches){for(const el of board.querySelectorAll('.unit')){const previous=old.get(el.dataset.id),next=el.getBoundingClientRect();if(previous&&(previous.x!==next.x||previous.y!==next.y)){el.animate([{translate:`${previous.x-next.x}px ${previous.y-next.y}px`},{translate:'0 0'}],{duration:300,easing:'ease-out'});}}}
}
function renderHand(){const hand=$('#hand');hand.innerHTML='';view.state.hand.forEach((kind,i)=>{const button=document.createElement('button');button.className='card'+(selected?.card===i?' selected':'');button.innerHTML=portrait(kind,view.side)+`<strong>${esc(name(kind))}</strong><small>${rulebook.units[kind]?'HERO':'ITEM'} · 1 ACTION</small>`;button.setAttribute('aria-label',`Select ${name(kind)}`);button.onclick=()=>select({card:i});button.disabled=!canPlay()||busy;hand.append(button);});for(let i=view.state.hand.length;i<6;i++){const slot=document.createElement('div');slot.className='card empty-card';slot.innerHTML='◆';hand.append(slot);}}
function renderControls(){
 if(!view)return;const s=view.state;
 $('#avatar0').innerHTML=portrait('knight',0);$('#avatar1').innerHTML=portrait('wizard',1);
 $('#reserve0').textContent=`${s.remaining[0]} reinforcements`;$('#reserve1').textContent=`${s.remaining[1]} reinforcements`;
 $('#turn-label').textContent=`TURN ${s.turn}`;$('#turn-status').textContent=s.winner!==null?`${team(s.winner)} wins!`:canPlay()?'Your turn':`${team(s.player)} is playing`;
 $('#mode-label').textContent=current.mode==='practice'?'Practice · Council vs Council':current.mode==='hotseat'?'Pass & play · Council':'Friendly duel · Council';
 $('#ap-number').textContent=s.ap;$('#ap-pips').innerHTML=Array.from({length:5},(_,i)=>`<i class="${i>=s.ap?'spent':''}"></i>`).join('');
 $('#undo').disabled=busy||!actions.length;$('#reset').disabled=busy||!actions.length;
 $('#submit').disabled=busy||!canPlay()||!view.joined;$('#submit').textContent=busy?'Working…':s.winner!==null?(actions.length?'Confirm victory →':'Battle complete'):!view.joined?'Waiting for friend':canPlay()?'Submit turn →':'Waiting for opponent';
 $('#deck-count').textContent=`${Math.max(0,s.remaining[view.side]-s.hand.length)} in reserve`;
 $('#announcement').classList.toggle('winner',s.winner!==null);
 $('#announcement').textContent=s.winner!==null?(actions.length?`${team(s.winner)} wins with this plan. Submit to confirm, or undo.`:`${team(s.winner)} Council wins the battle. Start another from Battles.`):!view.joined?'Share your invitation from Match options. Your friend has not joined yet.':!canPlay()?'Turn submitted and saved. You can leave and return later.':s.ap===0?'All five actions used. Submit your turn, or undo to try another plan.':actions.length?`${actions.length} action${actions.length===1?'':'s'} planned. Nothing is committed until you submit.`:current.mode==='practice'?'Practice battlefield · Your opponent responds when you submit.':'Deploy a hero on one of your two corner squares to begin.';
 $('#exchange').hidden=selected?.card===undefined||!legal.some(l=>l.action.type==='swap_card');$('#exchange').disabled=busy;
 $('#hint').textContent=selected?.card!==undefined?'Choose a highlighted square to use this reinforcement.':selected?.unit?'Blue: move · Red: attack · Green: heal or swap':'Select a hero or reinforcement to see legal actions.';
}
function renderInspector(){
 const el=$('#inspector');let kind,unit;
 if(selected?.unit){unit=view.state.units.find(u=>u.id===selected.unit);kind=unit?.kind;}
 if(selected?.card!==undefined)kind=view.state.hand[selected.card];
 if(!kind){el.innerHTML='<span class="eyebrow">FIELD NOTES</span><h2>Choose your next move.</h2><p>Inspect a hero to see its stats. Every move, attack, deployment, and item costs one action.</p>';return;}
 const st=unit?.stats||rulebook.units[kind];
 el.innerHTML=`<div class="inspector-portrait">${portrait(kind,unit?.owner??view.side,unit?.gear||[])}</div><span class="eyebrow">${unit?team(unit.owner)+' COUNCIL':'REINFORCEMENT'}</span><h2>${esc(name(kind))}</h2>${st?`<div class="stat-grid"><span><b>${unit?unit.hp+'/':''}${st.hp}</b>Health</span><span><b>${st.power}</b>Power</span><span><b>${st.reach}</b>Range</span><span><b>${st.move}</b>Movement</span><span><b>${st.physical}%</b>Armor</span><span><b>${st.magical}%</b>Resistance</span></div><p>${esc(st.ability)}</p>`:`<p>${esc(rulebook.items[kind].description)}</p>`}${unit?.gear.length?`<p>Equipped: ${unit.gear.map(name).join(', ')}</p>`:''}`;
}
function renderJournal(){const logs=view.history||[];$('#journal-count').textContent=`${logs.length} recent turns`;$('#journal').innerHTML=logs.length?[...logs].reverse().map(h=>`<div class="journal-turn ${h.player===1?'enemy':''}"><b>Turn ${h.turn} · ${team(h.player)}</b>${h.replay_available?`<button class="replay-button quiet" data-replay="${h.turn}">▶ Watch turn</button>`:''}<p>${h.events.filter(e=>e.label).map(e=>esc(e.label)).join(' → ')||'Passed'}${h.events.some(e=>e.type==='damage')?' · '+h.events.filter(e=>e.type==='damage').reduce((n,e)=>n+e.amount,0)+' damage':''}</p></div>`).join(''):'<p>Your submitted turns will appear here.</p>';}
async function select(selection){
 if(busy)return;selected=selection;legal=[];renderBoard();renderHand();renderInspector();renderControls();
 if(!canAct())return;
 const epoch=++selectionEpoch;
 try{const data=await api(`/matches/${current.id}/preview`,{method:'POST',body:{revision:view.revision,actions,selection}});if(epoch!==selectionEpoch)return;legal=(data.legal||[]).sort((a,b)=>['attack','heal','teleport','move','deploy','item','swap_card'].indexOf(a.action.type)-['attack','heal','teleport','move','deploy','item','swap_card'].indexOf(b.action.type));renderBoard();renderControls();}catch(e){toast(e.message);}
}
async function clickTile(x,y){if(busy)return;const choice=legal.find(l=>l.action.x===x&&l.action.y===y);if(choice&&canAct()){await perform(choice.action);return;}const unit=unitAt(x,y);if(unit){await select({unit:unit.id});}else{selected=null;legal=[];selectionEpoch++;render();}}
async function perform(action){
 if(!canAct())return;lock(true);selectionEpoch++;
 try{const data=await api(`/matches/${current.id}/preview`,{method:'POST',body:{revision:view.revision,actions:[...actions,action]}});const previousEvents=(view.events||[]).length;actions.push(action);view=data;legal=[];const keep=action.unit;selected=keep?{unit:keep}:null;saveDraft();render();animateEvents(data.events.slice(previousEvents));tone(action.type);}
 catch(e){toast(e.message);}finally{lock(false);renderHand();}
 if(selected&&canAct())await select(selected);
}
async function undo(reset=false){if(busy||!actions.length)return;lock(true);selectionEpoch++;const next=reset?[]:actions.slice(0,-1);try{const data=await api(`/matches/${current.id}/preview`,{method:'POST',body:{revision:view.revision,actions:next}});actions=next;view=data;selected=null;legal=[];saveDraft();render();}catch(e){toast(e.message);}finally{lock(false);renderHand();}}
async function submit(){if(busy||!canPlay())return;lock(true);selectionEpoch++;const previousHistory=view.history.length;
 try{view=await api(`/matches/${current.id}/submit`,{method:'POST',body:{revision:view.revision,actions}});actions=[];selected=null;legal=[];saveDraft();saveMatch({...current,result:view.state.winner===null?`Turn ${view.state.turn}`:`${team(view.state.winner)} victory`});render();tone('heal');if(current.mode==='hotseat'&&view.state.winner===null)offerHandoff();else if(current.mode==='practice'){const latest=view.history.slice(-1)[0];if(latest?.player===1)animateEvents(latest.events);}}
 catch(e){toast(e.message);if(e.status===409){await refresh(true);}}finally{lock(false);renderHand();}
}
function offerHandoff(){modal(`<h2>Pass to ${team(view.state.player)}.</h2><p>Your turn has been saved. Pass the device to the other player before revealing their hand.</p><button class="gold" id="handoff">I'm ready — reveal my hand</button>`);$('#handoff').onclick=async()=>{const old=current.token;current.token=current.other_token;current.other_token=old;persist();$('#modal').close();await openMatch(current);};}
async function refresh(force=false){if(!current||(!force&&(busy||actions.length||canPlay())))return;const id=current.id;try{const updated=await api(`/matches/${id}`);if(!current||current.id!==id||(!force&&actions.length))return;if(updated.revision!==view.revision||updated.joined!==view.joined||force){view=updated;actions=[];selected=null;legal=[];saveDraft();render();if(canPlay())toast('Your turn!');}}catch(e){if(force)toast(e.message);}}
function animateEvents(events){
 if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 const effects=$('#effects');let delay=0;
 for(const event of events){if(event.x===undefined)continue;
 setTimeout(()=>{if(!current)return;const cell=$(`#board [data-x="${event.x}"][data-y="${event.y}"]`);if(!cell)return;const r=cell.getBoundingClientRect(),p=effects.getBoundingClientRect();const cx=r.x-p.x+r.width/2,cy=r.y-p.y+r.height/2;
 if(event.type==='damage'||event.type==='heal'){const el=document.createElement('span');el.className='float-number '+(event.type==='heal'?'heal':'');el.textContent=event.amount?(event.type==='heal'?'+':'−')+event.amount:'✦';el.style.left=cx+'px';el.style.top=cy+'px';effects.append(el);setTimeout(()=>el.remove(),1100);cell.classList.add('impact');setTimeout(()=>cell.classList.remove('impact'),450);}
 if(event.type==='spell'){const el=document.createElement('span');el.className='spell-ring';el.style.left=cx+'px';el.style.top=cy+'px';effects.append(el);setTimeout(()=>el.remove(),800);}
 if(event.type==='attack'){const source=$(`#board [data-x="${event.from_x}"][data-y="${event.from_y}"]`);if(source){const sr=source.getBoundingClientRect();const el=document.createElement('i');el.className='projectile';el.style.left=(sr.x-p.x+sr.width/2)+'px';el.style.top=(sr.y-p.y+sr.height/2)+'px';effects.append(el);requestAnimationFrame(()=>requestAnimationFrame(()=>el.style.transform=`translate(${cx-(sr.x-p.x+sr.width/2)}px,${cy-(sr.y-p.y+sr.height/2)}px)`));setTimeout(()=>el.remove(),350);}}
 },delay);if(event.type==='attack'||event.type==='spell')delay+=180;
 }
}

async function watchReplay(turn){
 try{const replay=await api(`/matches/${current.id}/replay/${turn}`);let frame=0;let timer=null;
 modal(`<h2>Turn ${turn} · ${team(replay.player)}</h2><p>Watch the committed actions. Neither player's hand is revealed.</p><div id="replay-board" class="board replay-board"></div><p id="replay-caption"></p><div class="replay-controls"><button id="replay-prev" class="secondary">← Back</button><button id="replay-play" class="gold">▶ Play</button><button id="replay-next" class="secondary">Next →</button></div>`);
 const paint=()=>{const snapshot=replay.frames[frame];let html='';for(let y=0;y<5;y++)for(let x=0;x<9;x++){const u=snapshot.units.find(u=>u.x===x&&u.y===y);html+=`<div class="tile ${(x+y)%2?'alternate':''} ${rulebook.tiles[`${x},${y}`]||''}">${u?`<div class="unit ${u.hp===0?'ko':''}">${portrait(u.kind,u.owner,u.gear)}</div><span class="hp-text">${u.hp||'KO'}</span>`:''}</div>`;}$('#replay-board').innerHTML=html;$('#replay-caption').textContent=frame===0?'Before the turn':`Action ${frame} of ${replay.frames.length-1} · ${snapshot.events.filter(e=>e.label).map(e=>e.label).join(' · ')}`;$('#replay-prev').disabled=frame===0;$('#replay-next').disabled=frame===replay.frames.length-1;};
 const stop=()=>{clearInterval(timer);timer=null;if($('#replay-play'))$('#replay-play').textContent='▶ Play';};
 $('#replay-prev').onclick=()=>{stop();frame=Math.max(0,frame-1);paint();};$('#replay-next').onclick=()=>{stop();frame=Math.min(replay.frames.length-1,frame+1);paint();};
 $('#replay-play').onclick=()=>{if(timer){stop();return;}if(frame===replay.frames.length-1)frame=0;paint();$('#replay-play').textContent='Ⅱ Pause';timer=setInterval(()=>{if(!$('#modal').open||!$('#replay-board')){stop();return;}frame++;paint();if(frame===replay.frames.length-1)stop();},900);if(replay.frames.length===1)stop();};
 $('#modal').addEventListener('close',stop,{once:true});paint();
 }catch(e){toast(e.message);}
}

function showInvite(){if(!current.invite){toast('Your friend has already received their invitation, or this is not an invitation match.');return;}const link=`${location.origin}/#join=${current.id}&invite=${current.invite}`;modal(`<h2>Invite your opponent.</h2><p>This invitation claims the Crimson side once. Your own player key stays private.</p><input readonly aria-label="Invitation link" value="${esc(link)}"><button id="copy-invite" class="gold">Copy invitation</button><p><small>This build is available only on this Mac at localhost. Open the invitation in another browser profile to test it. Remote friends need a hosted address.</small></p>`);$('#copy-invite').onclick=()=>copy(link);}
async function copy(text){try{await navigator.clipboard.writeText(text);toast('Copied.');}catch{toast('Copy the link from the text field.');}}
function options(){modal(`<h2>Match options</h2><p>Keep your private player link to resume this side in another browser. Anyone with it can play your side.</p><input readonly aria-label="Private player link" value="${esc(location.origin+'/#match='+current.id+'&key='+current.token)}"><button id="copy-player" class="secondary">Copy player link</button>${current.invite?'<button id="invite-again" class="gold">Show invitation</button>':''}<hr><button id="refresh-match" class="secondary">Refresh saved match</button><button id="resign" class="quiet" style="color:#a64d48">Resign battle</button>`);$('#copy-player').onclick=()=>copy(`${location.origin}/#match=${current.id}&key=${current.token}`);if($('#invite-again'))$('#invite-again').onclick=showInvite;$('#refresh-match').onclick=()=>{if(actions.length){toast('Reset your draft before refreshing.');return;}$('#modal').close();refresh(true);};$('#resign').onclick=()=>{modal('<h2>Resign this battle?</h2><p>Your opponent will win. This cannot be undone.</p><button class="gold" id="confirm-resign">Resign battle</button>');$('#confirm-resign').onclick=async()=>{if(busy)return;lock(true);try{view=await api(`/matches/${current.id}/resign`,{method:'POST',body:{revision:view.revision}});actions=[];legal=[];selected=null;saveDraft();saveMatch({...current,result:`${team(view.state.winner)} victory`});$('#modal').close();render();}catch(e){toast(e.message);}finally{lock(false);renderHand();}};};}
function guide(){modal(`<h2>Welcome to the academy.</h2><p>Destroy all enemy crystals, or eliminate every enemy hero and reserve hero.</p><ol><li><b>Deploy:</b> select a hero from your hand, then a glowing corner square on your side.</li><li><b>Plan:</b> select a standing hero. Blue squares show moves, red squares attacks, green squares healing or a Ninja swap.</li><li><b>Equip:</b> select an item, then a friendly hero. Inferno targets a 3×3 area.</li><li><b>Finish the job:</b> heroes at zero health can be revived. Move onto a fallen hero to stomp it permanently.</li><li><b>Commit:</b> each action costs one of your five points. Undo or reset as much as you like before submitting.</li></ol><p><b>Premium squares:</b> crossed swords add 100 power; the shield adds 20% physical resistance; holding the purple crystal adds 300 damage to attacks against enemy crystals.</p><p>Hands refill after submission. Your opponent's hand is hidden. In practice mode you begin with a deployed squad and play against a simple sparring bot.</p><button class="gold" id="guide-done">Got it — let's play</button>`);$('#guide-done').onclick=()=>$('#modal').close();}
function fidelity(){modal(`<h2>Faithful numbers. Honest limits.</h2><p>This build reconstructs the original Council using launch-era stat tables. It is not yet a verified exact clone.</p><table><tr><th>Hero</th><th>HP</th><th>Power</th><th>Move</th><th>Range</th></tr>${Object.entries(rulebook.units).filter(([k])=>k!=='crystal').map(([k,u])=>`<tr><td>${u.name}</td><td>${u.hp}</td><td>${u.power}</td><td>${u.move}</td><td>${u.reach}</td></tr>`).join('')}</table><p>Wizard chain targeting, line-of-sight corners, crystal health, card exchange ordering, and some cross-version healing details remain provisional. Other factions are not implemented yet.</p><p>Sources: <a href="https://www.destructoid.com/a-starters-guide-to-robot-entertainments-hero-academy/" target="_blank" rel="noreferrer">2012 firsthand guide</a> · <a href="https://wyattcheng.blogspot.com/2012/02/" target="_blank" rel="noreferrer">Army inventory counts</a> · <a href="https://njustesen.github.io/njustesen/publications/justesen-masterthesis.pdf" target="_blank" rel="noreferrer">2015 research thesis</a>.</p><p>The full implementation ledger is in the repository's <code>docs/FIDELITY.md</code>. Artwork and sound are original approximations.</p>`);}
$('#home').onclick=e=>{e.preventDefault();if(!busy)lobby();};$('#back').onclick=()=>{if(!busy)lobby();};
$('#undo').onclick=()=>undo();$('#reset').onclick=()=>undo(true);$('#submit').onclick=submit;
$('#exchange').onclick=()=>{const action=legal.find(l=>l.action.type==='swap_card')?.action;if(action)perform(action);};
$('#journal').onclick=e=>{const button=e.target.closest('[data-replay]');if(button)watchReplay(Number(button.dataset.replay));};
$('#match-menu').onclick=options;$('#guide-button').onclick=guide;$('#fidelity-button').onclick=fidelity;
$('#sound-button').onclick=()=>{sound=!sound;$('#sound-button').textContent=sound?'Sound on':'Sound off';$('#sound-button').setAttribute('aria-pressed',String(sound));tone();};
for(const button of document.querySelectorAll('[data-create]'))button.onclick=()=>create(button.dataset.create);
window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='z'&&current&&!$('#modal').open){e.preventDefault();undo();}if(e.key==='Escape'&&!$('#modal').open){selected=null;legal=[];selectionEpoch++;if(view)render();}});
window.addEventListener('beforeunload',()=>saveDraft());
setInterval(()=>{if(!document.hidden)refresh();},8000);
async function start(){
 $('#hero-art').innerHTML=portrait('knight',0)+portrait('wizard',1)+portrait('crystal',0);
 try{rulebook=await api('/rules',{token:null});await api('/health',{token:null});$('#connection').textContent='● Academy online';
 const params=new URLSearchParams(location.hash.slice(1));
 if(params.has('join')){const mid=params.get('join'),invite=params.get('invite');modal('<h2>A friendly challenge.</h2><p>Join the Crimson Council and face your friend. The invitation can only be claimed once.</p><button id="join-battle" class="gold">Join battle</button>');$('#join-battle').onclick=async()=>{if(busy)return;lock(true);try{const m=await api(`/matches/${encodeURIComponent(mid)}/join`,{method:'POST',body:{invite},token:null});$('#modal').close();await openMatch(saveMatch(m));}catch(e){toast(e.message);}finally{lock(false);}};}
 else if(params.has('match')){let saved=saves.find(m=>m.id===params.get('match'));if(params.has('key'))saved=saveMatch({id:params.get('match'),token:params.get('key'),mode:saved?.mode||'friend'});if(saved)await openMatch(saved);}
 await renderMatches();
 }catch(e){$('#connection').textContent='Academy offline';toast(e.message);}
}
start();
