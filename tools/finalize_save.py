"""Normalize a native OpenGothic export using original save data, without touching either input."""
import pathlib,json,struct,zipfile,sys,hashlib
import argparse
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--workspace',type=pathlib.Path,required=True);P.add_argument('--input',type=pathlib.Path,required=True);P.add_argument('--output',type=pathlib.Path,required=True)
args=P.parse_args();root=args.workspace.resolve()
if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
source=json.loads((root/'source-save.json').read_text())
u32=lambda n:struct.pack('<I',n)
def string(s):
    b=s.encode('latin1');return u32(len(b))+b
class Reader:
    def __init__(self,b):self.b=b;self.p=0
    def uint(self):v=struct.unpack_from('<I',self.b,self.p)[0];self.p+=4;return v
    def byte(self):v=self.b[self.p];self.p+=1;return v
    def string(self):n=self.uint();v=self.b[self.p:self.p+n];self.p+=n;return v.decode('latin1')
path=args.input;output=args.output
with zipfile.ZipFile(path) as archive:
    assert archive.testzip() is None
    entries={n:archive.read(n) for n in archive.namelist()}
header=Reader(entries['header']);assert header.b.startswith(b'OpenGothic/Save\0');header.p=len(b'OpenGothic/Save\0')
version=struct.unpack_from('<H',header.b,header.p)[0];header.p+=2
oldname=header.string();world=header.string();tm=header.b[header.p:header.p+36];header.p+=36
oldworldtime,oldplaytime=struct.unpack_from('<qQ',header.b,header.p);header.p+=16;game=header.byte();tail=header.b[header.p:]
assert version>=39 and game==2,(version,game)
day,hour,minute=source['time'];worldtime=((day*24+hour)*60+minute)*60000
entries['header']=b'OpenGothic/Save\0'+struct.pack('<H',version)+string('ORIGINAL SAVE IMPORT (EXPERIMENTAL)')+string(world)+tm+struct.pack('<qQ',worldtime,source['playSeconds']*1000)+bytes([game])+tail
# Keep native tick counters consistent with the freshly-created NPC timers; only restore world calendar.
session=bytearray(entries['game/session']);struct.pack_into('<q',session,8,worldtime);entries['game/session']=session
previous=Reader(entries['game/quests'])
for _ in range(previous.uint()):
    previous.string();previous.p+=2
    for __ in range(previous.uint()):previous.string()
# Keep the known-dialog pairs and the engine's guild attitude vector after the journal.
quest_tail=previous.b[previous.p:]
quests=bytearray(u32(len(source['quests'])))
for q in source['quests']:
    quests+=string(q['title'])+bytes([q['section'],q['status']])+u32(len(q['entries']))
    for e in reversed(q['entries']):quests+=string(e)
entries['game/quests']=quests+quest_tail
r=Reader(entries['game/daedalus']);out=bytearray(u32(r.uint()));expected=dict(source['symbols']);seen=set();changed=0
count=struct.unpack_from('<I',out)[0]
for _ in range(count):
    start=r.p;typ=r.uint()
    if typ in (1,2,3):
        name=r.string();n=r.uint();value_start=r.p
        if typ in (1,2):r.p+=n*4
        else:
            for __ in range(n):r.string()
        record=bytearray(r.b[start:r.p])
        if typ==2 and name in expected:
            vals=expected[name];assert len(vals)==n,(name,n,len(vals));seen.add(name)
            patch=b''.join(struct.pack('<i',v) for v in vals)
            if r.b[value_start:r.p]!=patch:changed+=1
            record[value_start-start:]=patch
        out+=record
    elif typ==7:
        cls=r.byte()
        if cls:
            r.string();r.p+=4
            if cls==3:r.p+=4
        out+=r.b[start:r.p]
    else:assert typ==0,typ;out+=r.b[start:r.p]
assert r.p==len(r.b),(r.p,len(r.b));assert seen==set(expected),(len(seen),len(expected))
entries['game/daedalus']=out
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for n,b in entries.items():archive.writestr(n,b)
with zipfile.ZipFile(output) as archive:assert archive.testzip() is None
report=dict(output=str(output),version=version,world=world,originalGlobalsVerified=len(seen),globalsRestoredAfterWorldInitialization=changed,journalTopics=len(source['quests']),calendar=source['time'],nativePlayTicksPreserved=True,entries=len(entries),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),limitations='Intermediate normalization only. Run world restoration and equipment restoration next; exact AI compatibility remains unsupported.')
(root/'normalization-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
