// Engine API stubs test lifecycle transitions, not gameplay compatibility.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname,'../mod/index.js'),'utf8');

function fixture({level=0,mask=0,identityApi=true,failCalls=false}={}) {
    const callbacks={};let calls=0;
    const hero={player:true,level:0};
    const source={world:'NEWWORLD',worlds:{NEWWORLD:[hero],OLDWORLD:[]},symbols:[],quests:[],infos:[],time:[1,8,0],migrationId:'synthetic'};
    const player={valid:true,level,experience:0,itemCount:()=>0};
    if(identityApi)player.setMigrationKey=()=>true;
    const state={mask};
    const context=vm.createContext({
        require:(name)=>name==='./snapshot.json'?source:{enableRemoteControl:false},
        player,world:{name:()=> 'newworld.zen'},
        debug:{signature:()=>true,symbol:()=>({value:state.mask}),setInfoKnown:()=>true,
               call:(name)=>{calls++;return failCalls&&name==='OGI_IMPORT_GLOBALS'?{ok:false,error:'synthetic failure'}:{ok:true,result:0};}},
        events:{on:(event,fn)=>{callbacks[event]=fn;}},
        ui:{tab:()=>{}},screen:{print:()=>{}},console:{log:()=>{},error:()=>{}},
    });
    vm.runInContext(script,context);
    return {player,state,callbacks,run:code=>vm.runInContext(code,context),calls:()=>calls};
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
console.log('Importer lifecycle checks passed');
