"""Read vector tables from canonical toolkit PRGs for exact renderer comparisons.

This is not an arbitrary PRG importer: it requires the toolkit pointer layout,
screen/HUD initialization signatures, unique metadata layout and exact clear
coverage. Camera, sampling, visibility and source pixels are preserved.
"""
from pathlib import Path
import re
from .pipeline import FrameBuild,decode_record_points
from .font import bitmap_text

def extract(path):
 b=Path(path).read_bytes()
 if len(b)<3:raise ValueError('truncated PRG')
 load=int.from_bytes(b[:2],'little');end=load+len(b)-2
 if end>65536:raise ValueError('PRG exceeds address space')
 ram=bytearray(65536);ram[load:end]=b[2:]
 def get(p,n):
  if not (load<=p<=p+n<=end):raise ValueError('read range')
  return ram[p:p+n]
 hits=[]
 for n in range(1,65):
  a=ram[0x1600:0x1600+4*n];cp=[a[i]+256*a[n+i] for i in range(n)];lp=[a[2*n+i]+256*a[3*n+i] for i in range(n)]
  if cp[0]!=0x4800 or not all(0x4800<=p<0x6000 for p in cp) or any(a>=b for a,b in zip(cp,cp[1:])):continue
  for colors in (False,True):
   try:
    fs=[]
    for i,(p,q) in enumerate(zip(cp,lp)):
     count=get(p,1)[0];p+=1;clear=[tuple(get(p+3*j,3)) for j in range(count)];p+=3*count
     spans=[]
     if colors:
      count=get(p,1)[0];p+=1;spans=[tuple(get(p+4*j,4)) for j in range(count)];p+=4*count
     if i+1<n and p!=cp[i+1]:raise ValueError('metadata ends')
     if not (0x4800<=q<0x6000 or 0x8000<=q<0xc800):raise ValueError('line arena')
     rc=get(q,1)[0];q+=1;recs=[];points=set()
     for _ in range(rc):
      h=get(q,4);axis=(h[3]>>6)&1;phase=(h[3]>>3)&7 if axis else h[3]&7
      if not 2<=h[2]<=127:raise ValueError('run length')
      size=4+(phase+h[2]+7)//8;rec=tuple(get(q,size));q+=size;pts=decode_record_points(rec)
      if any(not(0<=x<256 and 0<=y<192) for x,y in pts):raise ValueError('viewport')
      points.update(pts);recs.append(rec)
     touched={((y//8)*320+(x//8)*8) for x,y in points};cleared=set()
     for lo,hi,c in clear:
      off=lo+hi*256
      if c==0 or off%8 or off+c*8>7680:raise ValueError('clear span')
      cleared.update(range(off,off+c*8,8))
     if touched!=cleared:raise ValueError('clear coverage')
     if any(not(1<=c<=255 and lo+hi*256+c<=960) for lo,hi,c,v in spans):raise ValueError('colors')
     fs.append(FrameBuild(recs,clear,sum(r[2] for r in recs),len(points),[],spans))
    hits.append((fs,colors))
   except (ValueError,RuntimeError,IndexError):pass
 if len(hits)!=1:raise ValueError((path,len(hits),[(len(x),c) for x,c in hits]))
 sig=re.search(b'\xa9(.)\xa2\x00\x9d\x00\x04\x9d\x00\x05',b[:0x1600-load+2],re.S)
 if not sig:raise ValueError('screen init signature')
 hud=re.search(b'\xbd(..)\x9d\x00\x3e\x9d\x00\x7e\x9d\x00\xfe\xe8\xe0(.)',b[:0x1600-load+2],re.S)
 if not hud:raise ValueError('HUD signature')
 raw=bytes(get(int.from_bytes(hud[1],'little'),hud[2][0]));glyphs={bytes(bitmap_text(chr(c),1)):chr(c) for c in range(32,96)}
 glyphs[bytes(bitmap_text(' ',1))]=' '
 text=''.join(glyphs.get(raw[i:i+8],'?') for i in range(0,len(raw),8))
 return *hits[0],sig[1][0],raw,text
