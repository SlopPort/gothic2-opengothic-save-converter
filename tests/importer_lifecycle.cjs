// Engine API stubs test lifecycle transitions, not gameplay compatibility.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname,'../mod/index.js'),'utf8');

function fixture({level=0,mask=0,identityApi=true,failCalls=false,routineApi=true,routineFunction=null}={}) {
    const callbacks={};let calls=0;
    const hero={player:true,level:0,routineFunction,migrationKey:'synthetic',helper:'HELPER',inventory:{},slots:[],items:[],talents:[],position:[0,0,0],rotation:[[1,0,0],[0,1,0],[0,0,1]],attributes:[1]};
    const source={world:'NEWWORLD',worlds:{NEWWORLD:[hero],OLDWORLD:[]},symbols:[],quests:[],infos:[],time:[1,8,0],migrationId:'synthetic'};
    const player={valid:true,level,experience:0,itemCount:()=>0,setPuppet:()=>{},setFlags:()=>{},setPosition:()=>{},setRotation:()=>{},setOverlays:()=>{}};
    if(identityApi)player.setMigrationKey=()=>true;
    if(routineApi)player.setMigrationRoutine=()=>true;
    const state={mask,world:'NEWWORLD',travels:[]};
    const context=vm.createContext({
        require:(name)=>name==='./snapshot.json'?source:{enableRemoteControl:false},
        player,world:{name:()=>state.world.toLowerCase()+'.zen',setTime:()=>{},changeLevel:name=>{state.travels.push(name);}},
        npcs:{nearby:()=>[]},
        debug:{signature:()=>true,symbol:()=>({value:state.mask}),setInfoKnown:()=>true,setSymbol:(name,value)=>{state.mask=value;},
               call:(name)=>{calls++;return failCalls&&name==='OGI_IMPORT_GLOBALS'?{ok:false,error:'synthetic failure'}:{ok:true,result:0};}},
        events:{on:(event,fn)=>{callbacks[event]=fn;}},
        ui:{tab:()=>{}},screen:{print:()=>{}},console:{log:()=>{},error:()=>{}},
    });
    vm.runInContext(script,context);
    return {player,state,source,callbacks,run:code=>vm.runInContext(code,context),calls:()=>calls};
}

{
    const f=fixture({level:7,mask:3});f.callbacks.tick();
    assert.equal(f.run('status().phase'),'loaded migrated save');
    f.player.level=0;f.state.mask=0;f.callbacks['world:change']();
    assert.equal(f.run('status().finished'),false);
    assert.equal(f.run('status().phase'),'waiting');
    f.run('begin()');assert.equal(f.run('status().active'),true);
}
{
    const f=fixture({level:7,mask:3});f.callbacks.tick();f.callbacks['world:change']();
    assert.equal(f.run('status().active'),false);
    assert.equal(f.run('status().finished'),true);
}
{
    const f=fixture({identityApi:false});
    assert.throws(()=>f.run('begin()'),/identity.patch/);
    assert.equal(f.run('status().active'),false);
}
{
    const f=fixture({level:2});
    assert.throws(()=>f.run('begin()'),/NEW game/);
    assert.equal(f.run('status().active'),false);
}
{
    const f=fixture({failCalls:true});f.run('begin()');f.callbacks.tick();
    assert.equal(f.run('status().phase'),'failed');
    f.callbacks.tick();assert.equal(f.run('status().phase'),'failed');
    assert.throws(()=>f.run('begin()'),/Previous migration failed/);
    f.callbacks['world:change']();assert.equal(f.run('status().phase'),'waiting');
}
{
    const f=fixture({routineApi:false,routineFunction:'RTN_START_1'});
    assert.throws(()=>f.run('begin()'),/migration-routines.patch/);
    assert.equal(f.run('status().active'),false);
}
{
    const f=fixture({routineFunction:'RTN_START_1'});const order=[];
    Object.assign(f.player,{setPuppet:()=>{},setMigrationRoutine:name=>{order.push(name);return true;},
                           setFlags:()=>{},setPosition:()=>{},setRotation:()=>{},setOverlays:()=>{}});
    f.run("applyNpc(player,{migrationKey:'synthetic',routineFunction:'RTN_START_1',helper:'HELPER',inventory:{},slots:[],items:[],talents:[],position:[0,0,0],rotation:[[1,0,0],[0,1,0],[0,0,1]],attributes:[1]})");
    assert.deepEqual(order,['RTN_START_1']);
    f.player.setMigrationRoutine=()=>false;
    assert.throws(()=>f.run("applyNpc(player,{migrationKey:'synthetic',routineFunction:'RTN_START_1'})"),/Cannot restore daily routine/);
}
{
    const f=fixture();f.run('begin(true)');
    for(let i=0;i<12;i++)f.callbacks.tick();
    assert.equal(f.run('status().waitingForWorld'),'OLDWORLD');
    assert.deepEqual(f.state.travels,['oldworld.zen']);
    assert.equal(f.run('status().finished'),false);
    // Merely seeing the target name must not run the import before the load event.
    f.state.world='OLDWORLD';for(let i=0;i<3;i++)f.callbacks.tick();
    assert.equal(f.state.mask,1);
    f.callbacks['world:change']();for(let i=0;i<5;i++)f.callbacks.tick();
    assert.equal(f.state.mask,3);
    assert.deepEqual(f.state.travels,['oldworld.zen','newworld.zen']);
    assert.equal(f.run('status().waitingForWorld'),'NEWWORLD');
    f.player.valid=false;f.state.world='NEWWORLD';f.callbacks['world:change']();f.callbacks.tick();
    assert.equal(f.run('status().finished'),false);
    f.player.valid=true;for(let i=0;i<5;i++)f.callbacks.tick();
    assert.equal(f.run('status().finished'),true);
    assert.equal(f.run('status().waitingForWorld'),null);
}
{
    const f=fixture();delete f.source.worlds.OLDWORLD;f.run('begin(true)');
    for(let i=0;i<12;i++)f.callbacks.tick();
    assert.equal(f.run('status().finished'),true);assert.deepEqual(f.state.travels,[]);
}
{
    const f=fixture();f.source.worlds.ADDONWORLD=[];
    assert.throws(()=>f.run('begin(true)'),/supports New World and Old World only/);
    assert.equal(f.run('status().active'),false);
}
{
    const f=fixture();f.run('begin(true)');for(let i=0;i<12;i++)f.callbacks.tick();
    f.player.valid=false;f.run('transition.started=Date.now()-180001');f.callbacks.tick();
    assert.equal(f.run('status().phase'),'failed');
    assert.match(f.run('status().error'),/timed out/);
    assert.equal(f.run('status().waitingForWorld'),null);
}
console.log('Importer lifecycle checks passed');
