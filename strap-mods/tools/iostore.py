import struct, sys
def fstr(d,o):
    n,=struct.unpack_from('<i',d,o); o+=4
    if n==0: return '',o
    if n<0:
        n=-n; s=d[o:o+n*2-2].decode('utf-16le'); o+=n*2
    else:
        s=d[o:o+n-1].decode('latin1'); o+=n
    return s,o
def parse_toc(path):
    d=open(path,'rb').read()
    o=16; ver=d[o]; o+=4
    hdr,ent,cbe,cbs,cmc,cml,cbsz,dis,pc=struct.unpack_from('<9I',d,o); o+=36
    cid,=struct.unpack_from('<Q',d,o); o+=8
    o+=16; flags=d[o]; o+=1
    seeds,=struct.unpack_from('<I',d,84); nohash,=struct.unpack_from('<I',d,96)
    o=hdr
    ids=[d[o+12*i:o+12*i+12] for i in range(ent)]; o+=12*ent
    offs=[]
    for i in range(ent):
        b=d[o:o+10]; o+=10
        offs.append((int.from_bytes(b[:5],'big'),int.from_bytes(b[5:],'big')))
    o+=4*seeds+4*nohash
    blocks=[]
    for i in range(cbe):
        b=d[o:o+12]; o+=12
        off=int.from_bytes(b[:5],'little'); csz=int.from_bytes(b[5:8],'little'); usz=int.from_bytes(b[8:11],'little'); m=b[11]
        blocks.append((off,csz,usz,m))
    o+=cmc*cml
    if flags & 2: # signed
        sz,=struct.unpack_from('<I',d,o); o+=4+sz*2+20*cbe
    dir_data=d[o:o+dis]; o+=dis
    meta=[d[o+33*i:o+33*i+33] for i in range(ent)]
    # dir index
    p=0
    mount,p=fstr(dir_data,p)
    n,=struct.unpack_from('<I',dir_data,p); p+=4
    dirs=[struct.unpack_from('<4I',dir_data,p+16*i) for i in range(n)]; p+=16*n
    n,=struct.unpack_from('<I',dir_data,p); p+=4
    files=[struct.unpack_from('<3I',dir_data,p+12*i) for i in range(n)]; p+=12*n
    n,=struct.unpack_from('<I',dir_data,p); p+=4
    strs=[]
    for i in range(n):
        s,p=fstr(dir_data,p); strs.append(s)
    paths={}
    def walk(di,prefix):
        name,child,sib,first=dirs[di]
        pre=prefix
        if name!=0xFFFFFFFF: pre=prefix+strs[name]+'/'
        f=first
        while f!=0xFFFFFFFF:
            fn,nf,ue=files[f]; paths[ue]=pre+strs[fn]; f=nf
        c=child
        while c!=0xFFFFFFFF:
            walk(c,pre); c=dirs[c][2]
    walk(0,'')
    return dict(ids=ids,offs=offs,blocks=blocks,paths=paths,meta=meta,bsz=cbsz,flags=flags,cid=cid,ver=ver,mount=mount)
def read_chunk(toc,ucas,i):
    off,ln=toc['offs'][i]; bsz=toc['bsz']
    out=b''
    first=off//bsz; last=(off+ln-1)//bsz
    with open(ucas,'rb') as f:
        for b in range(first,last+1):
            boff,csz,usz,m=toc['blocks'][b]
            assert m==0
            f.seek(boff); out+=f.read(usz)
    s=off-first*bsz
    return out[s:s+ln]
if __name__=='__main__':
    t=parse_toc(sys.argv[1])
    print('mount',t['mount'],'ver',t['ver'],'flags',t['flags'],'entries',len(t['ids']))
    for i,(idb,(o,l)) in enumerate(zip(t['ids'],t['offs'])):
        typ=idb[11]
        print(i,idb.hex(),'type',typ,l,t['paths'].get(i,''))
