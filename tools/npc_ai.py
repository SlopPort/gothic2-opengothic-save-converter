"""Read the pinned NPC AI prefix and rebase its absolute calendar deadline.

Simulation-tick waits and animation clocks are deliberately preserved.
"""
import struct
from native_format import Reader,item,archive,pack_visited_world
from npc_state import npc_pose_state,npc_script_state

END_OF_TIME=(1<<63)-1

def skip_inventory(r):
    n=r.u()
    if n>=10000:raise ValueError('Invalid transformed inventory count')
    for _ in range(n):item(r)
    n=r.u()
    if n>len(r.b)//8:raise ValueError('Invalid transformed model count')
    for _ in range(n+2):r.s();r.skip(4)
    r.skip(16*4+1+8)

def npc_ai_prefix(data):
    r=Reader(data,npc_pose_state(data)['known_end'])
    r.skip(16+33*4)  # Perception clocks and PERC_Count callback indices.
    r.skip(30)  # Last hit and spell-casting state.
    transformed=r.number('<B')
    if transformed not in (0,1):raise ValueError('Invalid NPC transform flag')
    if transformed:
        r.skip(npc_script_state(data[r.p:])['prefix_size'])
        skip_inventory(r);r.skip(44*4)
        r.s();r.s();r.skip(16);r.s()
    waits_offset=r.p;r.skip(4*8)  # aniWaitTime, waitTime, faiWaitTime, outWaitTime.
    policy=r.number('<B')
    functions_offset=r.p;functions=[r.u() for _ in range(3)]
    start=r.number('<Q');offset=r.p;end=r.number('<q')
    started_offset=r.p;started=r.number('<B')
    if started not in (0,1):raise ValueError('Invalid NPC AI started flag')
    next_loop=r.number('<Q');previous=r.u()
    return dict(calendar_offset=offset,calendar_end=end,functions=functions,started=started,
                simulation_start=start,next_loop=next_loop,previous=previous,policy=policy,prefix_end=r.p,
                waits_offset=waits_offset,functions_offset=functions_offset,started_offset=started_offset)

def saved_ai_functions(source,byname):
    ai=source['ai'];kind='current' if ai.get('currentValid') else 'next' if ai.get('nextValid') else None
    if kind is None:return [0xffffffff]*3,False
    name=ai[kind+'Name'].upper()
    def resolve(name,required):
        symbol=byname.get(name)
        if symbol is None and not required:return 0xffffffff
        if not symbol or symbol['type']!=5 or symbol['count']!=0 or symbol['flags']&12:
            raise ValueError('Saved AI state is not a matching internal function: '+name)
        return symbol['index']
    # The archive's signed state indices are engine identifiers, not DAT indices.
    return [resolve(name,True),resolve(name+'_LOOP',False),resolve(name+'_END',False)],bool(ai.get(kind+'IsRoutine'))

def skip_ai_queue(r):
    n=r.u()
    if n>(len(r.b)-r.p)//32:raise ValueError('Invalid NPC AI queue count')
    for _ in range(n):
        action=r.u();r.skip(8);r.s();r.skip(12);r.s()
        if action==47:r.skip(4);r.s()
    r.skip(8)  # Format-56 synchronization counters.

def restart_saved_ai(data,source,byname,ticks):
    """Restart a saved script entrypoint; this does not resume original AI queues."""
    if source.get('attributes',[1])[0]<=0:return data  # Do not run death initialization twice.
    state=npc_ai_prefix(data);functions,is_routine=saved_ai_functions(source,byname)
    r=Reader(data,state['prefix_end']);skip_ai_queue(r);skip_ai_queue(r)
    result=bytearray(data)
    result[state['waits_offset']:state['waits_offset']+32]=bytes(32)
    struct.pack_into('<3I',result,state['functions_offset'],*functions)
    struct.pack_into('<Q',result,state['calendar_offset']-8,ticks)
    if not is_routine:struct.pack_into('<q',result,state['calendar_offset'],END_OF_TIME)
    struct.pack_into('<BQI',result,state['started_offset'],0,ticks,0xffffffff)
    result[state['prefix_end']:r.p]=bytes(24)  # Two empty queues and their sync counters.
    return bytes(result)

def verify_ai_restart(data,source,byname,ticks):
    if source.get('attributes',[1])[0]<=0:return
    state=npc_ai_prefix(data);functions,is_routine=saved_ai_functions(source,byname)
    if state['functions']!=functions or state['started'] or state['simulation_start']!=ticks or state['next_loop']!=ticks or state['previous']!=0xffffffff:
        raise ValueError('Saved AI restart fields differ from source initialization')
    if data[state['waits_offset']:state['waits_offset']+32]!=bytes(32):raise ValueError('Saved AI restart retains stale waits')
    if data[state['prefix_end']:state['prefix_end']+24]!=bytes(24):raise ValueError('Saved AI restart retains stale queues')
    if not is_routine and state['calendar_end']!=END_OF_TIME:raise ValueError('Unexpected non-routine AI deadline')

def rebase_npc_calendar(data,delta):
    state=npc_ai_prefix(data);end=state['calendar_end']
    if end==END_OF_TIME or delta==0:return data,False
    adjusted=end+delta
    if not -(1<<63)<=adjusted<END_OF_TIME:raise ValueError('NPC calendar deadline overflow')
    result=bytearray(data);struct.pack_into('<q',result,state['calendar_offset'],adjusted)
    return bytes(result),True

def rebase_world_calendars(entries,delta):
    result=dict(entries);changed=0
    for path,data in entries.items():
        if path.startswith('worlds/') and path.endswith('.zip'):
            nested,count=rebase_world_calendars(archive(data),delta)
            result[path]=pack_visited_world(nested);changed+=count
        elif path.startswith('worlds/') and '/npc' in path and path.endswith('/data'):
            result[path],did_change=rebase_npc_calendar(data,delta);changed+=did_change
    return result,changed
