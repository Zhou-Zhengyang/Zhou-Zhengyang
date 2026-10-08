# 无头模拟：用 V8 加载 index.html 的游戏脚本，模拟玩家通关，定位波次推进 bug
import re
import json
from py_mini_racer import py_mini_racer

FILE = r'c:\Users\zzh\AppData\Roaming\Trae CN\User\workspaceStorage\1789223496002\external-files\home\0-mtyhj8bo-z6io\index.html'
html = open(FILE, encoding='utf-8').read()
m = re.search(r'<script>([\s\S]*?)</script>', html)
if not m:
    raise SystemExit('script block not found')
game_code = m.group(1)

setup = r'''
var __logs = [];
function print(s){ __logs.push(String(s)); }
var console = { log: function(){ print(Array.prototype.slice.call(arguments).map(String).join(' ')); } };
var setTimeout = function(fn){ return 0; };
var clearTimeout = function(){};
var requestAnimationFrame = function(fn){ return 0; };
// 万能 no-op 代理：充当 canvas 2d context
var noop = new Proxy(function(){}, {
  get: function(t, p){ if (p === Symbol.toPrimitive) return function(){ return 0; }; return noop; },
  apply: function(){ return noop; },
  set: function(){ return true; },
  construct: function(){ return noop; }
});
function makeEl(id){
  if (id === 'game') return { width:0, height:0, style:{}, addEventListener:function(){}, getContext:function(){ return noop; }, getBoundingClientRect:function(){ return {left:0, top:0, width:1280, height:720}; } };
  return { style:{}, classList:{ add:function(){}, remove:function(){}, contains:function(){ return false; } }, textContent:'', innerHTML:'', addEventListener:function(){}, offsetWidth:0 };
}
var __els = {};
var document = { getElementById: function(id){ if (!__els[id]) __els[id] = makeEl(id); return __els[id]; } };
function AudioContext(){ this.state = 'running'; this.currentTime = 0; this.destination = {}; }
AudioContext.prototype.resume = function(){};
AudioContext.prototype.createGain = function(){ return { connect:function(){}, gain:{ setValueAtTime:function(){}, exponentialRampToValueAtTime:function(){}, linearRampToValueAtTime:function(){}, value:0 } }; };
AudioContext.prototype.createOscillator = function(){ return { type:'', frequency:{ setValueAtTime:function(){}, exponentialRampToValueAtTime:function(){}, linearRampToValueAtTime:function(){}, value:0 }, connect:function(){}, start:function(){}, stop:function(){} }; };
AudioContext.prototype.createBuffer = function(ch, len){ return { getChannelData:function(){ return new Float32Array(len); } }; };
AudioContext.prototype.createBufferSource = function(){ return { buffer:null, connect:function(){}, start:function(){} }; };
AudioContext.prototype.createBiquadFilter = function(){ return { type:'', frequency:{ value:0 }, connect:function(){} }; };
var window = { addEventListener:function(){}, AudioContext: AudioContext };
'''

harness = r'''
muted = true;
var __run = '';
var __f = 0;
var _startWave = startWave;
startWave = function (n) { print('[' + __run + ' f' + __f + '] startWave(' + n + ')'); return _startWave(n); };
var _spawnBoss = spawnBoss;
spawnBoss = function (i) { print('[' + __run + ' f' + __f + '] spawnBoss(idx=' + i + ')'); return _spawnBoss(i); };
var _victory = victory;
victory = function () { print('[' + __run + ' f' + __f + '] *** VICTORY ***'); return _victory(); };
damagePlayer = function () {};   // 玩家无敌
var _killEnemy = killEnemy;

function runFrame() {
  game.time++;
  if (game.shake > 0) game.shake *= 0.88;
  if (game.slowmo > 0) game.slowmo--;
  var step = game.slowmo > 0 ? (game.time % 3 !== 0 ? 0 : 1) : 1;
  if (step) {
    updatePlayer();
    updateEnemies();
    updateBullets(bullets, true);
    updateBullets(enemyBullets, false);
    updatePickups();
    updateParticles();
    updateWave();
  } else {
    updateParticles();
  }
  updateHUD();
  render();
}

print('===== 方案A: 每90帧清空全部敌人（验证纯流程） =====');
__run = 'A';
startGame();
try {
  for (__f = 0; __f < 60000; __f++) {
    runFrame();
    if (__f % 90 === 0) while (enemies.length) _killEnemy(0);
    if (game.state !== 'playing') break;
  }
  print('A END: frame=' + __f + ' wave=' + game.wave + ' state=' + game.state + ' queue=' + game.spawnQueue.length + ' enemies=' + enemies.length);
} catch (err) {
  print('A CRASH frame=' + __f + ' wave=' + game.wave + ' err=' + err.stack);
}

print('===== 方案B: 自动瞄准+自动开火（模拟真实游玩） =====');
__run = 'B';
mouseDown = true;
startGame();
try {
  for (__f = 0; __f < 180000; __f++) {
    var tgt = null, bd = 1e9;
    for (var ei = 0; ei < enemies.length; ei++) {
      var d2 = dist(player.x, player.y, enemies[ei].x, enemies[ei].y);
      if (d2 < bd) { bd = d2; tgt = enemies[ei]; }
    }
    if (tgt) { mouseX = tgt.x; mouseY = tgt.y; } else { mouseX = W / 2; mouseY = H / 2; }
    runFrame();
    if (__f % 5000 === 0) print('B status f=' + __f + ' wave=' + game.wave + ' state=' + game.state + ' queue=' + game.spawnQueue.length + ' enemies=' + enemies.length);
    if (game.state !== 'playing') break;
  }
  print('B END: frame=' + __f + ' wave=' + game.wave + ' state=' + game.state + ' queue=' + game.spawnQueue.length + ' enemies=' + enemies.length);
} catch (err) {
  print('B CRASH frame=' + __f + ' wave=' + game.wave + ' err=' + err.stack);
}
'''

ctx = py_mini_racer.MiniRacer()
try:
    ctx.eval(setup + game_code + harness)
except Exception as e:
    print('EVAL ERROR:', e)

print(json.dumps(json.loads(ctx.eval('JSON.stringify(__logs)')), ensure_ascii=False, indent=1))
