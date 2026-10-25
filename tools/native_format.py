"""Helpers for the tested OpenGothic format 56. ZIP directory entries are significant."""
import io,os,struct,tempfile,zipfile
class Reader:
 def __init__(self,b,p=0):self.b=b;self.p=p
 def skip(self,n):
  if n<0 or self.p+n>len(self.b):raise ValueError('Truncated native save data')
  self.p+=n
 def u(self):
  start=self.p;self.skip(4);return struct.unpack_from('<I',self.b,start)[0]
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
def inventory(b):
 r=Reader(b);n=r.u()
 if n>=10000:raise ValueError('Invalid inventory item count')
 records=[item(r) for _ in range(n)]
 for _ in range(r.u()):r.s();r.skip(4)
 for _ in range(2):r.s();r.skip(4)
 r.skip(16*4+1+8)
 if r.p!=len(b):raise ValueError('Trailing inventory data')
 return records
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
 """Validate a completed ZIP and publish it atomically without replacing a file.

 Hard-link creation is the commit point. Both paths are on the same filesystem;
 unsupported filesystems fail safely rather than falling back to an overwrite.
 This checks archive integrity, not engine revision or gameplay compatibility.
 """
 from pathlib import Path
 candidate,output=Path(candidate),Path(output)
 if candidate.resolve()==output.resolve():raise ValueError('Input and output must differ')
 data=candidate.read_bytes()
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
