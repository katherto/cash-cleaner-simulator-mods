"""Append one extra chunk (a package) to an existing uncompressed IoStore container, in place."""
import struct, sys
import iostore, iobuild as B

def parse_dir(dd):
    p=0
    ln,=struct.unpack_from('<i',dd,p); mp=dd[p:p+4+ln]; p+=4+ln
    n,=struct.unpack_from('<I',dd,p); p+=4
    dirs=[list(struct.unpack_from('<4I',dd,p+16*i)) for i in range(n)]; p+=16*n
    n,=struct.unpack_from('<I',dd,p); p+=4
    files=[list(struct.unpack_from('<3I',dd,p+12*i)) for i in range(n)]; p+=12*n
    n,=struct.unpack_from('<I',dd,p); p+=4
    strs=[]
    for i in range(n):
        l,=struct.unpack_from('<i',dd,p); strs.append(dd[p:p+4+l]); p+=4+l
    assert p==len(dd)
    return mp,dirs,files,strs
def ser_dir(mp,dirs,files,strs):
    return mp+struct.pack('<I',len(dirs))+b''.join(struct.pack('<4I',*d) for d in dirs)+struct.pack('<I',len(files))+b''.join(struct.pack('<3I',*f) for f in files)+struct.pack('<I',len(strs))+b''.join(strs)

def parse_header(h):
    magic,ver,cid,cnt=struct.unpack_from('<IIQI',h,0); o=20
    ids=list(struct.unpack_from(f'<{cnt}Q',h,o)); o+=8*cnt
    sz,=struct.unpack_from('<I',h,o); o+=4
    se=h[o:o+sz]; o+=sz
    entries=[]
    for k in range(cnt):
        n,off,sn,so=struct.unpack_from('<IIII',se,16*k)
        assert sn==0 and so==0
        entries.append(list(struct.unpack_from(f'<{n}Q',se,16*k+off)) if n else [])
    return magic,ver,cid,ids,entries,h[o:]
def ser_header(magic,ver,cid,ids,entries,tail):
    base=16*len(ids); hdrs=b'';data=b''
    for k,imps in enumerate(entries):
        off=base+len(data)-16*k
        hdrs+=struct.pack('<IIII',len(imps),off if imps else 0,0,0)
        data+=b''.join(struct.pack('<Q',i) for i in imps)
    se=hdrs+data
    return struct.pack('<IIQI',magic,ver,cid,len(ids))+b''.join(struct.pack('<Q',i) for i in ids)+struct.pack('<I',len(se))+se+tail

def read_toc_raw(path):
    d=open(path,'rb').read()
    hdr,ent,cbe,cbs,cmc,cml,cbsz,dis,pc=struct.unpack_from('<9I',d,20)
    assert hdr==144 and cbs==12 and cmc==0 and d[80]&5==0
    o=144
    ids=d[o:o+12*ent]; o+=12*ent
    offs=d[o:o+10*ent]; o+=10*ent
    blocks=d[o:o+12*cbe]; o+=12*cbe
    di=d[o:o+dis]; o+=dis
    meta=d[o:o+33*ent]; o+=33*ent
    assert o==len(d)
    return d[:144],ids,offs,blocks,di,meta

def merge_multi(utoc,ucas,asset_dir_chain,assets):
    """assets: list of (file_name, package_id, asset_bytes, imports)"""
    h144,ids,offs,blocks,di,meta=read_toc_raw(utoc)
    ent=len(ids)//12; cbe=len(blocks)//12
    t=iostore.parse_toc(utoc)
    # --- locate container header chunk (type 6)
    hi=[i for i in range(ent) if ids[12*i+11]==6]; assert len(hi)==1; hi=hi[0]
    hdr_bytes=iostore.read_chunk(t,ucas,hi)
    parts=parse_header(hdr_bytes)
    assert ser_header(*parts)==hdr_bytes, 'container header roundtrip failed'
    # --- directory index
    mp,dirs,files,strs=parse_dir(di)
    assert ser_dir(mp,dirs,files,strs)==di,'dir index roundtrip failed'
    # find target dir
    cur=0
    for name in asset_dir_chain:
        c=dirs[cur][1]; found=None
        while c!=0xFFFFFFFF:
            s=strs[dirs[c][0]]
            if s[4:-1].decode()==name: found=c;break
            c=dirs[c][2]
        assert found is not None,name
        cur=found
    for k,(fname,_,_,_) in enumerate(assets):
        strs.append(B.fstr(fname))
        files.append([len(strs)-1,dirs[cur][3],ent+k])
        dirs[cur][3]=len(files)-1
    new_di=ser_dir(mp,dirs,files,strs)
    ucas_data=open(ucas,'rb').read()
    bsz=65536
    magic,ver,cid,pids,entries,tail=parts
    for _,pid,_,imps in assets:
        assert pid not in pids
        pids=pids+[pid]; entries=entries+[list(imps)]
    new_hdr=ser_header(magic,ver,cid,pids,entries,tail); assert len(new_hdr)<=bsz
    k=len(assets)
    ids2=ids; offs_l=[offs[10*i:10*i+10] for i in range(ent)]
    blocks2=blocks; new_ucas=bytearray(ucas_data)
    for j,(fname,pid,data,imps) in enumerate(assets):
        assert len(data)<=bsz
        ids2+=B.chunk_id(pid,1)
        offs_l.append(((cbe+j)*bsz).to_bytes(5,'big')+len(data).to_bytes(5,'big'))
        pos=len(new_ucas)
        blocks2+=pos.to_bytes(5,'little')+len(data).to_bytes(3,'little')+len(data).to_bytes(3,'little')+b'\0'
        new_ucas+=data
    offs_l[hi]=((cbe+k)*bsz).to_bytes(5,'big')+len(new_hdr).to_bytes(5,'big')
    pos=len(new_ucas)
    blocks2+=pos.to_bytes(5,'little')+len(new_hdr).to_bytes(3,'little')+len(new_hdr).to_bytes(3,'little')+b'\0'
    new_ucas+=new_hdr
    new_ucas+=b'\0'*((-len(new_ucas))%16)      # keep aligned-read inside the file
    meta2=meta+b'\0'*(33*k)
    h=bytearray(h144)
    struct.pack_into('<III',h,24,ent+k,cbe+k+1,12)
    struct.pack_into('<I',h,48,len(new_di))
    toc=bytes(h)+ids2+b''.join(offs_l)+blocks2+new_di+meta2
    return toc,bytes(new_ucas)

if __name__=='__main__':
    pass
