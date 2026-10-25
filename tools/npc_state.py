"""Read the INpc script-state prefix in the pinned format-56 NPC record.

The following movement, visual, AI, and relationship payload is not decoded here.
"""
from native_format import Reader

def npc_script_state(data):
    r=Reader(data)
    def ints(count):return [r.number('<i') for _ in range(count)]
    result=dict(symbol=r.u(),id=r.number('<i'))
    for _ in range(7):r.s()  # Five display names, slot, and effect.
    result['type'],result['flags']=ints(2)
    for name,count in (('attributes',8),('hitChance',5),('protection',8),('damage',8)):
        result[name]=ints(count)
    result['damageType'],result['guild'],result['level']=ints(3)
    r.skip((5+5)*4)  # Missions, tactic, weapon, voice, pitch, body mass.
    result['dailyRoutine'],result['startAiState']=ints(2)
    r.s();r.skip(3*4)
    result['aiVars']=ints(100)
    r.s()
    result['xp'],result['xpNext'],result['lp']=ints(3)
    r.skip(2*4)
    result['prefix_size']=r.p
    return result
