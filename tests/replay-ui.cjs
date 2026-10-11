// Offline regression checks. Minimal DOM stubs exercise the generated page's
// calculations, event handlers and rendering; these are not visual browser tests.
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = new Map(), storage = new Map();
function element(key) {
  if (!elements.has(key)) elements.set(key, {
    value: key === '#mode' ? 'power' : '', max: '2000', hidden: false,
    innerHTML: '', textContent: '', style: {}, dataset: {}, events: {},
    addEventListener(type, fn) { (this.events[type] ||= []).push(fn); },
    setAttribute(k, v) { this[k] = v; }, removeAttribute(k) { delete this[k]; },
    insertAdjacentHTML(_, value) { this.innerHTML += value; },
    querySelectorAll() { return []; }, contains(x) { return x === this; },
    focus() { this.focused = true; },
    getBoundingClientRect() { return {left: 900, bottom: 400}; },
    offsetWidth: 420, offsetHeight: 350,
  });
  return elements.get(key);
}
const ctx = vm.createContext({
  console, setTimeout, clearTimeout,
  window: {addEventListener() {}, innerWidth: 1080, innerHeight: 800},
  document: {querySelector: element, querySelectorAll: () => [], addEventListener() {}},
  localStorage: {getItem: k => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,String(v))},
});
vm.runInContext(script, ctx);
const run = code => vm.runInContext(code, ctx);
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('PASS', name); }
run(`
  function fixture(slot=1) {
    const builds=Array.from({length:13},()=>['berserker_unit_id:4|5:0','berserker_unit_id:5|5:0']);
    return {playerSlot:slot,playerName:'Player '+slot,legion:'Mech',buildPerWave:builds,
      valuePerWave:Array(13).fill(380),mercenariesReceivedPerWave:Array.from({length:13},()=>['snail_unit_id']),
      mercenariesSentPerWave:Array.from({length:13},()=>['ghost_knight_unit_id','ghost_knight_unit_id','snail_unit_id'])};
  }
  const players=[1,2,5,6].map(fixture);
  R={g:{endingWave:13,version:'26.9.hf3'},P:players,by:Object.fromEntries(players.map(p=>[p.playerSlot,p]))};rw=12;
`);

test('right-click imports duplicate fighters, selected wave and RECEIVED mythium', () => {
  const board = {dataset:{playerSlot:'1'}};
  let prevented = false;
  element('#rview').events.contextmenu[0]({target:{closest:()=>board},preventDefault(){prevented=true;}});
  assert(prevented);
  assert.equal(run('cur'), 13);
  assert.equal(run('JSON.stringify(lineup)'), '[["Berserker",2]]');
  assert.equal(Number(element('#budget').value), 20); // Outgoing is 500, received is 20.
  assert.equal(storage.get('ltd2-budget'), '20');
  assert.equal(storage.get('ltd2-tab'), 'plan');
  assert.match(element('#replay-import-note').textContent, /收到.*20/);
});
test('zero-received import and draft reload retain zero and buy no mercenaries', () => {
  run('R.by[1].mercenariesReceivedPerWave[12]=[];importReplayBoard(1);loadDraft();renderPlan();');
  assert.equal(Number(element('#budget').value), 0);
  assert.equal(run('lastCombos.A.length'), 0);
  assert.equal(storage.get('ltd2-budget'), '0');
});
test('import into local draft does not write to a selected shared board', () => {
  run(`DB={collection(){throw Error('unexpected shared write')}};boardId='shared';dirty=true;importReplayBoard(1);DB=null;`);
  assert.equal(run('boardId'), '');
  assert.equal(run('dirty'), false);
});
test('unknown fighters are reported, not silently imported as known units', () => {
  run(`R.by[1].buildPerWave[12].push('future_unit_id:1|1:0');importReplayBoard(1);`);
  assert.match(element('#replay-import-note').textContent, /未收錄、未載入.*future/);
  assert.match(run('boardStrength(R.by[1],12,[]).unavailable'), /future/);
  run('R.by[1].buildPerWave[12].pop()');
});
test('attribute calculation and signed zero/positive/negative changes', () => {
  // W13: Berserker attacks fortified for 0.8 and takes impact at 0.8.
  assert.equal(run('boardStrength(R.by[1],12,[]).effective'), 380);
  assert.match(run(`powerCell(boardStrength(R.by[1],12,[]),'test')`), /\+0/);
  assert(run('boardStrength(R.by[1],3,[]).effective') > 380); // Swift wave
  assert(run('boardStrength(R.by[1],0,[]).effective') < 380); // Pierce wave
  assert.match(run(`powerCell(boardStrength(R.by[1],3,[]),'test')`), /power-positive/);
  assert.match(run(`powerCell(boardStrength(R.by[1],0,[]),'test')`), /power-negative/);
  run(`const c=boardStrength(R.by[1],12,[byMerc('Snail')]);const b=boardStrength(R.by[1],12,[]);`);
  assert.equal(run('c.effective'), run('b.effective')); // Same attack/armor as W13
  const tip = run(`powerCalculation(c,'wave + snail')`);
  assert.match(tip, /蝸牛 1/);
  assert.match(tip, /Berserker ×2/);
  assert.match(tip, /√\(A × D\)/);
  assert.match(tip, /0\.8000/);
  assert.match(tip, /1\.2500/);
});
test('missing mercenary data and unsupported waves show unavailable', () => {
  run(`R.by[1].mercenariesReceivedPerWave[12]=['unknown_merc'];`);
  assert.match(run('analysisCard(R.by[1])'), /資料不足/);
  run(`R.by[1].mercenariesReceivedPerWave[12]=['snail_unit_id'];`);
  assert.match(run('boardStrength(R.by[1],21,[]).unavailable'), /此波次/);
});
test('official HP/DPS weighting and enemy quantity are used without simulating skills', () => {
  assert.equal(run('b.model'), 'hp-dps');
  assert.equal(run('b.hp'), 3740);
  assert.equal(run('b.dps'), 106); // Public guide rounds Berserker DPS to 53.
  assert.equal(run('b.enemyHp'), 21000); // Six drill golems at 3500 HP.
  assert.equal(run('b.enemyDps'), 972);
  assert.equal(run('c.enemyHp'), 21240);
  assert.equal(run('c.enemyDps'), 979);
  assert(run('c.pressureRatio < b.pressureRatio'));
  assert.match(run(`powerCalculation(c,'test')`), /非守住機率/);
  // Mixed board weights attack by real DPS and survival by HP, not gold value.
  run(`const mixed=statStrength([FBY.berserker,FBY.zeus],12,[],365);`);
  const expectedAttack = (53*.8+53*1.15)/(53+53); // Zeus's base attack is Impact, not its magic skill.
  assert(Math.abs(run('mixed.attack') - expectedAttack) < 1e-12);
  assert.equal(run(`statStrength([FBY.berserker],12,[byMerc('Snail'),byMerc('Snail')],190).enemyHp`), 21480);
  run(`const lizardMix=statStrength([FBY.berserker],12,[byMerc('Lizard')],190);`);
  assert(Math.abs(run('lizardMix.attack') - (21000*.8+280*.85)/21280) < 1e-12);
  assert(Math.abs(run('lizardMix.defense') - 993/(972*.8+21*1.2)) < 1e-12);
});
test('missing stats and mixed-spawn waves visibly fall back without fabricated stats', () => {
  assert.equal(run('boardStrength(R.by[1],4,[]).model'), undefined);
  assert.match(run(`powerCell(boardStrength(R.by[1],4,[]),'test')`), /屬性備援/);
  assert.match(run(`powerCalculation(boardStrength(R.by[1],4,[]),'test')`), /小王/);
  run(`const savedBerserker=COMBAT.units['Fighter:berserker'];delete COMBAT.units['Fighter:berserker'];`);
  assert.match(run('boardStrength(R.by[1],12,[]).fallbackReason'), /HP／DPS/);
  run(`COMBAT.units['Fighter:berserker']=savedBerserker;`);
  assert.match(run(`combatStatsLine('Fighter','Berserker')`), /HP 1870 · DPS ≈53/);
  assert.match(run(`combatStatsLine('Fighter','Heroic Scrappy')`), /未匹配/);
});
test('four analysis cards and boards occupy the same grid in player order', () => {
  run('renderReplay()');
  const view = element('#rview').innerHTML;
  assert.equal((view.match(/class="replay-grid"/g)||[]).length, 1);
  assert.deepEqual([...view.matchAll(/data-analysis-slot="(\d+)"/g)].map(m=>m[1]), ['1','2','5','6']);
  assert.deepEqual([...view.matchAll(/data-player-slot="(\d+)"/g)].map(m=>m[1]), ['1','2','5','6']);
  assert.equal((view.match(/data-calculation=/g)||[]).length, 8);
  assert(!view.includes('同預算候選'));
  assert.match(html, /\.replay-grid\{[^}]*repeat\(4,minmax\(240px,1fr\)\)/);
});
test('hover, keyboard focus, and click display escaped calculation text', () => {
  const number = element('test-power');
  number.dataset.calculation = 'V = 380\nround(380 × 1.0000) = 380';
  const event = {target:{closest:()=>number}};
  for (const type of ['mouseover','focusin','click']) {
    element('#rview').events[type][0](event);
    assert.equal(element('#power-tooltip').hidden, false);
    assert.equal(element('#power-tooltip').textContent, number.dataset.calculation);
    assert.equal(number['aria-describedby'], 'power-tooltip');
    run('hidePowerTooltip()');
  }
  assert.equal(element('#power-tooltip').hidden, true);
});
console.log(`${passed} regression checks passed.`);
