// One-shot experimental migration. The original save is never written to.
const source = require('./snapshot.json');
const config = require('./config.json');
const token = config.remoteToken;
const heroSource = source.worlds[source.world].find(n => n.player);
let queue = [], active = false, finished = false, phase = 'waiting', error = '';
let progress = 0, total = 0, frozen = [], lastWorld = '', importedWorlds = {};
let report = { globals: 0, infos: 0, quests: 0, npcs: 0, spawned: 0, removed: 0, failed: [] };
function call(name, args, npc) {
    const result = debug.call(name, args || [], npc ? {self:npc} : {});
    if (!result.ok) throw new Error(name + ': ' + result.error);
    return result.result;
}
function status() {
    let hero = null;
    if (player.valid) hero = {level:player.level, xp:player.experience, hp:player.health, maxHp:player.maxHealth,
        mana:player.mana, maxMana:player.maxMana, strength:player.strength, dexterity:player.dexterity,
        guild:player.guild, gold:player.itemCount('ITMI_GOLD'), position:player.position, armor:player.armor,
        lp:debug.signature('OGI_GET_LP') ? call('OGI_GET_LP',[],player) : null};
    return {phase, active, finished, error, progress, total, world:world.name(), hero, report,
        capabilities:{helper:!!debug.signature('OGI_IMPORT_GLOBALS'),info:typeof debug.setInfoKnown,
            inventory:debug.signature('NPC_CLEARINVENTORY')}, importedWorlds};
}
function thaw() { for (const n of frozen) if(n.valid) n.setPuppet(false); frozen=[]; }
function fail(e) {error=String(e);phase='failed';active=false;queue=[];thaw();console.error(error);}
function enqueue(fn) {queue.push(fn);total++;}
function applyNpc(npc, saved) {
    if(typeof npc.setMigrationKey!=='function')throw new Error('Migration identity engine patch is required');
    if(!npc.setMigrationKey(saved.migrationKey))throw new Error('Cannot set stable NPC migration identity');
    npc.setPuppet(true);
    call('NPC_CLEARINVENTORY',[npc]);
    call(saved.helper,[],npc);
    for (const item of Object.keys(saved.inventory)) npc.addItem(item,saved.inventory[item]);
    const slots=Object.fromEntries(saved.slots);
    for(const name of [slots.ZS_TORSO,slots.ZS_LONGSWORD || slots.ZS_SWORD,slots.ZS_CROSSBOW || slots.ZS_BOW]){
        if(name){const item=debug.symbol(name);if(item)call('EQUIPITEM',[npc,item.index]);}
    }
    for(const item of saved.items){
        if(item.flags<0&&/^(ITAM_|ITRI_|ITBE_)/.test(item.instance)){
            const symbol=debug.symbol(item.instance);if(symbol)call('EQUIPITEM',[npc,symbol.index]);
        }
    }
    // Equipping may change attributes; write the saved values afterwards.
    call(saved.helper,[],npc);
    call('NPC_SETTRUEGUILD',[npc,saved.guildTrue]);
    npc.setFlags(saved.flags);
    for (const t of saved.talents) {
        call('NPC_SETTALENTVALUE',[npc,t[0],t[1]]);
        call('NPC_SETTALENTSKILL',[npc,t[0],t[2]]);
    }
    npc.setPosition(saved.position[0],saved.position[1],saved.position[2]);
    npc.setRotation(Math.atan2(saved.rotation[2][0],saved.rotation[2][2])*180/Math.PI);
    npc.setOverlays(saved.overlays || []);
    if (saved.attributes[0]<=0) npc.kill();
    npc.setPuppet(false);
}
function importWorld(name) {
    phase='NPCs '+name;
    const saved=source.worlds[name].filter(n=>!n.player);
    const present=npcs.nearby(10000000), groups={}, used=new Set();
    for(const n of present){n.setPuppet(true);frozen.push(n);(groups[n.instance]||(groups[n.instance]=[])).push(n);}
    for(const record of saved) enqueue(()=>{
        let candidates=(groups[record.instance]||[]).filter(n=>!used.has(n.id));
        candidates.sort((a,b)=>distance(a,record)-distance(b,record));
        let npc=candidates[0];
        if(!npc){npc=npcs.spawn(record.instance,...record.position,0,{puppet:true});if(npc)report.spawned++;}
        if(!npc)throw new Error('Cannot restore NPC '+record.instance);
        used.add(npc.id);applyNpc(npc,record);report.npcs++;
    });
    enqueue(()=>{
        for(const n of present)if(n.valid&&!used.has(n.id)){n.remove();report.removed++;}
        thaw();importedWorlds[name]=true;phase='world complete';
        const mask=debug.symbol('OGI_IMPORT_MASK');
        if(mask)debug.setSymbol('OGI_IMPORT_MASK',mask.value | (name==='NEWWORLD'?1:2));
    });
}
function distance(n,r) {return (n.x-r.position[0])**2+(n.y-r.position[1])**2+(n.z-r.position[2])**2;}
function resetIfFreshGame(allowFailed=false) {
    if(active||!player.valid||player.level!==0||player.experience!==0)return;
    const mask=debug.symbol('OGI_IMPORT_MASK');
    if(!mask||mask.value!==0||(!finished&&!(allowFailed&&error)))return;
    thaw();queue=[];active=false;finished=false;phase='waiting';error='';
    progress=0;total=0;importedWorlds={};
    report={globals:0,infos:0,quests:0,npcs:0,spawned:0,removed:0,failed:[]};
}
function begin() {
    resetIfFreshGame();
    if(active||finished)throw new Error('Already started');
    if(error)throw new Error('Previous migration failed; start a NEW game before retrying');
    if(!player.valid||player.level!==0||player.experience!==0)throw new Error('Import requires a NEW game');
    if(!debug.signature('OGI_IMPORT_GLOBALS')||typeof debug.setInfoKnown!=='function')throw new Error('Required import API missing');
    if(typeof player.setMigrationKey!=='function')throw new Error('Apply patches/migration-identity.patch to the migration engine');
    if(!source.migrationId)throw new Error('Prepare a fresh migration workspace');
    active=true;phase='globals';
    enqueue(()=>{call('OGI_IMPORT_GLOBALS');report.globals=source.symbols.length;});
    for(const q of source.quests)enqueue(()=>{
        quests.create(q.title,q.title,q.section);
        for(const entry of q.entries.slice().reverse())quests.addEntry(q.title,entry);
        if(q.status>=1)quests.setStatus(q.title,q.status);report.quests++;
    });
    for(let start=0;start<source.infos.length;start+=40)enqueue(()=>{
        for(const info of source.infos.slice(start,start+40)) {
            if(!debug.setInfoKnown(info[0],info[1]))report.failed.push('info:'+info[0]);
            report.infos++;
        }
    });
    enqueue(()=>{applyNpc(player,heroSource);world.setTime(source.time[1],source.time[2]);phase='hero ready';});
    enqueue(()=>importWorld(source.world));
}
events.on('tick',()=>{
    resetIfFreshGame();
    if(!active&&!finished&&player.valid){
        const saved=debug.symbol('OGI_IMPORT_MASK');
        if(saved&&saved.value){finished=true;phase='loaded migrated save';importedWorlds.NEWWORLD=!!(saved.value&1);importedWorlds.OLDWORLD=!!(saved.value&2);}
    }
    if(!active||!player.valid)return;
    try{
        if(queue.length){const task=queue.shift();task();progress++;}
        else {
            active=false;finished=true;phase='complete';
            screen.print('Experimental import complete. Save to a NEW slot; offline finalization is still required.');
            console.log(JSON.stringify(status()));
        }
    }catch(e){fail(e);}
});
// The second visited world is migrated on its first entry, then persisted by the engine's normal save.
events.on('world:change',()=>{
    resetIfFreshGame(true);
    if(!finished)return;
    const name=world.name().split(/[\\/]/).pop().replace(/\.ZEN$/i,'').toUpperCase();
    if(source.worlds[name]&&!importedWorlds[name]){active=true;finished=false;importWorld(name);}
});
ui.tab('Original save import',()=>{
    ui.textWrapped('Experimental migration into a NEW game. This stage restores script state and NPCs. Containers and world objects are restored later by the offline tools. Keep your original saves.');
    ui.text(phase+' '+progress+'/'+total);
    if(error)ui.textWrapped(error);
    if(!active&&!finished&&ui.button('Import into a NEW game',-1,ui.fontSize()*2.3))try{begin();}catch(e){fail(e);}
    if(finished) {
        if(ui.button('Restore player position and equipment'))try{applyNpc(player,heroSource);}catch(e){fail(e);}
        if(source.worlds.OLDWORLD&&ui.button('Visit Old World (migration session only)'))world.changeLevel('oldworld.zen','START');
        if(ui.button('Return to New World (migration session only)'))world.changeLevel('newworld.zen','START');
    }
});
if(config.enableRemoteControl) {
net.listen(config.remotePort);
events.on('net:message',({peer,data})=>{
    try {
        const msg=JSON.parse(data);if(msg.token!==token){net.disconnect(peer);return;}
        if(msg.command==='begin')begin();
        if(msg.command==='repairHero'&&finished)applyNpc(player,heroSource);
        if(msg.command==='visitOld'&&finished)world.changeLevel('oldworld.zen','START');
        if(msg.command==='visitNew'&&finished)world.changeLevel('newworld.zen','START');
        net.send(peer,JSON.stringify(status()));
    }catch(e){net.send(peer,JSON.stringify({error:String(e)}));}
});
}
events.on('shutdown',()=>{thaw();if(config.enableRemoteControl)net.close();});
console.log('Experimental Steam save importer ready; no changes until explicitly started.');
