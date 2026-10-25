"""Helpers for the tested OpenGothic format 56. ZIP directory entries are significant."""
import io,os,struct,tempfile,zipfile
class Reader:
 def __init__(self,b,p=0):self.b=b;self.p=p
 def skip(self,n):
  if n<0 or self.p+n>len(self.b):raise ValueError('Truncated native save data')
  self.p+=n
 def read(self,n):
  start=self.p;self.skip(n);return self.b[start:self.p]
 def number(self,fmt):
  size=struct.calcsize(fmt)
  return struct.unpack(fmt,self.read(size))[0]
 def u(self):return self.number('<I')
 def end(self):
  if self.p!=len(self.b):raise ValueError('Trailing native save data')
 def s(self):
  n=self.u()
  if n>1000000:raise ValueError('Invalid native string length')
  start=self.p;self.skip(n);return self.b[start:self.p]
def item(r):
 start=r.p;symbol=r.u();r.skip(4);r.s();r.s();r.skip(3*4)
 r.skip((5+8+1+8+1+12+1+1+1+4+3)*4)
 r.s();r.s();r.s();r.skip(4);r.s();r.skip(5*4)
 r.s()
 for _ in range(6):r.s()
 r.skip((6+5)*4)
 amount=r.p;r.skip(4+12+2+64)
 return dict(symbol=symbol,raw=r.b[start:r.p],amount=amount-start,pos=amount-start+4,matrix=amount-start+18)
def inventory_layout(b):
 """Decode format-56 indices without invoking equip scripts or changing data."""
 r=Reader(b);n=r.u()
 if n>=10000:raise ValueError('Invalid inventory item count')
 records=[item(r) for _ in range(n)]
 def pointer():
  value=r.u()
  if value!=0xffffffff and value>=n:
   raise ValueError('Inventory pointer outside item table: '+str(value))
  return value
 models=[]
 count=r.u()
 if count>len(b)//8:raise ValueError('Invalid inventory model-slot count')
 for _ in range(count):models.append((r.s(),pointer()))
 attachments=[(r.s(),pointer()) for _ in range(2)]
 offset=r.p
 equipment=[pointer() for _ in range(16)]
 active=r.number('<B')
 # The engine writer emits 3..10 for the eight hotbar slots.
 if active not in (255,1,2,*range(3,11)):
  raise ValueError('Invalid active inventory slot')
 current,state=r.number('<i'),r.number('<i')
 r.end()
 return dict(records=records,models=models,attachments=attachments,
             equipment=equipment,equipment_offset=offset,active=active,
             current=current,state=state)

def inventory(b):
 return inventory_layout(b)['records']

def archive(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP entries')
  if z.testzip() is not None:raise ValueError('ZIP CRC check failed')
  return {n:z.read(n) for n in names}

def pack_archive(entries):
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,data in entries.items():z.writestr(name,data)
 return buf.getvalue()

def pack_visited_world(entries):
 payload=pack_archive(entries)
 return struct.pack('<I',len(payload))+payload


def publish_archive(candidate, output):
 """Publish a completed archive without replacing the input or an existing output."""
 from pathlib import Path
 candidate,output=Path(candidate),Path(output)
 if candidate.resolve()==output.resolve():raise ValueError('Input and output must differ')
 publish_bytes(candidate.read_bytes(),output)


def write_archive(entries,output):
 """Pack entries and publish atomically without replacing an existing file."""
 publish_bytes(pack_archive(entries),output)


def publish_bytes(data,output):
 """Validate ZIP integrity and commit using an exclusive same-filesystem hard link.

 Unsupported filesystems fail safely. This is not gameplay certification.
 """
 from pathlib import Path
 output=Path(output)
 entries=archive(data)
 for name,payload in entries.items():
  if name.startswith('worlds/') and name.endswith('.zip'):
   if len(payload)<4 or struct.unpack_from('<I',payload)[0]!=len(payload)-4:
    raise ValueError('Invalid visited-world archive length: '+name)
   archive(payload[4:])
 temporary=None
 try:
  with tempfile.NamedTemporaryFile(prefix='.save-converter-',suffix='.tmp',dir=output.parent,delete=False) as stream:
   temporary=Path(stream.name)
   stream.write(data)
   stream.flush()
   os.fsync(stream.fileno())
  os.link(temporary,output)
 finally:
  if temporary is not None:temporary.unlink(missing_ok=True)
