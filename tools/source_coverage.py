"""Summarize source behavior that the current migration does not reproduce exactly."""
def behavior_coverage(source):
    records=[npc for world in source['worlds'].values() for npc in world]
    known=[npc for npc in records if 'ai' in npc and 'news' in npc]
    return dict(npcs=len(records),behaviorMetadataNPCs=len(known),
                namedDailyRoutineNPCs=sum(bool(n.get('routine','').upper().startswith('RTN_')) for n in records),
                pendingExactReconstruction=dict(
                    currentAIStates=sum(bool(n['ai'].get('currentValid')) for n in known),
                    queuedNextAIStates=sum(bool(n['ai'].get('nextValid')) for n in known),
                    newsRecords=sum(len(n['news']) for n in known),
                    respawnFlags=sum(bool(n['ai'].get('respawn')) for n in known)),
                completeBehaviorCompatibility=False)
