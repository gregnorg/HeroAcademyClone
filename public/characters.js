// Original rounded storybook characters. All shapes are authored for this game.
const dwarfs=['paladin','gunner','grenadier','engineer','annihilator'];
const elves=['void_monk','impaler','necromancer','priestess','wraith','phantom'];
export const heroes=['knight','archer','wizard','cleric','ninja',...dwarfs,...elves];
let serial=0;
export function character(kind,side,gear=[]){
 const id='hero'+(++serial), dwarf=dwarfs.includes(kind), elf=elves.includes(kind), ghost=['wraith','phantom'].includes(kind);
 const blue=side===0, coat=blue?'#347fc2':'#c75363', highlight=blue?'#9ee7ff':'#ffc3ba', skin=elf?'#bea9df':'#f5bd8c', edge='#353044', hair=dwarf?'#b96637':'#68442e';
 const outline=`stroke="${edge}" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"`;
 const defs=`<defs><linearGradient id="${id}coat" x2=".7" y2="1"><stop stop-color="${highlight}"/><stop offset=".5" stop-color="${coat}"/><stop offset="1" stop-color="${blue?'#23527e':'#813c53'}"/></linearGradient><radialGradient id="${id}skin" cx=".35" cy=".25" r=".8"><stop stop-color="${elf?'#e6d7fb':'#ffe3b4'}"/><stop offset="1" stop-color="${skin}"/></radialGradient><linearGradient id="${id}metal" x2=".8" y2="1"><stop stop-color="#f0f4ef"/><stop offset=".5" stop-color="#adbccb"/><stop offset="1" stop-color="#637184"/></linearGradient></defs>`;
 const face=`<g class="face"><ellipse cx="50" cy="34" rx="21" ry="22" fill="url(#${id}skin)" ${outline}/><ellipse cx="35" cy="42" rx="5" ry="3" fill="#d67888" opacity=".35"/><ellipse cx="66" cy="42" rx="5" ry="3" fill="#d67888" opacity=".35"/><g class="eyes"><ellipse cx="41" cy="33" rx="5" ry="6.5" fill="#fff9ea"/><ellipse cx="60" cy="33" rx="5" ry="6.5" fill="#fff9ea"/><ellipse cx="43" cy="34" rx="2.7" ry="4" fill="${edge}"/><ellipse cx="62" cy="34" rx="2.7" ry="4" fill="${edge}"/><circle cx="44" cy="32" r="1" fill="white"/><circle cx="63" cy="32" r="1" fill="white"/></g><path d="M46 43q5 6 11-1" fill="none" stroke="#9a5660" stroke-width="2" stroke-linecap="round"/><ellipse cx="51" cy="39" rx="4" ry="3" fill="${skin}"/></g>`;
 const boots=`<ellipse cx="36" cy="86" rx="12" ry="7" fill="#504454" ${outline}/><ellipse cx="66" cy="86" rx="12" ry="7" fill="#504454" ${outline}/>`;
 const torso=`<path d="M31 54Q22 63 25 81Q50 91 76 81Q79 64 68 54Q51 46 31 54Z" fill="url(#${id}coat)" ${outline}/><path d="M29 73q22 8 44 0" fill="none" stroke="#714e3a" stroke-width="7"/><rect x="45" y="70" width="12" height="9" rx="3" fill="#edc777" ${outline}/><path d="M29 56q-13 7-11 16m54-16q12 7 11 16" fill="none" stroke="${coat}" stroke-width="13" stroke-linecap="round"/><circle cx="18" cy="72" r="7" fill="${skin}" ${outline}/><circle cx="83" cy="72" r="7" fill="${skin}" ${outline}/>`;
 const beard=`<path d="M31 40Q34 51 48 46Q65 51 70 40Q74 66 56 74L50 68 44 74Q28 65 31 40Z" fill="${hair}" ${outline}/><path d="M36 48q7 8 14 0q9 8 16 0M43 56q-2 7 4 11m10-12-3 10" fill="none" stroke="#e7a05a" stroke-width="2" stroke-linecap="round"/>`;
 const elfEars=elf?`<path d="M31 29Q16 15 19 31L32 43m37-14q15-14 12 2L68 43" fill="${skin}" ${outline}/>`:'';
 let back='', hat='', prop='', overlay='';
 if(kind==='knight'||kind==='paladin'){
  hat=`<path d="M29 31Q23 5 49 6Q77 3 73 33L64 25Q49 17 36 27Z" fill="url(#${id}metal)" ${outline}/><path d="M46 9Q45-2 65 3Q58 10 54 16" fill="${coat}" ${outline}/><circle cx="31" cy="32" r="5" fill="#dbb868"/>`;
  prop=`<path d="M9 56Q23 48 36 57L34 76Q24 88 14 78Z" fill="url(#${id}coat)" stroke="#f6d587" stroke-width="3"/><path d="M23 58v18m-7-10h14" stroke="#ffdf99" stroke-width="4" stroke-linecap="round"/>`+(kind==='paladin'?`<path d="M82 75V39" stroke="#8f643d" stroke-width="6"/><rect x="69" y="25" width="26" height="19" rx="6" fill="url(#${id}metal)" ${outline}/><path d="M81 29v11m-5-5h10" stroke="#f6d587" stroke-width="3"/>`:`<path d="M82 63V22l5-10 5 10v41" fill="url(#${id}metal)" ${outline}/><path d="M76 64h22m-11 0v13" stroke="#d6ac59" stroke-width="5" stroke-linecap="round"/>`);
 }
 if(kind==='archer'||kind==='impaler'){
  back=`<path d="M29 26Q24 2 51 5Q79 0 73 54L63 61 36 51Z" fill="${kind==='impaler'?'#e9e4f2':'#a66636'}" ${outline}/>`;
  hat=`<path d="M28 24Q31 4 54 8l20 17Q50 18 28 30Z" fill="${coat}" ${outline}/><path d="M62 14Q68 1 80 5L68 20" fill="#ffe3a2" ${outline}/>`;
  prop=kind==='archer'?`<path d="M81 38Q105 59 81 83" fill="none" stroke="#d8a363" stroke-width="5"/><path d="M81 38l3 22-3 23m-29-23h41" fill="none" stroke="#ffedb7" stroke-width="2"/><path d="M92 56l7 4-7 4" fill="#c5e3ed"/>`:`<path d="M86 87V26" stroke="#987aa9" stroke-width="5"/><path d="M86 10q-1 11-10 20l10-4 10 4q-9-9-10-20Z" fill="#a4edc7" ${outline}/>`;
 }
 if(kind==='wizard'||kind==='necromancer'){
  hat=kind==='wizard'?`<path d="M25 25Q37 17 42 4Q44-1 53 4l19 23Q46 19 25 25Z" fill="${coat}" ${outline}/><path d="M23 27q26-10 51 1" fill="none" stroke="#efcb73" stroke-width="6"/>`:`<path d="M26 31Q26 8 44 6Q61-4 74 28L60 20 43 19Z" fill="#50405f" ${outline}/>`;
  overlay=kind==='wizard'?`<path d="M33 43q9 6 17 0q8 6 17-1Q66 66 50 72Q34 65 33 43Z" fill="#faf1db" ${outline}/><path d="M43 52q-2 8 6 12" fill="none" stroke="#d8cdb6" stroke-width="2"/>`:'';
  prop=`<path d="M17 86l5-52" stroke="#947057" stroke-width="5" stroke-linecap="round"/><circle cx="23" cy="28" r="11" fill="${kind==='wizard'?'#a3def3':'#b5edc5'}" ${outline}/><path d="M17 25q5-6 10-2" fill="none" stroke="#fff9db" stroke-width="3"/>`;
 }
 if(kind==='cleric'||kind==='priestess'){
  back=`<path d="M25 44Q19 4 50 5Q82 3 76 53L62 48 35 53Z" fill="#f5ecd7" ${outline}/>`;
  hat=`<path d="M30 23Q50 12 70 23L61 12 50 6 39 12Z" fill="${coat}" ${outline}/><circle cx="50" cy="17" r="4" fill="#f9dc8d"/>`;
  prop=`<path d="M83 84V35" stroke="#d1b577" stroke-width="5"/><circle cx="83" cy="28" r="10" fill="#a3dfc1" stroke="#f6d78e" stroke-width="4"/><path d="M83 22v12m-6-6h12" stroke="#fff7d8" stroke-width="3"/>`;
 }
 if(kind==='ninja'){
  hat=`<path d="M28 29Q25 4 50 5Q77 4 73 28L64 22H38Z" fill="#3c3a55" ${outline}/><path d="M29 25h43" stroke="${coat}" stroke-width="6"/><path d="M29 25Q13 19 10 30q10-3 20 1" fill="${coat}"/>`;
  overlay=`<path d="M29 39q22 7 43 0Q68 57 51 58Q33 55 29 39Z" fill="#3c3a55" ${outline}/>`;
  prop=`<path d="M23 73L9 39l1-11 9 10 13 31m45 0 12-29 8-8-1 13-11 28" fill="url(#${id}metal)" ${outline}/>`;
 }
 if(dwarf&&!['paladin'].includes(kind)){
  hat=kind==='engineer'?`<path d="M26 28Q24 7 49 8Q76 5 75 28Z" fill="#d6a654" ${outline}/><path d="M24 27h53" stroke="#866447" stroke-width="6"/><g fill="#a8dded" stroke="#665369" stroke-width="4"><circle cx="38" cy="25" r="8"/><circle cx="61" cy="25" r="8"/></g>`:`<path d="M25 27Q27 7 49 7Q75 5 76 28L61 22 37 23Z" fill="${coat}" ${outline}/><path d="M29 19q20-9 41 0" stroke="#e8b968" stroke-width="4" fill="none"/>`;
  if(kind==='engineer')prop=`<path d="M79 80l8-30" stroke="#8298a7" stroke-width="9"/><path d="M83 52q-10-11-1-18l3 10 8-1 2-11q9 13-4 22" fill="#c3d1d6" ${outline}/>`;
  if(kind==='gunner'||kind==='annihilator')prop=`<path d="M53 66L78 48 95 49 94 63 67 77Z" fill="#8b6445" ${outline}/><path d="M73 47Q86 41 99 48v15Q85 69 73 61Z" fill="url(#${id}metal)" ${outline}/><ellipse cx="96" cy="55" rx="5" ry="8" fill="#313342"/><path d="M62 63l8 7" stroke="#edc77a" stroke-width="6"/>`;
  if(kind==='grenadier')prop=`<circle cx="82" cy="67" r="13" fill="#5d6575" ${outline}/><path d="M81 55q-6-16 5-18" fill="none" stroke="#b99764" stroke-width="4"/><path d="M86 31l2 7 7-2-6 7" fill="#ffd16b" stroke="#ef9f4f" stroke-width="2"/><path d="M75 62q4-6 9-3" stroke="#b5c6d3" stroke-width="3" fill="none"/>`;
 }
 if(kind==='annihilator'){
  back=`<rect x="18" y="40" width="60" height="40" rx="14" fill="url(#${id}metal)" ${outline}/><path d="M20 41V25m54 17V23" stroke="#6b7382" stroke-width="8" stroke-linecap="round"/>`;
  hat=`<path d="M24 29Q25 5 50 6Q76 5 77 29L64 23H37Z" fill="url(#${id}metal)" ${outline}/><path d="M28 26h45" stroke="${coat}" stroke-width="5"/><circle cx="51" cy="15" r="5" fill="#ffd17a" ${outline}/>`;
  prop=`<path d="M51 66L76 47 99 49 101 69 74 79Z" fill="url(#${id}metal)" ${outline}/><ellipse cx="96" cy="59" rx="8" ry="12" fill="#3c3a4c" stroke="#e5c580" stroke-width="4"/><ellipse cx="96" cy="59" rx="4" ry="7" fill="#f4aa66"/><path d="M68 54l4 21" stroke="${coat}" stroke-width="6"/>`;
 }
 if(kind==='void_monk'){
  hat=`<path d="M28 25Q31 8 50 9Q73 7 73 26" fill="#413452" ${outline}/><path d="M31 24h39" stroke="${coat}" stroke-width="5"/>`;
  prop=`<circle cx="16" cy="70" r="12" fill="#a0f0c4" opacity=".65"/><circle cx="85" cy="70" r="12" fill="#a0f0c4" opacity=".65"/><path d="M11 64q5-7 10 0m58 0q5-7 10 0" stroke="#efffde" stroke-width="3" fill="none"/>`;
 }
 let drawing=back+boots+torso+elfEars+`<g class="hero-head">${face}${hat}${dwarf&&kind!=='engineer'&&kind!=='paladin'?beard:''}${overlay}</g>`+prop;
 if(ghost)drawing=`<path d="M20 87Q26 73 25 43Q21 8 50 7Q80 6 76 42Q74 68 87 87Q75 80 68 90Q57 82 50 94Q40 82 30 91Z" fill="${kind==='phantom'?'#7cd7be':'#55406b'}" ${outline}/><ellipse cx="51" cy="34" rx="20" ry="21" fill="#302c47"/><g class="eyes" fill="#b0ffe0"><ellipse cx="42" cy="34" rx="5" ry="7"/><ellipse cx="61" cy="34" rx="5" ry="7"/></g><path d="M44 49q8 6 14-1" fill="none" stroke="#92d4bd" stroke-width="2"/><path d="M28 54q-22 5-19 22l10-8m56-13q23 4 17 22l-8-10" fill="none" stroke="#9be8c3" stroke-width="8" stroke-linecap="round"/><path d="M40 62q11 8 22 0l-10 21Z" fill="${coat}"/>`;
 if(gear.includes('sword'))drawing+=`<circle cx="51" cy="67" r="5" fill="#ffe095" stroke="#8c674c" stroke-width="2"/>`;
 if(gear.includes('scroll'))drawing+=`<path class="enchanted" d="M13 14l3-7 3 7 7 3-7 3-3 7-3-7-7-3Z" fill="#ffe697"/>`;
 return `<svg viewBox="0 0 110 100" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${defs}<ellipse cx="52" cy="92" rx="31" ry="5" fill="#172331" opacity=".22"/><g class="character-body">${drawing}</g></svg>`;
}
