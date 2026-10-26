"""Reject unsupported or ambiguous source populations before generating an import."""
def validate_source(source):
    worlds=source.get('worlds')
    if source.get('world')!='NEWWORLD' or not isinstance(worlds,dict) or 'NEWWORLD' not in worlds or set(worlds)-{'NEWWORLD','OLDWORLD'}:
        raise ValueError('Supported scope: current NEWWORLD with NEWWORLD/OLDWORLD saves only')
    heroes=[]
    for world,records in worlds.items():
        if not isinstance(records,list):raise ValueError('Source NPC population must be an array')
        for npc in records:
            if not isinstance(npc,dict) or type(npc.get('player')) is not bool:
                raise ValueError('Source NPC player marker must be a boolean')
            if npc['player']:heroes.append((world,npc))
    if len(heroes)!=1 or heroes[0][0]!=source['world']:
        raise ValueError('Source must contain exactly one player in the current world; the converter will not guess a missing player')
    return heroes[0][1]
