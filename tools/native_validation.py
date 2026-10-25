"""Structural checks for the pinned format-56 migration layout, not gameplay certification."""
import struct
from native_format import Reader,archive,inventory_layout,item
from script_state import guild_table_offset,restore_globals
from npc_state import npc_script_state

MAGIC=b'OpenGothic/Save\0'
WORLDS={'newworld.zen','oldworld.zen'}

def required(entries,name):
    try:return entries[name]
    except KeyError:raise ValueError('Missing save entry: '+name) from None

def world_name(raw):
    try:name=raw.decode('ascii')
    except UnicodeDecodeError:raise ValueError('Non-ASCII world identifier') from None
    if name not in WORLDS:raise ValueError('Unsupported world: '+repr(name))
    return name

def validate_world(entries,name,active=False):
    prefix='worlds/'+name+'/'
    version=required(entries,prefix+'version')
    if version!=struct.pack('<H',56):raise ValueError('Unsupported world version: '+name)
    counts={}
    for group in ('npc','npc_invalid'):
        base=prefix+group+'/'
        children={key[len(base):].split('/')[0] for key in entries if key.startswith(base) and key!=base}
        if children!={str(i) for i in range(len(children))}:
            raise ValueError('Non-contiguous NPC identifiers: '+base)
        for index in children:
            node=base+index+'/'
            if required(entries,node)!=b'':raise ValueError('Nonempty NPC directory: '+node)
            try:npc_script_state(required(entries,node+'data'))
            except ValueError as error:raise ValueError(node+'data: '+str(error)) from error
            required(entries,node+'visual')
            # Empty inventories are omitted by Npc::save and optional on load.
        counts[group]=len(children)
    if active and not counts['npc']:raise ValueError('Active world has no NPC directories')
    inventories=0;stacks=0
    for path,data in entries.items():
        if path.startswith(prefix) and path.endswith('/inventory'):
            try:layout=inventory_layout(data)
            except ValueError as error:raise ValueError(path+': '+str(error)) from error
            inventories+=1;stacks+=len(layout['records'])
    r=Reader(required(entries,prefix+'items'));n=r.u()
    for _ in range(n):item(r)
    r.end()
    return dict(**counts,inventories=inventories,inventory_stacks=stacks,loose_item_stacks=n)

def validate_save(data):
    entries=archive(data)
    r=Reader(required(entries,'header'))
    if r.read(len(MAGIC))!=MAGIC:raise ValueError('Invalid OpenGothic save signature')
    version=r.number('<H')
    if version!=56:raise ValueError('Only the pinned format 56 layout is supported')
    r.s()  # Save title is deliberately absent from the validation report.
    current=world_name(r.s())
    r.skip(36)
    calendar=r.number('<q');r.number('<Q')
    if r.number('<B')!=2:raise ValueError('Only Gothic II saves are supported')
    visited=[world_name(r.s()) for _ in range(r.number('<H'))]
    r.end()
    if len(visited)!=len(set(visited)) or current in visited:
        raise ValueError('Duplicate or active world in visited-world list')
    session=Reader(required(entries,'game/session'))
    session.number('<Q');session_calendar=session.number('<q');session.number('<Q')
    if world_name(session.s())!=current:raise ValueError('Header/session world mismatch')
    session.end()
    if calendar!=session_calendar:raise ValueError('Header/session calendar mismatch')
    guild_table_offset(required(entries,'game/quests'))
    restore_globals(required(entries,'game/daedalus'),[])
    expected={'worlds/'+name+'.zip' for name in visited}
    actual={key for key in entries if key.startswith('worlds/') and key.endswith('.zip')}
    if expected!=actual:raise ValueError('Visited-world list/payload mismatch')
    worlds={current:validate_world(entries,current,active=True)}
    for name in visited:
        payload=entries['worlds/'+name+'.zip']
        nested=Reader(payload);length=nested.u()
        if length!=len(payload)-4:raise ValueError('Invalid visited-world archive length: '+name)
        worlds[name]=validate_world(archive(nested.read(length)),name)
    return dict(format=version,game=2,current_world=current,worlds=worlds,
                scope='Structural checks only; engine revision and gameplay compatibility are not certified')
