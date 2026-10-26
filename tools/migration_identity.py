"""Source-bound NPC identities carried by the optional migration engine patch."""
import hashlib,re
from native_format import Reader

PATTERN=re.compile(r'OGI1:([0-9a-f]{64}):(NEWWORLD|OLDWORLD):([0-9]{1,10})\Z')

def source_fingerprint(dat,source):
    return hashlib.sha256(b'OGI1\0'+hashlib.sha256(dat).digest()+hashlib.sha256(source).digest()).hexdigest()

def decode_key(data):
    r=Reader(data)
    if r.u()!=1:raise ValueError('Unsupported NPC migration-key schema')
    try:key=r.s().decode('ascii')
    except UnicodeDecodeError:raise ValueError('Invalid NPC migration identity') from None
    r.end();match=PATTERN.fullmatch(key)
    if match is None:raise ValueError('Invalid NPC migration identity')
    fingerprint,world,index=match.groups()
    return fingerprint,world,int(index)

def map_npcs(entries,world,source,fingerprint,byname):
    prefix='worlds/'+world.lower()+'.zen/'
    mapped={};aliases=[];alias_keys=set()
    for path in entries:
        if path.startswith(prefix+'npc/') and path.endswith('/data') and path[:-4]+'migration-key' not in entries:
            raise ValueError('Missing stable identity for an active native NPC')
    for path,data in entries.items():
        if not path.startswith(prefix) or not path.endswith('/migration-key'):continue
        relative=path[len(prefix):].split('/')
        if len(relative)!=3 or relative[0] not in ('npc','npc_invalid') or not relative[1].isdigit():
            raise ValueError('Unexpected NPC migration-key location')
        found,source_world,index=decode_key(data)
        if found!=fingerprint:raise ValueError('Native NPC belongs to a different source migration')
        records=source['worlds'].get(source_world,[])
        if index>=len(records):raise ValueError('NPC migration index outside source population')
        original=records[index]
        node=path[:-len('migration-key')]
        npc=entries.get(node+'data',b'')
        r=Reader(npc);symbol=r.u()
        name=original['instance'].upper()
        if name not in byname or symbol!=byname[name]['index']:
            raise ValueError('NPC migration identity does not match instance symbol')
        if source_world!=world:
            if not original['player']:raise ValueError('NPC migration identity belongs to another world')
            alias_key=(source_world,index)
            if alias_key in alias_keys:raise ValueError('Duplicate player alias in visited world')
            alias_keys.add(alias_key)
            aliases.append((node,original))
            continue
        if index in mapped:raise ValueError('Duplicate NPC migration identity in world')
        mapped[index]=node
    missing=set(range(len(source['worlds'][world])))-set(mapped)
    if missing:raise ValueError('Missing stable NPC identities in '+world+': '+str(len(missing))+'; create a fresh migration with the identity engine patch')
    return [(mapped[index],original) for index,original in enumerate(source['worlds'][world])]+aliases


def strip_migration_keys(entries):
    from native_format import archive,pack_visited_world
    result={path:data for path,data in entries.items() if not path.endswith('/migration-key')}
    for path,data in list(result.items()):
        if path.startswith('worlds/') and path.endswith('.zip'):
            r=Reader(data);length=r.u()
            if length!=len(data)-4:raise ValueError('Invalid visited-world archive length')
            nested=archive(r.read(length))
            if any(name.endswith('/migration-key') for name in nested):
                result[path]=pack_visited_world({name:value for name,value in nested.items() if not name.endswith('/migration-key')})
    return result
