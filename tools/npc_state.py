"""Read and restore the INpc script prefix in the pinned format-56 NPC record.

Movement queues, animation, AI state, and relationships remain separate payloads.
"""
import math,struct
from native_format import Reader


def npc_script_state(data):
    r=Reader(data);offsets={}
    def ints(count,key=None):
        if key is not None:offsets[key]=r.p
        return [r.number('<i') for _ in range(count)]
    result=dict(symbol=r.u(),id=r.number('<i'))
    for _ in range(7):r.s()
    result['type']=ints(1,'type')[0];result['flags']=ints(1,'flags')[0]
    for name,count in (('attributes',8),('hitChance',5),('protection',8),('damage',8)):
        result[name]=ints(count,name)
    for name in ('damageType','guild','level'):
        result[name]=ints(1,name)[0]
    result['missions']=ints(5,'missions')
    result['fightTactic']=ints(1,'fightTactic')[0];r.skip(4*4)
    result['dailyRoutine']=ints(1,'dailyRoutine')[0]
    result['startAiState']=ints(1,'startAiState')[0]
    r.s();r.skip(3*4)
    result['aiVars']=ints(100,'aiVars')
    r.s()
    for name in ('xp','xpNext','lp','bodyStateOverride','noFocus'):
        result[name]=ints(1,name)[0]
    result['prefix_size']=r.p;result['offsets']=offsets
    return result


def restore_npc_script_state(data,source):
    native=npc_script_state(data);result=bytearray(data)
    arrays={'attributes':8,'protection':8,'aiVars':100,'missions':5}
    for name,count in arrays.items():
        if name not in source:continue
        values=source[name]
        if len(values)!=count:raise ValueError('Source NPC array length mismatch: '+name)
        struct.pack_into('<'+str(count)+'i',result,native['offsets'][name],*values)
    if 'hitChance' in source:
        if len(source['hitChance'])!=4:raise ValueError('Source hit-chance array length mismatch')
        struct.pack_into('<4i',result,native['offsets']['hitChance']+4,*source['hitChance'])
    if 'npcType' in source:struct.pack_into('<i',result,native['offsets']['type'],source['npcType'])
    for name in ('flags','guild','level','xp','xpNext','lp','fightTactic','bodyStateOverride'):
        if name in source:struct.pack_into('<i',result,native['offsets'][name],source[name])
    return bytes(result)


def verify_npc_script_state(data,source):
    native=npc_script_state(data)
    if 'npcType' in source and native['type']!=source['npcType']:
        raise ValueError('NPC script field differs from source: npcType')
    for name in ('attributes','protection','aiVars','missions','flags','guild','level','xp','xpNext','lp','fightTactic','bodyStateOverride'):
        if name in source and native[name]!=source[name]:raise ValueError('NPC script field differs from source: '+name)
    if 'hitChance' in source and native['hitChance'][1:]!=source['hitChance']:
        raise ValueError('NPC hit chances differ from source')


def npc_pose_state(data):
    prefix=npc_script_state(data);r=Reader(data,prefix['prefix_size']);offsets={}
    r.s();r.s();r.skip(4*4)
    offsets['modelFatness']=r.p;fatness=r.number('<f')
    offsets['position']=r.p;position=[r.number('<f') for _ in range(3)]
    offsets['angle']=r.p;angle=r.number('<f')
    offsets['modelScale']=r.p;scale=[r.number('<f') for _ in range(3)]
    r.skip(1);offsets['guildTrue']=r.p;guild=r.number('<i')
    offsets['talentSkills']=r.p;skills=[r.number('<i') for _ in range(22)]
    offsets['talentValues']=r.p;values=[r.number('<i') for _ in range(22)]
    r.skip(8);offsets['attitude']=r.p;attitude=r.number('<i')
    offsets['temporaryAttitude']=r.p;temporary=r.number('<i')
    if len(data)-12<r.p:raise ValueError('Missing NPC physics position')
    offsets['physicsPosition']=len(data)-12
    return dict(offsets=offsets,position=position,angle=angle,modelScale=scale,modelFatness=fatness,
                guildTrue=guild,talentSkills=skills,talentValues=values,attitude=attitude,
                temporaryAttitude=temporary,known_end=r.p)


def restore_npc_pose(data,source):
    state=npc_pose_state(data);result=bytearray(data);offsets=state['offsets']
    for name in ('position','modelScale'):
        if name in source:
            values=source[name]
            if len(values)!=3 or not all(math.isfinite(v) for v in values):raise ValueError('Invalid source NPC vector: '+name)
            struct.pack_into('<3f',result,offsets[name],*values)
            if name=='position':struct.pack_into('<3f',result,offsets['physicsPosition'],*values)
    if 'rotation' in source:
        rotation=source['rotation']
        if len(rotation)!=3 or any(len(row)!=3 for row in rotation):raise ValueError('Invalid source NPC rotation')
        angle=math.degrees(math.atan2(rotation[2][0],rotation[2][2]))
        if not math.isfinite(angle):raise ValueError('Invalid source NPC rotation')
        struct.pack_into('<f',result,offsets['angle'],angle)
    if 'modelFatness' in source:
        if not math.isfinite(source['modelFatness']):raise ValueError('Invalid source NPC model fatness')
        struct.pack_into('<f',result,offsets['modelFatness'],source['modelFatness'])
    for name in ('guildTrue','attitude','temporaryAttitude'):
        if name in source:struct.pack_into('<i',result,offsets[name],source[name])
    if 'talents' in source:
        skills=[0]*22;values=[0]*22;seen=set()
        for index,value,skill in source['talents']:
            if not isinstance(index,int) or not 0<=index<22 or index in seen:raise ValueError('Unsupported or duplicate source talent')
            seen.add(index);skills[index]=skill;values[index]=value
        struct.pack_into('<22i',result,offsets['talentSkills'],*skills)
        struct.pack_into('<22i',result,offsets['talentValues'],*values)
    return bytes(result)
