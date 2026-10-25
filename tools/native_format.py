"""Helpers for the tested OpenGothic format 56. ZIP directory entries are significant."""
import io,struct,zipfile
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
 r=Reader(b);n=r.u();assert n<10000
 records=[item(r) for _ in range(n)]
 for _ in range(r.u()):r.s();r.skip(4)
 for _ in range(2):r.s();r.skip(4)
 r.skip(16*4+1+8);assert r.p==len(b),(r.p,len(b))
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
